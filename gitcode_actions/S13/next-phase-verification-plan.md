# S13 下一阶段完整验证方案

## 1. 目标与授权范围

目标：以 `gitcode-pipeline-test-cases.xlsx` 的预期结果为判定依据，完成 S13 的 15 条用例真实功能验证。页面手动运行只用于可由 `workflow_dispatch` 验证的上下文、系统变量与 Secret 行为；Push、MR、Tag、容器和定时调度用例必须由对应真实事件触发。

已获授权：可创建、修改和清理测试用 Secret、Variables、Environment、测试分支、Tag、Merge Request 与临时 cron。所有测试值必须是一次性、非生产、不可复用值；禁止在本地证据、提交信息或报告中保存明文 Secret/Token。

## 2. 当前基线

现有手动 Run `ae4ddfa888a54e2c8b3fe5ca2cb58ce1` 已证明 S13 聚合 Workflow 的 15 个 Step 都可进入终态，`if: ${{ always() }}` 已阻止 TC-220 失败后跳过后续 Step。

当前已知事实：

| TC | 当前事实 | 下一步 |
| --- | --- | --- |
| TC-035 | `${{ atomgit.action }}` 非空 | 记录实际非敏感值并核对当前 Action 名称 |
| TC-220 | 手动运行中不满足 `false` 断言 | 页面确认实际值，保留 FAIL 或环境 BLOCKED 证据 |
| TC-304 | `uses: checkout` 失败 | 改为已验证的 repository/token 参数并增加文件断言 |
| 其余 TC | 聚合 Step 只输出 PARTIAL/BLOCKED 提示 | 依本计划补充真实资源与触发方式 |

## 3. 测试资源

### 3.1 Variables

在组织和当前项目分别创建下列测试变量：

| 名称 | 组织值 | 项目值 | 用途 |
| --- | --- | --- | --- |
| `DUP` | `org_var_s13` | `project_var_s13` | TC-194 项目 vars 覆盖组织 vars |
| `S13_NAMESPACE` | `org_var_namespace` | `project_var_namespace` | TC-535 vars 命名空间对照 |

### 3.2 Secrets

在组织和当前项目分别创建下列一次性测试 Secret：

| 名称 | 组织值 | 项目值 | 用途 |
| --- | --- | --- | --- |
| `DUP` | `org_secret_s13_once` | `project_secret_s13_once` | TC-195 项目 Secret 覆盖组织 Secret |
| `S13_NAMESPACE` | `org_secret_namespace_once` | `project_secret_namespace_once` | TC-535 Secret 与 vars 独立性 |
| `MASK_TEST_SECRET` | 不设置 | `mask_s13_once` | TC-354 页面日志掩码验证 |

测试完成、页面证据确认后立即轮换/删除全部上述 Secret。

## 4. 验证分组

### 4.1 手动上下文与安全组

文件：`yyl-session13-workflows.yml`，触发方式：`workflow_dispatch`。

| TC | 实现与判定 |
| --- | --- |
| TC-035 | 输出 `atomgit.action` 的非敏感值；非空且与当前运行 Action 名称一致为 PASS |
| TC-036 | 通过 `env` 注入 `${{ atomgit.token }}`；断言非空并输出完整一次性值，在页面确认 `***` 为 PASS |
| TC-194 | 读取 `${{ vars.DUP }}`，必须为 `project_var_s13`；否则 FAIL |
| TC-195 | 将 `${{ secrets.DUP }}` 与项目期望 Secret 安全注入 Runner；仅输出 `project_secret_selected=true/false`，true 为 PASS |
| TC-220 | 输出变量值或 `UNSET` 后断言精确 `false`；空值、true、其他值为 FAIL，若测试环境显式覆盖则 BLOCKED |
| TC-354 | `MASK_TEST_SECRET` 经 `env` 注入，输出 `MASK_CHECK=$MASK_CHECK`；页面显示 `***` 为 PASS |
| TC-355 | 第一 Step 检查开关为 false 并执行 `::set-env name=TC355_PROBE::allowed`；第二 Step 断言 `TC355_PROBE` 不等于 `allowed` |
| TC-535 | 分别注入 `${{ secrets.S13_NAMESPACE }}` 与 `${{ vars.S13_NAMESPACE }}`；只输出三个布尔结果：Secret 匹配、vars 匹配、两值不同；三者 true 为 PASS |

所有 Step 使用 `if: ${{ always() }}`，一条失败不阻断其余 TC。

### 4.2 Checkout 与容器组

文件：临时 `yyl-s13-runtime.yml`，触发方式：`workflow_dispatch`。

| TC | 实现与判定 |
| --- | --- |
| TC-304 | 命名 checkout Step 使用 `repository: ${{ atomgit.repositoryUrl }}` 与 `token: ${{ secrets.ATOMGIT_TOKEN }}`；下一 Step 断言 `.gitcode/workflows/yyl-session13-workflows.yml` 存在。两个 Step 完成即 PASS |
| TC-273 | 独立 Job 使用 `container: alpine:3.20`；在 Job 内断言 `/etc/alpine-release` 存在并输出 `container_os=alpine`。Job API resource 必须保留 container 配置。镜像/容器资源不可用为 BLOCKED |

### 4.3 Push 与 MR 组

文件：临时 `yyl-s13-push.yml` 与 `yyl-s13-pr-check.yml`。

| TC | 触发方式 | 判定 |
| --- | --- | --- |
| TC-387 | 专用分支 `test/yyl-s13-push` 的一次受控 Push | `ci` 场景 Workflow 由 Push 创建 Run，且最小构建/测试命令完成 |
| TC-388 | 由专用分支向 main 创建测试 MR 并推送一次提交 | `pr-check` 场景 Workflow 由 MR 事件创建 Run，事件类型和 Job 完成可复核 |

完成后关闭测试 MR，删除临时分支/文件或改回仅 `workflow_dispatch`。

### 4.4 Tag、Docker 与 Schedule 组

| TC | 文件与触发 | 判定 |
| --- | --- | --- |
| TC-389 | `yyl-s13-release.yml` 使用 `push.tags: [yulin-s13-release-*]`；推送一次性测试 Tag | Run 事件为 CreateTag，发布流程 Job 完成；缺发布资源为 BLOCKED |
| TC-390 | `yyl-s13-docker-build.yml`，由 `workflow_dispatch` 或受控 Tag 触发 | Docker build 和向测试 registry push 都完成；无 Docker/registry 权限为 BLOCKED |
| TC-391 | `yyl-s13-nightly.yml` 临时启用单个 `schedule` | 仅接受 Schedule 事件的真实 Run；记录 planned UTC、Run 创建时间、Job 时间。观察结束立即移除 cron |

## 5. 证据与判定

每个实际执行 TC 在 `S13/evidence/TC-<编号>/` 保存：

```text
run.json       完整 Actions Run API 响应
job.json       完整 Job API 响应
notes.md       前置资源、触发事件、预期、实际、状态和清理结果
log.txt        仅已脱敏的页面日志摘录；没有明文 Secret/Token
```

状态规则：

- PASS：完成 Excel 所述行为且有 Run/Job/页面证据。
- FAIL：平台行为与 Excel 预期相反。
- PARTIAL：行为执行，但掩码/UI 等关键证据不可取得。
- BLOCKED：授权已具备但平台资源、组织设置、Docker、registry 或 Scheduler 不可用。
- SKIP：平台明确不支持，且保存了原始解析/运行证据。

## 6. 串行执行顺序

1. 配置变量、Secret 与一次性测试值。
2. 更新并手动运行上下文与安全组，先记录 TC-035、036、194、195、220、354、355、535。
3. 运行 runtime 组，记录 TC-304、273。
4. 创建并验证一次受控 Push，记录 TC-387。
5. 创建测试 MR，记录 TC-388，随后关闭 MR。
6. 创建一次性 Tag，记录 TC-389；删除 Tag 或保留为测试证据。
7. 验证 Docker/registry 条件后运行 TC-390。
8. 最后单独启用并观察 TC-391 的真实 cron；结束后立即删除 schedule。
9. 轮换/删除全部测试 Secret、变量、环境、分支、MR、Tag、临时 Workflow 触发器，并更新 `test-record.md`。

## 7. 风险控制

1. 任何时刻只保留一个启用的 S13 schedule。
2. 不直接输出或保存 Secret 明文；掩码确认只能在页面查看完整一次性值的输出。
3. 每个临时 Push/MR/Tag Workflow 使用独立且精确的触发过滤，避免触发仓库其他业务 Workflow。
4. 任何 Job 日志 API 的 404 都记录为证据限制，不能据此把掩码类 TC 判为 PASS。
