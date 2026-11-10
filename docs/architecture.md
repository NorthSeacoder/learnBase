# Architecture

learnBase is a repository template, not a hosted application. A cloned repository is a private learning workspace for one learner. The initial release uses a small Python standard-library CLI to initialize local state, register topics and sources, and create traceable note files. Agent Skills orchestrate the parts that require interpretation: reading source material, deciding what is useful, explaining it, and drafting notes.

## Boundaries

| Area | Authority | Purpose |
| --- | --- | --- |
| `01-sources/` and source records | Original files stay at their owner; registry metadata is in SQLite | Provenance, location, source type, content revision, and topic links |
| `02-notes/` | Markdown | Canonical explanations, concepts, examples, and source citations |
| `03-reviews/` | Reserved for optional learner-readable review writeups | No CLI-generated review file is currently authoritative; structured activities and evidence live in SQLite |
| `data/learnbase.sqlite3` | SQLite | Stable topic/source/card identity, approved topic configuration, learning activities/evidence, provenance links, status history, and local topic/deck mappings |
| `04-cards/drafts/` | Markdown | Reviewable card proposals; never proof of mastery or a published Anki card |
| reports | Regenerable output | Evidence-linked learner profile and progress views |

## Topic and knowledge model

Topics have stable IDs and optional parent topics. They can form a hierarchy, but knowledge units and sources may connect to multiple topics. This keeps the navigation tree useful without forcing a concept into exactly one subject. Aliases and redirects can be added when a topic is renamed or merged.

Topic onboarding stores learner-approved learning intent in a one-to-one `topic_config` row keyed by the topic ID. Unknown scalar and list fields remain `NULL`; an empty list means the learner explicitly has no items to add. Suggested source hints are not source records or evidence claims.

## Source-to-note flow

1. Register a PDF, webpage, or other source. The registry stores an ID, type, location, title, topic links, and a content fingerprint when a local file is readable.
2. An agent reads the source using a host capability or a user-provided extraction. The source itself is not modified.
3. The agent proposes a note that separates verified content from interpretation and includes source IDs plus page/section/URL anchors.
4. Save the note as Markdown and validate that every cited source ID exists.
5. The learner reviews the note. Review evidence and card drafts may refer back to the stable note ID and source locators.

The v1 CLI records provenance and prepares note files; it does not bundle a PDF parser, web crawler, OCR service, or model API.

## Evidence and profile

A learning activity may be a question attempt, retrieval exercise, reading reflection, or practice reflection. Learner-provided responses, confidence, duration, and remembered approach remain separate from assistant analysis. Profile dimensions are configured per topic and start empty. Reports use explicit eligibility, confirmed-evidence thresholds, and recency windows; they show scope and evidence references without mastery or confidence scores. No evidence means unknown, not zero or mastered. Conflicting evidence remains visible with its history until the learner explicitly resolves it.

## Integrations

The core has no network requirement. Optional adapters may connect nmem for source/knowledge retrieval and Anki for card publication. An adapter must preserve the core's IDs and evidence links, expose a preview, and report its write receipt. External failure must not erase local records. The canonical skill lives in `.agents/skills/`; WorkBuddy uses a relative project link in `.workbuddy/skills/` and requires explicit project-resource selection.

The current flashcard slice stores Basic Q&A only in Markdown. SQLite holds a unique topic/objective card ID, path/timestamps, and note/evidence/source-locator relations. Approved merges union provenance; a distinct approved replacement explicitly revises the local body without removing links. Identical replay leaves the artifact unchanged. Validation checks references and linked notes; the conversational Skill checks factual content against source passages.

The implemented AnkiConnect adapter is read-only: deck/model/note queries on loopback, bounded HTTP responses/timeouts, local many-to-many deck mappings, and JSON previews. Previews include the Q&A, provenance, evidence status, and remote matches; Anki search includes subdecks. No Anki publication/reconciliation or nmem transport/write exists in the core. nmem retrieval is performed by the Skill's host and remains transient non-authoritative context. Both integrations are supported by default with no enable switch. Setup stays local; service availability is determined when used. The Anki CLI reports unavailability; the Skill can continue with local drafts and skip unavailable nmem retrieval.
