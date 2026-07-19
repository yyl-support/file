# 下一轮优化测试清单

## 1. Secret 日志掩码真实验证

目标：验证 GitCode 是否会将完整 Secret 输出替换为 `***`。本轮不再仅输出 `PARTIAL` 提示；在页面手动运行后，人工查看 Job 日志确认掩码结果。

覆盖范围：

| Session | TC | Secret 来源 | Excel 预期 |
| --- | --- | --- | --- |
| S1 | TC-011 | 一次性 `MASK_TEST_SECRET` 或 `SECRET_PROJ` | 完整 Secret 输出显示为 `***` |
| S1 | TC-100 | `secrets.ATOMGIT_TOKEN` | 输出显示为 `***` |
| S1 | TC-101 | `secrets.NPM_TOKEN` | 输出显示为 `***` |
| S1 | TC-102 | `secrets.SUPERSECRET` | 输出显示为 `***` |
| S13 | TC-036 | `atomgit.token` 或 `secrets.ATOMGIT_TOKEN` | 返回 Token 且日志受保护 |
| S13 | TC-354 | 一次性 `MASK_TEST_SECRET` | 日志替换为 `***` |

### 1.1 Workflow 固定模式

每个掩码 TC 使用独立命名环境变量，先断言已注入非空，再输出完整值：

```yaml
env:
  MASK_CHECK: ${{ secrets.MASK_TEST_SECRET }}

steps:
  - name: TC-000 verify secret log masking
    if: ${{ always() }}
    run: |
      test -n "$MASK_CHECK"
      echo "MASK_CHECK=$MASK_CHECK"
```

`TC-000` 在实际 Workflow 中替换为对应 TC 编号。使用 `env` 注入可将“Secret 是否可用”和“日志是否掩码”拆开验证，避免直接在脚本文本中嵌入 Secret 表达式造成解析层与日志层混淆。

### 1.2 页面验证标准

手动运行后，在 GitCode 页面打开对应 Step 日志：

| 观察结果 | 结论 |
| --- | --- |
| `MASK_CHECK=***`，且非空断言成功 | PASS |
| 输出真实 Secret 明文 | FAIL，立即停止后续同类输出并轮换该一次性 Secret |
| Secret 为空，非空断言失败 | FAIL 或 BLOCKED，取决于是否缺少配置资源 |
| Step 已运行但页面日志不可读取 | PARTIAL |

### 1.3 安全限制

1. 只能使用一次性、专门创建的测试 Secret；禁止输出生产凭据、个人 Token 或可复用 Token。
2. 禁止拆分、编码、拼接、截取或打印 Secret 片段；只输出完整值，以验证平台的标准掩码能力。
3. 禁止把 Secret 写入 Artifact、缓存、文件、环境诊断附件、本地 `notes.md`、截图或提交记录。
4. 报告只记录“页面显示为 `***`”或“显示为明文/无法读取”，不得记录实际值。
5. 若发生明文泄露，立即删除/轮换该测试 Secret，并将该 TC 记录为 FAIL 和安全问题。

### 1.4 本轮前置动作

1. 在项目设置中创建或确认 `MASK_TEST_SECRET` 为一次性测试值。
2. 更新 `yyl-session1-secrets.yml` 与 `yyl-session13-workflows.yml` 的上述六个 TC Step。
3. 保留 `if: ${{ always() }}`，确保某一条掩码测试失败不会阻断同 Session 后续 TC。
4. 从 Actions 页面手动运行对应 Session Workflow。
5. 页面确认日志后，在 `session-test-coverage-report.md` 和各 Session `test-record.md` 更新状态与结论。

## 2. S2 Vars 优先级真实验证

目标：通过“基线 Job + 覆盖 Job”验证 Shell 中同名变量的最终解析值，而不是只读取单独的 `${{ env.* }}` 或 `${{ vars.* }}` 上下文。每个 Job 必须独立，避免 Job 级 `env` 对基线结果造成污染。

### 2.1 前置配置

在 GitCode 项目 Variables 中设置以下非敏感测试值：

```text
SAME_NAME=vars_value
ATOMGIT_SHA=vars_value
```

不要在任何 TC-534 Job 的 YAML `env` 中设置 `ATOMGIT_SHA`。否则引入第三个来源，无法判定 `vars` 与系统变量的优先级。

### 2.2 TC-533 验证 `env > vars`

需要两个独立 Job：

```yaml
tc_533_vars_baseline:
  name: TC-533 vars baseline
  runs-on: [ubuntu-latest, x64, small]
  steps:
    - name: TC-533 verify vars reaches shell
      if: ${{ always() }}
      run: |
        echo "shell_same_name=${SAME_NAME:-UNSET}"
        echo "expression_vars_same_name=${{ vars.SAME_NAME }}"
        test "$SAME_NAME" = "vars_value"

tc_533_env_override:
  name: TC-533 env overrides vars
  runs-on: [ubuntu-latest, x64, small]
  env:
    SAME_NAME: env_value
  steps:
    - name: TC-533 verify env wins
      if: ${{ always() }}
      run: |
        echo "shell_same_name=${SAME_NAME:-UNSET}"
        echo "expression_env_same_name=${{ env.SAME_NAME }}"
        echo "expression_vars_same_name=${{ vars.SAME_NAME }}"
        test "$SAME_NAME" = "env_value"
```

判定：基线 Job 的 `$SAME_NAME` 必须为 `vars_value`，覆盖 Job 的 `$SAME_NAME` 必须为 `env_value`，两者成立才为 PASS。若 `${{ vars.SAME_NAME }}` 解析错误，记录 FAIL；若 vars 值不能进入 Shell，记录 PARTIAL 或平台不支持证据，不得声称优先级通过。

### 2.3 TC-534 验证 `vars > ATOMGIT_*`

同样需要两个独立 Job：

```yaml
tc_534_system_baseline:
  name: TC-534 system baseline
  runs-on: [ubuntu-latest, x64, small]
  steps:
    - name: TC-534 observe system value
      if: ${{ always() }}
      run: |
        echo "shell_atomgit_sha=${ATOMGIT_SHA:-UNSET}"
        test -n "$ATOMGIT_SHA"

tc_534_vars_override:
  name: TC-534 vars override system
  runs-on: [ubuntu-latest, x64, small]
  steps:
    - name: TC-534 verify vars wins
      if: ${{ always() }}
      run: |
        echo "shell_atomgit_sha=${ATOMGIT_SHA:-UNSET}"
        echo "expression_vars_atomgit_sha=${{ vars.ATOMGIT_SHA }}"
        test "${{ vars.ATOMGIT_SHA }}" = "vars_value"
        test "$ATOMGIT_SHA" = "vars_value"
```

判定：基线 Job 的 `$ATOMGIT_SHA` 必须非空，覆盖 Job 的 `${{ vars.ATOMGIT_SHA }}` 和 `$ATOMGIT_SHA` 都必须为 `vars_value`，才为 PASS。若 `${{ vars.ATOMGIT_SHA }}` 可读取但 Shell 中 `$ATOMGIT_SHA` 仍为系统 SHA，记录 FAIL。若基线系统变量为空，记录 BLOCKED。

### 2.4 页面取证与安全限制

1. 从 Actions 页面手动运行更新后的 `yyl-session2-vars.yml`。
2. 在页面日志记录 `shell_same_name`、`expression_vars_same_name`、`shell_atomgit_sha` 和 `expression_vars_atomgit_sha` 的非敏感测试值。
3. Job 日志下载 API 返回 HTTP 404 时，页面日志为优先证据；本地报告只保存变量名称、预期值、实际值和结论。
4. TC-533、TC-534 的任一 Job 失败不应阻断其余 S2 Job；所有步骤保留 `if: ${{ always() }}`。
