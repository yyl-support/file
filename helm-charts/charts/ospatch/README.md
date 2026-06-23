# ospatch

## 📖 服务介绍 (Service Overview)
A Helm chart for ospatch service

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 补丁管理服务，提供补丁的分发和管理能力。

### 底层组件
该服务在启动和运行过程中依赖：
* **vault**: [挂载服务所需的配置文件]

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| caozhi | george.cao@huawei.com   | GeorgeCao-hw |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| nameOverride | string | `""` | 服务名 |
| fullnameOverride | string | `"ospatch-backend"` | 服务名 |
| namespace.enabled | bool | `false` | 可选,创建命名空间资源 |
| namespace.name | string | `"patch-manager"` | 命名空间 |
| replicaCount | int | `1` | 副本数 |
| imagePullSecrets[0].name | string | `"huawei-swr-instance-image-pull-secret"` | 镜像拉取密钥 |
| serviceAccount.create | bool | `false` | 创建sa |
| serviceAccount.name | string | `"patch-manager"` | sa资源名 |
| serviceAccount.automount | bool | `false` | 取消自动挂载sa token |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/role" | string | `"patch-manager"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` | vault agent初始化容器优先启动 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 容器挂载卷名 |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志打印等级 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-config.yaml" | string | `"{{- with secret \"internal/data/infra-test/patch-manager\" -}}  \n{{ .Data.data.config }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret" | string | `"internal/data/infra-test/patch-manager"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/app/config"` | 配置文件挂载路径 |
| deployment.name | string | `"ospatch-backend"` | 部署名称 |
| deployment.annotations | object | `{}` | 部署注解 |
| deployment.strategy.type | string | `"RollingUpdate"` | 更新策略 |
| deployment.strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| deployment.strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本上限数 |
| deployment.image.repository | string | `"opensourceways-w5peto.swr-pro.myhuaweicloud.com/opensourceways/patch-manager-backend"` | 镜像名 |
| deployment.image.tag | string | `"latest"` | 镜像tag |
| deployment.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| deployment.resources.requests.cpu | string | `"250m"` | 容器资源配置 |
| deployment.resources.requests.memory | string | `"256Mi"` | 容器资源配置 |
| deployment.resources.limits.cpu | string | `"500m"` | 容器资源配置 |
| deployment.resources.limits.memory | string | `"512Mi"` | 容器资源配置 |
| deployment.securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| deployment.securityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| deployment.securityContext.runAsUser | int | `1000` | 容器运行用户id |
| deployment.initContainers | array | `[]` | 初始化容器配置 |
| deployment.readinessProbe.httpGet.path | string | `"/readyz"` | 就绪检查接口 |
| deployment.readinessProbe.httpGet.port | int | `8080` | 就绪检查端口号 |
| deployment.readinessProbe.initialDelaySeconds | int | `5` | 就绪检查初始延迟 |
| deployment.readinessProbe.periodSeconds | int | `10` | 就绪检查周期 |
| deployment.readinessProbe.timeoutSeconds | int | `5` | 就绪检查超时时间 |
| deployment.readinessProbe.failureThreshold | int | `3` | 就绪检查失败阈值 |
| deployment.livenessProbe.httpGet.path | string | `"/healthz"` | 健康检查接口 |
| deployment.livenessProbe.httpGet.port | int | `8080` | 健康检查端口号 |
| deployment.livenessProbe.initialDelaySeconds | int | `10` | 健康检查初始延迟 |
| deployment.livenessProbe.periodSeconds | int | `15` | 健康检查周期 |
| deployment.livenessProbe.timeoutSeconds | int | `5` | 健康检查超时时间 |
| deployment.livenessProbe.failureThreshold | int | `3` | 健康检查失败阈值 |
| deployment.service.name | string | `"http"` | 端口名 |
| deployment.service.port | int | `8080` | 端口号 |
| deployment.service.targetPort | int | `8080` | 容器监听端口号 |
| deployment.service.type | string | `"ClusterIP"` | service类型 |
| deployment.service.annotations | object | `{}` | service注解 |
| deployment.volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| deployment.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| deployment.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| deployment.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| ingress.enabled | bool | `false` | 是否启用ingress |
| ingress.host | string | `"ospatch.test.osinfra.cn"` | 域名 |
| ingress.serviceName | string | `"ospatch-backend"` | 服务名称 |
| ingress.serviceNumber | int | `8080` | 服务端口号 |
| ingress.annotations | object | `{}` | ingress注解 |
| ingress.paths[0].path | string | `"/"` | 路径 |
| ingress.paths[0].pathType | string | `"Prefix"` | 路径类型 |
| ingress.tlsSecrets.enabled | bool | `false` | 是否启用TLS |
| ingress.tlsSecrets.name | string | `"domain-tls"` | TLS密钥名称 |
| ingress.tlsSecrets.path | string | `"secrets/data/patch-manager/domain-tls"` | TLS密钥在vault中存放路径 |
| ingress.tlsSecrets.certKey | string | `"tls.cert"` | 证书key |
| ingress.tlsSecrets.keyKey | string | `"tls.key"` | 私钥key |
| autoscale.enabled | bool | `true` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 8 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |
| autoscale.timezone | string | `"Asia/Shanghai"` | 时区 |
| autoscale.targetRef | string | `""` | 伸缩目标引用 |

## 变更历史

## 1.0.0 - 2026-06-09

### 说明
- 初始版本发布
