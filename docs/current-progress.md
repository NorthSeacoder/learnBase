# Current Progress

**Updated**: 2026-11-10\
**Workspace**: learnBase template\
**Status source**: [`specs/learnbase-template/roadmap.md`](../specs/learnbase-template/roadmap.md) and [`specs/.active`](../specs/.active)

## Decisions

- This repository is the topic-free template source, not a learner workspace. Each learner creates a separate repository from it; setup, topic onboarding, sources, notes, and personal learning facts belong only in that created workspace.
- One repository represents one learner and supports multiple topics.
- Topics form a tree; a knowledge unit or source may link to multiple topics.
- Markdown is the authority for formal knowledge. SQLite is the authority for structured identities and learning facts; reports are derived.
- The core works offline. PDF/web readers, nmem, and Anki are optional adapters.
- Reviews cover question attempts, retrieval practice, reading observations, and practice reflections. Profile claims require traceable evidence; absent evidence remains unknown.
- Workspace setup and interactive per-topic onboarding stay separate from external service prerequisites. Anki/nmem are supported by default without enable switches or setup probing. CLI validates/stores fields; Skills conduct adaptive interviews.
- Anki topic-to-deck mappings may be many-to-many. Existing decks should be reused; remote creation/publication needs preview and explicit authorization.
- No personal records or exam-specific behavior are copied from the source project. The source repository at `/Users/yqg/personal/gwy` is a read-only reference when a concrete question requires it.

## Delivered

`source-note-foundation` is implemented and locally verified. It includes topic creation, PDF/web source registration, stable source IDs, read-only handling of external PDFs, source-linked note generation and validation, and the `learnbase-study` Agent Skill with Codex/WorkBuddy discovery guidance.

`workspace-topic-onboarding` is closed with a historical conditional pass for local use. `learnbase setup` initializes a cloned workspace, and the `learnbase-onboarding` Skill produces a learner-reviewed proposal that the CLI atomically stores with its topic in SQLite. The local test suite replays this flow from a temporary template copy and verifies that the template source remains unchanged. Its deck mapping and preview handoff is now delivered by M3; remote publication remains outside the selected release.

`review-profile-core` is closed with a local PASS. Its SQLite v3 migration, approved idempotent activity writes, source/note provenance, append-only evidence transitions, topic-scoped profile dimensions, and deterministic reports pass the 32-test suite and SDD closeout validation. Profile dimensions remain empty by default; evidence thresholds and recency are configurable; conflicts remain visible without mastery scores.

`flashcards-and-integrations` has a historical local PASS for Basic Q&A Markdown drafts, stable objective/card identity, provenance-preserving merges, explicit reviewed replacements, many-to-many mappings to existing decks, read-only AnkiConnect JSON preview, and read-only nmem Skill guidance. See its [acceptance](../specs/flashcards-and-integrations/acceptance.md) and [verification evidence](../specs/flashcards-and-integrations/verify-evidence.md) for the original implementation snapshot.

`default-integration-support` simplifies those defaults for personal use: Anki/nmem are supported without enable flags; setup remains local, availability is checked when used, and unavailable nmem retrieval is skipped. README documents dependencies and Anki failure behavior. The current 45-test regression suite passes after the change, including Anki without configuration, error/timeout handling, and the fresh-template workflow. Live Anki collections and host-specific nmem retrieval were not exercised; no model behavior eval is claimed. See [acceptance](../specs/default-integration-support/acceptance.md).

The template implementation was committed as `7cd01e865831f7cc13c3e5501f21a94690ee0958` (`feat: add local learning workspace with evidence and card previews`) and successfully pushed to `origin/main` on 2026-11-10, following the learner's explicit request. The 62-file baseline includes the CLI, tests, canonical Skills and host links, docs, and SDD records. Three local execution logs (`task_plan.md`, `findings.md`, `progress.md`) remain outside the commit plan. GitHub's Template setting was not changed; the last recorded value was `isTemplate=false`. A separate clone can now use the pushed implementation.

## Continuation State

`specs/.active` points to the completed `default-integration-support` follow-up. Its 45-test regression and SDD closeout-ready checks pass (E-001..E-004). The earlier M3 context manifest remains historical and is not claimed to describe the revised defaults. Anki publication/reconciliation and nmem writes remain outside the selected first release. Ordinary save failures are rolled back, but process termination/power loss between Markdown and SQLite writes has no journal-based recovery guarantee.

The learner confirmed on 2026-11-10 that no recurring source-extraction problem has appeared. `richer-source-adapters` stays deferred under its original start condition. The agreed local roadmap scope is delivered; [roadmap audit](../specs/learnbase-template/roadmap-audit.md) preserves the requirement-by-requirement coverage and remaining boundaries.

The onboarding closeout record is in [`specs/workspace-topic-onboarding/acceptance.md`](../specs/workspace-topic-onboarding/acceptance.md), with verification details in [`specs/workspace-topic-onboarding/verify-evidence.md`](../specs/workspace-topic-onboarding/verify-evidence.md).

## Next Actions

1. Try the delivered workflow in a separate learner workspace; establish recurring extraction limits before activating optional source adapters.
2. Enable GitHub's Template setting only if separately requested. Commit/push of the implementation is complete; the clean-template copy workflow is tested. See the [commit record](../specs/learnbase-template/commit-plan.md).
