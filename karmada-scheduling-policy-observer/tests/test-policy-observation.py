#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "lib" / "policy_observation.py"
SPEC = importlib.util.spec_from_file_location("policy_observation", MODULE)
policy_observation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy_observation)


def cluster(name, labels):
    return {"metadata": {"name": name, "labels": labels}, "status": {"conditions": [{"type": "Ready", "status": "True"}]}}


class PolicyObservationTests(unittest.TestCase):
    def test_policy_integrity_accepts_expected_live_policy(self):
        raw = {
            "clusters": {"items": [cluster("001", {"has-cpu": "true", "dispatch/auto": "true"}), cluster("wlcb", {"dispatch/auto": "true"})]},
            "cop": {"metadata": {"generation": 6}, "spec": {"overrideRules": [{"overriders": {"plaintext": [{"value": {"nodeAffinity": {
                "requiredDuringSchedulingIgnoredDuringExecution": {"nodeSelectorTerms": [{"matchExpressions": [{"key": "accelerator/huawei-npu", "operator": "DoesNotExist"}]}]},
                "preferredDuringSchedulingIgnoredDuringExecution": [{"weight": 100, "preference": {"matchExpressions": [{"key": "node.cce.io/billing-mode", "operator": "In", "values": ["pre-paid"]}]}}],
            }}}]}}]}},
            "p20": {"metadata": {"generation": 5}, "spec": {"placement": {"clusterAffinity": {"labelSelector": {"matchLabels": {"has-cpu": "true"}}}}}},
            "namespace-cpps": {"items": [{"metadata": {"name": name}, "spec": {"placement": {"clusterAffinity": {"labelSelector": {"matchLabels": {"dispatch/auto": "true"}}}}}} for name in policy_observation.NAMESPACE_POLICIES]},
        }

        result = policy_observation.policy_integrity(raw)

        self.assertEqual(result["has_cpu_targets"], ["001"])
        self.assertEqual(result["dispatch_auto_targets"], ["001", "wlcb"])
        self.assertTrue(result["cop_prepaid_weight_100"])
        self.assertTrue(result["cop_required_npu_exclusion"])
        self.assertTrue(result["p20_has_cpu_selector"])
        self.assertEqual(result["namespace_policies_dispatch_auto"], 11)

    def test_workload_metrics_classifies_member_pod_billing_mode(self):
        raw = {
            "jobs": {"items": [{"metadata": {"namespace": "argo", "name": "cpu-job", "labels": {}}, "status": {"state": {"phase": "Running"}}}]},
            "works": {"items": []},
            "nodes-001": {"items": [cluster("prepaid-node", {"node.cce.io/billing-mode": "pre-paid"})]},
            "nodes-wlcb": {"items": []},
            "pods-001": {"items": [{"metadata": {"namespace": "argo", "labels": {"volcano.sh/job-name": "cpu-job"}}, "spec": {"nodeName": "prepaid-node"}}]},
            "pods-wlcb": {"items": []},
        }

        result = policy_observation.workload_metrics(raw)

        self.assertEqual(result["active_non_npu_jobs"], 1)
        self.assertEqual(result["non_npu_pods_by_placement"], [{"cluster": "001", "billing_mode": "pre-paid", "node_class": "non-npu", "pods": 1}])

    def test_hna_metrics_keeps_conditions_and_related_events(self):
        hnas = {"items": [{
            "metadata": {"namespace": "default", "name": "pool-hna", "uid": "123", "generation": 2},
            "status": {"observedGeneration": 2, "conditions": [{"type": "Active", "status": "True", "reason": "ScalingUp"}]},
        }]}
        events = {"items": [{
            "metadata": {"namespace": "default"},
            "involvedObject": {"kind": "HorizontalNodeAutoscaler"},
            "reason": "ScaleUp", "message": "requested node", "eventTime": "2026-07-20T10:00:00Z",
        }]}

        result = policy_observation.hna_metrics(hnas, events)

        self.assertEqual(result["objects"][0]["name"], "pool-hna")
        self.assertEqual(result["objects"][0]["conditions"][0]["reason"], "ScalingUp")
        self.assertEqual(result["events"][0]["reason"], "ScaleUp")

    def test_hna_metrics_parses_cce_action_history(self):
        hnas = {"items": [{
            "metadata": {"name": "pool-hna"},
            "status": {"conditions": [{
                "state": "Successful", "message": "increase 1 node",
                "lastProbeTime": "2026-07-20T10:00:00Z", "ruleName": "cpu-rule",
                "countBeforeScale": 4, "countAfterScale": 5,
            }]},
        }]}

        result = policy_observation.hna_metrics(hnas, {"items": []})

        action = result["objects"][0]["conditions"][0]
        self.assertEqual(action["type"], "ScaleAction")
        self.assertEqual(action["status"], "Successful")
        self.assertEqual(action["count_before_scale"], 4)
        self.assertEqual(action["count_after_scale"], 5)


if __name__ == "__main__":
    unittest.main()
