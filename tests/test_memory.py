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


if __name__ == "__main__":
    unittest.main()
