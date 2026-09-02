# Active Task Specification

## Task Metadata
- **TASK ID**: TASK-001
- **PHASE**: Phase 1 - Architecture & Setup
- **TITLE**: Bootstrap project architecture and verify memory system
- **STATUS**: IN_PROGRESS

---

## 🎯 Goal & Description
Initialize foundational project structure for zeroscan and verify initial test/build setup.

---

## 📋 Acceptance Criteria
- [ ] Requirements defined in task goal are implemented.
- [ ] Code follows existing project style and patterns.
- [ ] Unit/integration tests pass with 0 errors.
- [ ] Memory state checkpointed via `.agent/memory.py checkpoint`.

---

## 📂 Target Files
- `.agent/PROJECT_MAP.json`
- `README.md`
- `pyproject.toml`

---

## 🧪 Verification Commands
```bash
python3 .agent/memory.py validate
```
