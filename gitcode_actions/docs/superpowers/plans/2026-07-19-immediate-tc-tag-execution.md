# Immediate TC Tag Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the immediately executable yulin cases one at a time through isolated Git tags, avoiding the congested Push-event queue.

**Architecture:** Each TC has one `.gitcode/workflows/TC-<number>-<name>.yml` file on `main`, with an exact one-off tag pattern and one named Job. The test tag triggers only that workflow; after the Run reaches a terminal state, save the Run/Job JSON locally, update the local record, then move to the next TC.

**Tech Stack:** GitCode Actions YAML, Git tags, GitCode v8 Actions API, PowerShell.

---

### Task 1: TC-220 System Command Flag

**Files:**
- Create: `D:\user\data\test-0719\S13\TC-220-allow-unsecure-commands.yml`
- Modify in target repo: `.gitcode/workflows/TC-220-allow-unsecure-commands.yml`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-220\run.json`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-220\job.json`
- Modify: `D:\user\data\test-0719\S13\test-record.md`

- [ ] **Step 1: Write the failing assertion first**

The only assertion must fail unless the system variable is exactly `false`:

```sh
test "$ATOMGIT_ACTIONS_ALLOW_UNSECURE_COMMANDS" = "false"
```

- [ ] **Step 2: Create the minimal isolated workflow**

```yaml
name: TC-220 allow unsecure commands

on:
  push:
    tags: [yulin-tc-220-*]

jobs:
  verify:
    name: TC-220 verify command flag
    runs-on: [ubuntu-latest, x64, small]
    steps:
      - name: TC-220 assert default false
        run: |
          test "$ATOMGIT_ACTIONS_ALLOW_UNSECURE_COMMANDS" = "false"
          printf 'allow_unsecure_commands=false\n'
```

- [ ] **Step 3: Validate before uploading**

Run:

```powershell
git diff --check
```

Expected: exit code `0`.

- [ ] **Step 4: Commit and push the workflow to `main`**

Run:

```powershell
git add .gitcode/workflows/TC-220-allow-unsecure-commands.yml
git push origin HEAD:main
```

- [ ] **Step 5: Create exactly one execution tag**

Run:

```powershell
git tag yulin-tc-220-1
```

- [ ] **Step 6: Save terminal evidence before proceeding**

Use the Actions API to locate the Run with `workflow_name=TC-220 allow unsecure commands`, `event=CreateTag`, and tag SHA. GitCode reports a matching `on.push.tags` trigger as `CreateTag`. Save the full run response to `evidence/TC-220/run.json` and Job response to `evidence/TC-220/job.json`.

Expected PASS: Run, Job, and sole Step are `COMPLETED`, and the Step succeeds. Any value other than `false` is FAIL.

### Task 2: TC-355 Insecure set-env Command

**Files:**
- Create: `D:\user\data\test-0719\S13\TC-355-unsecure-command-setting.yml`
- Modify in target repo: `.gitcode/workflows/TC-355-unsecure-command-setting.yml`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-355\run.json`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-355\job.json`
- Modify: `D:\user\data\test-0719\S13\test-record.md`

- [ ] **Step 1: Write the failing propagation assertion**

The second Step must fail if the deprecated command makes its probe variable available:

```sh
test "${TC355_PROBE:-}" != "allowed"
```

- [ ] **Step 2: Create the isolated workflow**

```yaml
name: TC-355 unsecure command setting

on:
  push:
    tags: [yulin-tc-355-*]

jobs:
  verify:
    name: TC-355 verify unsecure command setting
    runs-on: [ubuntu-latest, x64, small]
    steps:
      - name: TC-355 invoke deprecated set env probe
        run: |
          test "$ATOMGIT_ACTIONS_ALLOW_UNSECURE_COMMANDS" = "false"
          echo "::set-env name=TC355_PROBE::allowed"
      - name: TC-355 assert probe was not propagated
        run: |
          test "${TC355_PROBE:-}" != "allowed"
          printf 'set_env_blocked=true\n'
```

- [ ] **Step 3: Commit, push to `main`, then create `yulin-tc-355-1`**

Run:

```powershell
git add .gitcode/workflows/TC-355-unsecure-command-setting.yml
git push origin HEAD:main
```

- [ ] **Step 4: Preserve evidence and update status**

Save matching CreateTag Run/Job API responses under `evidence/TC-355/`. A parser/runtime rejection of the deprecated command, or a completed second Step where `TC355_PROBE` is absent, is PASS. A propagated `TC355_PROBE=allowed` is FAIL.

### Task 3: TC-304 Checkout Action

**Files:**
- Create: `D:\user\data\test-0719\S13\TC-304-checkout-action.yml`
- Modify in target repo: `.gitcode/workflows/TC-304-checkout-action.yml`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-304\run.json`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-304\job.json`
- Modify: `D:\user\data\test-0719\S13\test-record.md`

- [ ] **Step 1: Write the post-checkout failing assertion**

```sh
test -f .gitcode/workflows/TC-304-checkout-action.yml
```

- [ ] **Step 2: Create the isolated workflow**

```yaml
name: TC-304 checkout action

on:
  push:
    tags: [yulin-tc-304-*]

jobs:
  verify:
    name: TC-304 verify checkout action
    runs-on: [ubuntu-latest, x64, small]
    steps:
      - name: TC-304 checkout source
        uses: checkout
      - name: TC-304 assert repository checkout
        run: |
          test -f .gitcode/workflows/TC-304-checkout-action.yml
          printf 'checkout_file_present=true\n'
```

- [ ] **Step 3: Commit, push, tag, and retain terminal API evidence**

Run:

```powershell
git add .gitcode/workflows/TC-304-checkout-action.yml
git push origin HEAD:main
```

Save the matching terminal Run/Job responses in `evidence/TC-304/`. PASS requires the named checkout Step and the repository-file assertion Step both complete.

### Task 4: TC-273 Job Container

**Files:**
- Create: `D:\user\data\test-0719\S13\TC-273-job-container.yml`
- Modify in target repo: `.gitcode/workflows/TC-273-job-container.yml`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-273\run.json`
- Create after execution: `D:\user\data\test-0719\S13\evidence\TC-273\job.json`
- Modify: `D:\user\data\test-0719\S13\test-record.md`

- [ ] **Step 1: Write the container-specific failing assertion**

```sh
test -f /etc/alpine-release
```

- [ ] **Step 2: Create the isolated workflow**

```yaml
name: TC-273 job container

on:
  push:
    tags: [yulin-tc-273-*]

jobs:
  verify:
    name: TC-273 verify custom container
    runs-on: [ubuntu-latest, x64, small]
    container: alpine:3.20
    steps:
      - name: TC-273 assert alpine container
        run: |
          test -f /etc/alpine-release
          printf 'container_os=alpine\n'
```

- [ ] **Step 3: Commit, push, tag, and retain terminal API evidence**

Run:

```powershell
git add .gitcode/workflows/TC-273-job-container.yml
git push origin HEAD:main
```

Save terminal Run/Job responses in `evidence/TC-273/`. PASS requires a completed Job whose API resource contains the configured container and whose Step completes. An unavailable container runner/image is BLOCKED, not PASS.

### Task 5: TC-530 Undefined Secret

**Files:**
- Create: `D:\user\data\test-0719\S1\TC-530-undefined-secret.yml`
- Modify in target repo: `.gitcode/workflows/TC-530-undefined-secret.yml`
- Create after execution: `D:\user\data\test-0719\S1\evidence\TC-530\run.json`
- Create after execution: `D:\user\data\test-0719\S1\evidence\TC-530\job.json`
- Modify: `D:\user\data\test-0719\S1\test-record.md`

- [ ] **Step 1: Write the empty-value failing assertion**

```sh
test -z "$UNDEFINED_SECRET"
```

- [ ] **Step 2: Create the isolated workflow**

```yaml
name: TC-530 undefined secret

on:
  push:
    tags: [yulin-tc-530-*]

jobs:
  verify:
    name: TC-530 verify undefined secret
    runs-on: [ubuntu-latest, x64, small]
    env:
      UNDEFINED_SECRET: ${{ secrets.YULIN_TC530_NOT_DEFINED }}
    steps:
      - name: TC-530 assert undefined secret is empty
        run: |
          test -z "$UNDEFINED_SECRET"
          printf 'undefined_secret_empty=true\n'
```

- [ ] **Step 3: Commit, push, tag, and retain terminal API evidence**

Run:

```powershell
git add .gitcode/workflows/TC-530-undefined-secret.yml
git push origin HEAD:main
```

Save terminal Run/Job responses in `evidence/TC-530/`. PASS requires a completed Job and empty-value assertion success. A parser error or non-empty unexpected value is FAIL.

### Task 6: Local Static Reviews

**Files:**
- Create: `D:\user\data\test-0719\S1\evidence\TC-443\notes.md`
- Create: `D:\user\data\test-0719\S1\evidence\TC-444\notes.md`
- Modify: `D:\user\data\test-0719\S1\test-record.md`

- [ ] **Step 1: Review TC-443 dangerous output paths**

Run a static scan across all yulin TC YAML files for direct Secret output and record every match:

```powershell
Select-String -Path '.gitcode/workflows/TC-*.yml' -Pattern 'echo.*secrets\.|echo.*\$\{\{\s*secrets|toJson\(secrets' -CaseSensitive:$false
```

PASS requires no match in yulin workflows and a manual review that Secret values are only used in Runner comparisons or controlled full-value masking checks.

- [ ] **Step 2: Review TC-444 Artifact/cache paths**

Run:

```powershell
Select-String -Path '.gitcode/workflows/TC-*.yml' -Pattern 'artifact|cache|secrets\.' -CaseSensitive:$false
```

PASS requires no Secret expression in a file-write, upload, cache key, or cache path context. Record the reviewed files and matches in `evidence/TC-444/notes.md`.

## Plan Self-Review

- Scope coverage: Covers the agreed immediate sequence TC-220, TC-355, TC-304, TC-273, TC-530, then local static reviews TC-443 and TC-444.
- Isolation: Every dynamic TC has a distinct exact Tag prefix and unique Tag. No Push trigger is added.
- Evidence: Every dynamic case requires terminal Run and Job API evidence before the following case begins.
- Safety: No Secret is printed, static reviews explicitly inspect output and persistence paths, and test tags carry no Secret data.
