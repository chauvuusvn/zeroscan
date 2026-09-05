#!/usr/bin/env python3
"""
Project Memory V2.0 Engine (core/memory.py)
Standard runtime for managing Git-backed .agent/ project memory.
Pure Python 3.11+ standard library implementation (zero external dependencies).
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MAX_BOOTSTRAP_CONTEXT_BYTES = 10 * 1024  # 10 KB budget

REQUIRED_AGENT_FILES = [
    "BOOT.md",
    "PROJECT_STATE.json",
    "PROJECT_MAP.json",
    "DECISIONS.md",
    "TASK_LEDGER.jsonl",
    "NEXT_TASK.md",
    "MEMORY_PROTOCOL.md",
]


def find_agent_dir(start_path: Optional[Path] = None) -> Path:
    """Finds the .agent directory in start_path or any parent directory."""
    current = (start_path or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        agent_dir = parent / ".agent"
        if agent_dir.is_dir():
            return agent_dir
    # If currently inside .agent itself
    if current.name == ".agent":
        return current
    # Default fallback to current / .agent
    return (current / ".agent")


def get_git_commit(cwd: Path) -> str:
    """Returns the current HEAD git commit hash (short or full), or 'uncommitted'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "uncommitted"


def get_git_status_summary(cwd: Path) -> Dict[str, Any]:
    """Returns git status details."""
    try:
        commit = get_git_commit(cwd)
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown"

        dirty_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        is_dirty = bool(dirty_res.stdout.strip()) if dirty_res.returncode == 0 else False

        return {
            "commit": commit,
            "branch": branch,
            "is_dirty": is_dirty,
        }
    except Exception as e:
        return {"commit": "unknown", "branch": "unknown", "is_dirty": False, "error": str(e)}


def calculate_metrics(agent_dir: Path) -> Dict[str, Any]:
    """Calculates bootstrap context bytes and total agent system bytes."""
    file_sizes = {}
    total_system_bytes = 0

    if agent_dir.is_dir():
        for p in agent_dir.rglob("*"):
            if p.is_file():
                sz = p.stat().st_size
                rel = str(p.relative_to(agent_dir))
                file_sizes[rel] = sz
                total_system_bytes += sz

    bootstrap_files = ["BOOT.md", "PROJECT_STATE.json", "NEXT_TASK.md"]
    bootstrap_bytes = sum(file_sizes.get(f, 0) for f in bootstrap_files)

    # Count tasks in TASK_LEDGER.jsonl
    ledger_path = agent_dir / "TASK_LEDGER.jsonl"
    task_count = 0
    if ledger_path.is_file():
        with open(ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    task_count += 1

    return {
        "bootstrap_context_bytes": bootstrap_bytes,
        "total_agent_system_bytes": total_system_bytes,
        "completed_tasks_count": task_count,
        "budget_limit_bytes": MAX_BOOTSTRAP_CONTEXT_BYTES,
        "budget_used_percent": round((bootstrap_bytes / MAX_BOOTSTRAP_CONTEXT_BYTES) * 100, 2),
        "file_sizes": file_sizes,
    }


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    temp_path = path.with_suffix(f".tmp.{os.getpid()}")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    temp_path.replace(path)


def atomic_write_text(path: Path, text: str) -> None:
    temp_path = path.with_suffix(f".tmp.{os.getpid()}")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(text)
    temp_path.replace(path)


def generate_boot_markdown(state: Dict[str, Any]) -> str:
    """Generates a synchronized, minimal BOOT.md from state."""
    commit_str = state.get("verified_commit", "uncommitted")
    if len(commit_str) > 12 and commit_str != "uncommitted":
        short_commit = commit_str[:8]
    else:
        short_commit = commit_str

    content = f"""# {state.get('project_name', 'Project')} — Agent Boot Anchor

**MISSION**: {state.get('mission', '')}

---

## ⚡ Current Execution State
- **CURRENT PHASE**: {state.get('current_phase', 'Phase 0')}
- **CURRENT STATUS**: {state.get('status', 'INITIALIZING')}
- **ACTIVE TASK**: {state.get('active_task', 'None')}
- **VERIFIED COMMIT**: `{short_commit}`
- **LAST CHECKPOINT**: {state.get('last_updated', datetime.datetime.now(datetime.timezone.utc).isoformat())}

---

## 🔒 Critical Constraints
1. **Zero-Scan Boot**: Do NOT recursively explore the repo. Consult `.agent/PROJECT_MAP.json`.
2. **Budget Rule**: Combined size of `BOOT.md`, `PROJECT_STATE.json`, `NEXT_TASK.md` must be `<= 10 KB`.
3. **Locked Decisions**: Adhere strictly to locked architectural decisions in `.agent/DECISIONS.md`.
4. **Evidence First**: Only mark tasks complete after passing verified test suites.

---

## 🧭 Files to Read Next
1. `.agent/NEXT_TASK.md` (Active task requirements & acceptance criteria)
2. `.agent/PROJECT_MAP.json` (GPS domain map for relevant files & test suites)
"""
    return content


def generate_next_task_markdown(
    task_id: str,
    phase: str,
    title: str,
    description: str = "",
    criteria: Optional[List[str]] = None,
    target_files: Optional[List[str]] = None,
    verification: Optional[List[str]] = None,
) -> str:
    """Generates a standardized NEXT_TASK.md specification."""
    desc_str = description.strip() if description else f"Execute requirements and verify tests for {title}."

    crit_list = criteria or [
        "Requirements defined in task goal are implemented.",
        "Code follows existing project style and patterns.",
        "Unit/integration tests pass with 0 errors.",
        "Memory state checkpointed via `.agent/memory.py checkpoint`.",
    ]
    crit_str = "\n".join(f"- [ ] {c}" for c in crit_list)

    files_list = target_files or ["Consult `.agent/PROJECT_MAP.json` for domain paths."]
    files_str = "\n".join(f"- `{f}`" if not f.startswith("-") else f for f in files_list)

    verif_list = verification or ["pytest", "python3 .agent/memory.py validate"]
    verif_str = "\n".join(verif_list)

    return f"""# Active Task Specification

## Task Metadata
- **TASK ID**: {task_id}
- **PHASE**: {phase}
- **TITLE**: {title}
- **STATUS**: IN_PROGRESS

---

## 🎯 Goal & Description
{desc_str}

---

## 📋 Acceptance Criteria
{crit_str}

---

## 📂 Target Files
{files_str}

---

## 🧪 Verification Commands
```bash
{verif_str}
```
"""


def validate_agent_memory(agent_dir: Path) -> Tuple[bool, List[str], List[str]]:
    """Validates memory integrity against rules and schemas."""
    errors = []
    warnings = []

    if not agent_dir.is_dir():
        errors.append(f"Directory not found: {agent_dir}")
        return False, errors, warnings

    # 1. Check required files
    for req_file in REQUIRED_AGENT_FILES:
        fp = agent_dir / req_file
        if not fp.is_file():
            errors.append(f"Missing required memory file: {req_file}")

    # If critical files missing, stop early
    if errors:
        return False, errors, warnings

    # 2. Validate JSON syntax and required keys
    state_file = agent_dir / "PROJECT_STATE.json"
    map_file = agent_dir / "PROJECT_MAP.json"

    try:
        state = load_json(state_file)
        state_req_keys = [
            "version",
            "project_name",
            "mission",
            "current_phase",
            "status",
            "active_task",
            "verified_commit",
            "last_updated",
            "metrics",
        ]
        for k in state_req_keys:
            if k not in state:
                errors.append(f"PROJECT_STATE.json missing required key: '{k}'")
    except Exception as e:
        errors.append(f"PROJECT_STATE.json is invalid JSON: {e}")
        state = {}

    try:
        pmap = load_json(map_file)
        map_req_keys = ["version", "project_name", "domains", "infrastructure"]
        for k in map_req_keys:
            if k not in pmap:
                errors.append(f"PROJECT_MAP.json missing required key: '{k}'")
    except Exception as e:
        errors.append(f"PROJECT_MAP.json is invalid JSON: {e}")

    # 3. Validate TASK_LEDGER.jsonl format
    ledger_file = agent_dir / "TASK_LEDGER.jsonl"
    ledger_count = 0
    try:
        with open(ledger_file, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    ledger_count += 1
                    for lk in ["task_id", "timestamp", "summary"]:
                        if lk not in record:
                            warnings.append(f"TASK_LEDGER.jsonl line {line_no} missing key '{lk}'")
                except json.JSONDecodeError:
                    errors.append(f"TASK_LEDGER.jsonl line {line_no} is not valid JSON")
    except Exception as e:
        errors.append(f"Failed to read TASK_LEDGER.jsonl: {e}")

    # 4. Check synchronization between BOOT.md and PROJECT_STATE.json
    boot_file = agent_dir / "BOOT.md"
    try:
        boot_content = boot_file.read_text(encoding="utf-8")
        if state.get("project_name") and state["project_name"] not in boot_content:
            warnings.append("BOOT.md project_name does not match PROJECT_STATE.json")
        if state.get("current_phase") and state["current_phase"] not in boot_content:
            warnings.append("BOOT.md current_phase is out of sync with PROJECT_STATE.json")
    except Exception as e:
        errors.append(f"Failed to read BOOT.md: {e}")

    # 5. Check git commit synchronization
    repo_root = agent_dir.parent
    git_info = get_git_status_summary(repo_root)
    verified_commit = state.get("verified_commit")
    if verified_commit and verified_commit != "uncommitted" and git_info["commit"] != "uncommitted":
        if not git_info["commit"].startswith(verified_commit) and not verified_commit.startswith(git_info["commit"]):
            warnings.append(
                f"Git HEAD ({git_info['commit'][:8]}) differs from verified_commit ({verified_commit[:8]}) in state."
            )
    if git_info.get("is_dirty"):
        warnings.append("Working tree has uncommitted changes.")

    # 6. Check context size budget
    metrics = calculate_metrics(agent_dir)
    bootstrap_bytes = metrics["bootstrap_context_bytes"]
    if bootstrap_bytes > MAX_BOOTSTRAP_CONTEXT_BYTES:
        errors.append(
            f"Bootstrap context size ({bootstrap_bytes} B) exceeds 10 KB budget limit ({MAX_BOOTSTRAP_CONTEXT_BYTES} B)!"
        )

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def cmd_status(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.exists():
        print(f"[ERROR] .agent directory not found at: {agent_dir}")
        return 1

    state_file = agent_dir / "PROJECT_STATE.json"
    if not state_file.exists():
        print(f"[ERROR] PROJECT_STATE.json not found in {agent_dir}")
        return 1

    state = load_json(state_file)
    metrics = calculate_metrics(agent_dir)
    git_info = get_git_status_summary(agent_dir.parent)

    print("=" * 60)
    print(f"  PROJECT MEMORY V2.0 STATUS: {state.get('project_name', 'Unknown')}")
    print("=" * 60)
    print(f"Mission          : {state.get('mission')}")
    print(f"Current Phase    : {state.get('current_phase')}")
    print(f"Status           : {state.get('status')}")
    print(f"Active Task      : {state.get('active_task')}")
    print(f"Verified Commit  : {state.get('verified_commit')}")
    print(f"Git Current HEAD : {git_info['commit']} (dirty={git_info['is_dirty']})")
    print(f"Last Checkpoint  : {state.get('last_updated')}")
    print("-" * 60)
    print("BUDGET & SIZE METRICS:")
    print(
        f"Bootstrap Context: {metrics['bootstrap_context_bytes']} / {metrics['budget_limit_bytes']} bytes ({metrics['budget_used_percent']}%)"
    )
    print(f"Total Agent Files: {metrics['total_agent_system_bytes']} bytes")
    print(f"Tasks Completed  : {metrics['completed_tasks_count']}")
    print("-" * 60)
    print("FILE SIZE BREAKDOWN:")
    for fn, sz in sorted(metrics["file_sizes"].items()):
        print(f"  - {fn:<22}: {sz:>6} bytes")
    print("=" * 60)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    print(f"🔍 Validating Project Memory V2.0 at: {agent_dir} ...")
    is_valid, errors, warnings = validate_agent_memory(agent_dir)

    for w in warnings:
        print(f"  ⚠️  [WARN] {w}")

    if errors:
        for e in errors:
            print(f"  ❌ [FAIL] {e}")
        print(f"\n❌ Validation FAILED with {len(errors)} error(s) and {len(warnings)} warning(s).")
        return 1

    metrics = calculate_metrics(agent_dir)
    print("  ✅ All required files present and valid.")
    print("  ✅ Schema and JSON syntax verified.")
    print(f"  ✅ Context budget OK: {metrics['bootstrap_context_bytes']} bytes <= 10,240 bytes limit ({metrics['budget_used_percent']}% utilized).")
    print("\n✨ Memory integrity verification PASSED.")
    return 0


def cmd_metrics(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    metrics = calculate_metrics(agent_dir)
    if getattr(args, "json", False):
        print(json.dumps(metrics, indent=2))
    else:
        print(f"Bootstrap Context Bytes : {metrics['bootstrap_context_bytes']} B")
        print(f"Total Agent System Bytes: {metrics['total_agent_system_bytes']} B")
        print(f"Budget Limit            : {metrics['budget_limit_bytes']} B")
        print(f"Budget Utilization      : {metrics['budget_used_percent']}%")
        print(f"Completed Tasks         : {metrics['completed_tasks_count']}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    state_file = agent_dir / "PROJECT_STATE.json"
    if not state_file.exists():
        print(f"[ERROR] PROJECT_STATE.json not found in {agent_dir}")
        return 1

    state = load_json(state_file)
    repo_root = agent_dir.parent

    # Update state fields if provided
    if args.phase:
        state["current_phase"] = args.phase
    if args.status:
        state["status"] = args.status
    if args.active_task:
        state["active_task"] = args.active_task

    commit = args.commit or get_git_commit(repo_root)
    state["verified_commit"] = commit
    state["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Append to ledger if requested or task details provided
    if args.record_ledger or (args.task_id and args.task_summary):
        task_id = args.task_id or f"TASK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        summary = args.task_summary or f"Completed {state.get('active_task')}"
        evidence = args.evidence or "verified_by_checkpoint"
        ledger_entry = {
            "task_id": task_id,
            "phase": state.get("current_phase"),
            "timestamp": state["last_updated"],
            "commit": commit,
            "summary": summary,
            "evidence": evidence,
        }
        ledger_path = agent_dir / "TASK_LEDGER.jsonl"
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(ledger_entry) + "\n")
        print(f"📝 Appended record {task_id} to TASK_LEDGER.jsonl")

    # Update NEXT_TASK.md if requested
    if getattr(args, "next_task", None):
        next_task_title = args.next_task
        state["active_task"] = next_task_title
        next_task_id = getattr(args, "next_task_id", None) or f"TASK-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        next_task_file = agent_dir / "NEXT_TASK.md"
        next_task_content = generate_next_task_markdown(
            task_id=next_task_id,
            phase=state["current_phase"],
            title=next_task_title,
            description=getattr(args, "next_task_desc", "") or "",
        )
        atomic_write_text(next_task_file, next_task_content)
        print(f"📋 Synchronized NEXT_TASK.md for {next_task_id}: {next_task_title}")

    # Update metrics inside state
    metrics = calculate_metrics(agent_dir)
    state["metrics"]["bootstrap_context_bytes"] = metrics["bootstrap_context_bytes"]
    state["metrics"]["total_agent_system_bytes"] = metrics["total_agent_system_bytes"]
    state["metrics"]["completed_tasks_count"] = metrics["completed_tasks_count"]

    if args.test_status:
        state["metrics"]["test_suite_status"] = args.test_status

    # Write synchronized PROJECT_STATE.json
    atomic_write_json(state_file, state)

    # Synchronize BOOT.md
    boot_file = agent_dir / "BOOT.md"
    boot_content = generate_boot_markdown(state)
    atomic_write_text(boot_file, boot_content)

    # Recalculate and persist updated metrics after file rewrites
    updated_metrics = calculate_metrics(agent_dir)
    state["metrics"]["bootstrap_context_bytes"] = updated_metrics["bootstrap_context_bytes"]
    state["metrics"]["total_agent_system_bytes"] = updated_metrics["total_agent_system_bytes"]
    atomic_write_json(state_file, state)

    print(f"💾 Checkpoint saved successfully at {state['last_updated']}.")
    print(f"   Phase: {state['current_phase']} | Status: {state['status']} | Active: {state['active_task']}")
    print(f"   Commit: {commit[:8] if len(commit) >= 8 else commit}")
    print(f"   Bootstrap Size: {updated_metrics['bootstrap_context_bytes']} bytes ({updated_metrics['budget_used_percent']}%)")
    return 0


def cmd_add_decision(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    decisions_file = agent_dir / "DECISIONS.md"
    if not decisions_file.exists():
        print(f"[ERROR] DECISIONS.md not found in {agent_dir}")
        return 1

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    status_label = f"[{args.status.upper()}]"

    adr_block = f"""
## {args.id}: {args.title}
- **Date**: {today}
- **Status**: {status_label}
- **Context**: {args.context}
- **Decision**: {args.decision}
- **Consequences**: {args.consequences}
"""
    with open(decisions_file, "a", encoding="utf-8") as f:
        f.write(adr_block)

    print(f"🏛️ Added {args.id} to DECISIONS.md with status {status_label}")
    return 0


def main() -> int:
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--target",
        "-t",
        help="Target repository or .agent path (defaults to current directory search)",
    )

    parser = argparse.ArgumentParser(
        parents=[common_parser],
        description="Project Memory V2.0 Engine CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # status
    p_status = subparsers.add_parser("status", parents=[common_parser], help="Show project memory state and budget metrics")
    p_status.set_defaults(func=cmd_status)

    # validate
    p_val = subparsers.add_parser("validate", parents=[common_parser], help="Validate memory integrity, schemas, and context budget")
    p_val.set_defaults(func=cmd_validate)

    # metrics
    p_metrics = subparsers.add_parser("metrics", parents=[common_parser], help="Calculate context size metrics")
    p_metrics.add_argument("--json", action="store_true", help="Output metrics as JSON")
    p_metrics.set_defaults(func=cmd_metrics)

    # checkpoint
    p_cp = subparsers.add_parser("checkpoint", parents=[common_parser], help="Atomically update state and synchronize BOOT.md")
    p_cp.add_argument("--phase", help="Current project phase")
    p_cp.add_argument("--status", choices=["INITIALIZING", "IN_PROGRESS", "PAUSED", "COMPLETED", "BLOCKED"], help="Execution status")
    p_cp.add_argument("--active-task", help="Active task description")
    p_cp.add_argument("--commit", help="Explicit verified commit hash (defaults to git rev-parse HEAD)")
    p_cp.add_argument("--test-status", help="Status summary of test suite (e.g. 'ALL_PASS (42/42)')")
    p_cp.add_argument("--record-ledger", action="store_true", help="Record task completion to TASK_LEDGER.jsonl")
    p_cp.add_argument("--task-id", help="Task ID for ledger (e.g. TASK-002)")
    p_cp.add_argument("--task-summary", help="Summary for ledger record")
    p_cp.add_argument("--evidence", help="Verification evidence tag or output hash")
    p_cp.add_argument("--next-task", help="Title of next active task (updates NEXT_TASK.md and state)")
    p_cp.add_argument("--next-task-id", help="Task ID for next active task (e.g. TASK-003)")
    p_cp.add_argument("--next-task-desc", help="Goal and description for next active task")
    p_cp.set_defaults(func=cmd_checkpoint)

    # add-decision
    p_adr = subparsers.add_parser("add-decision", parents=[common_parser], help="Append an ADR to DECISIONS.md")
    p_adr.add_argument("--id", required=True, help="ADR ID (e.g. ADR-002)")
    p_adr.add_argument("--title", required=True, help="Decision title")
    p_adr.add_argument("--status", default="LOCKED", choices=["LOCKED", "PROPOSED", "DEPRECATED", "SUPERSEDED"], help="Status")
    p_adr.add_argument("--context", required=True, help="Context and problem statement")
    p_adr.add_argument("--decision", required=True, help="The decision made")
    p_adr.add_argument("--consequences", required=True, help="Consequences and trade-offs")
    p_adr.set_defaults(func=cmd_add_decision)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
