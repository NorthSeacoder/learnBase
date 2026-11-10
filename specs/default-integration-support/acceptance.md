# Acceptance: Default Integration Support

**Date**: 2026-11-10 | **Spec**: [spec.md](spec.md) | **Evidence**: [verify-evidence.md](verify-evidence.md)

## Evidence Table

| Requirement | Evidence IDs | Evidence Summary | Verdict |
|---|---|---|---|
| FR-001 默认支持、无 enable 开关 | E-001, E-002 | 无 TOML 文件的 Anki 读取成功；模板及 Skill 不要求 enable 字段 | PASS |
| FR-002 setup 保持本地 | E-001, E-002 | 原 setup/模板副本回归通过；函数未添加探测、安装或网络调用 | PASS |
| FR-003 不可用时的明确行为 | E-001, E-002 | Anki API/超时/损坏响应继续报错；Skill 说明预览未运行，nmem 不可用跳过检索 | PASS |
| FR-004 保留只读与证据边界 | E-001, E-002 | HTTP action allowlist 与无写入回归通过；nmem 不作笔记/证据权威 | PASS |
| FR-005 README 与交互契约 | E-002, E-003 | README 依赖表及命令示例、CLI/Skill/规则/架构说明同步 | PASS |

## Decision Capture Outcome

| Decision ID | Final Status | Consequence Observed | Evidence | Drift / Follow-up |
|---|---|---|---|---|
| DEC-001 | accepted | 删除默认关闭门禁；按使用时的服务状态处理可用性；用户无需先编辑配置 | E-001, E-002 | supersedes M3 默认关闭规则；只读范围不变 |

## Verdict Summary

| Dimension | Verdict | Notes |
|---|---|---|
| Component capability | PASS | 现有 adapter 可直接调用，未增加 setup 探测机制 |
| Workflow closure | PASS | 45 项回归覆盖无配置读取、离线核心、错误路径和模板副本；nmem 宿主执行未实测 |
| User-visible outcome | PASS | README 解释“默认支持”和外部依赖；服务缺失时结果明确 |

**Overall**: PASS（本地默认行为与只读指导契约）。

## Workflow Replay

- 输入：无 learnbase.toml 的临时 workspace、HTTP 牌组/Basic fixture、已有草稿。
- 结果：Anki 直接返回牌组或可审核预览 JSON；API 错误及超时不更改草稿；独立模板副本仍可离线完成 setup 至 card validate。见 E-001 的对应测试名。
- 类型：本地 CLI + HTTP fixture；无真实集合访问。nmem 仅审查 Skill，未声称宿主或模型行为验收。

## Closeout Checklist

| Item | Status | Evidence / Rationale |
|---|---|---|
| 旧门禁退役 | 已完成 | 删除 _require_integration、唯一 tomllib 用途及 integrations 字段；E-002 |
| 文档与规则 | 已完成 | README、CLI、Skill、AGENTS 和进度文档同步；E-002/E-003 |
| 架构决策 | 已完成 | DEC-001 明确替代 M3 默认关闭；未新增探测/插件框架 |
| SDD 最终结构检查 | 已完成 | E-004：closeout-ready 退出码 0，完整文档链接检查通过 |
| Knowledge Capture | 已完成 | 下表仅本地保存 |
| Git/模板发布 | 延后 | 未请求 commit/push；文件范围已列入 umbrella commit plan |

## Knowledge Capture

| Type | Title | Summary | Evidence | Scope | Sync Status | Follow-up |
|---|---|---|---|---|---|---|
| decision | 按需判断服务可用性 | 自用 workspace 默认支持已有 adapter；服务状态变化不写入启用配置。默认支持不授权外部写入。 | DEC-001；E-001/E-002 | learnBase Anki/nmem | recorded-only | 无 |

## Completion Record

- 最终结论：PASS；本地实现与 closeout 完成。
- 完成依据：E-001 的 45 项测试、E-002 定点审查与编译、E-003 文档/模板卫生、E-004 SDD closeout-ready。
- 阻塞项：无。
- 延后项：真实 Anki/nmem 宿主实测、模型 eval、提交/推送；外部写入仍不在当前范围。
- 退役结论：启用 gate 及配置已删除，不保留兼容层。
- 提交结论：not_submitted；见 [commit plan](../learnbase-template/commit-plan.md)。
- 后续动作：无未完成实现；更丰富的来源 adapter 仍以真实反复抽取问题为条件。
