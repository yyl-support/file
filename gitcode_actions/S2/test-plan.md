# S2 变量优先级测试计划

## 1. 测试目标与判定原则

负责人：`yulin`。本模块验证 `env`、`vars` 与 `ATOMGIT_*` 系统变量同名时的解析优先级。

Excel 是唯一预期来源：TC-005 预期组织级 vars 在组织下项目可用；TC-006 预期项目级 vars 仅当前项目可用；TC-007 预期项目级 vars 覆盖组织级 vars；TC-533 预期 `env > vars`；TC-534 预期 `vars > ATOMGIT_*` 系统变量。平台是否支持 `vars`、YAML 是否能解析、Job 是否创建，均为执行前或执行中的事实，不得据此改写 Excel 预期。

每个 TC 必须先完成“表达式是否被解析、是否能设置对照值、如何读取最终值、证据来自何处”的评审，之后才生成和执行对应独立 Workflow。

## 2. 范围与文件命名

| TC | Excel 预期 | 计划文件 |
| --- | --- | --- |
| TC-005 | 组织级 `ORG_VAR` 在组织下项目可用 | `yyl-session2-vars.yml` |
| TC-006 | 项目级 `PROJ_VAR` 仅当前项目可用 | `yyl-session2-vars.yml` |
| TC-007 | 同名 `DUP` 时项目级 vars 覆盖组织级 vars | `yyl-session2-vars.yml` |
| TC-533 | 同名时 `env` 覆盖 `vars` | `TC-533-env-overrides-vars.yml` |
| TC-534 | 同名时 `vars` 覆盖 `ATOMGIT_*` 系统变量 | `TC-534-vars-overrides-system-variable.yml` |

## 3. 执行前评审

| TC | 对照数据设计 | 正确断言 | 必须保存的证据 | 不能接受的结论 |
| --- | --- | --- | --- | --- |
| TC-005 | 在组织设置中定义 `ORG_VAR=org_value` | `${{ vars.ORG_VAR }}` 解析后必须非空 | 原始 YAML、Run/Job API、脱敏日志或等价步骤输出 | 仅因当前 Workflow 被识别就判定组织 vars 可用 |
| TC-006 | 在项目设置中定义 `PROJ_VAR=project_value`，并使用未配置该变量的对照项目 | 当前项目解析值必须为 `project_value`；对照项目为空或不可用 | 两个项目的原始 YAML、Run/Job API、脱敏日志 | 只验证当前项目非空就判定“仅当前项目可用” |
| TC-007 | 组织与项目均定义 `DUP`，值分别为 `org_value`、`project_value` | `${{ vars.DUP }}` 必须解析为 `project_value` | 原始 YAML、Run/Job API、脱敏日志或等价步骤输出 | 仅验证任一 `DUP` 值非空 |
| TC-533 | 在 Job `env` 设 `SAME_NAME=env_value`，同时配置可读取的 `vars.SAME_NAME=vars_value` | 实际解析到的同名值必须为 `env_value` | 原始 YAML、Run/Job API、脱敏日志或等价步骤输出 | 仅因 Job 创建成功就判定 `env > vars` |
| TC-534 | 保留可识别的系统变量值，同时配置同名 `vars` 值 | 实际解析到的值必须为 `vars` 值，而非系统变量值 | 原始 YAML、Run/Job API、脱敏日志或等价步骤输出 | 仅通过 Job 环境表推断 `vars` 已覆盖 |

### 3.1 当前评审结论：不能直接生成优先级断言 Workflow

Excel 中 TC-533、TC-534 的“引用语法”和“YAML 示例片段”均为空，预期规则仅注明“仅能经 Job 日志断言”。因此，Excel 明确了目标优先级，但没有定义 `env`、`vars`、`ATOMGIT_*` 在哪个表达式、环境变量注入点或运行时解析位置会自动合并为同一个“最终值”。

`${{ env.SAME_NAME }}`、`${{ vars.SAME_NAME }}` 和 Shell 的 `$SAME_NAME` 是三个可能不同的读取位置：分别读取前两者只能证明对应上下文能否解析，读取 Shell 变量还会受到 Job/Step `env` 注入方式影响。未经平台语法或原始用例示例确认，不能把任一读取位置主观定义成 Excel 所说的“优先级”。

在获得以下任一信息前，TC-533、TC-534 只允许执行语法/环境探针，不允许生成声称验证优先级的正式 YAML：

1. Excel 用例的原始 YAML 示例或引用语法；
2. GitCode 官方文档中关于 `env`、`vars`、`ATOMGIT_*` 同名覆盖发生位置的明确规则；
3. 用例编写人确认的统一解析入口，例如某个固定的 `${{ ... }}` 表达式或 Runner 环境变量注入规则。

若取得上述信息，先在本节补充“统一解析入口、三个对照值、预期最终值、失败时的日志特征”，再创建对应 `TC-533-*.yml` 或 `TC-534-*.yml`。

## 4. Workflow 设计要求

1. 每个 TC 一个文件、一个命名 Job 和一个直接的值比较断言。
2. 对照值必须不同且不包含真实凭据，例如 `env_value`、`vars_value`、`system_value`。
3. 先记录 Workflow 在解析阶段、Job 创建阶段或步骤运行阶段的表现；只有步骤真实解析并比较到最终值，才可验证优先级。
4. 若平台明确拒绝 `vars.*`，先保存原始错误。只有在已确认统一解析入口的前提下，该拒绝才能作为 Excel 优先级预期的 `FAIL`；未确认入口时，记录为 `SKIP`，原因是无法构成可归因的优先级比较。
5. 执行完成后删除临时触发配置，保存本地证据；所有文件待全部测试结束后统一提交。

## 5. 结果判定

- `PASS`：实际步骤明确验证了 Excel 规定的优先级。
- `FAIL`：表达式被实际解析且解析值与 Excel 预期相反，或平台明确拒绝实现该 Excel 预期。
- `PARTIAL`：步骤已执行但缺少读取最终值所必需的日志/UI 证据。
- `SKIP`：平台明确不支持该语法，且无法开展有意义的优先级比较。
- `BLOCKED`：缺少变量配置权限或其他必要资源。

## 6. 本地证据

每次执行在 `evidence/TC-533/` 或 `evidence/TC-534/` 保留 YAML 副本、`run.json`、`job.json`、已脱敏日志和 `notes.md`。记录中必须区分“语法已解析”和“优先级已验证”。

## 7. 已发现的平台问题与规避规则

1. GitCode Job 必须显式设置 `name:`；否则 Workflow 可在 Job 创建前失败并返回 `jobs=[]`。
2. S2 实测表明 `vars` 表达式可被平台接受到创建和执行 Job 的阶段，不能在没有查看 Job/Step 状态时笼统判定为解析拒绝。
3. Job 日志下载接口返回 HTTP 404 时，必须保存 Run API、Job API、Step 状态和 Job 环境变量表作为替代证据；这些证据只能说明步骤是否运行，不能凭空补出最终输出值。
