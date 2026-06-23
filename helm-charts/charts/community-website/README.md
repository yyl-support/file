# community-website

![Version: 1.0.5](https://img.shields.io/badge/Version-1.0.5-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
> **社区官网前端服务**

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 功能点1，静态资源展示

### 底层组件
该服务在启动和运行过程中依赖：
* **nginx**: [存放前端静态资源]
* **vault**: [挂载nginx所需的ssl相关配置文件]

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| liuyang | yang_liu0418@163.com | githubliuyang777 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| env[0].name | string | `"DET_URL"` | 环境变量名称 |
| env[0].value | string | `"https://www.mindspore.cn"` | URL地址 |
| global.appName | string | `"website-v2"` | 服务名称 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像仓库访问凭证名称 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/mindspore/mindspore-website"` | 镜像名称 |
| image.tag | string | `"v1.0.20251125052217"` | 镜像Tag |
| ingress.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | igress和容器通信协议 |
| ingress.className | string | `"nginx"` | ingress类型 |
| ingress.enabled | bool | `true` | 是否渲染ingress资源 |
| ingress.host | string | `"www.mindspore.cn"` | 域名 |
| istio.enabled | bool | `false` | 是否启用istio |
| istio.gateway | string | `""` | istio网关名称 |
| istio.mtlsMode | string | `"DISABLE"` | mtls模式开关 |
| istio.nslabel | object | `{}` | 启用istio时命名空间所需标签 |
| istio.tlsMode | string | `"SIMPLE"` | 服务是否启用tls协议 |
| istio.virtualService.host | string | `""` | 域名 |
| istio.virtualService.http | list | `[]` | 路径转发配置 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.httpGet.httpHeaders[0].name | string | `"Host"` | 自定义header名 |
| livenessProbe.httpGet.httpHeaders[0].value | string | `"www.mindspore.cn"` | header值 |
| livenessProbe.httpGet.path | string | `"/"` | 请求路径 |
| livenessProbe.httpGet.port | int | `8080` | 服务端口 |
| livenessProbe.httpGet.scheme | string | `"HTTPS"` | 请求发送的通信协议 |
| livenessProbe.initialDelaySeconds | int | `5` | 等待容器初始化时间 |
| livenessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.timeoutSeconds | int | `5` | 超时时间设置 |
| namespace.enabled | bool | `false` | 是否渲染namespace资源 |
| namespace.name | string | `"website-revision"` | 命名空间名称 |
| podAnnotations."vault.hashicorp.com/agent-iniuit-first" | string | `"true"` | 初始化容器是否最先启动 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-abc.txt" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-dhparam.pem" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-abc.txt" | string | `"internal/data/mindspore/mindspore-website"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-dhparam.pem" | string | `"internal/data/mindspore/mindspore-website"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/mindspore/mindspore-website"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/mindspore/mindspore-website"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-abc.txt" | string | `"{{- with secret \"internal/data/mindspore/mindspore-website\" -}}\n{{ .Data.data.certificatePassword }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-dhparam.pem" | string | `"{{- with secret \"internal/data/mindspore/mindspore-website\" -}}\n{{ .Data.data.dhparamPem }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/mindspore/mindspore-website\" -}}\n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/mindspore/mindspore-website\" -}}\n{{ .Data.data.ServerKey }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"mindspore-website"` | vault权限角色名称 |
| podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/etc/nginx/cert/"` | 文件挂载在容器中的路径 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent与server通信是否跳过tls验证 |
| podLabels.app | string | `"website-v2"` | pod匹配标签 |
| readinessProbe.failureThreshold | int | `3` | 失败重试次数 |
| readinessProbe.httpGet.httpHeaders[0].name | string | `"Host"` | 自定义header名 |
| readinessProbe.httpGet.httpHeaders[0].value | string | `"www.mindspore.cn"` | header值 |
| readinessProbe.httpGet.path | string | `"/"` | 请求路径 |
| readinessProbe.httpGet.port | int | `8080` | 服务端口 |
| readinessProbe.httpGet.scheme | string | `"HTTPS"` | 请求发送的通信协议 |
| readinessProbe.initialDelaySeconds | int | `5` | 等待容器初始化时间 |
| readinessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| readinessProbe.successThreshold | int | `1` | 成功标志次数 |
| readinessProbe.timeoutSeconds | int | `5` | 超时时间设置 |
| replicaCount | int | `4` | 容器副本数 |
| resources.limits.cpu | int | `1` | 服务最大使用CPU资源数 |
| resources.limits.memory | string | `"1Gi"` | 服务最大使用内存容量 |
| resources.requests.cpu | int | `1` | 容器运行所需CPU资源，最小值为1 |
| resources.requests.memory | string | `"1Gi"` | 容器运行所需内存资源，最小值为1Gi |
| secret.ca_crt_key | string | `"ca.cert"` | secret中的键名 |
| secret.enable | bool | `true` | 是否渲染secret资源 |
| secret.name | string | `"website-tls"` | secret名称 |
| secret.path | string | `"secrets/data/mindspore/mindspore-cn-tls"` | secret资源在vault中存放路径 |
| secret.tls_crt_key | string | `"ca.cert"` | secret中的键名 |
| secret.tls_key_key | string | `"ca.key"` | secret中的键名 |
| service.port | int | `8080` | service对外端口 |
| service.portName | string | `"tls-1"` | 端口名 |
| service.targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"mindspore-website"` | sa名称 |
| strategy.rollingUpdate.maxSurge | int | `2` | 更新时最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `2` | 更新时最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.5 - 2025-11-4

### 说明
- 1.0.5： 增加istio相关资源

## 1.0.6 - 2026-1-21

### 说明
- 1.0.6： 增加deployment label

## 1.0.7 - 2026-2-28

### 说明
- 1.0.7： 增加autoscale配置