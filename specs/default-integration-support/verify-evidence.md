# Verify Evidence: Default Integration Support

**Date**: 2026-11-10

## Implementation Baseline

| Field | Value |
|---|---|
| Implementation Baseline | snapshot:219fc8f53b5103b16f7ea94c034b199d0e3a8386440bc093ece2e5ba6270ab34 |
| Baseline Scope | 下表 CLI、测试、配置、README、规则与当前交互文档 |
| Captured At | 2026-11-10T12:17:48Z |

快照为下列路径到 SHA-256 的 map 经 Python `json.dumps(map, sort_keys=True)` 序列化后的 SHA-256。specs/进度记录不计入实现基线。M3 的旧证据保持历史状态，不用于证明本轮默认行为。

| File | SHA-256 |
|---|---|
| `tools/learnbase.py` | d6cde4107a8d96ac4d9d6016d58d591a14b41fdec675ff7c555ac7b59bb0ab04 |
| `tests/test_learnbase.py` | 8329f8da00dedb7da5789198719e1e951d228f6d8b2285600ad3656628629f72 |
| `README.md` | 5f5504a6412b5321255e7ba4579eedc43e4c295e783ed14e4a79f0599083c271 |
| `AGENTS.md` | 02369c35968d3cf3090725abf2118f85813b3a7f34cffa52f4eb74b76c30e82c |
| `learnbase.toml` | 3735d6cf75c2d37c3ebd98a67e082c1d263e6413e98876bb43cd2e7446528e0a |
| `docs/cli.md` | ae9bd5d5357a16a51b622a93849a879a5bc11e22af7776b44c34e8cc8ebd0cb5 |
| `docs/architecture.md` | 2cd37a3c7a43a8dd89593612d101a8b1403981324f56bcf4f825e83227ddfbbb |
| `docs/glossary.md` | 242364b75ab247c295e3866928e5e89251e8a8dd201b01d40659b450ec7fc02e |
| `docs/adr/0004-layered-onboarding.md` | 72e52de8aa1635950c32e064e1394113ed42b45f0c63ea7cd080724ac97e190f |
| `.agents/skills/learnbase-flashcards/SKILL.md` | f5039a2912ba8f6f17ed1c2a030627be7841eb3ff84d78dc8a71333918885daa |
| `.agents/skills/learnbase-study/SKILL.md` | 274a0469fd36753b7a99639d15c7d55656eb5a83ed77c275ef72ada9871e82c2 |

## Evidence Ledger

| ID | Maps To | Action | Result | Exit/Verdict | Observed At | Based On | Scope | Source | Status |
|---|---|---|---|---|---|---|---|---|---|
| E-001 | FR-001..FR-004, T001, T003 | `rtk proxy python3 -W error::ResourceWarning -c` unittest discovery, capturing routine stdout | 45 tests passed in 3.586s; Anki works without a config file; prior source/onboarding/profile/card/HTTP-error regressions pass | exit 0 | 2026-11-10T12:17:48Z | snapshot:219fc8f53b5103b16f7ea94c034b199d0e3a8386440bc093ece2e5ba6270ab34 | CLI、离线流程、只读 HTTP adapter 与 Skill 链接 | `tests/test_learnbase.py`: test_anki_adapter_works_without_configuration_and_rejects_writes_and_errors; test_anki_preview_uses_only_read_actions_and_classifies_existing_basic_notes; test_anki_malformed_transport_and_preview_results_fail_without_writes; test_fresh_template_cli_replays_source_review_profile_and_card_workflow | fresh |
| E-002 | FR-002..FR-005, DEC-001, T002 | 定点审查 setup、Anki gate 删除、README 与 canonical Skills；compileall | 无新增 setup 网络调用/能力缓存；Anki 保留 read allowlist/timeout/error；nmem 默认可用、不可用跳过；Python 编译通过 | PASS | 2026-11-10T12:17:48Z | snapshot:219fc8f53b5103b16f7ea94c034b199d0e3a8386440bc093ece2e5ba6270ab34 | 默认行为、依赖、用户可见错误与来源/授权边界 | `tools/learnbase.py` setup_workspace/anki_decks/_ankiconnect_request; README Anki and nmem; flashcards Skill Optional Anki Preview/Optional nmem Retrieval | fresh |
| E-003 | FR-005, T003 | `rtk git diff --check`、Markdown 链接/空白与模板 DB 检查 | 无 diff/空白或已有文档链接错误；新建验收文件的前向链接将在创建后复核；模板无学习者数据库 | exit 0 | 2026-11-10T12:17:48Z | snapshot:219fc8f53b5103b16f7ea94c034b199d0e3a8386440bc093ece2e5ba6270ab34 | 文档与模板卫生 | Python 本地链接/空白扫描；template DB exists=false | fresh |

| E-004 | T003, FR-005 | `rtk bash /Users/yqg/.agents/skills/sdd/scripts/validate-sdd.sh --workspace-root /Users/yqg/personal/libs/learnBase --closeout-ready`; full local-link/whitespace scan | validate-sdd: OK; all local links resolve and whitespace scan is empty after acceptance creation | exit 0 | 2026-11-10T12:19:54Z | snapshot:219fc8f53b5103b16f7ea94c034b199d0e3a8386440bc093ece2e5ba6270ab34 | SDD tasks/ledger/acceptance and active/roadmap alignment | validator command output; link scan JSON; acceptance.md and umbrella roadmap | fresh |

## Limits and Verdict

- 测试使用隔离本地 HTTP mock；因监听 loopback 在沙箱外运行，未访问真实 Anki 或 nmem。
- nmem 是 Skill/host 工作流；这里只核对指导契约，不声称真实检索或模型行为 eval 通过。
- setup 不检测服务，因此不会将“此刻未运行”写成长期 disabled 配置。显式 Anki CLI 失败返回错误，Skill 不能将跳过冒充成功预览。
- DEC-001 无架构漂移：删除配置 gate，没有新增依赖、抽象层或远端写入。
- Verdict: PASS（默认支持与既有只读契约）；E-004 记录 SDD closeout-ready 与完整文档链接检查通过。
