# Implementation Plan: Workspace and Topic Onboarding

**Workspace**: `workspace-topic-onboarding` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Replace the unpublished `learnbase init` command with deterministic `learnbase setup [--name NAME]` and add a host-neutral `learnbase-onboarding` Skill. The CLI validates and stores workspace state plus an approved topic proposal; the Skill conducts the adaptive interview, presents the complete proposal, and invokes persistence only after learner approval. Keep Anki adapter setup as a separate opt-in follow-up boundary.

## Architecture Overview

```text
clone template -> learnbase setup [--name NAME] -> local folders + SQLite registry
               -> learnbase-onboarding Skill -> learner-reviewed JSON proposal
                                             -> topic onboard --approved -> topics + topic_config
optional: enable adapter -> inspect existing resources -> mapping preview -> authorized write
```

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| Workspace setup CLI | Validated local settings | All CLI commands and skills | Fresh-workspace command tests read the effective defaults |
| `learnbase-onboarding` Skill | Learner-reviewed JSON proposal | `learnbase topic onboard` | CLI tests prove unknown values remain `null` and missing approval performs no write |
| `learnbase topic onboard` | Stable topic identity and `topic_config` row | Source intake, review/profile feature | CLI tests read the topic and configuration through SQLite |
| Future Anki setup | Deck identity and topic mappings | Card drafting/publishing feature | Deferred; this feature must not create remote decks |

**孤儿 artifact 处理**: Future Anki mapping is specified but not implemented here; it is a contract for `flashcards-and-integrations` and must not be written by M1 commands.

## Decisions

- [ADR 0004](../../docs/adr/0004-layered-onboarding.md): keep workspace setup, topic onboarding, and integration setup distinct.
- Keep secrets outside tracked `learnbase.toml`; this feature stores no remote credentials.
- Topic onboarding is a proposal/review flow, not an automatic learner-profile writer.
- Workspace setup is deterministic; topic onboarding owns the adaptive interview. Since this template is unpublished, `setup` replaces `init` without a compatibility alias. Explicit `--name` updates the stored name; omitting it on rerun preserves the current value.

### Decision Capture

`decision-capture: update`

Historical lookup checked ADR-0001, ADR-0002, ADR-0004, existing feature plans/acceptance records, and Nowledge Mem; no prior decision for the onboarding payload was found.

#### DEC-001: Replace `init` with `setup`

- **Background**: the repository is an unpublished template and its only initializer is `init`; onboarding needs one canonical workspace entry point.
- **Candidates**: keep `init` and add a second `setup` command; replace `init` with `setup` and do not add an alias.
- **Decision**: replace `init`; no compatibility alias is required.
- **Reason**: there are no published users or supported external callers, and two entry points would duplicate the setup contract.
- **Cost**: local scripts or workspaces created from the unpublished tree must use the new command.
- **Upgrade trigger**: publish the template or document external automation that depends on `init`.
- **Supersedes**: none.

#### DEC-002: Store topic configuration in SQLite

- **Background**: the Skill must pass a learner-reviewed, structured proposal to the CLI, and the topic has a stable ID in SQLite.
- **Candidates**: a SQLite `topic_config` row; one JSON file per topic.
- **Decision**: store the accepted configuration in a one-to-one SQLite row and keep the proposal transient.
- **Reason**: the project already treats SQLite as the authority for structured identity and facts; one transaction can create the topic and configuration together.
- **Rejected option**: JSON files would make each configuration easy to edit but create a second identity-bearing representation that must be reconciled with the topic registry.
- **Cost**: human edits go through the CLI; accepted values are not individually version-controlled.
- **Upgrade trigger**: a concrete requirement for standalone editable topic files or independent config versioning.
- **Supersedes**: none.

### Implementation Boundaries

- Use Python standard-library JSON and SQLite. No new runtime dependencies, profile engine, network access, or adapter writes.
- Setup initializes the existing directory layout and advances the local database schema non-destructively; it does not rewrite `learnbase.toml`.
- The topic proposal is versioned JSON on stdin. Unknown keys and malformed values are rejected before any database write.

## Validation Strategy

- Test new and repeated workspace setup, including default naming, explicit rename, preservation of an existing name when omitted, and a v1-to-v2 database upgrade without losing topics or sources.
- Test valid, skipped, and unknown proposal fields; require learner approval before the atomic topic/configuration write; reject duplicate IDs and invalid parents without partial rows.
- Test host-neutral skill trigger text and WorkBuddy project link.
- Verify README distinguishes current commands from planned commands.
- No live Anki operations belong in this feature; assert that setup does not create external resources.
- Replay the workflow from a temporary copy of the template and confirm the source checkout remains unchanged.
