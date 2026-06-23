# issue-921 RAG 对外域名开放方案（单 pod + ingress）

> 关联：backlog#921「openUBMC社区RAG支持对外查询接口」（OPEN）；已并入 main 的 PR #114、#130。
>
> **本次决策（最终）**：
> 1. 新域名统一命名为 **`lightrag.test.osinfra.cn`**（测试环境）。
> 2. 对外暴露走 **nginx Ingress** 那套逻辑（不走 istio VirtualService）。
> 3. **单 pod、零代码改动**：复用现有 forum-robot pod（其 `main.py` 默认已在 5000 提供 `/api/v1/rag/*`，`external_api.enabled` 默认 true），只给它加 Service + Ingress；**不新增独立 RAG pod、不改 forum-reply-robot 代码**。
>
> 说明：曾评估过"独立 RAG-only pod"方案（隔离更好，但需在 `main.py` 加 RAG-only 运行模式以跳过 ForumMonitor / lightrag 全量初始化），已放弃以避免代码改动。RAG 知识库在外部 LightRAG 服务（`retrieval.base_url`，现有 pod 已配好），单 pod 方案对后端无任何改动。

---

## 1. 背景

issue-921 给 forum-reply-robot 增加了一套对外 RAG 查询接口（`/api/v1/rag/*`：OIDC 授权码登录 authorize/callback/refresh、retrieve、tokenize、knowledge/upload、health），跑在 forum-robot 容器的 **5000 端口**。代码已合入，但**没有任何对外通路**（无 Service、无 Ingress、无域名），导致无法联调验收。

本方案解决：注册并开放对外域名 `lightrag.test.osinfra.cn`，把 RAG 接口通过 nginx Ingress 暴露到 forum-robot:5000。

---

## 2. 三者关系（forum-reply-robot / helm-charts / helm-chart-value）

forum-reply-robot 不是 `robot` chart，而是被 **`discourse` chart** 顺带部署的：

```
forum-reply-robot (代码工程)
   │ 构建成镜像 forum-robot
   ▼
helm-charts/charts/discourse/templates/robot.yaml      ← 模板（怎么部署）
   │ 容器 forum-robot，端口 5000，/health；RAG API 也在这 5000
   ▼
helm-chart-value/openeuler/discourse/{test,prod}/values.yaml ← 取值（部署成什么样）
      robot:
        enabled: true
        image: swr.../opensourceway/forum-robot:<tag>
        podLabels: { app: forum-robot }
```

| 角色 | 位置 | 职责 |
| --- | --- | --- |
| **helm-charts** | `charts/discourse/templates/`（`robot.yaml` / `service.yaml` / `ingress.yaml` / `istio.yaml`） | 部署模板。robot 本体 + 网络暴露的模板 |
| **helm-chart-value** | `openeuler/discourse/{test,prod}/values.yaml` 的 `robot:`、`ingress`、`istio` 段 | 具体取值：镜像、副本、域名、TLS |
| **forum-reply-robot** | 独立代码仓库 → `forum-robot` 镜像 | 业务逻辑；域名最终把流量送到它的 5000 |

证据：`discourse/templates/robot.yaml:29`（容器 `forum-robot`）、`:44`（5000 探针）；`openeuler/discourse/test/values.yaml:203-271`（`robot:` 段、镜像 `forum-robot`，含已配好的 RAG `service`/`ingress`）。

---

## 3. 现状 gap（必须先补 chart 能力）

1. **robot 没有 Service**：`discourse/templates/service.yaml` 只建了 `web-server` Service（指向 discourse 网站 8080）；`robot.yaml` 只建 Deployment，**没有 Service 指向 forum-robot:5000**。
2. **ingress 模板与 robot 无关**：`discourse/templates/ingress.yaml` 后端写死 `web-server:8080`、单 host（`ingress.host`）。无法直接复用来暴露 robot。
3. 现网 discourse web 用的是 istio（`istio.enabled: true`），`ingress.enabled: false`。本方案为 RAG **单独新增一套 nginx Ingress**，与现有 istio 并存、互不影响。

> 结论：要开放 RAG 对外域名，**先给 `discourse` chart 补两块模板（robot Service + robot Ingress），再在 openeuler 的 discourse values 里配 `lightrag.test.osinfra.cn`**。

---

## 4. 改造方案

### 4.1 chart 改造（helm-charts/charts/discourse/templates/）

#### 4.1.1 新增 `robot-service.yaml`

```yaml
{{- with .Values.robot }}
{{- if .enabled }}
{{- if .service }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "discourse.fullname" $ }}-robot
  namespace: {{ $.Values.namespace.name }}
  labels:
    {{- include "discourse.labels" $ | nindent 4 }}
spec:
  type: {{ .service.type | default "ClusterIP" }}
  ports:
    - name: {{ .service.portName | default "http" }}
      port: {{ .service.port }}
      targetPort: {{ .service.targetPort }}
      protocol: TCP
  selector:
    {{- toYaml .podLabels | nindent 4 }}
{{- end }}
{{- end }}
{{- end }}
```

#### 4.1.2 新增 `robot-ingress.yaml`

```yaml
{{- with .Values.robot }}
{{- if .enabled }}
{{- if and .ingress .ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .ingress.name }}
  namespace: {{ $.Values.namespace.name }}
  {{- with .ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {{ .ingress.host }}
      secretName: {{ .ingress.secretName }}
  rules:
    - host: {{ .ingress.host }}
      http:
        paths:
          - path: {{ .ingress.path | default "/" }}
            pathType: {{ .ingress.pathType | default "Prefix" }}
            backend:
              service:
                name: {{ include "discourse.fullname" $ }}-robot
                port:
                  number: {{ .service.port }}
{{- end }}
{{- end }}
{{- end }}
```

> 说明：`path: /` 即覆盖 `/api/v1/rag/*`（含 OIDC 回调 `/api/v1/rag/auth/callback`）。

### 4.2 value 配置（helm-chart-value/openeuler/discourse/**test**/values.yaml）

> `lightrag.test.osinfra.cn` 是**测试域名**，配置加在 openeuler 的 **test** values 文件 `test/values.yaml` 里。
>
> **当前状态：已完成**。该段已写入 `openeuler/discourse/test/values.yaml:255-271`（与下方模板一致）。

在 `robot:` 段内新增 `service` 与 `ingress`：

```yaml
robot:
  enabled: true
  # ...（既有 image / replicaCount / podLabels: { app: forum-robot } 等保持不变）
  service:
    type: ClusterIP
    portName: http
    port: 5000
    targetPort: 5000
  ingress:
    enabled: true
    name: forum-robot-rag-ingress
    host: lightrag.test.osinfra.cn
    path: /
    pathType: Prefix
    secretName: lightrag-rag-tls
    annotations:
      nginx.ingress.kubernetes.io/proxy-body-size: "20m"   # knowledge/upload 需放大请求体
      # 注意：forum-robot 是明文 HTTP:5000，切勿设置 backend-protocol: HTTPS
```

---

## 5. 域名一致性（以 lightrag.test.osinfra.cn 为唯一口径）

| 位置 | 当前值 | 处理 |
| --- | --- | --- |
| `config/config.yaml` `redirect_uri` | `https://lightrag.test.osinfra.cn/api/v1/rag/auth/callback` | **已一致**，无需改（实际由 Vault `internal/data/infra-test/openeuler-discourse` 的 `robotConf` 注入，确认 Vault 里也是此值） |
| `Issue-921-测试命令.md` 网关地址 | `rag.test.osinfra.cn` | 改为 `lightrag.test.osinfra.cn` |
| 单测 `tests/test_*.py` 夹具 | `rag.openubmc.cn` | 测试夹具，可选对齐（不影响线上） |
| 新 ingress `host` / TLS | — | 新增为 `lightrag.test.osinfra.cn` |

---

## 6. 开放新域名完整步骤清单

### 阶段 0 · 决策（已定）
- [x] 域名：`lightrag.test.osinfra.cn`
- [x] 暴露方式：nginx Ingress（`ingressClassName: nginx`）
- [ ] 谁注册/解析 DNS、谁签发证书（待落实到运维或本人）

### 阶段 1 · DNS 与证书
- [ ] 注册/解析 `lightrag.test.osinfra.cn`，指向 nginx ingress 入口
- [ ] 准备 TLS 证书 → 在目标 namespace（`discourse`）创建 Secret `lightrag-rag-tls`（或用现有 `*.osinfra.cn` 通配证书）

### 阶段 2 · chart 改造（helm-charts/charts/discourse）
- [ ] 新增 `templates/robot-service.yaml`（见 4.1.1）
- [ ] 新增 `templates/robot-ingress.yaml`（见 4.1.2）
- [ ] `helm template` 本地渲染校验，确认生成 robot Service + Ingress 且后端指向 `<fullname>-robot:5000`

### 阶段 3 · value 配置（helm-chart-value/openeuler/discourse/test）
- [x] 在 `robot:` 段加 `service` + `ingress`（见 4.2）— 已写入 `openeuler/discourse/test/values.yaml:255-271`

### 阶段 4 · OneID 与应用配置
- [ ] OneID 应用注册回调 `redirect_uri = https://lightrag.test.osinfra.cn/api/v1/rag/auth/callback`
- [ ] 确认 Vault `robotConf` 中 `redirect_uri` 为该值

### 阶段 5 · 联调与验收（对照 `Issue-921-测试命令.md`，地址换成新域名）
- [ ] `curl https://lightrag.test.osinfra.cn/health`
- [ ] 浏览器走 authorize → OneID → callback 拿 token
- [ ] retrieve / tokenize 正常
- [ ] 无 token → 401；非授权角色 upload → 403；连续 101 次 → 429
- [ ] 若前置 CloudWAF，把联调来源 IP 加白名单

---

## 7. 风险与注意

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| forum-robot 监听地址 | 应用绑定自动探测的内网私有 IP（优先 10. 段）而非 0.0.0.0 | k8s pod IP 通常为 10.x，现有 5000 探针（httpGet）已工作即说明 podIP:5000 可达 → Service 可路由；若不通需改应用绑定 0.0.0.0 |
| backend-protocol | discourse web 用 `backend-protocol: HTTPS`(8080 TLS)；robot 是明文 HTTP | robot ingress **不要**设 HTTPS，用默认 HTTP |
| 请求体大小 | knowledge/upload 传文件 | ingress 设 `proxy-body-size` 放大 |
| 与 istio 共存 | discourse web 走 istio，RAG 走 nginx ingress | 两套独立、host 不同，互不影响 |
| 测试 vs 正式 | 本次仅开测试域名 | 上线再按同模式加 prod 域名（如 `rag.openubmc.cn`）到 prod values |
