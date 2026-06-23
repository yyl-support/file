# helm-charts 与 helm-chart-value 说明

本文档沉淀对 `helm-charts/` 和 `helm-chart-value/` 两个目录的分析，以及新增 service 的操作方法。

## 一、整体关系

这是 Helm 部署中典型的 **"chart 模板" 与 "values 配置" 分离** 结构：

- `helm-charts/` —— Chart 定义（可复用的部署模板，定义"怎么部署"）
- `helm-chart-value/` —— 部署配置（每个部署实例的具体取值，定义"用什么值部署"）

`helm-chart-value` 里的 values 在部署时**喂给** `helm-charts` 里同名的 chart，组合后生成最终的 K8s 资源。

部署示例：

```bash
helm install <release> helm-charts/charts/discourse \
  -f helm-chart-value/openeuler/discourse/test/values.yaml
```

证据：`helm-chart-value/openeuler/discourse/test/values.yaml` 第 1 行为 `#ChartVersion: 1.0.8`（指向 chart 版本），其 `replicaCount` / `image` / `serviceAccount` 等字段正是 `helm-charts/charts/discourse/templates` 所消费的变量。

## 二、helm-charts/ —— Chart 定义（模板/包）

- 根目录：`README.md`（"Saved charts for all our services"）、`.gitignore`、`.github/`（CI）、`charts/`
- `charts/` 下是约 45 个独立 Helm chart，每个对应一个服务。
- 每个 chart 通常包含：
  - `Chart.yaml`（chart 元数据）
  - `templates/`（deployment / service / ingress / sa / secret / autoscaler 等 K8s 资源模板）
  - 部分含 `values.yaml`（默认值）、`README.md`、`crds/` 等

### 现有 chart 列表

```
api-autotest          apig-discovery        ascend-runner-onboarding
audit-server          auth-center           coder
community-sig-monitor  community-summary     community-website
consul                cve-defect            cve-manager
cve-manager-ng        cvesa-test            dapr
discourse             doc-search            easywhisperx
etherpad              hotopic               image-scanning
infra-radar           libcoder              lightrag
log-scan              mail                  meeting
message-center        multi-docs-website    neo4j
om-collection        om-webserver          oneid-workbench
openjiuwen           osi-task              ospatch
patchwork            repo                  rm-check
robot                signatrust            sync-model
unifiedbus           vulnerability
```

### 模板约定（以 doc-search 为例）

本仓库 chart 模板使用较扁平的 values key。`charts/doc-search/templates/deployment.yaml` 用到的字段示例：

- `.Values.appName` / `.Values.namespace` / `.Values.replicaCount`
- `.Values.image.repository` / `.image.tag` / `.image.pullPolicy`
- `.Values.serviceAccount.name` / `.Values.imagePullSecret`
- `.Values.deploymentLabels` / `.Values.podAnnotations` / `.Values.strategy`
- `.Values.resources` / `.readinessProbe` / `.livenessProbe`
- `.Values.containerSecurityContext` / `.podSecurityContext`
- `.Values.volumeMounts` / `.Values.volumes` / `.Values.env` / `.Values.configPath`

`Chart.yaml` 示例（doc-search）：

```yaml
apiVersion: v2
appVersion: 0.1.0
description: A Helm chart for doc-search
name: doc-search
type: application
version: 1.0.3
```

## 三、helm-chart-value/ —— 部署配置（values）

三层目录结构：**社区/租户 → 应用 → 环境**

- 第一层（社区/产品）：`cann`、`common`、`hifloat`、`hpckit`、`mindspore`、`openeuler`、`openfuyao`、`opengauss`、`openjiuwen`、`openpangu`、`openubmc`、`unifiedbus`
- 第二层（应用名）：`discourse`、`mail`、`meeting`、`robot`、`website`、`etherpad`、`neo4j` 等，**与 `helm-charts/charts/` 下的 chart 同名**
- 第三层（环境）：`prod`、`test`（也有 `prod-v2`、`prod-atom`、`prod-turbo`、`test-02` 等变体），内含 `values.yaml`

部分应用除 `values.yaml` 外还有配套文件，例如：

- robot：`values-configmaps.yaml`
- mail：`values-configmap.yaml`
- server 类（如 unifiedbus/server）：多份 `values-*.yaml`（values-base / values-server / values-captcha 等）
- 部分应用有 `values-base.yaml` 作为公共基线

## 四、如何新增一个 service

### 情况 A：服务类型已有 chart（最常见）

给某社区新部署一个已存在的应用时，**不动 `helm-charts`**，只在 `helm-chart-value` 加配置：

1. 建目录 `helm-chart-value/<社区>/<应用>/<环境>/`（环境一般是 `prod`、`test`）
2. 放 `values.yaml`，照抄同应用其它社区的 values 改值（镜像 tag、namespace、域名、副本数、Vault 路径等）
3. 如该应用有配套文件（`values-configmaps.yaml` / `values-configmap.yaml` / 多份 `values-*.yaml`），参照已有同应用目录一并补齐

### 情况 B：全新类型的服务（仓库无同名 chart）

需要先建 chart，再建 values：

**第 1 步 —— 在 `helm-charts/charts/<服务名>/` 建 chart**

- `Chart.yaml`（参照 doc-search：`apiVersion: v2`、`name`、`version`、`type: application`）
- `templates/` 下放需要的 K8s 资源，沿用本仓库扁平 values key 约定
- 常见资源组合：`deployment.yaml`、`service.yaml`、`ingress.yaml`、`sa.yaml`、`secret.yaml`、`autoscaler.yaml`
- 最快做法：复制一个最接近的现有 chart 再改名/改内容

**第 2 步 —— 在 `helm-chart-value/<社区>/<服务名>/<环境>/values.yaml` 建配置**，填上模板里用到的所有 key。

### 部署

```bash
helm install <release> helm-charts/charts/<服务名> \
  -f helm-chart-value/<社区>/<服务名>/<环境>/values.yaml
```
