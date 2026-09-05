# Active Task Specification

## Task Metadata
- **TASK ID**: TASK-003
- **PHASE**: Phase 2 - Engine Maturation
- **TITLE**: Automated CI/CD validation tests
- **STATUS**: IN_PROGRESS

---

## 🎯 Goal & Description
Setup GitHub Actions workflow to run validate on all PRs and commits

---

## 📋 Acceptance Criteria
- [ ] Requirements defined in task goal are implemented.
- [ ] Code follows existing project style and patterns.
- [ ] Unit/integration tests pass with 0 errors.
- [ ] Memory state checkpointed via `.agent/memory.py checkpoint`.

---

## 📂 Target Files
- `Consult `.agent/PROJECT_MAP.json` for domain paths.`

---

## 🧪 Verification Commands
```bash
pytest
python3 .agent/memory.py validate
```
