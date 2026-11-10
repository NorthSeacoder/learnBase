# Feature Specification: Review and Evidence-Backed Learner Profile

**Workspace**: `review-profile-core`\
**Created**: 2026-11-09\
**Status**: Completed (local verification)
**Input**: Add domain-neutral review for wrong answers and other learning activities, and generate a learner profile grounded in evidence.

## Change Profile

| Field | Value |
|---|---|
| Change Profile | high |
| Risk Signals | Persistent learner facts, evidence interpretation, idempotent writes, profile projection, and potentially misleading user-facing claims |
| Override | none |
| Upgrade Trigger | Add automatic scheduling, external sync, or irreversible profile writes |

## Feature Traits

| Trait | Hit | Basis |
|---|---|---|
| `multi-stage-workflow` | yes | Activity capture, evidence review, profile projection, and user feedback |
| `external-side-effects` | no | Core remains local-first |
| `artifact-handoff` | yes | Reviews link attempts, notes, topics, and profile claims |
| `user-visible-output` | yes | Profile reports and review summaries are user-facing |
| `decision-capture` | ✅ | Activity, evidence, profile, and migration contracts change persisted/public behavior |
| `prior-closure-failure` | no | New feature |
| `bugfix-loop-breaker` | no | Not a bug fix |

## User Scenarios

### Story 1: Review varied learning activities (P1)

As a learner, I want to review wrong answers, retrieval practice, reading, and practical work so that the system reflects more than exam-style correctness.

**Acceptance direction**: Activity type, learner-provided evidence, and assistant analysis remain distinguishable. Missing answers, confidence, approach, or duration stay unknown instead of being inferred.

### Story 2: Inspect a trustworthy learner profile (P1)

As a learner, I want profile statements to show their scope and supporting evidence so that I can correct, qualify, or retest them.

**Acceptance direction**: Profile dimensions are configurable for the learning domain; every profile claim links to evidence and an evidence-through date. No evidence is not a zero score or proof of mastery.

## Initial Requirements

- **FR-001**: Represent question attempts, knowledge-recall activities, reading observations, and practice reflections in a shared activity model with type-specific evidence.
- **FR-002**: Preserve learner statements separately from assistant interpretation and verified outcomes.
- **FR-003**: Keep unknown, pending, conflicting, and confirmed evidence states distinct.
- **FR-004**: Support configurable profile dimensions and scoped claims linked to evidence.
- **FR-005**: Generate profile summaries as rebuildable projections; they must not become an alternate write path for learner facts.
- **FR-006**: Ensure repeated import or retry cannot double-count the same activity.
- **FR-007**: Configure profile dimensions per topic, with no dimensions enabled by default. A dimension explicitly declares its observable description, eligible activity/evidence types, minimum confirmed evidence count, and recency window.
- **FR-008**: Emit only descriptive, evidence-backed claims when that dimension's configured minimum count and recency window are met. Reports show evidence IDs, source/note locators when available, scope, and evidence-through date; they do not produce mastery scores or unsupported confidence labels.
- **FR-009**: Preserve contradictory evidence and history. A projection with eligible confirmed evidence in both supporting and contradicting directions is `conflicting`, lists both sides, and does not flatten the history into one claim. An individually disputed evidence item remains visible with status `conflicting` but does not count as confirmed. Resolution is explicit and recorded; evidence is not deleted.
- **FR-010**: Treat assistant analysis as separate from learner statements, observed artifacts, and verified outcomes. Assistant analysis is never eligible as profile evidence.
- **FR-011**: Generate profile summaries as rebuildable Markdown reports and provide a read-only CLI view; reports are not an alternate write path for learner facts.
- **FR-012**: Require an idempotency key for activity writes. Replaying the same key and payload returns the original activity; reusing a key with a different payload is rejected without changes.

## Out of Scope for M2

- Multi-learner accounts or hosted collaboration.
- Fixed exam-centric metrics or automatic mastery conclusions without an explicit evidence rule.
- Anki scheduling/publication and nmem synchronization.
- A universal spaced-repetition scheduler.

## Unclear Questions

None blocking plan.

## Clarification Outcomes

- Profile dimensions are configured per topic; a newly onboarded topic has no enabled dimensions until the learner or workspace owner defines them.
- Each dimension uses explicit eligibility, a configurable minimum number of confirmed evidence items, and a configurable recency window. The profile reports observations and evidence coverage, never a numeric mastery/confidence score.
- Contradictory evidence is retained. The generated dimension view becomes `conflicting` when eligible confirmed items explicitly point in both directions, or when an eligible item is explicitly marked conflicting. The report shows each direction and disputed item separately. A disputed item does not count toward the confirmed threshold; the learner can explicitly confirm or supersede it through an audited transition. No evidence is deleted.
- Recency is based only on learner-supplied activity `occurred_at`; an undated activity remains visible but cannot satisfy a recency-gated claim.
- Only evidence explicitly marked eligible and confirmed may contribute. Learner statements and observed artifacts retain their evidence type; assistant analysis is stored separately and cannot contribute. No outcome, confidence, duration, or mistake is inferred from an answer key or assistant explanation.
- Reports are regenerable Markdown under `reports/`, with a read-only CLI summary path for inspection.
- Activity idempotency uses a required caller-supplied key and a canonical payload digest to distinguish a safe retry from a conflicting reuse.

## Stage Readiness

- Current step: `closeout complete`
- Blockers: none. Local implementation and acceptance evidence are recorded in `verify-evidence.md` and `acceptance.md`; optional Anki/nmem integrations remain in M3.
