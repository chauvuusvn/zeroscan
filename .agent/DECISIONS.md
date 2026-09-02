# Architectural Decision Records (ADRs)

This file records key architectural, design, and structural decisions for the project. Decisions marked `[LOCKED]` are binding on all autonomous agents and human developers until formally superseded.

---

## ADR-001: Adoption of Project Memory V2.0 Architecture
- **Date**: 2026-09-02
- **Status**: [LOCKED]
- **Context**: Autonomous agents require deterministic session resumption and fast context loading without scanning the entire repository.
- **Decision**: Adopt `.agent/` directory structure with Level 0 `BOOT.md`, machine-readable `PROJECT_STATE.json`, `PROJECT_MAP.json`, and append-only `TASK_LEDGER.jsonl`.
- **Consequences**: All agents must follow `MEMORY_PROTOCOL.md` and keep bootstrap context `<= 10 KB`.
