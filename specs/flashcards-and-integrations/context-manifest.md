# Context Manifest: flashcards-and-integrations

**Workspace**: `flashcards-and-integrations`\
**Created**: 2026-11-10\
**Status**: closed

## Implement Context

Historical implementation-entry context; Check Context below records the verified final revisions.

| File / Source | Reason | Phase | Required | Revision | Observed At | Freshness | Summary |
|---|---|---|---|---|---|---|---|
| `specs/flashcards-and-integrations/spec.md` | User-approved card, merge, and adapter boundaries | implement | yes | unknown | 2026-11-10 | unknown | Basic Q&A; one topic/objective card; local drafts; Anki read-only preview; nmem read-only opt-in |
| `specs/flashcards-and-integrations/plan.md` | Architecture, DEC records, API and failure contracts | implement | yes | unknown | 2026-11-10 | unknown | Markdown authority, SQLite IDs/links, fixed loopback read-only adapter |
| `specs/flashcards-and-integrations/tasks.md` | Slice boundaries and acceptance mapping | implement | yes | unknown | 2026-11-10 | unknown | T001-T006 create, merge, preview, Skill, and closeout sequence |
| `specs/flashcards-and-integrations/data-model.md` | Table/key and Markdown contracts | implement | yes | unknown | 2026-11-10 | unknown | Card identity/relations, topic-deck map, no duplicate card body |
| `tools/learnbase.py` | Current schema, CLI patterns, note/evidence validation and atomic writes | implement | yes | unknown | 2026-11-10 | unknown | Standard-library SQLite CLI; schema v3 baseline |
| `tests/test_learnbase.py` | Regression fixtures and current CLI test approach | implement | yes | unknown | 2026-11-10 | unknown | 32-test baseline covers source, onboarding, review, profile |
| `.agents/skills/learnbase-review/SKILL.md` | Ensure card references use reviewed evidence without inferring learner facts | implement | yes | unknown | 2026-11-10 | unknown | Skill owns interview; CLI validates approved structured proposal |
| `AGENTS.md` | Workspace authority, external-write and source provenance rules | implement | yes | unknown | 2026-11-10 | unknown | Markdown notes authoritative; SQLite structured facts; writes need approval |
| `docs/architecture.md` | Existing ownership boundaries and adapter model | implement | yes | unknown | 2026-11-10 | unknown | Local-first architecture with reserved card drafts and optional adapters |
| `docs/cli.md` | Current command grammar and approval pattern | implement | yes | unknown | 2026-11-10 | unknown | Existing approved JSON proposal CLI style |

## Check Context

| File / Source | Reason | Phase | Required | Revision | Observed At | Freshness | Summary |
|---|---|---|---|---|---|---|---|
| `specs/flashcards-and-integrations/spec.md` | Verify every user story and approved exclusion | verify | yes | sha256:ea8ea6f9079f376399357b81b60e7349e63eb96c53db35323e7d0f6124712863 | 2026-11-10T11:50:21+00:00 | fresh | FR-001..FR-011; local verification PASS and closeout boundary |
| `specs/flashcards-and-integrations/plan.md` | Check DEC contracts and architecture drift | verify | yes | sha256:e4ae41e09955cdf19bfc7021f1874b7d89d205aa618cb0390b6aa273ade06a74 | 2026-11-10T11:50:21+00:00 | fresh | DEC-001..DEC-004; direct review with stale-reviewer fallback |
| `specs/flashcards-and-integrations/tasks.md` | Check implementation/evidence coverage and task completion | verify | yes | sha256:e3e35a7b9745151a2b2111c09dc37965f3332b019779417e7cdc6c1b84c6fd9a | 2026-11-10T11:50:21+00:00 | fresh | T001..T006 with dependency, requirement and verification mappings |
| `specs/flashcards-and-integrations/data-model.md` | Check SQLite/Markdown ownership and persistence semantics | verify | yes | sha256:8ebbc2bff30fbea4aa08c1cbc4ed08e533e6b9471bdd2bb83355e11c19929994 | 2026-11-10T11:50:21+00:00 | fresh | v4 IDs/relations; ordinary failure rollback; no crash journal guarantee |
| `tools/learnbase.py` | Verify card proposal, file/DB writes and read-only HTTP boundary | verify | yes | sha256:644a3b298eacba098e5fce668b140afa251a4f680595c1059bcc54cde5941384 | 2026-11-10T11:50:21+00:00 | fresh | Reviewed card/Anki implementation; snapshot matches tested bytes |
| `tests/test_learnbase.py` | Check runtime proof and all prior workflow regressions | verify | yes | sha256:9836d6815dcf6a80fbe1f9e5b76cff70e30b2637e5d74f7165de17e079751f84 | 2026-11-10T11:50:21+00:00 | fresh | 45 tests; full template replay; rollback and loopback HTTP fixtures |
| `specs/flashcards-and-integrations/verify-evidence.md` | Inspect current implementation baseline and actual evidence ledger | verify | yes | sha256:779a1bc950d4ac1bf0858ceacdc27138765e168b8b3b587b1f544c2d741d5464 | 2026-11-10T11:50:21+00:00 | fresh | 45 tests, syntax/hygiene and direct review; explicit environment limitations |
| `.agents/skills/learnbase-flashcards/SKILL.md` | Check approval, merge handoff and optional nmem contract | verify | yes | sha256:a49aabe98fb33851d283ea004bdeae9958f58fc07848e20e30c920f33e410fe7 | 2026-11-10T11:50:21+00:00 | fresh | Canonical guidance; no nmem write or automatic Anki publication |
| `learnbase.toml` | Confirm no integration is enabled in the template | verify | yes | sha256:da7ab3c08f98dc12f6c3037199720dfd750af01338780b9c1a2afacde606a247 | 2026-11-10T11:50:21+00:00 | fresh | nmem=false; anki=false; no learner topic or personal data |

## Research Context

| File / Source | Reason | Phase | Verified |
|---|---|---|---|
| https://github.com/amikey/anki-connect | Verify v6 action names, request envelope, and read-only note fields | plan / implement / verify | yes, via Context7 on 2026-11-10 |
| https://git.sr.ht/~foosoft/anki-connect | Confirm current API documents legacy v6 availability and current API guidance | plan / verify | yes, via Context7 on 2026-11-10 |

## Rules

- Re-read changed required entries before verify and update revision/freshness then.
- Live Anki/nmem behavior is outside the local verification environment; mock the Anki contract and report the limitation.
- Never call a write-capable adapter action during tests or verification.
