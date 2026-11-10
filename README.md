# learnBase

learnBase is a local-first learning workspace template for one learner studying multiple subjects. It keeps knowledge in Markdown, tracks learning evidence in SQLite, and lets agent skills guide source intake, review, learner profiles, and optional flashcard integrations.

## Template Lifecycle

This repository is the reusable, topic-free template source. Do not use it as a learner's workspace or store real learner settings, topics, sources, or notes here. Create a separate repository from this template first; workspace setup and topic onboarding happen in that new repository. The source template should remain usable as a clean starting point for every learner.

## Start

In a newly created learning repository, run the deterministic workspace setup, then use the `learnbase-onboarding` Skill to shape and review a topic proposal. The CLI also supports manually adding a topic. See [current progress](docs/current-progress.md) for the implementation status. Neither setup nor topic onboarding requires Anki or nmem.

Requires Python 3.11 or newer; no third-party runtime packages are needed.

```sh
python3 tools/learnbase.py setup --name "My Learning Base"
python3 tools/learnbase.py topic add language --name "Language"
python3 tools/learnbase.py source add web --url https://example.org/article --title "Example article" --topic language
python3 tools/learnbase.py note new --title "Article notes" --topic language --source SRC-0001 --locator SRC-0001=section:Key%20findings
```

For a PDF, register its path with `source add pdf --path ...`. Source registration records provenance; it does not copy, move, or alter the original file. Use the `learnbase-study` Agent Skill to extract and organize source material into a cited note with the available host tools.

## First-Use Setup

- **Workspace setup** initializes local folders and the SQLite registry. It asks no interview questions; rerunning it without `--name` preserves the current workspace name.
- **Topic onboarding** happens when starting a new subject. The `learnbase-onboarding` Skill helps define the intended outcome, existing background, time constraints, useful sources, and future progress signals. Unknown or skipped answers stay unknown, and the complete proposal is reviewed before saving.
- **Integrations** support Anki and nmem by default, with no enable switches or setup detection. Their services are needed only when used. Topic-to-deck mapping may be many-to-many and shared decks are allowed. Remote deck creation or card publication requires a preview and explicit authorization.

Workspace setup and the topic-onboarding Skill are implemented. The Skill is available at [`.agents/skills/learnbase-onboarding/`](.agents/skills/learnbase-onboarding/) and through the WorkBuddy project link; select it in WorkBuddy's project resources when starting a topic. The CLI saves the reviewed proposal only after explicit approval. The detailed interview belongs in the Skill; this README stays a short entry point.

Review capture and evidence-backed profiles are available through the [`learnbase-review` Skill](.agents/skills/learnbase-review/SKILL.md). Configure dimensions per topic; none are enabled by default. CLI commands are summarized in the [CLI reference](docs/cli.md).

The [`learnbase-flashcards` Skill](.agents/skills/learnbase-flashcards/SKILL.md) creates reviewed Basic Q&A drafts and merges the same objective across sources while retaining provenance. AnkiConnect preview reads existing decks/cards; nmem retrieval provides search context only. Publication and synchronization are outside this release.

## Anki and nmem

Both integrations are supported by default. `setup` initializes local state without checking, installing, or starting either service. Availability is checked when used; no integration flags belong in `learnbase.toml`.

| Integration | Prerequisites | When unavailable |
|---|---|---|
| Anki preview | Anki Desktop running with AnkiConnect at `127.0.0.1:8765`; a `Basic` note type with `Front` and `Back` fields | The CLI reports an error; the Skill explains that preview was skipped and continues local drafting |
| nmem retrieval | An available host read-only search tool, or an installed/configured `nmem` CLI with its service reachable | The Skill skips retrieval and continues from local notes |

```sh
python3 tools/learnbase.py anki decks
python3 tools/learnbase.py anki preview --topic language --deck "Languages"
```

Use an existing topic and deck in your workspace. The flashcards Skill can use `nmem m search "<topic or objective>" -n 5` for relevant context. Anki operations in this release are read-only; nmem results never replace local notes or learning evidence. See the [CLI reference](docs/cli.md) for mappings and preview details.

## Workspace

- `01-sources/`: source manifests and locally owned source copies, when intentionally added.
- `02-notes/`: authoritative knowledge notes, organized by topic.
- `03-reviews/`: review records and reflection notes.
- `04-cards/drafts/`: flashcard drafts before any external publication.
- `data/learnbase.sqlite3`: topic/source registry, approved topic configuration, activities/evidence, profile dimensions, card identities/provenance, and local topic/deck mappings.
- `.agents/skills/`: host-neutral Agent Skills. Host-specific instructions belong in a thin adapter, not in the learning model.

## Principles

- One repository represents one learner and may contain many related or independent topics.
- Markdown is the authority for knowledge content. SQLite is the authority for structured learning facts and their evidence.
- Topics form a tree; knowledge may link to multiple topics.
- A profile is a derived, evidence-linked view. Unknown stays unknown; generated advice is not a learner fact.
- The core works offline. nmem, Anki, web fetchers, and PDF extractors are optional adapters.
- Original sources are read-only by default. A source reference never implies permission to modify or redistribute it.

See [the roadmap](docs/roadmap.md), [architecture](docs/architecture.md), [decisions](docs/adr/), and [glossary](docs/glossary.md).
