# Data Model: Workspace and Topic Onboarding

**Workspace**: `workspace-topic-onboarding` | **Date**: 2026-11-09

## Entities

### Topic configuration (table: `topic_config`)

One approved learning-intent record for a stable topic identity. A topic may exist without this record when created through the low-level `topic add` command; onboarding creates both rows atomically.

| Field | Type | Constraints | Meaning |
|---|---|---|---|
| `topic_id` | TEXT | PK, FK to `topics.topic_id` | Stable identity; not derived again after creation |
| `config_version` | INTEGER | NOT NULL, currently `1` | Stored payload schema |
| `learning_goal` | TEXT | nullable, max 1000 chars | Learner-reviewed intended outcome |
| `prior_background` | TEXT | nullable, max 1000 chars | Learner-provided prior background |
| `constraints_json` | TEXT | nullable JSON array of strings | Learner-provided time or study constraints |
| `source_hints_json` | TEXT | nullable JSON array of strings | Suggested sources, not registered source evidence |
| `progress_signals_json` | TEXT | nullable JSON array of strings | Learner-defined ways to observe future progress |
| `approved_at` | TEXT | NOT NULL, UTC ISO-8601 | Time the approved proposal was stored |

Scalar `null` means skipped or unknown; an absent scalar is normalized to `null`. For list fields, `null` means skipped or unknown and `[]` means the learner explicitly has none to add. Empty strings are invalid. Lists accept at most 20 items, with each item at most 500 characters.

### Proposal payload

`learnbase topic onboard --proposal - --approved` reads one JSON object from stdin. `proposal_version` must be the JSON integer `1` (booleans and fractional numeric values are rejected); `topic_id` must use the existing lowercase ASCII slug pattern; `name` is required and limited to 160 characters; `parent_id` is nullable and must identify an existing topic. Optional configuration fields follow the table above. Unknown keys, wrong types, or out-of-bound values are rejected before any database write.

The Skill presents this proposal to the learner and waits for approval. Without `--approved`, the CLI rejects the request without creating either row. The proposal is transient; only the accepted fields are stored.

## Relationships

```text
topics 1 --- 0..1 topic_config
topics 1 --- 0..N child topics
```

## Migration Notes

- Database schema version advances from `1` to `2` by creating `topic_config` and updating metadata.
- The migration is additive and preserves existing topic, source, and note rows.
- A database declaring a newer schema version is rejected; setup must not downgrade it.
