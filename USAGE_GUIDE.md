# 📘 Zero-Scan (`.agent/`) Usage Guide — Project Memory V2.2.0

> **Target Audience:** Software Engineers & Autonomous AI Coding Agents (Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek-V3, Qwen 2.5, Llama 3.3, Cursor, Windsurf, Trae, Codex, Hermes).  
> **Standard:** `v2.2.0 (Production / Enterprise Ready)` — Zero External Dependencies (Pure Python 3.9+ Standard Library).  
> **PyPI Distribution:** `pip install zeroscan`

---

## 🎯 1. Overview & Core Mission

The **Zero-Scan Project Memory V2.2.0** (`.agent/`) architecture resolves the four major bottlenecks in AI-driven software development:

1. **Zero Context Waste (Zero-Scan):** New agent sessions do not need to scan 50,000–200,000 LOC. Loading only the **Bootstrap Context (~2.5 KB)** restores 100% context, architecture invariants, and current objectives instantly.
2. **ADR Locking:** Prevents subsequent agent sessions from silently reverting or rewriting architectural decisions locked in `DECISIONS.md`.
3. **Immutable Evidence Gate:** A task is marked `DONE` only when validated with reproducible test executions (`pytest`, `unittest`) and bound to a verifiable Git Commit SHA.
4. **Self-Healing & Concurrency Engine:** Cross-platform advisory file locking (`fcntl.flock` + Windows spinlock), automatic state-to-boot synchronization, and resilient `.bak` JSON recovery.

---

## 📁 2. The `.agent/` Directory Architecture

```text
.agent/
├── BOOT.md              # [MANDATORY FIRST READ] Level 0 session boot anchor (< 1 KB)
├── PROJECT_STATE.json   # Repo state machine (bound to code_commit and memory_commit)
├── PROJECT_MAP.json     # Codebase GPS map: Domain -> File Paths -> Test Suites
├── DECISIONS.md         # Active Architectural Decision Records (ADRs) marked [LOCKED]
├── NEXT_TASK.md         # Detailed specification of active task, domains & acceptance criteria
├── TASK_LEDGER.jsonl    # Append-only immutable task ledger
├── MEMORY_PROTOCOL.md   # 10 mandatory agent behavioral rules
├── memory.py            # Core CLI engine for validation, metrics, and state synchronization
└── archive/             # Automated archive directory for completed tasks (> 50 items)
```

---

## 🚀 3. Installation & Global CLI Operations

### A. Install from PyPI
```bash
pip install zeroscan
```

### B. Scaffold `.agent/` for any repository
```bash
zeroscan-bootstrap --name "my-awesome-project" --mission "Build scalable AI systems" --domains "core,auth,api,db"
```

### C. Core CLI Commands
```bash
# 1. Check status and schema compliance
zeroscan status
zeroscan validate
zeroscan validate --strict

# 2. Inspect context budget metrics
zeroscan metrics
zeroscan metrics --json

# 3. Checkpoint task completion and update next task
zeroscan checkpoint --task-id "TASK-001" --summary "Implement auth module" --evidence "pytest 15/15 pass" --next-task-id "TASK-002" --next-task-desc "Build billing API"

# 4. Record an Architectural Decision Record (ADR)
zeroscan add-decision --id "ADR-002" --title "Use PostgreSQL for DB" --decision "Adopt Postgres 16 for ACID compliance"

# 5. Synchronize BOOT.md and checkpoint git commit
zeroscan sync

# 6. Start MCP Server for Claude Desktop / Cursor / Windsurf
zeroscan-mcp
```

---

## 📊 4. Context Budget Metrics

| Metric | Definition | Threshold | Actual Zero-Scan V2.2.0 |
|---|---|---|---|
| **`BOOTSTRAP_CONTEXT_BYTES`** | Total bytes of `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` | $\le$ **10,240 bytes (10 KB)** | **~2,400 bytes (23.5%)** |
| **`TOTAL_AGENT_SYSTEM_BYTES`** | Full `.agent/` directory footprint (helpers, protocols, ADRs) | Informational | **~29.4 KB** |

---

## 🔒 5. The 10 Golden Rules (Memory Protocol)

1. **Read `BOOT.md` First:** Never begin a session by recursively scanning the codebase.
2. **Verify Git Sync:** Always execute `zeroscan validate` before writing code.
3. **Route via `PROJECT_MAP.json`:** Open only the files belonging to the active task domain.
4. **Honor `[LOCKED]` Decisions:** Never modify locked ADRs in `DECISIONS.md`.
5. **Evidence Gate:** Never mark a task `DONE` without passing test execution logs.
6. **No Fabricated Output:** Ground truth resides in source files, logs, and Git commits.
7. **Separate Code and Memory Commits:** Commit code first, record SHA in memory checkpoint second.
8. **Append-Only Task Ledger:** Never delete or alter previous records in `TASK_LEDGER.jsonl`.
9. **Zero-Scan Resume:** Every new session must resume cleanly from `.agent/` alone.
10. **Honest Reporting:** Accurately report token metrics and exact test diffs.

---

## ⚠️ 6. 8 Common Pitfalls & Recovery Protocols

### Pitfall 1: Phantom Commits (Uncommitted Task Completion)
* **Symptom:** Task marked complete in ledger, but no matching Git commit exists.
* **Recovery:** Run `zeroscan validate`. Commit working tree changes first: `git add . && git commit -m "fix: complete task"`, then re-checkpoint.

### Pitfall 2: Decisions Bloat
* **Symptom:** `DECISIONS.md` exceeds 20 KB over long sprints.
* **Recovery:** Apply Compaction Protocol: Consolidate stabilized invariants into `PROJECT_STATE.json`, archive historical ADRs to `DECISIONS_ARCHIVE.md`.

### Pitfall 3: Multi-Agent Race Conditions
* **Symptom:** Parallel subagents write simultaneously to state files causing lost updates.
* **Recovery:** Engine enforces cross-platform advisory file locking (`file_lock()` + `.tmp.<pid>` + `os.replace` + `fsync`).

### Pitfall 4: Accidental Full-Scan Drift
* **Symptom:** Agent runs unrestricted recursive grep across `node_modules` or `venv`.
* **Recovery:** Use `PROJECT_MAP.json` GPS routing to target domain files directly.

### Pitfall 5: Git Branch & Worktree Drift
* **Symptom:** Switching branches leaves `.agent/` tracking a different branch.
* **Recovery:** Run `zeroscan sync` to align `BOOT.md` with the active checked-out branch.

### Pitfall 6: Greedy MCP Context Bleed
* **Symptom:** MCP clients inject full 50-task ledger history into prompts.
* **Recovery:** Use `zeroscan_read_state` in default `compact` mode ($\le 1\text{ KB}$ payload, 3 active tasks).

### Pitfall 7: Git Rebase & Detached HEAD Deadlock
* **Symptom:** Pre-commit validation blocks automated CI rebase or squash merges.
* **Recovery:** Validator detects `.git/rebase-merge` environments and permits transient non-blocking passthrough.

### Pitfall 8: Corrupted JSON Crash
* **Symptom:** `PROJECT_STATE.json` becomes 0 bytes or malformed due to abrupt termination.
* **Recovery:** Resilient loader automatically falls back to `.bak` snapshot.
