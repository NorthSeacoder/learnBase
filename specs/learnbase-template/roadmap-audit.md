# Roadmap 范围审计

**Date**: 2026-11-10 | **Roadmap**: [roadmap.md](roadmap.md)

## 后续默认行为调整

用户随后要求面向自用简化：Anki/nmem 默认支持，不需要 enable 开关或 setup 探测。`default-integration-support` 实现并重新验证这一调整，见其 [验收](../default-integration-support/acceptance.md) 与 [当前证据](../default-integration-support/verify-evidence.md)。下述 M3 requirement 映射与快照保留为原交付历史；默认关闭的说明已由后续 feature 替代，只读边界保留。

## 当前结论

M1、onboarding、M2 与所选 M3 首版均有本地实现和验收证据。M3 [E-001](../flashcards-and-integrations/verify-evidence.md) 的 45 项测试是当前共享实现的全量回归；旧 ledger 保留历史结论，不将旧快照改写为当前实现。

学习者已于 2026-11-10 明确答复“暂未遇到，按原条件保留后续项”。因此本轮已同意的本地交付范围为以上四个 feature；`richer-source-adapters` 保留为条件后续项，不声称已经实现，也不因本机缺少 PDF/OCR 命令而引入依赖。M3 E-005/E-006 记录全部 9 项必需上下文匹配和 SDD closeout-ready 通过，本轮整体目标按该范围收口。

## Requirement 覆盖

| Feature / Requirements | 当前交付与证据 | 状态 / 未覆盖范围 |
|---|---|---|
| M1 FR-001..FR-007 | 当前测试覆盖 setup、稳定 topic/source/note ID、PDF 只读登记、指纹/replay/变更拒绝、来源定位和 note validate；历史验收逐项映射 | 本地交付 |
| M1 FR-008、NFR-001 | canonical study Skill、离线标准库核心和 host extraction 边界；M3 模板副本 replay | 本地交付；未捆绑抽取器 |
| Onboarding FR-001..FR-005、FR-009..FR-010 | 当前全量回归验证 rerun、可跳过字段、unknown/empty、批准、原子写入和模板副本；Skill 保留问卷 | 本地交付 |
| Onboarding FR-006 | integrations 默认 false；setup/onboarding 不索取远端配置；M3 opt-in 测试 | 本地交付 |
| Onboarding FR-007 | 原先 deferred 的多对多 topic/deck 映射与既有牌组复用，现由 M3 FR-007、E-001/E-004 消费 | 交接已完成 |
| Onboarding FR-008 | M3 FR-008/FR-009 提供只读预览；Skill 明确预览不授权远端发布 | 发布动作继续不提供；不是已验证的写入流程 |
| M2 FR-001..FR-003、FR-009..FR-010 | 四类活动、学习者输入/模型分析分离、证据状态与 append-only history；当前全量回归覆盖 | 本地交付 |
| M2 FR-004、FR-007..FR-008 | topic 独立维度、默认空、明确资格/数量/时间门槛，unknown/conflicting 投影与来源链接 | 本地交付；不输出掌握分数 |
| M2 FR-005、FR-011 | profile show/report 从 SQLite 推导；报告路径及失败回滚测试 | 本地交付 |
| M2 FR-006、FR-012 | idempotency key/digest、相同 payload replay、不同 payload 拒绝与无部分写入 | 本地交付 |
| M3 FR-001..FR-006 | Basic Markdown 草稿、审核证据、稳定目标、来源并集、显式替换及普通失败回滚；M3 E-001/E-004 | 本地交付；强杀/断电恢复无 journal 保证 |
| M3 FR-007..FR-009 | opt-in 多对多映射及 loopback 只读预览；HTTP mock、allowlist、timeout/大小/响应错误测试 | 本地协议验收；未测试真实集合/自定义模型/API key |
| M3 FR-010..FR-011 | canonical Skill 的默认关闭、只读 nmem search/show 与临时上下文规则；离线 CLI replay 和 host 链接 | 文档/结构与本地链路验收；未作宿主检索或模型行为 eval |
| richer-source-adapters | 原 roadmap 要求“反复抽取限制 + 宿主能力”后 specify；学习者确认暂未遇到 | deferred by confirmed start condition；继续保留后续项 |

## 后续顺序

1. M3 的 freshness / closeout-ready 校验及状态同步已完成。
2. 已记录用户确认暂无问题，按条件延后来源适配器；本轮 roadmap 目标收口。
3. 日后出现反复抽取问题时，先记录材料类别、失败表现和宿主能力，再 specify/plan/tasks，实现与验证对应可选 adapter。

## 独立的发布跟进

Git commit/push、GitHub Template 启用、Anki 发布/回收和 nmem 写入均未执行。它们分别需要提交/发布指令或未来写入 feature 的具体审核，不作为当前只读能力的隐式后续步骤。文件范围见 [commit-plan.md](commit-plan.md)。
