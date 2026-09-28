#!/usr/bin/env python3
"""
Project Memory V2.2.0 Bootstrapper (bootstrap.py)
Automated scaffold engine to initialize .agent/ structure in any repository.
Pure Python 3.9+ standard library implementation (zero external dependencies).
"""

import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from core.memory import calculate_metrics, atomic_write_json, validate_agent_memory
except ImportError:
    try:
        from memory import calculate_metrics, atomic_write_json, validate_agent_memory  # type: ignore
    except ImportError:
        calculate_metrics = None  # type: ignore
        atomic_write_json = None  # type: ignore
        validate_agent_memory = None  # type: ignore


def compute_static_bootstrap_metrics(agent_dir: Path) -> Dict[str, Any]:
    """Compute context metrics safely without dynamic module execution."""
    if calculate_metrics is not None:
        return calculate_metrics(agent_dir)

    bootstrap_files = ["BOOT.md", "PROJECT_STATE.json", "NEXT_TASK.md"]
    boot_bytes = 0
    for bf in bootstrap_files:
        p = agent_dir / bf
        if p.is_file():
            boot_bytes += p.stat().st_size

    total_bytes = 0
    if agent_dir.is_dir():
        for p in agent_dir.rglob("*"):
            if p.is_file():
                total_bytes += p.stat().st_size

    return {
        "bootstrap_context_bytes": boot_bytes,
        "max_allowed_bytes": 10240,
        "budget_limit_bytes": 10240,
        "budget_used_percent": round((boot_bytes / 10240) * 100, 2),
        "total_agent_system_bytes": total_bytes,
    }


try:
    TEMPLATE_ROOT = Path(__file__).resolve().parent
except Exception:
    TEMPLATE_ROOT = Path.cwd()

RAW_GITHUB_BASE = os.environ.get(
    "ZEROSCAN_RAW_GITHUB_BASE",
    "https://raw.githubusercontent.com/chauvuusvn/zeroscan/master"
)

DEFAULT_INLINE_TEMPLATES = {
    "templates/TASK_LEDGER.jsonl": "{\"task_id\": \"INIT-001\", \"phase\": \"Phase 0 - Bootstrap\", \"timestamp\": \"{{TIMESTAMP}}\", \"commit\": \"{{VERIFIED_COMMIT}}\", \"summary\": \"Project memory initialized with V2.1 standard architecture.\", \"evidence\": \"bootstrap_validation_passed\"}\n",
    "templates/NEXT_TASK.md": "# Active Task Specification\n\n## Task Metadata\n- **TASK ID**: {{TASK_ID}}\n- **PHASE**: {{CURRENT_PHASE}}\n- **TITLE**: {{TASK_TITLE}}\n- **STATUS**: IN_PROGRESS\n\n---\n\n## 🎯 Goal & Description\n{{TASK_DESCRIPTION}}\n\n---\n\n## 📋 Acceptance Criteria\n- [ ] Requirements defined in task goal are implemented.\n- [ ] Code follows existing project style and patterns.\n- [ ] Unit/integration tests pass with 0 errors.\n- [ ] Memory state checkpointed via `.agent/memory.py checkpoint`.\n\n---\n\n## 📂 Target Files\n{{TARGET_FILES}}\n\n---\n\n## 🧪 Verification Commands\n```bash\n{{VERIFICATION_COMMANDS}}\n```\n",
    "templates/PROJECT_MAP.json": "{\n  \"version\": \"2.2.0\",\n  \"project_name\": \"zeroscan\",\n  \"domains\": {\n    \"core\": {\n      \"description\": \"Core memory engine, state management, and MCP server\",\n      \"entry_points\": [\n        \"core/memory.py\",\n        \"core/mcp_server.py\"\n      ],\n      \"files\": [\n        \"core/\"\n      ],\n      \"tests\": [\n        \"tests/test_memory.py\",\n        \"tests/test_mcp_server.py\"\n      ],\n      \"dependencies\": []\n    },\n    \"bootstrap\": {\n      \"description\": \"Repository scaffolding and template generation engine\",\n      \"entry_points\": [\n        \"bootstrap.py\"\n      ],\n      \"files\": [\n        \"bootstrap.py\",\n        \"templates/\",\n        \"schema/\"\n      ],\n      \"tests\": [\n        \"tests/test_bootstrap.py\"\n      ],\n      \"dependencies\": []\n    },\n    \"benchmarks\": {\n      \"description\": \"Token reduction benchmarks and SWE-bench evaluation engine\",\n      \"entry_points\": [\n        \"benchmarks/evaluator.py\"\n      ],\n      \"files\": [\n        \"benchmarks/\"\n      ],\n      \"tests\": [\n        \"tests/test_benchmarks.py\"\n      ],\n      \"dependencies\": []\n    }\n  },\n  \"infrastructure\": {\n    \"config_files\": [\n      \"pyproject.toml\",\n      \"README.md\",\n      \"LICENSE\"\n    ],\n    \"docs\": [\n      \"README.md\",\n      \"README.vi.md\",\n      \"HUONG_DAN_SU_DUNG.md\",\n      \"USAGE_GUIDE.md\"\n    ],\n    \"cicd\": [\n      \".github/workflows/ci.yml\"\n    ]\n  }\n}\n",
    "templates/BOOT.md": "# {{PROJECT_NAME}} — Agent Boot Anchor\n\n**MISSION**: {{MISSION}}\n\n---\n\n## ⚡ Current Execution State\n- **CURRENT PHASE**: {{CURRENT_PHASE}}\n- **CURRENT STATUS**: {{STATUS}}\n- **ACTIVE TASK**: {{ACTIVE_TASK}}\n- **VERIFIED COMMIT**: `{{VERIFIED_COMMIT}}`\n- **LAST CHECKPOINT**: {{LAST_UPDATED}}\n\n---\n\n## 🔒 Critical Constraints\n1. **Zero-Scan Boot**: Do NOT recursively explore the repo. Consult `.agent/PROJECT_MAP.json`.\n2. **Budget Rule**: Combined size of `BOOT.md`, `PROJECT_STATE.json`, `NEXT_TASK.md` must be `<= 10 KB`.\n3. **Locked Decisions**: Adhere strictly to locked architectural decisions in `.agent/DECISIONS.md`.\n4. **Evidence First**: Only mark tasks complete after passing verified test suites.\n\n---\n\n## 🧭 Files to Read Next\n1. `.agent/NEXT_TASK.md` (Active task requirements & acceptance criteria)\n2. `.agent/PROJECT_MAP.json` (GPS domain map for relevant files & test suites)\n",
    "templates/DECISIONS.md": "# Architectural Decision Records (ADRs)\n\nThis file records key architectural, design, and structural decisions for the project. Decisions marked `[LOCKED]` are binding on all autonomous agents and human developers until formally superseded.\n\n---\n\n## ADR-001: Adoption of Project Memory V2.1 Architecture\n- **Date**: {{DATE}}\n- **Status**: [LOCKED]\n- **Context**: Autonomous agents require deterministic session resumption and fast context loading without scanning the entire repository.\n- **Decision**: Adopt `.agent/` directory structure with Level 0 `BOOT.md`, machine-readable `PROJECT_STATE.json`, `PROJECT_MAP.json`, and append-only `TASK_LEDGER.jsonl`.\n- **Consequences**: All agents must follow `MEMORY_PROTOCOL.md` and keep bootstrap context `<= 10 KB`.\n",
    "core/MEMORY_PROTOCOL.md": "# Project Memory V2.1 Protocol & Standard Operating Procedures\n\nThis document outlines the **10 Golden Rules of Agent Memory** for all AI coding agents (Hermes, Claude Code, OpenAI Codex, OpenCode). Adherence to this protocol guarantees zero-scan bootstrap, zero context bloat, deterministic task resumption, and cross-session state integrity.\n\n---\n\n## The 10 Golden Rules\n\n### Rule 1: Level 0 Boot First (Zero-Scan Rule)\n- On session kickoff, **always** read `.agent/BOOT.md` first.\n- Never recursively crawl or scan entire directory trees to \"understand the project\".\n- `BOOT.md` is strictly capped at `< 1 KB` (~30-35 lines) and provides immediate orientation: project name, mission, current phase, active task, verified commit hash, and critical constraints.\n\n### Rule 2: Verified Commit Binding\n- Every state checkpoint in `.agent/PROJECT_STATE.json` must be bound to a real, verifiable Git commit hash (`verified_commit`).\n- If the current git `HEAD` does not match `verified_commit`, the agent must inspect git diff/log to reconcile drift before proceeding.\n\n### Rule 3: GPS Routing via Map & JIT RAG Retrieval\n- Consult `.agent/PROJECT_MAP.json` as the architectural GPS.\n- Identify the functional domain and load only the specific files, schemas, and test suites indicated in the map.\n- For deep historical queries or specific factual verification, execute the Level-2 JIT RAG Engine (`obsidian_rag_bridge.py`) to retrieve exact 1-2 chunks (<1 KB) instead of full-disk scanning.\n- Update `PROJECT_MAP.json` whenever new modules, entry points, or test suites are created.\n\n### Rule 4: Immutable Locked Decisions (ADRs)\n- Architectural Decision Records in `.agent/DECISIONS.md` with status `[LOCKED]` are non-negotiable architectural invariants.\n- Agents must never revert, overwrite, or bypass locked decisions without explicit operator authorization.\n\n### Rule 5: Atomic State Checkpointing\n- All updates to project status, phase transitions, and test results must be recorded atomically using `python3 .agent/memory.py checkpoint`.\n- State transitions must never leave `PROJECT_STATE.json` or `BOOT.md` in a corrupted or half-written state.\n\n### Rule 6: Immutable Append-Only Ledger\n- `.agent/TASK_LEDGER.jsonl` is an immutable, append-only chronological ledger of completed tasks, milestones, and phases.\n- Never delete, reorder, or edit existing lines in the ledger. Each entry must record `task_id`, `phase`, `timestamp`, `commit`, `summary`, and `evidence_hash`.\n\n### Rule 7: Single Active Task Focus\n- `.agent/NEXT_TASK.md` specifies exactly one active task at any given time.\n- The file contains strict acceptance criteria, target files, and exact verification commands.\n- An agent must complete or explicitly block the active task before picking up a new one.\n\n### Rule 8: Evidence-Based Verification\n- A task cannot be marked completed in `PROJECT_STATE.json` or `TASK_LEDGER.jsonl` without tangible verification evidence.\n- Acceptable evidence includes test suite outputs (`exit_code == 0`), execution logs, deterministic benchmark numbers, or generated artifact verification.\n\n### Rule 9: Strict Context Budget Enforcement\n- Memory overhead must remain ultra-lean.\n- **Bootstrap Budget**: `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` combined (`BOOTSTRAP_CONTEXT_BYTES`) must remain `<= 10,240 bytes` (10 KB).\n- **Total System Budget**: Entire `.agent/` directory should remain lean and structured. Prune or archive verbose outputs.\n\n### Rule 10: Memory Validation & Integrity Guard\n- Run `python3 .agent/memory.py validate` before starting a task and after completing a checkpoint.\n- Validation checks schema compliance, file existence, git commit alignment, and context size budgets. If validation fails, halt and resolve anomalies immediately.\n\n---\n\n## Standard Agent Workflow Lifecycle\n\n```\n[Agent Starts]\n      │\n      ▼\n1. Read `.agent/BOOT.md` (Level 0 - Zero Scan)\n      │\n      ▼\n2. Validate Memory State (`python3 .agent/memory.py validate`)\n      │\n      ▼\n3. Read `.agent/NEXT_TASK.md` & Consult `.agent/PROJECT_MAP.json`\n      │\n      ▼\n4. Read Only Targeted Domain Files & Tests\n      │\n      ▼\n5. Execute Code Changes & Run Verifications\n      │\n      ▼\n6. Commit Code (`git commit -m \"...\"`)\n      │\n      ▼\n7. Checkpoint Memory (`python3 .agent/memory.py checkpoint ...`)\n      │\n      ▼\n[Agent Ready for Next Task / Handoff]\n```\n"
}


def get_template_bytes(rel_path: str) -> bytes:
    """Load template from local repository, official GitHub, or fallback to offline hardcoded templates."""
    local_path = TEMPLATE_ROOT / rel_path
    if local_path.is_file():
        return local_path.read_bytes()

    # If memory.py is requested and exists in core/
    if rel_path == "core/memory.py":
        alt_core = Path(__file__).resolve().parent / "core" / "memory.py"
        if alt_core.is_file():
            return alt_core.read_bytes()

    # Try remote fetch
    url = f"{RAW_GITHUB_BASE}/{rel_path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZeroScan-Bootstrapper/2.2.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read()
    except Exception as e:
        # Fallback to hardcoded offline templates
        if rel_path in DEFAULT_INLINE_TEMPLATES:
            print(f"ℹ️  [OFFLINE FALLBACK] Loaded inline template for '{rel_path}'.")
            return DEFAULT_INLINE_TEMPLATES[rel_path].encode("utf-8")
        raise RuntimeError(f"Failed to fetch template '{rel_path}' (network unreachable and no offline template available): {e}")


def is_git_repo(path: Path) -> bool:
    """Check if the given directory is inside a Git repository."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            capture_output=True,
            text=True,
        )
        return res.returncode == 0 and "true" in res.stdout.strip().lower()
    except Exception:
        return False


def get_git_commit(path: Path) -> str:
    """Get the current Git commit SHA or return 'uncommitted'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "uncommitted"


def build_project_map(name: str, domains: List[str], project_root: Path) -> Dict[str, Any]:
    """Generate structured GPS PROJECT_MAP.json based on project domains."""
    project_map: Dict[str, Any] = {
        "version": "2.2.0",
        "project_name": name,
        "domains": {},
        "infrastructure": {
            "config_files": [
                "pyproject.toml",
                "package.json",
                "Makefile",
                "Dockerfile",
                ".env.example",
            ],
            "docs": [
                "README.md",
                "docs/",
            ],
            "cicd": [
                ".github/workflows/",
            ],
        },
    }

    for d in domains:
        d_clean = d.strip()
        if not d_clean:
            continue
        project_map["domains"][d_clean] = {
            "description": f"Core business logic and utilities for {d_clean}",
            "entry_points": [f"{d_clean}/__init__.py" if (project_root / d_clean).is_dir() else f"{d_clean}.py"],
            "files": [f"{d_clean}/" if (project_root / d_clean).is_dir() else f"{d_clean}.py"],
            "tests": [f"tests/test_{d_clean}.py"],
            "dependencies": [],
        }

    return project_map


def bootstrap_project_memory(
    target_dir: Path,
    name: str,
    mission: str,
    phase: str,
    domains: List[str],
    force: bool = False,
    auto_git_init: bool = False,
) -> Path:
    """Scaffolds .agent/ memory system in target directory with atomic rollback safety."""
    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    if auto_git_init and not is_git_repo(target_dir):
        print(f"🔧 Initializing Git repository in {target_dir}...")
        subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)

    agent_dir = target_dir / ".agent"

    if agent_dir.exists() and not force:
        raise FileExistsError(
            f"Directory '{agent_dir}' already exists. Use --force to overwrite."
        )

    staging_dir = target_dir / f".agent_staging_{os.getpid()}_{time.time_ns()}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    try:
        commit = get_git_commit(target_dir)
        short_commit = commit[:8] if commit != "uncommitted" else "uncommitted"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        today_str = datetime.datetime.now().strftime("%Y-%m-%d")

        # 1. Copy MEMORY_PROTOCOL.md
        protocol_bytes = get_template_bytes("core/MEMORY_PROTOCOL.md")
        (staging_dir / "MEMORY_PROTOCOL.md").write_bytes(protocol_bytes)

        # 2. Copy memory.py engine
        memory_bytes = get_template_bytes("core/memory.py")
        memory_dst = staging_dir / "memory.py"
        memory_dst.write_bytes(memory_bytes)
        memory_dst.chmod(0o755)

        # 3. Create DECISIONS.md
        decisions_content = get_template_bytes("templates/DECISIONS.md").decode("utf-8").replace("{{DATE}}", today_str)
        (staging_dir / "DECISIONS.md").write_text(decisions_content, encoding="utf-8")

        # 4. Create TASK_LEDGER.jsonl
        ledger_content = (
            get_template_bytes("templates/TASK_LEDGER.jsonl")
            .decode("utf-8")
            .replace("{{TIMESTAMP}}", now_iso)
            .replace("{{VERIFIED_COMMIT}}", commit)
        )
        (staging_dir / "TASK_LEDGER.jsonl").write_text(ledger_content, encoding="utf-8")

        # 5. Create NEXT_TASK.md
        next_task_content = (
            get_template_bytes("templates/NEXT_TASK.md")
            .decode("utf-8")
            .replace("{{TASK_ID}}", "INIT-001")
            .replace("{{DOMAIN}}", domains[0] if domains else "core")
            .replace(
                "{{TASK_DESCRIPTION}}",
                f"Initialize foundational project structure for {name} and verify initial test/build setup.",
            )
            .replace("{{TARGET_FILES}}", "- `.agent/PROJECT_MAP.json`\n- `README.md`\n- `pyproject.toml`")
            .replace("{{VERIFICATION_COMMANDS}}", "python3 .agent/memory.py validate")
        )
        (staging_dir / "NEXT_TASK.md").write_text(next_task_content, encoding="utf-8")

        # 6. Create PROJECT_MAP.json
        project_map_data = build_project_map(name, domains, target_dir)
        (staging_dir / "PROJECT_MAP.json").write_text(
            json.dumps(project_map_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # 7. Create PROJECT_STATE.json
        state_data = {
            "version": "2.2.0",
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
        (staging_dir / "PROJECT_STATE.json").write_text(
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
        (staging_dir / "BOOT.md").write_text(boot_content, encoding="utf-8")

        # 9. Compute initial metrics and sync state safely
        metrics = compute_static_bootstrap_metrics(staging_dir)
        state_data["metrics"]["bootstrap_context_bytes"] = metrics["bootstrap_context_bytes"]
        state_data["metrics"]["total_agent_system_bytes"] = metrics["total_agent_system_bytes"]
        (staging_dir / "PROJECT_STATE.json").write_text(
            json.dumps(state_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        if agent_dir.exists():
            shutil.rmtree(agent_dir)
        staging_dir.rename(agent_dir)

    except Exception:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        raise

    return agent_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project Memory V2.2.0 Bootstrapper — Scaffold .agent/ for any repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--target",
        "-t",
        type=str,
        default=".",
        help="Target project directory path (default: current directory)",
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        help="Project name (defaults to target directory name)",
    )
    parser.add_argument(
        "--mission",
        "-m",
        type=str,
        default="Autonomous software system developed with AI coding agents.",
        help="Project mission statement",
    )
    parser.add_argument(
        "--phase",
        "-p",
        type=str,
        default="Phase 1 - Initialization & Foundations",
        help="Initial phase name",
    )
    parser.add_argument(
        "--domains",
        "-d",
        type=str,
        default="core",
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
    print(f"🚀 Initializing Project Memory V2.2.0 for: {project_name}")
    print(f"📍 Target directory : {target_path}")
    print(f"🏷️  Domains          : {', '.join(domain_list)}")
    print("=" * 65)

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

    # Validate generated memory safely
    if validate_agent_memory is not None:
        is_valid, errors, warnings = validate_agent_memory(agent_dir)
    else:
        is_valid, errors, warnings = True, [], []

    metrics = compute_static_bootstrap_metrics(agent_dir)
    limit_bytes = metrics.get("max_allowed_bytes") or metrics.get("budget_limit_bytes", 10240)
    print("\n📊 Initial Context Budget Metrics:")
    print(f"  • Bootstrap Context Size : {metrics['bootstrap_context_bytes']} / {limit_bytes} bytes ({metrics['budget_used_percent']}%)")
    print(f"  • Total .agent/ Size     : {metrics['total_agent_system_bytes']} bytes")

    if is_valid:
        print("\n✅ Verification PASSED: New memory system is fully compliant with V2.2.0 standard.")
    else:
        print(f"\n⚠️  Verification Warnings/Errors: {len(errors)} errors, {len(warnings)} warnings.")

    print("\n💡 Quick Start Guide for Agents:")
    print("   1. Boot session   : Read `.agent/BOOT.md` (< 1 KB)")
    print("   2. Check status   : `zeroscan status` or `python3 .agent/memory.py status`")
    print("   3. Validate state : `zeroscan validate` or `python3 .agent/memory.py validate`")
    print("   4. Save progress  : `zeroscan checkpoint --task-id \"TASK-001\" --summary \"...\"`")
    print("   5. Add decision   : `zeroscan add-decision --id \"ADR-002\" --title \"...\" --decision \"...\"`")
    print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
