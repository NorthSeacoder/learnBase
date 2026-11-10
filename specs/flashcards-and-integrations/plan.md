# Implementation Plan: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)\
**Input**: Clarified feature specification

## Summary

Add learner-approved Basic Q&A drafts as Markdown artifacts with SQLite identity and provenance links. Add an opt-in, read-only AnkiConnect preview and Skill-guided, optional nmem retrieval; no external writes are part of this feature.

## Route Context

| Field | Value |
|---|---|
| Change Profile | high |
| Risk Signals | Persistent identity and provenance; duplicate merge; optional external reads; generated learner-facing artifacts |
| Override | none |
| Upgrade Trigger | Adding external writes, reconciliation, remote identity persistence, or automatic scheduling |
| Execution Mode | direct |
| Fallback | stale reviewer installation; verify uses documented direct review |

## Architecture Overview

```text
validated 02-notes/ + reviewed SQLite evidence
                 |
        learnbase-flashcards Skill
    (draft, inspect duplicates, learner review)
                 |
      approved bounded JSON proposal
                 v
learnbase card draft save --approved
       |                         |
       v                         v
04-cards/drafts/*.md      SQLite card IDs/links
                          notes, sources, locators,
                          evidence, topic/deck map
                                   |
                                   v (explicit read only)
                         AnkiConnect localhost
                         deck/model/note preview

optional nmem retrieval -> Skill context only; never a card citation or write
```

The CLI remains standard-library-only. Local draft save and validation work offline. Network calls occur only for an explicit Anki deck-discovery, mapping, or preview command; the client uses the fixed loopback host and bounded timeout. The Skill handles semantic drafting and optional host-side nmem reads. SQLite stores identity and relations, while the Markdown draft is the sole editable card body.

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| `learnbase-flashcards` Skill | Learner-approved proposal JSON | CLI card draft save | CLI validation and end-to-end test |
| CLI card draft save | Markdown draft + stable card ID and links | Learner and Anki preview | `card validate`; preview returns a result for each selected draft |
| Local notes/review store | Note/source/evidence IDs and locators | Card Markdown and SQLite relation tables | Tests query all persisted links and compare Markdown frontmatter |
| AnkiConnect read-only API | Deck/model/existing Basic note data | Preview classifier | Mock server assertions verify only read actions and preview categories |
| Optional nmem retrieval | Search results | Skill context only | Skill contract states results cannot be cited or persisted as evidence |

**Orphan artifact handling**: nmem results are intentionally ephemeral context, not learning artifacts. Anki preview is a derived report and does not change external or local state.

## Quality Attribute Targets

| Attribute | Target | Design impact | Verification |
|---|---|---|---|
| Provenance integrity | Every card relation points to registered records; source locators remain associated with their note/evidence origin | Validate references and write card file/relations atomically | Invalid-reference, merge, replay, and rollback tests |
| Offline availability | Draft creation, validation, and all core tests need no network | Standard library; Anki isolated behind explicit commands | Offline test suite uses a local mock server only |
| External boundary | No remote mutation; only fixed loopback AnkiConnect reads | No arbitrary endpoint, mutation actions, or nmem write path | Mock server records requested action names and rejects unexpected calls |
| Duplicate safety | One topic/objective maps to one stable card; replay does not duplicate links | Unique constraint and insert-ignore relations; content mismatch rejects | Duplicate and content-conflict tests |
| Failure atomicity | Validation, filesystem, DB, or API errors do not partially alter draft state | Transactional SQLite operations and temporary Markdown replacement | Failure injection and missing/invalid response tests |

## Historical Decision Lookup

- **Query Scope**: `docs/adr/0001-markdown-and-sqlite.md`, `docs/adr/0003-offline-core-and-adapters.md`, `docs/adr/0004-layered-onboarding.md`, onboarding plan/acceptance, review-profile plan/acceptance; queries: Markdown authority, adapter boundary, Anki deck mapping, preview, explicit writes, stable IDs, nmem.
- **Matches**: ADR-0001, ADR-0003, ADR-0004, workspace-topic-onboarding DEC-001/DEC-002 and deferred FR-007, review-profile-core DEC-004/DEC-005. No prior card-specific DEC records.
- **Handling**: `update` for the existing Anki/nmem boundary; new DEC records below for card identity, merge, and preview details.
- **Rationale**: Existing architecture decisions already establish Markdown authority, SQLite identity/evidence, opt-in adapters, and many-to-many Anki deck mapping. This plan narrows the M3 first release to read-only operations and creates the missing card contract.
- **Unverified**: Behavior against a live learner Anki collection; validation uses mocked AnkiConnect responses.

### DEC-001: Keep card content in Markdown and identity/provenance in SQLite

- **Status**: `accepted`
- **Trigger**: high profile; artifact-handoff; persistent card identity
- **Context**: Cards need editable Q&A text plus stable links to notes, sources, locators, and evidence.
- **Options**: A) store card body in SQLite; B) keep Markdown body and store only IDs/relations in SQLite.
- **Decision**: B, under `04-cards/drafts/`; SQLite stores `card_id`, topic, objective key, path, timestamps, and relation rows. Body edits remain in Markdown; validation checks structure and provenance rather than a second body or content hash.
- **Rejected**: A would create a second editable body and conflict with the repository's designated Markdown draft area.
- **Consequences**: CLI validation must detect path/frontmatter/body drift; a file is not considered valid just because its DB row exists.
- **Evidence**: `AGENTS.md`, ADR-0001, `docs/architecture.md`.
- **Upgrade Trigger**: A concrete query/performance need that cannot be served by a derived index.
- **Supersedes / Superseded By**: none

### DEC-002: Deduplicate by explicit topic-scoped objective and merge target

- **Status**: `accepted`
- **Trigger**: explicit learner choice; duplicate/merge contract
- **Context**: A learning objective can be supported by several notes and sources, but should produce one card.
- **Options**: A) automatic semantic merge; B) learner/Skill selects an existing stable card ID and the CLI unions provenance; C) always create separate cards.
- **Decision**: B. `(topic_id, objective_key)` is unique; merge targets the existing card and idempotently adds its note/source/evidence relations while retaining the existing body. Q&A comparison preserves line breaks/internal whitespace (NFC, normalized line endings, surrounding whitespace trimmed). A content mismatch fails with no writes; an explicit `card_id` plus approved `replace_content: true` resolves it locally without removing provenance.
- **Rejected**: A is not deterministic or safely reviewable; C contradicts the confirmed one-card decision.
- **Consequences**: The Skill must inspect existing objective keys and present a merge candidate. This does not claim automatic semantic deduplication.
- **Evidence**: `spec.md` clarified decisions; `tools/learnbase.py` stable topic/note/source ID patterns.
- **Upgrade Trigger**: Learners repeatedly need revision history or explicit alternate formulations for the same objective.
- **Supersedes / Superseded By**: none

### DEC-003: Limit Anki integration to loopback read-only preview

- **Status**: `accepted`
- **Trigger**: explicit learner scope; external-side-effects trait
- **Context**: The first delivery must inspect existing decks and identify duplicates without publishing cards.
- **Options**: A) reviewed export/import file; B) AnkiConnect read-only preview; C) preview and publish in one release.
- **Decision**: B. Call the local AnkiConnect v6 action endpoint for deck/model/note reads; use only `deckNames`, `modelNames`, `modelFieldNames`, `findNotes`, and `notesInfo`. A mapped deck must already exist. No arbitrary host, deck creation, or mutation action is supported.
- **Rejected**: A does not support the selected AnkiConnect workflow; C exceeds the selected first-release scope and adds irreversible external writes.
- **Consequences**: Anki Desktop and AnkiConnect must be running for discovery/preview. All local card work remains offline. New API calls must be added to the allowlist only with an updated decision and tests.
- **Evidence**: ADR-0003, ADR-0004, official API docs: https://github.com/amikey/anki-connect and https://git.sr.ht/~foosoft/anki-connect (Context7 lookup, 2026-11-10).
- **Upgrade Trigger**: A separately clarified publication feature with preview, explicit authorization, receipts, and failure/reconciliation rules.
- **Supersedes / Superseded By**: none

### DEC-004: Keep nmem retrieval opt-in, read-only, and non-authoritative

- **Status**: `accepted`
- **Trigger**: explicit learner scope; optional integration boundary
- **Context**: nmem may help locate context but must not become a second editable note store or provenance source.
- **Options**: A) omit nmem entirely; B) optional read-only Skill/host retrieval; C) sync local notes to nmem.
- **Decision**: B, gated by the workspace's `integrations.nmem` opt-in. Search results are transient context; card claims must be checked against validated local notes and reviewed evidence.
- **Rejected**: A omits the selected scope; C creates an external write path and competing note authority.
- **Consequences**: The core CLI does not implement nmem transport and remains offline. If no read-only host adapter is available, the Skill continues using local notes without failure.
- **Evidence**: `learnbase.toml`, ADR-0001, ADR-0003, clarified `spec.md`.
- **Upgrade Trigger**: A concrete request for nmem writes with an explicit preview/authorization and provenance contract.
- **Supersedes / Superseded By**: none

## Module Design

### Module: Card draft persistence

**Responsibility**: Validate a bounded, learner-approved card proposal; check topic, notes, evidence, and source provenance; write Markdown and SQLite links atomically; validate existing drafts.

**CLI contract**:

```text
learnbase card draft save --proposal <path|-> --approved
learnbase card draft validate <path>
learnbase card draft list --topic <topic-id>
```

The JSON proposal contains a version, `topic_id`, stable `objective_key`, Basic `front` and `back`, one or more local `note_ids`, one or more `evidence_ids`, and optional existing `card_id` merge target. A target must own the same topic/objective. New provenance requires that explicit target. Q&A must match unless learner-approved `replace_content: true` explicitly resolves a content conflict. The CLI derives source IDs/locators from note/evidence links, including notes linked by evidence. An identical replay returns the existing card without rewriting it.

### Module: AnkiConnect adapter

**Responsibility**: List existing deck/model names, persist many-to-many topic/deck choices, and classify local card drafts against an existing deck without writes.

**CLI contract**:

```text
learnbase anki decks
learnbase anki map add --topic <topic-id> --deck <existing-name>
learnbase anki map list [--topic <topic-id>]
learnbase anki map remove --topic <topic-id> --deck <name>
learnbase anki preview --topic <topic-id> [--deck <name>]
```

The adapter requires `integrations.anki = true`, talks only to `127.0.0.1:8765`, uses a two-second socket timeout and 2 MiB response limit, verifies complete result envelopes/IDs, and emits JSON preview rows including Q&A, all provenance, evidence statuses, and remote matches. A same-front/different-back note is a conflict; exact normalized Basic front/back is already present; otherwise it is a proposed addition. Conflicting/superseded evidence causes a skip. Remote HTML formatting is normalized to text; local draft text is never interpreted as HTML. Nested deck search semantics are displayed. The v6 action endpoint is the bounded, documented protocol for this first preview adapter; v1 is a future transport choice, not a repository compatibility layer.

### Module: `learnbase-flashcards` Skill

**Responsibility**: Read and validate local note/evidence context, draft Basic Q&A proposals, inspect existing card IDs before selecting create/merge, present full card and provenance for learner review, and call approved local CLI actions. Optional nmem retrieval is allowed only when enabled and available; it cannot be used as a citation or persisted evidence.

## Data Model

See [data-model.md](data-model.md). Schema v4 adds card identity and relation tables plus `topic_anki_decks`. Card text remains solely in Markdown. Setup creates the additive schema; this feature does not add an old-workspace migration framework.

## Risks and Tradeoffs

- Objective keys are explicit stable identifiers, not automatic semantic similarity. The Skill must surface likely existing candidates and the learner chooses the merge target.
- Requiring identical normalized front/back on merge prevents silent content replacement, but requires a separate reviewed resolution when the wording or answer changes.
- Anki search by deck may include nested decks; the preview must display what was matched and avoid representing the result as an exact isolated deck when Anki semantics include children.
- A localhost service can be unavailable, unauthenticated, or return malformed results. Report a clear error and leave local state unchanged.
- nmem tool availability varies by host. Its absence must not block drafting or verification.

## Verification Strategy

- Unit tests for proposal validation, note validation, evidence/topic ownership, objective uniqueness, idempotent merge, Q&A conflict, Markdown/DB consistency, and failure atomicity.
- CLI end-to-end test covering setup, source/note/review records, approved draft, validation, merge across sources, list, and offline operation.
- Local mock HTTP server tests for AnkiConnect request allowlist, deck/model discovery, exact match/add/conflict classification, unavailable endpoint, timeout, API error, malformed payload, and no write actions.
- Skill and host-link tests verify canonical-source links and the opt-in/read-only nmem contract.
- Run full unit suite, Python compile, `git diff --check`, context freshness, and SDD verify/closeout validators with fresh evidence.

## Stage Readiness

- `data-model.md`: required; new stable entities and relations
- Next step: `implement` through the slices in `tasks.md`
- Blockers: none

## Sources

| Decision | Source | Notes |
|---|---|---|
| Markdown/local identity authority | `AGENTS.md`, ADR-0001 | Repository contract |
| Optional adapters and explicit side-effect boundaries | ADR-0003, ADR-0004 | Existing design decisions |
| AnkiConnect read-only action names, request envelope, note fields | https://github.com/amikey/anki-connect ; https://git.sr.ht/~foosoft/anki-connect | Context7 lookup on 2026-11-10; live Anki behavior remains unverified |
