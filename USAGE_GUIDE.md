# 📘 Zero-Scan (`.agent/`) Usage Guide — Project Memory V2.2.1

> **Target Audience:** Software Engineers & Autonomous AI Coding Agents (Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek-V3, Qwen 2.5, Llama 3.3, Cursor, Windsurf, Trae, Codex, Hermes).  
> **Standard:** `v2.2.1 (Production / Enterprise Ready)` — Zero External Dependencies (Pure Python 3.9+ Standard Library).  
> **PyPI Distribution:** `pip install --upgrade zeroscan`

---

## 🎯 1. Overview & Core Mission

The **Zero-Scan Project Memory V2.2.1** (`.agent/`) architecture resolves the four major bottlenecks in AI-driven software development:

1. **Zero Context Waste (Zero-Scan):** New agent sessions do not need to scan 50,000–200,000 LOC. Loading only the **Bootstrap Context (~2.5 KB)** restores 100% context, architecture invariants, and current objectives instantly.
2. **ADR Locking:** Prevents subsequent agent sessions from silently reverting or rewriting architectural decisions locked in `DECISIONS.md`.
3. **Immutable Evidence Gate:** A task is marked `DONE` only when validated with reproducible test executions (`pytest`, `unittest`) and bound to a verifiable Git Commit SHA.
4. **Self-Healing & Concurrency Engine:** Cross-platform advisory file locking (`fcntl.flock` + Windows spinlock with 30s stale recovery), atomic replacements on all state files (including `BOOT.md`), and automated Git hook synchronization.

---

## 📁 2. The `.agent/` Directory Architecture

```text
.agent/
├── BOOT.md              # [MANDATORY FIRST READ] Level 0 session boot anchor (< 1 KB)
├── PROJECT_STATE.json   # Repo state machine (bound to code_commit and memory_commit)
├── PROJECT_MAP.json     # Codebase GPS map: Domain -> File Paths -> Test Suites
├── DECISIONS.md         # Active Architectural Decision Records (ADRs) marked [LOCKED]
├── NEXT_TASK.md         # Detailed specification of active task, domains & acceptance criteria
├── TASK_LEDGER.jsonl    # Append-only immutable historical record of completed tasks
└── memory.py            # Zero-dependency governance and metrics engine (stdlib only)
```

---

## 🛠️ 3. Installation & CLI Command Reference

### Quick Installation via pip:
```bash
pip install --upgrade zeroscan
```

### CLI Commands:
```bash
# 1. Bootstrap Zero-Scan in any existing repository
zeroscan-bootstrap --name "my-project" --mission "Build enterprise AI systems"

# 2. Install Git Post-Commit Auto-Sync Hook (v2.2.1 New Feature)
zeroscan install-hooks

# 3. View context budget metrics and real-time status
zeroscan status
zeroscan metrics

# 4. Strictly validate system integrity against JSON Schema
zeroscan validate --strict

# 5. Checkpoint completed task and atomically update state
zeroscan checkpoint \
  --task "TASK-102" \
  --desc "Implement resilient JWT auth" \
  --commit "8a9f3b2" \
  --next-task "TASK-103" \
  --next-desc "Add OAuth2 provider integration"

# 6. Add and lock Architectural Decision Record (ADR)
zeroscan add-decision \
  --id "ADR-014" \
  --title "Adopt Pure-Python Schema Validation" \
  --decision "Enforce zero-external-dependencies policy" \
  --context "Preserve fast startup and zero supply-chain risk" \
  --status "LOCKED"

# 7. Start Model Context Protocol (MCP) Server for Cursor / Windsurf / Claude Desktop
zeroscan-mcp
```

---

## 🌟 4. Enterprise-Grade Invariants in V2.2.1

1. **Automated Git Hook Auto-Sync (`zeroscan install-hooks`):**
   - Automatically provisions `.git/hooks/post-commit`.
   - On every developer or agent `git commit`, `zeroscan sync` runs in the background, updating `BOOT.md` and `verified_commit` in real-time with **0% State Drift**.
2. **Pure-Python Recursive Schema Validator:**
   - Features a built-in recursive JSON schema validator (`validate_pure_python_schema`) with zero external dependencies (`jsonschema` not required).
   - Deeply validates all required fields, data types, nested objects, and arrays against `schema/project_state.schema.json`.
3. **Full Concurrency Locking for `BOOT.md` & `PROJECT_STATE.json`:**
   - Both machine-readable state and human-readable boot anchors are wrapped in `file_lock()` with atomic `.tmp.{pid}.{timestamp}` $\rightarrow$ `replace()` semantics, preventing partial writes during parallel multi-agent swarms.
4. **Dynamic Workspace Discovery:**
   - MCP Server automatically inspects `ZEROSCAN_PROJECT_ROOT` and `WORKSPACE_FOLDER` environment variables before falling back to `cwd`.

---

## 📊 5. Context Budget Metrics

| Metric | Definition | Threshold | Actual Zero-Scan V2.2.1 |
|---|---|---|---|
| **`BOOTSTRAP_CONTEXT_BYTES`** | Total bytes of `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` | $\le$ **10,240 bytes (10 KB)** | **~2,360 bytes (23.1%)** |
| **`TOTAL_AGENT_SYSTEM_BYTES`** | Full `.agent/` directory footprint (helpers, protocols, ADRs) | Informational | **~29.4 KB** |
| **`KV_CACHE_SAVINGS`** | Reduction in GPU VRAM allocation vs full recursive scan | $\ge$ **95.0%** | **97.5% – 99.0%** |

---

## 🔒 6. The 10 Golden Rules (Memory Protocol)

1. **Read `BOOT.md` First:** Never begin a session by recursively scanning the codebase.
2. **Install Git Hooks:** Run `zeroscan install-hooks` to guarantee real-time commit synchronization.
3. **Route via `PROJECT_MAP.json`:** Open only the files belonging to the active task domain.
4. **Honor `[LOCKED]` Decisions:** Never modify locked ADRs in `DECISIONS.md`.
5. **Evidence Gate:** Never mark a task `DONE` without passing test execution logs.
6. **No Fabricated Output:** Ground truth resides in source files, logs, and Git commits.
7. **Separate Code and Memory Commits:** Commit code first, record SHA in memory checkpoint second.
8. **Append-Only Task Ledger:** Never delete or alter previous records in `TASK_LEDGER.jsonl`.
9. **Zero-Scan Resume:** Every new session must resume cleanly from `.agent/` alone.
10. **Honest Reporting:** Accurately report token metrics and exact test diffs.

---

## ⚠️ 7. 8 Common Pitfalls & Recovery Protocols

### Pitfall 1: Phantom Commits (Uncommitted Task Completion)
* **Symptom:** Task marked complete in ledger, but no matching Git commit exists.
* **Recovery:** Run `zeroscan validate`. Commit working tree changes first: `git add . && git commit -m "fix: complete task"`, then re-checkpoint.

### Pitfall 2: Decisions Bloat
* **Symptom:** `DECISIONS.md` exceeds 20 KB over long sprints.
* **Recovery:** Apply Compaction Protocol: Consolidate stabilized invariants into `PROJECT_STATE.json`, archive historical ADRs to `DECISIONS_ARCHIVE.md`.

### Pitfall 3: Multi-Agent Race Conditions
* **Symptom:** Parallel subagents write simultaneously to state files causing lost updates.
* **Recovery:** Engine enforces cross-platform advisory file locking (`file_lock()` + `.tmp.<pid>` + `os.replace` + `fsync` on all state and markdown files).

### Pitfall 4: Accidental Full-Scan Drift
* **Symptom:** Agent runs unrestricted recursive grep across `node_modules` or `venv`.
* **Recovery:** Use `PROJECT_MAP.json` GPS routing to target domain files directly.

### Pitfall 5: Git Branch & Worktree Drift
* **Symptom:** Switching branches leaves `.agent/` tracking a different branch.
* **Recovery:** Run `zeroscan sync` (or trigger post-commit hook) to align `BOOT.md` with the active checked-out branch.

### Pitfall 6: Greedy MCP Context Bleed
* **Symptom:** MCP clients inject full 50-task ledger history into prompts.
* **Recovery:** Use `zeroscan_read_state` in default `compact` mode ($\le 1\text{ KB}$ payload, 3 active tasks).

### Pitfall 7: Git Rebase & Detached HEAD Deadlock
* **Symptom:** Pre-commit validation blocks automated CI rebase or squash merges.
* **Recovery:** Validator detects `.git/rebase-merge` environments and permits transient non-blocking passthrough.

### Pitfall 8: Corrupted JSON Crash
* **Symptom:** `PROJECT_STATE.json` becomes 0 bytes or malformed due to abrupt termination.
* **Recovery:** Resilient loader automatically falls back to `.bak` snapshot and recreates state safely.
