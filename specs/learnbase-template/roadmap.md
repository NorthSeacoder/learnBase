# Roadmap: learnBase Learning Workspace Template

**Umbrella**: `learnbase-template`\
**Created**: 2026-11-09\
**Status**: completed (local scope; conditional adapter backlog retained)\
**Current Feature**: `default-integration-support`
**Next Recommended Feature**: `richer-source-adapters` (deferred pending evidence)

## Summary

learnBase turns the useful parts of the current learning workflow into a generic, local-first template for one learner across multiple topics. The work is split into independently usable features: knowledge/source intake, evidence-backed review and learner profiles, then flashcards and external integrations.

This repository is the topic-free template source. A learner creates a separate repository from it, then initializes workspace settings and topics there. Real learner configuration and study data must never be added to the template source.

## Current State

| Field | Value |
|---|---|
| Current feature | `default-integration-support` |
| specs/.active expected | `default-integration-support` |
| Current stage | `closeout complete` |
| Next stage | None activated; richer-source-adapters remains conditional |
| Current objective | Default Anki/nmem support delivered; dependencies and on-demand availability documented |

## Feature Roadmap

| Feature | Goal | Status | Depends On | Start Condition | Recommended Stage | Notes |
|---|---|---|---|---|---|---|
| `source-note-foundation` | Initialize the workspace and create traceable notes from registered PDFs/web sources | done | none | complete | closeout complete | Local tests pass; included in pushed baseline `7cd01e8` |
| `workspace-topic-onboarding` | Implement reusable workspace setup and per-topic onboarding for repositories created from the template | completed | `source-note-foundation` | Design decisions captured and task list ready | closeout complete | Historical conditional pass; mapping and preview handoff consumed by M3. Remote writes remain outside the agreed release. See [acceptance](../workspace-topic-onboarding/acceptance.md) |
| `review-profile-core` | Record question and non-question learning activities, evidence, and configurable profile claims | done | `workspace-topic-onboarding` | Implementation, verification, and closeout complete | closeout complete | PASS for the local review/profile core; see [acceptance](../review-profile-core/acceptance.md) and [verification evidence](../review-profile-core/verify-evidence.md) |
| `flashcards-and-integrations` | Draft cards from verified learning and optionally connect Anki/nmem | done | `review-profile-core` | Implementation, local verification and closeout complete | closeout complete | PASS for local drafts and read-only integration contracts; [acceptance](../flashcards-and-integrations/acceptance.md), [evidence](../flashcards-and-integrations/verify-evidence.md), E-001..E-006 |
| `richer-source-adapters` | Add optional extraction helpers for PDFs, web pages, OCR, and other media | deferred | `source-note-foundation` | Identify recurring extraction limits and host capabilities | specify only after trigger | Learner confirmed on 2026-11-10: no recurring problem yet; retain the original condition. Core remains offline and parser-agnostic |
| `default-integration-support` | Default Anki/nmem support without enable switches or setup probing | done | `flashcards-and-integrations` | User requested simpler personal-use defaults | closeout complete | 45 tests and SDD closeout-ready pass; [acceptance](../default-integration-support/acceptance.md), E-001..E-004 |

## Completion Log

| Feature | Date | Verdict | Evidence | Impact On Roadmap |
|---|---|---|---|---|
| `source-note-foundation` | 2026-11-09 | PASS (local) | `specs/source-note-foundation/acceptance.md`, E-001 through E-004 | Establishes stable source/topic/note IDs; review activities can link notes and topics |
| `workspace-topic-onboarding` | 2026-11-09 | CONDITIONAL PASS (local) | `specs/workspace-topic-onboarding/acceptance.md`, E-001 through E-006 | Establishes setup and learner-approved SQLite topic configuration; sends `review-profile-core` to clarify and defers Anki integration work |
| `review-profile-core` | 2026-11-10 | PASS (local) | `specs/review-profile-core/acceptance.md`, E-001 through E-006 | Closes M2 with idempotent, provenance-linked evidence and descriptive profile reports; advances `flashcards-and-integrations` to clarify |
| `flashcards-and-integrations` | 2026-11-10 | PASS (local) | `specs/flashcards-and-integrations/acceptance.md`, E-001 through E-006 | Delivers Basic drafts, provenance merge, existing-deck mapping and read-only preview; consumes onboarding handoff; no remote writes |
| `richer-source-adapters` scope decision | 2026-11-10 | Deferred by confirmed start condition | Learner reply: 暂未遇到，按原条件保留后续项 | No extraction helpers or dependencies added; reopen only after recurring material failures |
| `default-integration-support` | 2026-11-10 | PASS (local) | `specs/default-integration-support/acceptance.md`, E-001..E-004 | Removes default-off switches; no setup probing; existing read-only boundaries retained |
| Template baseline commit/push | 2026-11-10 | Completed | `7cd01e865831f7cc13c3e5501f21a94690ee0958`; successful `git push origin main` | Publishes the 62-file implementation baseline; GitHub Template setting unchanged |

## Next Recommendation

No implementation remains active. The `default-integration-support` follow-up passed local closeout: both adapters are supported by default, availability is checked when used, and setup remains local. README documents external dependencies. M3's original opt-in decision remains historical. Richer source adapters retain their original evidence condition; Anki publication/reconciliation and nmem writes remain a separately clarified future scope. See [roadmap audit](roadmap-audit.md) for requirement coverage and [commit record](commit-plan.md) for the pushed baseline.

The source-to-note foundation and local onboarding workflow can be used from a separate clone of the pushed repository. GitHub's "Use this template" setting was not changed; its last recorded value was disabled. Enabling that setting remains a separately requested action.

## Deferred Features

- `richer-source-adapters`: add only where actual PDF/web/OCR intake demonstrates a recurring need; keep them optional. Learner explicitly confirmed deferral on 2026-11-10.
- Anki publication/update/delete/reconciliation and nmem writes/synchronization: outside the selected first-release scope; require separate specification and concrete authorization before external writes.
- Multi-learner collaboration, cloud sync, and automatic profile conclusions remain out of scope.
