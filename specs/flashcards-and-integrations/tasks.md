# Tasks: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations` | **Date**: 2026-11-10\
**Input**: `spec.md` + `plan.md` + `data-model.md`\
**Prerequisites**: all design decisions accepted; no blockers

## Execution Principles

- Keep card text in Markdown and SQLite limited to identity and relations.
- Use local/mock AnkiConnect tests; no live collection is required or written.
- Each task is independently verifiable; preserve explicit opt-in and no-write boundaries.

## Phase 1: Card Draft Slice

**Goal**: Persist and validate one learner-approved Basic Q&A draft with its local provenance.

- [x] T001 [Foundation] Add the v4 card identity, relation, and topic/deck mapping schema.
  - scope: `tools/learnbase.py`, `tests/test_learnbase.py`, `specs/flashcards-and-integrations/data-model.md`
  - slice: Schema setup exposes stable card identity and note/evidence/source/deck relations without storing card body text in SQLite.
  - blocked_by: none
  - maps_to: DEC-001, FR-003, FR-004, FR-007
  - verify: schema/version tests; setup rerun is idempotent; SQLite schema has no front/back columns.

- [x] T002 [US1] Implement approved Basic Q&A draft create, list, and validate commands.
  - scope: `tools/learnbase.py`, `tests/test_learnbase.py`, CLI docs
  - slice: A proposal with a validated local note and reviewed evidence creates one Markdown draft and stable registry links; invalid or unapproved input writes nothing.
  - blocked_by: T001
  - maps_to: DEC-001, FR-001, FR-002, FR-003, FR-004, FR-006
  - verify: unit and CLI tests validate note/evidence ownership, source locators, safe Markdown rendering, approval gate, and file/DB rollback.

## Phase 2: Merge and Preview Slices

**Goal**: Merge same-objective provenance without content loss and preview against existing Anki data.

- [x] T003 [US2] Implement objective-key merge, idempotent provenance union, and content-conflict rejection.
  - scope: `tools/learnbase.py`, `tests/test_learnbase.py`
  - slice: A learner-approved second source for an existing topic/objective updates the same card's provenance while preserving its ID/body; a changed Q&A fails with no writes.
  - blocked_by: T002
  - maps_to: DEC-002, FR-004, FR-005, FR-006
  - verify: tests cover explicit target, duplicate key, repeated merge, all source locators/evidence, cross-topic rejection, mismatched content, and injected persistence failure.

- [x] T004 [US3] Implement loopback AnkiConnect deck discovery, many-to-many mapping, and read-only preview.
  - scope: `tools/learnbase.py`, `tests/test_learnbase.py`, CLI docs
  - slice: An explicit command discovers decks, maps topics only to live existing decks, and previews each draft as already-present, proposed-addition, conflict, or skipped without mutating Anki.
  - blocked_by: T002, T003
  - maps_to: DEC-003, FR-007, FR-008, FR-009
  - verify: mock-server tests assert loopback-only transport, bounded timeout, exact read-action allowlist, result/error validation, mapping behavior, and preview classifications; no Anki write action is sent.

## Phase 3: Skill Handoff and Closeout

**Goal**: Connect learner-facing drafting/review to the CLI and record fresh acceptance evidence.

- [x] T005 [US4] Add the canonical `learnbase-flashcards` Skill and host discovery links.
  - scope: `.agents/skills/learnbase-flashcards/`, `.workbuddy/skills/`, `.claude/skills/`, `.cursor/skills/`, `README.md`, `docs/cli.md`, `docs/architecture.md`, `docs/glossary.md`
  - slice: The Skill reviews source/evidence context, presents draft and merge candidates for approval, and optionally uses enabled read-only nmem search as transient context; host links resolve to the same canonical skill.
  - blocked_by: T002, T003, T004
  - maps_to: DEC-001, DEC-002, DEC-004, FR-001, FR-005, FR-006, FR-010, FR-011
  - verify: skill/host-link checks; docs state adapter defaults and boundaries; no nmem write or sync command exists.

- [x] T006 [Verify] Run focused and full verification, record evidence, and close out the feature.
  - scope: `specs/flashcards-and-integrations/verify-evidence.md`, `acceptance.md`, `tasks.md`, `specs/learnbase-template/roadmap.md`, `docs/current-progress.md`, `task_plan.md`, `progress.md`
  - slice: All in-scope requirements have fresh local test evidence and the roadmap/pointer accurately state the resulting status and next feature.
  - blocked_by: T001, T002, T003, T004, T005
  - maps_to: DEC-001..DEC-004, all FRs
  - verify: full unit suite, compile, diff check, context freshness, SDD verify/closeout validators; no live Anki/nmem writes.

## Decision Verification Coverage

| Decision ID | Implementation Task | Verification Task | Drift Check |
|---|---|---|---|
| DEC-001 | T001, T002 | T002, T006 | Confirm Markdown owns card body and SQLite has identity/link tables only |
| DEC-002 | T003 | T003, T006 | Confirm one topic/objective identity, all provenance, and no overwrite on content conflict |
| DEC-003 | T004 | T004, T006 | Confirm calls are loopback read-only actions and preview does not publish |
| DEC-004 | T005 | T005, T006 | Confirm nmem is opt-in, read-only, transient, and not used as provenance |

## Dependencies and Order

Critical path: T001 -> T002 -> T003 -> T004 -> T005 -> T006. T004 can begin after T002, but final Skill handoff waits for its CLI contract. No implementation task needs live external credentials or a live Anki collection.

## Coverage

| Scenario / requirement | Tasks |
|---|---|
| US1 and FR-001..FR-004, FR-006 | T001, T002 |
| US2 and FR-005 | T003 |
| US3 and FR-007..FR-009 | T001, T004 |
| US4 and FR-010..FR-011 | T005 |
| Fresh evidence and closeout | T006 |

## Stage Readiness

- T001-T005 verification: 45 tests passed, including the fresh-template CLI replay, local HTTP adapter contract tests, and draft failure-injection tests. See E-001 through E-004 in `verify-evidence.md`.
- T006 verification: E-005 confirms all 9 required Check Context entries fresh; E-006 records passing SDD closeout-ready validation and template documentation hygiene.
- Recommended next step: retain this completed feature as the continuation pointer; no new implementation is active until the conditional source-adapter start condition is met
- Blockers: none
