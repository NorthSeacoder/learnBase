# Roadmap

The SDD roadmap and active feature are the source of truth for design and task status: [learnBase template roadmap](../specs/learnbase-template/roadmap.md), [active feature](../specs/.active). Current handoff summary: [current progress](current-progress.md).

Feature plans and task states live under `specs/<feature>/`. Do not maintain a second checklist here.

## M2: Review and learner profile

- Support question review and non-question learning reflections through one activity model.
- Record learner evidence separately from model analysis; preserve unknowns.
- Add idempotent write APIs, evidence references, profile claims, and rebuildable reports.
- Configure profile dimensions per topic, empty by default; use explicit evidence thresholds and avoid mastery scores.
- Add retrieval/practice scheduling only after the evidence and review rules are specified.

## M3: Flashcards and integrations

- Generate card drafts from verified notes and review evidence.
- Deduplicate by learning objective and preserve provenance.
- Deliver optional read-only AnkiConnect preview against existing decks; publication and reconciliation require a future scope.
- Deliver optional read-only nmem retrieval guidance; synchronization remains outside this release.

## Current Execution

The local scope covers source/note foundation, workspace/topic onboarding, evidence-backed review/profile, and Basic Q&A drafts with read-only integration contracts. The follow-up `default-integration-support` removes enable switches for Anki/nmem and documents availability when used; setup remains local. Its current 45-test regression suite covers these workflows and a fresh template copy. `specs/.active` points to this follow-up. Earlier M3 evidence is historical; see the latest feature acceptance and umbrella roadmap for current validation and runtime limits. Anki publication/reconciliation and nmem writes are outside this release.

## Deferred

- Richer PDF/web/OCR adapters: the learner confirmed no recurring extraction problem on 2026-11-10; retain the original evidence-based start condition.
- Anki publication/reconciliation and nmem writes/synchronization.
- Multi-learner collaboration and hosted synchronization.
- A mandatory GUI, cloud database, or model provider.
- Automatic mastery scoring or profile conclusions without evidence.
