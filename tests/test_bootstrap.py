"""Unit tests for Project Memory V2.0 Bootstrapper (bootstrap.py)."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import bootstrap
from core import memory


class TestBootstrapGenerator(unittest.TestCase):
    """Test suite for automated scaffolding of .agent/ structure."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bootstrap_scaffold_creates_valid_agent_system(self):
        """Verify bootstrap_project_memory creates all required files and passes validation."""
        agent_dir = bootstrap.bootstrap_project_memory(
            target_dir=self.target_dir,
            name="demo_project",
            mission="Scaffolding test for Zero-Scan",
            phase="Phase 1 - Inception",
            domains=["core", "auth", "api"],
            force=True,
            auto_git_init=True,
        )

        self.assertTrue(agent_dir.is_dir())
        self.assertTrue((agent_dir / "BOOT.md").is_file())
        self.assertTrue((agent_dir / "PROJECT_STATE.json").is_file())
        self.assertTrue((agent_dir / "PROJECT_MAP.json").is_file())
        self.assertTrue((agent_dir / "DECISIONS.md").is_file())
        self.assertTrue((agent_dir / "NEXT_TASK.md").is_file())
        self.assertTrue((agent_dir / "TASK_LEDGER.jsonl").is_file())
        self.assertTrue((agent_dir / "MEMORY_PROTOCOL.md").is_file())
        self.assertTrue((agent_dir / "memory.py").is_file())

        # Validate with memory engine
        valid, errors, _ = memory.validate_agent_memory(agent_dir)
        self.assertTrue(valid, f"Scaffolded memory failed validation: {errors}")

        # Check metrics
        metrics = memory.calculate_metrics(agent_dir)
        self.assertLessEqual(metrics["bootstrap_context_bytes"], 10240)


if __name__ == "__main__":
    unittest.main()
