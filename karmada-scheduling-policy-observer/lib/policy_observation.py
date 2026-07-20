#!/usr/bin/env python3
"""Summarize read-only Karmada scheduling observations and multi-day evidence."""

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


NAMESPACE_POLICIES = {
    "argo-namespace-propagation", "pytorch-namespace-propagation",
    "indexsdk-namespace-propagation", "recsdk-namespace-propagation",
    "ragsdk-namespace-propagation", "op-plugin-namespace-propagation",
    "fbgemm-ascend-namespace-propagation", "multimodalsdk-namespace-propagation",
    "mindie-llm-namespace-propagation", "mindie-motor-namespace-propagation",
    "mindie-sd-namespace-propagation",
}
TERMINAL_JOB_PHASES = {"Completed", "Failed", "Terminated", "Aborted"}


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def get_path(value, *parts, default=None):
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def condition_status(item, condition_type):
    for condition in get_path(item, "status", "conditions", default=[]) or []:
        if condition.get("type") == condition_type:
            return condition.get("status", "Unknown")
    return "Unknown"


def cluster_targets(clusters, label):
    return sorted(
        item["metadata"]["name"]
        for item in clusters.get("items", [])
        if get_path(item, "metadata", "labels", default={}).get(label) == "true"
    )


def policy_integrity(raw):
    clusters = raw["clusters"]
    cop = raw["cop"]
    p20 = raw["p20"]
    policies = raw["namespace-cpps"].get("items", [])
    preferred = get_path(cop, "spec", "overrideRules", default=[])
    preferred = get_path(preferred[0], "overriders", "plaintext", default=[]) if preferred else []
    preferred = get_path(preferred[0], "value", "nodeAffinity", "preferredDuringSchedulingIgnoredDuringExecution", default=[]) if preferred else []
    prepaid_preference = any(
        entry.get("weight") == 100 and any(
            expression.get("key") == "node.cce.io/billing-mode"
            and expression.get("operator") == "In"
            and expression.get("values") == ["pre-paid"]
            for expression in get_path(entry, "preference", "matchExpressions", default=[])
        ) for entry in preferred
    )
    required = get_path(cop, "spec", "overrideRules", default=[])
    required = get_path(required[0], "overriders", "plaintext", default=[]) if required else []
    required = get_path(required[0], "value", "nodeAffinity", "requiredDuringSchedulingIgnoredDuringExecution", "nodeSelectorTerms", default=[]) if required else []
    npu_exclusion = any(
        expression.get("key") == "accelerator/huawei-npu" and expression.get("operator") == "DoesNotExist"
        for term in required for expression in term.get("matchExpressions", [])
    )
    namespace_selector_ok = {
        item["metadata"]["name"]: get_path(item, "spec", "placement", "clusterAffinity", "labelSelector", "matchLabels", default={}).get("dispatch/auto") == "true"
        for item in policies if item.get("metadata", {}).get("name") in NAMESPACE_POLICIES
    }
    return {
        "ready_clusters": sorted(item["metadata"]["name"] for item in clusters.get("items", []) if condition_status(item, "Ready") == "True"),
        "has_cpu_targets": cluster_targets(clusters, "has-cpu"),
        "dispatch_auto_targets": cluster_targets(clusters, "dispatch/auto"),
        "cop_generation": get_path(cop, "metadata", "generation"),
        "cop_prepaid_weight_100": prepaid_preference,
        "cop_required_npu_exclusion": npu_exclusion,
        "p20_generation": get_path(p20, "metadata", "generation"),
        "p20_has_cpu_selector": get_path(p20, "spec", "placement", "clusterAffinity", "labelSelector", "matchLabels", default={}).get("has-cpu") == "true",
        "namespace_policies_expected": len(NAMESPACE_POLICIES),
        "namespace_policies_dispatch_auto": sum(namespace_selector_ok.values()),
        "namespace_policies_missing": sorted(NAMESPACE_POLICIES - set(namespace_selector_ok)),
        "namespace_policies_invalid": sorted(name for name, valid in namespace_selector_ok.items() if not valid),
    }


def node_index(nodes):
    return {
        item["metadata"]["name"]: {
            "billing_mode": get_path(item, "metadata", "labels", default={}).get("node.cce.io/billing-mode", "unknown"),
            "npu": "accelerator/huawei-npu" in get_path(item, "metadata", "labels", default={}),
            "ready": condition_status(item, "Ready") == "True",
        }
        for item in nodes.get("items", [])
    }


def workload_metrics(raw):
    jobs = raw["jobs"].get("items", [])
    non_npu_jobs = [job for job in jobs if "huawei.com/npu" not in get_path(job, "metadata", "labels", default={})]
    active_jobs = [job for job in non_npu_jobs if get_path(job, "status", "state", "phase", default="Unknown") not in TERMINAL_JOB_PHASES]
    job_keys = {(item["metadata"].get("namespace", "default"), item["metadata"]["name"]) for item in non_npu_jobs}
    nodes = {"001": node_index(raw["nodes-001"]), "wlcb": node_index(raw["nodes-wlcb"])}
    pod_counts = Counter()
    unscheduled = 0
    for cluster in ("001", "wlcb"):
        for pod in raw[f"pods-{cluster}"].get("items", []):
            labels = get_path(pod, "metadata", "labels", default={})
            key = (get_path(pod, "metadata", "namespace", default="default"), labels.get("volcano.sh/job-name"))
            if key not in job_keys:
                continue
            node = get_path(pod, "spec", "nodeName")
            if not node:
                unscheduled += 1
                continue
            details = nodes[cluster].get(node, {"billing_mode": "unknown", "npu": False})
            pod_counts[(cluster, details["billing_mode"], "npu" if details["npu"] else "non-npu")] += 1
    works = [item for item in raw["works"].get("items", []) if any(
        manifest.get("kind") == "Job" and manifest.get("apiVersion") == "batch.volcano.sh/v1alpha1"
        and "huawei.com/npu" not in get_path(manifest, "metadata", "labels", default={})
        for manifest in get_path(item, "spec", "workload", "manifests", default=[])
    )]
    return {
        "non_npu_jobs": len(non_npu_jobs),
        "active_non_npu_jobs": len(active_jobs),
        "non_npu_job_phases": dict(sorted(Counter(get_path(job, "status", "state", "phase", default="Unknown") for job in non_npu_jobs).items())),
        "non_npu_works": len(works),
        "work_applied": dict(sorted(Counter(condition_status(work, "Applied") for work in works).items())),
        "non_npu_pods_by_placement": [
            {"cluster": cluster, "billing_mode": billing, "node_class": node_class, "pods": count}
            for (cluster, billing, node_class), count in sorted(pod_counts.items())
        ],
        "unscheduled_non_npu_pods": unscheduled,
        "nodes": {
            cluster: {"total": len(index), "ready": sum(node["ready"] for node in index.values()), "billing_mode": dict(sorted(Counter(node["billing_mode"] for node in index.values()).items()))}
            for cluster, index in nodes.items()
        },
    }


def hna_metrics(hnas, events):
    records = []
    for item in hnas.get("items", []):
        status = item.get("status", {})
        conditions = []
        for condition in status.get("conditions", []):
            # CCE HNA uses action-history entries instead of the standard
            # Kubernetes Condition schema.
            if "state" in condition or "lastProbeTime" in condition:
                conditions.append({
                    "type": "ScaleAction",
                    "status": condition.get("state", "Unknown"),
                    "reason": condition.get("message", ""),
                    "last_transition_time": condition.get("lastProbeTime", ""),
                    "rule_name": condition.get("ruleName", ""),
                    "count_before_scale": condition.get("countBeforeScale"),
                    "count_after_scale": condition.get("countAfterScale"),
                    "target_nodepool_id": condition.get("targetNodepoolId", ""),
                    "target_scale_group": condition.get("targetScaleGroup", ""),
                })
            else:
                conditions.append({
                    "type": condition.get("type", "Unknown"),
                    "status": condition.get("status", "Unknown"),
                    "reason": condition.get("reason", ""),
                    "last_transition_time": condition.get("lastTransitionTime", ""),
                })
        records.append({
            "namespace": get_path(item, "metadata", "namespace", default="default"),
            "name": get_path(item, "metadata", "name", default="unknown"),
            "uid": get_path(item, "metadata", "uid", default=""),
            "generation": get_path(item, "metadata", "generation"),
            "observed_generation": status.get("observedGeneration"),
            "conditions": conditions,
        })
    hna_events = [
        {
            "namespace": get_path(item, "metadata", "namespace", default="default"),
            "reason": item.get("reason", ""),
            "message": item.get("message", ""),
            "event_time": item.get("eventTime") or get_path(item, "lastTimestamp", default=""),
        }
        for item in events.get("items", [])
        if get_path(item, "involvedObject", "kind", default="") == "HorizontalNodeAutoscaler"
    ]
    return {"objects": records, "events": hna_events}


def collect(args):
    directory = Path(args.input_dir)
    required = ["clusters", "cop", "p20", "namespace-cpps", "jobs", "works", "resourcebindings", "nodes-001", "pods-001", "hnas-001", "warnings-001", "nodes-wlcb", "pods-wlcb", "hnas-wlcb", "warnings-wlcb"]
    raw = {name: load(directory / f"{name}.json") for name in required}
    result = {
        "timestamp": args.timestamp,
        "policy": policy_integrity(raw),
        "workloads": workload_metrics(raw),
        "hna": {
            "001": hna_metrics(raw["hnas-001"], raw["warnings-001"]),
            "wlcb": hna_metrics(raw["hnas-wlcb"], raw["warnings-wlcb"]),
        },
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def light_metrics(args):
    directory = Path(args.input_dir)
    required = ["jobs", "works", "nodes-001", "pods-001", "hnas-001", "events-001", "nodes-wlcb", "pods-wlcb", "hnas-wlcb", "events-wlcb"]
    raw = {name: load(directory / f"{name}.json") for name in required}
    workloads = workload_metrics(raw)
    print(json.dumps({"timestamp": args.timestamp, "metrics": {
        "non_npu_jobs": workloads["non_npu_jobs"],
        "active_non_npu_jobs": workloads["active_non_npu_jobs"],
        "non_npu_job_phases": workloads["non_npu_job_phases"],
        "non_npu_works": workloads["non_npu_works"],
        "work_applied": workloads["work_applied"],
        "unscheduled_non_npu_pods": workloads["unscheduled_non_npu_pods"],
        "nodes": workloads["nodes"],
        "hna": {
            "001": hna_metrics(raw["hnas-001"], raw["events-001"]),
            "wlcb": hna_metrics(raw["hnas-wlcb"], raw["events-wlcb"]),
        },
    }}, ensure_ascii=False, sort_keys=True))


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def report(args):
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    summaries = []
    for path in sorted(Path(args.snapshot_dir).glob("*/summary.json")):
        summary = load(path)
        if parse_timestamp(summary["timestamp"]).astimezone(timezone.utc) >= cutoff:
            summaries.append(summary)
    if not summaries:
        raise SystemExit(f"No snapshots in the last {args.days} days: {args.snapshot_dir}")
    light_metrics = []
    for path in sorted(Path(args.light_metrics_dir).glob("metrics-*.jsonl")):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    metric = json.loads(line)
                    if parse_timestamp(metric["timestamp"]).astimezone(timezone.utc) >= cutoff:
                        light_metrics.append(metric)
    def policy_is_intact(item):
        policy = item["policy"]
        return all((
            policy["has_cpu_targets"] == ["001"],
            policy["dispatch_auto_targets"] == ["001", "wlcb"],
            policy["cop_prepaid_weight_100"],
            policy["cop_required_npu_exclusion"],
            policy["p20_has_cpu_selector"],
            policy["namespace_policies_dispatch_auto"] == policy["namespace_policies_expected"],
            set(policy["ready_clusters"]) >= {"001", "wlcb"},
        ))

    integrity_passes = sum(policy_is_intact(item) for item in summaries)
    placements = Counter()
    active_samples = 0
    for summary in summaries:
        if summary["workloads"]["active_non_npu_jobs"]:
            active_samples += 1
        for placement in summary["workloads"]["non_npu_pods_by_placement"]:
            if placement["node_class"] == "non-npu":
                placements[placement["billing_mode"]] += placement["pods"]
    prepaid = placements["pre-paid"]
    total_placed = sum(placements.values())
    evidence = "insufficient workload evidence"
    if total_placed:
        evidence = f"{prepaid}/{total_placed} observed non-NPU Pod placements were on pre-paid nodes ({prepaid / total_placed:.1%})"
    peak_active = max((item["metrics"]["active_non_npu_jobs"] for item in light_metrics), default=0)
    peak_pending = max((item["metrics"]["unscheduled_non_npu_pods"] for item in light_metrics), default=0)
    node_ranges = {}
    scale_outs = []
    previous = None
    for item in light_metrics:
        if previous:
            for cluster in ("001", "wlcb"):
                before = previous["metrics"]["nodes"][cluster]["total"]
                after = item["metrics"]["nodes"][cluster]["total"]
                if after > before:
                    scale_outs.append({"timestamp": item["timestamp"], "cluster": cluster, "before": before, "after": after})
        previous = item
    for cluster in ("001", "wlcb"):
        for billing_mode in ("pre-paid", "post-paid"):
            values = [item["metrics"]["nodes"][cluster]["billing_mode"].get(billing_mode, 0) for item in light_metrics]
            if values:
                node_ranges[f"{cluster}/{billing_mode}"] = f"{min(values)}-{max(values)}"
    lines = [
        "# 正式调度策略持续验证报告", "", f"- 统计窗口：最近 {args.days} 天", f"- 快照数：{len(summaries)}",
        f"- 首个快照：{summaries[0]['timestamp']}", f"- 最后快照：{summaries[-1]['timestamp']}",
        "- 采集方式：仅 Kubernetes `get/list`，未执行写入、删除、驱逐或扩缩容操作。", "",
        "## 策略完整性", "",
        f"- 完整策略与健康条件同时满足：{integrity_passes}/{len(summaries)} 个快照。",
        "- 判定项：001 是唯一 `has-cpu=true` 目标；001/wlcb 精确为 `dispatch/auto=true` 目标；COP 保留 NPU 排除和 pre-paid 权重 100 偏好；p20 与 11 条 Namespace CPP 保持预期选择器；001/wlcb Ready。", "",
        "## 运行时调度证据", "", f"- 存在活动非 NPU Job 的快照：{active_samples}/{len(summaries)}。",
        f"- {evidence}。", "",
        "## 十分钟轻量指标", "",
        f"- 有效轻量指标记录：{len(light_metrics)} 条。",
        f"- 非 NPU 活动 Job 峰值：{peak_active}。",
        f"- 非 NPU 未调度 Pod 峰值：{peak_pending}。",
        f"- Ready 节点计费模式范围：{', '.join(f'{name}={value}' for name, value in sorted(node_ranges.items())) or '无轻量指标'}。", "",
        "## HNA 与 ECS 弹性扩容观测", "",
        f"- HNA 相关 Event：{sum(len(item['metrics']['hna'][cluster]['events']) for item in light_metrics for cluster in ('001', 'wlcb'))} 条（同一 Event 可能出现在多次采样中）。",
        f"- 连续十分钟采样识别到节点数上升：{len(scale_outs)} 次。",
    ]
    if scale_outs:
        lines.extend(f"- {item['timestamp']}：{item['cluster']} 节点总数 {item['before']} -> {item['after']}。" for item in scale_outs)
    lines.extend([
        "- 节点数上升是 ECS 扩容的观测线索；需使用实例 ID/任务 ID 与 CTS/CCE 审计去重确认实际 ECS 创建结果。",
        "- HNA conditions 只保留有限历史，不能用当前 conditions 数量推断累计扩容次数。", "",
        "## 结论", "",
    ])
    if integrity_passes == len(summaries) and total_placed and prepaid == total_placed:
        lines.append("采样期内策略未漂移，且所有观测到的非 NPU Pod 均落在 pre-paid、非 NPU 节点，可支持当前调度策略有效的结论。")
    elif integrity_passes == len(summaries) and total_placed:
        lines.append("策略在采样期内保持完整；观测到 post-paid 落点。需结合当时 pre-paid 节点的剩余容量判断其是否为高峰容量耗尽后的预期回退，不能仅据此否定策略。")
    elif integrity_passes == len(summaries):
        lines.append("策略在采样期内保持完整，但没有足够的非 NPU Pod 落点样本证明运行时偏好效果；应延长采集或在自然业务高峰后复核。")
    else:
        lines.append("存在策略或集群健康条件不满足的快照，当前不能得出策略持续有效的结论；请按快照定位偏离项。")
    lines.extend(["", "## 局限", "", "- 十分钟轻量指标缩小了短作业遗漏窗口，但不能替代逐分钟审计。", "- 小时级完整快照适合策略漂移和实际 Pod 落点复核。", "- COP 的 pre-paid 是软偏好；在符合 required 条件的 pre-paid 容量不足时，post-paid 落点可能是预期的容量回退。", "- 节点数上升不等于已成功创建同等数量 ECS；最终 ECS 口径须按实例 ID、任务 ID、节点池和 CTS/CCE 审计去重。", ""])
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(required=True)
    collect_parser = commands.add_parser("collect")
    collect_parser.add_argument("--input-dir", required=True)
    collect_parser.add_argument("--output", required=True)
    collect_parser.add_argument("--timestamp", required=True)
    collect_parser.set_defaults(func=collect)
    light_parser = commands.add_parser("light-metrics")
    light_parser.add_argument("--input-dir", required=True)
    light_parser.add_argument("--timestamp", required=True)
    light_parser.set_defaults(func=light_metrics)
    report_parser = commands.add_parser("report")
    report_parser.add_argument("--snapshot-dir", required=True)
    report_parser.add_argument("--light-metrics-dir", required=True)
    report_parser.add_argument("--days", type=int, required=True)
    report_parser.add_argument("--output", required=True)
    report_parser.set_defaults(func=report)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
