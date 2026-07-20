#!/usr/bin/env bash

set -Eeuo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${BASE_DIR}/lib/common.sh"

usage() {
  cat <<'EOF'
Usage: ./61-policy-observation-report.sh [--days 3|4] [--output PATH]

Builds a Markdown report from completed read-only snapshots. The report states
evidence and gaps; it does not claim a preference was effective when no eligible
non-NPU Pods were observed.
EOF
}

days=3
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --days) days="${2:-}"; shift 2 ;;
    --output) output="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) usage >&2; exit 2 ;;
  esac
done
[[ "${days}" == "3" || "${days}" == "4" ]] || die "--days must be 3 or 4"

OBSERVATION_DIR="${OBSERVATION_DIR:-${RUNTIME_DIR}/policy-observation}"
if [[ -z "${output}" ]]; then
  output="${OBSERVATION_DIR}/reports/scheduling-policy-${days}d-$(date '+%Y%m%d-%H%M%S').md"
fi
mkdir -p "$(dirname "${output}")"

python3 "${BASE_DIR}/lib/policy_observation.py" report \
  --snapshot-dir "${OBSERVATION_DIR}/snapshots" \
  --light-metrics-dir "${OBSERVATION_DIR}/light-metrics" \
  --days "${days}" \
  --output "${output}"
printf '%s\n' "${output}"
