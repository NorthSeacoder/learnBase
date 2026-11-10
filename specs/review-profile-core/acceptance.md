# Acceptance Record: Review and Evidence-Backed Learner Profile

**Workspace**: review-profile-core | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Evidence Table

| Requirement | Evidence IDs | Evidence Summary | Verdict |
|---|---|---|---|
| FR-001..FR-003: shared activities, learner evidence, unknowns and conflicts | E-001 | Typed activity and evidence proposals preserve unknowns, separate assistant analysis, and retain audited status history | PASS |
| FR-004, FR-007..FR-010: topic-scoped evidence rules | E-001 | Dimensions default empty, are topic-scoped, declare eligible evidence and gates, and exclude assistant analysis | PASS |
| FR-005, FR-008, FR-011: rebuildable evidence-linked profile output | E-001 | Projection and Markdown report cover thresholds, recency, disputes, opposing directions, provenance, and no scores | PASS |
| FR-006, FR-012: idempotent activity writes | E-001 | Same-key/same-payload replay returns the original activity; changed payload is rejected | PASS |
| Schema upgrade and source/onboarding regression | E-001 | Populated v1/v2 upgrades, future-schema rejection, and prior workflow tests pass | PASS |
| Python syntax and workspace whitespace | E-002, E-003 | Compilation and diff checks pass | PASS |
| SDD context and closeout contracts | E-004, E-005 | Required verify context is fresh and closeout-ready validation passes | PASS |
| Post-closeout roadmap handoff | E-006 | Active pointer and roadmap now select flashcards-and-integrations at clarify | PASS |

## Verdict Summary

| Dimension | Verdict | Notes |
|---|---|---|
| Component capability | PASS | SQLite v3 activity/evidence writes, provenance, status history, topic dimensions, projection, and report generation are implemented and tested |
| Workflow closure | PASS | The approved review-to-profile CLI path is replayed end-to-end; writes remain learner-approved and local |
| User-visible outcome | PASS | Reports show evidence IDs, dates, scope, and conflicts without mastery or confidence scores |

**Overall**: PASS for the local review/profile core.

## Workflow Replay

- Input: a temporary workspace, a topic with an approved profile dimension, learner-reviewed activity/evidence proposals, and explicit status transitions.
- Final result: the CLI stores the activity once, preserves source/note provenance and status history, and produces a deterministic profile view with evidence IDs, dates, and conflict status.
- User-visible assertions: unknown values remain unknown; same-key replay does not duplicate evidence; unresolved disputes and opposing confirmed directions stay visible; no mastery score is emitted.
- Replay type: local end-to-end CLI test in E-001; no network account or external adapter is required.

## Decision Capture Outcome

| Decision | Final Status | Evidence | Drift / Follow-up |
|---|---|---|---|
| DEC-001: per-topic dimensions, empty by default | accepted | E-001 covers empty defaults and topic isolation | No drift; reusable presets remain opt-in future work |
| DEC-002: configured evidence count/recency gates | accepted | E-001 covers threshold, inclusive recency, undated evidence, and descriptive output | No drift; do not add automatic mastery scoring |
| DEC-003: preserve and mark conflicting evidence | accepted | E-001 covers append-only transitions, explicit disputes, and opposing directions | No drift; resolution remains learner-approved and audited |
| DEC-004: required idempotency key plus payload digest | accepted | E-001 covers replay and changed-payload rejection | No drift; adapters must preserve a stable key per event |
| DEC-005: assistant analysis is not profile evidence | accepted | E-001 covers separate storage and evidence-type validation | No drift; any future analysis-derived fact requires learner-confirmed evidence |

## Closeout Checklist

| Item | Status | Evidence / Rationale | Next Step |
|---|---|---|---|
| Migration and prior behavior | complete | E-001 verifies additive v1/v2 upgrades, data preservation, and rejection of future schema versions | None |
| Legacy review paths or compatibility fallbacks | not applicable | This feature adds the first review/profile path in the new template; no earlier public review command exists | None |
| External writes and secrets | not applicable | The feature is local-only and has no adapter credentials or remote calls | Keep Anki/nmem writes behind preview and authorization in M3 |
| Docs, tasks, evidence, and acceptance | complete | E-001 through E-005 cover implementation, current contracts, and SDD closeout validation | Continue with flashcards-and-integrations clarification |
| Architecture and decision capture | complete | DEC-001..DEC-005 and the evidence authority rules are recorded in the plan and data model | Revisit only on their stated upgrade triggers |
| Commit, push, CI, and template publication | deferred | The worktree remains uncommitted; no commit, push, CI publication, or GitHub template action was requested | Review a scoped commit plan before any commit or publication |

## Knowledge Capture

| Type | Title | Summary | Evidence | Scope | Sync Status | Follow-up |
|---|---|---|---|---|---|---|
| pattern | Evidence-gated profile projection | Store evidence separately from analysis, require explicit eligibility and thresholds, retain conflicts, and rebuild descriptive output from source rows. | E-001, DEC-001..DEC-005, plan.md, data-model.md | Local single-learner SQLite profile projection | recorded-only | Reassess only when a concrete adapter requires a new evidence contract |
| convention | Learner approval for persisted facts | Skills conduct the conversation; the CLI validates bounded proposals and writes only after explicit approval. | E-001, learnbase-review/SKILL.md, docs/cli.md | Review and profile write paths | recorded-only | Apply to future structured learning-event writers |

## Completion Record

- Final conclusion: PASS for the local review/profile core.
- Completion basis: E-001 through E-006 cover requirements, migrations, regressions, context freshness, decisions, closeout readiness, and next-feature routing.
- Blockers: none for the approved local feature scope.
- Deferred: flashcard drafting and optional Anki/nmem adapters; external writes remain separately previewed and explicitly authorized.
- Commit status: not committed or pushed; the repository remains in the user's uncommitted initial worktree.
- Next action: clarify flashcards-and-integrations; retain richer-source-adapters as deferred until recurring extraction limits are evidenced.
