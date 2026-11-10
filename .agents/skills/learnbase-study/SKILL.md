---
name: learnbase-study
description: Organize learning material from PDFs, webpages, and other sources into cited Markdown notes in a learnBase workspace. Also supports review preparation and evidence-linked study records as those phases are enabled.
---

# learnBase Study

Use this skill for source intake and knowledge-note creation in a learnBase workspace. Follow the repository's `AGENTS.md`; the local Markdown note is the canonical knowledge body.

## Source to note

1. Identify the learner's requested topic and intended use. Reuse an existing topic where possible; create a new topic only when asked or clearly needed.
2. Register the source before extracting it:
   - PDF: `python3 tools/learnbase.py source add pdf --path <path> --title <title> --topic <topic-id>`
   - Web: `python3 tools/learnbase.py source add web --url <url> --title <title> --topic <topic-id>`
   - Repeat `--topic` when the source serves more than one topic.
3. Read the source itself. Use a PDF-capable reader/OCR tool for PDFs and a web reader/browser for URLs. A search snippet is not a substitute for the cited page. Keep page, heading, timestamp, or URL fragment locators.
4. Separate source statements from explanation, examples, and inference. Preserve definitions, conditions, units, exceptions, and uncertainty. Do not invent missing content.
5. Create a note linked to every source used:
   `python3 tools/learnbase.py note new --title <title> --topic <topic-id> --source <SRC-ID> --locator <SRC-ID>=<page-or-section>`
   Repeat `--topic`, `--source`, and `--locator` for additional links. Add concrete source locators to each citation in the note.
6. Run `python3 tools/learnbase.py note validate <note-path>`. Read the note back and check the cited passages against the original before treating it as verified knowledge.

## Review and cards

Use the canonical [`learnbase-review`](../learnbase-review/SKILL.md) skill to capture learner-reviewed activities, configure topic-specific profile dimensions, and inspect reports. Keep the source-to-note workflow separate from review capture: a note is not evidence that the learner demonstrated a capability. Never treat an Anki review result as a verified assessment or publish external cards without an explicit preview and authorization.

Use the canonical [`learnbase-flashcards`](../learnbase-flashcards/SKILL.md) skill to create learner-reviewed Basic Q&A drafts, merge the same objective across sources, and run read-only AnkiConnect preview or nmem retrieval when useful and available. Both are supported by default without enable settings. Draft creation is local and keeps every source locator.
