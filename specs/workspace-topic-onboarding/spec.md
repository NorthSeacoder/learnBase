# Feature Specification: Workspace and Topic Onboarding

**Workspace**: `workspace-topic-onboarding`\
**Created**: 2026-11-09\
**Status**: Closed locally (conditional pass)\
**Input**: Decide what a learner should configure when cloning learnBase, starting a subject, and optionally enabling Anki or another integration.

## Change Profile

| Field | Value |
|---|---|
| Change Profile | medium |
| Risk Signals | Persistent user configuration and optional remote adapter setup; generated profile information could become sensitive or misleading |
| Override | none |
| Upgrade Trigger | Store credentials, write to remote services, or infer profile facts automatically |

## Feature Traits

| Trait | Hit | Basis |
|---|---|---|
| `multi-stage-workflow` | yes | Workspace setup, per-topic onboarding, optional integration setup |
| `external-side-effects` | yes (adapter path only) | Anki may create decks or write cards after authorization |
| `artifact-handoff` | yes | Interview output becomes validated topic and integration configuration |
| `user-visible-output` | yes | The generated topic proposal and learner approval are user-facing |
| `decision-capture` | yes | Public CLI and persisted topic-configuration contracts change |
| `prior-closure-failure` | no | New workflow |
| `bugfix-loop-breaker` | no | Not a bug fix |

## User Scenarios

### Story 1: Start a cloned workspace (P1)

As a learner, I want to configure only what the local workspace needs so I can begin without answering irrelevant domain or integration questions.

**Acceptance direction**:

- `learnbase setup` is a deterministic, idempotent command and safe to rerun.
- Nonessential fields have sensible defaults; no learner biography, subject goal, Anki, nmem, or network access is required.
- The local workspace remains usable offline.
- `setup` replaces the unpublished `init` command; no compatibility alias is required.

### Story 2: Begin a new subject (P1)

As a learner, I want an interactive conversation to shape a useful learning topic without pretending I know every detail up front.

**Acceptance direction**:

- The Skill asks about outcome, prior background, time/constraints, sources, and observable evidence of progress in a low-friction order.
- The learner may skip or mark any answer unknown.
- The Skill proposes topic structure/configuration and shows it for review before persistence.
- The CLI validates and stores structured fields; the Skill owns the adaptive interview.

### Story 3: Enable Anki only when useful (P2)

As a learner, I want to connect Anki later and reuse existing decks so that the template does not create a separate deck for every topic by default.

**Acceptance direction**:

- Integration setup is separate and opt-in.
- A topic can map to multiple decks and a deck can be shared by multiple topics.
- Remote deck creation and card publication are previewed and require explicit authorization.
- Secrets are not stored in tracked workspace configuration.

## Requirements

- **FR-001**: Provide a deterministic `learnbase setup` command that initializes local workspace state and safely preserves settings on rerun.
- **FR-002**: Provide a separate interactive topic-onboarding Agent Skill for learning goals, prior background, constraints, sources, and progress evidence.
- **FR-003**: Keep onboarding answers optional unless needed to create a valid topic; represent skipped/unknown fields as `null`, not guessed values. For list fields, `null` means unknown and `[]` means the learner explicitly has none to add.
- **FR-004**: Show generated topic configuration to the learner and obtain approval before persistence.
- **FR-005**: Put structured-field validation/persistence in the CLI and conversation/modeling in the Skill. Persist approved topic configuration in SQLite linked to its stable topic ID.
- **FR-006**: Keep Anki/nmem integration setup opt-in and separate from both workspace setup and topic onboarding.
- **FR-007**: Model topic-to-Anki-deck mapping as many-to-many and reuse existing deck identities.
- **FR-008**: Require preview and explicit authorization before remote deck creation or card publication.
- **FR-009**: Make README the concise onboarding index; keep the complete interview contract in the Skill and feature spec.
- **FR-010**: Require an explicit approval flag on the CLI topic-proposal writer; create the topic identity and its configuration atomically.

## Out of Scope

- Implementing Anki publication itself; that belongs to `flashcards-and-integrations`.
- Requiring a single fixed profile schema for every study domain.
- Automatically assigning a learner level or mastery score from conversation.
- Multi-learner workspaces or cloud synchronization.

## Key Entities

- **Workspace settings**: local runtime defaults for a cloned repository.
- **Topic plan**: learner-reviewed configuration of a study topic.
- **Topic configuration**: structured learning intent linked one-to-one to a topic ID in SQLite; source hints are leads, not registered or verified source evidence.
- **Integration profile**: opt-in adapter connection and topic/resource mappings.
- **Topic-to-deck mapping**: many-to-many binding between a topic and actual Anki deck identities.

## Stage Readiness

- Outcome: closeout complete for local workspace/topic onboarding.
- Deferred: Anki mapping, preview, and remote writes belong to `flashcards-and-integrations`.
