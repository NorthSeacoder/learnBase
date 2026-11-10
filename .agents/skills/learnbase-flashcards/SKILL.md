---
name: learnbase-flashcards
description: Draft learner-reviewed Basic question/answer cards with local note and evidence provenance, merge learning objectives across sources, and optionally preview against Anki or retrieve nmem context without external writes.
---

# learnBase Flashcards

Use this skill for flashcard drafting, same-objective merging, and optional read-only integration preview. Follow `AGENTS.md`. Knowledge notes in `02-notes/` are authoritative knowledge; editable card text lives only in `04-cards/drafts/`. SQLite owns card identity and structured links. Drafting and preview never imply publication or mastery.

## Gather Local Context

1. Identify the topic and intended learning objective. Run `python3 tools/learnbase.py card draft list --topic <topic-id>` and read likely existing cards before selecting a new objective key. Semantic equivalence is a learner-reviewed choice; the CLI compares explicit keys and content.
2. Read the local notes and cited source passages. Validate each note with `python3 tools/learnbase.py note validate <path>`. Registration/validation checks IDs and locators; it does not prove the note's claims are correct. Check the cited material, preserve conditions and uncertainty, and leave unavailable locators explicitly unknown.
3. Read relevant existing learning evidence from SQLite through the supported profile view (`python3 tools/learnbase.py profile show --topic <topic-id>`) or read-only SQLite queries for activity/evidence and provenance rows. Need at least one existing note ID and one reviewed evidence ID in the selected topic. Read-only lookup is permitted; all evidence writes must use the supported CLI.
4. Never infer a learner's mistake, confidence, duration, outcome, or mastery from a source, answer key, Anki history, nmem result, or assistant explanation. If no relevant learner evidence exists, use the canonical [learnbase-review](../learnbase-review/SKILL.md) conversation to obtain it, or stop drafting until evidence is available. Do not manufacture evidence just to satisfy a command.

## Draft and Review

Create one Basic question/answer card for each learning objective. Keep the prompt focused and the answer accurate, bounded, and useful for recall. Cloze and other note types are outside this release. Front/back are plain text with line breaks and optional inline notation; heading lines are reserved by the file format.

Prepare this bounded JSON proposal:

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

Use actual registered IDs. The CLI derives all source IDs/locators through note/evidence links; do not invent source fields. Limits: objective key is a lowercase ASCII slug of at most 80 characters; front at most 5000 characters; back at most 10000; 1–20 note IDs and 1–20 evidence IDs.

Show the learner the full question, answer, objective, note/evidence IDs and their statuses, all sources/locators, and whether this creates or merges a card. Surface unknown/pending evidence; conflicting or superseded evidence prevents Anki preview eligibility. Invite corrections. Save only after explicit approval of the concrete proposal:

```sh
python3 tools/learnbase.py card draft save --proposal - --approved
```

Pass reviewed JSON on stdin. Validate and read the resulting Markdown draft back:

```sh
python3 tools/learnbase.py card draft validate <draft-path>
```

## Merge or Revise an Existing Objective

Reuse the existing `objective_key` and add its explicit `card_id` when adding notes/evidence. Show the union of old and incoming provenance before approval. Identical replays return the existing card. A merge retains its stable ID, existing question/answer, and every source locator; it never discards old provenance.

If front/back differ, the CLI rejects the proposal. Present existing and proposed text plus all provenance for learner review. Only after the learner explicitly approves replacing the content, send the existing `card_id`, the complete approved text and `replace_content: true`. This changes only the local draft and preserves existing provenance. Do not set `replace_content` automatically to bypass a conflict.

## Optional Anki Preview

Anki is supported by default; no enable setting or setup probe is needed. Use the adapter when preview is relevant. Do not request an Anki deck or credentials during workspace setup or topic onboarding. If Anki is unavailable, explain that preview could not run and continue with local drafting; never present an unavailable preview as a successful comparison.

Anki Desktop plus AnkiConnect must be running on `127.0.0.1:8765`. Discover existing decks; reuse them. A topic may map to several decks and a deck may serve several topics:

```sh
python3 tools/learnbase.py anki decks
python3 tools/learnbase.py anki map add --topic <topic-id> --deck <existing-deck-name>
python3 tools/learnbase.py anki map list --topic <topic-id>
python3 tools/learnbase.py anki preview --topic <topic-id>
```

`--deck <existing-deck-name>` may select one preview target without saving a mapping. The collection must have a note type named `Basic` with exactly `Front` and `Back` fields. The preview displays local Q&A, provenance, evidence statuses, existing matching note IDs/text, target deck and the fact that Anki deck search includes subdecks. Results are `already_present`, `proposed_addition`, `conflict`, or `skipped`. Formatting in remote HTML is normalized for comparison; no remote HTML is executed. Anki unavailability or an invalid response leaves local drafts intact.

This release has no publish, update, delete, deck creation, sync, or reconciliation command. Do not call another tool to publish as an implicit continuation of preview. Any future external write needs a concrete reviewed preview and separate explicit authorization.

## Optional nmem Retrieval

nmem is supported by default; no enable setting or setup probe is needed. When retrieval would help, use an available host read-only search tool, or the installed and configured CLI:

```sh
nmem m search "<topic or learning objective>" -n 5
nmem m show <memory-id>
```

Treat results as transient retrieval context. Preserve the result's memory ID for discussion, then locate and verify the underlying local note/source before using a claim. nmem results are not source IDs, card citations, reviewed evidence, or another editable knowledge body. Do not call add/update/delete/sync or save local notes to nmem. If retrieval is unavailable, state that briefly and continue from local material. Local drafting needs neither nmem nor Anki.
