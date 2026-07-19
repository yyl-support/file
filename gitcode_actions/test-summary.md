# Yulin 53 个用例测试总结

## 测试范围

测试范围以远端 `gitcode-pipeline-test-cases.xlsx` 中 `责任人=yulin` 为准，共 53 条：

| 会话 | 用例数 | TC 范围 |
| --- | ---: | --- |
| S1 Secrets | 12 | TC-008、009、010、011、100、101、102、443、444、530、531、532 |
| S2 变量优先级 | 2 | TC-533、534 |
| S3 Schedule | 24 | TC-237、427、428、429、430、471-479、505-512、562、563 |
| S13 Push 与工作流能力 | 15 | TC-035、036、194、195、220、273、304、354、355、387-391、535 |
| **总计** | **53** | |

## 结果统计

| 状态 | 数量 | 说明 |
| --- | ---: | --- |
| PASS | 5 | 已完成 Excel 预期对应的行为断言，并保存 API 证据。 |
| PARTIAL | 4 | 行为 Step 已完成，但 GitCode Job 日志 API 返回 404，无法取得掩码 UI/日志证据。 |
| FAIL | 4 | 平台行为与 Excel 预期相反。 |
| BLOCKED | 40 | 缺少必要资源，或平台基础能力失败导致无法对单个用例归因。 |
| SKIP | 0 | 无。 |
| **总计** | **53** | |

## 分会话结果

### S1 Secrets

| 状态 | 数量 | TC |
| --- | ---: | --- |
| PASS | 4 | TC-009、TC-443、TC-444、TC-530 |
| PARTIAL | 4 | TC-011、TC-100、TC-101、TC-102 |
| FAIL | 2 | TC-531、TC-532 |
| BLOCKED | 2 | TC-008、TC-010 |

主要结论：

- `SECRET_PROJ`、`NPM_TOKEN`、`SUPERSECRET`、`ATOMGIT_TOKEN` 均可通过 Job 环境变量非空断言读取。
- TC-443 的测试 Workflow 未执行 Secret 拆分、编码或片段输出。
- TC-444 的固定内容 Artifact 创建与上传 Step 完成，未向 Artifact 写入 Secret。
- TC-530 验证未定义 Secret 引用为空字符串且不报错。
- TC-531 失败：平台拒绝 `MY-SECRET-NAME` 连字符命名，只允许替代名 `MY_SECRET_NAME`。
- TC-532 失败：平台拒绝创建空值 Secret。
- TC-008 和 TC-010 因未配置组织级/环境级 Secret 被阻塞。

### S2 变量优先级

| 状态 | 数量 | TC |
| --- | ---: | --- |
| PASS | 1 | TC-533 |
| FAIL | 1 | TC-534 |

主要结论：

- TC-533：`env.SAME_NAME` 保持为 `env_value`，对应 Step 成功完成，符合 `env > vars` 预期。
- TC-534：`vars.ATOMGIT_SHA` 对应 Step 失败；Job API 显示 `ATOMGIT_SHA=env_system_value`，未体现 `vars > ATOMGIT_*` 的预期覆盖关系。

### S3 Schedule

| 状态 | 数量 | TC |
| --- | ---: | --- |
| FAIL | 1 | TC-237 |
| BLOCKED | 23 | TC-427、428、429、430、471-479、505-512、562、563 |

主要结论：

- 在 `main` 临时启用有效 cron `15 5 19 7 *`。
- 计划触发时间为 `2026-07-19T05:15:00Z`，发布后观察 18 分钟。
- 未创建任何匹配的 schedule Run，TC-237 判定为 FAIL。
- 因基础 scheduler 未触发，UTC 时区、调度延迟、默认分支、最小间隔、cron 运算符、字段边界和扩展语义均无法独立归因，记录为 BLOCKED。
- 测试 cron 已从 `main` 删除，且已通过 API 确认没有残留 `yyl-s3-*.yml` 文件。

### S13 Push 与工作流能力

| 状态 | 数量 | TC |
| --- | ---: | --- |
| BLOCKED | 15 | TC-035、036、194、195、220、273、304、354、355、387-391、535 |

主要结论：

- `yyl-s13-core` 共进行了三次最小差异尝试：初始版本、对齐 `checkout` 成功参考版本、隔离 `${{ atomgit.action }}` 表达式版本。
- 三次运行均被平台识别，但都在 Job 创建前失败：`status=FAILED`、`jobs=[]`。
- 因没有任何 S13 Job 被创建，不能将失败归因于单个 TC 的实际运行行为，全部记录为 BLOCKED。
- TC-194、TC-195 额外缺少组织级与项目级变量/Secret 覆盖资源；TC-388、389、390 额外需要 PR、Tag/Release、Docker 资源；TC-391 受 S3 scheduler 基础失败影响。
- `yyl-s13-core.yml` 已从 `main` 删除。

## 关键平台发现

1. GitCode Workflow 的每个 Job 必须显式声明非空 `name:`。缺少 Job `name` 会在创建 Job 前失败，表现为 `FAILED` 和 `jobs=[]`。
2. Job 创建前失败仅表示 Workflow 配置/编译失败，不能作为其中全部 TC 的行为结果。
3. S1 的最小增量探针证明：补充 Job `name` 后，Job 可正常创建；`ATOMGIT_TOKEN`、`SECRET_PROJ`、`NPM_TOKEN`、`SUPERSECRET` 的 Job env 注入均可运行。
4. GitCode Job 日志下载 API 在 S1、S2 完成的 Job 上返回 HTTP 404。Run API、Job API 和 Step 状态可以证明执行状态，但无法替代完整日志或 UI 掩码证据。
5. 有效 main 分支 cron 未触发，导致 S3 不能验证具体 cron 语法和调度语义。
6. S13 的 Workflow 在三次最小差异修改后仍无法创建 Job。后续如需继续排查，应从单 Job、单 Step、具名 Job 的 `yyl-s13-probe` 开始，每次只添加一个字段、表达式、env、uses Step 或断言。

## 证据与记录位置

| 内容 | 本地位置 |
| --- | --- |
| S1 测试方案与记录 | `D:\user\data\test-0719\S1\` |
| S2 测试方案与记录 | `D:\user\data\test-0719\S2\` |
| S3 测试方案与记录 | `D:\user\data\test-0719\S3\` |
| S13 测试方案与记录 | `D:\user\data\test-0719\S13\` |
| 汇总性描述 | `D:\user\data\test-0719\test-summary.md` |
| 逐 TC 本地结果与 API 证据 | `manual-results\yulin\`（测试工作区） |
| 一次性 Excel 待回填清单 | `manual-results\yulin\excel-patch.md`（测试工作区） |

## 清理与回填状态

- 已确认 `main` 不存在 `yyl-s*.yml` 临时测试 Workflow。
- 已确认 `main` 不存在 yulin S3 测试 cron。
- 已对本地证据和 `D:\user\data\test-0719` 完成已知测试 Secret/Token 明文扫描。
- Excel 尚未回填；53 条结果已整理在本地 `excel-patch.md`，应在最终确认后一次性更新 `测试结果` 和 `失败原因/备注` 两列。
