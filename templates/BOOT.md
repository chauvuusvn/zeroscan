# {{PROJECT_NAME}} — Agent Boot Anchor

**MISSION**: {{MISSION}}

---

## ⚡ Current Execution State
- **CURRENT PHASE**: {{CURRENT_PHASE}}
- **CURRENT STATUS**: {{STATUS}}
- **ACTIVE TASK**: {{ACTIVE_TASK}}
- **VERIFIED COMMIT**: `{{VERIFIED_COMMIT}}`
- **LAST CHECKPOINT**: {{LAST_UPDATED}}

---

## 🔒 Critical Constraints
1. **Zero-Scan Boot**: Do NOT recursively explore the repo. Consult `.agent/PROJECT_MAP.json`.
2. **Budget Rule**: Combined size of `BOOT.md`, `PROJECT_STATE.json`, `NEXT_TASK.md` must be `<= 10 KB`.
3. **Locked Decisions**: Adhere strictly to locked architectural decisions in `.agent/DECISIONS.md`.
4. **Evidence First**: Only mark tasks complete after passing verified test suites.

---

## 🧭 Files to Read Next
1. `.agent/NEXT_TASK.md` (Active task requirements & acceptance criteria)
2. `.agent/PROJECT_MAP.json` (GPS domain map for relevant files & test suites)
