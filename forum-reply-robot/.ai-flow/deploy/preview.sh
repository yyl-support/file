#!/usr/bin/env bash
# forum-reply-robot 预览部署 hook (独立预览环境版)
# ==================================================
# 由 backlog Workflow Develop preview 调用(backlog/.ai-flow/src/deployer/deploy.sh
# 探测到本仓 .ai-flow/deploy/preview.sh 就交权)。
# 由 backlog/.ai-flow/scripts/gen-preview-hook.sh 生成,模板 = meeting-server 实测实现。
#
# 入参 env: WORK_DIR/UMBRELLA/ISSUE_NUMBER/BRANCH/GH_TOKEN/KUBECONFIG/NAMESPACE/
#           PREVIEW_INGRESS_DOMAIN/VAULT_ADDR/VAULT_USERNAME/VAULT_PASSWORD
set -uo pipefail

PREVIEW_NS="${NAMESPACE:?NAMESPACE required}"
ING_DOMAIN="${PREVIEW_INGRESS_DOMAIN:-preview.test.osinfra.cn}"
PG_PWD="forum-reply-robot_preview_2026"
PG_SVC="postgresql-service"
ISSUE="${ISSUE_NUMBER:?ISSUE_NUMBER required}"
BRANCH="${BRANCH:?BRANCH required}"
WD="${WORK_DIR:?WORK_DIR required}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICES_YAML="$HERE/services.yaml"
DEPLOY_OUT="${RUNNER_TEMP:-/tmp}/ai/deploy"; mkdir -p "$DEPLOY_OUT"

echo "::notice::forum-reply-robot preview: ns=$PREVIEW_NS issue=$ISSUE domain=$ING_DOMAIN"
if [ -z "${KUBECONFIG:-}" ] || ! command -v kubectl >/dev/null 2>&1; then
  echo "::warning::无 KUBECONFIG/kubectl,降级跳过"; exit 0
fi
# 验权:Jenkins 临时 kubeconfig 的 SA 只在 preview.namespace 里有权限
if ! kubectl auth can-i create deployments -n "$PREVIEW_NS" >/dev/null 2>&1; then
  echo "::error::kubeconfig 在 ns '$PREVIEW_NS' 无 create deployments 权限(检查 services/<svc>.yaml preview.namespace)"; exit 1
fi

# 社区判定(默认 openeuler;issue 正文含 "社区: x"/"community: x" 则用指定)
COMMUNITY="openeuler"
for f in "${RUNNER_TEMP:-/tmp}/issue.txt" "$WD/../issue.txt"; do
  if [ -f "$f" ]; then
    c="$(grep -ioE '(社区|community)[:：[:space:]]+[a-zA-Z]+' "$f" 2>/dev/null | head -1 | grep -oE '[a-zA-Z]+$' || true)"
    [ -n "$c" ] && COMMUNITY="$c"; break
  fi
done
echo "::notice::community=$COMMUNITY"

# 1. namespace
if ! kubectl get ns "$PREVIEW_NS" >/dev/null 2>&1; then
  echo "-- create ns $PREVIEW_NS --"
  kubectl create ns "$PREVIEW_NS" 2>&1 | sed 's/^/  /' || { echo "::error::create ns 失败"; exit 1; }
fi

# 2. 底座 PostgreSQL(首次才部署;init.sql 建库名要跟 services.yaml foundation.init_databases 对齐)
if kubectl get deploy postgresql -n "$PREVIEW_NS" >/dev/null 2>&1; then
  echo "::notice::底座 PostgreSQL 已存在,复用"
else
  echo "-- 首次部署底座 PostgreSQL --"
  # TODO: 把下面 init.sql 的 CREATE DATABASE 改成本服务的库名(对齐 services.yaml)
  cat <<PG | kubectl apply -n "$PREVIEW_NS" -f - 2>&1 | sed 's/^/  /'
apiVersion: v1
kind: ConfigMap
metadata: { name: postgresql-init-script, labels: { base: forum-reply-robot-foundation } }
data:
  init.sql: |
    CREATE DATABASE forum_reply_robot;
PG
  cat <<PGDEPLOY | kubectl apply -n "$PREVIEW_NS" -f - 2>&1 | sed 's/^/  /'
apiVersion: apps/v1
kind: Deployment
metadata: { name: postgresql, labels: { app: postgresql, base: forum-reply-robot-foundation } }
spec:
  replicas: 1
  strategy: { type: Recreate }
  selector: { matchLabels: { app: postgresql } }
  template:
    metadata: { labels: { app: postgresql, base: forum-reply-robot-foundation } }
    spec:
      containers:
      - name: postgresql
        image: postgres:15
        ports: [ { containerPort: 5432 } ]
        env:
        - { name: POSTGRES_PASSWORD, value: "${PG_PWD}" }
        - { name: POSTGRES_DB, value: "forum_reply_robot" }
        volumeMounts:
        - { name: init, mountPath: /docker-entrypoint-initdb.d }
        - { name: data, mountPath: /var/lib/postgresql/data }
        readinessProbe: { tcpSocket: { port: 5432 }, initialDelaySeconds: 20, periodSeconds: 5 }
        resources: { requests: { cpu: 100m, memory: 256Mi }, limits: { cpu: 1, memory: 1Gi } }
      volumes:
      - { name: init, configMap: { name: postgresql-init-script } }
      - { name: data, emptyDir: {} }
PGDEPLOY
  cat <<PGSVC | kubectl apply -n "$PREVIEW_NS" -f - 2>&1 | sed 's/^/  /'
apiVersion: v1
kind: Service
metadata: { name: ${PG_SVC}, labels: { base: forum-reply-robot-foundation } }
spec:
  selector: { app: postgresql }
  ports: [ { port: 5432, targetPort: 5432 } ]
  type: ClusterIP
PGSVC
  kubectl wait --for=condition=Available deployment/postgresql -n "$PREVIEW_NS" --timeout=180s 2>&1 | sed 's/^/  /' || echo "::warning::postgresql 未就绪,继续"
fi

get_field() {  # $1=sub $2=dot-path under subs.<sub>
  python3 - "$SERVICES_YAML" "$1" "$2" <<'PY' 2>/dev/null
import sys, subprocess
try: import yaml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], capture_output=True)
    import yaml
try: cfg=yaml.safe_load(open(sys.argv[1],encoding='utf-8')) or {}
except FileNotFoundError: sys.exit(0)
cur=(cfg.get('subs',{}) or {}).get(sys.argv[2],{}) or {}
for k in sys.argv[3].split('.'):
    cur=cur.get(k) if isinstance(cur,dict) else None
print(cur if isinstance(cur,(str,int,bool,float)) else '')
PY
}
get_top() {  # $1=dot-path under root
  python3 - "$SERVICES_YAML" "$1" <<'PY' 2>/dev/null
import sys, subprocess
try: import yaml
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pyyaml"], capture_output=True)
    import yaml
try: cfg=yaml.safe_load(open(sys.argv[1],encoding='utf-8')) or {}
except FileNotFoundError: sys.exit(0)
cur=cfg
for k in sys.argv[2].split('.'):
    cur=cur.get(k) if isinstance(cur,dict) else None
print(cur if isinstance(cur,(str,int,bool,float)) else '')
PY
}

# 3. 枚举全部子仓 + 算改动子仓
cd "$WD"
ALL_SUBS=$(git config -f .gitmodules --get-regexp path 2>/dev/null | awk '{print $2}')
if [ -z "$ALL_SUBS" ]; then
  ALL_SUBS="."
  echo "::notice::无 .gitmodules,按单体仓库处理(ALL_SUBS=.)"
fi
is_changed() {
  local p="$1"
  [ -n "$(git -C "$p" status --porcelain 2>/dev/null)" ] && return 0
  local b; b="$(git -C "$p" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null | sed 's#.*/##' || echo main)"
  [ -n "$(git -C "$p" log "origin/${b:-main}..HEAD" --oneline 2>/dev/null)" ]
}

# 4. 部署:改动子仓→issue 版;未改子仓→base 基线(首次部署,跨 issue 复用)
ROUTE_MAP=""
ANY_CHANGED=0
for sub_path in $ALL_SUBS; do
  [ -z "$sub_path" ] && continue
  if [ "$sub_path" = "." ]; then
    sub="$(basename "$WD")"
    full="$WD"
  else
    sub="$(basename "$sub_path")"
    full="$WD/$sub_path"
  fi
  repo="$(git -C "$full" config --get remote.origin.url | sed -E 's#.*github.com[:/]##; s#\.git$##')"
  settings_module="$(get_field "$sub" settings_module)"
  health_endpoint="$(get_field "$sub" health_endpoint)"; [ -z "$health_endpoint" ] && health_endpoint="/"
  db_name="$(get_field "$sub" db.name)"
  synclog="${RUNNER_TEMP:-/tmp}/_sync_${sub}.log"

  if is_changed "$sub_path"; then
    ANY_CHANGED=1
    name="${sub}-issue-${ISSUE}"; deploy_branch="$BRANCH"; skip_ing=""
    echo; echo "-- 改动子仓 $sub → $name (issue 版) --"
  else
    name="${sub}-base"; deploy_branch="main"; skip_ing="1"
    if kubectl get deploy "$name" -n "$PREVIEW_NS" >/dev/null 2>&1; then
      echo; echo "-- 未改子仓 $sub → $name 已存在,复用 --"
      ROUTE_MAP="${ROUTE_MAP}${sub}=${name};"; continue
    fi
    echo; echo "-- 未改子仓 $sub → 首次部署 base $name (main) --"
  fi

  DEPLOY_NAME="$name" DEPLOY_BRANCH="$deploy_branch" SKIP_INGRESS="$skip_ing" \
  SUB="$sub" COMMUNITY="$COMMUNITY" PREVIEW_NS="$PREVIEW_NS" ISSUE="$ISSUE" BRANCH="$BRANCH" \
  REPO="$repo" SETTINGS_MODULE="$settings_module" PG_SVC="$PG_SVC" PG_PWD="$PG_PWD" DB_NAME="$db_name" ING_DOMAIN="$ING_DOMAIN" \
  HEALTH_ENDPOINT="$health_endpoint" VAULT_ADDR="${VAULT_ADDR:-https://vault.preview.test.osinfra.cn}" \
  VAULT_USERNAME="${VAULT_USERNAME:-}" VAULT_PASSWORD="${VAULT_PASSWORD:-}" GH_TOKEN="${GH_TOKEN:-}" \
  OUT_DIR="${RUNNER_TEMP:-/tmp}/ai/test-sync" \
    bash "$HERE/test-sync/sync.sh" > "$synclog" 2>&1 || echo "::warning::$sub test-sync 非 0"
  sed 's/^/  /' "$synclog"
  ing_host="$(tail -1 "$synclog")"
  ROUTE_MAP="${ROUTE_MAP}${sub}=${name};"

  ready=true
  kubectl rollout status deployment/"$name" -n "$PREVIEW_NS" --timeout=6000s 2>&1 | sed 's/^/  /' || ready=false

  if is_changed "$sub_path"; then
    preview_url="https://${ing_host}${health_endpoint}"
    svc_port="$(get_field "$sub" port)"; [ -z "$svc_port" ] && svc_port="5000"
    python3 - "$sub" "$name" "$BRANCH" "$ready" "$PREVIEW_NS" "$preview_url" "$svc_port" > "${DEPLOY_OUT}/${sub}.json" <<'PY'
import json,sys
sub,name,branch,ready,ns,preview_url,port=sys.argv[1:8]
print(json.dumps({"sub":sub,"name":name,"service":f"{name}.{ns}.svc","port":int(port),
  "branch":branch,"ready":ready=="true",
  "clusterip_url":f"http://{name}.{ns}.svc.cluster.local:{port}","preview_url":preview_url},ensure_ascii=False))
PY
    echo "  -> ${DEPLOY_OUT}/${sub}.json (ready=$ready, preview=$preview_url)"
  fi
done

if [ "$ANY_CHANGED" = 0 ]; then echo "::notice::无改动子仓,底座+base 已保证,preview 完成"; exit 0; fi

# 5. 同步 test 路由拓扑 → 一个 issue 共享 host
ARCHIVE_REPO="$(get_top test_archive.repo)"; [ -z "$ARCHIVE_REPO" ] && ARCHIVE_REPO="${GITHUB_REPOSITORY_OWNER:-opensourceways}/infra-common"
ARCHIVE_PATH="$(get_top test_archive.path)"
ARCHIVE_REF="$(get_top test_archive.ref)"; [ -z "$ARCHIVE_REF" ] && ARCHIVE_REF="master"
if [ -n "$ARCHIVE_PATH" ] && [ -n "$ROUTE_MAP" ]; then
  echo; echo "-- 同步 test 路由拓扑 → issue 共享 host --"
  ISSUE_HOST="forum-reply-robot-issue-${ISSUE}.${ING_DOMAIN}"
  routelog="${RUNNER_TEMP:-/tmp}/_routes.log"
  PREVIEW_NS="$PREVIEW_NS" ISSUE="$ISSUE" ING_DOMAIN="$ING_DOMAIN" GH_TOKEN="${GH_TOKEN:-}" \
  ARCHIVE_REPO="$ARCHIVE_REPO" ARCHIVE_PATH="$ARCHIVE_PATH" ARCHIVE_REF="$ARCHIVE_REF" \
  ROUTE_MAP="$ROUTE_MAP" ISSUE_HOST="$ISSUE_HOST" OUT_DIR="${RUNNER_TEMP:-/tmp}/ai/test-sync" \
    bash "$HERE/test-sync/routes.sh" > "$routelog" 2>&1 || echo "::warning::routes-sync 非 0"
  sed 's/^/  /' "$routelog"
  echo "::notice::issue 共享路由 host: https://${ISSUE_HOST}/"
fi

# 网络诊断(定位 pod 连底座 PostgreSQL 超时)
echo; echo "::group::网络诊断 (postgresql 连通性)"
kubectl get ns "$PREVIEW_NS" --show-labels 2>&1 | sed 's/^/  /' || true
kubectl get endpoints "$PG_SVC" -n "$PREVIEW_NS" -o wide 2>&1 | sed 's/^/  /' || true
kubectl get networkpolicy -n "$PREVIEW_NS" 2>&1 | sed 's/^/  /' || true
kubectl get peerauthentication -A 2>&1 | sed 's/^/  /' || echo "  (无 istio CRD 或无权限)"
echo "::endgroup::"

echo; echo "::notice::forum-reply-robot preview 完成"
