# Verify Evidence: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Implementation Baseline

| Field | Value |
|---|---|
| Implementation Baseline | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 |
| Baseline Scope | `tools/learnbase.py`, `tests/test_learnbase.py`, README, workspace config/rules, canonical Skills, CLI/architecture/glossary docs |
| Captured At | 2026-11-10T11:01:59Z |

The snapshot identifier is SHA-256 of the JSON map below, serialized with `json.dumps(map, sort_keys=True)`. The working tree is uncommitted. Stage/acceptance/progress records are excluded to avoid circular hashes.

| File | SHA-256 |
|---|---|
| `tools/learnbase.py` | 644a3b298eacba098e5fce668b140afa251a4f680595c1059bcc54cde5941384 |
| `tests/test_learnbase.py` | 9836d6815dcf6a80fbe1f9e5b76cff70e30b2637e5d74f7165de17e079751f84 |
| `README.md` | 4361b0166f4fcd0560438e12244dd3156652c899b3bbea2e2c74e2f0805f68d8 |
| `learnbase.toml` | da7ab3c08f98dc12f6c3037199720dfd750af01338780b9c1a2afacde606a247 |
| `AGENTS.md` | ed92cf196dcf3cb49982dad312d37769dc0d97c6cff6e2c253319f7b18badfc0 |
| `docs/cli.md` | 090f2e76fd6efcdcc35dab22a4912a37a82ecadbff58928b88cd839b4b239ce4 |
| `docs/architecture.md` | b0dfcfae8cbd4a0d5989c3526156ee774a322206faeafdd88b8126da1c5e65eb |
| `docs/glossary.md` | 531be9db677251a86e49f8b90bb5079c30c1ff1844070271f7d4071bf79e01ca |
| `.agents/skills/learnbase-flashcards/SKILL.md` | a49aabe98fb33851d283ea004bdeae9958f58fc07848e20e30c920f33e410fe7 |
| `.agents/skills/learnbase-onboarding/SKILL.md` | fb87332cf4d6c4b54706ac88867c6da7434f0670fa8533524be46f85a3f5f792 |
| `.agents/skills/learnbase-review/SKILL.md` | c2a37172ee9cfd3ba002860fed4301b899da7a9678616e9923c15741a8423788 |
| `.agents/skills/learnbase-study/SKILL.md` | 5808a5c2f65d024ffe2cd74f6daf0f10fd30acdf7b2b1796a03f5395e72e5ae7 |

## Evidence Ledger

| ID | Maps To | Action | Result | Exit/Verdict | Observed At | Based On | Scope | Source | Status |
|---|---|---|---|---|---|---|---|---|---|
| E-001 | FR-001..FR-011, DEC-001..DEC-004, T001..T005 | `rtk proxy python3 -W error::ResourceWarning -c` unittest discovery with captured routine stdout | 45 tests passed, including original source/onboarding/profile regressions, cards, rollback, loopback HTTP mock, CLI JSON, and template-copy replay | exit 0 | 2026-11-10T11:01:59Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Local CLI, schema, persistence, adapter protocol, and Skill discovery | `tests/test_learnbase.py`; Test Map below | fresh |
| E-002 | T001..T006 | `rtk python3 -m compileall -q tools tests`; Python AST parse of source/test files | Python sources compiled and AST parsing passed | exit 0 | 2026-11-10T11:01:59Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Python syntax | compileall command output; AST parse output | fresh |
| E-003 | T006 | `rtk git diff --check`; Markdown trailing-whitespace scan; template runtime check | No whitespace errors; template source contains no learner database | exit 0 | 2026-11-10T11:01:59Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Tracked diff, docs/specs/Skills, template hygiene | command outputs; template-copy regression test | fresh |
| E-004 | DEC-001..DEC-004, T006 | Direct review of card proposal/parser/persistence, HTTP boundary, preview, CLI, Skill, and tests | No blocking finding after fixes for explicit replacement, idempotent replay, body preservation, response completeness, opt-in gates, and path containment | PASS | 2026-11-10T11:01:59Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Correctness, external boundary, tests, performance, maintenance | Review and Limitations below; `tools/learnbase.py` card/Anki functions | fresh |
| E-005 | T006, FR-001..FR-011 | `rtk ruby /Users/yqg/.agents/skills/sdd/scripts/check-context-freshness.rb --workspace-root /Users/yqg/personal/libs/learnBase --manifest specs/flashcards-and-integrations/context-manifest.md --phase verify` | All 9 required Check Context entries fresh; read_required and blocked_by empty; tested snapshot has 12 matching file hashes | exit 0 | 2026-11-10T11:48:08Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Actual source revisions, spec/plan/task coverage, Skill/config boundaries | `context-manifest.md` Check Context; checker JSON summary; independent snapshot recomputation | fresh |
| E-006 | T006 | `rtk bash /Users/yqg/.agents/skills/sdd/scripts/validate-sdd.sh --workspace-root /Users/yqg/personal/libs/learnBase --closeout-ready` | validate-sdd: OK; task completion, evidence ledger, acceptance, decisions and roadmap structure pass; local-link/whitespace scan also reports no issue and template has no learner DB | exit 0 | 2026-11-10T11:48:08Z | snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134 | Local SDD closeout and template documentation consistency | `acceptance.md`, `tasks.md`; umbrella `roadmap-audit.md`, `roadmap.md`, `commit-plan.md`; validation output | fresh |

## Test Map

| Requirements | Authoritative tests / checks |
|---|---|
| FR-001, FR-002, FR-003, FR-004, FR-006 | `test_approved_card_draft_persists_markdown_and_traceable_links`, `test_card_proposal_rejects_unlinked_evidence_and_cli_validation`, `test_card_file_collision_bad_note_and_invalid_proposals_never_write_rows`, `test_card_topic_ownership_tamper_and_path_escape_are_rejected` |
| FR-004, FR-005 | `test_card_merge_unions_provenance_idempotently_and_rejects_content_conflict`, `test_card_replay_replacement_and_failed_write_preserve_local_state`, `test_card_merge_preserves_multiple_locators_and_rolls_back_failed_commit` |
| FR-007, FR-008, FR-009 | `test_anki_preview_uses_only_read_actions_and_classifies_existing_basic_notes`, `test_anki_adapter_rejects_mutating_actions_and_api_errors`, `test_anki_malformed_transport_and_preview_results_fail_without_writes`, `test_anki_cli_preview_returns_reviewable_json_without_local_mutations` |
| FR-010, FR-011 | `test_flashcard_skill_and_host_links_preserve_read_only_contract`; direct Skill review of opt-in nmem read-only CLI/host workflow and non-authoritative result use |
| Full learner workflow | `test_fresh_template_cli_replays_source_review_profile_and_card_workflow`: copied template -> setup -> approved onboarding -> source/note -> approved profile dimension/review -> profile -> approved draft -> list -> validate; relative host links remain in the copy; source template remains topic-free |

## Review and Limitations

- **Execution Mode**: direct; **Fallback**: stale. Installed reviewer manifest is `2026-06-16`; skill requires `2026-09-19`. No independent reviewer result is claimed and no agent was installed or invoked.
- Basic card body remains solely in Markdown. SQLite holds identities and relations; every draft has note/evidence references and derived source/locator rows. Approved merges retain source locators; content changes require explicit replacement. Normal replay does not rewrite the artifact.
- HTTP uses a fixed loopback host, allowlisted read actions, two-second socket timeout, bounded response size and batches. Preview includes content/provenance and rejects incomplete or malformed responses. It never sends a mutation action. Tests ran against an isolated local HTTP server, requiring sandbox escalation for loopback listening, not a learner collection.
- nmem is a Skill/host read workflow, disabled by default. Search results remain transient; no nmem write or synchronization exists in the core. Host-specific search runtime was not exercised, and no conversational model eval is claimed; the delivered guidance/links were reviewed and tested structurally.
- Ordinary filesystem/SQLite failures are rolled back and tested, including commit failure after replacement. Power loss or process termination between file and database operations has no journal-based recovery guarantee. No multi-process stress test was performed.
- Live Anki behavior, API-key-protected endpoints, custom/localized models, and transport v1 are not covered. The supported preview contract requires Basic/Front/Back on the local v6 endpoint. These are declared limits, not evidence of live collection acceptance.

## Architecture And Decision Drift

- **Architecture drift**: none after plan alignment. The initial redundant content-hash idea was removed because Markdown owns the editable body; only identity/provenance are checked against SQLite. No framework, queue, cache, runtime dependency, or remote-write path was added.
- **Decision drift**: DEC-001 preserves Markdown/SQLite authority; DEC-002 implements explicit objective merge and reviewed replacement; DEC-003 implements optional read-only loopback preview; DEC-004 implements opt-in Skill-level read-only retrieval. E-001 and E-004 support each decision.

## Verdict

- **Verdict**: PASS for the selected local drafts and read-only integration contract.
- **Unresolved Risks**: the runtime limits above; no unmet in-scope P1 requirement was identified.
- **Next Stage**: closeout complete; E-005/E-006 record context and structural checks. Later administrative completion edits do not change the tested implementation snapshot; manifest revisions are refreshed after those edits.
