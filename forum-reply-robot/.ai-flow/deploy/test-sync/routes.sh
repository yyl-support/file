#!/usr/bin/env bash
# routes.sh —— 把 test 环境的路由拓扑同步成预览形态(一个 issue 共享 host)
# ====================================================================
# 由 backlog/.ai-flow/scripts/gen-preview-hook.sh 生成,模板 = meeting-server。
# 逐个 sub 拉 test 归档里的 ingress.yaml,改:host→共享 host、backend→预览部署名、
# 去 tls / backend-protocol HTTPS、保留 path/rewrite、正则 path 自动转 ImplementationSpecific。
set -uo pipefail

PREVIEW_NS="${PREVIEW_NS:?}"
ISSUE="${ISSUE:?}"
ING_DOMAIN="${ING_DOMAIN:-preview.test.osinfra.cn}"
ARCHIVE_REPO="${ARCHIVE_REPO:-${GITHUB_REPOSITORY_OWNER:-opensourceways}/infra-common}"
ARCHIVE_PATH="${ARCHIVE_PATH:?ARCHIVE_PATH required}"
ARCHIVE_REF="${ARCHIVE_REF:-master}"
ROUTE_MAP="${ROUTE_MAP:?ROUTE_MAP required (sub=backend;...)}"
ISSUE_HOST="${ISSUE_HOST:-issue-${ISSUE}.${ING_DOMAIN}}"
OUT_DIR="${OUT_DIR:-${RUNNER_TEMP:-/tmp}/ai/test-sync}"
mkdir -p "$OUT_DIR"

echo "::group::routes-sync (issue host=$ISSUE_HOST)"
echo "  route_map=$ROUTE_MAP"
ANY=0
IFS=';' read -ra PAIRS <<< "$ROUTE_MAP"
for pair in "${PAIRS[@]}"; do
  [ -z "$pair" ] && continue
  sub="${pair%%=*}"; backend="${pair#*=}"
  [ -z "$sub" ] || [ -z "$backend" ] && continue
  ING_RAW="https://raw.githubusercontent.com/${ARCHIVE_REPO}/${ARCHIVE_REF}/${ARCHIVE_PATH}/${sub}/ingress.yaml"
  src="$OUT_DIR/test-ingress-${sub}.yaml"
  curl -fsSL -H "Authorization: token ${GH_TOKEN:-}" "$ING_RAW" -o "$src" 2>/dev/null \
    || curl -fsSL "$ING_RAW" -o "$src" 2>/dev/null || { echo "  ::warning::$sub 无 test ingress.yaml,跳过"; continue; }
  out="$OUT_DIR/route-${sub}.yaml"
  python3 - "$src" "$out" "$sub" "$backend" "$PREVIEW_NS" "$ISSUE" "$ISSUE_HOST" <<'PY'
import sys, yaml
src, out, sub, backend, ns, issue, host = sys.argv[1:8]
try: docs = [d for d in yaml.safe_load_all(open(src, encoding='utf-8')) if d]
except Exception as e: sys.stderr.write(f"parse fail {sub}: {e}\n"); sys.exit(0)
res = []
for d in docs:
    if d.get('kind') != 'Ingress': continue
    md = d.setdefault('metadata', {})
    md['name'] = f"issue-{issue}-{sub}"; md['namespace'] = ns
    md.setdefault('labels', {}).update({'app':'preview','repo':sub,'issue':str(issue)})
    ann = md.get('annotations', {}) or {}
    ann.pop('nginx.ingress.kubernetes.io/backend-protocol', None)
    ann['nginx.ingress.kubernetes.io/ssl-redirect'] = 'false'
    spec = d.setdefault('spec', {})
    spec['ingressClassName'] = 'nginx'; spec.pop('tls', None)
    use_regex = False
    for rule in spec.get('rules', []):
        rule['host'] = host
        for p in rule.get('http', {}).get('paths', []):
            path = p.get('path', '/')
            if any(ch in path for ch in '()$*+?[]'):
                use_regex = True; p['pathType'] = 'ImplementationSpecific'  # 正则 path 必须用这个,否则 admission 拒
            be = p.setdefault('backend', {}).setdefault('service', {})
            be['name'] = backend; be.setdefault('port', {})['number'] = 5000
    if use_regex: ann['nginx.ingress.kubernetes.io/use-regex'] = 'true'
    md['annotations'] = ann; res.append(d)
if res:
    yaml.safe_dump_all(res, open(out, 'w', encoding='utf-8'), default_flow_style=False, allow_unicode=True)
    print("  rendered route:", sub, "→", backend)
PY
  if [ -f "$out" ]; then
    kubectl apply -n "$PREVIEW_NS" -f "$out" 2>&1 | sed 's/^/  /' && ANY=1 || echo "  ::warning::$sub route apply 失败"
  fi
done
[ "$ANY" = 0 ] && echo "  ::warning::没同步到任何路由"
echo "::endgroup::"
echo "$ISSUE_HOST"
