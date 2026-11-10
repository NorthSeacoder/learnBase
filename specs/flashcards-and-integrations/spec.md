# Feature Specification: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations`\
**Created**: 2026-11-10\
**Status**: Closed with local PASS\
**Input**: Create learner-reviewed, source-traceable basic Q&A card drafts from validated notes and reviewed learning evidence, with optional read-only AnkiConnect preview and nmem retrieval.

## Change Profile

| Field | Value |
|---|---|
| Change Profile | high |
| Risk Signals | Persistent card identity/provenance, duplicate merging, external adapter boundary, learner-facing generated artifacts |
| Override | none |
| Upgrade Trigger | Any Anki write, reconciliation, automatic scheduling, or nmem write is added |

## Feature Traits

| Trait | Hit | Basis |
|---|---|---|
| multi-stage-workflow | yes | Draft, learner review, adapter preview, and any future publication are separate steps |
| external-side-effects | yes | Optional adapters access AnkiConnect and nmem; first release is read-only |
| artifact-handoff | yes | Cards link notes, registered sources, locators, and reviewed evidence |
| user-visible-output | yes | Card drafts and previews are learner-facing |
| decision-capture | yes | Persistent identity, merge, and adapter contracts affect future behavior |
| prior-closure-failure | no | New feature |
| bugfix-loop-breaker | no | Not a bug fix |

## User Scenarios

### Story 1: Create traceable card drafts (P1)

As a learner, I want a basic question/answer card proposal grounded in validated notes and reviewed learning evidence, so that I can inspect its wording and provenance before using it.

**Acceptance**: The CLI persists an approved draft under `04-cards/drafts/`, assigns a stable card ID, and retains note, source, locator, and evidence references. The card Markdown is the only editable card body. A note must pass note validation before it is linked. Card creation never implies publication or mastery.

### Story 2: Merge one learning objective across sources (P1)

As a learner, I want one card for the same learning objective even when several sources support it, so that review does not create redundant cards and provenance is not lost.

**Acceptance**: The learner/Skill resolves an incoming proposal to an existing card ID for the same topic and objective. A reviewed merge unions all note/source/locator/evidence links. Replays are idempotent. A proposal with different question or answer text cannot silently replace an existing card; it fails without writes and requires an explicit reviewed resolution.

### Story 3: Preview cards against existing Anki decks (P1)

As a learner, I want to inspect existing decks and compare approved drafts before any Anki change, so that I can reuse my collection without accidental writes.

**Acceptance**: Topic-to-deck mappings are many-to-many and point only to existing decks. The first release uses AnkiConnect read-only calls to inspect decks and matching Basic notes. Preview reports exact matches, proposed additions, and conflicts/skips. It has no create, update, delete, or deck-creation operation.

### Story 4: Retrieve optional nmem context (P2)

As a learner, I want an opt-in read-only search of nmem to help locate relevant context, while keeping local Markdown notes authoritative.

**Acceptance**: nmem is off by default and is used only when the learner enables it. Search results may help the Skill locate local notes for verification; they are not source citations, learner evidence, or permission to write to nmem. Cards remain grounded in validated local notes and reviewed evidence.

## Requirements

- **FR-001**: Create a card only from at least one validated local note and at least one learner-reviewed learning-evidence record. Assistant analysis, answer keys, and nmem results are not learner evidence.
- **FR-002**: Support one first-release card format: `Basic` question/answer (`front`, `back`). Cloze and other card formats are out of scope.
- **FR-003**: Store editable card content as Markdown under `04-cards/drafts/`; SQLite stores stable card identity, path/timestamps, and relations, not a second editable card body.
- **FR-004**: Every card must retain stable note IDs and evidence IDs plus the registered source IDs and locators derivable from its linked notes/evidence. Missing source locators remain explicitly empty/unknown.
- **FR-005**: Deduplicate through an explicit stable objective key scoped to a topic and learner-reviewed merge target. Merge adds provenance idempotently and preserves the existing card ID. Different card content for an existing objective is a conflict; replacing the local body requires an explicit `card_id`, `replace_content: true`, and learner approval, preserving all existing provenance.
- **FR-006**: Saving or merging a card proposal requires an explicit `--approved` confirmation from the Skill/learner. Invalid proposals or failed filesystem/database writes leave no partial card or relation updates.
- **FR-007**: Allow many-to-many topic-to-existing-Anki-deck mappings. Read current deck names through AnkiConnect before mapping; never create a deck in this feature.
- **FR-008**: Anki preview uses read-only AnkiConnect operations and clearly displays the target deck and comparison result. There is no Anki publication command in this feature.
- **FR-009**: AnkiConnect is called only by an explicit preview/deck-discovery command, through the loopback endpoint, with a bounded timeout. Offline setup, drafting, validation, and tests do not require Anki.
- **FR-010**: nmem retrieval is optional, disabled by default, read-only, and owned by the conversational Skill/host adapter. The core CLI has no nmem write or sync operation.
- **FR-011**: Keep all external adapters optional; local card drafting and validation work offline.

## Explicitly Out of Scope

- Publishing, updating, deleting, or reconciling Anki notes/cards; creating Anki decks; importing Anki review history.
- Any nmem create/update/delete/sync operation or use of nmem as an editable note store.
- Cloze cards, automatic scheduling, mastery inference, profile changes, and model-driven automatic publication.
- Automatic semantic deduplication without learner review.

## Clarified Decisions

- **Card format**: basic question/answer only for the first slice.
- **Same objective across sources**: one card with all provenance retained; merge resolves to an existing stable card ID.
- **Anki/nmem scope**: local drafts plus read-only AnkiConnect preview; nmem read-only retrieval only.
- **Deck mapping**: preserve the earlier many-to-many mapping decision and reuse existing decks.
- **Write boundary**: preview is the maximum external Anki behavior in this feature; publishing/reconciliation remains a later explicitly authorized feature.

## Stage Readiness

- Current step: closeout complete
- Clarification blockers: none
- Required design: SQLite card identity/provenance relations; Markdown card validation; read-only loopback AnkiConnect preview; optional Skill-level nmem retrieval.
- The 45-test suite and mocked AnkiConnect contract/failure tests pass against the recorded implementation snapshot. Context freshness and SDD closeout-ready validation passed; see `verify-evidence.md` E-001..E-006 and `acceptance.md`.
