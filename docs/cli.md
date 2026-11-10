# CLI Reference

Run commands from a learner-created workspace. `--workspace <path>` may be supplied before the command to select another workspace. Initialize with `setup` before using commands that access SQLite.

## Review Capture

The `learnbase-review` Skill interviews the learner, prepares the JSON proposal, shows it for review, and waits for explicit approval. The CLI validates the proposal and writes the activity, evidence, and provenance links in one transaction.

```sh
python3 tools/learnbase.py review add --proposal - --approved
```

The proposal requires `proposal_version: 1`, a unique `idempotency_key`, `topic_id`, `activity_type`, a type-specific `learner_input` object, and an `evidence` array. `occurred_at` and `assistant_analysis` are optional. The four activity types are `question_attempt`, `recall_practice`, `reading_observation`, and `practice_reflection`. Each evidence item contains a type, reviewed statement, status, dimension links, source links, and note IDs. See the Skill for exact field allowlists.

An identical normalized payload under the same idempotency key returns the existing activity. Reusing the key with changed content fails without writes. Assistant analysis is stored separately and cannot be evidence.

Evidence status transitions require a reviewed proposal and reason:

```sh
python3 tools/learnbase.py review evidence status --proposal - --approved
```

Transitions are append-only in `evidence_status_history`. `superseded` is terminal; evidence rows are never deleted by this command.

## Profile Configuration and Reports

Each topic starts with no profile dimensions. Configure a dimension only after learner review; its rule includes eligible activity/evidence types, a minimum confirmed count, and an inclusive recency window in days.

```sh
python3 tools/learnbase.py profile dimension set --proposal - --approved
python3 tools/learnbase.py profile show --topic biology
python3 tools/learnbase.py profile report --topic biology --output profile.md
```

`profile show` is read-only. `profile report` writes under `reports/`, refuses to overwrite a user-authored file, and atomically replaces a report with the generated marker. Output distinguishes unknown, pending, conflicting, and confirmed evidence; it shows source/note references and an evidence-through date without mastery or confidence scores. Recency uses the learner-supplied activity date, never the database insertion date.

## Local Basic Q&A Drafts

Use the [learnbase-flashcards Skill](../.agents/skills/learnbase-flashcards/SKILL.md) to inspect source passages, select evidence and learning objectives, and review the concrete proposal. Card text is stored only in Markdown under `04-cards/drafts/`; SQLite stores stable IDs and provenance links. Local drafting works offline.

```sh
python3 tools/learnbase.py card draft list --topic biology
python3 tools/learnbase.py card draft save --proposal - --approved
python3 tools/learnbase.py card draft validate 04-cards/drafts/biology/<date>-CARD-0001.md
```

Proposal example (use actual registered IDs):

```json
{
  "proposal_version": 1,
  "topic_id": "biology",
  "objective_key": "cell-membrane-function",
  "front": "What does the cell membrane regulate?",
  "back": "The movement of substances into and out of the cell.",
  "note_ids": ["NOTE-0001"],
  "evidence_ids": ["EVD-0001"]
}
```

The topic and objective key are lowercase ASCII slugs; the key has at most 80 characters. Front/back allow 5000/10000 characters, plain text and line breaks; heading lines are reserved by the draft format. Both ID lists require 1–20 items in the selected topic. Notes must pass note validation. Evidence must already exist as learner-reviewed records; no learner facts are inferred. Registered sources and all available locators are derived from notes/evidence, including notes linked by evidence. Empty locators remain explicit.

One `(topic_id, objective_key)` has one stable card ID. Replaying an identical draft returns that card without modifying it. To merge new sources, include the existing `card_id` and use its current front/back; the CLI unions all note/evidence/source links and preserves the body. Different content raises a conflict with no writes. To resolve it, explicitly review the replacement text, include `card_id` plus `replace_content: true`, and save with `--approved`. Replacement never discards existing provenance.

`card draft validate` checks the Markdown structure, stable identity and relations, and linked notes. It does not verify the truth of a source passage or an agent explanation. Markdown remains editable; rerun validation and review the actual text before integration preview.

## Optional Read-Only AnkiConnect Preview

Anki is supported by default without a configuration switch. Setup makes no adapter request; deck discovery, mapping, or preview checks availability when invoked. Start Anki Desktop and AnkiConnect on `127.0.0.1:8765`. The client uses version 6 read actions, a two-second socket timeout, a 2 MiB response limit, batches of at most 100 note IDs, and at most 10000 Basic notes per deck scope. It supports no arbitrary remote endpoint or write action. API-key-protected endpoints currently return an error; credential configuration is outside this release.

```sh
python3 tools/learnbase.py anki decks
python3 tools/learnbase.py anki map add --topic biology --deck "Existing Deck"
python3 tools/learnbase.py anki map list --topic biology
python3 tools/learnbase.py anki map remove --topic biology --deck "Existing Deck"
python3 tools/learnbase.py anki preview --topic biology
python3 tools/learnbase.py anki preview --topic biology --deck "Existing Deck"
```

Mapping changes only local SQLite. One topic may map to several existing decks and a deck may be shared by topics. Preview rechecks live deck availability and requires the `Basic` model with exactly `Front` and `Back` fields. Preview prints JSON containing Q&A, all sources/locators, evidence statuses, target deck, matching remote note IDs/text and a result: `already_present`, `proposed_addition`, `conflict`, or `skipped`. Linked conflicting or superseded evidence causes `skipped`. HTML formatting is normalized only for remote comparisons. Existing same-front notes with any different answer produce `conflict`. Deck search includes subdecks, which is declared in each preview row.

This release provides no Anki publish/update/delete/deck creation or reconciliation operation. A preview neither changes local drafts nor writes to Anki. Offline, timeout, malformed-response, and API failures leave local cards intact.

## Optional Read-Only nmem Retrieval

nmem is supported by default without a configuration switch. When useful, the flashcards Skill may use an available host read-only search tool or the installed/configured CLI: `nmem m search "<objective>" -n 5`, followed by `nmem m show <memory-id>`. Results are transient retrieval context, never a source citation, reviewed evidence, or a second editable note body. Underlying claims must be verified against local notes and registered sources before drafting. There is no nmem write/sync command. Missing or unavailable retrieval is skipped and does not block the local workflow; setup does not probe or persist service availability.
