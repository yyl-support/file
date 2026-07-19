# S13 Push 与工作流能力验证测试计划

## 1. 测试目标与判定原则

负责人：`yulin`。本模块覆盖 `atomgit` 上下文、系统变量、组织/项目变量与密钥优先级、容器 Job、Action 调用、密钥掩码及常见 Workflow 命名和触发行为。

Excel 预期结果是唯一测试判定标准。每个 TC 先完成设计评审：确认触发方式、必要资源、真实断言和证据路径；只有满足前置条件时才创建并执行该 TC 的独立 Workflow。缺少 Docker、组织资源、合并请求、Tag/Release、Scheduler 或日志证据时，必须如实标记，禁止输出无条件 PASS。

## 2. 范围与计划文件

共 15 个用例：`TC-035`、`TC-036`、`TC-194`、`TC-195`、`TC-220`、`TC-273`、`TC-304`、`TC-354`、`TC-355`、`TC-387`、`TC-388`、`TC-389`、`TC-390`、`TC-391`、`TC-535`。

每个用例使用 `TC-<编号>-<name>.yml` 独立文件。本地保存的默认版本使用 `workflow_dispatch`；仅在经过评审的受控执行窗口内临时添加 `push`、`merge_requests`、Tag 或 `schedule` 触发，避免意外重复运行。

## 3. 用例评审清单

| TC | Excel 预期 | 执行前必须确认 | 正确断言和证据 |
| --- | --- | --- | --- |
| TC-035 | `atomgit.action` 返回当前 Action 名称 | 受控 Workflow 可运行 | 输出上下文的非敏感字段并与 Workflow 名称核对 |
| TC-036 | `atomgit.token` 返回 `ATOMGIT_TOKEN` 类 Token 且受保护 | 可安全查看脱敏日志 | 注入 `${{ atomgit.token }}` 后断言非空；仅检查日志掩码，不保存 Token 明文 |
| TC-194 | 项目 `vars` 覆盖组织 `vars` | 同名组织与项目变量均已配置，值分别为 `org_value`、`project_value` | `run: echo ${{ vars.DUP }}` 的输出必须为 `project_value`；保存脱敏日志 |
| TC-195 | 项目 Secret 覆盖组织 Secret | 同名组织与项目 Secret 均已配置，且均为一次性不同测试值 | 将 `${{ secrets.DUP }}` 和项目级期望值分别注入 Runner 环境，仅输出比较结果 `project_secret_selected=true/false` |
| TC-220 | `ATOMGIT_ACTIONS_ALLOW_UNSECURE_COMMANDS` 默认返回 `false` | 系统变量对 Runner 可见，且未被测试配置覆盖 | 输出该变量；值必须精确为 `false` |
| TC-273 | `jobs.<id>.container` 使用自定义容器 | 允许拉取公开、固定版本的测试镜像，Runner 支持容器 | 使用固定公开镜像并在 Job 内读取镜像特征文件；Job 元数据显示容器配置，命令在容器内完成 |
| TC-304 | `checkout` Action 可检出仓库代码 | 可用 Action 语法和测试仓库 | 命名 `uses: checkout` Step 后检查仓库文件存在 |
| TC-354 | Secret 输出日志显示 `***` | 一次性测试 Secret 与可读取日志 | 仅输出完整测试值，检查掩码 |
| TC-355 | 不安全命令开关默认关闭并限制 `set-env` | 系统变量未被覆盖；可使用无敏感内容的探针变量 | 先断言开关精确为 `false`，再执行只写入 `TC355_PROBE=allowed` 的 `set-env` 探针；后续 Step 中该变量不得可用，并保存失败/拒绝日志 |
| TC-387 | `ci.yml` 命名的工作流可在 push/PR 执行构建测试 | 受控 push 或 MR | 实际触发并完成最小构建/测试步骤 |
| TC-388 | `pr-check.yml` 自动检查 PR 提交 | 可创建测试 MR | MR 提交触发 Run 并记录事件类型 |
| TC-389 | `release.yml` 在 Tag 时触发发布流程 | 可创建测试 Tag/Release | Tag 触发 Run；缺少发布资源不得伪造成功 |
| TC-390 | `docker-build.yml` 构建并推送 Docker 镜像 | Docker、镜像仓库和测试凭据 | 构建与推送均有可复核证据 |
| TC-391 | `nightly.yml` 每日运行构建 | Scheduler 正常且有观察窗口 | 真实 Schedule Run 与计划时间匹配 |
| TC-535 | `secrets` 与 `vars` 同名时命名空间相互独立 | 同名 Secret 和 vars 已配置，值分别为一次性不同测试值 | 分别将 `${{ secrets.DUP }}` 与 `${{ vars.DUP }}` 注入不同 Runner 环境变量；只输出 `secret_matches_expected=true/false`、`var_matches_expected=true/false` 和 `values_are_distinct=true/false` |

## 4. Workflow 设计要求

1. 每个 YAML 仅对应一个 TC，文件名必须符合 `TC-<编号>-<小写-kebab-name>.yml`。
2. 每个 Job 与 Step 必须有 `name`；`uses: checkout` 等 Action Step 也必须有名称。
3. 默认提交版本使用 `workflow_dispatch`，执行 push 验证时采用专用测试分支；不直接在 `main` 持续保留测试触发器。
4. TC-036、TC-195、TC-354、TC-535 均禁止保存 Secret 明文；日志先脱敏后才可落盘。
5. TC-387 至 TC-391 不得仅凭文件名判定 PASS，必须验证 Excel 所说的触发或构建行为。
6. TC-194、TC-535 如遇 `vars.*` 不受支持，应保存解析/运行证据，并以 Excel 预期判定差异。

### 4.1 敏感值与优先级的安全断言约定

TC-195、TC-535 不采用 Excel 示例中的直接 `echo ${{ secrets.DUP }}`，因为该示例会把 Secret 交给日志掩码机制，无法安全地区分项目级值、组织级值和错误值。等价的安全实现是在 Runner 内完成字符串比较，只输出固定布尔文本。

```sh
if [ "$RESOLVED_SECRET" = "$EXPECTED_PROJECT_SECRET" ]; then
  echo "project_secret_selected=true"
else
  echo "project_secret_selected=false"
  exit 1
fi
```

`EXPECTED_PROJECT_SECRET` 也必须从安全的项目级注入方式取得，不能写入 YAML、记录或本地证据。组织级和项目级测试值必须不同、一次性且不含生产凭据。

TC-194 的值是非敏感测试变量，允许使用 Excel 示例的 `run: echo ${{ vars.DUP }}` 输出 `project_value`。TC-535 中 `vars.DUP` 可以输出固定测试值，但 Secret 只允许通过上述布尔比较输出。

### 4.2 系统变量、容器和不安全命令的精确判定

1. TC-220 的 Excel 示例为 `echo $ATOMGIT_ACTIONS_ALLOW_UNSECURE_COMMANDS`，默认期望明确为 `false`。空值、`true`、其他字符串或变量缺失均为 `FAIL`，除非执行前确认测试环境主动覆盖了该系统变量，此时为 `BLOCKED`。
2. TC-273 使用固定公开镜像，例如 `alpine:3.20`。Job 内必须成功执行 `test -f /etc/alpine-release` 并输出固定前缀 `container_os=alpine`；仅 YAML 接受 `container:` 而未创建容器 Job 不能判定 PASS。
3. TC-355 的 `set-env` 探针不得引用 Secret、Token、路径或外部资源。若平台以解析阶段拒绝命令、运行时拒绝命令，或后续 Step 未获得 `TC355_PROBE=allowed`，均与“默认 false 禁止 set-env”一致；若后续 Step 获得该值则为 FAIL。

## 5. 结果判定与本地证据

- `PASS`：已完成 Excel 所述的实际行为断言，且存在可复核证据。
- `FAIL`：平台行为与 Excel 预期相反。
- `PARTIAL`：步骤运行但日志/UI 等关键证据不可取得。
- `BLOCKED`：必要的组织资源、Docker、MR、Tag/Release、Scheduler 或权限不存在。
- `SKIP`：平台明确不支持，且无法进行有意义的实际行为验证。

每个用例的本地证据目录为 `evidence/TC-<编号>/`，保存 `run.json`、`job.json`、已脱敏 `log.txt`（如可得）和 `notes.md`。所有文件先保留在本地，全部 TC 完成后再统一提交。

## 6. 已发现的平台问题与后续探针规则

1. GitCode 可以识别 Workflow 文件，但仍在 Job 创建前失败。API 特征为 `status=FAILED`、`jobs=[]`，且没有可下载的 Job 日志。
2. Run/Job API 和常见错误/日志端点未返回具体 YAML 校验行号或错误文本。需要精确行级原因时，必须同时保留 GitCode Web UI 上的原始失败提示。
3. S13 的初始 Workflow 包含多个 TC，无法将 Job 创建前失败归因到某一个 TC。禁止将该类失败直接作为其中每个 TC 的行为 `FAIL`；它只能作为 Workflow 配置阻塞证据。
4. 重试 S13 必须先从已成功的单 Job、单 Step、显式 Job `name` 的 `yyl-s13-probe` 开始。确认 `jobs=1` 后，每次只增加一个字段、表达式、`env` 条目、`uses` Step 或断言。第一次使 `jobs=1` 变为 `jobs=[]` 的改动才是确认的不兼容项。
5. 已成功的 `cq-s10-actions.yml` 使用 `checkout` 配置 `repository: ${{ atomgit.repositoryUrl }}` 与 `token: ${{ secrets.ATOMGIT_TOKEN }}`。对齐此写法后 S13 仍为 `jobs=[]`，因此 checkout 参数不是目前已确认的根因。
