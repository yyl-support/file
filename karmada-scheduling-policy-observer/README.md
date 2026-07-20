# Karmada Scheduling Policy Observer

用于连续 3 至 4 天只读验证 Karmada 非 NPU Job 调度策略的工具包。

## 目的

- 验证 COP 持续保留 NPU 节点排除和 pre-paid weight 100 软偏好。
- 验证 p20 的 `has-cpu=true` 目标及 11 条 Namespace CPP 的 `dispatch/auto=true` 目标没有漂移。
- 记录非 NPU Job/Work、实际 Pod 落点、pre-paid/post-paid 节点数量、Pending 峰值与 HNA 动作。
- 识别 HNA 扩容与节点数上升，作为 ECS 弹出线索；不将节点增量直接等同于 ECS 成功创建数。

## 采集策略

- 每小时完整快照：策略对象、集群标签、Job/Work/ResourceBinding、节点、Pod、HNA 和 Event 原始 JSON。
- 每 10 分钟轻量指标：Job/Work、未调度 Pod、节点计费模式和 HNA 动作，按日追加 JSONL。
- 全程只使用 Kubernetes `get/list`，不创建、更新、删除、驱逐或扩缩容任何资源。

## 快速开始

生产推荐 Linux 常开主机和 `systemd/` 下的 timer。将三个只读 kubeconfig 通过环境变量传入，或按 `systemd/karmada-policy-observation.env.example` 配置。

```bash
export KARMADA_KUBECONFIG=/secure/path/karmada.yaml
export CLUSTER_001_KUBECONFIG=/secure/path/001.yaml
export CLUSTER_WLCB_KUBECONFIG=/secure/path/wlcb.yaml

./60-policy-observation.sh --once
./62-policy-light-metrics.sh --once
./61-policy-observation-report.sh --days 3
```

完整的 Linux/macOS 安装、权限、启动、停止、报告判读、HNA/ECS 边界和排障说明请参阅 [自动采集脚本使用文档.md](自动采集脚本使用文档.md)。

## 不包含的内容

该包不含 kubeconfig、token、集群快照、运行日志或其他生产数据。`kubeconfigs/` 和 `runtime/` 已被 Git 忽略。
