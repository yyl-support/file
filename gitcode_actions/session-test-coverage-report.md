# Yulin Session 测试覆盖与验证报告

更新时间：2026-07-19。Excel 预期结果是本报告的测试判定标准；GitCode Actions 中 Step 显示 `COMPLETED` 仅表示该 Step 的脚本以零退出码结束，不自动代表对应 Excel TC 通过。

## 1. 总览

### 1.1 统计口径

本报告统计 S1、S2、S3、S13 共 56 条 TC。S2 按 Excel 实际变量范围计入 TC-005、TC-006、TC-007、TC-533、TC-534 五条；四条聚合 Workflow 已在 `main` 运行。页面日志与下载的 S13 Job ZIP 是本轮取证来源。

`PARTIAL` 表示“运行一半”：Workflow/Step 已执行或已获得部分正向事实，但缺少 Excel 预期所需的完整对照、页面日志或触发事件证据。`BLOCKED` 表示当前无法开展有效验证，原因是缺资源、缺前置对照、缺真实触发条件或基础 Scheduler 失效。

| 状态 | TC 数 | 占比 | 含义 |
| --- | ---: | ---: | --- |
| PASS | 5 | 8.9% | Excel 预期已由实际断言和可复核证据满足 |
| FAIL | 4 | 7.1% | 平台实际行为与 Excel 预期相反 |
| PARTIAL | 9 | 16.1% | 已部分运行或观察到部分行为，但证据不足以完成判定 |
| BLOCKED | 38 | 67.9% | 缺少资源、对照或真实触发事件，不能完成有效验证 |
| **合计** | **56** | **100%** | S1 12 + S2 5 + S3 24 + S13 15 |

| Session | TC 数 | PASS | FAIL | PARTIAL | BLOCKED | 当前主要问题 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| S1 | 12 | 1 | 2 | 7 | 2 | 组织/环境/对照项目资源和页面掩码证据不足 |
| S2 | 5 | 0 | 2 | 1 | 2 | `vars`/Job `env` 表达式可解析但未注入 Bash；组织和双层对照资源不足 |
| S3 | 24 | 0 | 0 | 0 | 24 | 两个 Job ZIP 均来自手动分支，仍无真实 Schedule Run |
| S13 | 15 | 4 | 0 | 1 | 10 | 容器初始化、`set-env`、组织资源、MR/Tag/Docker/Schedule 前置条件 |

所有聚合 Workflow 均在 `main/.gitcode/workflows/` 下，可通过 `workflow_dispatch` 从页面手动运行。日志下载 API 对这些 Job 返回 HTTP 404，因此日志掩码类断言需在 GitCode 页面人工查看，不能仅依赖 API。

### 1.2 全部 TC 状态总表

| Session | TC | Excel 验证目标 | 当前状态 | 当前事实与缺口 | 下一步验证动作 |
| --- | --- | --- | --- | --- |
| S1 | TC-008 | 组织级 Secret 在组织下项目可用 | BLOCKED | 未配置 `SECRET_ORG` 和项目授权 | 配置组织 Secret 后在当前项目断言非空 |
| S1 | TC-009 | 项目级 Secret 仅当前项目可用 | PARTIAL | 当前项目 `SECRET_PROJ` 非空；无对照项目 | 在未配置该 Secret 的对照项目运行同一断言 |
| S1 | TC-010 | 仅匹配 environment 时可用 | BLOCKED | 无匹配与不匹配环境 Secret 对照 | 建 `prod` 和对照环境，比较 `PROD_KEY` |
| S1 | TC-011 | 完整 Secret 输出显示 `***` | PARTIAL | Step 已运行；日志 API 404，未确认页面掩码 | 用一次性 Secret 通过 env 注入 echo，在页面确认 `***` |
| S1 | TC-100 | `secrets.YULIN_ATOMGIT_TOKEN` 被掩码 | PARTIAL | Token 可注入；无页面掩码证据 | 页面输出完整值，确认 `***` |
| S1 | TC-101 | `secrets.NPM_TOKEN` 被掩码 | PARTIAL | Token 可注入；无页面掩码证据 | 页面输出完整值，确认 `***` |
| S1 | TC-102 | `secrets.SUPERSECRET` 被掩码 | PARTIAL | Secret 可注入；无页面掩码证据 | 页面输出完整值，确认 `***` |
| S1 | TC-443 | 不使用危险 Secret 输出方式 | PARTIAL | 当前 YAML 不直接输出 Secret；无全量审查清单 | 扫描 yulin YAML 的 run/env/Action 参数并记录结果 |
| S1 | TC-444 | Secret 不写入 Artifact/缓存 | PARTIAL | 未保存 Artifact/缓存配置和列表证据 | 检查文件、上传路径、缓存键/路径和缓存列表 |
| S1 | TC-530 | 未定义 Secret 为空且不报错 | PASS | 空值断言完成 | 保存 Run/Job API 证据 |
| S1 | TC-531 | 连字符 Secret 名可访问 | FAIL | 平台拒绝 `MY-SECRET-NAME` 创建/使用 | 保留平台拒绝证据；如平台更新再复测 |
| S1 | TC-532 | 空值 Secret 可创建并读取为空 | FAIL | 平台拒绝创建空值 Secret | 保留平台拒绝证据；如平台更新再复测 |
| S2 | TC-005 | 组织级 `ORG_VAR` 可用 | BLOCKED | 修订 Workflow 已运行，但 `${{ vars.ORG_VAR }}` 非空断言以 code 1 失败；未配置/授权组织变量 | 配置并授权 `ORG_VAR=org_value` 后复测 |
| S2 | TC-006 | 项目级 `PROJ_VAR` 仅当前项目可用 | PARTIAL | 输出 `project_var_present=true`，确认当前项目可读；无对照项目 | 在未配置该变量的对照项目运行同一断言 |
| S2 | TC-007 | 项目 vars 覆盖组织 vars | BLOCKED | `${{ vars.DUP }}` 对 `project_value` 的断言失败，未提供两级 `DUP` 配置证明 | 配置组织 `org_value` 与项目 `project_value` 后复测 |
| S2 | TC-533 | `env > vars` | FAIL | `${{ vars.SAME_NAME }}` 和 `${{ env.SAME_NAME }}` 都正确解析，但两 Job 的 `$SAME_NAME` 都是 `UNSET` | 平台 Job `env` 未注入 Bash，保留日志证据 |
| S2 | TC-534 | `vars > ATOMGIT_*` | FAIL | `$ATOMGIT_SHA` 基线已注入，但平台保留 `ATOMGIT_` 前缀，无法创建同名 `vars.ATOMGIT_SHA` 对照 | 保留保留前缀限制和系统变量基线证据 |
| S3 | TC-237 | cron 到点创建 Schedule Run | BLOCKED | 本轮两个 Job ZIP 都是手动分支，未包含 `event=schedule`；历史 18 分钟观察不足以排除部署/时间窗口因素 | 在 `main` 等待 UTC 10:00（北京时间 18:00）及延迟窗口的真实 Schedule Run |
| S3 | TC-427 | cron 使用 UTC | BLOCKED | 无真实 Schedule Run 可比较 | 在 TC-237 正向成功后比较计划 UTC 与 Run 时间 |
| S3 | TC-428 | 非默认分支不调度 | BLOCKED | 无默认分支正向 Scheduler 基线 | 先建立正向基线，再观察非默认分支完整窗口 |
| S3 | TC-429 | 小于五分钟间隔无效 | BLOCKED | Scheduler 基线失败 | 单独启用 `*/1`，观察 6 分钟和延迟窗口 |
| S3 | TC-430 | 调度可有分钟级延迟 | BLOCKED | 无真实 Schedule Run | 记录计划 UTC 与 Run 创建时间差 |
| S3 | TC-471 | `*` 每分钟触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `* * * * *`，观察连续分钟 Run |
| S3 | TC-472 | `,` 列表星期触发 | BLOCKED | Scheduler 基线失败 | 在目标周一/三/五窗口启用并观察 |
| S3 | TC-473 | `-` 星期范围触发 | BLOCKED | Scheduler 基线失败 | 在工作日窗口启用并观察 |
| S3 | TC-474 | `/` 步长触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `*/15`，观察两个边界 |
| S3 | TC-475 | 分钟字段边界 | BLOCKED | Scheduler 基线失败 | 单独启用 `30 * * * *`，观察目标时间 |
| S3 | TC-476 | UTC 小时字段边界 | BLOCKED | Scheduler 基线失败 | 单独启用 `0 2 * * *`，观察 UTC 02:00 |
| S3 | TC-477 | 月日字段边界 | BLOCKED | Scheduler 基线失败/日期窗口长 | 在下月 1 日观察，或先记录配置接受 |
| S3 | TC-478 | 月字段边界 | BLOCKED | Scheduler 基线失败/日期窗口长 | 在下个 1 月 1 日观察，或先记录配置接受 |
| S3 | TC-479 | 星期字段边界 | BLOCKED | Scheduler 基线失败 | 下个周日 UTC 00:00 观察 |
| S3 | TC-505 | 分钟列表触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `5,15,25 * * * *` |
| S3 | TC-506 | 分钟范围触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `0-5 * * * *` |
| S3 | TC-507 | 分钟步长触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `*/15 * * * *` |
| S3 | TC-508 | `?` 语法 | BLOCKED | Scheduler 基线失败 | 先验证配置接受，再观察下一 02:00 UTC |
| S3 | TC-509 | `L` 最后一天 | BLOCKED | Scheduler 基线失败/日期窗口长 | 先验证配置接受，月末观察 |
| S3 | TC-510 | `W` 最近工作日 | BLOCKED | Scheduler 基线失败/日期窗口长 | 先验证配置接受，目标日期观察 |
| S3 | TC-511 | `#` 第 N 个星期 | BLOCKED | Scheduler 基线失败/日期窗口长 | 先验证配置接受，目标星期观察 |
| S3 | TC-512 | 范围加步长触发 | BLOCKED | Scheduler 基线失败 | 单独启用 `5-45/10 * * * *` |
| S3 | TC-562 | 非默认分支 schedule 不触发 | BLOCKED | 无默认分支正向基线 | 与 TC-428 同一对照方式验证 |
| S3 | TC-563 | Schedule 可延迟数分钟 | BLOCKED | 无真实 Schedule Run | 使用任何已验证 cron 记录延迟 |
| S13 | TC-035 | `atomgit.action` 返回当前 Action 名 | PASS | ZIP 日志输出 `atomgit_action=TC-035 atomgit action`，与当前 Step 名称一致 | 无 |
| S13 | TC-036 | `atomgit.token` 可用且受保护 | PASS | `YULIN_ATOMGIT_TOKEN` 非空断言成功，日志显示 `atomgit_token=***` | 无 |
| S13 | TC-194 | 项目 vars 覆盖组织 vars | BLOCKED | 两级 vars 未配置 | 配置不同 `DUP` 值，断言项目值 |
| S13 | TC-195 | 项目 Secret 覆盖组织 Secret | BLOCKED | 两级 Secret 未配置 | 安全布尔比较项目 Secret 是否被选中 |
| S13 | TC-220 | 系统变量默认 `false` | BLOCKED | 旧 YAML 仅断言变量字面值，不能验证禁用不安全命令的实际能力；已改为两步传播探针，尚未运行 | 手动运行修订 Workflow，确认 `::set-env` 后下一 Step 中变量仍不可见 |
| S13 | TC-273 | Job 使用自定义容器 | BLOCKED | `container.image: alpine:3.20` Job 的 ZIP 只有调度检查行，脚本未启动；缺容器初始化失败信息 | 从 Job 总览补充容器创建/拉取失败原因 |
| S13 | TC-304 | checkout 拉取仓库 | PASS | checkout 使用 `repository`/`token` 成功 fetch 并 checkout `origin/main`；后续 `README.md` 失败因仓库无该文件 | 将后置断言改为现存 `.gitcode/workflows/yyl-session13-workflows.yml` |
| S13 | TC-354 | Secret 日志掩码为 `***` | PASS | ZIP 日志显示 `mask_test_secret=***`，且非空断言通过 | 无 |
| S13 | TC-355 | 默认 false 禁止 `set-env` | BLOCKED | 本轮 ZIP 未包含独立两步探针 Job 日志 | 运行并取得 `TC355_PROBE` 下一 Step 可见性日志 |
| S13 | TC-387 | ci 场景在 Push/PR 构建测试 | PARTIAL | 手动运行不能验证 Push/PR 触发 | 专用分支 Push 或 MR 创建 Run 并完成最小构建 |
| S13 | TC-388 | PR 提交自动检查 | BLOCKED | 未创建测试 MR | 创建受控 MR 并记录 MR 事件 Run |
| S13 | TC-389 | Tag 触发发布 | BLOCKED | 未创建测试 Tag/Release | 推送一次性 Tag 并记录 CreateTag Run |
| S13 | TC-390 | 构建并推送 Docker 镜像 | BLOCKED | 无 Docker/registry 资源 | 配置测试 registry 后验证 build 与 push |
| S13 | TC-391 | 每日定时构建 | BLOCKED | 无真实 Scheduler Run | 临时单 cron，观察 Schedule 事件 |
| S13 | TC-535 | Secret/vars 同名空间独立 | BLOCKED | 同名对照资源未配置 | 分别注入不同值，输出三个布尔比较结果 |

## 2. S1 密钥测试

### 当前覆盖

本轮 S1 页面日志确认 `SECRET_PROJ` 以非空值注入，输出 `project_secret_present=true`。TC-531、TC-532 的 FAIL 依据是平台 Secret 创建 UI 的历史拒绝证据；本次 Workflow 仅复述该结论，未在 Runner 中创建 Secret。

| TC | Excel 预期 | 当前结论 | 依据与限制 |
| --- | --- | --- | --- |
| TC-008 | 组织级 Secret 在组织下项目可用 | BLOCKED | 未配置组织级 Secret/授权项目 |
| TC-009 | 项目级 Secret 仅当前项目可用 | PARTIAL | 当前项目非空；无对照项目验证“仅当前项目” |
| TC-010 | 仅匹配 `job.environment` 时可用 | BLOCKED | 无匹配与不匹配环境对照 |
| TC-011 | 日志将完整 Secret 替换为 `***` | PARTIAL | 本次摘录未包含 `MASK_TEST_SECRET` 输出行 |
| TC-100 | `secrets.atomgit_token` 被掩码 | PARTIAL | 本次摘录未包含 Token 输出行；S13 的独立 `YULIN_ATOMGIT_TOKEN` 已验证掩码 |
| TC-101 | `secrets.NPM_TOKEN` 被掩码 | PARTIAL | 本次摘录未包含 NPM Token 输出行 |
| TC-102 | `secrets.SUPERSECRET` 被掩码 | PARTIAL | 本次摘录未包含 SUPERSECRET 输出行 |
| TC-443 | 避免危险 Secret 输出写法 | PARTIAL | 当前 YAML 不直接输出 Secret；尚无全量静态审查清单 |
| TC-444 | 不写入 Artifact/缓存 | PARTIAL | 未检查缓存和 Artifact 实际配置/列表 |
| TC-530 | 未定义 Secret 为空且不报错 | PASS | 空值断言完成 |
| TC-531 | 含连字符 Secret 可正常访问 | FAIL | 历史实测平台拒绝创建/使用连字符名称 |
| TC-532 | 空值 Secret 可创建并读取为空 | FAIL | 历史实测平台拒绝创建空值 Secret |

### 进一步验证方式

1. 为 TC-008 配置 `SECRET_ORG`，并授权当前项目；手动运行后断言其非空。
2. 为 TC-009 创建一个未配置 `SECRET_PROJ` 的对照项目：当前项目应非空，对照项目应为空或不可用。
3. 为 TC-010 建立 `prod` 环境和一个不绑定 `PROD_KEY` 的对照环境；比较两个 Job 的引用值。
4. 对 TC-011、100、101、102 使用一次性测试 Secret，在页面 Job 日志中确认 `***` 且无明文；不要将明文复制到本地报告。
5. 对 TC-443 扫描全部 yulin Workflow 的 `run`、`env`、Action 参数，确认没有直接/拼接/编码输出 Secret。
6. 对 TC-444 检查 Artifact 文件、缓存路径、缓存键和缓存列表，确认没有 Secret 表达式进入持久化路径。

## 3. S2 Vars 测试

### 当前覆盖

本轮修订版 S2 已执行五条 TC。日志证明 `${{ vars.SAME_NAME }}` 与 `${{ env.SAME_NAME }}` 可解析，但 Job `env` 的 `SAME_NAME` 未进入 Bash；两项 Shell 优先级断言均失败。

| TC | Excel 预期 | 当前结论 | 依据与限制 |
| --- | --- | --- | --- |
| TC-005 | 组织级 `ORG_VAR` 在组织项目中可用 | BLOCKED | `${{ vars.ORG_VAR }}` 非空断言失败，缺组织变量配置或项目授权 |
| TC-006 | 项目级 `PROJ_VAR` 仅当前项目可用 | PARTIAL | `project_var_present=true`；仍缺未配置变量的对照项目 |
| TC-007 | 项目级 `DUP` 覆盖组织级 `DUP` | BLOCKED | 断言项目值 `project_value` 失败，未提供组织/项目两级不同 `DUP` 配置 |
| TC-533 | `env > vars` | FAIL | 两个 Job 的表达式值均正确，但 `$SAME_NAME=UNSET`，Job `env` 未注入 Bash |
| TC-534 | `vars > ATOMGIT_*` | FAIL | `$ATOMGIT_SHA` 系统基线存在；平台保留 `ATOMGIT_` 前缀，无法创建同名 vars 对照 |

### 进一步验证方式

1. 配置并授权组织变量 `ORG_VAR=org_value`，复测 TC-005。
2. 在不含 `PROJ_VAR` 的对照项目复测 TC-006。
3. 在组织和项目分别配置 `DUP=org_value`、`DUP=project_value`，复测 TC-007。
4. TC-533 保留失败证据：表达式解析成功而 Job `env` 未注入 Shell。
5. TC-534 保留失败证据：`YULIN_ATOMGIT_SHA` 不等价于保留的系统变量名，不能替代同名覆盖对照。

## 4. S3 Schedule 测试

### 当前覆盖

本轮两个 S3 Job ZIP 均为手动触发分支：`schedule_core` 输出 `PARTIAL manual run cannot verify schedule trigger`，`schedule_extended` 仅输出候选 cron 文本。它们证明 YAML 可解析和 Bash Step 可执行，但不含 `event=schedule`。

| TC 范围 | 当前结论 | 原因 |
| --- | --- | --- |
| TC-237 | BLOCKED | 手动 Job 明确不是 Scheduler 事件；历史 18 分钟观察不能排除部署、时区或观察窗口因素 |
| TC-427、TC-430、TC-563 | BLOCKED | `date -u` 只证明 Runner UTC 时钟；无真实 Schedule Run，无法验证调度 UTC/延迟 |
| TC-428、TC-562 | BLOCKED | 无默认分支正向 Scheduler 基线，无法归因非默认分支不触发 |
| TC-429、TC-471 至 TC-479、TC-505 至 TC-512 | BLOCKED | 手动候选 cron 文本不构成 Scheduler 解析或触发证据 |

### 进一步验证方式

1. 先单独复测 TC-237：仅启用一个有效 cron，在 `main` 记录 `planned_utc`、提交 SHA、发布时间和观察结束时间。
2. 只接受事件为 `schedule` 的 Run；手动运行、Push 或重跑不能作为 schedule 证据。
3. Run 创建时间必须落在计划 UTC 时间及允许延迟窗口内，且保存 Job 开始时间作为辅助证据。
4. TC-237 正向触发成功后，再串行执行其他用例；同一时刻绝不启用两个测试 cron。
5. 对“不应触发”的 TC-428/562，必须先有默认分支正向对照，再覆盖一个完整理论触发时刻和延迟窗口。
6. TC-429 应使用 `*/1 * * * *` 验证“小于五分钟”，因为 Excel 中 `*/5` 示例与其文字预期矛盾；`*/5` 只能作为正向对照。
7. 每次观察结束立即移除 `on.schedule` 并确认清理，避免持续消耗 Runner。

## 5. S13 Push 与工作流能力测试

### 当前覆盖

本轮 S13 运行的三个下载 ZIP 覆盖主 Job、TC-304 checkout Job 和 TC-273 container Job。日志确认 `atomgit.action`、Token/Secret 掩码和 checkout 能力；容器 Job 在脚本启动前停止，需补容器初始化阶段证据。

| TC | 当前结论 | 依据与限制 |
| --- | --- | --- |
| TC-035 | PASS | 日志为 `atomgit_action=TC-035 atomgit action`，与当前 Step 名称一致 |
| TC-036 | PASS | `YULIN_ATOMGIT_TOKEN` 非空断言通过，输出为 `atomgit_token=***` |
| TC-194 | BLOCKED | 未配置组织级和项目级同名 vars |
| TC-195 | BLOCKED | 未配置组织级和项目级同名 Secret |
| TC-220 | BLOCKED | 旧版只验证变量字面值，无法证明 `set-env` 是否被禁止；修订版以两步传播探针复测 |
| TC-273 | BLOCKED | `container.image: alpine:3.20` Job 日志仅有 duration check，Shell 脚本未启动；需容器初始化错误 |
| TC-304 | PASS | checkout 配置 Token 后成功 fetch 和 checkout `origin/main`；后续 `README.md` 断言失败因仓库无该文件，非 checkout 故障 |
| TC-354 | PASS | 一次性 Secret 非空断言通过，输出为 `mask_test_secret=***` |
| TC-355 | BLOCKED | 本轮下载 ZIP 未含独立两步 `set-env` Job 日志 |
| TC-387 | PARTIAL | 手动运行不能验证 Push/PR 构建触发 |
| TC-388 | BLOCKED | 未创建测试 MR |
| TC-389 | BLOCKED | 未创建测试 Tag/Release |
| TC-390 | BLOCKED | 未配置 Docker、镜像仓库和测试凭据 |
| TC-391 | BLOCKED | 未获得 Scheduler 实际运行证据 |
| TC-535 | BLOCKED | 未配置同名 Secret 与 vars 的不同测试值 |

### 进一步验证方式

1. TC-035、036、354 已取得 ZIP 日志证据并通过；不再输出或保存 Secret 明文。
2. TC-194/195/535 配置组织级和项目级同名资源，使用不同测试值；Secret 用 Runner 内布尔比较，不直接输出。
3. TC-220 手动运行修订后的两步 Job；若 `::set-env` 后 `TC355_PROBE` 仍不可见，则证明禁用能力存在。仅变量为 `UNSET` 不构成 FAIL。
4. TC-273 从 Job 总览或平台侧日志取得 `container.image` 创建/拉取失败原因；当前只有 Shell 未启动的现象。
5. TC-304 已通过 `repository: ${{ atomgit.repositoryUrl }}` 和 `token: ${{ secrets.YULIN_ATOMGIT_TOKEN }}` 成功检出；后置断言应改为现存 `.gitcode/workflows/yyl-session13-workflows.yml`，不能使用不存在的 `README.md`。
6. TC-355 取得独立 Job ZIP，执行无敏感的 `::set-env name=TC355_PROBE::allowed`，并在下一 Step 验证变量是否可见。
7. TC-387 至 TC-391 需要独立受控 Workflow：分别验证 Push/MR、MR、Tag、Docker 推送、Schedule 事件；页面手动运行只能验证 YAML 解析，不能替代触发行为。

## 6. 共通限制与建议顺序

1. GitCode Job 日志下载 API 当前持续返回 HTTP 404；掩码类和输出值类用例需要在页面人工查看日志并记录截图/结论。
2. 聚合 Workflow 适合确认文件可解析、Job 可创建、Step 可调度；它不能替代需要不同项目、组织资源、环境、MR、Tag、Docker 或真实 Schedule 事件的验证。
3. 页面运行聚合 Workflow 后，应先按本报告更新状态，不能把 Job 的绿色 `COMPLETED` 直接填为 Excel PASS。
4. 推荐后续优先级：S1 的对照资源与静态审查 -> S2 的 TC-005/006/007 配置和统一优先级语义 -> S13 的 TC-304/273/355 独立 Job -> S3 基础 TC-237 受控 schedule 复测。
