# Verify Evidence: Workspace and Topic Onboarding

**Workspace**: `workspace-topic-onboarding` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Implementation Baseline

| Field | Value |
|---|---|
| Implementation Baseline | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` |
| Baseline Scope | `tools/learnbase.py`, `tests/test_learnbase.py`, `.agents/skills/learnbase-onboarding/SKILL.md`, `.workbuddy/skills/learnbase-onboarding`, `README.md`, `AGENTS.md`, and the `spec.md`, `plan.md`, `data-model.md`, and `tasks.md` contracts present at capture time |
| Captured At | 2026-11-09T13:22:37Z |

SHA-256: `tools/learnbase.py` = `d6173f5db5fbb0c7153618e0d444cdd1ad18b300dab4f64f959dd7232b17f423`; `tests/test_learnbase.py` = `2a4b92a840beccd71f452a7319eaa2de506f00c3f5386d1ca896db1d08931394`; `learnbase-onboarding/SKILL.md` = `fb87332cf4d6c4b54706ac88867c6da7434f0670fa8533524be46f85a3f5f792`.

## Evidence Ledger

| ID | Maps To | Action | Result | Exit/Verdict | Observed At | Based On | Scope | Source | Status |
|---|---|---|---|---|---|---|---|---|---|
| E-001 | FR-001..FR-005, FR-009..FR-010, DEC-001..DEC-002, T002..T004 | `rtk python3 -W error::ResourceWarning -m unittest discover -s tests -v` | All 19 tests pass, including setup rerun and v1 upgrade, proposal type/approval/atomicity checks, template-copy replay, canonical Skill discovery, and source-to-note regression coverage | exit 0 | 2026-11-09T13:23:27Z | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` | CLI behavior and end-to-end local workflows | `tests/test_learnbase.py` | fresh |
| E-002 | FR-002..FR-004, FR-009, T004..T005 | Inspect `.agents/skills/learnbase-onboarding/SKILL.md`, `.workbuddy/skills/learnbase-onboarding`, `README.md`, and `AGENTS.md`; `rtk ls -ld .workbuddy/skills/learnbase-onboarding` | The canonical Skill describes optional answers, proposal schema, review, and explicit approval; the WorkBuddy link resolves to it and project entry points identify the same onboarding path | PASS | 2026-11-09T13:23:27Z | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` | Host discovery and learner approval contract | `.agents/skills/learnbase-onboarding/SKILL.md`; `.workbuddy/skills/learnbase-onboarding`; `README.md`; `AGENTS.md` | fresh |
| E-003 | FR-007..FR-008 | Review feature scope and CLI command surface with `rtk python3 tools/learnbase.py --help` | No Anki mapping or remote-write command is exposed; deck mapping, preview, and authorized publication remain assigned to `flashcards-and-integrations` | not-applicable: deferred adapter scope | 2026-11-09T13:23:27Z | `not-applicable: flashcards-and-integrations owns adapter setup and remote writes` | Deferred integration boundary; no external side effects in this feature | `specs/workspace-topic-onboarding/plan.md`; CLI help output | not-applicable |
| E-004 | T006, DEC-001..DEC-002 | `rtk bash /Users/yqg/.agents/skills/sdd/scripts/validate-sdd.sh --workspace-root /Users/yqg/personal/libs/learnBase --closeout-ready` | Closeout validation checks complete tasks, evidence integrity, acceptance sections, decision capture, and roadmap alignment | exit 0 | 2026-11-09T13:26:58Z | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` | SDD closeout readiness while this feature is active | SDD validator output `validate-sdd: OK` | fresh |
| E-005 | T006 | `rtk bash /Users/yqg/.agents/skills/sdd/scripts/validate-sdd.sh --workspace-root /Users/yqg/personal/libs/learnBase` | The active pointer and umbrella roadmap agree on `review-profile-core` at clarify | exit 0 | 2026-11-09T13:26:58Z | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` | Post-closeout continuation routing | SDD validator output `validate-sdd: OK` | fresh |
| E-006 | T006 | `rtk git diff --check` and targeted UTF-8 trailing-whitespace scan across source, workspace docs, acceptance, and evidence files | No diff whitespace errors, trailing tabs, single trailing spaces, or runs longer than two spaces found; intentional two-space Markdown hard breaks are retained | exit 0 | 2026-11-09T13:29:39Z | `snapshot:learnbase-workspace-topic-onboarding-2026-11-09-132237` | Edited source and feature/workspace documentation, including closeout artifacts | Command output and targeted scan | fresh |

## Architecture And Decision Drift

- **Architecture drift**: none observed. Workspace state and topic configuration remain local SQLite data; the template source is unchanged by the replayed onboarding workflow.
- **Decision drift**: none. `DEC-001` replaces the unpublished `init` command without an alias; `DEC-002` stores accepted configuration in SQLite linked to its stable topic ID.

## Verdict

- **Verdict**: CONDITIONAL PASS for local workspace and topic onboarding.
- **Unresolved scope**: many-to-many Anki deck mapping, preview, and remote publication remain deferred to `flashcards-and-integrations`; no adapter or external write was attempted here.
- **Next Stage**: closeout, then clarify `review-profile-core`.
