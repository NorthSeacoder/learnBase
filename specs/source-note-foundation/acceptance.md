# Acceptance Record: Source-to-Note Foundation

**Workspace**: `source-note-foundation` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Evidence Table

| Requirement | Evidence IDs | Evidence Summary | Verdict |
|---|---|---|---|
| FR-001: initialize workspace and SQLite registry | E-001 | Fresh-workspace CLI flow succeeds | PASS |
| FR-002: create stable topics and parent links | E-001 | Topic CLI path is exercised in a fresh workspace | PASS |
| FR-003: register PDF/web sources and multiple topic links | E-001 | Both source types and topic links are exercised | PASS |
| FR-004: fingerprint local PDF and preserve external file | E-001 | SHA-256 is stored; external file remains in place | PASS |
| FR-005: reuse source identity and reject unreviewed changed revision | E-001 | Repeat registration reuses ID; changed content is rejected without replacing the stored hash | PASS |
| FR-006: create cited notes with stable IDs and locators | E-001 | CLI creates source-linked Markdown note | PASS |
| FR-007: validate registry and citation consistency | E-001 | Valid note passes; changed citation is rejected | PASS |
| FR-008: provide host-neutral Agent Skill | E-003 | Canonical skill and WorkBuddy project link exist | PASS |
| NFR-001: work offline and avoid third-party core dependencies | E-001, E-004 | Standard-library CLI tests and local structure validation pass | PASS |

## Verdict Summary

| Dimension | Verdict | Notes |
|---|---|---|
| Component capability | PASS | CLI operations and tests are present and pass |
| Workflow closure | PASS | Source registration, cited note creation, and validation form an end-to-end local flow |
| User-visible outcome | PASS | The CLI creates a note under `02-notes/` and reports validation results |

**Overall**: PASS for local implementation

## Workflow Replay

- **Input**: fresh workspace, topic `history`, registered webpage source, note with section locator.
- **Final result**: CLI created the note and `note validate` accepted it; covered by `test_fresh_workspace_commands_cover_web_intake` in E-001.
- **Replay type**: local CLI test; PDF extraction and live webpage reading remain host-tool responsibilities.

## Closeout Checklist

| Item | Status | Evidence / Rationale | Next Step |
|---|---|---|---|
| Old logic, fallback, or temporary compatibility | 不适用 | New template feature; no predecessor path to retire | 无 |
| Commit, push, CI, or publication | 延后 | Local worktree is modified; remote `isTemplate=false` and does not yet contain these changes | Commit/push and enable template setting when explicitly scheduled |
| Docs, stage notes, templates, and acceptance | 已完成 | This feature has spec, plan, tasks, evidence, and acceptance records | M2 clarification |
| ADR and architecture debt | 已完成 | Three accepted ADRs define storage, learner/topic, and adapter boundaries | Revisit only if external sync or hosted use is added |
| Knowledge Capture | 已完成 | Source provenance and authority boundaries recorded below | Keep in this repository |

## Knowledge Capture

| Type | Title | Summary | Evidence | Scope | Sync Status | Follow-up |
|---|---|---|---|---|---|---|
| convention | Source-to-note authority | Keep knowledge prose in Markdown and source/topic/note identities in SQLite. Source registration must preserve external originals and citations must retain locators. | E-001, ADR-0001, ADR-0003 | learnBase workspace | recorded-only | None |

## Completion Record

- **Final conclusion**: PASS for local implementation and verification.
- **Completion basis**: E-001 through E-004 cover all requirements and the local SDD workspace validates.
- **Blockers**: none for local M1.
- **Deferred**: Git commit/push and GitHub template flag; optional PDF/web extraction adapters.
- **Retirement**: not applicable.
- **Commit status**: not submitted; no commit or push was requested.
- **Next action**: continue `review-profile-core` at clarify stage.
