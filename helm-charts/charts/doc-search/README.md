# doc-search

![Version: 1.0.1](https://img.shields.io/badge/Version-1.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
用于给各社区提供搜索服务

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
1. 使用es查询搜索关键词并匹配最佳结果返回

### 底层组件
* **Database**: [elasticsearch 7.19.8+]

### 维护者

|  名称     |            邮箱              | Github ID |
|-----------|------------------------------|-----------|
|  谢承志   |  xiechengzhi3@h-partners.com | 2511689622 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| appName | string | `"common-search-deployment"` | deployment名称 |
| configPath | string | `"/vault/secrets/application.yml"` | 配置文件绝对路径 |
| containerSecurityContext.allowPrivilegeEscalation | bool | `false` | 是否允许提权操作 |
| containerSecurityContext.capabilities.drop[0] | string | `"ALL"` | 移除所有linux能力 |
| containerSecurityContext.runAsUser | int | `1001` | 限制容器运行的UID |
| cronjob.annotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否注入vault agent容器 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-perms-application.yml" | string | `"0400"` | 配置文件属性 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-perms-mq.crt" | string | `"0400"` | 证书文件属性 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-secret-application.yml" | string | `"internal/data/infra-common/search"` | 配置文件在vault中存放路径 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-secret-mq.crt" | string | `"internal/data/infra-common/search"` | 证书文件在vault中存放路径 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-template-application.yml" | string | `"{{- with secret \"internal/data/infra-common/search\" -}}  \n{{ .Data.data.import }}\n{{- end }}\n"` | 配置文件渲染模版 |
| cronjob.annotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为初始化容器 |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | agent容器运行用户组 |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | agent容器运行用户 |
| cronjob.annotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | sa token名称 |
| cronjob.annotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| cronjob.annotations."vault.hashicorp.com/role" | string | `"mindspore-search"` | vault权限角色 |
| cronjob.annotations."vault.hashicorp.com/secret-volume-path" | string | `"/config/"` | vault文件挂载路径 |
| cronjob.annotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | agent与server通信是否跳过验证 |
| cronjob.env[0].name | string | `"APPLICATION_PATH"` | 环境变量名 |
| cronjob.env[0].value | string | `"/config/application.yml"` | 环境变量值 |
| cronjob.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/search-import-refactor"` | 镜像名 |
| cronjob.image.tag | string | `"feature-refactor-0c40f2"` | 镜像Tag |
| cronjob.name | string | `"cronjob-easysearch-import-refactor"` | 定时任务名称 |
| cronjob.policy | string | `"Forbid"` | 并发策略 |
| cronjob.resources.limits.cpu | int | `1` | 容器运行限制CPU资源 |
| cronjob.resources.limits.memory | string | `"2Gi"` | 容器运行限制内存资源 |
| cronjob.resources.requests.cpu | int | `1` | 容器运行最少所需CPU资源 |
| cronjob.resources.requests.memory | string | `"500Mi"` | 容器运行最少所需内存资源 |
| cronjob.schedule | string | `"0 2 1 * *"` | 定时任务触发周期 |
| cronjob.suspend | bool | `false` | 是否停止运行 |
| env[0].name | string | `"MINDSPORE_OFFICIAL"` | 环境变量名 |
| env[0].value | string | `"https://www.mindspore.cn"` | 环境变量值 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/mindspore/docs-search"` | 镜像名 |
| image.tag | string | `"release-refactor-multi-d70043"` | 镜像Tag |
| imagePullSecret[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| ingress.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | ingress与服务通信协议 |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.host | string | `"doc-search-common.osinfra.cn"` | 域名 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.httpGet.path | string | `"/error"` | 健康检查接口 |
| livenessProbe.httpGet.port | int | `8080` | 服务暴露端口 |
| livenessProbe.httpGet.scheme | string | `"HTTPS"` | 请求协议 |
| livenessProbe.initialDelaySeconds | int | `20` | 容器初始化等待时间 |
| livenessProbe.periodSeconds | int | `20` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.timeoutSeconds | int | `5` | 超时时间 |
| namespace | string | `"mindspore-doc-search"` | 命名空间名称 |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-application.yml" | string | `"0600"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-es.jks" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-tls.pfx" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-application.yml" | string | `"internal/data/infra-common/search"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-es.jks" | string | `"internal/data/infra-common/search"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/infra-common/search"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-tls.pfx" | string | `"internal/data/infra-common/search"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-application.yml" | string | `"{{- with secret \"internal/data/infra-common/search\" -}}  \n{{ .Data.data.application }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-es.jks" | string | `"{{- with secret \"internal/data/infra-common/search\" -}}  \n{{ base64Decode .Data.data.esJks }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/infra-common/search\" -}}  \n{{ .Data.data.redisCRT }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-tls.pfx" | string | `"{{- with secret \"internal/data/infra-common/search\" -}}  \n{{ base64Decode .Data.data.tlspfx }}\n{{- end }}        \n"` |  |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | agent容器是否作为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` |  |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` |  |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | sa token的卷名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| podAnnotations."vault.hashicorp.com/role" | string | `"mindspore-search"` |  |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| readinessProbe.failureThreshold | int | `3` |  |
| readinessProbe.httpGet.path | string | `"/error"` |  |
| readinessProbe.httpGet.port | int | `8080` |  |
| readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| readinessProbe.initialDelaySeconds | int | `10` |  |
| readinessProbe.periodSeconds | int | `10` |  |
| readinessProbe.successThreshold | int | `1` |  |
| readinessProbe.timeoutSeconds | int | `5` |  |
| replicaCount | int | `2` | pod副本数 |
| resources.limits.cpu | string | `"1"` |  |
| resources.limits.memory | string | `"2Gi"` |  |
| resources.requests.cpu | string | `"500m"` |  |
| resources.requests.memory | string | `"1Gi"` |  |
| secret.enabled | bool | `true` | 是否渲染secret资源 |
| secret.keysMap."ca.crt" | string | `"server.crt"` | 在vault中对应的键名 |
| secret.keysMap."tls.crt" | string | `"server.crt"` | 在vault中对应的键名 |
| secret.keysMap."tls.key" | string | `"server.key"` | 在vault中对应的键名 |
| secret.name | string | `"doc-search-osinfra-tls"` | secret资源名称 |
| secret.tlsPath | string | `"secrets/data/infra-common/osinfra-cn"` | 在vault中存放的路径 |
| service.port | int | `8080` | service对外端口 |
| service.portName | string | `"http"` | 端口名称 |
| service.targetPort | int | `8080` | 服务暴露端口 |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"mindspore-search"` | sa名称 |
| strategy.rollingUpdate.maxSurge | int | `1` | 更新时最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 更新时最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-9-22

### 说明
- 初始版本发布

## 1.0.2 - 2026-2-28

### 说明
- 增加deployment label; 增加autoscale配置

## 1.0.3 - 2026-3-23

### 说明
- 增加配置文件挂载