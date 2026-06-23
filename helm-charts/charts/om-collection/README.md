# omcollection

![Version: 1.0.5](https://img.shields.io/badge/Version-1.0.5-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for om collection

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能

### 底层组件

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
|  |  |  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| autoscaling.enabled | bool | `false` | 启用弹性伸缩 |
| collectData.containerSecurityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| collectData.containerSecurityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| collectData.containerSecurityContext.runAsUser | int | `1001` | 容器运行用户id |
| collectData.enabled | bool | `false` | 启用collecdata 容器 |
| collectData.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/om/om-collection"` | 镜像名 |
| collectData.image.tag | string | `"0.6.49"` | 镜像tag |
| collectData.imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥 |
| collectData.labels.app | string | `"om-collect"` | pod标签 |
| collectData.name | string | `"meeting-om-collect-new"` | 服务名 |
| collectData.podAnnotations | object | `{}` | pod声明 |
| collectData.podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| collectData.podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| collectData.replicaCount | int | `1` | 副本数 |
| collectData.resources.limits.cpu | string | `"500m"` | 容器资源配置 |
| collectData.resources.limits.memory | string | `"500Mi"` | 容器资源配置 |
| collectData.resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| collectData.resources.requests.memory | string | `"500Mi"` | 容器资源配置 |
| collectData.strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本上限数 |
| collectData.strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| collectData.strategy.type | string | `"RollingUpdate"` | 更新策略 |
| collectData.volumeMounts | object | `{}` | 容器挂载配置 |
| collectData.volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| collectData.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| collectData.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| collectData.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| deployments[0].configPath | string | `"/opt/config"` | 配置文件挂载目录 |
| deployments[0].containerSecurityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| deployments[0].containerSecurityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| deployments[0].containerSecurityContext.runAsUser | int | `1001` | 容器运行用户id |
| deployments[0].imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| deployments[0].imageTag | string | `"0.6.49"` | 镜像tag |
| deployments[0].name | string | `"om-collect"` | 服务名 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-config.ini" | string | `"0400"` | 配置文件属性 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/mindspore/om"` | 配置文件在vault中存放路径 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/mindspore/om\" -}}  \n{{ .Data.data.config }}\n{{- end }}\n"` | 配置文件渲染模版 |
| deployments[0].podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/opt/config"` | 配置文件挂载目录 |
| deployments[0].replicaCount | int | `1` | 副本数 |
| deployments[0].resources.limits.cpu | string | `"500m"` | 容器资源配置 |
| deployments[0].resources.limits.memory | string | `"500Mi"` | 容器资源配置 |
| deployments[0].resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| deployments[0].resources.requests.memory | string | `"500Mi"` | 容器资源配置 |
| deployments[0].strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本上限数 |
| deployments[0].strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| deployments[0].strategy.type | string | `"RollingUpdate"` | 更新策略 |
| deployments[0].volumeMounts | object | `{}` | 容器挂载目录 |
| deployments[0].volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| deployments[0].volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| deployments[0].volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| deployments[0].volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| imageRepository | string | `"swr.cn-north-4.myhuaweicloud.com/om/om-collection"` | 镜像名 |
| namespace | string | `"om"` | 命名空间 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组 |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 容器挂载卷名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志打印等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"om"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` | vault agent刷新配置文件间隔 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| secret.enabled | bool | `false` | 创建secret资源 |
| secret.keysMaps.config_ini.key | string | `"opengauss_meetings_credentials.cfg"` | secret运用vault仓库中的key名 |
| secret.name | string | `"meeting-om-secrets"` | secret资源名 |
| secret.path | string | `"secrets/data/opengauss/om"` | secret引用vault仓库中的路径 |
| serviceAccount.create | bool | `true` | 创建sa |
| serviceAccount.name | string | `"om"` | sa资源名 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-7-9

### 说明
- 初始版本发布

## 1.0.6 - 2026-1-26

### 说明
- 增加deployment labels

## 1.0.7 - 2026-2-28

### 说明
- 增加autoscale配置