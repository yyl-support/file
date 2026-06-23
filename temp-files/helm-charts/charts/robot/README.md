# robot

![Version: 2.0.0](https://img.shields.io/badge/Version-2.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
A Helm chart for community robot

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
    社区机器人评论，合入代码
### 底层组件
1. Kubernetes 1.19+
2. Helm 3.2.0+

### 维护者

| 名称           | 邮箱                        | Github ID    |
|--------------|---------------------------|--------------|
| LiYanghang00 | Liyanghang00@huawei.com   | LiYanghang00 |
| ibforu | fengchao73@h-partners.com | ibforu       |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| containerSecurityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| containerSecurityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| containerSecurityContext.runAsUser | int | `1000` | 安全策略，容器运行用户uid |
| deployments[0].args[0] | string | `"--port=8888"` | 启动参数 |
| deployments[0].args[1] | string | `"--hmac-secret-file=/vault/secrets/gitcode-secret"` | 启动参数 |
| deployments[0].args[2] | string | `"--config-file=/vault/secrets/config"` | 启动参数 |
| deployments[0].args[3] | string | `"--handle-path=gitcode-hook"` | 启动参数 |
| deployments[0].image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| deployments[0].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-hook-delivery"` | 镜像名 |
| deployments[0].image.tag | string | `"develop-lts-a0c6fb"` | 镜像tag |
| deployments[0].labels.app | string | `"robot-universal-hook-delivery"` | pod标签 |
| deployments[0].name | string | `"robot-universal-hook-delivery"` | 服务名 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` | 配置文件属性 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-gitcode-secret" | string | `"0400"` | 配置文件属性 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/openeuler/robot-openeuler"` | 配置文件在vault中存放路径 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-gitcode-secret" | string | `"internal/data/openeuler/robot-openeuler"` | 配置文件在vault中存放路径 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.deliveryConfig }}\n{{- end }}\n"` | 配置文件渲染模版 |
| deployments[0].podAnnotations."vault.hashicorp.com/agent-inject-template-gitcode-secret" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.deliverySecrets }}\n{{- end }}\n"` | 配置文件渲染模版 |
| deployments[0].replicas | int | `2` | pod副本数 |
| deployments[0].resources.limits.cpu | string | `"1"` | 容器资源配置 |
| deployments[0].resources.limits.memory | string | `"1Gi"` | 容器资源配置 |
| deployments[0].resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| deployments[0].resources.requests.memory | string | `"1Gi"` | 容器资源配置 |
| deployments[0].service.port | int | `8888` | service端口号 |
| deployments[0].service.portName | string | `"http-port"` | 端口名称 |
| deployments[0].service.targetPort | int | `8888` | 容器端口号 |
| deployments[0].service.type | string | `"ClusterIP"` | 服务暴露访问,集群内访问 |
| deployments[0].strategy.rollingUpdate.maxSurge | int | `2` | 滚动升级过程最大增加副本数 |
| deployments[0].strategy.rollingUpdate.maxUnavailable | int | `0` | 滚动升级过程允许减少副本数 |
| deployments[0].strategy.type | string | `"RollingUpdate"` | 升级类型 |
| deployments[0].vaultVolume | string | `"create"` | 启用vault认证所需sa token挂载卷 |
| deployments[0].volumeMounts | list | `[]` | 挂载目录列表 |
| deployments[0].volumes | list | `[]` | 挂载卷列表 |
| deployments[1].args[0] | string | `"--port=8888"` | 启动参数 |
| deployments[1].args[1] | string | `"--config-file=/app/conf/config.yaml"` | 启动参数 |
| deployments[1].args[2] | string | `"--handle-path=gitcode-hook"` | 启动参数 |
| deployments[1].image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| deployments[1].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-access"` | 镜像名 |
| deployments[1].image.tag | string | `"develop-lts-6dc552"` | 镜像tag |
| deployments[1].labels.app | string | `"robot-universal-access"` | pod标签 |
| deployments[1].name | string | `"robot-universal-access"` | 服务名 |
| deployments[1].podAnnotations | string | `""` | pod声明配置 |
| deployments[1].replicas | int | `2` | 副本数 |
| deployments[1].resources.limits.cpu | string | `"1"` | 容器资源配置 |
| deployments[1].resources.limits.memory | string | `"1Gi"` | 容器资源配置 |
| deployments[1].resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| deployments[1].resources.requests.memory | string | `"1Gi"` | 容器资源配置 |
| deployments[1].service.port | int | `8888` | service端口号 |
| deployments[1].service.portName | string | `"http-port"` | 端口名称 |
| deployments[1].service.targetPort | int | `8888` | 容器端口号 |
| deployments[1].service.type | string | `"ClusterIP"` | 服务暴露访问,集群内访问 |
| deployments[1].strategy.rollingUpdate.maxSurge | int | `2` | 滚动升级过程最大增加副本数 |
| deployments[1].strategy.rollingUpdate.maxUnavailable | int | `0` | 滚动升级过程允许减少副本数 |
| deployments[1].strategy.type | string | `"RollingUpdate"` | 升级类型 |
| deployments[1].vaultVolume | string | `""` | 启用vault认证所需sa token挂载卷 |
| deployments[1].volumeMounts[0].mountPath | string | `"/app/conf/"` | 配置文件挂载目录 |
| deployments[1].volumeMounts[0].name | string | `"app-config"` | 挂载目录别名 |
| deployments[1].volumeMounts[0].readOnly | bool | `true` | 挂载文件只读 |
| deployments[1].volumes[0].configMap.name | string | `"configmap-universal-access"` | configmap资源名 |
| deployments[1].volumes[0].name | string | `"app-config"` | 挂载目录别名 |
| deployments[2].args[0] | string | `"--port=8888"` |  |
| deployments[2].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[2].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[2].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[2].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[2].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-assign"` |  |
| deployments[2].image.tag | string | `"develop-lts-a42f9d"` |  |
| deployments[2].labels.app | string | `"robot-universal-assign"` |  |
| deployments[2].name | string | `"robot-universal-assign"` |  |
| deployments[2].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[2].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[2].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[2].replicas | int | `2` |  |
| deployments[2].resources.limits.cpu | string | `"1"` |  |
| deployments[2].resources.limits.memory | string | `"1Gi"` |  |
| deployments[2].resources.requests.cpu | string | `"500m"` |  |
| deployments[2].resources.requests.memory | string | `"1Gi"` |  |
| deployments[2].service.port | int | `8888` |  |
| deployments[2].service.portName | string | `"http-port"` |  |
| deployments[2].service.targetPort | int | `8888` |  |
| deployments[2].service.type | string | `"ClusterIP"` |  |
| deployments[2].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[2].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[2].strategy.type | string | `"RollingUpdate"` |  |
| deployments[2].vaultVolume | string | `"create"` |  |
| deployments[2].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[2].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[2].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[2].volumes[0].configMap.name | string | `"configmap-universal-assign"` |  |
| deployments[2].volumes[0].name | string | `"app-config"` |  |
| deployments[3].args[0] | string | `"--port=8888"` |  |
| deployments[3].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[3].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[3].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[3].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[3].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-associate"` |  |
| deployments[3].image.tag | string | `"develop-lts-c2d33d"` |  |
| deployments[3].labels.app | string | `"robot-universal-associate"` |  |
| deployments[3].name | string | `"robot-universal-associate"` |  |
| deployments[3].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[3].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[3].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[3].replicas | int | `2` |  |
| deployments[3].resources.limits.cpu | string | `"1"` |  |
| deployments[3].resources.limits.memory | string | `"1Gi"` |  |
| deployments[3].resources.requests.cpu | string | `"500m"` |  |
| deployments[3].resources.requests.memory | string | `"1Gi"` |  |
| deployments[3].service.port | int | `8888` |  |
| deployments[3].service.portName | string | `"http-port"` |  |
| deployments[3].service.targetPort | int | `8888` |  |
| deployments[3].service.type | string | `"ClusterIP"` |  |
| deployments[3].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[3].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[3].strategy.type | string | `"RollingUpdate"` |  |
| deployments[3].vaultVolume | string | `"create"` |  |
| deployments[3].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[3].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[3].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[3].volumes[0].configMap.name | string | `"configmap-universal-associate"` |  |
| deployments[3].volumes[0].name | string | `"app-config"` |  |
| deployments[4].args[0] | string | `"--port=8888"` |  |
| deployments[4].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[4].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[4].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[4].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[4].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-cla"` |  |
| deployments[4].image.tag | string | `"develop-lts-e9f2b0"` |  |
| deployments[4].labels.app | string | `"robot-universal-cla"` |  |
| deployments[4].name | string | `"robot-universal-cla"` |  |
| deployments[4].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[4].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[4].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[4].replicas | int | `2` |  |
| deployments[4].resources.limits.cpu | string | `"1"` |  |
| deployments[4].resources.limits.memory | string | `"1Gi"` |  |
| deployments[4].resources.requests.cpu | string | `"500m"` |  |
| deployments[4].resources.requests.memory | string | `"1Gi"` |  |
| deployments[4].service.port | int | `8888` |  |
| deployments[4].service.portName | string | `"http-port"` |  |
| deployments[4].service.targetPort | int | `8888` |  |
| deployments[4].service.type | string | `"ClusterIP"` |  |
| deployments[4].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[4].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[4].strategy.type | string | `"RollingUpdate"` |  |
| deployments[4].vaultVolume | string | `"create"` |  |
| deployments[4].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[4].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[4].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[4].volumes[0].configMap.name | string | `"configmap-universal-cla"` |  |
| deployments[4].volumes[0].name | string | `"app-config"` |  |
| deployments[5].args[0] | string | `"--port=8888"` |  |
| deployments[5].args[1] | string | `"--config-file=/vault/secrets/config"` |  |
| deployments[5].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[5].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-hook-dispatcher"` |  |
| deployments[5].image.tag | string | `"develop-lts-91526e"` |  |
| deployments[5].labels.app | string | `"robot-hook-dispatcher"` |  |
| deployments[5].name | string | `"robot-hook-dispatcher"` |  |
| deployments[5].podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` |  |
| deployments[5].podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[5].podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.dispatcher }}\n{{- end }}\n"` |  |
| deployments[5].replicas | int | `1` |  |
| deployments[5].resources.limits.cpu | string | `"1"` |  |
| deployments[5].resources.limits.memory | string | `"1Gi"` |  |
| deployments[5].resources.requests.cpu | string | `"500m"` |  |
| deployments[5].resources.requests.memory | string | `"1Gi"` |  |
| deployments[5].service.port | int | `8888` |  |
| deployments[5].service.portName | string | `"http-port"` |  |
| deployments[5].service.targetPort | int | `8888` |  |
| deployments[5].service.type | string | `"ClusterIP"` |  |
| deployments[5].strategy.rollingUpdate.maxSurge | int | `1` |  |
| deployments[5].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[5].strategy.type | string | `"RollingUpdate"` |  |
| deployments[5].vaultVolume | string | `"create"` |  |
| deployments[5].volumeMounts | list | `[]` |  |
| deployments[5].volumes | list | `[]` |  |
| deployments[6].args[0] | string | `"--port=8888"` |  |
| deployments[6].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[6].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[6].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[6].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[6].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-review"` |  |
| deployments[6].image.tag | string | `"develop-lts-tmp-0efb7e"` |  |
| deployments[6].labels.app | string | `"robot-universal-review"` |  |
| deployments[6].name | string | `"robot-universal-review"` |  |
| deployments[6].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[6].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[6].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[6].replicas | int | `2` |  |
| deployments[6].resources.limits.cpu | string | `"1"` |  |
| deployments[6].resources.limits.memory | string | `"1Gi"` |  |
| deployments[6].resources.requests.cpu | string | `"500m"` |  |
| deployments[6].resources.requests.memory | string | `"1Gi"` |  |
| deployments[6].service.port | int | `8888` |  |
| deployments[6].service.portName | string | `"http-port"` |  |
| deployments[6].service.targetPort | int | `8888` |  |
| deployments[6].service.type | string | `"ClusterIP"` |  |
| deployments[6].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[6].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[6].strategy.type | string | `"RollingUpdate"` |  |
| deployments[6].vaultVolume | string | `"create"` |  |
| deployments[6].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[6].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[6].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[6].volumes[0].configMap.name | string | `"configmap-universal-review"` |  |
| deployments[6].volumes[0].name | string | `"app-config"` |  |
| deployments[7].args[0] | string | `"--port=8888"` |  |
| deployments[7].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[7].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[7].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[7].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[7].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-label"` |  |
| deployments[7].image.tag | string | `"develop-lts-712c4d"` |  |
| deployments[7].labels.app | string | `"robot-universal-label"` |  |
| deployments[7].name | string | `"robot-universal-label"` |  |
| deployments[7].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[7].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[7].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[7].replicas | int | `2` |  |
| deployments[7].resources.limits.cpu | string | `"1"` |  |
| deployments[7].resources.limits.memory | string | `"1Gi"` |  |
| deployments[7].resources.requests.cpu | string | `"500m"` |  |
| deployments[7].resources.requests.memory | string | `"1Gi"` |  |
| deployments[7].service.port | int | `8888` |  |
| deployments[7].service.portName | string | `"http-port"` |  |
| deployments[7].service.targetPort | int | `8888` |  |
| deployments[7].service.type | string | `"ClusterIP"` |  |
| deployments[7].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[7].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[7].strategy.type | string | `"RollingUpdate"` |  |
| deployments[7].vaultVolume | string | `"create"` |  |
| deployments[7].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[7].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[7].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[7].volumes[0].configMap.name | string | `"configmap-universal-label"` |  |
| deployments[7].volumes[0].name | string | `"app-config"` |  |
| deployments[8].args[0] | string | `"--port=8888"` |  |
| deployments[8].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[8].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[8].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[8].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[8].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-lifecycle"` |  |
| deployments[8].image.tag | string | `"develop-lts-298f05"` |  |
| deployments[8].labels.app | string | `"robot-universal-lifecycle"` |  |
| deployments[8].name | string | `"robot-universal-lifecycle"` |  |
| deployments[8].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[8].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[8].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[8].replicas | int | `2` |  |
| deployments[8].resources.limits.cpu | string | `"1"` |  |
| deployments[8].resources.limits.memory | string | `"1Gi"` |  |
| deployments[8].resources.requests.cpu | string | `"500m"` |  |
| deployments[8].resources.requests.memory | string | `"1Gi"` |  |
| deployments[8].service.port | int | `8888` |  |
| deployments[8].service.portName | string | `"http-port"` |  |
| deployments[8].service.targetPort | int | `8888` |  |
| deployments[8].service.type | string | `"ClusterIP"` |  |
| deployments[8].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[8].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[8].strategy.type | string | `"RollingUpdate"` |  |
| deployments[8].vaultVolume | string | `"create"` |  |
| deployments[8].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[8].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[8].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[8].volumes[0].configMap.name | string | `"configmap-universal-lifecycle"` |  |
| deployments[8].volumes[0].name | string | `"app-config"` |  |
| deployments[9].args[0] | string | `"--port=8888"` |  |
| deployments[9].args[1] | string | `"--config-file=/app/conf/config.yaml"` |  |
| deployments[9].args[2] | string | `"--handle-path=gitcode-hook"` |  |
| deployments[9].args[3] | string | `"--token-path=/vault/secrets/token"` |  |
| deployments[9].image.pullPolicy | string | `"IfNotPresent"` |  |
| deployments[9].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/robot-universal-welcome"` |  |
| deployments[9].image.tag | string | `"develop-lts-2ae547"` |  |
| deployments[9].labels.app | string | `"robot-universal-welcome"` |  |
| deployments[9].name | string | `"robot-universal-welcome"` |  |
| deployments[9].podAnnotations."vault.hashicorp.com/agent-inject-perms-token" | string | `"0400"` |  |
| deployments[9].podAnnotations."vault.hashicorp.com/agent-inject-secret-token" | string | `"internal/data/openeuler/robot-openeuler"` |  |
| deployments[9].podAnnotations."vault.hashicorp.com/agent-inject-template-token" | string | `"{{- with secret \"internal/data/openeuler/robot-openeuler\" -}}  \n{{ .Data.data.token }}\n{{- end }}\n"` |  |
| deployments[9].replicas | int | `2` |  |
| deployments[9].resources.limits.cpu | string | `"1"` |  |
| deployments[9].resources.limits.memory | string | `"1Gi"` |  |
| deployments[9].resources.requests.cpu | string | `"500m"` |  |
| deployments[9].resources.requests.memory | string | `"1Gi"` |  |
| deployments[9].service.port | int | `8888` |  |
| deployments[9].service.portName | string | `"http-port"` |  |
| deployments[9].service.targetPort | int | `8888` |  |
| deployments[9].service.type | string | `"ClusterIP"` |  |
| deployments[9].strategy.rollingUpdate.maxSurge | int | `2` |  |
| deployments[9].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| deployments[9].strategy.type | string | `"RollingUpdate"` |  |
| deployments[9].vaultVolume | string | `"create"` |  |
| deployments[9].volumeMounts[0].mountPath | string | `"/app/conf/"` |  |
| deployments[9].volumeMounts[0].name | string | `"app-config"` |  |
| deployments[9].volumeMounts[0].readOnly | bool | `true` |  |
| deployments[9].volumes[0].configMap.name | string | `"configmap-universal-welcome"` |  |
| deployments[9].volumes[0].name | string | `"app-config"` |  |
| ingress.enabled | bool | `true` |  |
| ingress.host | string | `"hook-delivery.openeuler.openatom.cn"` |  |
| ingress.name | string | `"hook-delivery-ingress"` |  |
| initContainers[0].command[0] | string | `"/bin/bash"` |  |
| initContainers[0].command[1] | string | `"-c"` |  |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets; chown -R 1000:1000 /vault/secrets; chmod g-s /vault/secrets; ls -ld /vault/secrets"` |  |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler:22.03-lts-sp3"` |  |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` |  |
| initContainers[0].name | string | `"init-openeuler"` |  |
| istio.dr[0].name | string | `"destinationrule-openeuler-robot"` |  |
| istio.dr[0].port | int | `8888` |  |
| istio.dr[0].serviceName | string | `"robot-universal-hook-delivery-service"` |  |
| istio.enabled | bool | `false` |  |
| istio.gateway | string | `"istio-system/istio-gateway-https"` |  |
| istio.mtlsMode | string | `"DISABLE"` |  |
| istio.nslabel.istio-injection | string | `"enabled"` |  |
| istio.pa[0].name | string | `"peerauthentication-openeuler-robot-disable-mtls"` |  |
| istio.pa[0].podLabels.app | string | `"robot-universal-hook-delivery"` |  |
| istio.tlsMode | string | `"DISABLE"` |  |
| istio.vs.host | string | `"hook-delivery.openeuler.openatom.cn"` |  |
| istio.vs.http[0].match[0].uri.prefix | string | `"/"` |  |
| istio.vs.http[0].rewrite.uri | string | `"/"` |  |
| istio.vs.http[0].route[0].destination.host | string | `"robot-universal-hook-delivery-service.robot-openeuler.svc.cluster.local"` |  |
| istio.vs.http[0].route[0].destination.port.number | int | `8888` |  |
| istio.vs.name | string | `"openeuler-robot-virtualservice"` |  |
| namespace.enabled | bool | `true` |  |
| namespace.name | string | `"robot-openeuler"` |  |
| podAnnotations."traffic.sidecar.istio.io/excludeOutboundIPRanges" | string | `"0.0.0.0/0"` |  |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| podAnnotations."vault.hashicorp.com/role" | string | `"robot-openeuler"` |  |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` |  |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` |  |
| secret.crtKey | string | `"server.crt"` |  |
| secret.enabled | bool | `true` |  |
| secret.keyKey | string | `"server.key"` |  |
| secret.name | string | `"openeuler-openatom-cn-tls"` |  |
| secret.path | string | `"secrets/data/openeuler/openeuler-openatom-cn-tls"` |  |
| serviceAccount.create | bool | `true` |  |
| serviceAccount.name | string | `"robot-openeuler"` |  |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取访问凭证 |

## 变更历史

## 1.0.0 - 2025-6-20

### 说明
- 初始版本发布

## 2.0.1- 2025-12-16

### 说明
- 兼容sync-bot 和 ci-tools机器人

## 2.0.2- 2025-12-17

### 说明
- 修复ingress策略冲突

## 2.0.3- 2026-1-27

### 说明
- 增加deployment labels

## 2.0.4 - 2026-2-28

### 说明
- 增加autoscale配置

## 2.0.5 - 2026-3-2

### 说明
- 更改ingress模板为数组循环生成

## 2.0.6 - 2026-4-7

### 说明
- 更改imagePullSecrets为Values定义