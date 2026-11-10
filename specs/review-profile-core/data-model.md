# Data Model: Review and Evidence-Backed Learner Profile

**Workspace**: `review-profile-core` | **Date**: 2026-11-09 | **Schema**: v3

## Entities

### Learning activity (`learning_activities`)

One learner activity, keyed by a generated stable `activity_id` and a required caller `idempotency_key` unique within the workspace.

| Field | Type | Constraints | Meaning |
|---|---|---|---|
| `activity_id` | TEXT | PK | Stable activity identity |
| `idempotency_key` | TEXT | NOT NULL UNIQUE | Retry/import identity; stable for one event |
| `payload_sha256` | TEXT | NOT NULL | Digest of normalized validated proposal |
| `topic_id` | TEXT | FK to `topics.topic_id` | Primary topic scope |
| `activity_type` | TEXT | check-constrained | `question_attempt`, `recall_practice`, `reading_observation`, `practice_reflection` |
| `occurred_at` | TEXT | UTC ISO-8601 | Learner-supplied time; missing input is unknown, never guessed |
| `learner_input_json` | TEXT | NOT NULL JSON object | Type-specific learner-provided prompt, response, reflection, confidence, approach, duration, or artifact locator |
| `assistant_analysis` | TEXT | nullable | Separate analysis; never evidence or profile input |
| `created_at` | TEXT | UTC ISO-8601 | Local persistence time |

Type-specific JSON allowlists prevent accidental mixing while preserving explicit `null` values. Omitted optional learner fields normalize to unknown. Duration, confidence, answer correctness, and learner mistakes are never inferred from content or analysis.

### Learning evidence (`learning_evidence`)

An explicit learner-reviewed statement or observation associated with one activity.

| Field | Type | Constraints | Meaning |
|---|---|---|---|
| `evidence_id` | TEXT | PK | Stable evidence identity |
| `activity_id` | TEXT | FK | Activity that produced or recorded it |
| `evidence_type` | TEXT | check-constrained | `learner_statement`, `observed_artifact`, or `verified_outcome` |
| `statement` | TEXT | non-empty | Exact bounded description reviewed by learner |
| `status` | TEXT | check-constrained | `unknown`, `pending`, `confirmed`, `conflicting`, or `superseded` |
| `created_at` | TEXT | UTC ISO-8601 | Evidence record time |

`confirmed` means the row was explicitly reviewed and admitted as evidence of the stated kind; it does not mean the learner has mastered a topic. `conflicting` means the learner explicitly disputed this item; it remains visible but does not count toward configured confirmed-evidence thresholds. `assistant_analysis` is not a valid evidence type.

### Evidence provenance (`evidence_sources`, `evidence_notes`)

Evidence may link to registered source IDs plus locators, and to stable note IDs. Imported source claims retain source ID and locator whenever available. Evidence without external provenance remains a learner statement or local observation, not a fabricated citation.

### Evidence dimensions (`evidence_dimensions`)

Many-to-many association between evidence and explicitly configured topic dimensions. Each link has a required direction: `supports`, `contradicts`, or `observes`. Direction is selected in the reviewed proposal; it is never inferred from text or assistant analysis.

### Evidence status history (`evidence_status_history`)

Append-only transition rows preserve prior states, approval timestamp, and required resolution reason. Evidence is never physically removed by the review CLI. `superseded` records remain available to audit but do not count in new projections.

### Topic profile dimension (`topic_profile_dimensions`)

No dimension rows are created by setup or topic onboarding. Each row belongs to one topic and declares:

| Field | Meaning |
|---|---|
| `dimension_id` | Stable slug scoped to topic |
| `name` | Learner-facing label |
| `description` | Observable capability/behavior, not an inferred level |
| `eligible_activity_types_json` | Explicit activity types that can contribute |
| `eligible_evidence_types_json` | Explicit evidence types that can contribute; assistant analysis cannot appear |
| `minimum_evidence_count` | Positive number of confirmed, non-superseded evidence links required |
| `recency_days` | Positive inclusive evidence window relative to report generation time |
| `created_at`, `updated_at` | UTC ISO-8601 config audit dates |

## Projection States

The report computes each dimension from eligible evidence whose activity has a learner-supplied `occurred_at` in the configured inclusive time window. Undated evidence remains visible but cannot satisfy the recency gate. Persistence timestamps are not used as substitutes for learner activity dates.

- `unknown`: no eligible evidence is present.
- `pending`: evidence exists, but has unconfirmed/undated items or does not meet the configured confirmed directional count.
- `conflicting`: an eligible item is explicitly marked `conflicting`, or at least one recent confirmed `supports` item and one recent confirmed `contradicts` item exist. The report shows disputed items and both confirmed directions separately.
- `confirmed`: the configured count is met in exactly one explicit direction and there is no unresolved eligible evidence. Wording is descriptive and names the evidence count, date range, and references; it is not a mastery verdict or numerical score.

`observes` evidence is listed but does not support a directional summary. A dimension with no directional evidence cannot emit a supported/challenged claim. `conflicting` and superseded rows never satisfy the confirmed count. Superseded and stale evidence is excluded from the current projection but remains available in historical records.

## Proposal Contracts

- Review proposal: versioned JSON containing idempotency key, topic ID, activity type, optional learner-supplied occurred time, type-specific learner input, optional separate assistant analysis, and reviewed evidence/source/note/dimension links.
- Dimension proposal: versioned JSON containing topic/dimension IDs, name, observable description, eligible activity/evidence lists, minimum confirmed count, and recency days.
- Status transition: evidence ID, next status, learner approval, and non-empty reason. Transitions append history and do not delete or rewrite the original statement.
- Omitted optional learner-input fields normalize to null. Link collections use empty arrays to mean no links; unknown proposal fields are rejected.
- Unknown proposal keys, invalid types, invalid source/note/dimension IDs, missing locators where the source supplies them, and out-of-range values are rejected before writes.

## Relationships

```text
topics 1 --- 0..N learning_activities
learning_activities 1 --- 0..N learning_evidence
learning_evidence N --- M sources (with locator)
learning_evidence N --- M notes
learning_evidence N --- M topic_profile_dimensions (with explicit direction)
learning_evidence 1 --- 0..N status-history rows
topics 1 --- 0..N topic_profile_dimensions
```

## Migration

Schema v2 to v3 is additive and transactional. It adds activity, evidence, provenance, dimension, and history tables/indexes without rewriting existing topic, source, note, or `topic_config` data. Setup rejects future schema versions and never downgrades.
