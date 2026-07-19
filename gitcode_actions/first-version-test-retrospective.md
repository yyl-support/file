# 第一版测试复盘与第二版执行规则

## 1. 第一版的主要问题

### 1.1 将“Workflow 被识别”或“Step 打印 PASS”误当作测试通过

第一版参考的批量 Workflow 中，很多 Step 只打印 `PASS`、`SKIP` 或文档描述，没有读取平台实际值，也没有在断言失败时以非零退出码结束。此类 Step 可以证明 YAML 能被解析，但不能证明 Excel 预期成立。

改进：每个 TC 使用独立 YAML、一个明确断言和可复核的 Run/Job 证据。Shell 断言失败必须返回非零，例如 `test -n "$value"`，不能只输出 `FAIL` 文本后继续成功退出。

### 1.2 多个 TC 放在一个 Workflow，无法定位 Job 创建前失败根因

第一版 S13 Workflow 同时包含多个上下文、Secret、Action、Docker 和触发器配置。平台在 Job 创建前失败时返回 `jobs=[]`，没有任何 Job 日志，无法将失败归因到其中某一条 TC。

改进：从单 Job、单 Step、显式 Job `name` 的最小 YAML 开始。确认 API 返回 `jobs=1` 后，每次只新增一个字段、表达式或断言；首个使 `jobs=1` 变为 `jobs=[]` 的改动才可记录为不兼容项。

### 1.3 未满足 Excel 预期的完整范围

例如 TC-009 的“仅当前项目可用”和 TC-010 的“仅匹配环境可用”，第一版只验证了当前项目或匹配环境中的正向可用性；这不足以证明“仅”。TC-444 只检查 Artifact，未检查缓存。

改进：范围型用例必须同时设计正向和负向对照。没有受控对照项目、对照环境或缓存检查证据时，只能标记 `PARTIAL` 或 `BLOCKED`，不能标记 `PASS`。

### 1.4 直接输出 Secret 或依赖无法取得的日志

Secret 掩码类用例的 Excel 示例包含 `echo ${{ secrets.X }}`，但第一版 Job 日志下载 API 返回 HTTP 404。直接输出敏感值也不能安全区分组织级、项目级或错误来源。

改进：Secret 优先级用例在 Runner 内比较值，只输出固定布尔结果；掩码用例只使用一次性测试值，且日志不可读取时记录为 `PARTIAL`。本地绝不保存明文 Token 或 Secret。

### 1.5 把平台限制或历史现象直接当作 Excel 用例结论

S2 的 TC-533、TC-534 没有给出统一优先级解析入口。仅从 `env` 表、`vars` 表或失败 Step 不能推出 `env > vars` 或 `vars > ATOMGIT_*`。

改进：Excel 未提供引用语法、YAML 示例或统一解析入口时，先记录为设计阻塞，只做语法/环境探针；取得原始用例语法、官方规则或编写人确认后，才生成优先级断言 YAML。

### 1.6 Schedule 用例没有独立的计划时间和观察窗口

第一版调度验证在基础 cron 没有创建 Run 后，无法区分 Scheduler、分支、表达式、间隔和日历条件导致的结果。

改进：每个 cron 单独启用、记录 `planned_utc` 和观察终止时间，只接受事件为 `schedule` 的 Run。每次结束后删除 `on.schedule` 并确认清理；任何时刻只保留一个启用的测试 cron。

## 2. 已提交 Workflow 为什么可以创建 Job

目标仓库中近期已完成的独立 Workflow，例如 `.gitcode/workflows/tc-233.yml`、`.gitcode/workflows/tc-469.yml`，以及本次 TC-035 的 Job API，具有相同的最小可运行结构：

```yaml
name: tc-name

on:
  push:
    branches: [test-branch]

jobs:
  verify:
    name: Human readable job name
    runs-on: [ubuntu-latest, x64, small]
    steps:
      - name: Human readable step name
        run: |
          test "$VALUE" = "expected"
```

关键原因：

1. 文件放在 `.gitcode/workflows/`，并有顶层 `name` 与有效 `on` 触发器。
2. 每个 Job 显式声明 `name`；缺失时平台可在创建 Job 前失败并返回 `jobs=[]`。
3. 使用仓库中已实际完成过的 Runner 标签 `runs-on: [ubuntu-latest, x64, small]`。
4. 每个 Step 都有 `name`，且只包含一个 `run` 或一个 `uses`。
5. 单 Job 保持不超过 16 个 Step，避免平台 Job Step 数限制。
6. 触发分支与 `on.push.branches` 完全匹配，避免 Workflow 未触发和 YAML 解析失败混淆。

这些结构规则只能证明 Job 可以被创建；它们不证明批量 Workflow 中每个 TC 的业务断言正确。第二版必须保留独立断言和 API/日志证据。

## 3. 本次第二版首条验证

文件：`.gitcode/workflows/TC-035-atomgit-action.yml`。

提交：`a9ba1747286216fd49a22113ad0e72e2b60955a6`，分支：`test/yulin-tc`。

Run：`6c668207a2134da39cdf7db913a81e11`。

已确认：平台创建了一个 Job `TC-035 verify atomgit action` 和一个 `official_shell` Step，说明 YAML 已完成解析并越过第一版的 `jobs=[]` 配置失败阶段。

当前阻塞：Job 保持 `INIT`，尚无 `start_time`、执行 ID 或报错。该现象属于 Runner 调度队列或资源分配阶段，不能判定 TC-035 通过或失败。后续仅在该 Run 结束并保存 Run/Job 结果后，才上传下一条 TC。
