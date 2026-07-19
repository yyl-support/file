# S1 密钥（Secrets）测试计划

## 1. 测试目标与判定原则

负责人：`yulin`。

本模块验证 GitCode Actions 中 `secrets` 上下文、不同作用域的密钥，以及密钥输出安全性。用例的**预期结果以 `gitcode-pipeline-test-cases.xlsx` 为唯一业务判定标准**；当前平台行为、历史执行结论和平台文档仅用于判断可执行性及记录实际差异，不能据此修改 Excel 预期。

执行顺序固定为：先评审单个 TC 是否具备正确的前置条件、断言和证据路径，再创建并执行对应 Workflow。未完成评审的 TC 不得执行，也不得因为 Workflow 能运行就判定通过。

## 2. 范围

共 12 个用例：`TC-008`、`TC-009`、`TC-010`、`TC-011`、`TC-100`、`TC-101`、`TC-102`、`TC-443`、`TC-444`、`TC-530`、`TC-531`、`TC-532`。

后续每个用例使用独立文件，命名格式为 `TC-<编号>-<name>.yml`，保存在本目录。示例：`TC-009-project-secret.yml`。

## 3. 执行前通用检查

1. 在项目设置中确认测试用密钥已经配置，且名称、作用域和值均与当前 TC 一致。
2. 为每个 Workflow 的 Job 和 Step 设置非空 `name`；单个 Job 的 Step 数不得超过 16。
3. 密钥值必须是专用测试值，不得使用生产凭据、个人 Token 或可复用 Token。
4. 任何需要查看日志的操作先检查日志内容，日志、截图和本地证据中不得保留明文密钥。
5. 每次执行后在本地保存 Run API、Job API、已脱敏日志及执行说明；日志 API 无法取得时，必须如实记录，不得用“已运行”替代日志断言。
6. Workflow 执行结束后移除临时触发文件或触发条件，确认不再继续触发。

## 4. 用例评审清单

| TC | Excel 预期结果 | 执行前必须确认 | 正确断言与证据 | 评审结论 |
| --- | --- | --- | --- | --- |
| TC-008 | 组织级 Secret 可供组织下项目使用 | 当前项目所属组织已配置 `SECRET_ORG`，且允许该项目访问 | Job 环境中变量非空；保存 Job 元数据与脱敏日志 | 缺少组织资源时标记 `BLOCKED`，不能改写预期 |
| TC-009 | 项目级 `SECRET_PROJ` 仅在当前项目可用 | 当前项目已配置专用 `SECRET_PROJ`；另有受控对照项目且未配置同名 Secret | 当前项目引用非空，对照项目同名引用为空或不可用；两侧均保存脱敏 Job 日志 | 无对照项目时只能验证“可用”，状态为 `PARTIAL` |
| TC-010 | 环境 Secret 仅在 Job 的 `environment` 匹配时可用 | 已创建绑定 `PROD_KEY` 的 `prod` 环境，以及未绑定该 Secret 的对照环境 | `environment: prod` 时引用非空；对照环境引用为空或不可用；保存两次脱敏 Job 日志 | 无对照环境时只能验证“匹配环境可用”，状态为 `PARTIAL`；缺少环境资源时为 `BLOCKED` |
| TC-011 | 输出完整 Secret 时日志显示为 `***` | 配置一次性测试 Secret；可安全读取日志 | 仅输出完整测试值，检查日志中出现掩码而非明文 | 无日志证据只能为 `PARTIAL` |
| TC-100 | 读取 `secrets.atomgit_token` 时返回掩码值 | 平台提供对应 Token，且允许安全验证 | 只验证日志掩码，不保存 Token 明文 | 无日志证据只能为 `PARTIAL` |
| TC-101 | 读取 `secrets.NPM_TOKEN` 时返回掩码值 | 配置专用 `NPM_TOKEN` | 只验证完整值的掩码表现 | 无日志证据只能为 `PARTIAL` |
| TC-102 | 读取 `secrets.SUPERSECRET` 时返回掩码值 | 配置专用 `SUPERSECRET` | 只验证完整值的掩码表现 | 无日志证据只能为 `PARTIAL` |
| TC-443 | 不应通过可能绕过掩码的方式输出 Secret | 已取得待审查 Workflow YAML 和执行日志 | 静态检查所有 `run`、`env`、Action 参数中不存在 `echo '${{secrets.X}}'`、整体 `secrets` 输出或等价危险输出；运行日志仅含固定非敏感文本 | 这是安全设计审查，不以 Workflow 成功作为主要证据 |
| TC-444 | 不应将 Secret 写入制品或缓存 | 已取得待审查 Workflow YAML、制品清单和缓存配置/列表 | 静态确认没有 Secret 注入文件、Artifact 或缓存路径；若使用 Artifact，仅上传固定非敏感内容；若使用缓存，缓存键和路径均不引用 Secret；检查制品和缓存列表 | 未检查缓存配置或列表时只能为 `PARTIAL` |
| TC-530 | 未定义 Secret 返回空字符串，不报错 | 不创建该名称的 Secret | 引用未定义 Secret 并断言为空；记录解析、运行或平台拒绝结果 | 按实际结果判定 PASS/FAIL |
| TC-531 | 含连字符的 Secret 名称可正常访问 | 平台允许创建该名称的 Secret | 创建并引用该名称，验证可访问 | 平台拒绝创建或访问时为 `FAIL` |
| TC-532 | 空值 Secret 可配置且读取为空字符串，不报错 | 平台允许创建空值 Secret | 创建空值并断言引用结果为空 | 平台拒绝创建或访问时为 `FAIL` |

## 5. Workflow 设计要求

1. 每个 TC 只验证一个 Excel 预期，禁止一个 Workflow 混合多个 TC 的结论。
2. 使用显式 Job 环境变量承接 Secret，例如 `TEST_VALUE: ${{ secrets.SECRET_PROJ }}`，再用 shell 断言非空或为空。
3. 掩码用例只能打印完整的一次性测试值，禁止拆分、编码、拼接或打印片段，避免构造绕过掩码的行为。
4. TC-443 是静态安全设计审查：逐行检查 `run`、`env`、Action 参数和日志，禁止 `echo '${{ secrets.X }}'`、整体 `secrets` 输出、Secret 拼接或等价输出方式；Workflow 成功不能单独证明该 TC 通过。
5. TC-444 同时检查 Artifact 和缓存：禁止将 Secret 注入待上传文件、上传路径、缓存路径或缓存键；未使用缓存时保留 YAML 静态检查证据，使用缓存时还必须保存缓存配置和列表证据。
6. 对平台解析阶段拒绝的配置，保存报错、YAML 和 API 结果；该结果本身是对 Excel 预期的反例证据。

## 6. 结果判定

- `PASS`：完成了 Excel 预期对应的行为断言，且证据可复核。
- `FAIL`：平台实际行为与 Excel 预期相反，包括创建、解析或运行阶段的明确拒绝。
- `PARTIAL`：行为步骤已执行，但掩码等必须依赖日志/UI 的证据不可取得。
- `BLOCKED`：组织、环境、凭据等必要资源未配置，无法开始有效验证。
- `SKIP`：仅在平台明确声明不支持且无需继续运行验证时使用，必须附带原始错误或平台说明。

## 7. 本地证据与清理

每个已执行用例在本地建立 `evidence/TC-<编号>/`，至少保存 `run.json`、`job.json`、`notes.md`；有日志时仅保存已脱敏的 `log.txt`。所有结果、YAML 和证据先保留在本地，待全部用例完成后再统一提交。

## 8. 已发现的平台问题与规避规则

1. GitCode 的每个 Job 必须显式声明非空 `name:`。缺少 Job `name` 时，Workflow 会在创建 Job 前失败，API 特征为 `status=FAILED`、`jobs=[]`。
2. Job 创建前失败是 Workflow 配置失败，不能作为该 Workflow 中全部 TC 的行为结果。必须先使用一个带 `name` 的单 Job、单 Step 探针，确认 `jobs=1` 后再逐项增加 Secret、Action 或断言。
3. GitCode 的 Job 日志下载接口在已完成的 S1 Job 上返回 HTTP 404。Run/Job API 可以证明 Step 完成，但不能证明 UI 是否显示 `***`；缺少 UI 或日志掩码证据时，TC-011、TC-100、TC-101、TC-102 必须记录为 `PARTIAL`。
