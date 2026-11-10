# Plan: 默认支持已有集成

**Date**: 2026-11-10 | **Execution Mode**: direct | **Fallback**: none

## DEC-001: 去掉启用开关，调用时判断可用性

- Status: accepted
- 依据：用户最新要求优先于 M3 DEC-004 中默认关闭的配置门禁。
- 决定：移除 `_require_integration`、其唯一 tomllib 用途及模板 integrations 字段。Anki 沿用固定 loopback、只读 allowlist 和现有 timeout/error 行为；nmem 沿用 Skill/host 只读检索与缺失跳过。
- 取舍：不在 setup 探测服务。服务可用性随运行状态变化，持久化当时状态只会增加无效配置。
- 保留：Anki 写入需另行预览/授权；nmem 不作正式笔记或证据权威。

## Changes and Validation

- CLI：只移除 Anki gate，其他协议和错误处理不变。
- 配置/Skill/README：删除手动 enable 步骤；说明依赖和按需使用。保留 README 现有结构，仅更新相关段落。
- 测试：修改已有 adapter 测试，证明无配置也调用 read API；移除 fixtures 中人工启用配置；保留错误与无写入回归。
- 验证：45 项既有全量测试、compile、diff 与文档链接检查、SDD closeout。Anki 使用本地 HTTP fixture，不访问真实集合；nmem 指引静态核对，无模型 eval。
