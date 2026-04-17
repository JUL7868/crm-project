# DO NOT DELETE — CORE SYSTEM FILE

# PROJECT RULES (CANONICAL)

This document defines the non-negotiable rules governing all development work on this project.

These rules exist to prevent system breakage, eliminate ambiguity, and ensure long-term stability.

---

## 1. FILE INTEGRITY RULE

- All code changes must be delivered as FULL FILES
- No partial snippets
- No “insert this here” instructions
- Every file must be complete and directly usable

---

## 2. NO ASSUMPTIONS RULE

- No code may be written without seeing the current version of the file
- If a file is not provided, it must be requested before proceeding
- No guessing of surrounding logic or structure

---

## 3. BACKWARD COMPATIBILITY RULE

- Existing functionality must not break
- All current behavior must be preserved unless explicitly approved otherwise
- Any risk to existing functionality must be clearly stated before implementation

---

## 4. CHANGE SCOPE RULE

Every change must clearly define:

- What is being changed
- What is NOT being changed
- Known risks or potential side effects

No work begins without this clarity.

---

## 5. SINGLE SOURCE OF TRUTH

- The Git repository is the only authoritative system state
- Chat outputs, notes, or memory are NOT authoritative
- If it is not in the repo, it does not exist

---

## 6. VERSION CONTROL RULE

- Every completed change must be committed before new work begins
- No stacking of multiple uncommitted changes
- Every commit must represent a stable, testable state

---

## 7. PROJECT MEMORY RULE

- PROJECT_STATE.md must be updated after any meaningful change
- This file represents the current system understanding
- All development decisions must align with it

---

## 8. NO SILENT REFACTORING RULE

- No renaming, restructuring, or optimization without explicit approval
- No hidden improvements
- No “cleanup” changes unless specifically requested

---

## 9. DEPLOYMENT RULE

- All changes must be tested locally before deployment
- Deployment must never be used as a testing environment
- Only verified code is deployed

---

## 10. FAILURE PROTOCOL

If something breaks:

1. STOP immediately
2. Do not attempt blind fixes
3. Revert to last known working commit
4. Diagnose root cause before making any changes

---

## 11. FULL CONTEXT RESPONSIBILITY

- All code must align with the current system architecture
- Changes must integrate cleanly with existing files
- No isolated or disconnected implementations

---

## 12. CLARITY OVER SPEED

- Correctness is prioritized over speed
- Ambiguity must be resolved before coding
- If something is unclear, it must be clarified first

---

## FINAL PRINCIPLE

This project is governed by system discipline, not conversation.

All work must follow these rules without exception.