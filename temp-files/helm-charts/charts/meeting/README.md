# meeting

![Version: 1.0.10](https://img.shields.io/badge/Version-1.0.10-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for meeting server

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
| cronjobCommon.env[0].name | string | `"TZ"` | 环境变量名 |
| cronjobCommon.env[0].value | string | `"Asia/Shanghai"` | 环境变量值 |
| cronjobCommon.env[1].name | string | `"CONFIG_PATH"` |  |
| cronjobCommon.env[1].value | string | `"/vault/secrets/config"` |  |
| cronjobCommon.env[2].name | string | `"VAULT_PATH"` |  |
| cronjobCommon.env[2].value | string | `"/vault/secrets/secrets.yaml"` |  |
| cronjobCommon.env[3].name | string | `"MYSQL_TLS_PEM_PATH"` |  |
| cronjobCommon.env[3].value | string | `"/vault/secrets/ca.pem"` |  |
| cronjobCommon.env[4].name | string | `"TLS_CRT_PATH"` |  |
| cronjobCommon.env[4].value | string | `"/vault/secrets/server.crt"` |  |
| cronjobCommon.env[5].name | string | `"TLS_KEY_PATH"` |  |
| cronjobCommon.env[5].value | string | `"/vault/secrets/server.key"` |  |
| cronjobCommon.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| cronjobCommon.securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| cronjobCommon.securityContext.readOnlyRootFilesystem | bool | `false` |  |
| cronjobCommon.securityContext.runAsUser | int | `1000` |  |
| cronjobs[0].command[0] | string | `"/bin/bash"` | 启动命令 |
| cronjobs[0].command[1] | string | `"-c"` | 启动命令 |
| cronjobs[0].command[2] | string | `"python3 manage.py handle_meeting\n"` | 启动命令 |
| cronjobs[0].concurrencyPolicy | string | `"Forbid"` | 并发策略 |
| cronjobs[0].enabled | bool | `true` | 是否渲染cronjob资源 |
| cronjobs[0].image.imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| cronjobs[0].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/meeting/meeting-platform"` | 镜像名 |
| cronjobs[0].image.tag | string | `"main-28a899"` | 镜像Tag |
| cronjobs[0].labels.app | string | `"handle-meeting"` | pod标签 |
| cronjobs[0].name | string | `"handle-meeting"` | cronjob名称 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` | 配置文件属性 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` | 配置文件属性 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-perms-secrets.yaml" | string | `"0400"` | 配置文件属性 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/opengauss/opengauss-meeting"` | 配置文件在vault中存放路径 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/opengauss/opengauss-meeting"` | 配置文件在vault中存放路径 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-secrets.yaml" | string | `"internal/data/opengauss/opengauss-meeting"` | 配置文件在vault中存放路径 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformConfig }}\n{{- end }}\n"` | 配置文件渲染模版 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.kafkacrt }}\n{{- end }}\n"` | 配置文件渲染模版 |
| cronjobs[0].podAnnotations."vault.hashicorp.com/agent-inject-template-secrets.yaml" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformSecrets }}\n{{- end }}\n"` | 配置文件渲染模版 |
| cronjobs[0].resources.limits.cpu | string | `"500m"` | 容器运行限制CPU资源 |
| cronjobs[0].resources.limits.memory | string | `"500Mi"` | 容器运行限制内存资源 |
| cronjobs[0].resources.requests.cpu | string | `"500m"` | 容器运行最少所需CPU资源 |
| cronjobs[0].resources.requests.memory | string | `"500Mi"` | 容器运行最少所需内存资源 |
| cronjobs[0].restartPolicy | string | `"OnFailure"` | 重启策略 |
| cronjobs[0].schedule | string | `"0 * * * *"` | 触发周期设置 |
| cronjobs[0].suspend | bool | `false` | 是否停止运行 |
| cronjobs[1].command[0] | string | `"/bin/bash"` |  |
| cronjobs[1].command[1] | string | `"-c"` |  |
| cronjobs[1].command[2] | string | `"python manage.py handle_recordings\n"` |  |
| cronjobs[1].concurrencyPolicy | string | `"Replace"` |  |
| cronjobs[1].enabled | bool | `true` |  |
| cronjobs[1].image.imagePullPolicy | string | `"IfNotPresent"` |  |
| cronjobs[1].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/meeting/meeting-platform"` |  |
| cronjobs[1].image.tag | string | `"main-28a899"` |  |
| cronjobs[1].labels.app | string | `"handle-recording"` |  |
| cronjobs[1].name | string | `"handle-recordings"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-perms-secrets.yaml" | string | `"0400"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-secret-secrets.yaml" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformConfig }}\n{{- end }}\n"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.kafkacrt }}\n{{- end }}\n"` |  |
| cronjobs[1].podAnnotations."vault.hashicorp.com/agent-inject-template-secrets.yaml" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformSecrets }}\n{{- end }}\n"` |  |
| cronjobs[1].resources.limits.cpu | string | `"500m"` |  |
| cronjobs[1].resources.limits.memory | string | `"500Mi"` |  |
| cronjobs[1].resources.requests.cpu | string | `"500m"` |  |
| cronjobs[1].resources.requests.memory | string | `"500Mi"` |  |
| cronjobs[1].restartPolicy | string | `"OnFailure"` |  |
| cronjobs[1].schedule | string | `"30 19 * * *"` |  |
| cronjobs[1].suspend | bool | `false` |  |
| cronjobs[2].command[0] | string | `"/bin/bash"` |  |
| cronjobs[2].command[1] | string | `"-c"` |  |
| cronjobs[2].command[2] | string | `"python manage.py sync_sig\n"` |  |
| cronjobs[2].concurrencyPolicy | string | `"Forbid"` |  |
| cronjobs[2].enabled | bool | `true` |  |
| cronjobs[2].image.imagePullPolicy | string | `"IfNotPresent"` |  |
| cronjobs[2].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/meeting/meeting-center"` |  |
| cronjobs[2].image.tag | string | `"master-5725b4"` |  |
| cronjobs[2].labels.app | string | `"updating-sigs"` |  |
| cronjobs[2].name | string | `"updating-sigs"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-perms-secrets.yaml" | string | `"0400"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-secret-secrets.yaml" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.centerConfig }}\n{{- end }}\n"` |  |
| cronjobs[2].podAnnotations."vault.hashicorp.com/agent-inject-template-secrets.yaml" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.centerSecrets }}\n{{- end }}\n"` |  |
| cronjobs[2].resources.limits.cpu | string | `"500m"` |  |
| cronjobs[2].resources.limits.memory | string | `"500Mi"` |  |
| cronjobs[2].resources.requests.cpu | string | `"500m"` |  |
| cronjobs[2].resources.requests.memory | string | `"500Mi"` |  |
| cronjobs[2].restartPolicy | string | `"OnFailure"` |  |
| cronjobs[2].schedule | string | `"0 * * * *"` |  |
| cronjobs[2].suspend | bool | `false` |  |
| image.center.imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.center.repository | string | `""` | 镜像名 |
| image.center.tag | string | `""` | 镜像Tag |
| image.platform.imagePullPolicy | string | `"IfNotPresent"` |  |
| image.platform.repository | string | `""` |  |
| image.platform.tag | string | `""` |  |
| image.server.imagePullPolicy | string | `"IfNotPresent"` |  |
| image.server.repository | string | `""` |  |
| image.server.tag | string | `""` |  |
| ingress.enabled | bool | `false` | 是否启用ingress |
| ingress.host | string | `"meetings.opengauss.org"` | 域名 |
| ingress.port.number | int | `80` | service对外端口 |
| ingressNew.enabled | bool | `false` | 是否启用ingress |
| initContainer.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler"` |  |
| initContainer.image.tag | string | `"22.03-lts-sp3"` |  |
| istio.dr[0].name | string | `"meeting-center"` | dr资源名 |
| istio.dr[0].portNumber | int | `80` | service对外端口 |
| istio.dr[0].serviceName | string | `"meeting-center"` | service名称 |
| istio.dr[0].tlsMode | string | `"SIMPLE"` | tls模式开关 |
| istio.dr[1].name | string | `"meeting-platform"` |  |
| istio.dr[1].portNumber | int | `80` |  |
| istio.dr[1].serviceName | string | `"meeting-platform"` |  |
| istio.dr[1].tlsMode | string | `"SIMPLE"` |  |
| istio.enabled | bool | `true` | 是否启用istio |
| istio.gateway | string | `"istio-system/istio-gateway-https"` | gateway名称 |
| istio.host | string | `"meetings.opengauss.org"` | 域名 |
| istio.nslabel.istio-injection | string | `"enabled"` | 启用istio时命名空间所需标签 |
| istio.pa[0].label.app | string | `"meeting-center"` | pod选择标签 |
| istio.pa[0].mtlsMode | string | `"DISABLE"` | mtls模式开关 |
| istio.pa[0].name | string | `"meeting-center"` | pa资源名 |
| istio.pa[1].label.app | string | `"meeting-platform"` |  |
| istio.pa[1].mtlsMode | string | `"DISABLE"` |  |
| istio.pa[1].name | string | `"meeting-platform"` |  |
| istio.vs.http[0].match[0].uri.prefix | string | `"/api-platform/"` | 路径匹配 |
| istio.vs.http[0].rewrite.uri | string | `"/"` | 转发路径 |
| istio.vs.http[0].route[0].destination.host | string | `"meeting-platform.meetingserver.svc.cluster.local"` | service地址 |
| istio.vs.http[0].route[0].destination.port.number | int | `80` | service对外端口 |
| istio.vs.http[1].match[0].uri.prefix | string | `"/"` |  |
| istio.vs.http[1].rewrite.uri | string | `"/"` |  |
| istio.vs.http[1].route[0].destination.host | string | `"meeting-center.meetingserver.svc.cluster.local"` |  |
| istio.vs.http[1].route[0].destination.port.number | int | `80` |  |
| meetingCenter.enabled | bool | `true` | 是否渲染meeting-center服务 |
| meetingCenter.name | string | `"meeting-center"` | 服务名称 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` | 配置文件属性 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-perms-secrets.yaml" | string | `"0400"` | 配置文件属性 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/opengauss/opengauss-meeting"` | 配置文件在vault中存放路径 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-secret-secrets.yaml" | string | `"internal/data/opengauss/opengauss-meeting"` | 配置文件在vault中存放路径 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.centerConfig }}\n{{- end }}\n"` | 配置文件渲染模版 |
| meetingCenter.podAnnotations."vault.hashicorp.com/agent-inject-template-secrets.yaml" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.centerSecrets }}\n{{- end }}\n"` | 配置文件渲染模版 |
| meetingCenter.podLabels.app | string | `"meeting-center"` | pod标签 |
| meetingCenter.replicas | int | `2` | pod副本数 |
| meetingCenter.resources.limits.cpu | string | `"2"` |  |
| meetingCenter.resources.limits.memory | string | `"4Gi"` |  |
| meetingCenter.resources.requests.cpu | string | `"500m"` |  |
| meetingCenter.resources.requests.memory | string | `"500Mi"` |  |
| meetingCenter.service.annotations | object | `{}` |  |
| meetingCenter.service.ports[0].name | string | `"tls-1"` | 端口名，应用istio时名字需包含tls |
| meetingCenter.service.ports[0].port | int | `80` |  |
| meetingCenter.service.ports[0].protocol | string | `"TCP"` |  |
| meetingCenter.service.ports[0].targetPort | int | `8080` |  |
| meetingCenter.service.type | string | `"ClusterIP"` |  |
| meetingPlatform.enabled | bool | `true` |  |
| meetingPlatform.name | string | `"meeting-platform"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-perms-config" | string | `"0400"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-perms-secrets.yaml" | string | `"0400"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-secret-config" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-secret-secrets.yaml" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-template-config" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformConfig }}\n{{- end }}\n"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.kafkacrt }}\n{{- end }}\n"` |  |
| meetingPlatform.podAnnotations."vault.hashicorp.com/agent-inject-template-secrets.yaml" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.platformSecrets }}\n{{- end }}\n"` |  |
| meetingPlatform.podLabels.app | string | `"meeting-platform"` |  |
| meetingPlatform.replicas | int | `2` |  |
| meetingPlatform.resources.limits.cpu | string | `"2"` |  |
| meetingPlatform.resources.limits.memory | string | `"4Gi"` |  |
| meetingPlatform.resources.requests.cpu | string | `"500m"` |  |
| meetingPlatform.resources.requests.memory | string | `"500Mi"` |  |
| meetingPlatform.service.ports[0].name | string | `"tls-1"` |  |
| meetingPlatform.service.ports[0].port | int | `80` |  |
| meetingPlatform.service.ports[0].protocol | string | `"TCP"` |  |
| meetingPlatform.service.ports[0].targetPort | int | `8080` |  |
| meetingPlatform.service.type | string | `"ClusterIP"` |  |
| meetingServer.enabled | bool | `true` | 是否渲染旧版meetingserver服务 |
| namespace.enabled | bool | `true` |  |
| namespace.name | string | `"meetingserver"` |  |
| podAnnotations."traffic.sidecar.istio.io/excludeOutboundIPRanges" | string | `"0.0.0.0/0"` |  |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-ca.pem" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-ca.pem" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/opengauss/opengauss-meeting"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-ca.pem" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.MysqlCA }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.servercrt }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/opengauss/opengauss-meeting\" -}}\n{{ .Data.data.serverkey }}\n{{- end }}\n"` |  |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| podAnnotations."vault.hashicorp.com/role" | string | `"opengauss-meeting"` |  |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` |  |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` |  |
| secret.enable | bool | `false` |  |
| securityContext.allowPrivilegeEscalation | bool | `false` |  |
| securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| securityContext.runAsUser | int | `1000` |  |
| serviceAccount.create | bool | `true` |  |
| serviceAccount.name | string | `"opengauss-meeting"` |  |
| strategy.rollingUpdate.maxSurge | int | `1` |  |
| strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| strategy.type | string | `"RollingUpdate"` |  |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-6-19
### 说明
- 初始版本发布

## 1.0.11 - 2025-12-15
### 说明
- 兼容旧版meetingserver

## 1.0.12 - 2026-1-21
### 说明
- 添加deployment label

## 1.0.13 - 2026-1-30
### 说明
- 修改ingress annotation到values定义

## 1.0.14 - 2026-2-28

### 说明
- 增加autoscale配置

## 1.0.15 - 2026-3-31

### 说明
- 修改imagePullSecrets引用