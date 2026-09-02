# Project Memory V2.0 Protocol & Standard Operating Procedures

This document outlines the **10 Golden Rules of Agent Memory** for all AI coding agents (Hermes, Claude Code, OpenAI Codex, OpenCode). Adherence to this protocol guarantees zero-scan bootstrap, zero context bloat, deterministic task resumption, and cross-session state integrity.

---

## The 10 Golden Rules

### Rule 1: Level 0 Boot First (Zero-Scan Rule)
- On session kickoff, **always** read `.agent/BOOT.md` first.
- Never recursively crawl or scan entire directory trees to "understand the project".
- `BOOT.md` is strictly capped at `< 1 KB` (~30-35 lines) and provides immediate orientation: project name, mission, current phase, active task, verified commit hash, and critical constraints.

### Rule 2: Verified Commit Binding
- Every state checkpoint in `.agent/PROJECT_STATE.json` must be bound to a real, verifiable Git commit hash (`verified_commit`).
- If the current git `HEAD` does not match `verified_commit`, the agent must inspect git diff/log to reconcile drift before proceeding.

### Rule 3: GPS Routing via Map
- Consult `.agent/PROJECT_MAP.json` as the architectural GPS.
- Identify the functional domain and load only the specific files, schemas, and test suites indicated in the map.
- Update `PROJECT_MAP.json` whenever new modules, entry points, or test suites are created.

### Rule 4: Immutable Locked Decisions (ADRs)
- Architectural Decision Records in `.agent/DECISIONS.md` with status `[LOCKED]` are non-negotiable architectural invariants.
- Agents must never revert, overwrite, or bypass locked decisions without explicit operator authorization.

### Rule 5: Atomic State Checkpointing
- All updates to project status, phase transitions, and test results must be recorded atomically using `python3 .agent/memory.py checkpoint`.
- State transitions must never leave `PROJECT_STATE.json` or `BOOT.md` in a corrupted or half-written state.

### Rule 6: Immutable Append-Only Ledger
- `.agent/TASK_LEDGER.jsonl` is an immutable, append-only chronological ledger of completed tasks, milestones, and phases.
- Never delete, reorder, or edit existing lines in the ledger. Each entry must record `task_id`, `phase`, `timestamp`, `commit`, `summary`, and `evidence_hash`.

### Rule 7: Single Active Task Focus
- `.agent/NEXT_TASK.md` specifies exactly one active task at any given time.
- The file contains strict acceptance criteria, target files, and exact verification commands.
- An agent must complete or explicitly block the active task before picking up a new one.

### Rule 8: Evidence-Based Verification
- A task cannot be marked completed in `PROJECT_STATE.json` or `TASK_LEDGER.jsonl` without tangible verification evidence.
- Acceptable evidence includes test suite outputs (`exit_code == 0`), execution logs, deterministic benchmark numbers, or generated artifact verification.

### Rule 9: Strict Context Budget Enforcement
- Memory overhead must remain ultra-lean.
- **Bootstrap Budget**: `BOOT.md` + `PROJECT_STATE.json` + `NEXT_TASK.md` combined (`BOOTSTRAP_CONTEXT_BYTES`) must remain `<= 10,240 bytes` (10 KB).
- **Total System Budget**: Entire `.agent/` directory should remain lean and structured. Prune or archive verbose outputs.

### Rule 10: Memory Validation & Integrity Guard
- Run `python3 .agent/memory.py validate` before starting a task and after completing a checkpoint.
- Validation checks schema compliance, file existence, git commit alignment, and context size budgets. If validation fails, halt and resolve anomalies immediately.

---

## Standard Agent Workflow Lifecycle

```
[Agent Starts]
      │
      ▼
1. Read `.agent/BOOT.md` (Level 0 - Zero Scan)
      │
      ▼
2. Validate Memory State (`python3 .agent/memory.py validate`)
      │
      ▼
3. Read `.agent/NEXT_TASK.md` & Consult `.agent/PROJECT_MAP.json`
      │
      ▼
4. Read Only Targeted Domain Files & Tests
      │
      ▼
5. Execute Code Changes & Run Verifications
      │
      ▼
6. Commit Code (`git commit -m "..."`)
      │
      ▼
7. Checkpoint Memory (`python3 .agent/memory.py checkpoint ...`)
      │
      ▼
[Agent Ready for Next Task / Handoff]
```
