# Acceptance Record: Flashcards and Integrations

**Workspace**: `flashcards-and-integrations` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Evidence Table

证据编号均引用本 feature 的 [verify-evidence.md](verify-evidence.md)，对应实现快照 `snapshot:b2d9bb81b113fe2fec9926e92b957922fbca665a79fa95dc4df2c7668f1f5134`。

| Requirement | Evidence IDs | Evidence Summary | Verdict |
|---|---|---|---|
| FR-001：经过验证的本地笔记与学习者审核证据 | E-001, E-004 | 拒绝无效笔记、缺失证据及跨 topic 引用；Skill 明确禁止用答案或模型分析推断学习者事实 | PASS |
| FR-002：首版仅 Basic 问答 | E-001, E-004 | proposal 校验 front/back，预览核验 Basic/Front/Back 模型契约 | PASS |
| FR-003：Markdown 卡片正文唯一权威 | E-001, E-004 | SQLite v4 仅存身份与关系；卡片验证从 Markdown 读取正文 | PASS |
| FR-004：保留全部来源与定位 | E-001 | 合并保留 note/evidence ID、证据间接关联的来源及同源不同 locator；未知定位为空 | PASS |
| FR-005：目标去重、显式合并与冲突处理 | E-001, E-004 | topic/objective 唯一；新增来源需指定 card ID；replay 不重写；显式批准 replacement 才替换正文 | PASS |
| FR-006：批准与失败回滚 | E-001 | 未批准、无效 proposal、文件操作或 commit 失败不留下部分卡片/关系；replacement 失败恢复原文件 | PASS |
| FR-007：复用已有牌组与多对多映射 | E-001 | 映射前读取现有 deckNames；验证多 topic/多 deck、未知牌组拒绝及移除映射 | PASS |
| FR-008：只读、可审核的 Anki 预览 | E-001, E-004 | 完整 JSON 显示目标、正文、来源、证据状态和远端匹配；四类结果；无远端写 action | PASS |
| FR-009：显式调用、loopback 与超时 | E-001, E-004 | opt-in gate、固定本地 endpoint、只读 allowlist、超时、大小限制、完整响应与错误路径均有覆盖 | PASS |
| FR-010：nmem 可选只读检索 | E-001, E-004 | canonical Skill 明确默认关闭、只读 search/show、结果仅作临时上下文；host 链接一致；未声称宿主实测 | PASS |
| FR-011：离线草稿独立于适配器 | E-001, E-004 | 临时模板副本在无 Anki/nmem 的情况下完成 setup 到 card validate；核心无第三方运行依赖 | PASS |

## Decision Capture Outcome

| Decision ID | Planned Status | Final Status | Consequence Observed | Evidence | Drift / Follow-up |
|---|---|---|---|---|---|
| DEC-001 | accepted | accepted | 卡片正文只存在 Markdown；SQLite 保存 ID、路径与来源关系 | E-001, E-004 | 无；无需旧版兼容框架 |
| DEC-002 | accepted | accepted | 稳定 objective/card ID 支持显式来源并集；内容冲突由学习者审核解决 | E-001, E-004 | 无；出现多版本需求后再设计 revision history |
| DEC-003 | accepted | accepted | loopback 只读预览可复用已有牌组；无发布或远端回收路径 | E-001, E-004 | 真实集合、本地化/自定义模型及 API-key endpoint 未验证 |
| DEC-004 | accepted | accepted | nmem 检索由 opt-in Skill/host 负责，结果不进入笔记或证据权威层 | E-001, E-004 | 宿主检索未实测；不声称模型行为评估通过 |

## Verdict Summary

| Dimension | Verdict | Notes |
|---|---|---|
| Component capability | PASS | 本地草稿、来源关系、冲突处理与只读 adapter 契约由 E-001、E-004 覆盖 |
| Workflow closure | PASS | 模板副本的 CLI 链路及 mock HTTP 预览链路均闭环；Skill/host 交接经静态审查 |
| User-visible outcome | PASS | 可读取/验证的 Basic 草稿和含完整比较内容的 JSON 预览满足首版范围 |

**Overall**: PASS（所选本地草稿及只读集成契约）。真实 Anki 集合、nmem 宿主执行及对话模型质量不在该结论的验证范围内。

## Workflow Replay

- **输入摘要**：临时模板副本、biology topic、带 `section:Membrane` 定位的注册来源/笔记、批准的 dimension/review/card proposal。
- **最终 payload 摘要**：setup → approved onboarding → source/note → approved profile dimension/review → profile → approved draft → list → validate；生成 `CARD-0001`，objective 为 `cell-membrane-function`，保留 `NOTE-0001`、`EVD-0001` 与来源定位。另以本地 HTTP fixture 返回现有牌组、Basic 模型及卡片内容供 CLI 预览。
- **用户可见结果断言**：profile 含证据 ID；卡片 listing/Markdown 与 registry 一致；预览是可审核 JSON，并保留远端匹配正文；副本的 host 链接仍指向 canonical Skill；模板源无学习者数据库。
- **Replay 类型**：E-001 的真实本地 CLI + fixture 数据；Anki 用隔离 HTTP mock，无真实学习者集合或外部写入。

## Closeout Checklist

| Item | Status | Evidence / Rationale | Next Step |
|---|---|---|---|
| 旧逻辑、旧路径或临时兼容退役 | 不适用 | 新模板功能；无旧卡片/远端发布路径，也无新增兼容层 | 无 |
| 发布、提交、CI 或 follow-through | 延后 | 工作树含前序 feature 的未提交文件；本轮未请求提交/推送或启用 GitHub Template | 见 umbrella commit plan，另行安排发布 |
| 文档、任务、roadmap 与上下文 | 已完成 | T001..T006 全部完成；E-005 核验 9 个必需来源；roadmap/current-progress/audit 同步 | 无 |
| SDD 最终收口校验 | 已完成 | E-006：closeout-ready 退出码 0；默认 validator 也通过 | 无 |
| ADR、架构债与演进信号 | 已完成 | DEC-001..DEC-004 及 E-004；普通失败回滚有测试，跨文件/DB 的强杀或断电恢复无 journal 保证 | 出现 crash recovery 或发布需求后单独设计 |
| Knowledge Capture | 已完成 | 下表仅保存在本地；不调用外部知识库写入 | 无 |

## Knowledge Capture

| Type | Title | Summary | Evidence | Scope | Sync Status | Follow-up |
|---|---|---|---|---|---|---|
| decision | 卡片正文与身份分离 | Markdown 是卡片可编辑正文；SQLite 仅保存稳定身份和关系。结构验证不能替代来源内容核查。 | DEC-001；E-001、E-004 | learnBase 本地卡片 | recorded-only | 无 |
| pattern | 显式目标与来源并集 | 目标键限定在 topic 内；显式 card ID 合并来源并保留旧定位；内容替换单独审核。 | DEC-002；E-001 | learnBase 同目标草稿合并 | recorded-only | 多版本需求出现后再扩展 |
| convention | 外部检索单独启用 | Anki/nmem 默认关闭；预览和检索不带来发布或同步权限。 | DEC-003、DEC-004；E-001、E-004 | learnBase Skills 与可选适配器 | recorded-only | 外部写入需新 feature |
| gotcha | 回滚与断电恢复边界 | 普通文件/数据库异常可回滚；两个存储介质之间没有 crash-recovery journal。 | data-model.md；E-001、E-004 | 卡片持久化 | recorded-only | 对强杀恢复有明确需求时设计 journal |

## Commit Result

| Field | Value |
|---|---|
| Status | not_submitted |
| Commit Hashes | 无 |
| Commit Messages | 无 |
| Included Files | 无实际提交；建议批次见 [umbrella commit plan](../learnbase-template/commit-plan.md) |
| Excluded / Remaining Files | README 及未跟踪的 tools/tests/Skills/docs/specs 等本地模板实现 |
| Reason | 用户要求实现与验证；本轮未请求提交、推送或启用 GitHub Template |

## Completion Record

- **最终结论**：PASS（本地首版功能及 closeout）。
- **完成依据**：E-001 的 45 项测试、E-002 语法、E-003 模板卫生、E-004 主线程审查、E-005 上下文 freshness、E-006 closeout-ready；上述需求表逐项覆盖 FR-001..FR-011。
- **阻塞项**：无。
- **延后项**：Anki 发布/更新/删除/回收、nmem 写入不属于首版；Git 提交、推送与 Template 启用另行安排。更丰富的来源适配器仍以实际反复抽取问题为启动条件。
- **退役结论**：新功能，无旧路径需退役。
- **提交结论**：not_submitted；未执行 git add/commit/push。
- **后续动作**：本轮所选 roadmap 范围交付完成；学习者已确认暂无反复抽取问题，`richer-source-adapters` 保留原启动条件。提交/发布另行安排。
