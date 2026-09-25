#!/usr/bin/env python3
"""
Project Memory V2.1.2 Self-Healing Engine (core/memory.py)
Standard runtime for managing Git-backed .agent/ project memory.
Pure Python 3.9+ standard library implementation (zero external dependencies).
"""

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    fcntl = None  # type: ignore
    HAS_FCNTL = False

MAX_BOOTSTRAP_CONTEXT_BYTES = 10240  # 10 KB budget ceiling
SPECIFICATION_VERSION = "2.1.2"


@contextlib.contextmanager
def file_lock(lock_path: Path, timeout: float = 5.0):
    """Cross-platform atomic file lock supporting POSIX (fcntl) and Windows (O_EXCL atomic spinlock)."""
    lock_file = lock_path.with_suffix(lock_path.suffix + ".lock")
    start_time = time.time()
    acquired = False
    fd = None

    lock_file.parent.mkdir(parents=True, exist_ok=True)
    if HAS_FCNTL and fcntl is not None:
        fd = os.open(str(lock_file), os.O_CREAT | os.O_RDWR)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (BlockingIOError, IOError):
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Zero-Scan: Timed out waiting for file lock on {lock_path}")
                time.sleep(0.05)
    else:
        while True:
            try:
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                acquired = True
                break
            except (FileExistsError, OSError):
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Zero-Scan: Timed out waiting for file lock on {lock_path}")
                time.sleep(0.05)

    try:
        yield
    finally:
        if fd is not None:
            if HAS_FCNTL and fcntl is not None:
                try:
                    fcntl.flock(fd, fcntl.LOCK_UN)
                except Exception:
                    pass
            try:
                os.close(fd)
            except Exception:
                pass
        if not HAS_FCNTL and acquired:
            try:
                lock_file.unlink(missing_ok=True)
            except Exception:
                pass


def find_agent_dir(start_path: Optional[Path] = None, require_existing: bool = False) -> Path:
    """Locate the .agent directory by traversing upwards from start_path."""
    curr = (start_path or Path.cwd()).resolve()
    for p in [curr] + list(curr.parents):
        agent = p / ".agent"
        if agent.is_dir():
            return agent
    fallback = curr / ".agent"
    if require_existing and not fallback.is_dir():
        raise FileNotFoundError(
            f"Zero-Scan: No .agent/ directory found at or above {curr}. "
            "Please initialize with 'zeroscan-bootstrap' first."
        )
    return fallback


def load_json(path: Path, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Resilient JSON reader with backup fallback when files are empty or corrupted."""
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("File is empty (0 bytes)")
            return json.loads(content)
    except Exception as e:
        bak_path = path.with_suffix(path.suffix + ".bak")
        if bak_path.is_file():
            try:
                with open(bak_path, "r", encoding="utf-8") as fb:
                    return json.load(fb)
            except Exception:
                pass
        if default is not None:
            return default
        raise ValueError(f"Corrupted JSON in {path} and no valid .bak recovery available: {e}")


def atomic_write_json(path: Path, data: Dict[str, Any], auto_sync_boot: bool = True) -> None:
    """Atomic write with fsync, file locking, and automatic BOOT.md synchronization."""
    with file_lock(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")

        # Only create .bak backup if existing file has valid non-empty content
        if path.is_file() and path.stat().st_size > 0:
            bak_path = path.with_suffix(path.suffix + ".bak")
            try:
                shutil.copy2(path, bak_path)
            except Exception:
                pass

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        temp_path.replace(path)

        if auto_sync_boot and path.name == "PROJECT_STATE.json":
            sync_boot_anchor(path.parent)


def sync_boot_anchor(agent_dir: Path) -> None:
    """Render and write BOOT.md from current PROJECT_STATE.json to guarantee 0% state drift."""
    state_file = agent_dir / "PROJECT_STATE.json"
    boot_file = agent_dir / "BOOT.md"
    if not state_file.is_file():
        return

    try:
        state = load_json(state_file)
        content = generate_boot_markdown(state)
        temp_boot = boot_file.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
        with open(temp_boot, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        temp_boot.replace(boot_file)
    except Exception:
        pass


def generate_boot_markdown(state: Dict[str, Any]) -> str:
    """Generate minimal Level 0 BOOT.md markdown payload (< 1 KB)."""
    p_name = state.get("project_name", "Unknown Project")
    mission = state.get("mission", "No mission specified.")
    phase = state.get("current_phase") or state.get("phase", "Phase 1 - Initialization")
    active_task = state.get("active_task", "None")
    last_up = state.get("last_updated", datetime.datetime.now(datetime.timezone.utc).isoformat())
    commit_sha = state.get("verified_commit", "INITIAL_STATE")

    return f"""# LEVEL 0 BOOT ANCHOR: {p_name.upper()}
> **Spec Version:** 2.1.2 | **Zero-Scan Hard Budget:** <= 10 KB | **Auto-Synced**

- **Project:** {p_name}
- **Mission:** {mission}
- **Phase:** {phase}
- **Active Task:** {active_task}
- **Verified Commit:** `{commit_sha[:8] if len(commit_sha) >= 8 else commit_sha}`
- **Last Synchronized:** `{last_up}`

## MANDATORY AGENT BOOT PROTOCOL
1. Do NOT scan the entire repository tree.
2. Read `.agent/PROJECT_MAP.json` to navigate only active domain files.
3. Check `.agent/NEXT_TASK.md` for current task acceptance criteria.
4. Check `.agent/DECISIONS.md` for locked architectural constraints.
5. On task completion, commit code to git, then run `zeroscan checkpoint`.
"""


def get_git_commit(repo_root: Path) -> str:
    """Fetch current Git commit hash or return UNCOMMITTED/DIRTY state."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "NO_GIT_COMMIT"


def get_git_status_summary(repo_root: Path) -> Dict[str, Any]:
    """Inspect git branch, commit hash, and dirty status."""
    info = {"commit": "NO_GIT", "branch": "unknown", "is_dirty": False}
    try:
        c_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True)
        if c_res.returncode == 0:
            info["commit"] = c_res.stdout.strip()

        b_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, capture_output=True, text=True)
        if b_res.returncode == 0:
            info["branch"] = b_res.stdout.strip()

        s_res = subprocess.run(["git", "status", "--porcelain"], cwd=repo_root, capture_output=True, text=True)
        if s_res.returncode == 0:
            info["is_dirty"] = bool(s_res.stdout.strip())
    except Exception:
        pass
    return info


def calculate_metrics(agent_dir: Path) -> Dict[str, Any]:
    """Calculate exact bootstrap context bytes and total agent memory footprint."""
    bootstrap_files = ["BOOT.md", "PROJECT_STATE.json", "NEXT_TASK.md"]
    boot_bytes = 0
    file_breakdown = {}

    for bf in bootstrap_files:
        p = agent_dir / bf
        size = p.stat().st_size if p.is_file() else 0
        boot_bytes += size
        file_breakdown[bf] = size

    total_agent_bytes = 0
    if agent_dir.is_dir():
        for p in agent_dir.rglob("*"):
            if p.is_file():
                total_agent_bytes += p.stat().st_size

    pct = round((boot_bytes / MAX_BOOTSTRAP_CONTEXT_BYTES) * 100, 2)
    return {
        "bootstrap_context_bytes": boot_bytes,
        "max_allowed_bytes": MAX_BOOTSTRAP_CONTEXT_BYTES,
        "budget_limit_bytes": MAX_BOOTSTRAP_CONTEXT_BYTES,
        "budget_used_percent": pct,
        "is_within_budget": boot_bytes <= MAX_BOOTSTRAP_CONTEXT_BYTES,
        "total_agent_system_bytes": total_agent_bytes,
        "file_breakdown": file_breakdown,
    }


def record_task_ledger(
    agent_dir: Path,
    task_id: str,
    summary: str,
    evidence: str = "verified",
    phase: Optional[str] = None,
    branch: Optional[str] = None,
    max_active_tasks: int = 50,
) -> None:
    """Append a task to TASK_LEDGER.jsonl and auto-prune to archive if over budget."""
    ledger_file = agent_dir / "TASK_LEDGER.jsonl"
    git_info = get_git_status_summary(agent_dir.parent)
    record = {
        "task_id": task_id,
        "phase": phase or "Active Phase",
        "branch": branch or git_info.get("branch", "master"),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "commit": git_info.get("commit", "UNCOMMITTED"),
        "summary": summary,
        "evidence": evidence,
    }

    with file_lock(ledger_file):
        with open(ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    prune_and_archive_ledger(agent_dir, max_active=max_active_tasks)


def prune_and_archive_ledger(
    agent_dir: Path,
    max_active: int = 50,
    max_tasks: Optional[int] = None,
    keep_recent: int = 20,
) -> int:
    """Archive older completed tasks into .agent/archive/TASK_LEDGER_ARCHIVE.jsonl."""
    limit = max_tasks if max_tasks is not None else max_active
    ledger_file = agent_dir / "TASK_LEDGER.jsonl"
    if not ledger_file.is_file():
        return 0

    with file_lock(ledger_file):
        with open(ledger_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) <= limit:
            return 0

        archive_dir = agent_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_file = archive_dir / "TASK_LEDGER_ARCHIVE.jsonl"

        split_index = max(0, len(lines) - keep_recent)
        to_archive = lines[:split_index]
        to_keep = lines[split_index:]

        with open(archive_file, "a", encoding="utf-8") as fa:
            for item in to_archive:
                fa.write(item + "\n")

        temp_ledger = ledger_file.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
        with open(temp_ledger, "w", encoding="utf-8") as fk:
            for item in to_keep:
                fk.write(item + "\n")
            fk.flush()
            os.fsync(fk.fileno())

        temp_ledger.replace(ledger_file)
        return len(to_archive)


def add_decision_record(
    agent_dir: Path,
    adr_id: str,
    title: str,
    decision: str,
    context: str = "",
    status: str = "LOCKED",
) -> None:
    """Append a new Architectural Decision Record (ADR) to DECISIONS.md."""
    dec_file = agent_dir / "DECISIONS.md"
    today = datetime.date.today().isoformat()
    entry = f"""
## {adr_id}: {title}
- **Date:** {today}
- **Status:** [{status.upper()}]
- **Context:** {context or 'Architectural decision for project governance.'}
- **Decision:** {decision}
"""
    if dec_file.is_file():
        with open(dec_file, "a", encoding="utf-8") as f:
            f.write(entry)
    else:
        with open(dec_file, "w", encoding="utf-8") as f:
            f.write(f"# Architectural Decision Records (ADRs)\n{entry}")

    # Trigger metric update in state
    state_file = agent_dir / "PROJECT_STATE.json"
    if state_file.is_file():
        state = load_json(state_file)
        state["metrics"] = calculate_metrics(agent_dir)
        atomic_write_json(state_file, state, auto_sync_boot=True)


def update_next_task_doc(
    agent_dir: Path,
    task_id: str,
    description: str,
    domains: Optional[List[str]] = None,
    criteria: Optional[List[str]] = None,
) -> None:
    """Update NEXT_TASK.md with full specifications and acceptance criteria."""
    task_file = agent_dir / "NEXT_TASK.md"
    d_list = ", ".join(domains) if domains else "core"
    crit_text = "\n".join([f"- [ ] {c}" for c in (criteria or ["Verify implementation with tests", "Pass validation"])])

    content = f"""# CURRENT ACTIVE TASK: {task_id}

- **Task ID:** `{task_id}`
- **Assigned Domain(s):** `{d_list}`
- **Status:** `IN_PROGRESS`

## Objective & Description
{description}

## Acceptance Criteria
{crit_text}
"""
    temp_task = task_file.with_suffix(f".tmp.{os.getpid()}.{time.time_ns()}")
    with open(temp_task, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    temp_task.replace(task_file)


def validate_agent_memory(agent_dir: Path, strict_git: bool = False) -> Tuple[bool, List[str], List[str]]:
    """Strict specification validator for .agent memory compliance and budget."""
    errors = []
    warnings = []

    required_files = [
        "BOOT.md",
        "PROJECT_STATE.json",
        "PROJECT_MAP.json",
        "DECISIONS.md",
        "NEXT_TASK.md",
        "TASK_LEDGER.jsonl",
    ]

    for rf in required_files:
        p = agent_dir / rf
        if not p.is_file():
            errors.append(f"Missing mandatory file: {rf}")

    metrics = calculate_metrics(agent_dir)
    if not metrics["is_within_budget"]:
        errors.append(
            f"Bootstrap context exceeded budget ceiling: {metrics['bootstrap_context_bytes']} > {MAX_BOOTSTRAP_CONTEXT_BYTES} bytes"
        )

    # Validate PROJECT_STATE.json schema
    state_file = agent_dir / "PROJECT_STATE.json"
    if state_file.is_file():
        try:
            state = load_json(state_file)
            for k in ["project_name", "active_task", "verified_commit"]:
                if k not in state:
                    errors.append(f"PROJECT_STATE.json missing required field: {k}")
            if "phase" not in state and "current_phase" not in state:
                errors.append("PROJECT_STATE.json missing required field: current_phase or phase")
        except Exception as e:
            errors.append(f"PROJECT_STATE.json is invalid JSON: {e}")

    # Check Git synchronization
    git_info = get_git_status_summary(agent_dir.parent)
    if git_info.get("is_dirty"):
        if strict_git:
            errors.append("Strict validation failed: Git working tree is dirty (uncommitted changes).")
        else:
            warnings.append("Git working tree is dirty (uncommitted changes detected).")

    is_valid = len(errors) == 0
    return is_valid, errors, warnings


def cmd_status(args: argparse.Namespace) -> int:
    """Display comprehensive status and metrics."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1

    state_file = agent_dir / "PROJECT_STATE.json"
    state = load_json(state_file, default={})
    metrics = calculate_metrics(agent_dir)
    git_info = get_git_status_summary(agent_dir.parent)

    print("=" * 60)
    print(f"🏛️  ZERO-SCAN PROJECT MEMORY V2.1.2 — STATUS")
    print("=" * 60)
    print(f"Project Name     : {state.get('project_name', 'Unknown')}")
    print(f"Phase            : {state.get('current_phase') or state.get('phase', 'Unknown')}")
    print(f"Active Task      : {state.get('active_task', 'None')}")
    print(f"Active Branch    : {git_info.get('branch', 'unknown')}")
    print(f"Verified Commit  : {git_info.get('commit', 'UNKNOWN')[:8]}")
    print(f"Bootstrap Budget : {metrics['bootstrap_context_bytes']} / {metrics['max_allowed_bytes']} bytes ({metrics['budget_used_percent']}%)")
    print(f"Budget Status    : {'PASSED ✅' if metrics['is_within_budget'] else 'EXCEEDED ❌'}")
    print("=" * 60)
    return 0


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


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate memory integrity against specification."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    print(f"🔍 Validating Project Memory V2.1.2 at: {agent_dir} ...")
    strict = getattr(args, "strict", False)
    is_valid, errors, warnings = validate_agent_memory(agent_dir, strict_git=strict)

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


def cmd_checkpoint(args: argparse.Namespace) -> int:
    """Record completed task, update state, and create memory checkpoint."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1

    task_id = getattr(args, "task_id", None) or f"TASK-{int(time.time())}"
    summary = getattr(args, "summary", None) or getattr(args, "task_summary", None) or "Task completed"
    evidence = getattr(args, "evidence", None) or getattr(args, "test_status", None) or "verified"
    phase = getattr(args, "phase", None)
    status = getattr(args, "status", None)

    record_task_ledger(
        agent_dir=agent_dir,
        task_id=task_id,
        summary=summary,
        evidence=evidence,
        phase=phase,
    )

    state_file = agent_dir / "PROJECT_STATE.json"
    state = load_json(state_file, default={})
    git_info = get_git_status_summary(agent_dir.parent)
    state["verified_commit"] = git_info["commit"]
    state["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if phase:
        if "current_phase" in state:
            state["current_phase"] = phase
        else:
            state["phase"] = phase
    if status:
        state["status"] = status

    next_id = getattr(args, "next_task_id", None) or getattr(args, "next_task", None)
    next_desc = getattr(args, "next_task_desc", None)

    if next_id or next_desc:
        target_next = next_id or "NEXT-TASK"
        state["active_task"] = target_next
        update_next_task_doc(
            agent_dir=agent_dir,
            task_id=target_next,
            description=next_desc or f"Objective for {target_next}",
        )
    elif getattr(args, "active_task", None):
        state["active_task"] = args.active_task

    state["metrics"] = calculate_metrics(agent_dir)
    atomic_write_json(state_file, state, auto_sync_boot=True)
    print(f"✅ Checkpoint recorded for task [{task_id}] bound to Git commit: {git_info['commit'][:8]}")
    return 0


def cmd_add_decision(args: argparse.Namespace) -> int:
    """Record an Architectural Decision Record (ADR) into DECISIONS.md."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    if not agent_dir.is_dir():
        print(f"[ERROR] No .agent directory found at {agent_dir}")
        return 1

    add_decision_record(
        agent_dir=agent_dir,
        adr_id=args.id,
        title=args.title,
        decision=args.decision,
        context=args.context or "",
        status=args.status or "LOCKED",
    )
    print(f"✅ Decision [{args.id}: {args.title}] recorded successfully in DECISIONS.md")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-Scan Project Memory V2.1.2 CLI Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_status = subparsers.add_parser("status", help="Show project memory status and metrics")
    p_status.add_argument("--target", "-t", type=str, help="Target project root directory")

    p_metrics = subparsers.add_parser("metrics", help="Show context budget metrics")
    p_metrics.add_argument("--target", "-t", type=str, help="Target project root directory")
    p_metrics.add_argument("--json", action="store_true", help="Output metrics as JSON")

    p_val = subparsers.add_parser("validate", help="Validate memory files against schema & budget")
    p_val.add_argument("--target", "-t", type=str, help="Target project root directory")
    p_val.add_argument("--strict", action="store_true", help="Enforce strict Git validation (fail on dirty working tree)")

    p_sync = subparsers.add_parser("sync", help="Synchronize BOOT.md and checkpoint git commit")
    p_sync.add_argument("--target", "-t", type=str, help="Target project root directory")

    p_cp = subparsers.add_parser("checkpoint", help="Record task completion and checkpoint state")
    p_cp.add_argument("--task-id", type=str, help="Task ID (e.g. TASK-001)")
    p_cp.add_argument("--summary", "-m", type=str, help="Summary of work completed")
    p_cp.add_argument("--task-summary", type=str, help="Alias for --summary")
    p_cp.add_argument("--evidence", "-e", type=str, help="Evidence or test execution proof")
    p_cp.add_argument("--test-status", type=str, help="Alias for --evidence")
    p_cp.add_argument("--phase", "-p", type=str, help="Current development phase")
    p_cp.add_argument("--status", "-s", type=str, help="Project status (e.g. IN_PROGRESS, COMPLETED)")
    p_cp.add_argument("--next-task", type=str, help="Next task name/id")
    p_cp.add_argument("--next-task-id", type=str, help="Next task ID")
    p_cp.add_argument("--next-task-desc", type=str, help="Next task description")
    p_cp.add_argument("--record-ledger", action="store_true", help="Confirm ledger recording")
    p_cp.add_argument("--target", "-t", type=str, help="Target project root directory")

    p_dec = subparsers.add_parser("add-decision", help="Record a new Architectural Decision Record (ADR)")
    p_dec.add_argument("--id", type=str, required=True, help="ADR ID (e.g. ADR-002)")
    p_dec.add_argument("--title", type=str, required=True, help="ADR Title")
    p_dec.add_argument("--decision", "-d", type=str, required=True, help="The architectural decision")
    p_dec.add_argument("--context", "-c", type=str, help="Problem context / rationale")
    p_dec.add_argument("--status", "-s", type=str, default="LOCKED", help="Status (default: LOCKED)")
    p_dec.add_argument("--target", "-t", type=str, help="Target project root directory")

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    elif args.command == "metrics":
        return cmd_metrics(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "sync":
        return cmd_sync(args)
    elif args.command == "checkpoint":
        return cmd_checkpoint(args)
    elif args.command == "add-decision":
        return cmd_add_decision(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
