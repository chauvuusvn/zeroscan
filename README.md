# ZeroScan (`.agent/`) — Project Memory V2.0

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README.vi.md) | [ 📘 Complete Usage Guide ](USAGE_GUIDE.md) | [ 📕 Hướng dẫn sử dụng ](HUONG_DAN_SU_DUNG.md)

> **The Zero-Scan, Git-Aware Context Engine for AI Coding Agents**  
> Compatible with Hermes Agent, Claude Code, OpenAI Codex, and OpenCode.

---

## 🌟 Overview

**Project Memory V2.0** is an open standard designed to eliminate context bloat, hallucination, and directory-crawling overhead in AI-driven software development.

Traditional coding agents waste tens of thousands of tokens scanning entire codebases upon startup. Project Memory replaces scanning with a lightweight, Git-bound **Level 0 Boot Anchor** (`BOOT.md` < 1 KB) and an architectural **GPS Map** (`PROJECT_MAP.json`), ensuring agents boot instantly with `<= 10 KB` of total context.

---

## 💡 Why It Saves 90–95% Tokens

### 1. Zero-Scan Startup (Level 0 Boot Anchor)
Traditional agents ingest entire repositories on every session turn, easily burning 30,000–100,000+ tokens before writing a single line of code. With Project Memory, the agent reads **only `BOOT.md` (~1 KB / ~500 tokens)**, gaining immediate architectural clarity and task direction without exploring irrelevant directories.

### 2. GPS Navigation via `PROJECT_MAP.json`
Instead of performing costly regex searches across the tree, agents query the structured domain map to resolve exact source and test file paths just-in-time. Irrelevant modules are never loaded into working context.

### 3. Lean Multi-Agent Task Delegation
When an orchestrator agent delegates tasks to subagents or workers (e.g. specialized coding models), it passes only `BOOT.md` and `NEXT_TASK.md`. Worker agents operate in isolated, razor-sharp context windows without paying the token tax of the full repository.

### 📊 Token Consumption Comparison

| Lifecycle Stage | Traditional Approach (Full Scan) | Project Memory V2.0 (`.agent/`) | Token Savings |
|---|---|---|:---:|
| **Session Boot** | Ingest whole repo (30k–100k+ tokens) | Read `BOOT.md` (< 1 KB / ~500 tokens) | **~95%** |
| **Domain Navigation** | Recursive grep & tree traversal | Query `PROJECT_MAP.json` (< 3 KB) | **~90%** |
| **Worker Subagent Boot** | Re-read full repo per child agent | Load `NEXT_TASK.md` + target files | **~92%** |
| **Session Memory Drift** | Prompt bloat & hallucination | External append-only ledger & ADRs | **Zero Drift** |

> **📌 Engineering Scope Note:** Token savings specifically measure context initialization, recursive directory crawling, and exploratory search overhead. Tokens required to author or modify actual code files depend naturally on the size of the generated diff.

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

### Option A: Instant One-Liner (No Clone Required)
```bash
curl -fsSL https://raw.githubusercontent.com/chauvuusvn/zeroscan/main/bootstrap.py | python3 - -n "Quantum Engine" --domains "engine,storage,network,api" --git-init
```

### Option B: Using local `bootstrap.py`
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

### 3. Checkpoint State Atomically & Synchronize Next Task
```bash
python3 .agent/memory.py checkpoint \
  --phase "Phase 2 - Feature Development" \
  --status "IN_PROGRESS" \
  --record-ledger \
  --task-id "TASK-002" \
  --task-summary "Completed user registration and password hashing" \
  --evidence "pytest_exit_0_hash_abc123" \
  --test-status "ALL_PASS (48/48)" \
  --next-task "Build JWT Refresh Token Rotation" \
  --next-task-id "TASK-003" \
  --next-task-desc "Implement Redis-backed refresh token rotation with revoke whitelist"
```
- Atomically updates `PROJECT_STATE.json`.
- Synchronously regenerates `BOOT.md`.
- Synchronously updates `NEXT_TASK.md` with acceptance criteria.
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

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><b>1. Which AI coding agents are compatible with Project Memory V2.0?</b></summary>

Project Memory V2.0 is designed as a model-agnostic, open specification. It works out-of-the-box with:
- **Hermes Agent**
- **Claude Code (Anthropic)**
- **OpenAI Codex**
- **OpenCode**
- **Cursor / Aider / Custom LLM Agent Frameworks**
</details>

<details>
<summary><b>2. Does `.agent/` require external Python packages or third-party dependencies?</b></summary>

**No.** The core engine (`memory.py` and `bootstrap.py`) is written in 100% pure Python 3.11+ standard library (`json`, `subprocess`, `hashlib`, `argparse`, `pathlib`). There are zero external `pip` dependencies required to run status checks, validation, or state checkpointing.
</details>

<details>
<summary><b>3. How does Project Memory V2.0 prevent context drift across long sessions?</b></summary>

Context drift occurs when agents rely on transient chat memory that gets truncated or diluted. Project Memory moves ground-truth memory out of the prompt window and into the filesystem:
- Architecture rules are locked in `DECISIONS.md`.
- Historical progress is permanently recorded in the immutable `TASK_LEDGER.jsonl`.
- The active session only reads `< 2.5 KB` of state from `BOOT.md`, eliminating hallucination.
</details>

<details>
<summary><b>4. Can I apply Project Memory V2.0 to an existing, established repository?</b></summary>

**Yes.** Simply run:
```bash
python3 bootstrap.py --target /path/to/existing-repo --domains "auth,api,db,ui"
```
Then define your module mappings in `.agent/PROJECT_MAP.json` and set your current phase in `.agent/PROJECT_STATE.json`.
</details>

<details>
<summary><b>5. How can I enforce memory integrity in CI/CD pipelines?</b></summary>

Add `python3 .agent/memory.py validate` to your GitHub Actions workflow or pre-commit hooks. It will fail with exit code `1` if:
- Bootstrap context exceeds 10 KB budget.
- JSON state files fail schema validation.
- Uncommitted or unverified changes violate the git commit baseline.
</details>

---

## 👤 Author & Maintainer

**Chau Vu (Châu Vũ)** — [@chauvuusvn](https://github.com/chauvuusvn)  
*Architected for high-autonomy multi-agent ecosystems and lean AI workflows.*

---

## 🧪 License
Apache-2.0 / MIT. Created for high-autonomy agent workflows.
