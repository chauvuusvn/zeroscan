# Project Memory V2.0 Template & Generator (`.agent/`)

> **The Zero-Scan, Git-Aware Context Engine for AI Coding Agents**  
> Compatible with Hermes Agent, Claude Code, OpenAI Codex, and OpenCode.

---

## 🌟 Overview

**Project Memory V2.0** is an open standard designed to eliminate context bloat, hallucination, and directory-crawling overhead in AI-driven software development.

Traditional coding agents waste tens of thousands of tokens scanning entire codebases upon startup. Project Memory replaces scanning with a lightweight, Git-bound **Level 0 Boot Anchor** (`BOOT.md` < 1 KB) and an architectural **GPS Map** (`PROJECT_MAP.json`), ensuring agents boot instantly with `<= 10 KB` of total context.

---

## 📁 Standard `.agent/` Architecture

Every compliant project contains an `.agent/` directory with the following structure:

```
.agent/
├── BOOT.md               # [Level 0] Ultra-light session anchor (< 1 KB / ~30 lines)
├── PROJECT_STATE.json    # [Level 1] Machine state tied to git verified_commit & metrics
├── PROJECT_MAP.json      # Codebase GPS: Maps functional domains to files & tests
├── DECISIONS.md          # Architectural Decision Records (ADRs) with [LOCKED] status
├── TASK_LEDGER.jsonl     # Immutable append-only record of completed tasks & evidence
├── NEXT_TASK.md          # Concrete active task spec, acceptance criteria & test commands
├── MEMORY_PROTOCOL.md    # The 10 Golden Rules for agent execution & evidence verification
└── memory.py             # Pure Python 3.11+ zero-dependency engine (validate, checkpoint, status)
```

---

## 🚀 Quick Start: Scaffolding a New Project

Use `bootstrap.py` to generate a standard `.agent/` memory system in any target repository:

```bash
# Basic usage in current directory
python3 bootstrap.py

# Custom scaffolding for a specific project
python3 bootstrap.py \
  --target /path/to/my-project \
  --name "Quantum Engine" \
  --mission "High-performance distributed event processing engine" \
  --phase "Phase 1 - Core Architecture" \
  --domains "engine,storage,network,api" \
  --git-init
```

### CLI Arguments for `bootstrap.py`:
| Option | Short | Default | Description |
|---|---|---|---|
| `--target` | `-t` | `.` | Target project directory path |
| `--name` | `-n` | Directory name | Name of the project |
| `--mission` | `-m` | "Autonomous..." | High-level mission statement |
| `--phase` | `-p` | "Phase 1..." | Initial project phase name |
| `--domains` | `-d` | "core" | Comma-separated functional domain names |
| `--force` | `-f` | `False` | Overwrite existing `.agent/` directory |
| `--git-init` | | `False` | Run `git init` if target is not a git repo |

---

## 🛠️ Operating `.agent/memory.py` in Target Projects

Once bootstrapped, agents interact with the memory engine directly:

### 1. View Project Status & Budget
```bash
python3 .agent/memory.py status
```
Displays mission, current phase, active task, git HEAD vs verified commit, and context size budget breakdown.

### 2. Validate Memory Integrity
```bash
python3 .agent/memory.py validate
```
Validates JSON schemas, git commit alignment, and verifies that `BOOTSTRAP_CONTEXT_BYTES <= 10,240 bytes` (10 KB).

### 3. Checkpoint State Atomically
```bash
python3 .agent/memory.py checkpoint \
  --phase "Phase 2 - Feature Development" \
  --status "IN_PROGRESS" \
  --active-task "Implement authentication middleware" \
  --record-ledger \
  --task-id "TASK-002" \
  --task-summary "Completed user registration and password hashing" \
  --evidence "pytest_exit_0_hash_abc123" \
  --test-status "ALL_PASS (48/48)"
```
- Atomically updates `PROJECT_STATE.json`.
- Synchronously regenerates `BOOT.md`.
- Appends task evidence to `TASK_LEDGER.jsonl`.
- Recalculates exact context metrics.

### 4. Append Architectural Decision (ADR)
```bash
python3 .agent/memory.py add-decision \
  --id "ADR-002" \
  --title "Use SQLite with WAL mode for local cache" \
  --status "LOCKED" \
  --context "High concurrent read requirements without external DB services" \
  --decision "Use embedded SQLite database with WAL and 64MB mmap" \
  --consequences "Zero external runtime dependencies; single-node only"
```

---

## 📊 Context Size Metrics & Limits

Project Memory V2.0 strictly enforces context budgets:

- **Bootstrap Context Budget (`BOOTSTRAP_CONTEXT_BYTES`)**:
  $$\text{Size}(\text{BOOT.md}) + \text{Size}(\text{PROJECT_STATE.json}) + \text{Size}(\text{NEXT_TASK.md}) \le 10,240 \text{ bytes (10 KB)}$$
- **Zero Directory Traversal**: Agents read `BOOT.md` and `PROJECT_MAP.json` to navigate directly to relevant files instead of listing/reading entire trees.

---

## 📜 The 10 Golden Rules

1. **Level 0 Boot First**: Read `.agent/BOOT.md` on boot. Never recursive-scan codebase.
2. **Verified Commit Binding**: All state transitions must reference valid git commit hashes.
3. **GPS Routing via Map**: Use `PROJECT_MAP.json` to load only relevant domain files.
4. **Immutable Locked Decisions**: Never violate `[LOCKED]` ADRs in `DECISIONS.md`.
5. **Atomic State Checkpointing**: Use `memory.py checkpoint` for all updates.
6. **Append-Only Ledger**: Never modify or truncate `TASK_LEDGER.jsonl`.
7. **Single Active Task Focus**: `NEXT_TASK.md` governs the current single focus.
8. **Evidence-Based Verification**: Only mark tasks complete after passing verified test suites.
9. **Strict Context Budget**: Keep combined bootstrap files under 10 KB.
10. **Memory Validation Guard**: Run `memory.py validate` in pre-commit / CI.

---

## 🧪 License
Apache-2.0 / MIT. Created for high-autonomy agent workflows.
