# Data Model: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations` | **Date**: 2026-11-10

## Authority

- `04-cards/drafts/<topic>/<date>-<CARD-ID>.md` is the only editable card body.
- SQLite `cards` stores stable identity and local registry metadata. Relation tables preserve structured references; they do not contain the question or answer.
- Existing notes remain authoritative Markdown in `02-notes/`; SQLite note/source/evidence relations remain authoritative for structured provenance.
- Anki data is read only during explicit preview. nmem results are transient search context only.

## Entities

### `cards`

| Field | Type | Contract |
|---|---|---|
| `card_id` | TEXT PRIMARY KEY | Stable `CARD-NNNN` identity |
| `topic_id` | TEXT NOT NULL FK | One topic per first-release card |
| `objective_key` | TEXT NOT NULL | Learner/Skill-reviewed stable key, unique within a topic |
| `path` | TEXT NOT NULL UNIQUE | Workspace-relative path under `04-cards/drafts/` |
| `created_at`, `updated_at` | TEXT NOT NULL | UTC timestamps |

Constraint: `UNIQUE(topic_id, objective_key)`. Card text is parsed from Markdown when validating or previewing; no front/back columns are stored in SQLite.

### `card_notes`

`(card_id, note_id)` is the primary key. Both columns reference stable card and note rows. The linked Markdown note must pass existing note validation before the relation is saved.

### `card_evidence`

`(card_id, evidence_id)` is the primary key. Evidence must already exist and be linked to a learning activity in the same topic. The card never changes the evidence status or derives a profile conclusion from it.

### `card_sources`

| Field | Type | Contract |
|---|---|---|
| `card_id` | TEXT FK | Card identity |
| `source_id` | TEXT FK | Registered source identity |
| `locator` | TEXT NOT NULL DEFAULT '' | Existing source position; empty means no locator is available |

The primary key is `(card_id, source_id, locator)`. Distinct locators remain distinct rows; source origins are retained through the card's `card_notes` and `card_evidence` relations. Rows are derived from local note/evidence relations, never trusted directly from proposal text.

### `topic_anki_decks`

`(topic_id, deck_name)` is the primary key. Deck names are copied from current AnkiConnect `deckNames` results; this table is a local mapping, not a claim that a deck remains available. Preview rechecks the live deck list. Multiple topics may map to one deck, and one topic may map to several decks.

## Card Markdown Contract

Frontmatter contains `id`, `topic`, `objective_key`, `created`, `updated`, `notes`, `evidence`, and `sources`. Source entries include `id` and `locator`. The body contains one `## Front` and one `## Back` section. Values are encoded as quoted YAML-compatible strings or JSON strings to avoid custom YAML dependencies; the validator rejects missing/duplicate sections and checks frontmatter relations against SQLite.

The CLI renders a complete temporary draft within a SQLite write transaction, replaces the Markdown, then commits relations. On an ordinary operation/commit failure it restores the previous file and rolls back database changes. New drafts use a no-overwrite hard-link operation. This is not a crash-recovery journal: process termination between file replacement and SQLite commit may need manual validation/recovery. Identical replay does not rewrite the file. Front/back remain editable Markdown; structure/identity/provenance are validated, not a database copy or content hash.

## Lifecycle

```text
reviewed proposal
      |
      +-- no objective exists --> create stable card + Markdown + links
      |
      +-- objective exists and explicit target/content match --> union links (idempotent)
      |
      +-- target or content mismatch --> reject with no writes; learner resolves
      |       +-- explicit card_id + replace_content + approval --> revise local body, retain all links
      |
      +-- explicit preview --> read Anki and render result; no local/remote writes
```

There is no `published` state or remote card ID in this feature because Anki publication and reconciliation are out of scope.

## Schema and Migration

Increment the schema marker to v4 and add tables/indexes through the existing idempotent schema setup. Do not build a general migration framework; old-workspace compatibility was explicitly excluded for this new template feature. Existing setup reruns should remain idempotent for the current schema.
