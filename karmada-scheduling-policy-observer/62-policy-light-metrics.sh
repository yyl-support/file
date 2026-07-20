#!/usr/bin/env bash

# Ten-minute, read-only aggregate metrics for short scheduling bursts.
set -Eeuo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${BASE_DIR}/lib/common.sh"

usage() {
  cat <<'EOF'
Usage: ./62-policy-light-metrics.sh [--once]

Appends one compact, read-only metrics record. It does not retain full
Kubernetes objects and does not use any Kubernetes write operation.
EOF
}

[[ "${1:-}" != "--help" && "${1:-}" != "-h" ]] || { usage; exit 0; }
[[ $# -eq 0 || "${1:-}" == "--once" ]] || { usage >&2; exit 2; }

require_commands

OBSERVATION_DIR="${OBSERVATION_DIR:-${RUNTIME_DIR}/policy-observation}"
TMP_DIR="${OBSERVATION_DIR}/.light-metrics-$$"
mkdir -p "${TMP_DIR}" "${OBSERVATION_DIR}/light-metrics"
trap 'rm -rf "${TMP_DIR}"' EXIT

collect() {
  local output="$1"
  shift
  "$@" -o json > "${TMP_DIR}/${output}"
}

collect jobs.json karmada get jobs.batch.volcano.sh -A
collect works.json karmada get works.work.karmada.io -A
collect nodes-001.json cluster001 get nodes
collect pods-001.json cluster001 get pods -A
collect hnas-001.json cluster001 get horizontalnodeautoscalers -A
collect events-001.json cluster001 get events -A
collect nodes-wlcb.json clusterwlcb get nodes
collect pods-wlcb.json clusterwlcb get pods -A
collect hnas-wlcb.json clusterwlcb get horizontalnodeautoscalers -A
collect events-wlcb.json clusterwlcb get events -A

record="$(python3 "${BASE_DIR}/lib/policy_observation.py" light-metrics \
  --input-dir "${TMP_DIR}" \
  --timestamp "$(date --iso-8601=seconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')")"
metrics_file="${OBSERVATION_DIR}/light-metrics/metrics-$(date '+%Y%m%d').jsonl"
printf '%s\n' "${record}" >> "${metrics_file}"
printf '%s\n' "${metrics_file}"
