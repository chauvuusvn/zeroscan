#!/usr/bin/env python3
"""
Project Memory V2.0 Bootstrap Generator (bootstrap.py)
Automated scaffolding CLI to initialize standard .agent/ memory structure into any project repository.
Zero external dependencies (pure Python 3.11+). Supports standalone curl execution.
"""

import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    TEMPLATE_ROOT = Path(__file__).resolve().parent
except Exception:
    TEMPLATE_ROOT = Path.cwd()

RAW_GITHUB_BASE = "https://raw.githubusercontent.com/chauvuusvn/zeroscan/main"


def get_template_bytes(rel_path: str) -> bytes:
    """Loads template bytes from local repository directory or downloads via GitHub raw fallback."""
    try:
        local_file = TEMPLATE_ROOT / rel_path
        if local_file.is_file():
            return local_file.read_bytes()
    except Exception:
        pass

    # Remote fallback for standalone / pipe execution
    url = f"{RAW_GITHUB_BASE}/{rel_path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZeroScan-Bootstrap/2.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read()
    except Exception as e:
        raise RuntimeError(f"Could not load template '{rel_path}' locally or from {url}: {e}")


def get_git_commit(repo_path: Path) -> str:
    """Returns current git commit hash of repo or 'uncommitted'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "uncommitted"


def is_git_repo(repo_path: Path) -> bool:
    """Checks if directory is inside a git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        return res.returncode == 0 and res.stdout.strip() == "true"
    except Exception:
        return False


def build_project_map(project_name: str, domains_list: List[str], repo_root: Path) -> Dict[str, Any]:
    """Builds initial PROJECT_MAP.json content."""
    domains = {}
    for d in domains_list:
        d_clean = d.strip()
        if not d_clean:
            continue
        # Guess common file/test paths
        domain_files = [f"src/{d_clean}/"] if (repo_root / "src" / d_clean).exists() else [f"{d_clean}/"]
        domain_tests = [f"tests/test_{d_clean}.py"] if (repo_root / "tests").exists() else [f"tests/"]
        domains[d_clean] = {
            "description": f"Core business logic and utilities for {d_clean}",
            "entry_points": [f"{d_clean}/__init__.py" if (repo_root / d_clean).exists() else f"src/{d_clean}/__init__.py"],
            "files": domain_files,
            "tests": domain_tests,
            "dependencies": []
        }

    # Add default general domain if none given
    if not domains:
        domains["core"] = {
            "description": "Primary application module and logic",
            "entry_points": ["src/main.py"],
            "files": ["src/"],
            "tests": ["tests/"],
            "dependencies": []
        }

    return {
        "version": "2.0",
        "project_name": project_name,
        "domains": domains,
        "infrastructure": {
            "config_files": ["pyproject.toml", "package.json", "Makefile", "Dockerfile", ".env.example"],
            "docs": ["README.md", "docs/"],
            "cicd": [".github/workflows/"]
        }
    }


def bootstrap_project_memory(
    target_dir: Path,
    name: str,
    mission: str,
    phase: str,
    domains: List[str],
    force: bool = False,
    auto_git_init: bool = False,
) -> Path:
    """Scaffolds .agent/ memory system in target directory."""
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    if auto_git_init and not is_git_repo(target_dir):
        print(f"🔧 Initializing Git repository in {target_dir}...")
        subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)

    agent_dir = target_dir / ".agent"

    if agent_dir.exists():
        if not force:
            raise FileExistsError(
                f"Directory '{agent_dir}' already exists. Use --force to overwrite."
            )
        else:
            shutil.rmtree(agent_dir)

    agent_dir.mkdir(parents=True, exist_ok=True)

    commit = get_git_commit(target_dir)
    short_commit = commit[:8] if commit != "uncommitted" else "uncommitted"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 1. Copy MEMORY_PROTOCOL.md
    protocol_bytes = get_template_bytes("core/MEMORY_PROTOCOL.md")
    (agent_dir / "MEMORY_PROTOCOL.md").write_bytes(protocol_bytes)

    # 2. Copy memory.py engine
    memory_bytes = get_template_bytes("core/memory.py")
    memory_dst = agent_dir / "memory.py"
    memory_dst.write_bytes(memory_bytes)
    memory_dst.chmod(0o755)

    # 3. Create DECISIONS.md
    decisions_content = get_template_bytes("templates/DECISIONS.md").decode("utf-8").replace("{{DATE}}", today_str)
    (agent_dir / "DECISIONS.md").write_text(decisions_content, encoding="utf-8")

    # 4. Create TASK_LEDGER.jsonl
    ledger_content = (
        get_template_bytes("templates/TASK_LEDGER.jsonl")
        .decode("utf-8")
        .replace("{{TIMESTAMP}}", now_iso)
        .replace("{{VERIFIED_COMMIT}}", commit)
    )
    (agent_dir / "TASK_LEDGER.jsonl").write_text(ledger_content, encoding="utf-8")

    # 5. Create NEXT_TASK.md
    next_task_content = (
        get_template_bytes("templates/NEXT_TASK.md")
        .decode("utf-8")
        .replace("{{TASK_ID}}", "TASK-001")
        .replace("{{CURRENT_PHASE}}", phase)
        .replace("{{TASK_TITLE}}", "Bootstrap project architecture and verify memory system")
        .replace(
            "{{TASK_DESCRIPTION}}",
            f"Initialize foundational project structure for {name} and verify initial test/build setup.",
        )
        .replace("{{TARGET_FILES}}", "- `.agent/PROJECT_MAP.json`\n- `README.md`\n- `pyproject.toml`")
        .replace("{{VERIFICATION_COMMANDS}}", "python3 .agent/memory.py validate")
    )
    (agent_dir / "NEXT_TASK.md").write_text(next_task_content, encoding="utf-8")

    # 6. Create PROJECT_MAP.json
    project_map_data = build_project_map(name, domains, target_dir)
    (agent_dir / "PROJECT_MAP.json").write_text(
        json.dumps(project_map_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 7. Create PROJECT_STATE.json
    state_data = {
        "version": "2.0",
        "project_name": name,
        "mission": mission,
        "current_phase": phase,
        "status": "INITIALIZING",
        "active_task": "Bootstrap project architecture and verify memory system",
        "verified_commit": commit,
        "last_updated": now_iso,
        "metrics": {
            "bootstrap_context_bytes": 0,
            "total_agent_system_bytes": 0,
            "completed_tasks_count": 1,
            "test_suite_status": "PENDING_SETUP",
        },
        "constraints": [
            "Keep bootstrap context <= 10 KB",
            "Follow MEMORY_PROTOCOL.md strictly",
            "Verify all changes with tests before checkpointing",
        ],
    }
    (agent_dir / "PROJECT_STATE.json").write_text(
        json.dumps(state_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 8. Create Level 0 BOOT.md
    boot_content = (
        get_template_bytes("templates/BOOT.md")
        .decode("utf-8")
        .replace("{{PROJECT_NAME}}", name)
        .replace("{{MISSION}}", mission)
        .replace("{{CURRENT_PHASE}}", phase)
        .replace("{{STATUS}}", "INITIALIZING")
        .replace("{{ACTIVE_TASK}}", "Bootstrap project architecture and verify memory system")
        .replace("{{VERIFIED_COMMIT}}", short_commit)
        .replace("{{LAST_UPDATED}}", now_iso)
    )
    (agent_dir / "BOOT.md").write_text(boot_content, encoding="utf-8")

    # 9. Dynamically import memory engine to compute metrics and sync state
    spec = importlib.util.spec_from_file_location("agent_memory", agent_dir / "memory.py")
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        metrics = mod.calculate_metrics(agent_dir)
        state_data["metrics"]["bootstrap_context_bytes"] = metrics["bootstrap_context_bytes"]
        state_data["metrics"]["total_agent_system_bytes"] = metrics["total_agent_system_bytes"]
        mod.atomic_write_json(agent_dir / "PROJECT_STATE.json", state_data)

    return agent_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project Memory V2.0 Bootstrapper — Scaffold .agent/ for any repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        "-t",
        default=".",
        help="Target project directory path (default: current directory)",
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Project name (defaults to target directory name)",
    )
    parser.add_argument(
        "--mission",
        "-m",
        default="Autonomous system development and execution",
        help="Project mission statement",
    )
    parser.add_argument(
        "--phase",
        "-p",
        default="Phase 1 - Architecture & Setup",
        help="Initial phase name",
    )
    parser.add_argument(
        "--domains",
        "-d",
        default="core,auth,api,db",
        help="Comma-separated initial domain list (e.g. core,auth,api,db)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing .agent/ directory",
    )
    parser.add_argument(
        "--git-init",
        action="store_true",
        help="Run git init if target directory is not a git repository",
    )

    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    project_name = args.name or target_path.name

    domain_list = [d.strip() for d in args.domains.split(",") if d.strip()]

    print("=" * 65)
    print("🚀 Project Memory V2.0 Scaffolder")
    print("=" * 65)
    print(f"Target Directory: {target_path}")
    print(f"Project Name    : {project_name}")
    print(f"Mission         : {args.mission}")
    print(f"Phase           : {args.phase}")
    print(f"Domains         : {', '.join(domain_list)}")
    print("-" * 65)

    try:
        agent_dir = bootstrap_project_memory(
            target_dir=target_path,
            name=project_name,
            mission=args.mission,
            phase=args.phase,
            domains=domain_list,
            force=args.force,
            auto_git_init=args.git_init,
        )
    except FileExistsError as fee:
        print(f"\n❌ [ERROR] {fee}")
        return 1
    except Exception as e:
        print(f"\n❌ [ERROR] Scaffolding failed: {e}")
        return 1

    print(f"\n✨ Scaffolding complete! Structure created at `.agent/`:")
    for item in sorted(agent_dir.glob("*")):
        if item.is_file():
            print(f"  ├── {item.name:<20} ({item.stat().st_size:>5} bytes)")

    # Validate generated memory
    spec = importlib.util.spec_from_file_location("agent_memory", agent_dir / "memory.py")
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        is_valid, errors, warnings = mod.validate_agent_memory(agent_dir)
        metrics = mod.calculate_metrics(agent_dir)
        print("\n📊 Initial Context Budget Metrics:")
        print(f"  • Bootstrap Context Size : {metrics['bootstrap_context_bytes']} / {metrics['budget_limit_bytes']} bytes ({metrics['budget_used_percent']}%)")
        print(f"  • Total .agent/ Size     : {metrics['total_agent_system_bytes']} bytes")

        if is_valid:
            print("\n✅ Verification PASSED: New memory system is fully compliant with V2.0 standard.")
        else:
            print(f"\n⚠️  Verification Warnings/Errors: {len(errors)} errors, {len(warnings)} warnings.")

    print("\n💡 Quick Start Guide for Agents:")
    print("   1. Boot session   : Read `.agent/BOOT.md` (< 1 KB)")
    print("   2. Check status   : `python3 .agent/memory.py status`")
    print("   3. Validate state : `python3 .agent/memory.py validate`")
    print("   4. Save progress  : `python3 .agent/memory.py checkpoint --phase \"...\" --status IN_PROGRESS`")
    print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
