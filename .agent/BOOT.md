# LEVEL 0 BOOT ANCHOR: ZEROSCAN
> **Spec Version:** 2.2.1 | **Zero-Scan Hard Budget:** <= 10 KB | **Auto-Synced**

- **Project:** zeroscan
- **Mission:** The Zero-Scan, Git-Aware Context Engine for AI Coding Agents
- **Phase:** Phase 2 - Engine Maturation
- **Active Task:** Automated CI/CD validation tests
- **Verified Commit:** `2388dc82`
- **Last Synchronized:** `2026-09-28T16:05:16.005212+00:00`

## MANDATORY AGENT BOOT PROTOCOL
1. Do NOT scan the entire repository tree.
2. Read `.agent/PROJECT_MAP.json` to navigate only active domain files.
3. Check `.agent/NEXT_TASK.md` for current task acceptance criteria.
4. Check `.agent/DECISIONS.md` for locked architectural constraints.
5. On task completion, commit code to git, then run `zeroscan checkpoint`.
