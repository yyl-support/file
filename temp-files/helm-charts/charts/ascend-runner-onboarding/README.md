# ascend-runner-onboarding

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
> **openEuler 社区 Ascend NPU 资源自助开通网关服务**

将 ascend-runner-mgmt GitHub App 的安装转化为自助式 NPU runner 开发环境开通。

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 接收 GitHub App webhook 事件
* 写入 Vault 密钥
* 推送 deployment repo 和 argocd repo PR
* PR 合入后 ArgoCD 同步，用户可使用 NPU runner 标签

### 底层组件
该服务在启动和运行过程中依赖：
* **PostgreSQL**: 存储安装记录与状态
* **Redis**: 任务队列与流处理
* **Vault**: 密钥管理与 GitHub App 私钥注入

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| wuhejun | wuhejun@h-partners.com | JavaPythonAIForBAT |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| configMap.data | object | `{}` | ConfigMap 数据，包含 allowlist.yaml 和 reference-projects.yaml |
| configMap.enabled | bool | `true` | 是否渲染 ConfigMap 资源 |
| configMap.name | string | `"ascend-runner-onboarding-config"` | ConfigMap 名称 |
| env | list | `[]` | 环境变量列表，支持 value 和 valueFrom |
| global.appName | string | `"ascend-runner-onboarding"` | 服务名称 |
| global.namespace | string | `"ascend"` | 命名空间 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像仓库访问凭证名称 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceways/ascend-runner-onboarding"` | 镜像名称 |
| image.tag | string | `"latest"` | 镜像Tag |
| ingress.annotations | object | `{}` | Ingress 注解 |
| ingress.className | string | `"nginx"` | Ingress 类型 |
| ingress.enabled | bool | `false` | 是否渲染 Ingress 资源 |
| ingress.host | string | `""` | 域名 |
| initContainers | list | `[]` | 初始化容器 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.httpGet.path | string | `"/healthz"` | 请求路径 |
| livenessProbe.httpGet.port | int | `8080` | 服务端口 |
| livenessProbe.initialDelaySeconds | int | `10` | 等待容器初始化时间 |
| livenessProbe.periodSeconds | int | `15` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.timeoutSeconds | int | `5` | 超时时间设置 |
| namespace.enabled | bool | `false` | 是否渲染 Namespace 资源 |
| namespace.name | string | `"ascend"` | 命名空间名称 |
| podAnnotations | object | `{}` | Pod 注解，包含 Vault Agent 注入配置 |
| podLabels.app | string | `"ascend-runner-onboarding"` | Pod 标签 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | seccomp 本地配置文件 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | seccomp 类型 |
| readinessProbe.failureThreshold | int | `3` | 失败重试次数 |
| readinessProbe.httpGet.path | string | `"/healthz"` | 请求路径 |
| readinessProbe.httpGet.port | int | `8080` | 服务端口 |
| readinessProbe.initialDelaySeconds | int | `5` | 等待容器初始化时间 |
| readinessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| readinessProbe.successThreshold | int | `1` | 成功标志次数 |
| readinessProbe.timeoutSeconds | int | `3` | 超时时间设置 |
| replicaCount | int | `1` | Pod 副本数 |
| resources.limits.cpu | string | `"1000m"` | 服务最大使用 CPU 资源 |
| resources.limits.memory | string | `"512Mi"` | 服务最大使用内存容量 |
| resources.requests.cpu | string | `"200m"` | 容器运行所需 CPU 资源 |
| resources.requests.memory | string | `"256Mi"` | 容器运行所需内存资源 |
| secret.ca_crt_key | string | `""` | Secret 中 CA 证书的键名 |
| secret.enable | bool | `false` | 是否渲染 TLS Secret 资源 |
| secret.name | string | `""` | TLS Secret 名称 |
| secret.path | string | `""` | Secret 在 Vault 中存放路径 |
| secret.tls_crt_key | string | `""` | Secret 中 TLS 证书的键名 |
| secret.tls_key_key | string | `""` | Secret 中 TLS 私钥的键名 |
| secretDefinitions | object | `{}` | SecretDefinition 配置，从 Vault 拉取密钥 |
| securityContext.allowPrivilegeEscalation | bool | `false` | 是否允许权限提升 |
| securityContext.capabilities.drop | list | `["ALL"]` | 丢弃的 Linux 能力 |
| securityContext.runAsUser | int | `1000` | 容器运行用户 ID |
| service.port | int | `8080` | Service 对外端口 |
| service.portName | string | `"http"` | 端口名 |
| service.targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | Service 类型 |
| serviceAccount.automount | bool | `false` | 是否自动挂载 SA |
| serviceAccount.create | bool | `true` | 是否渲染 SA 资源 |
| serviceAccount.name | string | `"ascend"` | SA 名称 |
| strategy.rollingUpdate.maxSurge | int | `1` | 更新时最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 更新时最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumeMounts | list | `[]` | 卷挂载配置 |
| volumes | list | `[]` | 卷配置 |

## 变更历史

## 1.0.0 - 2026-06-11

### 说明
- 初始版本发布
