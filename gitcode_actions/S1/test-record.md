# S1 密钥（Secrets）测试记录

## 1. 记录原则

本记录保存已发生的实际观察结果，不以历史计划或平台限制替代 Excel 预期。最终判定仍以 `gitcode-pipeline-test-cases.xlsx` 中的预期结果为准；当平台行为不同，应记录为 `FAIL`，并保留可复核证据。

范围：`TC-008`、`TC-009`、`TC-010`、`TC-011`、`TC-100`、`TC-101`、`TC-102`、`TC-443`、`TC-444`、`TC-530`、`TC-531`、`TC-532`。

## 2. 历史执行证据

以下 ID 为历史执行记录，后续复测应在对应 TC 的本地证据目录中补充 API 响应和脱敏日志。

| 用途 | Run ID | Job ID（如有） |
| --- | --- | --- |
| 解析器探测 | `b2c00e174faf44b1b53c357774aae419` | - |
| `ATOMGIT_TOKEN` 探测 | `55e05fcb80844f2cb78c1e4d877f1142` | - |
| `SECRET_PROJ` 探测 | `d64f41d2e9b94e38a0e1714c5510d191` | - |
| `NPM_TOKEN` 探测 | `0addc57fb83c4c99864c8580b8735e43` | - |
| `SUPERSECRET` 探测 | `8b87465abe8d400b847dd522f2888b68` | - |
| 核心检查 | `45e6fc81bf6841e48c930792fdf6775f` | `6b4de145277c456aa0bea7ccba12f86d` |

## 3. 已观察结果

| TC | 当前状态 | 已观察到的实际行为 | 与 Excel 预期的关系 | 后续动作 |
| --- | --- | --- | --- | --- |
| TC-008 | BLOCKED | 未配置组织级 Secret 资源 | 尚未验证 | 配置组织资源后重新执行 |
| TC-009 | PARTIAL | 项目级 `SECRET_PROJ` 以非空环境变量注入当前项目 Job | 已验证“当前项目可用”，但未在未配置同名 Secret 的对照项目验证“仅当前项目可用” | 配置受控对照项目后完成负向验证 |
| TC-010 | BLOCKED | 未配置环境与环境级 Secret | 尚未验证 | 配置环境资源后重新执行 |
| TC-011 | PARTIAL | 掩码步骤执行，但 Job 日志下载 API 返回 HTTP 404 | 缺少 `***` 日志证据 | 日志可用后复测 |
| TC-100 | PARTIAL | 相关 Secret 可注入，但日志 API 返回 HTTP 404 | 缺少掩码日志证据 | 日志可用后复测 |
| TC-101 | PARTIAL | 相关 Secret 可注入，但日志 API 返回 HTTP 404 | 缺少掩码日志证据 | 日志可用后复测 |
| TC-102 | PARTIAL | 相关 Secret 可注入，但日志 API 返回 HTTP 404 | 缺少掩码日志证据 | 日志可用后复测 |
| TC-443 | PARTIAL | 历史 Workflow 未输出 Secret，未使用危险的整体 Secret 输出方式 | 现有记录未保留逐行 YAML 静态审查和完整脱敏日志，尚不能覆盖全部危险输出形式 | 补充静态审查清单和日志证据 |
| TC-444 | PARTIAL | 历史上传内容为固定非敏感文本 | 已覆盖 Artifact 的部分安全检查，但未保留缓存配置或缓存列表证据 | 补充缓存静态检查和列表证据 |
| TC-530 | PASS | 未定义 Secret 的引用未导致错误，行为符合空值语义 | 符合预期 | 保存对应 YAML 与 API 证据 |
| TC-531 | FAIL | 平台拒绝创建或使用 `MY-SECRET-NAME` 这类含连字符名称 | 与“可正常访问”预期相反 | 保存平台报错并保持 FAIL |
| TC-532 | FAIL | 平台拒绝创建空值 Secret | 与“可配置并读取为空”预期相反 | 保存平台报错并保持 FAIL |

## 4. 关键限制与风险

1. 历史执行中，Job 日志下载接口对全部 S1 Job 返回 HTTP 404。因此，依赖日志中 `***` 的 TC-011、TC-100、TC-101、TC-102 不能仅凭 Job 成功判定 PASS。
2. 项目级 `SECRET_PROJ`、`NPM_TOKEN`、`SUPERSECRET` 与 `ATOMGIT_TOKEN` 曾以非空环境变量注入；该事实不能替代日志掩码验证。
3. 组织级和环境级资源尚未配置，因此 TC-008、TC-010 应保持 `BLOCKED`，不能用项目级 Secret 的结果推断。
4. 后续测试只使用一次性测试密钥，所有本地日志必须脱敏，禁止保存明文值。

## 5. 清理状态

历史 Workflow `yyl-s1-core-secrets.yml` 已从 `main` 移除，并已通过 GitCode Contents API 确认其不存在。后续新增的每个 TC Workflow 也必须在执行窗口结束后清理触发条件，并在本地记录清理证据。
