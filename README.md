# ZeroScan (`.agent/`) — Project Memory V2.1.3

[![CI Suite](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml/badge.svg)](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/badge/pypi-v2.1.3-blue.svg)](https://pypi.org/project/zeroscan/)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub%20Sponsors-ff69b4.svg)](https://github.com/sponsors/chauvuusvn)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![Context Budget](https://img.shields.io/badge/Context%20Budget-%3C=10%20KB-success.svg)](https://github.com/chauvuusvn/zeroscan)

```bash
# Instant Installation via pip
pip install zeroscan

# Instant Bootstrap in any repository
zeroscan-bootstrap --name "my-awesome-project" --mission "Build scalable AI systems"
```

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README.vi.md) | [ 📘 Usage Guide ](USAGE_GUIDE.md) | [ 📕 Hướng dẫn sử dụng ](HUONG_DAN_SU_DUNG.md) | [ 🚀 Deep-Dive Article ](articles/zero-scan-llm-vram-optimization.md)

> **The Universal, Model-Agnostic Context & Memory Protocol for ANY AI Coding Agent**  
> Native support for Claude 3.5, GPT-4o, Gemini 1.5, DeepSeek-V3, Qwen 2.5, Llama 3.3, Cursor, Windsurf, Trae, Codex, and Hermes.

---

## 🌟 Overview & Realistic Scope

**Zero-Scan (`.agent/`)** is a lightweight, Git-bound project state specification designed to eliminate **session bootstrap overhead** and **decision drift** in AI-assisted coding workflows.

### What Zero-Scan Actually Solves:
1. **Eliminates Bootstrap Token Waste:** Instead of letting AI agents (Claude Code, Cursor, Aider, Hermes) blindly scan 50–100 repository files on every session startup (burning 30,000–80,000 tokens each time), the agent reads a single `BOOT.md` file (~500 bytes / ~150 tokens) to instantly know the active task, constraints, and test boundaries.
2. **Zero Startup Latency:** Eliminates initial directory crawling; the agent is ready to work in < 1 second.
3. **Prevents Decision Drift & Regressions:** Externalizes critical architectural invariants and past decisions to `DECISIONS.md` on disk, preventing models from violating approved choices when long conversation contexts auto-compact.
4. **Enables Model Handoff:** Allows architecting with one model (e.g., Claude) and executing implementation tasks with another (e.g., DeepSeek-V3, GPT-4o, Gemini Flash) without losing track of previous decisions.

### What Zero-Scan Does NOT Do (Engineering Reality):
* It does **not** compress actual source code into 10 KB. When an agent writes or debugs code, it still reads/writes source files and consumes standard token budgets.
* It relies on **operational discipline**: The developer or agent must record progress via CLI checkpoints (`zeroscan checkpoint`) to keep on-disk state synchronized with actual code changes.

```text
┌─────────────────────────────────────────────────────────────┐
│                    ANY LLM / AI AGENT                       │
│  (Claude · GPT-4o · Gemini · DeepSeek · Qwen · Llama)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       MCP Protocol Server               CLI Engine
      (Cursor / Windsurf / Trae)      (Terminal / CI/CD)
               │                               │
               └───────────────┬───────────────┘
                               ▼
              ┌─────────────────────────────────┐
              │      Zero-Scan Context Core     │
              │  • Level 0 Boot Anchor (BOOT)   │
              │  • GPS Module Routing (MAP)     │
              │  • Concurrency Locking (flock)  │
              │  • Resilient JSON (.bak)        │
              └────────────────┬────────────────┘
                               ▼
                    TARGET GIT REPOSITORY
```

---

## 💡 Practical Benefits & Engineering Mechanics

### 1. Zero-Scan Startup (`BOOT.md` < 1 KB)
Instead of crawling repositories on every session turn, agents read `BOOT.md` (~150 tokens) to understand project state, skipping expensive preliminary discovery scans.

### 2. Targeted GPS Navigation (`PROJECT_MAP.json`)
Rather than running recursive regex searches across the repo, agents query `PROJECT_MAP.json` to navigate directly to the specific files belonging to the active domain.

### 3. Architectural Invariant Locking (`DECISIONS.md`)
Architectural and security decisions are permanently logged in `DECISIONS.md`. Models cannot silently overwrite or forget past choices during long sessions.

### 4. Immutable Evidence Gate & Git SHA Binding
Tasks are marked `DONE` only when validated with real test execution output (`pytest`, `unittest`) and bound to a verifiable Git Commit SHA.

---

## 🧠 Memory Externalization & Lifecycle Management

### 1. Ground Truth on Disk (Mitigating Context Compaction)
Conversational context windows naturally compact or degrade over long sessions. Zero-Scan anchors project memory directly in deterministic Git files:
- **`BOOT.md` (< 1 KB):** Instant operational awareness (Project goal, active phase, current task, verified commit SHA).
- **`PROJECT_MAP.json`:** Precise GPS file routing for active domains.
- **`DECISIONS.md`:** Non-negotiable architectural rules marked `[LOCKED]`.
- **`TASK_LEDGER.jsonl`:** Append-only record of completed work.

### 2. Auto-Pruning Ledger (Preventing Disk Bloat)
- When `TASK_LEDGER.jsonl` exceeds 50 tasks, older entries are automatically archived to `.agent/archive/TASK_LEDGER_ARCHIVE.jsonl`, keeping the active ledger small ($< 5\text{ KB}$).
- `BOOT.md` is re-rendered atomically from scratch on each checkpoint, never accumulating historical bloat.

### 3. Multi-Model Handoff
- **Session 1 (e.g., Claude):** Implements module $\rightarrow$ verifies tests $\rightarrow$ runs `zeroscan checkpoint`.
- **Session 2 (e.g., GPT-4o / DeepSeek):** Reads `BOOT.md` in < 1 ms and resumes immediately with full context clarity.

---

## 🛡️ V2.1.3 Enterprise-Grade Engineering Highlights

1. **⚡ Atomic State-to-Boot Auto-Sync:** Updating `PROJECT_STATE.json` automatically re-renders `BOOT.md` in real-time, preventing state drift.
2. **🔄 Resilient JSON Loader & `.bak` Fallback:** Automatic recovery from backup snapshots when state files are empty or corrupted.
3. **🔒 Cross-Platform Concurrency Locking:** Multi-agent concurrent write protection using `fcntl.flock` on Unix and atomic spinlocks on Windows with strict timeout exceptions.
4. **🛡️ Atomic Bootstrap Staging & Rollback:** Scaffolding takes place in a temporary staging directory first, ensuring zero data loss if network or generation fails.
5. **📦 Package Data Bundling:** Templates and schemas are packaged directly into the PyPI wheel for 100% offline usage.
6. **📦 Sized Ledger Archiving:** Automatically archives completed tasks to `.agent/archive/` when ledger exceeds 50 entries, keeping the active context $< 5\text{ KB}$.

---

## 📁 The `.agent/` Directory Structure

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

## ⚠️ 8 Common Pitfalls & Recovery Protocols

| # | Pitfall / Anti-Pattern | Root Cause | Real-World Impact | Zero-Scan Defense Protocol |
|---|---|---|---|---|
| **1** | **The Stale State Trap** | Agent completes work but forgets to update `BOOT.md` / `PROJECT_STATE.json`. | Next session restarts from stale state, causing duplicate work. | **Session Exit Gate**: Enforce `zeroscan checkpoint` before turn completion. |
| **2** | **Decisions Bloat Trap** | Accumulating dozens of trivial ADRs in `DECISIONS.md` $> 20\text{ KB}$. | Blows past 10 KB budget, inflating KV-cache VRAM. | **Compaction Protocol**: Stabilized decisions consolidated into axioms; history archived. |
| **3** | **Concurrent State Collision** | Multiple subagents writing to `PROJECT_STATE.json` simultaneously. | Lost updates or corrupted JSON writes. | **Advisory File Lock & Atomic Writes**: `file_lock` context manager + `.tmp.<pid>` + `fsync` + `os.replace`. |
| **4** | **Accidental Full-Scan Drift** | Agent invokes unrestricted `grep -r` across `node_modules` / `venv`. | Floods context window with 100k+ tokens, degrading model attention. | **Strict GPS Routing**: Agents query `PROJECT_MAP.json` to open active domain files only. |
| **5** | **Phantom Commit Binding** | Agent marks task `DONE` without committing code to git first. | State claims task verified, but Git HEAD is uncommitted. | **Git Verification Guard**: `zeroscan validate` checks `git rev-parse HEAD` against recorded hashes. |
| **6** | **Git Branch Drift** | Switching git branches while `.agent/` tracks a different branch. | Agent acts on objectives from another feature branch. | **Branch-Aware Ledger**: Tasks tagged with branch names; `zeroscan sync` aligns state. |
| **7** | **Greedy MCP Context Bleed** | MCP clients fetch full history (50+ tasks) into system prompts. | Token waste and prompt dilution. | **Selective View Filters**: `zeroscan_read_state` defaults to compact mode ($\le 1\text{ KB}$, 3 active tasks). |
| **8** | **Git Rebase Deadlock** | Strict commit verification aborts git rebase or detached HEAD CI builds. | CI/CD build failures during automated squash/merge. | **Non-Blocking Rebase Bypass**: Validator detects `.git/rebase-merge` environments gracefully. |

---

## 🚀 Quickstart & CLI Operations

```bash
# 1. Install via pip
pip install zeroscan

# 2. Bootstrap any repository
zeroscan-bootstrap --name "my-project" --mission "Build Agent Fleet" --domains "core,api,auth,db"

# 3. Check status & validate budget compliance
zeroscan status
zeroscan validate

# 4. Record task completion with evidence & update next task
zeroscan checkpoint --task-id "TASK-001" --summary "Implement auth module" --evidence "pytest 15/15 pass" --next-task-id "TASK-002" --next-task-desc "Build billing API"

# 5. Record an Architectural Decision Record (ADR)
zeroscan add-decision --id "ADR-002" --title "Use PostgreSQL for DB" --decision "Adopt Postgres 16 for ACID compliance"

# 6. Start MCP Server for Cursor / Claude Desktop / Windsurf
zeroscan-mcp
```

---

## 📜 License & Copyright
- **Author:** Chau Vu / CPF-FAMILY (`@chauvuusvn`)
- **License:** MIT License (100% Open Source)
- **PyPI Release:** [https://pypi.org/project/zeroscan/](https://pypi.org/project/zeroscan/)
