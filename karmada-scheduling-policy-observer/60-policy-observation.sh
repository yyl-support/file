#!/usr/bin/env bash

# Read-only production snapshot for the multi-day scheduling-policy evaluation.
set -Eeuo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${BASE_DIR}/lib/common.sh"

usage() {
  cat <<'EOF'
Usage: ./60-policy-observation.sh [--once]

Collects one read-only snapshot from Karmada, 001, and wlcb. Snapshots are
written under runtime/policy-observation/snapshots and are safe to run from a
scheduled task. No Kubernetes write verb is used.
EOF
}

[[ "${1:-}" != "--help" && "${1:-}" != "-h" ]] || { usage; exit 0; }
[[ $# -eq 0 || "${1:-}" == "--once" ]] || { usage >&2; exit 2; }

require_commands

OBSERVATION_DIR="${OBSERVATION_DIR:-${RUNTIME_DIR}/policy-observation}"
SNAPSHOT_TIME="$(date '+%Y%m%d-%H%M%S')"
SNAPSHOT_DIR="${OBSERVATION_DIR}/snapshots/${SNAPSHOT_TIME}"
TMP_DIR="${OBSERVATION_DIR}/.snapshot-${SNAPSHOT_TIME}-$$"
mkdir -p "${TMP_DIR}"
trap 'rm -rf "${TMP_DIR}"' EXIT

collect() {
  local output="$1"
  shift
  "$@" -o json > "${TMP_DIR}/${output}"
}

# Policy and workload reads from the Karmada control plane.
collect clusters.json karmada get clusters
collect cop.json karmada get cop non-npu-vcjob-node-affinity
collect p20.json karmada get cpp non-npu-vcjob-prefer-001
collect namespace-cpps.json karmada get cpp
collect jobs.json karmada get jobs.batch.volcano.sh -A
collect works.json karmada get works.work.karmada.io -A
collect resourcebindings.json karmada get rb -A
collect karmada-warning-events.json karmada get events -A --field-selector type=Warning

# Member reads identify the billing-mode and NPU characteristics of actual Pod
# placements. They do not alter nodes, pods, queues, or autoscalers.
collect nodes-001.json cluster001 get nodes
collect pods-001.json cluster001 get pods -A
collect hnas-001.json cluster001 get horizontalnodeautoscalers -A
collect warnings-001.json cluster001 get events -A --field-selector type=Warning
collect nodes-wlcb.json clusterwlcb get nodes
collect pods-wlcb.json clusterwlcb get pods -A
collect hnas-wlcb.json clusterwlcb get horizontalnodeautoscalers -A
collect warnings-wlcb.json clusterwlcb get events -A --field-selector type=Warning

python3 "${BASE_DIR}/lib/policy_observation.py" collect \
  --input-dir "${TMP_DIR}" \
  --output "${TMP_DIR}/summary.json" \
  --timestamp "$(date --iso-8601=seconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')"

mkdir -p "${OBSERVATION_DIR}/snapshots"
mv "${TMP_DIR}" "${SNAPSHOT_DIR}"
trap - EXIT
printf '%s\n' "${SNAPSHOT_DIR}/summary.json"
