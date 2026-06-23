# discourse

![Version: 1.0.8](https://img.shields.io/badge/Version-1.0.8-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 2.0.1](https://img.shields.io/badge/AppVersion-2.0.1-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
为开源社区提供论坛服务

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 用户可创建、修改、删除及回复话题或帖子
* 提供全面的管理后台，为管理员提供设置、用户管理、审查、数据导出等功能

### 底层组件
* Ruby on Rails：主后端框架，负责服务端逻辑、数据处理、API接口等
* PostgreSQL：存储持久性数据
* Redis：主要作为Sidekiq的队列和缓存，支持异步任务调度和部分数据高速缓存
* Sidekiq：基于Redis的后台任务队列，处理邮件发送，定时任务等各类异步操作
* EaseCheck：审核服务，为帖子文字及图片提供审核能力

### 维护者

| 名称         | 邮箱                     | Github ID |
|------------|------------------------|-----------|
| xiewenjing | xiewenjing4@huawei.com | roosterd  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | 亲和策略 |
| command[0] | string | `"/bin/bash"` | 启动命令 |
| command[1] | string | `"-c"` | 启动命令 |
| command[2] | string | `"/vault/secrets/envbash.sh"` | 启动命令 |
| configmaps[0].content | string | `"# Proxy configuration\n# Production environment proxy\n\n# Test environment proxy\nlocation /api-dsapi/ {\n    proxy_set_header X-Forwarded-For $http_x_real_ip;\n    proxy_pass https://dsapi.osinfra.cn/;\n}\n\n# Test environment proxy\n# Proxy configuration for logout\nlocation /ubmc-logout {\n    proxy_set_header X-Forwarded-For $http_x_real_ip;\n    proxy_pass https://omapi.openubmc.cn/oneid/logout;\n}"` | configmap文件内容 |
| configmaps[0].keyName | string | `"40-proxy.conf"` | configmap键名 |
| configmaps[0].name | string | `"discourse-proxy"` | configmap资源名 |
| env[0].name | string | `"DISCOURSE_MAXMIND_LICENSE_KEY"` | 环境变量名 |
| env[0].value | string | `""` | 环境变量值 |
| env[1].name | string | `"DISCOURSE_DEVELOPER_EMAILS"` | 环境变量名 |
| env[1].value | string | `""` | 环境变量值 |
| env[2].name | string | `"DISCOURSE_DB_NAME"` | 环境变量名|
| env[2].value | string | `""` | 环境变量值 |
| env[3].name | string | `"DISCOURSE_DB_PASSWORD"` | 环境变量名 |
| env[3].value | string | `""` | 环境变量值 |
| env[4].name | string | `"DISCOURSE_REDIS_PASSWORD"` | 环境变量名 |
| env[4].value | string | `""` | 环境变量值 |
| fullnameOverride | string | `"web-server"` | 服务名，用于相关资源生成 |
| image.pullPolicy | string | `"Always"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/discourse"` | 镜像名 |
| image.tag | string | `"v2.0.5"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| ingress.default.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | ingress与服务通信协议 |
| ingress.default.annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.default.annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"100"` | 单IP每分钟请求数上限 |
| ingress.default.annotations."nginx.ingress.kubernetes.io/proxy-body-size" | string | `"4m"` | 上传文件大小限制 |
| ingress.default.name | string | `"discuss-ingress"` | ingress名称 |
| ingress.default.path | string | `"/"` | 匹配路径 |
| ingress.default.pathType | string | `"Prefix"` | 路径匹配规则 |
| ingress.enabled | bool | `false` | 是否启用ingress |
| ingress.host | string | `"discuss.openubmc.cn"` | 域名 |
| ingress.limit.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | ingress与服务通信协议 |
| ingress.limit.annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.limit.annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"1"` | 单IP每分钟请求数上限 |
| ingress.limit.name | string | `"discourse-discussion-mail-send-ratelimit-ingress"` | ingress名称 |
| ingress.limit.path | string | `"/admin/email"` | 匹配路径 |
| ingress.limit.pathType | string | `"Exact"` | 路径匹配规则 |
| ingress.secretName | string | `"discourse-tls"` | tls secret名称 |
| initContainers[0].command[0] | string | `"/bin/bash"` | 启动命令 |
| initContainers[0].command[1] | string | `"-c"` | 启动命令 |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/;chmod 0700 /etc/nginx/; chmod 0700 /usr/local/share/ca-certificates/; chown -R 1000:1000 /vault/secrets/; chown -R 1000:1000 /etc/nginx/;chown -R 1000:1000 /usr/local/share/ca-certificates/; chmod g-s /vault/secrets/; chmod g-s /etc/nginx/;chmod g-s /usr/local/share/ca-certificates/; ls -ld /vault/secrets/"` | 启动命令 |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/openeuler:22.03-lts-sp3"` | 镜像名 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| initContainers[0].name | string | `"init-openeuler"` | 容器名称 |
| istio.enabled | bool | `true` | 是否启用istio |
| istio.gateway | string | `"istio-system/istio-gateway-https"` | 网关名称 |
| istio.mtlsMode | string | `"DISABLE"` | mtls模式开关 |
| istio.nslabel.istio-injection | string | `"enabled"` | 命名空间是否启用istio |
| istio.tls.mode | string | `"SIMPLE"` | tls协议开关 |
| istio.virtualService.routes[0].destinations[0].host | string | `"web-server.discourse.svc.cluster.local"` | 服务内网域名 |
| istio.virtualService.routes[0].match[0].uri.prefix | string | `"/"` | 匹配路径 |
| istio.virtualService.routes[0].rewrite.uri | string | `"/"` | 转发路径 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.initialDelaySeconds | int | `30` | 容器初始化等待时间 |
| livenessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.tcpSocket.port | int | `8080` | 服务暴露端口 |
| livenessProbe.timeoutSeconds | int | `5` | 超时时间 |
| nameOverride | string | `"web-server"` | 服务名，用于相关资源生成 |
| namespace.enabled | bool | `true` | 是否渲染namespace资源 |
| namespace.name | string | `"discourse"` | 命名空间名称 |
| nodeSelector."kubernetes.io/arch" | string | `"amd64"` | 节点选择标签 |
| podAnnotations."traffic.sidecar.istio.io/excludeOutboundIPRanges" | string | `"0.0.0.0/0"` | 启用istio时声明放行出方向所有地址 |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` | 初始化容器是否最先启动 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-command-discourse.key" | string | `"for count in 1 2 3; do if [ $(netstat -anlp | grep 8080| wc -l) -ge 1 ]; then echo \"success delete config\"; rm -rf /etc/nginx/* ; rm -rf /usr/local/share/ca-certificates/pg-server-ca.crt;\nrm -rf /usr/local/share/ca-certificates/redis-server-ca.crt ; break; else echo \"service not running skip\";sleep 10; fi done\n"` | 文件挂载时执行命令 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-discourse.crt" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-discourse.key" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-envbash.sh" | string | `"0500"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-monitor.sh" | string | `"0500"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-pg-server-ca.crt" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-redis-server-ca.crt" | string | `"0400"` | 文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-discourse.crt" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-discourse.key" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-envbash.sh" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-monitor.sh" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-pg-server-ca.crt" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-redis-server-ca.crt" | string | `"internal/data/openubmc/discourse"` | 文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-discourse.crt" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.serverCrt }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-discourse.key" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.serverKey }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-envbash.sh" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.envScript }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-monitor.sh" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.monitorScript }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-pg-server-ca.crt" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.pgsqlCA }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-redis-server-ca.crt" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.redisCA }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/role" | string | `"discourse"` | vault权限角色名称 |
| podAnnotations."vault.hashicorp.com/secret-volume-path-discourse.crt" | string | `"/etc/nginx/certs"` | 文件挂载在容器中的路径 |
| podAnnotations."vault.hashicorp.com/secret-volume-path-discourse.key" | string | `"/etc/nginx/certs"` | 文件挂载在容器中的路径 |
| podAnnotations."vault.hashicorp.com/secret-volume-path-pg-server-ca.crt" | string | `"/usr/local/share/ca-certificates"` | 文件挂载在容器中的路径 |
| podAnnotations."vault.hashicorp.com/secret-volume-path-redis-server-ca.crt" | string | `"/usr/local/share/ca-certificates"` | 文件挂载在容器中的路径 |
| podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` | 周期性挂载间隔时间 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent与server通信是否跳过tls验证 |
| podLabels.app | string | `"web-server"` | pod标签 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 安全策略文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 安全策略文件类型 |
| pvc.accessModes | string | `"ReadWriteMany"` | pvc访问模式 |
| pvc.enabled | bool | `true` | 是否渲染pvc资源 |
| pvc.name | string | `"openubmc-discourse-share-volume"` | pvc名称 |
| pvc.resources.requests.storage | string | `"500Gi"` | 磁盘容量 |
| pvc.storageClassName | string | `"csi-sfsturbo"` | 存储类型 |
| pvc.volumeMode | string | `"Filesystem"` | 卷类型 |
| pvc.volumeName | string | `"pv-efs-discourse"` | 卷名 |
| readinessProbe.failureThreshold | int | `3` | 失败重试次数 |
| readinessProbe.initialDelaySeconds | int | `30` | 等待容器初始化时间 |
| readinessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| readinessProbe.successThreshold | int | `1` | 成功标志次数 |
| readinessProbe.tcpSocket.port | int | `8080` | 容器暴露端口 |
| readinessProbe.timeoutSeconds | int | `5` | 超时时间设置 |
| replicaCount | int | `4` | pod副本数 |
| resources.limits.cpu | int | `2` | 服务最大使用CPU资源数 |
| resources.limits.memory | string | `"4Gi"` | 服务最大使用内存容量 |
| resources.requests.cpu | string | `"500m"` | 服务最小需要CPU资源数 |
| resources.requests.memory | string | `"1500Mi"` | 服务最小需要内存容量 |
| robot.enabled | bool | `true` | 是否渲染机器人服务 |
| robot.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| robot.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/forum-robot"` | 镜像名称 |
| robot.image.tag | string | `"forum_robot_beta-38d84c"` | 镜像Tag |
| robot.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-inject-command-config.yaml" | string | `"for count in 1 2 3; do if [ $(netstat -anlp | grep 5000| wc -l) -ge 1 ]; then echo \"success delete config\"; rm -rf /app/config/* ;  break; else echo \"service not running skip\";sleep 10; fi done\n"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-inject-perms-config.yaml" | string | `"0400"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-inject-secret-config.yaml" | string | `"internal/data/openubmc/discourse"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-inject-template-config.yaml" | string | `"{{- with secret \"internal/data/openubmc/discourse\" -}}  \n{{ .Data.data.robotConf }}\n{{- end }}\n"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| robot.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| robot.podAnnotations."vault.hashicorp.com/role" | string | `"discourse"` |  |
| robot.podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/app/config"` |  |
| robot.podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` |  |
| robot.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| robot.podLabels.app | string | `"forum-robot"` |  |
| robot.pvc.accessModes | string | `"ReadWriteMany"` |  |
| robot.pvc.name | string | `"pvc-forumrobot-data"` |  |
| robot.pvc.storage | string | `"10Gi"` |  |
| robot.pvc.storageClassName | string | `"sfsturbo-subpath-sc"` |  |
| robot.pvc.volumeMode | string | `"Filesystem"` |  |
| robot.replicaCount | int | `1` |  |
| robot.resources.limits.cpu | string | `"500m"` |  |
| robot.resources.limits.memory | string | `"1Gi"` |  |
| robot.resources.requests.cpu | string | `"200m"` |  |
| robot.resources.requests.memory | string | `"1Gi"` |  |
| robot.strategy.rollingUpdate.maxSurge | int | `1` |  |
| robot.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| robot.strategy.type | string | `"RollingUpdate"` |  |
| robot.volumeMounts[0].mountPath | string | `"/app/data/forum_data"` |  |
| robot.volumeMounts[0].name | string | `"data-vol"` |  |
| robot.volumes[0].name | string | `"token-vol"` |  |
| robot.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| robot.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| robot.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| robot.volumes[1].name | string | `"data-vol"` |  |
| robot.volumes[1].persistentVolumeClaim.claimName | string | `"pvc-forumrobot-data"` |  |
| securityContext.allowPrivilegeEscalation | bool | `false` | 是否允许提取操作 |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 移除所有linux能力 |
| securityContext.runAsUser | int | `1000` | 限制容器运行的UID |
| service.name | string | `"tls-1"` | 端口名称 |
| service.port | int | `8080` | service对外端口 |
| service.targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| serviceAccount.annotations | object | `{}` | sa自定义声明项 |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"discourse"` | sa名称 |
| tlsDefinition.enabled | bool | `false` | 是否渲染tls secret资源 |
| tlsDefinition.keysMap."ca.crt" | string | `"tls.cert"` | vault中对应的键名 |
| tlsDefinition.keysMap."tls.crt" | string | `"tls.cert"` | vault中对应的键名 |
| tlsDefinition.keysMap."tls.key" | string | `"tls.key"` | vault中对应的键名 |
| tlsDefinition.name | string | `"discourse-tls"` | tls secret资源名称 |
| tlsDefinition.path | string | `"secrets/data/openubmc/openubmc-cn-tls"` | secret资源在vault中存放路径 |
| tolerations | list | `[]` | 污点策略 |
| updateStrategy.rollingUpdate.maxSurge | int | `3` | 更新时最大超出副本数 |
| updateStrategy.rollingUpdate.maxUnavailable | int | `3` | 更新时最大不可用副本数 |
| updateStrategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumeMounts[0].mountPath | string | `"/shared"` | 磁盘挂载在容器中的路径 |
| volumeMounts[0].name | string | `"discourse-storage-new"` | 卷名 |
| volumeMounts[1].mountPath | string | `"/etc/nginx/conf.d/outlets/server/40-proxy.conf"` | 磁盘挂载在容器中的路径 |
| volumeMounts[1].name | string | `"config-vol"` | 卷名 |
| volumeMounts[1].subPath | string | `"40-proxy.conf"` | 文件名 |
| volumes[0].name | string | `"discourse-storage-new"` | 卷名 |
| volumes[0].persistentVolumeClaim.claimName | string | `"openubmc-discourse-share-volume"` | pvc名称 |
| volumes[1].name | string | `"token-vol"` | 卷名 |
| volumes[1].projected.sources[0].serviceAccountToken.audience | string | `"api"` | sa受众 |
| volumes[1].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | 过期时间 |
| volumes[1].projected.sources[0].serviceAccountToken.path | string | `"token"` | 挂载路径下的文件名 |
| volumes[2].configMap.name | string | `"discourse-proxy"` | configmap名称 |
| volumes[2].name | string | `"config-vol"` | 卷名 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 8 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-7-24

### 说明
- 初始版本发布

## 1.0.9 - 2026-1-7

### 说明
- 添加cci插件相关配置

## 1.0.10 - 2026-1-5

### 说明
- 添加复核定时任务

## 1.0.11 - 2026-2-28

### 说明
- 1.0.11： 增加autoscale配置