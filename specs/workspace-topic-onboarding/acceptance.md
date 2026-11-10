# Acceptance Record: Workspace and Topic Onboarding

**Workspace**: `workspace-topic-onboarding` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Evidence Table

| Requirement | Evidence IDs | Evidence Summary | Verdict |
|---|---|---|---|
| FR-001: deterministic and rerunnable workspace setup | E-001 | Fresh setup, name preservation/rename, additive schema upgrade, and template-copy replay pass | PASS |
| FR-002: separate adaptive topic-onboarding Skill | E-001, E-002 | Canonical Skill owns the interview and produces the bounded CLI proposal | PASS |
| FR-003: optional answers and explicit unknown/empty distinction | E-001, E-002 | Tests preserve `null` and `[]`; Skill contract allows skipped answers | PASS |
| FR-004: learner review before persistence | E-001, E-002 | Skill requires review and explicit approval; CLI refuses writes without `--approved` | PASS |
| FR-005: CLI validation and SQLite persistence | E-001 | Versioned proposal validates and creates topic plus `topic_config` atomically | PASS |
| FR-006: integration setup remains opt-in and separate | E-003 | Setup exposes no integration command or credentials workflow | PASS |
| FR-007: many-to-many topic/deck mapping and reuse | E-003 | Deferred to `flashcards-and-integrations`; no deck model is implemented in this feature | DEFERRED |
| FR-008: preview and authorization for remote writes | E-003 | Deferred with the adapter; this feature performs no remote writes | DEFERRED |
| FR-009: concise README index with Skill-owned interview details | E-002 | README and AGENTS point to the canonical Skill; the complete contract stays in the Skill/spec | PASS |
| FR-010: explicit approval flag and atomic identity/config write | E-001 | Missing approval and invalid proposals create no rows; valid proposals persist both rows | PASS |

## Verdict Summary

| Dimension | Verdict | Notes |
|---|---|---|
| Component capability | PASS | Setup, proposal validation, SQLite persistence, and host discovery are implemented and tested |
| Workflow closure | PASS | A copied template can be initialized and onboarded locally without changing the template source |
| User-visible outcome | PASS | The Skill presents the complete proposal contract and waits for explicit learner approval |
| Deferred integration scope | CONDITIONAL | Anki mapping, preview, and remote writes move to `flashcards-and-integrations` |

**Overall**: CONDITIONAL PASS for local workspace and topic onboarding; the Anki adapter slice remains explicitly deferred.

## Workflow Replay

- **Input**: temporary copy of the repository template, a fresh local workspace, and an approved `Astronomy` proposal.
- **Final result**: setup and onboarding succeed in the copied workspace; the test verifies that the template source database remains unchanged.
- **Replay type**: local end-to-end test, covered by E-001; no network or Anki account is required.

## Decision Capture Outcome

| Decision | Final Status | Evidence | Drift / Follow-up |
|---|---|---|---|
| DEC-001: replace `init` with `setup` without a compatibility alias | accepted | E-001 confirms `setup` is available and `init` is rejected | No drift; reconsider only if the template is published with external automation depending on `init` |
| DEC-002: store approved topic configuration in SQLite | accepted | E-001 verifies atomic topic/config persistence and explicit unknown values | No drift; revisit only if standalone editable topic files become a concrete requirement |

## Closeout Checklist

| Item | Status | Evidence / Rationale | Next Step |
|---|---|---|---|
| Retire old logic or compatibility fallback | complete | `init` was unpublished and has no compatibility alias; E-001 covers the command surface | None |
| External writes and secrets | not applicable | No adapter, credentials, or remote writes are part of this feature | Keep preview and authorization in the future adapter feature |
| Commit, push, CI, or template publication | deferred | The local worktree is still uncommitted and GitHub template publication is not enabled | Publish only after the clean-clone workflow is scheduled and reviewed |
| Docs, stage notes, tasks, and acceptance | complete | E-004 validates the active feature's closeout artifacts | Continue with `review-profile-core` clarification |
| Architecture and decision capture | complete | ADR-0004 and DEC-001/DEC-002 preserve the onboarding boundaries | Revisit only on an upgrade trigger |

## Knowledge Capture

| Type | Title | Summary | Evidence | Scope | Sync Status | Follow-up |
|---|---|---|---|---|---|---|
| convention | Learner-reviewed topic configuration | Skills conduct the adaptive interview; the CLI validates a bounded proposal and stores approved configuration beside its stable topic ID. Unknown list values stay distinct from explicitly empty lists. | E-001, E-002, DEC-002 | learnBase workspace | recorded-only | None |

## Completion Record

- **Final conclusion**: CONDITIONAL PASS for local workspace and topic onboarding.
- **Completion basis**: E-001 through E-006 cover the implemented local requirements, deferred integration boundary, SDD closeout, and post-closeout routing.
- **Blockers**: none for this feature's local onboarding scope.
- **Deferred**: Anki deck mapping, preview, remote publication, commit/push, and GitHub template activation.
- **Retirement**: no `init` compatibility path was published or retained.
- **Commit status**: not committed or pushed; no such operation was requested.
- **Next action**: clarify evidence thresholds, recency, and conflicting claims in `review-profile-core`.

## Handoff Follow-up: 2026-11-10

历史 CONDITIONAL PASS 与上述证据保持不变。FR-007 的既有牌组复用及多对多映射已由 `flashcards-and-integrations` FR-007 交付；FR-008 的只读预览由该 feature 的 FR-008/FR-009 交付。见 [M3 acceptance](../flashcards-and-integrations/acceptance.md) 和 [M3 E-001/E-004](../flashcards-and-integrations/verify-evidence.md)。学习者选择的首版不包含 Anki 发布/回收或 nmem 写入，因此未声称远端写入流程通过验收；将来单独 specify 并取得具体授权。
