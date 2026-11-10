# Feature: 默认支持 Anki 与 nmem

**Status**: closed, local PASS | **Date**: 2026-11-10

## Scope

用户主要自行使用 learnBase，要求默认支持已有 Anki/nmem 适配器，并在 README 说明条件；不需要 setup 探测和持久化启用状态。本 feature 更新先前 M3 的默认关闭决策；M3 原验收作为历史保留。

- FR-001：移除 Anki/nmem 的 integrations 配置开关。显式 Anki 读取命令直接使用已有 adapter；nmem 由 Skill 使用可用宿主检索或 CLI。
- FR-002：setup 仅初始化本地状态，不探测、启动、安装外部服务，不写入能力缓存；核心仍可离线使用。
- FR-003：Anki 失败明确提示且不修改本地卡片；Skill 可说明预览不可用后继续本地流程。nmem 不可用时跳过检索，不阻塞本地流程。
- FR-004：保留只读集成范围、学习者证据与来源规则。默认支持不授权 Anki 发布或 nmem 写入。
- FR-005：README、CLI 文档与 canonical Skills 明确依赖、调用方式和失败行为，不再要求先启用。

## Profile and Traits

- Change Profile: medium（默认行为跨代码、配置和交互指引；无新增外部写入）
- Feature Traits: user-visible-output、artifact-handoff、decision-capture
- 不增加插件框架、setup 自动探测、兼容层、nmem transport 或外部写入。

## Acceptance

无 integrations 配置的临时 workspace 可以通过 Anki mock 读取牌组并预览；离线 setup/草稿仍可运行；API 错误/超时测试继续通过；README/Skill 明确默认支持与按需可用性。
