# Karmada 调度优化与 Queue 护栏完整交接（2026-07-21 终版）

**日期**：2026-07-21
**目的**：完整记录调度优化实施过程、Queue 护栏策略演变、验证结果、遇到的问题与决策边界

---

## 一、背景与目标演变

### 1.1 调度优化（已上线，已验证）

上线对象：

- COP `non-npu-vcjob-node-affinity` generation 6
- p20 `non-npu-vcjob-prefer-001` generation 5
- 11 条 Namespace CPP 切换为 `dispatch/auto=true`

结论：策略字段无漂移，非 NPU Pod 优先落在 pre-paid 节点。但瞬时 80+ Job 高峰仍会耗尽 pre-paid 容量，触发 post-paid ECS 大规模弹出（峰值 40 台）。

### 1.2 唯一业务目标

> 尽可能减少批量非 NPU Job 导致的 post-paid ECS 瞬时弹出，同时维持任务等待 SLO（约 10 分钟）。

---

## 二、Queue 护栏策略设计

### 2.1 核心思路

```text
非 NPU Volcano Job
  → Karmada ClusterOverridePolicy（改写 spec.queue）
  → non-npu-guardrail-queue（capability 限制 CPU/内存）
  → 超额 Job 进入 Volcano Inqueue 状态
  → 减少瞬时可调度需求，避免 Autoscaler 大规模扩容
```

### 2.2 关键设计约束

- 不修改 COP、p20、HNA、Cluster Autoscaler、Cluster 标签
- 不修改 `shared-flexible-queue`（NPU/非 NPU 共享 Queue）
- Queue 从 Karmada 控制面创建并传播，不能在成员集群直接 apply
- 创建顺序：先精确 CPP → 再 Queue（避免被全局通配 Queue CPP 抢先传播）
- Override 只改 `spec.queue`，不改其他字段

### 2.3 正式 001 节点容量基线

21 台 pre-paid Ready 节点，受 COP 的 `accelerator/huawei-npu DoesNotExist` 影响后：

| 分类 | 数量 | 含义 |
| --- | ---: | --- |
| 带 NPU 标签（被 COP 排除） | 11 | 不可用 |
| 非 NPU 候选 | 10 | 可用 |
| └ amd64 普通非 NPU | ~4 | amd64 Job 候选 |
| └ arm64 普通非 NPU | ~4 | arm64 Job 候选 |
| └ amd64 带 `cache=true:NoSchedule` | 2 | 无 toleration 不可用 |

### 2.4 生产 Job 规格

高峰期全部非 NPU Job 规格一致：**31 CPU / 80Gi**，amd64 与 arm64 各约一半。

---

## 三、正式环境已部署资源

### 3.1 专用 Queue

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: Queue
metadata:
  name: non-npu-guardrail-queue
  labels:
    scheduling-optimization.karmada.io/guardrail: "true"
spec:
  parent: root
  priority: 100
  reclaimable: false
  weight: 1
  capability:
    cpu: "150"
    memory: "400Gi"
```

**说明**：capability 值经多次调整，当前最终定格为 `150 CPU / 400Gi`，允许约 4-5 个 `31 CPU / 80Gi` Job 并发。曾经短暂调为 `600/1600Gi`（非本次操作），已记录为外部变更。

### 3.2 Queue 传播策略

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: ClusterPropagationPolicy
metadata:
  name: non-npu-guardrail-queue-001
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
```

### 3.3 argo 灰度 Override（已回滚删除）

```yaml
apiVersion: policy.karmada.io/v1alpha1
kind: ClusterOverridePolicy
metadata:
  name: non-npu-guardrail-argo-gray
spec:
  resourceSelectors:
  - apiVersion: batch.volcano.sh/v1alpha1
    kind: Job
    namespace: argo
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

**回滚原因**：argo 任务在 Queue 中排队时间超过 40 分钟，远超 10 分钟 SLO。等待原因是单 Queue 共享 amd64+arm64 架构但各自候选节点池独立，且单个 argo 任务 `31 CPU / 80Gi` 规格下 `150 CPU / 400Gi` cap 只能同时放 4-5 个。

### 3.4 YAML 文件索引

| 文件 | 路径 | 用途 |
| --- | --- | --- |
| Queue + CPP | `正式/调度优化自动化/2026-07-21-non-npu-guardrail-queue-001.yaml` | 正式已部署 |
| Override（argo 灰度） | `正式/调度优化自动化/2026-07-21-argo-gray-override.yaml` | 已回滚删除 |
| Override（模拟） | `正式/调度优化自动化/2026-07-21-multins-queue-simulation-override.yaml` | 已清理 |
| 模拟 Job | `正式/调度优化自动化/2026-07-21-multins-queue-simulation-jobs.yaml` | 已清理 |
| Override（fbgemm 模拟） | `正式/调度优化自动化/2026-07-21-fbgemm-queue-simulation-override.yaml` | 已清理 |
| fbgemm 模拟 Job | `正式/调度优化自动化/2026-07-21-fbgemm-queue-simulation-jobs.yaml` | 已清理 |

---

## 四、正式环境验证时间线

### 4.1 里程碑

| 时间 | 事件 |
| --- | --- |
| 07-21 13:30 | 预置专用 Queue `non-npu-guardrail-queue`（cap 12/8Gi） |
| 07-21 14:24 | 多 Namespace 模拟（fbgemm/indeskd/mindie-llm），Override 生效，Inqueue 出现，mindie-llm 3 个正常，fbgemm+indexsdk 6 个被清理 |
| 07-21 17:13 | cap 调至 `150/400Gi` |
| 07-21 22:57 | 上线 argo 灰度 Override |
| 07-21 23:06 | Inqueue 存活验证：4 个测试 Job，2 Running + 2 Inqueue，持续 3+ 分钟无 ScheduleBindingFailed |
| 07-21 23:18 | cap 恢复 `150/400Gi`，测试 Job 清理 |
| 07-21 ~23:30 | argo 等待超 40 分钟 → 立即回滚 Override |
| 07-21 ~23:35 | 回滚完成，argo 存量 Job 继续自然完成 |

### 4.2 观测的快照节点数

| 时间 | pre-paid | post-paid | 总计 |
| --- | ---: | ---: | ---: |
| 07-21 13:26 | 21 | 6 | 27 |
| 07-21 17:13 | 21 | 38 | 59 |
| 07-21 ~19:00 | 21 | 32 | 53 |
| 07-21 ~22:00 | 21 | 24 | 45 |
| 07-21 ~23:00 | 21 | 22 | 43 |

---

## 五、测试环境验证结果

### 5.1 测试集群

测试 Karmada：`/Users/gorden/huawei/code/karmada/测试/karmada.yaml`
测试单集群：`member1`（API: `1.92.130.9:5443`）
`member2` 网络不通，未作为验证目标。

### 5.2 阶段 A-E 结论

| 阶段 | 结论 |
| --- | --- |
| 传播验证 | Queue + 精确 CPP 传播到 member1 成功，member2 无该 Queue |
| 单 Job 导流 | Override 改写 spec.queue 成功，Karmada 源 Job 不变 |
| 无护栏基线 | 2 Job 同时在 shared-flexible-queue 中 Running |
| capability 护栏 | 第 1 个 Running，第 2 个 Inqueue/NotEnoughResources → 释放后自动 Running |
| 对照 | Queue 排队语义成立，但测试环境无 Autoscaler，不能验证 ECS 效果 |

### 5.3 测试 YAML

目录：`测试/低成本验证/2026-07-21/`

| 文件 | 用途 |
| --- | --- |
| `non-npu-guardrail-queue-member1.yaml` | 测试 Queue + member1 CPP |
| `non-npu-guardrail-canary.yaml` | 单 Job 导流验证 |
| `non-npu-guardrail-baseline.yaml` | 无护栏基线对照 |
| `non-npu-guardrail-capability.yaml` | 护栏 overflow 验证 |

---

## 六、遇到的问题与解决方案

### 6.1 测试镜像拉取失败

- **现象**：模拟 Job 使用 `busybox:1.36`，正式 001 无法访问 Docker Hub
- **解决**：改为内部镜像 `swr.cn-southwest-2.myhuaweicloud.com/modelfoundry/alpine:3.23.3`

### 6.2 Override 标签匹配失败

- **现象**：第一批 3 个测试 Job 带 `huawei.com/npu: "false"` 标签，Override 使用 `DoesNotExist`
- **原因**：标签存在（值为 `false`）不满足 `DoesNotExist`
- **解决**：真实非 NPU Job 不带此标签，测试 Job 移除该标签

### 6.3 fbgemm-ascend/indexsdk Job 被 Karmada 清理

- **现象**：6 个 Inqueue Job 约 5-6 分钟后 ResourceBinding 被清理（ScheduleBindingFailed）
- **原因**：需要进一步排查。同批 mindie-llm 3 个 Job 正常，环境已有 76 条同类 Event
- **后续**：Inqueue 存活验证（23:18）证明 Job 在 Inqueue 中可存活 3+ 分钟无 ScheduleBindingFailed

### 6.4 argo 等待时间超 SLO

- **现象**：argo 约 13 个 Job 进入专用 Queue，等待超过 40 分钟
- **原因**：`150 CPU / 400Gi` 一次只能 4-5 个并发，amd64 和 arm64 混合在同一个 Queue 里排队
- **解决方向**：按架构拆分 Queue（amd64 + arm64），提高总并发；或扩大 capability
- **处理**：已回滚 argo Override

### 6.5 Queue cap 被外部修改

- **现象**：cap 从 `150/400Gi` 变为 `600/1600Gi`
- **状态**：暂不动，记录为外部变更

### 6.6 无法验证 ECS 减少效果

- **原因**：测试 member1 无 Cluster Autoscaler/HNA
- **影响**：只能验证 Queue 排队语义，无法直接证明 Queue 减少 ECS 弹出
- **结论**：需要在高负载正式窗口做全量覆盖观察后才能判定

---

## 七、当前正式环境状态

| 资源 | 状态 |
| --- | --- |
| Queue `non-npu-guardrail-queue` | Open，cap 600/1600（外部修改），allocated 约 380 CPU |
| CPP `non-npu-guardrail-queue-001` | 在线，仅 001 |
| Override | **全部已删除** |
| COP/p20/Namespace CPP | 在线，无漂移 |
| `shared-flexible-queue` | 正常，所有生产 Job 恢复使用 |

---

## 八、关键决策边界与注意事项

1. **正式环境写入需二次确认**，任何修改须经明确批准。
2. 不改 COP、p20、HNA、Autoscaler、Cluster 标签、shared-flexible-queue。
3. Queue 从 Karmada 控制面创建，按"先精确 CPP 再 Queue"顺序。
4. Override 匹配必须用 `huawei.com/npu DoesNotExist`（真实 Job 没有此标签），不能用 `false`。
5. **单 Queue 共享 amd64+arm64 会导致排队时间过长**，后续应拆分为两个 Queue。
6. **Queue 的 core trade-off**：cap 越大 = 并发越多 = ECS 抑制效果越弱但等待时间越短。
7. `ScheduleBindingFailed` 是正式环境已知非阻塞 Warning，不能直接等同于 Queue 丢任务。
8. 不能在 001 成员侧直接 apply Queue；Karmada 会回写覆盖。
9. 测试环境 member1 无 Autoscaler，无法做 ECS 扩容对照实验。

---

## 九、下一步建议

1. **采集两夜完整数据**，做 post-paid 峰值环比
2. **按架构拆分 Queue**：`non-npu-guardrail-amd64` + `non-npu-guardrail-arm64`，各自独立 cap
3. **小范围灰度**：选低风险 Namespace（如 `fbgemm-ascend`），先验证单架构 Queue 效果
4. **低峰窗口操作**：避免在 post-paid 超过 15-20 台时做任何策略变更
5. **正式全量覆盖前**：必须在至少一个完整的高峰周期观察 Autoscaler 行为变化

---

## 十、环境访问

| 资源 | 路径 |
| --- | --- |
| 正式 Karmada | `/Users/gorden/huawei/code/karmada/正式/正式贵阳karmada.yaml` |
| 正式 001 | `/Users/gorden/huawei/code/karmada/正式/0001.yaml` |
| 正式 wlcb | `/Users/gorden/huawei/code/karmada/正式/wlcb.yaml` |
| 测试 Karmada | `/Users/gorden/huawei/code/karmada/测试/karmada.yaml` |
| 测试 member1 | API `https://1.92.130.9:5443` |
| 自动化目录 | `/Users/gorden/huawei/code/karmada/正式/调度优化自动化/` |

---

## 十一、远端文档索引

| 文档 | 链接 |
| --- | --- |
| 完整交接（本文件） | https://github.com/yyl-support/file/blob/main/report/Karmada调度优化与Queue护栏完整交接_20260721.md |
| Queue 护栏验证路径 | https://github.com/yyl-support/file/blob/main/report/非NPU队列护栏验证路径_20260721.md |
| 队列与并发治理方案 | https://github.com/yyl-support/file/blob/main/report/非NPU任务队列与并发治理方案_20260721.md |
| 24h 效果观测 | https://github.com/yyl-support/file/blob/main/report/优化效果观测分析_20260721.md |
| 自动化工具包 | https://github.com/yyl-support/file/tree/main/karmada-scheduling-policy-observer |
