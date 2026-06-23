#!/usr/bin/env bash
# test-sync —— 把 test 环境的真实部署形态同步成预览形态,部署一个改动子仓
# =========================================================================
# 由 backlog/.ai-flow/scripts/gen-preview-hook.sh 生成,模板 = meeting-server 实测实现。
# 流程:service.md 查 (SUB, test, COMMUNITY) vault path → userpass 读 Vault →
#       改预览形态(DB 块指向底座 / DEBUG=true / 域名替换)→ 烘 k8s Secret 挂 /vault/secrets/ →
#       runtime-clone pod 现拉 issue 分支跑 → rollout restart。
set -uo pipefail

SUB="${SUB:?SUB required}"
COMMUNITY="${COMMUNITY:-openeuler}"
PREVIEW_NS="${PREVIEW_NS:?PREVIEW_NS required}"
ISSUE="${ISSUE:?ISSUE required}"
BRANCH="${BRANCH:?BRANCH required}"
REPO="${REPO:?REPO required}"
SETTINGS_MODULE="${SETTINGS_MODULE:-}"
PG_SVC="${PG_SVC:-postgresql-service}"
PG_PWD="${PG_PWD:-preview}"   # set -u 下必须有默认,避免 unbound 让 DB 改写空跑
ING_DOMAIN="${ING_DOMAIN:-preview.test.osinfra.cn}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/}"
VAULT_ADDR="${VAULT_ADDR:-https://vault.preview.test.osinfra.cn}"
OUT_DIR="${OUT_DIR:-${RUNNER_TEMP:-/tmp}/ai/test-sync}"
mkdir -p "$OUT_DIR"
NAME="${DEPLOY_NAME:-${SUB}-issue-${ISSUE}}"
EFFECTIVE_BRANCH="${DEPLOY_BRANCH:-$BRANCH}"
SKIP_INGRESS="${SKIP_INGRESS:-}"
HOSTPATH="github.com/${REPO}.git"

echo "::group::test-sync $SUB (community=$COMMUNITY ns=$PREVIEW_NS)"

# 1. service.md 查 (REPO, test, COMMUNITY) 的 vault path / 归档 / test ns
SVC_MD="$OUT_DIR/service.md"
curl -fsSL -H "Authorization: token ${GH_TOKEN:-}" \
  "https://raw.githubusercontent.com/${GITHUB_REPOSITORY_OWNER:-opensourceways}/infrastructure/main/service.md" -o "$SVC_MD" 2>/dev/null \
  || curl -fsSL "https://raw.githubusercontent.com/${GITHUB_REPOSITORY_OWNER:-opensourceways}/infrastructure/main/service.md" -o "$SVC_MD" 2>/dev/null || true
LINE="$(python3 - "$SVC_MD" "$REPO" "$COMMUNITY" <<'PY'
import sys
md, repo, community = sys.argv[1], sys.argv[2], sys.argv[3]
try: lines = open(md, encoding='utf-8').read().splitlines()
except FileNotFoundError: sys.exit(0)
best=None
for ln in lines:
    if not ln.startswith('|'): continue
    cols=[c.strip() for c in ln.strip().strip('|').split('|')]
    if len(cols)<11: continue
    # col[1]=环境 col[4]=镜像构建源码仓 col[5]=Vault Path(含社区名)
    if cols[1]!='test': continue
    if repo not in cols[4]: continue
    if community in cols[5]: best=cols; break
    if best is None: best=cols
if not best: sys.exit(0)
print('\t'.join([best[5], best[6], best[10]]))  # vault_path, vault_keys, test_ns
PY
)"
VAULT_PATH="$(echo "$LINE" | cut -f1)"
if [ -z "$VAULT_PATH" ]; then
  echo "::error::service.md 没找到 ($REPO, test, $COMMUNITY) 部署记录"; echo "::endgroup::"; exit 1
fi
echo "  vault_path=$VAULT_PATH"

# 2. Vault userpass 登录 + 读配置
VTOKEN=""
if [ -n "${VAULT_USERNAME:-}" ] && [ -n "${VAULT_PASSWORD:-}" ]; then
  VTOKEN="$(curl -s --max-time 20 -X POST "${VAULT_ADDR%/}/v1/auth/userpass/login/${VAULT_USERNAME}" \
    -d "{\"password\":\"${VAULT_PASSWORD}\"}" 2>/dev/null | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("auth",{}).get("client_token","") or "")
except Exception: print("")' 2>/dev/null || true)"
fi
[ -z "$VTOKEN" ] && echo "::warning::Vault 登录失败(login 200 read 403=policy 没授权读 internal/data/infra-test/<svc>,找 ops)"
VAULT_JSON=""
if [ -n "$VTOKEN" ]; then
  VAULT_JSON="$(curl -s --max-time 20 -H "X-Vault-Token: $VTOKEN" "${VAULT_ADDR%/}/v1/${VAULT_PATH}" 2>/dev/null || true)"
fi

# 3. 改造成预览形态 + 落地文件
# TODO(服务定制): 把 Vault data 的 key 名映射到 pod 期望的文件名(对齐 test 的 vault inject)。
#   meeting-platform 例: {"platformconfig":"secrets.yaml","platformconfig02":"config","MysqlCA":"ca.pem",...}
#   第一次跑看日志 "vault data keys:" 列出真实 key 名后填这里。
SECRET_DIR="$OUT_DIR/${SUB}-secrets"; rm -rf "$SECRET_DIR"; mkdir -p "$SECRET_DIR"
python3 - "$VAULT_JSON" "$SUB" "$SECRET_DIR" "$PG_SVC" "$PREVIEW_NS" "$ING_DOMAIN" "$PG_PWD" "${DB_NAME:-}" <<'PY'
import json, sys, os, re
vault_json, sub, out, pg_svc, ns, ing_domain, pg_pwd, db_name = sys.argv[1:9]
try: import yaml
except ImportError: yaml=None
try: data = json.loads(vault_json)["data"]["data"]
except Exception: data = {}
# TODO: 按本服务的 Vault key → 文件名填映射;secrets.yaml=DB 块配置, config=app config
mapping = {"robotConf":"config"}
DB_HOST = "%s.%s.svc.cluster.local" % (pg_svc, ns)
def rewrite_secrets(content):
    # database 块全套改写指向底座:host/port/user/password/database(只改 host 不够,见 README 坑 4)
    if yaml:
        try:
            doc = yaml.safe_load(content)
            if isinstance(doc, dict) and isinstance(doc.get("database"), dict):
                doc["database"].update({"host":DB_HOST,"port":5432,"user":"postgres","password":pg_pwd})
                if db_name: doc["database"]["database"]=db_name
                return yaml.safe_dump(doc, allow_unicode=True, default_flow_style=False)
        except Exception: pass
    # YAML 回退 regex：改写 host + database name（PyYAML 不可用时保底）
    # 注：database: 是 YAML 顶层 key；缩进的   database: 是嵌套的数据库名
    c = re.sub(r'(?im)^(\s*host\s*:\s*).*$', r'\g<1>%s' % DB_HOST, content)
    if db_name:
        c = re.sub(r'(?im)^(\s+database\s*:\s*).*$', r'\g<1>%s' % db_name, c)
    return c
def rewrite_config(content):
    # 域名替换 .test.osinfra.cn → .preview.test.osinfra.cn
    # 但排除外部依赖域名（LightRAG 已存在测试环境域名，用户要求不修改）
    # 保留: lightrag-cn4.test.osinfra.cn
    lines = content.split('\n')
    result = []
    for line in lines:
        # LightRAG retrieval.base_url 不替换（用户明确要求使用已存在测试环境域名）
        if 'lightrag-cn4.test.osinfra.cn' in line or 'retrieval' in line.lower():
            result.append(line)
        else:
            # 其他域名替换（如 OIDC redirect_uri）
            result.append(line.replace('.test.osinfra.cn', '.'+ing_domain))
    return '\n'.join(result)
written=[]
for k,fn in mapping.items():
    if k not in data: continue
    v = data[k]
    if isinstance(v, str):
        if fn=="secrets.yaml": v=rewrite_secrets(v)
        elif fn=="config":
            v=rewrite_secrets(v)
            v=rewrite_config(v)
    open(os.path.join(out,fn),'w',encoding='utf-8').write(v if isinstance(v,str) else json.dumps(v))
    written.append(fn)
print("  vault data keys:", ",".join(sorted(data.keys())) if data else "(空 — vault 读取失败)")
print("  rendered:", ",".join(written) if written else "(none — 填 mapping 后才会烘 Secret)")
PY

# 4. 建 k8s Secret(从烘出来的文件)
SECRET_NAME="${NAME}-config"
if ls "$SECRET_DIR"/* >/dev/null 2>&1; then
  kubectl create secret generic "$SECRET_NAME" -n "$PREVIEW_NS" \
    $(for f in "$SECRET_DIR"/*; do echo --from-file="$(basename "$f")=$f"; done) \
    --dry-run=client -o yaml | kubectl apply -n "$PREVIEW_NS" -f - 2>&1 | sed 's/^/  /' || true
else
  kubectl create secret generic "$SECRET_NAME" -n "$PREVIEW_NS" --dry-run=client -o yaml \
    | kubectl apply -n "$PREVIEW_NS" -f - >/dev/null 2>&1 || true
fi

# 5. 渲染 Deployment(runtime-clone)+ Service + Ingress
ING_HOST="${NAME}.${ING_DOMAIN}"
CLONE_SECRET="${NAME}-clone"
kubectl create secret generic "$CLONE_SECRET" -n "$PREVIEW_NS" \
  --from-literal=token="${GH_TOKEN:-}" --dry-run=client -o yaml \
  | kubectl apply -n "$PREVIEW_NS" -f - >/dev/null 2>&1 || true

# forum-reply-robot 是 Flask 应用(pip + python main.py),端口 5000。
#   Go/Node 子仓换 base image + 启动命令(如 golang:1.24-bookworm / node:20)。
cat > "$OUT_DIR/${SUB}.yaml" <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${NAME}
  namespace: ${PREVIEW_NS}
  labels: { app: preview, repo: ${SUB}, issue: "${ISSUE}" }
spec:
  replicas: 1
  progressDeadlineSeconds: 3600
  strategy: { type: Recreate }
  selector: { matchLabels: { app: preview, repo: ${SUB}, issue: "${ISSUE}" } }
  template:
    metadata: { labels: { app: preview, repo: ${SUB}, issue: "${ISSUE}" } }
    spec:
      automountServiceAccountToken: false
      containers:
      - name: ${SUB}
        image: python:3.9-slim
        imagePullPolicy: IfNotPresent
        env:
        - { name: TZ, value: Asia/Shanghai }
        - { name: BRANCH, value: "${EFFECTIVE_BRANCH}" }
        - { name: REPO_HOSTPATH, value: "${HOSTPATH}" }
        - { name: CONFIG_PATH, value: /vault/secrets/config }
        - { name: PREVIEW_ENV, value: "true" }
        ports:
        - containerPort: 5000
        command: [/bin/bash, -c]
        args:
        - |
          set -e
          apt-get update -qq && apt-get install -y -qq git gcc libpq-dev >/dev/null 2>&1 || true
          TOK="\$(cat /run/secrets/clone/token 2>/dev/null || true)"
          CLONE_URL="https://x-access-token:\${TOK}@\${REPO_HOSTPATH}"
          # BRANCH 传入的是 issue-N 前缀,真实 dev 分支是 issue-N-from-<base>;
          # 用前缀匹配解析真实分支(与 backlog deployer/preview-pod.yaml 同一套),解析不到才原样克隆。
          REF="\$(git ls-remote --heads "\$CLONE_URL" "refs/heads/\${BRANCH}-from-*" 2>/dev/null | sed -E 's#.*refs/heads/##' | head -n 1 || true)"
          [ -z "\$REF" ] && REF="\$(git ls-remote --heads "\$CLONE_URL" "refs/heads/\${BRANCH}-impl*" 2>/dev/null | sed -E 's#.*refs/heads/##' | head -n 1 || true)"
          [ -z "\$REF" ] && REF="\$BRANCH"
          echo "preview clone: BRANCH=\$BRANCH -> 真实分支 ref=\$REF"
          git clone --depth 1 --branch "\$REF" "\$CLONE_URL" /tmp/app
          cd /tmp/app
          cp /vault/secrets/config config/config.yaml
          pip install --no-cache-dir -r requirements.txt
          exec python main.py
        readinessProbe:
          tcpSocket: { port: 5000 }
          initialDelaySeconds: 600
          periodSeconds: 10
          failureThreshold: 60
        resources:
          requests: { cpu: 250m, memory: 512Mi }
          limits: { cpu: 2, memory: 2Gi }
        volumeMounts:
        - { name: vault-secrets, mountPath: /vault/secrets, readOnly: true }
        - { name: clone-token, mountPath: /run/secrets/clone, readOnly: true }
      volumes:
      - name: vault-secrets
        secret: { secretName: ${SECRET_NAME} }
      - name: clone-token
        secret: { secretName: ${CLONE_SECRET}, optional: true }
---
apiVersion: v1
kind: Service
metadata:
  name: ${NAME}
  namespace: ${PREVIEW_NS}
  labels: { app: preview, repo: ${SUB}, issue: "${ISSUE}" }
spec:
  type: ClusterIP
  selector: { app: preview, repo: ${SUB}, issue: "${ISSUE}" }
  ports:
  - { name: http, port: 5000, targetPort: 5000, protocol: TCP }
YAML

if [ -z "$SKIP_INGRESS" ]; then
cat >> "$OUT_DIR/${SUB}.yaml" <<YAML
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${NAME}
  namespace: ${PREVIEW_NS}
  labels: { app: preview, repo: ${SUB}, issue: "${ISSUE}" }
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  ingressClassName: nginx
  rules:
  - host: ${ING_HOST}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service: { name: ${NAME}, port: { number: 5000 } }
YAML
fi

echo "  apply $OUT_DIR/${SUB}.yaml"
kubectl apply -n "$PREVIEW_NS" -f "$OUT_DIR/${SUB}.yaml" 2>&1 | sed 's/^/  /' || echo "::warning::$SUB apply 失败"
# Secret 变了但 Deployment 没变 → apply no-op → 老 pod 不重挂 → 必须 rollout restart(坑 2)
kubectl rollout restart deployment/"$NAME" -n "$PREVIEW_NS" 2>&1 | sed 's/^/  /' || true
echo "::endgroup::"
echo "$ING_HOST"
