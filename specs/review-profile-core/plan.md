# Implementation Plan: Review and Evidence-Backed Learner Profile

**Workspace**: `review-profile-core` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Add a local, transactional review/evidence writer to the existing Python/SQLite CLI and a deterministic profile projection. The user or Skill captures learner-provided activity data, separately records assistant analysis, explicitly reviews the bounded proposal, and persists with a stable idempotency key. Per-topic profile dimensions are opt-in and declare which confirmed evidence can contribute, the minimum count, and the recency window. Reports link every generated statement to evidence and source/note locators when available. Conflicts remain visible until an explicit, history-preserving resolution.

## Architecture Overview

```text
learner activity + reviewed evidence proposal
  -> learnbase review add --proposal - --approved
  -> learning_activities + learning_evidence + source/note links (one transaction)
  -> explicit evidence status transition with audit history

topic config -- none by default
  -> learnbase profile dimension set --proposal - --approved
  -> topic_profile_dimensions
  -> read-only projection over eligible, confirmed, in-window evidence
  -> learnbase profile show / report -> stdout or generated Markdown
```

Keep the implementation in the standard-library CLI and SQLite. Do not create a second editable note body, call a model during projection, fetch sources, or require a network connection. Reports are derived artifacts and must be reproducible from database rows plus dimension configuration.

## Data And Interface Contract

- Bump SQLite schema from v2 to v3 with additive tables and preserve all existing metadata, topics, sources, note links, and topic configuration.
- Store one activity row per caller-supplied idempotency key and a digest of the normalized payload. A retry with the same digest returns the existing ID; a changed payload under the same key fails before writes.
- Store learner input, assistant analysis, and evidence as distinct fields/entities. Assistant analysis is never represented in the evidence table and never contributes to a profile dimension.
- Store typed evidence with explicit status and source/note provenance. A separate dimension-link table gives each evidence-to-dimension relation an explicit direction (`supports`, `contradicts`, or `observes`); no direction is inferred from a prompt, answer key, model explanation, or note text.
- Store evidence status changes in append-only history. Status resolution requires an explicit CLI command, approval, and reason; `superseded` evidence is retained and excluded from new projections.
- Store profile dimensions per topic. There are no default dimensions. Each dimension requires a description, eligible activity and evidence types, minimum confirmed count, and positive recency window.
- Projection status is `unknown` with no eligible evidence, `conflicting` when eligible evidence is explicitly disputed or confirmed evidence supports both directions, `pending` while relevant evidence is unconfirmed/undated or the directional threshold is unmet, and `confirmed` only when the configured threshold is met in one direction with no unresolved evidence. A `conflicting` evidence row remains visible but does not count toward the confirmed threshold. `confirmed` describes the evidence rule's result, not mastery.
- Apply the recency window to learner-supplied activity `occurred_at`, inclusively. If it is unknown, keep the evidence visible as undated and do not count it toward a recency-gated claim; persistence time is not a substitute for the learner's activity date.
- Reports contain no scores. They include the dimension description, scope, count, configured window, latest evidence date, status, and evidence/source/note locators. A conflict lists both directions without collapsing either side.
- Generate a deterministic Markdown report for a fixed projection `as_of` under `reports/` only to a caller-selected path contained in that directory; print the same report to stdout for read-only inspection. Refuse to overwrite a non-generated file.

## Producer-Consumer Matrix

| Producer | Artifact | Consumer | Consumption Proof |
|---|---|---|---|
| `learnbase review add` | Idempotent activity, typed evidence, provenance links | `learnbase profile show/report` | Tests inspect the persisted rows and resulting report |
| `learnbase review evidence status` | Append-only evidence state transition | Profile projection | Tests prove history is retained and superseded evidence is excluded |
| `learnbase profile dimension set` | Approved per-topic eligibility and threshold rule | Profile projection | Tests cover empty default config and validated configured thresholds |
| Profile projector | Evidence-linked Markdown | Learner and `learnbase profile show` | Deterministic replay yields the same text and every statement has evidence IDs |

**Orphan artifact handling**: no Anki card or external-memory artifact is produced in M2; those belong to `flashcards-and-integrations`.

## Decisions

### Historical Decision Lookup

- Query Scope: `docs/architecture.md`, `docs/adr/0001-markdown-and-sqlite.md` through `0004`, `learnbase.toml`, onboarding data model/plan/acceptance, all `specs/*/plan.md`, and acceptance Knowledge Capture for `activity`, `evidence`, `profile`, `report`, and persistence authority.
- Matches: ADR-0001 (SQLite structured evidence authority; Markdown knowledge body; reports derived); ADR-0002 (single learner, multiple topics, topic-scoped claims); ADR-0003 (offline core, optional adapters); onboarding DEC-002 (stable topic configuration stored in SQLite).
- Handling: reuse and extend those decisions.
- Rationale: the review/profile feature is the next data layer explicitly anticipated by architecture and ADR-0001; it does not require a second persistence authority.
- Unverified: no external user scale or production workload is established; this is a local single-learner workspace.

`decision-capture: update`

### DEC-001: Scope profile dimensions per topic with no defaults
- Status: accepted
- Trigger: high profile, configurable learning domains, and confirmed user clarification
- Context: a fixed dimension list would imply one domain's definition of progress applies to all topics.
- Options: workspace-wide defaults; optional shared preset; per-topic configuration that starts empty.
- Decision: store dimensions per topic and ship none by default.
- Rejected: implicit defaults can be inapplicable and can make absence look like failure.
- Consequences: a topic has no profile claims until dimensions are explicitly defined; each dimension must be validated and reviewed.
- Evidence: confirmed user choice; `learnbase.toml` currently has an empty profile dimensions list.
- Upgrade Trigger: repeated learner requests for reusable presets; presets must remain opt-in.
- Supersedes / Superseded By: none.

### DEC-002: Gate descriptive profile claims by configured confirmed evidence
- Status: accepted
- Trigger: high profile and confirmed user clarification
- Context: unsupported scores or mastery claims could misrepresent learner capability.
- Options: fixed global threshold; manually approved report claims; per-dimension count/recency/eligibility rules.
- Decision: require explicit per-dimension eligible types, minimum confirmed evidence count, and recency window. Produce descriptive summaries only, without a mastery/confidence score.
- Rejected: a global threshold ignores domain and dimension differences; hand-authored report claims are not reliably rebuildable.
- Consequences: initial setup requires dimensions to declare a threshold; low evidence yields unknown/pending output rather than a guessed conclusion.
- Evidence: confirmed user choice; ADR-0001 makes reports derived and ADR-0002 requires topic-scoped evidence.
- Upgrade Trigger: reviewed evaluation shows consistent thresholds are misleading or unusable for a defined learning domain.
- Supersedes / Superseded By: none.

### DEC-003: Preserve contradictory evidence and require explicit resolution
- Status: accepted
- Trigger: high profile, data integrity, and confirmed user clarification
- Context: last-write-wins would erase the history needed to explain a changed claim.
- Options: latest evidence wins while retaining history; preserve both and mark conflict; model decides which side is correct.
- Decision: keep all evidence; project `conflicting` when an eligible item is explicitly disputed or recent eligible confirmed evidence has opposing explicit directions. Disputed items do not satisfy the confirmed threshold. The learner may explicitly confirm or supersede an item with an audited reason.
- Rejected: automatic/model resolution would convert interpretation into learner fact; replacing old evidence loses history.
- Consequences: conflict can remain visible until the learner reviews it; status transitions need audit history.
- Evidence: confirmed user choice; AGENTS.md forbids inferring mastery or mistakes from assistant explanations.
- Upgrade Trigger: a future verified assessment import establishes a separately trusted resolution contract.
- Supersedes / Superseded By: none.

### DEC-004: Use required idempotency keys and payload digests for activity writes
- Status: accepted
- Trigger: FR-006, retry/import behavior, and persistent data integrity
- Context: duplicate retries must not inflate evidence counts, while changed retries must not silently mutate an existing event.
- Options: caller key only with last-write-wins; content-based dedupe; required stable caller key plus normalized payload digest.
- Decision: use a unique caller key and digest; identical replay returns the original activity, while differing replay rejects without writes.
- Rejected: content-based dedupe can collapse two genuine repeated learning activities; last-write-wins changes history on retry.
- Consequences: importing callers must generate and preserve a stable idempotency key per event.
- Evidence: FR-006; SQLite UNIQUE constraints and transactions are already used by the CLI.
- Upgrade Trigger: a concrete adapter cannot preserve caller keys and requires a separately versioned dedupe contract.
- Supersedes / Superseded By: none.

### DEC-005: Keep assistant analysis outside the evidence authority
- Status: accepted
- Trigger: FR-002, learner-trust boundary, and persistent profile projection
- Context: assistant analysis can help a learner but cannot establish what the learner did or knows.
- Options: store analysis as evidence; store analysis in activity but exclude it by convention; keep it separately typed and schema-ineligible.
- Decision: store assistant analysis in a separate activity field, with no link into the profile evidence relation.
- Rejected: convention-only exclusion is easy to violate in a generic evidence query.
- Consequences: model explanations remain available for review history but can never count toward configured profile thresholds.
- Evidence: AGENTS.md explicitly separates learner evidence and model analysis.
- Upgrade Trigger: none for this feature; any future analysis-derived fact needs learner-confirmed evidence first.
- Supersedes / Superseded By: none.

## Validation Strategy

- Test a fresh v3 setup and additive v2-to-v3 upgrade without losing M1 data; reject unsupported future versions.
- Test strict proposal schema/type/bounds checks, missing approval, foreign keys, rollback on invalid evidence, and source/note locator preservation.
- Test idempotent same-payload replay, changed-payload key collision, and concurrent/transactional behavior where practical.
- Test each activity type and preserve unknown learner fields without synthesizing values.
- Test assistant analysis cannot be inserted as evidence or counted by projection.
- Test per-topic dimension isolation, no default dimensions, valid eligibility, and strict minimum/recency boundaries.
- Test report statuses `unknown`, `pending`, `conflicting`, and `confirmed`; prove opposite evidence is listed, stale/superseded evidence is excluded, and reports contain evidence IDs/locators but no scores.
- Test evidence state transitions append history and require explicit approval/reason.
- Test deterministic report output and safe generated-file writes, including collision with user-authored files.
- Run source-note foundation regressions, the SDD closeout validator, and `git diff --check`.

## Risks And Recovery

- Incorrect projection wording could overstate evidence. Use factual count/date language, retain all supporting references, avoid scores, and refuse claim generation when thresholds or consistency are unmet.
- Schema migration can damage local learning history. Make v3 additive and transactional, exercise v2 upgrades with populated rows, and reject newer schemas without downgrade.
- Idempotency key reuse with changed content could hide learner history. Reject and require a new key for a genuinely new event.
- Reports could become a second write authority. Use generated markers, protect user files, and regenerate only from SQLite and approved dimension rules.
