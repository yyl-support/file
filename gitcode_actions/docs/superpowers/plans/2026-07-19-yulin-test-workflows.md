# Yulin Test Workflow Files Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create one locally retained, independently reviewable GitCode workflow YAML for every Excel-defined S1, S2, S3, and S13 test case assigned to yulin, using the `TC-<number>-<name>.yml` convention.

**Architecture:** Treat the Excel workbook's expected result as the test oracle. First document an implementation-review decision for each TC, including prerequisites, assertion, evidence source, and cleanup. Then create a focused workflow per approved TC under its S-module directory; scheduling workflows remain disabled by default so only an explicitly selected schedule case can be enabled. Keep generated files and evidence local until all checks pass, then make one commit in the actual Git repository that contains the files.

**Tech Stack:** GitCode Actions YAML, PowerShell, Python standard library and `openpyxl` for local workbook validation, Git.

---

## File Structure

- Create: `S1/TC-008-org-secret.yml` through `S1/TC-532-empty-secret.yml` - Twelve independent Secret test workflows.
- Create: `S2/TC-533-env-overrides-vars.yml`, `S2/TC-534-vars-overrides-system-variable.yml` - Two independent variable-precedence test workflows.
- Create: `S3/TC-237-schedule-cron.yml` through `S3/TC-563-schedule-delay.yml` - Twenty-four independent, disabled-by-default schedule test workflows.
- Create: `S13/TC-035-atomgit-action.yml` through `S13/TC-535-secrets-vars-namespaces.yml` - Fifteen independent push-trigger test workflows.
- Create: `S12/README.md` - Explicit local blocker describing why S12 cannot be generated before its TC mapping is provided.
- Modify: `S1/test-plan.md`, `S2/test-plan.md`, `S3/test-plan.md`, `S13/test-plan.md` - Add pre-execution TC review tables and per-file workflow inventory.
- Modify: `S1/test-record.md`, `S2/test-record.md`, `S3/test-record.md`, `S13/test-record.md` - Link execution evidence and statuses to the individual local YAML files without changing previously observed outcomes.
- Create: `reviewed-tc-index.md` - Master local index for the 53 in-scope Excel cases, review status, file path, prerequisites, and evidence destination.
- Create: `validate-test-workflows.py` - Local structural validator for filenames, expected TC inventory, YAML parseability, job/step names, 16-step limit, and disabled schedule safeguards.

### Task 1: Establish the Excel-derived TC manifest and local S12 blocker

**Files:**
- Create: `reviewed-tc-index.md`
- Create: `S12/README.md`
- Test: local `openpyxl` inventory command against `C:\Users\Administrator\AppData\Local\Temp\2\opencode\gitcode-demo\gitcode-pipeline-test-cases.xlsx`

- [ ] **Step 1: Extract and independently verify the source TC IDs from the workbook**

Run:

```powershell
python -c "from openpyxl import load_workbook; p=r'C:\Users\Administrator\AppData\Local\Temp\2\opencode\gitcode-demo\gitcode-pipeline-test-cases.xlsx'; ws=load_workbook(p, read_only=True, data_only=True)['测试用例清单']; ids={'TC-008','TC-009','TC-010','TC-011','TC-100','TC-101','TC-102','TC-443','TC-444','TC-530','TC-531','TC-532','TC-533','TC-534','TC-237','TC-427','TC-428','TC-429','TC-430','TC-471','TC-472','TC-473','TC-474','TC-475','TC-476','TC-477','TC-478','TC-479','TC-505','TC-506','TC-507','TC-508','TC-509','TC-510','TC-511','TC-512','TC-562','TC-563','TC-035','TC-036','TC-194','TC-195','TC-220','TC-273','TC-304','TC-354','TC-355','TC-387','TC-388','TC-389','TC-390','TC-391','TC-535'}; found=[r[0] for r in ws.iter_rows(min_row=2, values_only=True) if r[0] in ids]; print(len(found)); print(','.join(sorted(found)))"
```

Expected: `53`, followed by all and only the 53 listed TC IDs.

- [ ] **Step 2: Write the reviewed-TC master index**

Create `reviewed-tc-index.md` containing one row per TC with these columns:

```markdown
| TC | S module | Excel expected result | Workflow file | Review decision | Prerequisite / evidence |
| --- | --- | --- | --- | --- | --- |
| TC-008 | S1 | Organization Secret is available to organization projects | `S1/TC-008-org-secret.yml` | Requires organization Secret; execute only when configured | Job environment plus sanitized Job log |
```

Use these review decisions consistently:

```text
S1: organization and environment Secret cases require configured resources;
    masking cases require sanitized log evidence; undefined/hyphen/empty cases test Excel behavior directly.
S2: retain vars precedence expectations from Excel; record parser/runtime support before declaring precedence.
S3: schedule cases require a real scheduler observation; schedule files must remain disabled unless selected.
S13: organization precedence, Docker, merge-request, release/tag, Secret masking, and scheduling cases require their real prerequisites.
```

- [ ] **Step 3: Write the explicit S12 blocker**

Create `S12/README.md` with:

```markdown
# S12 Test Workflow Status

No S12 workflow has been generated. The local workbook has no S-number or owner column, and the workspace did not contain an S12 plan or record. Add the authoritative S12 TC-ID mapping before creating `TC-<number>-<name>.yml` files.
```

- [ ] **Step 4: Verify the index has the expected local scope**

Run:

```powershell
$index = Get-Content -LiteralPath 'reviewed-tc-index.md' -Raw
([regex]::Matches($index, '\| TC-\d{3} \|')).Count
```

Expected: `53`.

### Task 2: Create and review the S1 Secret workflows

**Files:**
- Create: `S1/TC-008-org-secret.yml`
- Create: `S1/TC-009-project-secret.yml`
- Create: `S1/TC-010-environment-secret.yml`
- Create: `S1/TC-011-secret-log-masking.yml`
- Create: `S1/TC-100-atomgit-token-secret.yml`
- Create: `S1/TC-101-npm-token-secret.yml`
- Create: `S1/TC-102-supersecret-secret.yml`
- Create: `S1/TC-443-no-secret-echo.yml`
- Create: `S1/TC-444-no-secret-artifact.yml`
- Create: `S1/TC-530-undefined-secret.yml`
- Create: `S1/TC-531-hyphenated-secret.yml`
- Create: `S1/TC-532-empty-secret.yml`
- Modify: `S1/test-plan.md`
- Modify: `S1/test-record.md`

- [ ] **Step 1: Add the S1 TC review table before creating workflows**

Add a `## TC Review Before Execution` table to `S1/test-plan.md`. Include all 12 IDs, their Excel expectation, resource prerequisite, a single assertion, and the planned file name. Preserve the existing historical result section in `S1/test-record.md` and append only file references and future evidence placeholders.

- [ ] **Step 2: Create each minimal S1 workflow**

Use this structural template, replacing `<TC>`, `<slug>`, `<secret_expression>`, and the assertion for the reviewed case:

```yaml
name: TC-<TC> <slug>

on:
  workflow_dispatch:

jobs:
  verify:
    name: TC-<TC> verify
    runs-on: ubuntu-latest
    env:
      TEST_VALUE: ${{ <secret_expression> }}
    steps:
      - name: TC-<TC> assert expected behavior
        run: |
          test -n "$TEST_VALUE"
```

For TC-011, TC-100, TC-101, TC-102, and TC-354-style masking checks, print only an entire disposable test value and record that console evidence must be sanitized. For TC-443 and TC-444, never write a Secret to output or an artifact; assert that the workflow only handles fixed non-secret content. For TC-530, TC-531, and TC-532, use the exact Excel expectation as the assertion target and preserve platform rejection as a test result, not a generator error.

- [ ] **Step 3: Verify S1 files**

Run:

```powershell
Get-ChildItem -LiteralPath 'S1' -Filter 'TC-*.yml' | Measure-Object | Select-Object -ExpandProperty Count
```

Expected: `12`.

### Task 3: Create and review the S2 variable-precedence workflows

**Files:**
- Create: `S2/TC-533-env-overrides-vars.yml`
- Create: `S2/TC-534-vars-overrides-system-variable.yml`
- Modify: `S2/test-plan.md`
- Modify: `S2/test-record.md`

- [ ] **Step 1: Record the two Excel precedence oracles in `S2/test-plan.md`**

Add one row for TC-533 with expected `env > vars`, and one for TC-534 with expected `vars > ATOMGIT_*`. For both, state that parser acceptance is a pre-execution observation only; a PASS requires observing the asserted resolved value.

- [ ] **Step 2: Create the two isolated workflows**

Use named jobs and named steps. TC-533 must set `SAME_NAME` in `env` and separately resolve `vars.SAME_NAME`. TC-534 must set the same `ATOMGIT_*` name in `env` and separately resolve `vars.<name>`. Each workflow must fail its shell assertion when the Excel precedence result is not observed.

- [ ] **Step 3: Verify scope and preserve prior evidence**

Run:

```powershell
Get-ChildItem -LiteralPath 'S2' -Filter 'TC-*.yml' | Select-Object -ExpandProperty Name
```

Expected: exactly `TC-533-env-overrides-vars.yml` and `TC-534-vars-overrides-system-variable.yml`.

Append file paths to `S2/test-record.md`; do not replace the recorded run and Job identifiers.

### Task 4: Create and review the S3 schedule workflows

**Files:**
- Create: `S3/TC-237-schedule-cron.yml`
- Create: `S3/TC-427-cron-utc-timezone.yml`
- Create: `S3/TC-428-schedule-default-branch.yml`
- Create: `S3/TC-429-schedule-minimum-interval.yml`
- Create: `S3/TC-430-schedule-dispatch-delay.yml`
- Create: `S3/TC-471-cron-wildcard.yml`
- Create: `S3/TC-472-cron-list.yml`
- Create: `S3/TC-473-cron-range.yml`
- Create: `S3/TC-474-cron-step.yml`
- Create: `S3/TC-475-cron-minute-boundary.yml`
- Create: `S3/TC-476-cron-hour-boundary.yml`
- Create: `S3/TC-477-cron-day-boundary.yml`
- Create: `S3/TC-478-cron-month-boundary.yml`
- Create: `S3/TC-479-cron-weekday-boundary.yml`
- Create: `S3/TC-505-cron-minute-list.yml`
- Create: `S3/TC-506-cron-minute-range.yml`
- Create: `S3/TC-507-cron-minute-step.yml`
- Create: `S3/TC-508-cron-question-mark.yml`
- Create: `S3/TC-509-cron-last-day.yml`
- Create: `S3/TC-510-cron-nearest-weekday.yml`
- Create: `S3/TC-511-cron-nth-weekday.yml`
- Create: `S3/TC-512-cron-range-step.yml`
- Create: `S3/TC-562-schedule-nondefault-branch.yml`
- Create: `S3/TC-563-schedule-delay.yml`
- Modify: `S3/test-plan.md`
- Modify: `S3/test-record.md`

- [ ] **Step 1: Add a per-TC schedule review table**

For each of the 24 files, document the Excel cron expectation, exact cron field under test, planned UTC trigger, observation window, and whether the result requires run creation or parser/configuration evidence.

- [ ] **Step 2: Create disabled-by-default schedules**

Every S3 file must use `workflow_dispatch` as its committed trigger and carry the target cron as a comment, for example:

```yaml
name: TC-471 cron wildcard

# Candidate schedule under test: "* * * * *". Add under `on.schedule` only for a single controlled execution.
on:
  workflow_dispatch:

jobs:
  verify:
    name: TC-471 verify
    runs-on: ubuntu-latest
    steps:
      - name: TC-471 record UTC time
        run: date -u +%Y-%m-%dT%H:%M:%SZ
```

Never commit more than one enabled `on.schedule` test file. When executing a case, add its reviewed cron temporarily, capture run and Job timestamps, remove the `schedule` block, then confirm the removal before moving to the next case.

- [ ] **Step 3: Verify S3 inventory and schedule safety**

Run:

```powershell
(Get-ChildItem -LiteralPath 'S3' -Filter 'TC-*.yml').Count
```

Expected: `24`.

Run:

```powershell
Select-String -LiteralPath (Get-ChildItem -LiteralPath 'S3' -Filter 'TC-*.yml').FullName -Pattern '^\s{2}schedule:'
```

Expected: no output.

### Task 5: Create and review the S13 push verification workflows

**Files:**
- Create: `S13/TC-035-atomgit-action.yml`
- Create: `S13/TC-036-atomgit-token.yml`
- Create: `S13/TC-194-project-vars-over-org-vars.yml`
- Create: `S13/TC-195-project-secret-over-org-secret.yml`
- Create: `S13/TC-220-unsecure-commands-variable.yml`
- Create: `S13/TC-273-job-container.yml`
- Create: `S13/TC-304-checkout-action.yml`
- Create: `S13/TC-354-secret-log-masking.yml`
- Create: `S13/TC-355-unsecure-command-setting.yml`
- Create: `S13/TC-387-ci-workflow-name.yml`
- Create: `S13/TC-388-pr-check-workflow-name.yml`
- Create: `S13/TC-389-release-workflow-name.yml`
- Create: `S13/TC-390-docker-build-workflow-name.yml`
- Create: `S13/TC-391-nightly-workflow-name.yml`
- Create: `S13/TC-535-secrets-vars-namespaces.yml`
- Modify: `S13/test-plan.md`
- Modify: `S13/test-record.md`

- [ ] **Step 1: Document execution prerequisites before workflow creation**

Add a 15-row review table to `S13/test-plan.md`. Mark actual prerequisites instead of simulating them: organization variables/secrets for TC-194/195, Docker/registry for TC-273/390, merge request for TC-388, tag/release for TC-389, scheduler for TC-391, and safe sanitised logs for TC-036/354.

- [ ] **Step 2: Create independently triggered workflow files**

Use `workflow_dispatch` for all committed S13 workflows. Add a `push` trigger temporarily only while executing a controlled test branch case. TC-304 must have a named `uses: checkout` step:

```yaml
- name: TC-304 checkout source
  uses: checkout
```

Use a named job and named steps in every file. Treat filename-oriented TCs 387-391 as behavior tests: add only the matching trigger and resource conditions during controlled execution, not unconditional success output.

- [ ] **Step 3: Verify S13 file count and preserve `PENDING` until execution begins**

Run:

```powershell
(Get-ChildItem -LiteralPath 'S13' -Filter 'TC-*.yml').Count
```

Expected: `15`.

Keep `S13/test-record.md` status as `PENDING` unless one of these workflows has actually run and produced local evidence.

### Task 6: Add local validation and run it against all workflows

**Files:**
- Create: `validate-test-workflows.py`
- Test: `validate-test-workflows.py`

- [ ] **Step 1: Write the failing local validation checks**

Create a test fixture or temporarily use a deliberately bad filename to establish that the validator rejects files not matching this expression:

```python
FILENAME = re.compile(r"^TC-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.yml$")
```

The validator must also reject an S3 file with an active `on.schedule` block and any YAML with a job missing `name`, a step missing `name`, or more than 16 steps in a job.

- [ ] **Step 2: Implement the validator**

Implement `validate-test-workflows.py` to:

```text
1. Expect exactly 12 S1, 2 S2, 24 S3, and 15 S13 `TC-*.yml` files.
2. Validate each basename against `TC-<three digits>-<lowercase-kebab-name>.yml`.
3. Parse YAML using an installed safe YAML parser; if none is installed, stop with an actionable dependency message rather than silently skipping parsing.
4. Ensure every job and every step declares a non-empty `name`.
5. Ensure no job has more than 16 steps.
6. Ensure committed S3 files contain no active schedule trigger.
7. Print each failing path and return a non-zero exit code on any error.
```

- [ ] **Step 3: Run the local validation**

Run:

```powershell
python validate-test-workflows.py
```

Expected: exit code `0` and a summary reporting `53 workflow files validated`.

### Task 7: Preserve results locally and make one final commit only in the target repository

**Files:**
- Modify: `S1/test-record.md`
- Modify: `S2/test-record.md`
- Modify: `S3/test-record.md`
- Modify: `S13/test-record.md`
- Create when runs occur: `evidence/TC-<number>/run.json`, `evidence/TC-<number>/job.json`, and sanitized log files when available

- [ ] **Step 1: Store run evidence locally per TC**

For each executed TC, create `evidence/TC-<number>/` and preserve:

```text
run.json       Actions run response
job.json       Actions Job response
log.txt        Only if reviewed and sanitized; never save raw sensitive output
notes.md       Planned time, observed time, status, and limitation rationale
```

- [ ] **Step 2: Update records only from actual evidence**

For each TC, set `PASS`, `FAIL`, `PARTIAL`, `BLOCKED`, or `SKIP` only after the expected behavior, available evidence, and prerequisite outcome have been recorded locally. Do not convert unexecuted S13 cases or scheduler-dependent S3 cases into PASS.

- [ ] **Step 3: Confirm no intermediate commit exists and identify the actual target repository**

Run from the repository containing the `S1/`, `S2/`, `S3/`, `S12/`, and `S13/` directories:

```powershell
git status --short
```

Expected: all intended changes visible in one working tree and no task-specific intermediate commit.

- [ ] **Step 4: Run final validation before the one commit**

Run:

```powershell
python validate-test-workflows.py
git diff --check
git status --short
```

Expected: validator succeeds, `git diff --check` reports no whitespace errors, and status lists only intended files.

- [ ] **Step 5: Make the single final commit only after every local result is ready**

Run:

```powershell
git add S1 S2 S3 S12 S13 reviewed-tc-index.md validate-test-workflows.py evidence
```

Expected: one new commit containing all reviewed YAML files, plans, records, local evidence, index, S12 blocker, and validator. Do not push unless separately requested.

## Plan Self-Review

- Source coverage: Tasks 2-5 cover all 53 Excel-mapped S1, S2, S3, and S13 cases; Task 1 explicitly retains S12 as blocked pending an authoritative mapping.
- Oracle: every review table and assertion uses the Excel expected result rather than silently changing expectations to current platform behavior.
- Safety: S3 schedules are disabled in committed local files, Secret logs are sanitized, and generated workflows are not run until per-TC review is complete.
- Validation: Task 6 checks naming, inventory, job/step names, step count, YAML parsing, and schedule safety before any final commit.
