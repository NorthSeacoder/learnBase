# Context Manifest: Review and Evidence-Backed Learner Profile

**Workspace**: `review-profile-core`
**Created**: 2026-11-09
**Status**: closed

## Implement Context

| File / Source | Reason | Phase | Required | Revision | Observed At | Freshness | Summary |
|---|---|---|---|---|---|---|---|
| `AGENTS.md` | Enforces evidence, persistence, provenance, and external-write boundaries | implement | yes | sha256:ed92cf196dcf3cb49982dad312d37769dc0d97c6cff6e2c253319f7b18badfc0 | 2026-11-10T00:42:21Z | fresh | Structured events use SQLite CLI/API; unknowns stay unknown; source IDs/locators are retained. |
| `specs/review-profile-core/spec.md` | Defines confirmed profile behavior and acceptance semantics | implement | yes | sha256:9b875ad4a099c4ba07aac0f7f7c21e6d33e4bfdba58fdf27e9437544a391498e | 2026-11-10T00:53:40Z | fresh | Topic-scoped opt-in dimensions, configurable gates, retained conflicts, no mastery scores; local feature verification is complete. |
| `specs/review-profile-core/plan.md` | Defines schema, CLI, projection contracts, decisions, and validation risks | implement | yes | sha256:ad9bf42825a2616d161e1fe5d9e7e0e01251417711297363aae04f35f79cf970 | 2026-11-10T00:42:21Z | fresh | SQLite v3, approved idempotent writes, explicit evidence directions, deterministic reports for fixed `as_of`. |
| `specs/review-profile-core/data-model.md` | Defines persisted entities, states, provenance, and migration rules | implement | yes | sha256:c412f5bf6ceb020a553503bd0bb3ab6e69c24609dfc8a6b42de6057298c4e618 | 2026-11-10T00:42:21Z | fresh | Activity/evidence tables, explicit topic dimensions, transition history, and unknown-date handling. |
| `specs/review-profile-core/tasks.md` | Bounds implementation slices and their verification points | implement | yes | sha256:ea181d83b4d514e9f42a9020f6effcb9b8c1252e1ad3f8e5ad8e9e701fccbad0 | 2026-11-10T00:53:40Z | fresh | T001-T007 complete with test, verification, and closeout evidence. |
| `docs/architecture.md` | Preserves authority, workflow, and local-first boundaries | implement | yes | sha256:f35528bb8521654d1595fe06da8d6c83e3bb57935248197aec884c51d6be8901 | 2026-11-10T00:42:21Z | fresh | Markdown owns knowledge; SQLite owns activity/evidence; reports are derived. |
| `docs/adr/0001-markdown-and-sqlite.md` | Confirms persistence authority and versioned transactional writer | implement | yes | sha256:233b763dbb10ec77075a7c36591de614d91691eaa018a1375405c270132ea766 | 2026-11-10T00:42:21Z | fresh | SQLite owns structured learning evidence; Markdown remains formal knowledge authority. |
| `learnbase.toml` | Confirms the template ships no profile dimensions and integrations stay optional | implement | yes | sha256:da7ab3c08f98dc12f6c3037199720dfd750af01338780b9c1a2afacde606a247 | 2026-11-10T00:42:21Z | fresh | `profile.dimensions` is empty; nmem and Anki are disabled. |
| `.agents/skills/learnbase-onboarding/SKILL.md` | Keeps setup/onboarding distinct from profile configuration and review | implement | yes | sha256:fb87332cf4d6c4b54706ac88867c6da7434f0670fa8533524be46f85a3f5f792 | 2026-11-10T00:42:21Z | fresh | Skill owns interviews and learner review; CLI validates bounded topic proposals. |
| `.agents/skills/learnbase-review/SKILL.md` | Defines the learner interview, proposal, explicit approval, and profile usage | implement | yes | sha256:c2a37172ee9cfd3ba002860fed4301b899da7a9678616e9923c15741a8423788 | 2026-11-10T00:42:21Z | fresh | Skill owns conversations; CLI validates activity, evidence, dimensions, status, and report commands. |
| `.agents/skills/learnbase-study/SKILL.md` | Checks that source intake links to the dedicated review workflow without merging authorities | implement | yes | sha256:31778470a818b692e7f4b2976ab82a2e79d374034a0226e5200610a749198a9b | 2026-11-10T00:42:21Z | fresh | A note is not evidence that the learner demonstrated a capability. |
| `docs/cli.md` | Verifies documented command names and external-write boundaries | implement | yes | sha256:4a3abf5bf1249155a8c0100c578db4eed8593fb1804201fc2bf2854a2ae18ba0 | 2026-11-10T00:42:21Z | fresh | Documents approved JSON writes, status history, profile show, and generated reports. |

## Check Context

| File / Source | Reason | Phase | Required | Revision | Observed At | Freshness | Summary |
|---|---|---|---|---|---|---|---|
| `specs/review-profile-core/spec.md` | Verify each user-facing and data-integrity requirement | verify | yes | sha256:9b875ad4a099c4ba07aac0f7f7c21e6d33e4bfdba58fdf27e9437544a391498e | 2026-11-10T00:53:40Z | fresh | Includes topic defaults, threshold, recency, conflict, approval, and no-score requirements; status records local completion. |
| `specs/review-profile-core/plan.md` | Check implementation against selected contracts and risks | verify | yes | sha256:ad9bf42825a2616d161e1fe5d9e7e0e01251417711297363aae04f35f79cf970 | 2026-11-10T00:42:21Z | fresh | Defines migration, idempotency, evidence state, CLI, and report behavior. |
| `specs/review-profile-core/data-model.md` | Verify entity constraints, state semantics, and provenance coverage | verify | yes | sha256:c412f5bf6ceb020a553503bd0bb3ab6e69c24609dfc8a6b42de6057298c4e618 | 2026-11-10T00:42:21Z | fresh | Confirms unknown dates, explicit evidence directions, and retained status history. |
| `specs/review-profile-core/tasks.md` | Verify all planned slices and their implementation evidence | verify | yes | sha256:ea181d83b4d514e9f42a9020f6effcb9b8c1252e1ad3f8e5ad8e9e701fccbad0 | 2026-11-10T00:53:40Z | fresh | T001-T007 are complete; evidence and acceptance records are present. |
| `AGENTS.md` | Verify persisted facts and source handling honor repository rules | verify | yes | sha256:ed92cf196dcf3cb49982dad312d37769dc0d97c6cff6e2c253319f7b18badfc0 | 2026-11-10T00:42:21Z | fresh | Requires supported writes, source locators, explicit approvals, and unknown preservation. |
| `docs/architecture.md` | Verify no second knowledge authority or required network dependency is introduced | verify | yes | sha256:f35528bb8521654d1595fe06da8d6c83e3bb57935248197aec884c51d6be8901 | 2026-11-10T00:42:21Z | fresh | Keeps formal knowledge in Markdown and structured review/profile data in local SQLite. |
| `.agents/skills/learnbase-review/SKILL.md` | Verify interview, evidence, profile, and approval behavior matches the CLI | verify | yes | sha256:c2a37172ee9cfd3ba002860fed4301b899da7a9678616e9923c15741a8423788 | 2026-11-10T00:42:21Z | fresh | Defines learner approval, explicit evidence directions, opt-in dimensions, and reports. |
| `.agents/skills/learnbase-study/SKILL.md` | Verify the source-to-note path delegates reviews to the canonical Skill | verify | yes | sha256:31778470a818b692e7f4b2976ab82a2e79d374034a0226e5200610a749198a9b | 2026-11-10T00:42:21Z | fresh | Separates knowledge notes from learner review evidence. |
| `docs/cli.md` | Verify public command syntax and generated report behavior | verify | yes | sha256:4a3abf5bf1249155a8c0100c578db4eed8593fb1804201fc2bf2854a2ae18ba0 | 2026-11-10T00:42:21Z | fresh | Records CLI command paths and approval/report boundaries. |

## Research Context

| File / Source | Reason | Phase | Verified |
|---|---|---|---|
