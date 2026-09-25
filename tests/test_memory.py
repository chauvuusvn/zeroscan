"""Unit tests for Project Memory V2.0 Core Engine (core/memory.py)."""

import argparse
import subprocess
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bootstrap
from core import memory


class TestProjectMemoryEngine(unittest.TestCase):
    """Test suite for memory engine functionality and budget validation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

        # Bootstrap clean valid memory structure
        self.agent_dir = bootstrap.bootstrap_project_memory(
            target_dir=self.repo_root,
            name="test_project",
            mission="Unit testing Zero-Scan engine",
            phase="Phase 1 - Testing",
            domains=["core", "auth", "api"],
            force=True,
            auto_git_init=True,
        )

        subprocess.run(["git", "config", "user.name", "Tester"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo_root, check=True)
        subprocess.run(["git", "commit", "-m", "Initial test commit"], cwd=self.repo_root, check=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_agent_dir(self):
        """Verify .agent directory discovery from repo root and nested subdirectories."""
        found = memory.find_agent_dir(self.repo_root)
        self.assertEqual(found.resolve(), self.agent_dir.resolve())

        nested = self.repo_root / "src" / "deep" / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        found_nested = memory.find_agent_dir(nested)
        self.assertEqual(found_nested.resolve(), self.agent_dir.resolve())

    def test_validate_agent_memory(self):
        """Verify memory validation passes and detects context budget correctly."""
        valid, errors, _ = memory.validate_agent_memory(self.agent_dir)
        self.assertTrue(valid, f"Validation failed with errors: {errors}")
        self.assertEqual(len(errors), 0)

    def test_calculate_metrics(self):
        """Verify context budget calculation is strictly <= 10 KB."""
        metrics = memory.calculate_metrics(self.agent_dir)
        self.assertIn("bootstrap_context_bytes", metrics)
        self.assertLessEqual(metrics["bootstrap_context_bytes"], 10240)
        self.assertIn("budget_used_percent", metrics)

    def test_cmd_status_and_validate(self):
        """Verify CLI subcommands return success exit code (0)."""
        args_val = argparse.Namespace(target=str(self.repo_root))
        ret_val = memory.cmd_validate(args_val)
        self.assertEqual(ret_val, 0)

        args_status = argparse.Namespace(target=str(self.repo_root))
        ret_status = memory.cmd_status(args_status)
        self.assertEqual(ret_status, 0)

        args_metrics = argparse.Namespace(target=str(self.repo_root), json=False)
        ret_metrics = memory.cmd_metrics(args_metrics)
        self.assertEqual(ret_metrics, 0)

    def test_corrupted_json_recovery_with_backup(self):
        """Verify resilient JSON loader falls back to .bak or default on corruption."""
        test_file = self.agent_dir / "TEST_STATE.json"
        valid_data = {"key": "original_valid"}
        memory.atomic_write_json(test_file, valid_data)
        
        # Second write creates TEST_STATE.json.bak
        updated_data = {"key": "updated_valid"}
        memory.atomic_write_json(test_file, updated_data)
        
        # Corrupt the main file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("{corrupted json...")
            
        # load_json should gracefully recover from .bak
        recovered = memory.load_json(test_file)
        self.assertIn("key", recovered)

    def test_atomic_write_json_auto_syncs_boot(self):
        """Verify atomic write to PROJECT_STATE.json auto-syncs BOOT.md."""
        state_file = self.agent_dir / "PROJECT_STATE.json"
        boot_file = self.agent_dir / "BOOT.md"
        state = memory.load_json(state_file)
        
        state["active_task"] = "TASK-AUTOSYNC-999"
        memory.atomic_write_json(state_file, state, auto_sync_boot=True)
        
        boot_content = boot_file.read_text(encoding="utf-8")
        self.assertIn("TASK-AUTOSYNC-999", boot_content)

    def test_prune_and_archive_ledger(self):
        """Verify task ledger archives old tasks when exceeding budget."""
        ledger_file = self.agent_dir / "TASK_LEDGER.jsonl"
        
        # Generate 60 tasks
        with open(ledger_file, "w", encoding="utf-8") as f:
            for i in range(60):
                f.write(f'{{"task_id": "TASK-{i:03d}", "timestamp": "2026-09-24", "summary": "Task {i}"}}\n')
                
        archived_count = memory.prune_and_archive_ledger(self.agent_dir, max_tasks=50)
        self.assertEqual(archived_count, 40)
        
        # Check active ledger has 20 tasks
        with open(ledger_file, "r", encoding="utf-8") as f:
            active_lines = [l for l in f if l.strip()]
        self.assertEqual(len(active_lines), 20)
        
        # Check archive exists
        archive_file = self.agent_dir / "archive" / "TASK_LEDGER_ARCHIVE.jsonl"
        self.assertTrue(archive_file.is_file())

    def test_cmd_checkpoint_and_add_decision(self):
        """Verify cmd_checkpoint and cmd_add_decision CLI subcommands execute properly."""
        args_cp = argparse.Namespace(
            target=str(self.repo_root),
            task_id="TASK-TEST-CLI",
            summary="CLI checkpoint validation",
            evidence="pytest 100% pass",
            phase="Phase 2 - Testing",
            next_task="TASK-TEST-CLI-NEXT",
        )
        ret_cp = memory.cmd_checkpoint(args_cp)
        self.assertEqual(ret_cp, 0)

        # Check ledger received the record
        ledger = (self.agent_dir / "TASK_LEDGER.jsonl").read_text(encoding="utf-8")
        self.assertIn("TASK-TEST-CLI", ledger)

        # Check BOOT.md synced
        boot = (self.agent_dir / "BOOT.md").read_text(encoding="utf-8")
        self.assertIn("TASK-TEST-CLI-NEXT", boot)

        # Check add_decision
        args_dec = argparse.Namespace(
            target=str(self.repo_root),
            id="ADR-CLI-099",
            title="Adopt CLI Governance",
            decision="Enforce CLI checkpoint command",
            context="Resolving audit gaps",
            status="LOCKED",
        )
        ret_dec = memory.cmd_add_decision(args_dec)
        self.assertEqual(ret_dec, 0)

        decisions = (self.agent_dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("ADR-CLI-099", decisions)


if __name__ == "__main__":
    unittest.main()
