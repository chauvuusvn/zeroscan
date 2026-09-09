# 📘 Project Memory V2.0 (`.agent/`) — Complete Usage Guide

> **Audience:** AI Coding Agents (Hermes, Claude Code, OpenAI Codex, OpenCode) & Software Engineers.  
> **Standard:** `v2.0 (Frozen Standard)` — Zero External Dependencies (Pure Python 3.11+ Stdlib).

---

## 🎯 1. Core Mission & Objectives

The **Project Memory V2.0** standard (`.agent/`) is engineered to solve the 3 largest bottlenecks in AI-driven software development:

1. **Eliminate Context & Token Bloat (Zero-Scan):** New agent sessions do NOT need to crawl 50,000–100,000 lines of codebase. Ingesting the **Bootstrap Context (~2.5 KB)** is sufficient to grasp repository state, architecture, and active tasks.
2. **Lock Architectural Decisions (ADR Locking):** Prevents downstream agents from spontaneously refactoring or violating established core architectural decisions.
3. **Prevent Hallucinated Progress (Evidence Gate):** Tasks are marked `DONE` ONLY when backed by verifiable test execution evidence (`pytest`, `unittest`, `vitest`) linked directly to a verified Git commit hash.

---

## 📁 2. Memory Structure (`.agent/`)

Every standardized repository contains an `.agent/` directory with 8 core components:

```text
.agent/
├── BOOT.md              # [MANDATORY SESSION BOOT] Level 0 session anchor file (< 1 KB)
├── PROJECT_STATE.json   # State machine (bound to verified Git code_commit & memory_commit)
├── PROJECT_MAP.json     # Architectural GPS map: Domains -> File Paths -> Tests
├── DECISIONS.md         # Immutable Architectural Decision Records (ADRs) in [LOCKED] status
├── NEXT_TASK.md         # Active task specification, involved domains & acceptance criteria
├── TASK_LEDGER.jsonl    # Immutable append-only audit ledger recording completed tasks
├── MEMORY_PROTOCOL.md   # 10 mandatory protocol rules enforced for autonomous agents
└── memory.py            # Zero-dependency CLI engine for validation, metrics, and checkpoints
```

---

## 🚀 3. CLI Quickstart & Setup

### A. Scaffolding a New Repository (`bootstrap.py`)

#### Option 1: Direct One-Liner (No repo cloning required)
```bash
curl -fsSL https://raw.githubusercontent.com/chauvuusvn/zeroscan/master/bootstrap.py | python3 - \
  --target /path/to/my-project \
  --name "MyProject" \
  --mission "Core mission objective of the project" \
  --phase "1" \
  --domains "core-engine,api-gateway,storage,test-suite" \
  --git-init
```

#### Option 2: Run Locally
From the `zeroscan` root directory:
```bash
python3 bootstrap.py \
  --target /path/to/my-project \
  --name "MyProject" \
  --mission "Core mission objective of the project" \
  --phase "1" \
  --domains "core-engine,api-gateway,storage,test-suite"
```

*Additional options:*
* `--git-init`: Automatically initialize a git repository if absent.
* `--force`: Overwrite existing `.agent/` files.

---

### B. Daily Operations & CLI Commands (`.agent/memory.py`)

Inside any repository equipped with `.agent/`:

#### 1. View Project Status Dashboard
```bash
python3 .agent/memory.py status
```
*Outputs current phase, verified commit, active task, test status, and bootstrap context token budget.*

#### 2. Validate Memory Integrity & Git Sync
```bash
python3 .agent/memory.py validate
```
*Validates:*
* All 8 required memory files are present.
* `BOOTSTRAP_CONTEXT_BYTES` stays strictly `<= 10 KB`.
* Git HEAD matches verified commit state. Flags desync if untracked changes exist.

#### 3. Save a Verified Checkpoint
Once coding and test execution pass:
```bash
python3 .agent/memory.py checkpoint \
  --task-id "TASK-001" \
  --evidence "pytest: 18 passed in 0.42s" \
  --next-task "TASK-002"
```

#### 4. Lock an Architectural Decision (ADR)
```bash
python3 .agent/memory.py add-decision \
  --id "ADR-002" \
  --title "Adopt DuckDB for In-Process OLAP" \
  --choice "DuckDB" \
  --rationale "Ultra low-latency analytics without separate server infrastructure."
```

#### 5. Synchronize GPS Map (`PROJECT_MAP.json`)
```bash
python3 .agent/memory.py sync-map
```
*Scans codebase and keeps domain file mappings up-to-date.*

---

## 🔄 4. Standard 5-Step Agent Workflow

All autonomous AI agents follow a strict 5-step lifecycle:

```text
  ┌────────────────────────────────────────────────────────┐
  │ STEP 1: BOOT SESSION                                   │
  │ • Ingest ONLY `.agent/BOOT.md` (< 1 KB / ~500 tokens) │
  │ • Grasp Mission, Phase, Constraints & Active Task      │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ STEP 2: VALIDATE STATE                                 │
  │ • Run: `python3 .agent/memory.py validate`             │
  │ • If [IN_SYNC] -> Proceed                              │
  │ • If [DESYNC] -> Inspect git diff of desynced files    │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ STEP 3: DOMAIN LOOKUP & SELECTIVE READ                 │
  │ • Read `.agent/NEXT_TASK.md` for target Domain         │
  │ • Query `.agent/PROJECT_MAP.json` for 2–3 target files │
  │ • DO NOT perform blind recursive scans                 │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ STEP 4: EXECUTE & TEST                                 │
  │ • Implement code changes / bugfixes                    │
  │ • Execute real test suite (must be 100% PASS)          │
  └──────────────────────────┬─────────────────────────────┘
                             ↓
  ┌────────────────────────────────────────────────────────┐
  │ STEP 5: COMMIT & CHECKPOINT                            │
  │ • `git add <files> && git commit -m "..."`             │
  │ • `python3 .agent/memory.py checkpoint ...`            │
  └────────────────────────────────────────────────────────┘
```

---

## 🛡️ 5. Zero-Scan Invariant Rules

1. **The 10 KB Budget Ceiling:** The combined size of `BOOT.md`, `PROJECT_STATE.json`, and `NEXT_TASK.md` must never exceed 10 KB.
2. **Deterministic Evidence:** Never update task status to `DONE` without attaching real execution log output and a verified Git commit hash.
3. **ADR Immutability:** Any decision marked `[LOCKED]` in `DECISIONS.md` cannot be overridden without explicit user approval.
