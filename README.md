# ZeroScan (`.agent/`) — Project Memory V2.1.2

[![CI Suite](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml/badge.svg)](https://github.com/chauvuusvn/zeroscan/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/badge/pypi-v2.1.2-blue.svg)](https://pypi.org/project/zeroscan/)
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

## 🌟 Overview

**Zero-Scan Project Memory V2.1.2** is an open standard designed to eliminate context bloat, hallucination, and directory-crawling overhead in AI-driven software development.

Traditional coding agents waste tens of thousands of tokens scanning entire codebases upon startup. Project Memory replaces scanning with a lightweight, Git-bound **Level 0 Boot Anchor** (`BOOT.md` < 1 KB) and an architectural **GPS Map** (`PROJECT_MAP.json`), ensuring agents boot instantly with `<= 10 KB` of total context.

```text
┌─────────────────────────────────────────────────────────────┐
│                    ANY LLM / AI AGENT                       │
│  (Claude 3.5 · GPT-4o · Gemini 1.5 · DeepSeek · Qwen · Llama)│
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

## 💡 Why Zero-Scan Outperforms Full Scans

### 1. Zero-Scan Startup (Level 0 Boot Anchor)
Traditional agents ingest entire repositories on every session turn, easily burning 30,000–200,000+ tokens before writing a single line of code. With Zero-Scan, agents **read only `BOOT.md` (~1 KB / ~500 tokens)**, instantly understanding the architecture and current task without touching unrelated files.

### 2. GPS Navigation via `PROJECT_MAP.json`
Instead of running expensive recursive regex greps across the repository, agents query `PROJECT_MAP.json` to navigate directly to the source files and test suites of the active domain.

### 3. Architectural Decision Locking (ADR Invariants)
Critical architectural decisions are recorded in `DECISIONS.md` under `[LOCKED]` status. Agents are strictly prohibited from modifying locked decisions without explicit approval.

### 4. Immutable Evidence Gate & Git SHA Binding
A task is considered `DONE` only when validated with real test execution evidence (`pytest`, `unittest`) and bound to a verifiable Git Commit SHA.

---

## 🛡️ V2.1.2 Enterprise-Grade Engineering Highlights

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
