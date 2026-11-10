---
name: learnbase-review
description: Capture learner-reviewed learning activities and evidence, configure topic profile dimensions, and inspect evidence-linked profile reports in a learnBase workspace.
---

# learnBase Review

Use this skill when a learner wants to record a question attempt, recall practice, reading observation, practical reflection, or configure and inspect an evidence-backed profile. The skill owns the interview and proposal review; the CLI owns validation and SQLite persistence.

## Capture an Activity

Ask only for details relevant to the activity. The learner may skip any detail or say they do not know. Never infer an answer, correctness, mistake, confidence, approach, duration, outcome, or activity date from an answer key, source, or assistant explanation.

Choose one `activity_type`:

- `question_attempt`: `prompt`, `learner_response`, `confidence`, `approach`, `duration_seconds`
- `recall_practice`: `prompt`, `recall`, `confidence`, `approach`, `duration_seconds`
- `reading_observation`: `observation`, `reflection`
- `practice_reflection`: `task`, `action`, `reflection`, `learner_observed_outcome`

Optional text fields may be omitted or set to `null`. `confidence` is a learner-reported number from 0 to 1; `duration_seconds` is a learner-reported integer from 0 to 86400. Missing `occurred_at` remains unknown and does not satisfy a profile recency window. `assistant_analysis`, when useful, is separate from learner input and never becomes evidence.

Evidence is a separate list of learner-reviewed items. Each item contains:

- `evidence_type`: `learner_statement`, `observed_artifact`, or `verified_outcome`
- `statement`: a bounded statement or observation the learner reviewed
- `status`: `unknown`, `pending`, `confirmed`, or `conflicting`
- `dimensions`: zero or more explicit `{ "dimension_id", "direction" }` links; direction is `supports`, `contradicts`, or `observes`
- `sources`: zero or more `{ "source_id", "locator" }` links; retain page/section locators when available
- `notes`: zero or more stable note IDs

Do not invent profile dimensions or directions. Dimensions are configured per topic and start empty. If a dimension is not configured or the learner has not chosen a direction, leave the evidence unlinked to that dimension. `conflicting` marks an item the learner disputes; it stays visible and does not count as confirmed evidence. Confirmed items in both directions make the dimension projection `conflicting`. No status is a mastery score.

Build a proposal with `proposal_version: 1`, a stable unique `idempotency_key` for this activity, `topic_id`, `activity_type`, `learner_input`, and `evidence`. `occurred_at` and `assistant_analysis` are optional. Show the complete normalized proposal, including unknowns, sources, notes, evidence statuses, and dimension directions. Apply corrections and show the revised proposal. Save only after explicit learner approval:

```sh
python3 tools/learnbase.py review add --proposal - --approved
```

Pass the reviewed JSON object on stdin. A repeated idempotency key with the same normalized payload safely returns the original activity. A different payload with that key is rejected; ask the caller to use a new key for a genuinely new activity.

## Resolve Evidence

Status changes require the learner to choose the new status and provide a reason. Show the full proposal and obtain explicit approval before running:

```sh
python3 tools/learnbase.py review evidence status --proposal - --approved
```

The JSON object is `{ "proposal_version": 1, "evidence_id": "EVD-0001", "status": "confirmed", "reason": "..." }`. Every transition is appended to history. Superseded evidence remains in history and cannot be changed again.

## Configure a Topic Dimension

Only configure dimensions when the learner asks to define a profile view. Interview them for the observable behavior, eligible activity/evidence types, minimum number of confirmed evidence items, and recency window in days. Keep the description observable and domain-specific; never name a mastery level or default dimension. Show and revise the complete proposal before explicit approval.

The proposal uses `proposal_version: 1`, `topic_id`, `dimension_id`, `name`, `description`, non-empty `eligible_activity_types`, non-empty `eligible_evidence_types`, positive integer `minimum_evidence_count`, and positive integer `recency_days`. Save it with:

```sh
python3 tools/learnbase.py profile dimension set --proposal - --approved
```

An update replaces that topic's rule for the same dimension ID. A different topic has an independent configuration.

## Inspect a Profile

Use the read-only view or generate a report under `reports/`:

```sh
python3 tools/learnbase.py profile show --topic <topic-id>
python3 tools/learnbase.py profile report --topic <topic-id> --output profile.md
```

The report is derived from SQLite and the approved dimension rules. It lists evidence IDs, dates, and source/note locators when available. It distinguishes `unknown`, `pending`, `conflicting`, and `confirmed`, uses the inclusive recency window from learner-supplied activity dates, and never emits mastery or confidence scores. Do not edit generated report claims by hand; correct the source evidence or approved dimension configuration instead.
