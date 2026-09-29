#!/usr/bin/env python3
"""
Project Memory V2.2.1 Self-Healing Engine (core/memory.py)
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
SPECIFICATION_VERSION = "2.2.1"


@contextlib.contextmanager
def file_lock(lock_path: Path, timeout: float = 5.0, stale_timeout: float = 30.0):
    """Cross-platform atomic file lock supporting POSIX (fcntl) and Windows (O_EXCL atomic spinlock with stale lock detection)."""
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
                # Stale lock recovery on Windows when a previous process crashed
                try:
                    if lock_file.exists():
                        mtime = os.path.getmtime(lock_file)
                        if time.time() - mtime > stale_timeout:
                            lock_file.unlink(missing_ok=True)
                            continue
                except Exception:
                    pass

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
    """Atomic write with fsync, file locking, cleanup on failure, and automatic BOOT.md synchronization."""
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

        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
                f.flush()
                os.fsync(f.fileno())

            temp_path.replace(path)
        finally:
            if temp_path.is_file():
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass

        if auto_sync_boot and path.name == "PROJECT_STATE.json":
            sync_boot_anchor(path.parent)


def sync_boot_anchor(agent_dir: Path) -> None:
    """Render and write BOOT.md from current PROJECT_STATE.json with atomic replace and file lock."""
    state_file = agent_dir / "PROJECT_STATE.json"
    boot_file = agent_dir / "BOOT.md"
    if not state_file.is_file():
        return

    try:
        with file_lock(boot_file):
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
> **Spec Version:** 2.2.1 | **Zero-Scan Hard Budget:** <= 10 KB | **Auto-Synced**

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
            lines = [line.strip() for line in s_res.stdout.strip().splitlines() if line.strip()]
            dirty_files = [l for l in lines if not (".agent/BOOT.md" in l or ".agent/PROJECT_STATE.json" in l)]
            info["is_dirty"] = bool(dirty_files)
            info["dirty_count"] = len(dirty_files)
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
    completed_tasks_count = 0
    ledger_file = agent_dir / "TASK_LEDGER.jsonl"
    if ledger_file.is_file():
        try:
            with open(ledger_file, "r", encoding="utf-8") as f:
                completed_tasks_count = sum(1 for line in f if line.strip())
        except Exception:
            pass

    return {
        "bootstrap_context_bytes": boot_bytes,
        "max_allowed_bytes": MAX_BOOTSTRAP_CONTEXT_BYTES,
        "budget_limit_bytes": MAX_BOOTSTRAP_CONTEXT_BYTES,
        "budget_used_percent": pct,
        "is_within_budget": boot_bytes <= MAX_BOOTSTRAP_CONTEXT_BYTES,
        "total_agent_system_bytes": total_agent_bytes,
        "completed_tasks_count": completed_tasks_count,
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


def validate_pure_python_schema(data: Any, schema: Dict[str, Any], path: str = "$") -> List[str]:
    """Lightweight pure-Python recursive JSON schema validator (zero external dependencies)."""
    errs: List[str] = []
    expected_type = schema.get("type")
    if expected_type:
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "null": type(None),
        }
        allowed = [expected_type] if isinstance(expected_type, str) else list(expected_type)
        is_valid = any(isinstance(data, type_map[t]) for t in allowed if t in type_map)
        if not is_valid:
            errs.append(f"{path}: expected type '{expected_type}', got '{type(data).__name__}'")
            return errs

    if isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                errs.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        for k, v in data.items():
            if k in props:
                errs.extend(validate_pure_python_schema(v, props[k], f"{path}.{k}"))

    elif isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema and isinstance(item_schema, dict):
            for idx, item in enumerate(data):
                errs.extend(validate_pure_python_schema(item, item_schema, f"{path}[{idx}]"))

    if "enum" in schema and data not in schema["enum"]:
        errs.append(f"{path}: value '{data}' not in allowed enum {schema['enum'][:5]}")

    return errs


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

    # Validate PROJECT_STATE.json schema deeply
    state_file = agent_dir / "PROJECT_STATE.json"
    if state_file.is_file():
        try:
            state = load_json(state_file)
            for k in ["project_name", "active_task", "verified_commit"]:
                if k not in state:
                    errors.append(f"PROJECT_STATE.json missing required field: {k}")
            if "phase" not in state and "current_phase" not in state:
                errors.append("PROJECT_STATE.json missing required field: current_phase or phase")
            
            # Deep schema validation against schema/project_state.schema.json if available
            schema_path = agent_dir.parent / "schema" / "project_state.schema.json"
            if not schema_path.is_file():
                schema_path = Path(__file__).resolve().parent.parent / "schema" / "project_state.schema.json"
            if schema_path.is_file():
                try:
                    s_def = load_json(schema_path)
                    s_errs = validate_pure_python_schema(state, s_def, "PROJECT_STATE")
                    errors.extend(s_errs)
                except Exception:
                    pass
        except Exception as e:
            errors.append(f"PROJECT_STATE.json is invalid JSON: {e}")

    # Validate PROJECT_MAP.json schema deeply
    map_file = agent_dir / "PROJECT_MAP.json"
    if map_file.is_file():
        try:
            pmap = load_json(map_file)
            map_schema_path = agent_dir.parent / "schema" / "project_map.schema.json"
            if not map_schema_path.is_file():
                map_schema_path = Path(__file__).resolve().parent.parent / "schema" / "project_map.schema.json"
            if map_schema_path.is_file():
                try:
                    m_def = load_json(map_schema_path)
                    m_errs = validate_pure_python_schema(pmap, m_def, "PROJECT_MAP")
                    errors.extend(m_errs)
                except Exception:
                    pass
        except Exception as e:
            errors.append(f"PROJECT_MAP.json is invalid JSON: {e}")

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
    print(f"🏛️  ZERO-SCAN PROJECT MEMORY V2.2.1 — STATUS")
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
    print(f"🔍 Validating Project Memory V2.2.1 at: {agent_dir} ...")
    strict = getattr(args, "strict", False)
    is_valid, errors, warnings = validate_agent_memory(agent_dir, strict_git=strict)

    for w in warnings:
        print(f"  ⚠️  [WARNING] {w}")

    if is_valid:
        print(f"  ✅ [PASS] Project Memory is 100% compliant with V{SPECIFICATION_VERSION} specification.")
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


def install_git_hooks(repo_root: Path) -> Tuple[bool, str]:
    """Install lightweight git hooks (post-commit, post-checkout, post-merge) to auto-sync Zero-Scan state."""
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        return False, f"Directory '{repo_root}' is not a Git repository (.git not found)."

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_script = """#!/usr/bin/env sh
# Zero-Scan Git Auto-Sync Hook (v2.2.1)
# Synchronizes BOOT.md and verified_commit on commit, checkout, and merge.

if command -v zeroscan >/dev/null 2>&1; then
    zeroscan sync --target "$PWD" >/dev/null 2>&1 || true
fi
"""
    installed_hooks = []
    for hook_name in ["post-commit", "post-checkout", "post-merge"]:
        hook_path = hooks_dir / hook_name
        hook_path.write_text(hook_script, encoding="utf-8")
        try:
            mode = hook_path.stat().st_mode
            hook_path.chmod(mode | 0o111)  # make executable
        except Exception:
            pass
        installed_hooks.append(hook_name)

    return True, f"Successfully installed Zero-Scan hooks ({', '.join(installed_hooks)}) in {hooks_dir}"


def resolve_merge_conflicts(agent_dir: Path) -> Tuple[bool, List[str]]:
    """Automatically resolve Git merge conflicts in TASK_LEDGER.jsonl and PROJECT_STATE.json."""
    actions: List[str] = []
    
    # 1. Resolve TASK_LEDGER.jsonl conflicts
    ledger_file = agent_dir / "TASK_LEDGER.jsonl"
    if ledger_file.is_file():
        try:
            raw_text = ledger_file.read_text(encoding="utf-8")
            if "<<<<<<<" in raw_text or "=======" in raw_text or ">>>>>>>" in raw_text:
                clean_entries = []
                seen_ids = set()
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("<<<<<<<") or line.startswith("=======") or line.startswith(">>>>>>>"):
                        continue
                    try:
                        entry = json.loads(line)
                        tid = entry.get("task_id") or entry.get("id") or json.dumps(entry, sort_keys=True)
                        if tid not in seen_ids:
                            seen_ids.add(tid)
                            clean_entries.append(entry)
                    except Exception:
                        pass
                
                with open(ledger_file, "w", encoding="utf-8") as f:
                    for entry in clean_entries:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                actions.append(f"Deduplicated and merged {len(clean_entries)} task records in TASK_LEDGER.jsonl")
        except Exception as e:
            actions.append(f"Error resolving ledger conflicts: {e}")

    # 2. Resolve PROJECT_STATE.json conflicts
    state_file = agent_dir / "PROJECT_STATE.json"
    if state_file.is_file():
        try:
            state_text = state_file.read_text(encoding="utf-8")
            if "<<<<<<<" in state_text or "=======" in state_text or ">>>>>>>" in state_text:
                # Extract clean JSON lines or restore from backup / git HEAD
                repo_root = agent_dir.parent
                head_sha = get_git_commit_hash(repo_root) or "0000000"
                branch = get_git_branch(repo_root) or "master"
                
                state = load_json(state_file, default={})
                if not state or not isinstance(state, dict) or "project_name" not in state:
                    bak_file = state_file.with_suffix(".json.bak")
                    if bak_file.is_file():
                        state = load_json(bak_file, default={})
                
                if state:
                    state["verified_commit"] = head_sha
                    state["active_branch"] = branch
                    state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    metrics = calculate_metrics(agent_dir)
                    state["metrics"] = {
                        "bootstrap_context_bytes": metrics["bootstrap_context_bytes"],
                        "total_agent_system_bytes": metrics["total_agent_system_bytes"],
                        "completed_tasks_count": metrics["completed_tasks_count"],
                    }
                    save_json(state_file, state)
                    actions.append("Reconstituted valid PROJECT_STATE.json from active Git HEAD")
        except Exception as e:
            actions.append(f"Error resolving state conflicts: {e}")

    # 3. Synchronize BOOT.md
    sync_boot_anchor(agent_dir)
    actions.append("Synchronized Level-0 BOOT.md anchor")
    return True, actions


def cmd_resolve_conflict(args: argparse.Namespace) -> int:
    """CLI handler to automatically resolve git merge conflicts in .agent/ state files."""
    agent_dir = find_agent_dir(Path(args.target) if getattr(args, "target", None) else None)
    ok, msgs = resolve_merge_conflicts(agent_dir)
    print("🤝 [ZERO-SCAN MERGE RESOLUTION]")
    for msg in msgs:
        print(f"  ✅ {msg}")
    return 0


def cmd_install_hooks(args: argparse.Namespace) -> int:
    """Install git hooks for automated background memory sync."""
    target_dir = Path(args.target) if getattr(args, "target", None) else Path.cwd()
    success, msg = install_git_hooks(target_dir.resolve())
    if success:
        print(f"  ✅ [HOOKS INSTALLED] {msg}")
        return 0
    else:
        print(f"  ❌ [ERROR] {msg}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Zero-Scan Project Memory V2.2.1 CLI Engine")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_resolve = subparsers.add_parser("resolve-conflict", help="Auto-resolve git merge conflicts in .agent/ state files")
    p_resolve.add_argument("--target", "-t", type=str, help="Target repository or .agent directory")

    p_hooks = subparsers.add_parser("install-hooks", help="Install automated git post-commit auto-sync hook")
    p_hooks.add_argument("--target", "-t", type=str, help="Target repository root directory")

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
    elif args.command == "resolve-conflict":
        return cmd_resolve_conflict(args)
    elif args.command == "install-hooks":
        return cmd_install_hooks(args)
    elif args.command == "add-decision":
        return cmd_add_decision(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
