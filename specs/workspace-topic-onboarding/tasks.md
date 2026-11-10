# Tasks: Workspace and Topic Onboarding

- [x] T001 Specify the workspace defaults and rerun contract. **Slice**: a cloned workspace gets safe local defaults. **Blocked by**: none. **Verify**: fresh and rerun tests cover default name, explicit rename, and name preservation when omitted.
- [x] T002 Replace `learnbase init` with deterministic `learnbase setup` and update the start path. **Slice**: learner can initialize a workspace without optional integrations. **Blocked by**: T001. **Verify**: setup works in a fresh template copy, needs no network/Anki, preserves v1 data, and leaves the template source unchanged; covered by E-001.
- [x] T003 Add versioned proposal validation and atomic `topic_config` persistence. **Slice**: an approved topic plan is stored with its stable topic identity. **Blocked by**: T001. **Verify**: known/unknown values are preserved; invalid or duplicate IDs and invalid parents produce no partial rows; no write occurs without `--approved`; covered by E-001.
- [x] T004 Add `learnbase-onboarding` Skill for adaptive topic interviews and learner review. **Slice**: conversation yields a bounded proposal consumed by T003. **Blocked by**: T003. **Verify**: skill contract covers skipped/unknown answers, user review, explicit approval, and the exact proposal schema; covered by E-001.
- [x] T005 Add thin WorkBuddy discovery link and update README/AGENTS with the onboarding path. **Slice**: both target hosts discover the same canonical Skill. **Blocked by**: T004. **Verify**: link resolves; README does not claim planned commands already exist; covered by E-001.
- [x] T006 Record verification evidence and update roadmap/current progress. **Slice**: next feature can resume from stable onboarding contracts. **Blocked by**: T001-T005. **Verify**: SDD validation, CLI tests, diff check, and evidence ledger; recorded in E-001 through E-006.

## Decision Verification Coverage

| Decision | Tasks | Evidence |
|---|---|---|
| DEC-001: replace `init` with `setup` without a compatibility alias | T002 | E-001 covers setup behavior and confirms `init` is rejected |
| DEC-002: persist approved topic configuration in SQLite | T003 | E-001 covers atomic topic/config persistence and unknown/empty values |

## Deferred Slice

Anki adapter setup, deck discovery, topic-to-deck mapping persistence, and remote preview/apply belong to `flashcards-and-integrations`, after card identity and provenance contracts are stable.

## Execution Order

T001 -> T002/T003 -> T004 -> T005 -> T006. T002 and T003 may proceed independently after T001; the proposal schema and approval boundary are now fixed in `data-model.md` and `plan.md`.
