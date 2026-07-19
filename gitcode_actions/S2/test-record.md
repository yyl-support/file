# S2 变量优先级测试记录

## 1. 范围与历史证据

范围：TC-533、TC-534。

| 项目 | 历史值 |
| --- | --- |
| Workflow | `yyl-s2-vars` |
| Run ID | `4e430566214f4b9aada060f5ed972511` |
| Job ID | `e27450397e934cc7811d0cee9a739d06` |

## 2. 当前结果

| TC | Excel 预期 | 当前状态 | 已观察行为 | 证据强度与后续动作 |
| --- | --- | --- | --- | --- |
| TC-533 | `env > vars` | PARTIAL | Job 中 `env.SAME_NAME` 保持为 `env_value`，对应 Step 已完成；未保留 `vars.SAME_NAME` 的实际解析对照值 | 尚不能证明同名 `env` 与 `vars` 的优先级；需用独立 Workflow 输出可复核的对照结果 |
| TC-534 | `vars > ATOMGIT_*` | PARTIAL | `vars.ATOMGIT_SHA` 对应 Step 失败；Job API 中 `ATOMGIT_SHA=env_system_value`，但 Excel 未给出统一优先级解析入口 | 失败步骤和 Job 环境表不能单独证明 `vars` 与系统变量的最终覆盖关系；日志下载 API 为 HTTP 404，需取得原始用例语法或平台规则后复测 |

## 3. 结果解读与风险

1. 历史运行至少说明 `vars` 相关 Workflow 曾进入 Job 创建/步骤执行路径，但这不自动证明 `vars` 已按预期解析。
2. 仓库现有平台说明标注 `vars.*` 不受支持，与上述运行事实存在冲突。后续复测必须以原始解析错误、步骤状态和实际解析值为准，不得只引用其中任一方。
3. Job 日志下载接口返回 HTTP 404，因此 TC-534 的失败 shell 输出目前不可用；保留的 Job API 能证明失败位置，但不足以自行还原所有表达式展开细节或最终优先级。
4. 后续独立 YAML 必须先通过用例评审，再执行 `TC-533-env-overrides-vars.yml` 与 `TC-534-vars-overrides-system-variable.yml`。

## 4. 清理状态

历史 Workflow `yyl-s2-vars.yml` 已从 `main` 移除。后续复测仅在受控分支或 `workflow_dispatch` 下进行，执行完成后在本地保存清理说明。
