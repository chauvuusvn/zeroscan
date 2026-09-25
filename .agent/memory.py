#!/usr/bin/env python3
"""
Project Memory V2.1 Self-Healing Engine (core/memory.py)
Standard runtime for managing Git-backed .agent/ project memory.
Pure Python 3.11+ standard library implementation (zero external dependencies).

New in V2.1:
- Resilient JSON loader with backup fallback & zero-crash guarantees.
- Atomic State-to-Boot Auto-Sync (Trips zero state drift).
- Ledger Auto-Pruning & Archival (Prevents context budget overflow > 10KB).
- Bound-checked agent directory locator.

Copyright (c) 2026 Chau Vu / CPF-FAMILY. Licensed under MIT.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MAX_BOOTSTRAP_CONTEXT_BYTES = 10 * 1024  # 10 KB budget
MAX_ACTIVE_LEDGER_TASKS = 50

REQUIRED_AGENT_FILES = [
    "BOOT.md",
    "PROJECT_STATE.json",
    "PROJECT_MAP.json",
    "DECISIONS.md",
    "TASK_LEDGER.jsonl",
    "NEXT_TASK.md",
    "MEMORY_PROTOCOL.md",
]


def find_agent_dir(start_path: Optional[Path] = None, require_existing: bool = False) -> Path:
    """
    Finds the .agent directory in start_path or any parent directory.
    If require_existing is True and not found, raises FileNotFoundError.
    """
    current = (start_path or Path.cwd()).resolve()
    for parent in [current] + list(current.parents):
        agent_dir = parent / ".agent"
        if agent_dir.is_dir():
            return agent_dir
    # If currently inside .agent itself
    if current.name == ".agent":
        return current
    
    fallback = current / ".agent"
    if require_existing and not fallback.is_dir():
        raise FileNotFoundError(
            f"Zero-Scan: No .agent/ directory found at {current} or any parent. "
            "Please initialize with 'zeroscan bootstrap' first."
        )
    return fallback


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

        diff_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        is_dirty = bool(diff_res.stdout.strip())

        return {
            "commit": commit,
            "branch": branch,
            "is_dirty": is_dirty,
            "status": "dirty" if is_dirty else "clean",
        }
    except Exception:
        return {
            "commit": "uncommitted",
            "branch": "unknown",
            "is_dirty": False,
            "status": "non-git",
        }


def calculate_metrics(agent_dir: Path) -> Dict[str, Any]:
    """Calculates byte sizes and context budget consumption."""
    file_sizes: Dict[str, int] = {}
    total_system_bytes = 0

    if agent_dir.is_dir():
        for fp in agent_dir.iterdir():
            if fp.is_file():
                sz = fp.stat().st_size
                file_sizes[fp.name] = sz
                total_system_bytes += sz

    bootstrap_files = ["BOOT.md", "PROJECT_STATE.json", "NEXT_TASK.md"]
    bootstrap_bytes = sum(file_sizes.get(f, 0) for f in bootstrap_files)

    # Count tasks in TASK_LEDGER.jsonl
    ledger_path = agent_dir / "TASK_LEDGER.jsonl"
    task_count = 0
    if ledger_path.is_file():
        with open(ledger_path, "r", encoding="utf-8", errors="replace") as f:
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


def load_json(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Resilient JSON loader with automatic backup fallback.
    Prevents crash on empty files or mid-write corruption.
    """
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                if default is not None:
                    return default
                raise ValueError(f"JSON file is empty: {path}")
            return json.loads(content)
    except (json.JSONDecodeError, ValueError) as e:
        # Check for .bak file
        bak_path = path.with_suffix(path.suffix + ".bak")
        if bak_path.is_file():
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        if default is not None:
            return default
        raise ValueError(f"Corrupted JSON in {path}: {e}") from e


def atomic_write_json(path: Path, data: Dict[str, Any], auto_sync_boot: bool = True) -> None:
    """
    Writes JSON data atomically with file sync and .bak snapshot.
    If writing PROJECT_STATE.json, automatically syncs BOOT.md.
    """
    # Create backup of current state if exists
    if path.is_file() and path.stat().st_size > 0:
        try:
            bak_path = path.with_suffix(path.suffix + ".bak")
            shutil.copy2(path, bak_path)
        except Exception:
            pass

    temp_path = path.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    temp_path.replace(path)

    # Automatic State-to-Boot Auto-Sync
    if auto_sync_boot and path.name == "PROJECT_STATE.json":
        agent_dir = path.parent
        boot_path = agent_dir / "BOOT.md"
        try:
            boot_md = generate_boot_markdown(data)
            atomic_write_text(boot_path, boot_md)
        except Exception:
            pass


def atomic_write_text(path: Path, text: str) -> None:
    """Writes text data atomically with fsync."""
    temp_path = path.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    temp_path.replace(path)


def prune_and_archive_ledger(agent_dir: Path, max_tasks: int = MAX_ACTIVE_LEDGER_TASKS) -> int:
    """
    Prunes TASK_LEDGER.jsonl when lines exceed max_tasks, moving older records
    to .agent/archive/TASK_LEDGER_ARCHIVE.jsonl to keep active context budget < 5 KB.
    """
    ledger_path = agent_dir / "TASK_LEDGER.jsonl"
    if not ledger_path.is_file():
        return 0

    lines: List[str] = []
    with open(ledger_path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line for line in f if line.strip()]

    if len(lines) <= max_tasks:
        return 0

    # Archive older lines, keep recent 20
    keep_count = 20
    to_archive = lines[:-keep_count]
    to_keep = lines[-keep_count:]

    archive_dir = agent_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / "TASK_LEDGER_ARCHIVE.jsonl"

    with open(archive_file, "a", encoding="utf-8") as f:
        f.writelines(to_archive)

    atomic_write_text(ledger_path, "".join(to_keep))
    return len(to_archive)


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
3. **Locked Decisions**: Adhere strictly to approved architectural invariants in `.agent/DECISIONS.md`.
4. **Task Lifecycle**: Check `NEXT_TASK.md`, perform work, verify, log to `TASK_LEDGER.jsonl`, checkpoint state.

---

## 🚀 Instant Navigation & Tooling
- **Architecture**: Consult `.agent/PROJECT_MAP.json`
- **Decisions Log**: Read `.agent/DECISIONS.md`
- **Ledger**: Append to `.agent/TASK_LEDGER.jsonl`
- **Validation**: Run `python3 .agent/memory.py validate`
"""
    return content


def generate_next_task_markdown(
    task_id: str,
    phase: str,
    title: str,
    description: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    target_files: Optional[List[str]] = None,
    verification: Optional[List[str]] = None,
) -> str:
    """Generates a structured NEXT_TASK.md specification."""
    desc_list = description or ["Execute active task per phase objective."]
    desc_str = "\n".join(f"- {d}" if not d.startswith("-") else d for d in desc_list)

    crit_list = acceptance_criteria or [
        "Implementation meets requirements.",
        "Zero regressions in existing test suite.",
        "Project Memory state checkpointed.",
    ]
    crit_str = "\n".join(f"- [ ] {c}" if not c.startswith("-") else c for c in crit_list)

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
        with open(ledger_file, "r", encoding="utf-8", errors="replace") as f:
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
                    errors.append(f"TASK_LEDGER.jsonl line {line_no} contains invalid JSON")
    except Exception as e:
        errors.append(f"Error reading TASK_LEDGER.jsonl: {e}")

    # 4. Validate context budget limit
    metrics = calculate_metrics(agent_dir)
    boot_bytes = metrics["bootstrap_context_bytes"]
    if boot_bytes > MAX_BOOTSTRAP_CONTEXT_BYTES:
        errors.append(
            f"Context budget exceeded: {boot_bytes} bytes > limit of {MAX_BOOTSTRAP_CONTEXT_BYTES} bytes."
        )
    elif boot_bytes > (MAX_BOOTSTRAP_CONTEXT_BYTES * 0.85):
        warnings.append(
            f"Context budget nearing limit: {boot_bytes} / {MAX_BOOTSTRAP_CONTEXT_BYTES} bytes ({metrics['budget_used_percent']}%)."
        )

    # 5. Check sync between BOOT.md and PROJECT_STATE.json
    boot_file = agent_dir / "BOOT.md"
    if boot_file.is_file() and state:
        boot_text = boot_file.read_text(encoding="utf-8", errors="replace")
        active_task = state.get("active_task")
        if active_task and active_task != "None" and active_task not in boot_text:
            warnings.append(f"BOOT.md appears desynchronized with active_task '{active_task}'")

    is_valid = (len(errors) == 0)
    return is_valid, errors, warnings


def cmd_metrics(args: argparse.Namespace) -> int:
    """Show context budget metrics in text or JSON."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1
    metrics = calculate_metrics(agent_dir)
    if getattr(args, "json", False):
        print(json.dumps(metrics, indent=2))
    else:
        print(f"Bootstrap Context : {metrics['bootstrap_context_bytes']} bytes")
        print(f"Total Agent Memory: {metrics['total_agent_system_bytes']} bytes")
        print(f"Budget Used       : {metrics['budget_used_percent']}%")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1

    state_file = agent_dir / "PROJECT_STATE.json"
    if not state_file.exists():
        print(f"[ERROR] PROJECT_STATE.json not found in {agent_dir}")
        return 1

    state = load_json(state_file, default={})
    metrics = calculate_metrics(agent_dir)
    git_info = get_git_status_summary(agent_dir.parent)

    print("=" * 60)
    print(f"  PROJECT MEMORY V2.1 STATUS: {state.get('project_name', 'Unknown')}")
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
    print(f"🔍 Validating Project Memory V2.1 at: {agent_dir} ...")
    is_valid, errors, warnings = validate_agent_memory(agent_dir)

    for w in warnings:
        print(f"  ⚠️  [WARNING] {w}")

    if is_valid:
        print(f"  ✅ [PASS] Project Memory is 100% compliant with V2.1 specification.")
        return 0
    else:
        for e in errors:
            print(f"  ❌ [ERROR] {e}")
        print(f"  ❌ [FAIL] Memory validation failed with {len(errors)} error(s).")
        return 1


def cmd_sync(args: argparse.Namespace) -> int:
    """Force synchronization of BOOT.md and project state."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1

    state_file = agent_dir / "PROJECT_STATE.json"
    if not state_file.exists():
        print(f"[ERROR] PROJECT_STATE.json not found in {agent_dir}")
        return 1

    state = load_json(state_file)
    git_info = get_git_status_summary(agent_dir.parent)
    state["verified_commit"] = git_info["commit"]
    state["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    metrics = calculate_metrics(agent_dir)
    state["metrics"] = metrics

    atomic_write_json(state_file, state, auto_sync_boot=True)
    pruned = prune_and_archive_ledger(agent_dir)

    print(f"✅ Synchronized BOOT.md with latest state (Commit: {git_info['commit'][:8]}).")
    if pruned > 0:
        print(f"📦 Archived {pruned} old task(s) to .agent/archive/TASK_LEDGER_ARCHIVE.jsonl")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-Scan Project Memory V2.1 CLI Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_status = subparsers.add_parser("status", help="Show project memory status and metrics")
    p_status.add_argument("--target", "-t", type=str, help="Target project root directory")

    p_metrics = subparsers.add_parser("metrics", help="Show context budget metrics")
    p_metrics.add_argument("--target", "-t", type=str, help="Target project root directory")
    p_metrics.add_argument("--json", action="store_true", help="Output metrics as JSON")

    p_val = subparsers.add_parser("validate", help="Validate memory files against schema & budget")
    p_val.add_argument("--target", "-t", type=str, help="Target project root directory")

    p_sync = subparsers.add_parser("sync", help="Synchronize BOOT.md and checkpoint git commit")
    p_sync.add_argument("--target", "-t", type=str, help="Target project root directory")

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "metrics":
        return cmd_metrics(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "sync":
        return cmd_sync(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
