# learnBase Workspace Rules

- Keep source material, formal knowledge notes, review records, flashcard drafts, and derived reports in their designated areas.
- Knowledge notes in `02-notes/` are the only editable formal knowledge body. Do not keep a second editable copy in SQLite or an external memory service.
- Structured learning events and profile evidence belong in the local SQLite database and must be written through the supported CLI/API. Reports are derived views.
- Every claim imported from a PDF, webpage, or other source must retain a source ID and a locator when available. Mark missing or uncertain evidence explicitly.
- Do not infer a learner's mistake, mastery, confidence, or duration from an answer key or from an agent's explanation. Ask for learner evidence or preserve `unknown`.
- Original source files are read-only by default. Do not move, rename, copy, or delete an external source as part of note intake.
- Keep Anki and other external writes behind an explicit preview and user authorization. Draft creation is not publication.
- Keep domain-specific rules in topic configuration or domain skills. Do not add exam-specific assumptions to the shared core.
- Use stable IDs for topics, sources, notes, and learning events. Titles and paths can change without changing identity.
- Python commands use the active environment's `python3`; the first release has no third-party runtime dependencies.
- Keep design, active feature, task status, and verification evidence in `specs/`; `specs/.active` is the continuation pointer.
- Treat `/Users/yqg/personal/gwy` as an optional reference repository. Consult its workflows or tests only when needed to answer a concrete design question; record the extracted generic rule here or in an ADR. Do not copy its personal notes, learning records, databases, or exam-specific rules.
- Update `docs/current-progress.md` and the umbrella roadmap when a feature changes stage. The target repository is the source of truth for future learnBase work.
- Keep workspace setup and per-topic onboarding separate from external service prerequisites. Anki/nmem are supported by default without enable switches or setup probing. Ask for an Anki deck or remote credentials only when the learner uses the relevant adapter.
- Topic onboarding may collect goals, background, constraints, sources, and progress evidence, but must allow skipping unknowns and require learner review before persisting generated topic configuration.
- Agent Skills own the conversational interview; the CLI validates and stores bounded structured fields. README documents the entry point and status, not the full questionnaire.

## Agent Skills

Read `.agents/skills/learnbase-study/SKILL.md` for the initial source-to-note workflow. Host adapters should link or select this same skill instead of keeping divergent copies.

Read `.agents/skills/learnbase-onboarding/SKILL.md` when starting a topic. It owns the adaptive interview, proposal review, and explicit approval boundary; the CLI validates and stores the approved structured proposal. Host adapters should link or select this canonical skill.

Read `.agents/skills/learnbase-review/SKILL.md` when capturing learner activities/evidence or configuring and inspecting a profile. It owns the review interview and learner approval; the CLI validates and stores bounded records. Host adapters should link or select this canonical skill.

WorkBuddy discovers the project link in `.workbuddy/skills/`. Registration does not activate the skill: select `learnbase-study` in the workspace's project resources. Codex reads the canonical source under `.agents/skills/`.
