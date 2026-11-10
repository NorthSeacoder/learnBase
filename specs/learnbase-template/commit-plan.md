# Commit Plan: learnBase 本地模板

**Workspace**: `learnbase-template` | **Date**: 2026-11-10 | **Status**: Implementation committed and pushed; documentation follow-up authorized

## Summary

计划制定时 HEAD 仅跟踪 README，M1、onboarding、M2、M3 与默认集成简化共享实现。用户授权后，62 文件模板基线已提交为 `7cd01e8` 并推送 `origin/main`。下表保留实际文件范围；第二批仅记录已完成的提交和推送结果。

## Included Files

| File | Reason | Evidence |
|---|---|---|
| `README.md`, `AGENTS.md`, `.gitignore`, `learnbase.toml` | 模板入口、边界、运行时排除与默认配置 | 四个 feature 的 spec/acceptance |
| `tools/learnbase.py`, `tests/test_learnbase.py` | 共享标准库 CLI 与 45 项回归 | M3 E-001 |
| `.agents/skills/learnbase-study/SKILL.md`, `.agents/skills/learnbase-onboarding/SKILL.md`, `.agents/skills/learnbase-review/SKILL.md`, `.agents/skills/learnbase-flashcards/SKILL.md` | canonical 交互流程 | 各 feature 的 Skill 任务 |
| `.workbuddy/README.md`, `.workbuddy/skills/learnbase-study`, `.workbuddy/skills/learnbase-onboarding`, `.workbuddy/skills/learnbase-review`, `.workbuddy/skills/learnbase-flashcards` | WorkBuddy discovery 与相对软链 | host-link/模板副本测试 |
| `.claude/skills/learnbase-review`, `.claude/skills/learnbase-flashcards`, `.cursor/skills/learnbase-review`, `.cursor/skills/learnbase-flashcards` | 复用 canonical Skills 的现有相对软链 | host-link 测试 |
| `docs/architecture.md`, `docs/cli.md`, `docs/current-progress.md`, `docs/glossary.md`, `docs/roadmap.md` | 使用契约与阶段入口 | 各 feature 文档任务 |
| `docs/adr/0001-markdown-and-sqlite.md`, `docs/adr/0002-single-learner-multi-topic.md`, `docs/adr/0003-offline-core-and-adapters.md`, `docs/adr/0004-layered-onboarding.md` | 保留架构决策 | plan 的历史决策查询 |
| `specs/.active`, `specs/learnbase-template/roadmap.md`, `specs/learnbase-template/commit-plan.md`, `specs/learnbase-template/roadmap-audit.md` | 续接指针、整体状态、提交计划与范围核对 | roadmap 与最终审计 |
| `specs/source-note-foundation/spec.md`, `plan.md`, `tasks.md`, `acceptance.md`, `verify-evidence.md`（均位于该目录） | M1 规格与本地验收 | source-note-foundation acceptance |
| `specs/workspace-topic-onboarding/spec.md`, `plan.md`, `data-model.md`, `tasks.md`, `acceptance.md`, `verify-evidence.md`（均位于该目录） | onboarding 规格、验收与交接 | workspace-topic-onboarding acceptance |
| `specs/review-profile-core/spec.md`, `plan.md`, `data-model.md`, `tasks.md`, `context-manifest.md`, `acceptance.md`, `verify-evidence.md`（均位于该目录） | M2 规格与本地验收 | review-profile-core acceptance |
| `specs/flashcards-and-integrations/spec.md`, `plan.md`, `data-model.md`, `tasks.md`, `context-manifest.md`, `acceptance.md`, `verify-evidence.md`（均位于该目录） | M3 规格与本地验收 | flashcards-and-integrations acceptance |
| `specs/default-integration-support/spec.md`, `plan.md`, `tasks.md`, `acceptance.md`, `verify-evidence.md`（均位于该目录） | 用户要求的默认集成简化与当前回归证据 | default-integration-support acceptance |

## Excluded Files

| File | Reason |
|---|---|
| `data/`, `.venv/`, `__pycache__/`, `*.py[cod]`, `.DS_Store` | 运行时、数据库或本机产物；由 `.gitignore` 排除 |
| `task_plan.md`, `findings.md`, `progress.md` | 本次执行日志；默认不作为模板交付正文 |
| 外部原始材料、真实笔记/卡片与学习者记录 | 模板源必须无个人数据；本轮未引入 |

## Needs User Decision

无文件归属待定。用户已明确要求“先提交并推送吧”，授权将上述文件提交并推送至当前 `origin/main`。

## Risks

| Risk | Impact | Handling |
|---|---|---|
| 共享实现依赖 | 只提交 README 会得到不可运行模板 | 已按精确清单提交全部 62 个模板文件 |
| 相对软链 | 宿主 discovery 依赖链接保真 | Git 保存链接；模板副本测试已核验 |
| 历史验收快照 | 前序 ledger 记录当时基线，不能冒充当前测试 | roadmap audit 引用 M3 E-001 的最新全量回归 |
| 发布与 Template 设置 | 代码推送不等于启用 GitHub Template | 代码已推送；Template 设置保持原状 |

## Commit Batches

| Batch | Files | Commit Message | Rationale |
|---|---|---|---|
| 1 | Included Files 中经确认的全部精确路径 | `feat: add local learning workspace with evidence and card previews` | 当前模块共享依赖，形成可运行的单个模板基线 |
| 2 | 本文件、`docs/current-progress.md`、`specs/learnbase-template/roadmap.md`、`specs/default-integration-support/acceptance.md` | `docs: record published template baseline` | 首批推送成功后记录实现 commit 与发布结果，避免验收仍称未提交 |

## Execution Rules

已取得明确提交与推送指令。按精确路径分批 add/commit，推送 `origin/main`；禁止宽泛 add。GitHub Template 设置及 Anki/nmem 写入不属于本轮操作。

## User Confirmation

用户确认：2026-11-10，“先提交并推送吧”。提交/推送结果在执行后补记于本文件。

## Execution Record

| Item | Result |
|---|---|
| Implementation commit | `7cd01e865831f7cc13c3e5501f21a94690ee0958` |
| Message | `feat: add local learning workspace with evidence and card previews` |
| Scope | 62 files; 8 relative Skill links; no learner database or external source files |
| Validation | 11 current implementation hashes matched; staged diff check and SDD closeout-ready passed |
| Formatting | 新文档双空格换行改为等效反斜杠换行，移除多余 EOF 空行；实现基线字节未变 |
| Push | `git push origin main` exited 0; local branch synchronized with origin/main after the push |
| Remaining local files | `task_plan.md`, `findings.md`, `progress.md` intentionally excluded |
| Documentation follow-up | Batch 2 records this result; authorized by the same commit/push request and subsequent “继续” |
| Other external actions | No GitHub Template setting change; no Anki/nmem writes |
