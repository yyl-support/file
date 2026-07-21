# Karmada 调度优化与非 NPU Queue 护栏完整交接

**日期**：2026-07-21
**目的**：供后续 LLM/人员无上下文损失地接手本项目的分析、验证与上线决策

---

## 一、正式环境当前状态

### 1.1 集群与策略

| 对象 | 状态 |
| --- | --- |
| Karmada 成员集群 | `001`（Ready）、`wlcb`（Ready） |
| COP `non-npu-vcjob-node-affinity` | generation 6，在线 |
| p20 `non-npu-vcjob-prefer-001` | generation 5，`has-cpu=true`，只匹配 `001` |
| 11 条 Namespace CPP | 均使用 `dispatch/auto=true`，精确匹配 `001/wlcb` |

### 1.2 COP 注入的调度约束

```yaml
requiredDuringSchedulingIgnoredDuringExecution:
  nodeSelectorTerms:
    - matchExpressions:
        - key: accelerator/huawei-npu
          operator: DoesNotExist
preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 100
    preference:
      matchExpressions:
        - key: node.cce.io/billing-mode
          operator: In
          values: ["pre-paid"]
```

### 1.3 001 节点分类与真实候选容量

总共 21 台 pre-paid Ready 节点，受 COP 影响后：

| 分类 | 数量 | 对非 NPU Job 的含义 |
| --- | ---: | --- |
| 带 `accelerator/huawei-npu` 标签 | 11 | 被 COP `DoesNotExist` 排除 |
| 不带 NPU 标签 | 10 | 可进入候选 |
| └ amd64 普通非 NPU | ~4 | amd64 Job 主候选池 |
| └ arm64 普通非 NPU | ~4 | arm64 Job 主候选池 |
| └ amd64 带 `cache=true:NoSchedule` | 2 | 无 toleration 的普通 Job 不可用 |

### 1.4 正式业务负载画像

- 历史峰值：活动 Job 约 125，Pending Pod 约 27，post-paid 峰值约 40
- 当前活跃非 NPU Job 全部规格一致：**`31 CPU / 80Gi`**
- amd64 约 7 个、arm64 约 6 个
- 所有 Job 使用 `shared-flexible-queue`

---

## 二、环境访问

### 2.1 Kubeconfig 路径

| 环境 | 路径 |
| --- | --- |
| 正式 Karmada | `/Users/gorden/huawei/code/karmada/正式/正式贵阳karmada.yaml` |
| 正式 001 | `/Users/gorden/huawei/code/karmada/正式/0001.yaml` |
| 正式 wlcb | `/Users/gorden/huawei/code/karmada/正式/wlcb.yaml` |
| 测试 Karmada | `/Users/gorden/huawei/code/karmada/测试/karmada.yaml` |
| 测试 member1 | API `https://1.92.130.9:5443`（token 从测试 Karmada Secret 临时读取） |
| 测试 member2 | API `https://172.22.6.121:5443`（当前机器网络不通） |

### 2.2 正式环境操作约束

1. 默认只读。任何写入需单独审批。
2. 不得修改 `shared-flexible-queue`、COP、p20、HNA、Cluster Autoscaler 或 `has-cpu`/`dispatch/auto` 标签。
3. 不得删除 post-paid 节点或驱逐业务 Pod。
4. Queue 必须从 Karmada 控制面创建，成员集群侧直接 apply 会被 Karmada Work 回写覆盖。

---

## 三、自动只读采集脚本

目录：`/Users/gorden/huawei/code/karmada/正式/调度优化自动化/`

| 脚本 | 作用 | 频率 | 输出 |
| --- | --- | --- | --- |
| `60-policy-observation.sh` | 每小时完整快照 | 每小时 | `runtime/policy-observation/snapshots/<ts>/summary.json` |
| `62-policy-light-metrics.sh` | 轻量指标 | 每 10 分钟 | `runtime/policy-observation/light-metrics/metrics-YYYYMMDD.jsonl` |
| `61-policy-observation-report.sh` | 生成 3/4 天报告 | 按需 | `runtime/policy-observation/reports/*.md` |

轻量指标 JSONL 每行结构：

```json
{"timestamp": "...", "metrics": {"active_non_npu_jobs": N, "non_npu_job_phases": {...}, "nodes": {"001": {"billing_mode": {...}}, "wlcb": {...}}, "hna": {"001": {"objects": [...], "events": [...]}}}}
```

支持 Linux `systemd`（`systemd/` 目录）和 macOS `launchd`（`*.plist.example`）。使用文档：`自动采集脚本使用文档.md`。

---

## 四、Queue 护栏方案

### 4.1 设计目标

**尽可能减少批量非 NPU Job 导致的 post-paid ECS 瞬时弹出**，同时维持任务等待 SLO。不修改 HNA、Cluster Autoscaler、COP、p20 或 `shared-flexible-queue`。

### 4.2 架构

```text
Karmada 非 NPU Volcano Job
  → ClusterOverridePolicy（改写 spec.queue）
  → non-npu-guardrail-queue（capability 限制 CPU/内存）
  → Volcano Queue 判定
  → 超额 Job 进入 Inqueue
  → 不触发大规模 Autoscaler 扩容
```

### 4.3 关键设计约束

- Queue 由 Karmada 管理，走 `ClusterPropagationPolicy` 传播，不能在成员集群直接 apply
- 创建顺序：先精确 CPP → 再 Queue（避免被全局通配 Queue CPP `volcano-global-all-queue-propagation` 抢先传播）
- 不修改 `shared-flexible-queue`（它是 NPU/非 NPU 共享 Queue）
- Override 只改 `spec.queue`，不改其他字段

---

## 五、已部署的正式环境 YAML

### 5.1 专用 Queue + 传播策略

文件：`正式/调度优化自动化/2026-07-21-non-npu-guardrail-queue-001.yaml`

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: ClusterPropagationPolicy
metadata:
  name: non-npu-guardrail-queue-001
  labels:
    scheduling-optimization.karmada.io/guardrail: "true"
spec:
  resourceSelectors:
  - apiVersion: scheduling.volcano.sh/v1beta1
    kind: Queue
    name: non-npu-guardrail-queue
  placement:
    clusterAffinity:
      clusterNames: ["001"]
    replicaScheduling:
      replicaSchedulingType: Duplicated
  conflictResolution: Abort
  priority: 1000
---
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: non-npu-guardrail-queue
spec:
  parent: root
  priority: 100
  reclaimable: false
  weight: 1
  capability:
    cpu: "12"
    memory: "8Gi"
```

**当前状态**：Queue 在 Karmada 和 001 均为 Open、allocated=0。`12 CPU / 8Gi` 为测试值，正式部署前应改为 `150 CPU / 400Gi`。

### 5.2 测试环境 YAML 索引

目录：`测试/低成本验证/2026-07-21/`

| 文件 | 用途 | 状态 |
| --- | --- | --- |
| `non-npu-guardrail-queue-member1.yaml` | 测试专用 Queue + member1 传播策略 | 在线 |
| `non-npu-guardrail-canary.yaml` | 单 Job 导流验证（CPP+Override+Job） | 已完成并清理 |
| `non-npu-guardrail-baseline.yaml` | 无护栏基线组（2 个 Job，共享 Queue） | 已完成并清理 |
| `non-npu-guardrail-capability.yaml` | capability 护栏组（2 个 Job，专用 Queue） | 已完成并清理 |

---

## 六、验证结果汇总

### 6.1 测试环境

**阶段 B：Queue 传播**
- Karmada Queue 创建成功
- `ClusterPropagationPolicy` 精确定向 member1，未传播到 member2
- member1 Queue 为 Open，capability `12 CPU / 8Gi` 生效

**阶段 C：单 Job 导流**
- Karmada Override 将成员侧 Job 的 `spec.queue` 从 `shared-flexible-queue` 改为 `non-npu-guardrail-queue`
- Karmada 源 Job 的 `spec.queue` 不变（预期行为）
- ResourceBinding: `FullyAppliedSuccess`，仅 member1
- Work: `AppliedSuccessful`
- PodGroup 位于专用 Queue，Pod 正常运行并 Completed

**阶段 D/E：对照实验**

| 实验 | Queue 分配 | Job 状态 | 节点变化 | 结论 |
| --- | --- | --- | --- | --- |
| 无护栏基线 | 16 CPU/8Gi/2 pods | 2 job 同时 Running → Completed | 无新增节点 | 共享 Queue 无限制，两个 Job 同时跑 |
| capability 护栏 | 8 CPU/4Gi/1 pod | 第 1 个 Running、第 2 个 Pending/Inqueue | 无新增节点 | Queue 超额限制生效 |
| capability 护栏（第一阶段完成后） | 8 CPU/4Gi/1 pod | 第 2 个自动 Running → Completed | 无新增节点 | 释放后自动继续 |

**Queue 排队语义已验证通过**：
- 超额 Job 进入 Inqueue，PodGroup 原因：`NotEnoughResources`
- 不会变成普通 `FailedScheduling` Pending Pod
- 第一批完成后超额 Job 自动运行
- Queue allocated 正常释放

### 6.2 正式环境模拟

**单 Namespace（fbgemm-ascend，5 个 Job）**
- Override 生效，成员 Job 进入专用 Queue
- Queue allocated: `12 CPU / 3Gi / 3 pods`
- 3 个 Job 调度的 Pod 尝试拉取 `busybox:1.36` 失败（Docker Hub 不通），导致 Pod 未完成
- 已清理

**多 Namespace（fbgemm-ascend + indexsdk + mindie-llm，9 个 Job）**
- Override 对全部 9 个 Job 生效
- 专用 Queue 先承接 3 个 Job（`mindie-llm`），Queue allocated: `12 CPU / 3Gi`
- 剩余 6 个 Job 进入 Inqueue
- `fbgemm-ascend` 和 `indexsdk` 的 6 个 Job 在 Inqueue 约 5-6 分钟后，ResourceBinding 被 Karmada 清理（Event: `ScheduleBindingFailed: skip schedule deleting resourceBinding`）
- `mindie-llm` 的 3 个 Job 正常完成
- 已清理

---

## 七、关键发现与遗留问题

### 7.1 已确认

1. Queue capability 排队机制成立：超额 Job → Inqueue → 释放后自动继续
2. `NotEnoughResources` 不会立即产生等同于普通 `Insufficient cpu` 的 Pending Pod
3. Karmada Override 改写 `spec.queue` 可行，源 Job 不变
4. 测试环境 `member1` 没有 Cluster Autoscaler/HNA，无法做 ECS 扩容对照

### 7.2 待验证/修复

1. **长期 Inqueue Job 被 Karmada 清理**：`ScheduleBindingFailed: skip schedule deleting resourceBinding`。发生在 `fbgemm-ascend` 和 `indexsdk` 的 6 个 Job 上，`mindie-llm` 的 3 个未受影响。大概率不是 Queue 引起的（同类 Event 在正式环境一直存在），但正式全量上线前需要在小范围灰度中验证。

2. **正式 Queue capability 未调整**：当前 `12 CPU / 8Gi`，正式业务单个 Job 就是 `31 CPU / 80Gi`。建议值 `150 CPU / 400Gi`（可承接 4-5 个生产规格 Job 并发）。

3. **ECS 弹出是否会减少**：当前没有任何环境能直接验证 Queue 是否真的减少 Autoscaler/HNA 扩容。测试 `member1` 无 Autoscaler，正式无法做大压力对照实验。

---

## 八、线上下一步操作建议

### 阶段 A：调整 Queue capability

```bash
kubectl --kubeconfig 正式贵阳karmada.yaml patch queue non-npu-guardrail-queue --type merge -p '
spec:
  capability:
    cpu: "150"
    memory: "400Gi"
'
```

### 阶段 B：小范围灰度 Override

创建一个仅匹配单个低风险 Namespace（如 `fbgemm-ascend`）的非 NPU Job 的 Override：

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: ClusterOverridePolicy
metadata:
  name: non-npu-guardrail-fbgemm-ascend
spec:
  resourceSelectors:
  - apiVersion: batch.volcano.sh/v1alpha1
    kind: Job
    namespace: fbgemm-ascend
    labelSelector:
      matchExpressions:
      - key: huawei.com/npu
        operator: DoesNotExist
  overrideRules:
  - targetCluster:
      clusterNames: ["001"]
    overriders:
      plaintext:
      - operator: replace
        path: /spec/queue
        value: non-npu-guardrail-queue
```

### 阶段 C：观察与回滚

至少观察两个完整高峰/回收周期，采集：

- Queue allocated、PodGroup Inqueue/Running 比例
- 非 NPU Job 完成时间与基线对比
- 是否有 Inqueue Job 被 Karmada 清理
- post-paid 节点峰值和十分钟增量

回滚方式：删除 Override，Job 恢复使用 `shared-flexible-queue`。无需删除 Queue，无需修改 COP/HNA/Autoscaler。

### 阶段 D：逐步扩大

按 Namespace 逐个扩大 Override 覆盖范围，每个扩展观察至少一个完整周期后再继续。

---

## 九、远端文档索引

| 文档 | 链接 |
| --- | --- |
| 非 NPU 队列护栏验证路径 | https://github.com/yyl-support/file/blob/main/report/非NPU队列护栏验证路径_20260721.md |
| 非 NPU 任务队列与并发治理方案 | https://github.com/yyl-support/file/blob/main/report/非NPU任务队列与并发治理方案_20260721.md |
| 优化效果观测分析（24h） | https://github.com/yyl-support/file/blob/main/report/优化效果观测分析_20260721.md |
| 工具包 | https://github.com/yyl-support/file/tree/main/karmada-scheduling-policy-observer |

---

## 十、本地文件索引

### YAML 清单

| 文件 | 位置 |
| --- | --- |
| Queue + membership CPP（正式） | `正式/调度优化自动化/2026-07-21-non-npu-guardrail-queue-001.yaml` |
| 多 Namespace Override（正式，已清理） | `正式/调度优化自动化/2026-07-21-multins-queue-simulation-override.yaml` |
| 多 Namespace 模拟 Job（正式，已清理） | `正式/调度优化自动化/2026-07-21-multins-queue-simulation-jobs.yaml` |
| 测试 Queue + member1 CPP | `测试/低成本验证/2026-07-21/non-npu-guardrail-queue-member1.yaml` |
| 测试 canary（CPP + Override + Job） | `测试/低成本验证/2026-07-21/non-npu-guardrail-canary.yaml` |
| 测试基线组 | `测试/低成本验证/2026-07-21/non-npu-guardrail-baseline.yaml` |
| 测试 capability 护栏组 | `测试/低成本验证/2026-07-21/non-npu-guardrail-capability.yaml` |

### 交接文档

| 文件 | 内容 |
| --- | --- |
| `正式/调度优化自动化/工作交接-2026-07-21.md` | 脚本、Queue 验证、测试结果 |
| `正式/调度优化自动化/工作交接-2026-07-20.md` | COP/p20/Namespace 策略与效果评估 |
| `正式/调度优化自动化/自动采集脚本使用文档.md` | 采集脚本使用手册 |

### 本地快照

| 路径 | 内容 |
| --- | --- |
| `正式/调度优化自动化/runtime/policy-observation/snapshots/` | 完整快照 JSON + summary.json |
| `正式/调度优化自动化/runtime/policy-observation/light-metrics/` | 十分钟轻量指标 JSONL |
