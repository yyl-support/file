# unifiedbus

![Version: 1.0.11](https://img.shields.io/badge/Version-1.0.11-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
A Helm chart for unifiedbus website

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能

### 底层组件

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| chenzeng | chenzeng2@huawei.com | zengchen1024 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| ingress.host | string | `"www.unifiedbus.com"` | 域名 |
| ingress.main.annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.main.annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"500"` | 单IP每分钟限制请求数 |
| ingress.main.enabled | bool | `false` | 启用ingress |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | 服务端协议类型 |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/configuration-snippet" | string | `"if ($host = 'unifiedbus.com') {\n    return 301 https://www.unifiedbus.com$request_uri;\n}\n"` | 自定义配置 |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` | 跨域白名单 |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` | 启用跨域 |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.rewrite.annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"10000"` | 单IP每分钟限制请求数 |
| ingress.rewrite.enabled | bool | `true` | 启用重定向 |
| ingress.rewrite.host | string | `"unifiedbus.com"` | 域名 |
| ingress.rewrite.name | string | `"unifiedbus-website-rewrite-ingress"` | ingress资源名 |
| ingress.secretName | string | `"tls-secret"` | 域名证书资源名 |
| ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` | 跨域白名单 |
| ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` | 启用跨域 |
| ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"2000"` | 单IP每分钟限制请求数 |
| ingress.subpaths[0].name | string | `"server-ingress"` | ingress资源名 |
| ingress.subpaths[0].path | string | `"/api-server(/|$)(.*)"` | ingress路径匹配 |
| ingress.subpaths[0].pathType | string | `"ImplementationSpecific"` | 匹配策略 |
| ingress.subpaths[0].serviceName | string | `"server-service"` | service资源名 |
| ingress.subpaths[0].servicePort | int | `8080` | service中的端口号 |
| ingress.subpaths[1].annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` | 跨域白名单 |
| ingress.subpaths[1].annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` | 启用跨域 |
| ingress.subpaths[1].annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.subpaths[1].annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"2000"` | 单IP每分钟限制请求数 |
| ingress.subpaths[1].name | string | `"statement-ingress"` | ingress资源名 |
| ingress.subpaths[1].path | string | `"/api-statement(/|$)(.*)"` | ingress路径匹配 |
| ingress.subpaths[1].pathType | string | `"ImplementationSpecific"` | 匹配策略 |
| ingress.subpaths[1].serviceName | string | `"statement-server-service"` | service资源名 |
| ingress.subpaths[1].servicePort | int | `8080` | service中的端口号 |
| ingress.subpaths[2].annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` | 跨域白名单 |
| ingress.subpaths[2].annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` | 启用跨域 |
| ingress.subpaths[2].annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` | 突增系数 |
| ingress.subpaths[2].annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"2000"` | 单IP每分钟限制请求数 |
| ingress.subpaths[2].name | string | `"captcha-ingress"` | ingress资源名 |
| ingress.subpaths[2].path | string | `"/api-captcha(/|$)(.*)"` |  |
| ingress.subpaths[2].pathType | string | `"ImplementationSpecific"` |  |
| ingress.subpaths[2].serviceName | string | `"captcha-common-service"` |  |
| ingress.subpaths[2].servicePort | int | `8080` |  |
| ingress.subpaths[3].annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` |  |
| ingress.subpaths[3].annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` |  |
| ingress.subpaths[3].annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` |  |
| ingress.subpaths[3].annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"2000"` |  |
| ingress.subpaths[3].name | string | `"stat-ingress"` |  |
| ingress.subpaths[3].path | string | `"/api-stat(/|$)(.*)"` |  |
| ingress.subpaths[3].pathType | string | `"ImplementationSpecific"` |  |
| ingress.subpaths[3].serviceName | string | `"website-backend-stat-service"` |  |
| ingress.subpaths[3].servicePort | int | `8080` |  |
| initContainers[0].command[0] | string | `"/bin/bash"` | 初始化容器启动命令 |
| initContainers[0].command[1] | string | `"-c"` | 初始化容器启动命令 |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/; chown -R 1000:1000 /vault/secrets/; chmod g-s /vault/secrets/; ls -ld /vault/secrets/"` | 初始化容器启动命令 |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/openeuler:22.03-lts-sp3"` | 初始化容器镜像 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 初始化容器镜像拉取策略 |
| initContainers[0].name | string | `"init-unifiedbus"` | 初始化容器名 |
| nodeSelector."kubernetes.io/arch" | string | `"amd64"` | 节点选择标签 |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` | vault agent容器首先启动 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 用于指定包含服务帐户令牌的卷，以便与 Vault 的 Kubernetes 进行自动身份验证 |
| podAnnotations."vault.hashicorp.com/role" | string | `"unifiedbus"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| pvc.accessModes[0] | string | `"ReadWriteMany"` | pvc挂载类型为多节点挂载 |
| pvc.annotations | object | `{}` | pvc自定义声明字段 |
| pvc.name | string | `"unifiedbus-server-data"` | pvc资源名 |
| pvc.storage | string | `"1Gi"` | pvc存储空间 |
| pvc.storageClassName | string | `"csi-sfs"` | 存储类型 |
| pvc.volumeMode | string | `"Filesystem"` | pvc存储卷类型 |
| secrets.enabled | bool | `true` | 创建secret |
| secrets.keysMap."ca.crt" | string | `"tls.cert"` | secret中的key |
| secrets.keysMap."tls.crt" | string | `"tls.cert"` | secret中的key |
| secrets.keysMap."tls.key" | string | `"tls.key"` | secret中的key |
| secrets.name | string | `"tls-secret"` | secret资源名 |
| secrets.path | string | `"secrets/data/unifiedbus/tls"` | secret引用vault中的路径 |
| serviceAccount.automount | bool | `false` | 取消自动挂载sa token |
| serviceAccount.name | string | `"unifiedbus"` | sa资源名 |
| updateStrategy.rollingUpdate.maxSurge | int | `1` | 滚动升级过程最大增加副本数 |
| updateStrategy.rollingUpdate.maxUnavailable | int | `0` | 滚动升级过程允许减少副本数 |
| updateStrategy.type | string | `"RollingUpdate"` | 升级类型 |
| captcha.args | object | `{}` | 启动参数 |
| captcha.env[0].name | string | `"APPLICATION_PATH"` | 环境变量名 |
| captcha.env[0].value | string | `"/vault/secrets/application.properties"` | 环境变量值 |
| captcha.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| captcha.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/captcha-common-prod"` | 镜像名 |
| captcha.image.tag | string | `"tfh-f32ba9"` | 镜像tag |
| captcha.initContainers[0].command[0] | string | `"/bin/bash"` | 容器启动命令 |
| captcha.initContainers[0].command[1] | string | `"-c"` | 容器启动命令 |
| captcha.initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/; chown -R 1001:1001 /vault/secrets/; chmod g-s /vault/secrets/; ls -ld /vault/secrets/"` | 容器启动命令 |
| captcha.initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/openeuler:22.03-lts-sp3"` | 容器镜像 |
| captcha.initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| captcha.initContainers[0].name | string | `"init-unifiedbus"` | 初始化容器名 |
| captcha.livenessProbe.failureThreshold | int | `3` | 健康检查失败重试次数 |
| captcha.livenessProbe.initialDelaySeconds | int | `20` | 健康检查初始检查延迟时间 |
| captcha.livenessProbe.periodSeconds | int | `10` | 健康检查周期 |
| captcha.livenessProbe.successThreshold | int | `1` | 健康检查成功次数 |
| captcha.livenessProbe.tcpSocket.port | int | `8080` | 健康检查端口号 |
| captcha.livenessProbe.timeoutSeconds | int | `5` | 健康检查超时 |
| captcha.name | string | `"captcha-common"` | 服务名 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-perms-application.properties" | string | `"0400"` | 挂载配置文件属性 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` | 挂载配置文件属性 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-perms-tls.pfx" | string | `"0400"` | 挂载配置文件属性 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-secret-application.properties" | string | `"internal/data/unifiedbus/unifiedbus-server"` | 配置文件在vault中存放路径 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` | 配置文件在vault中存放路径 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-secret-tls.pfx" | string | `"internal/data/unifiedbus/domain-tls"` | 配置文件在vault中存放路径 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-template-application.properties" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.captcha }}\n{{- end }}\n"` | 配置文件渲染模版 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.captchaRedisCrt }}\n{{- end }}\n"` | 配置文件渲染模版 |
| captcha.podAnnotations."vault.hashicorp.com/agent-inject-template-tls.pfx" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ base64Decode .Data.data.tlspfx }}\n{{- end }}\n"` | 配置文件渲染模版 |
| captcha.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组 |
| captcha.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户 |
| captcha.podLabels.app | string | `"captcha-common"` | pod标签 |
| captcha.readinessProbe.failureThreshold | int | `3` | 健康检查失败重试次数 |
| captcha.readinessProbe.initialDelaySeconds | int | `20` | 健康检查初始检查延迟时间 |
| captcha.readinessProbe.periodSeconds | int | `10` | 健康检查周期 |
| captcha.readinessProbe.successThreshold | int | `1` | 健康检查成功次数 |
| captcha.readinessProbe.tcpSocket.port | int | `8080` | 健康检查端口号 |
| captcha.readinessProbe.timeoutSeconds | int | `5` | 健康检查超时 |
| captcha.replicaCount | int | `3` | 副本数 |
| captcha.resources.limits.cpu | int | `1` | 容器资源配置 |
| captcha.resources.limits.memory | string | `"1Gi"` | 容器资源配置 |
| captcha.resources.requests.cpu | int | `1` | 容器资源配置 |
| captcha.resources.requests.memory | string | `"1Gi"` | 容器资源配置 |
| captcha.securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| captcha.securityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| captcha.securityContext.runAsUser | int | `1001` | 安全策略，容器运行用户uid |
| captcha.service.port | int | `8080` | service端口号 |
| captcha.service.targetPort | int | `8080` | 容器监听端口号 |
| captcha.volumeMounts | object | `{}` | 容器挂载配置 |
| captcha.volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| captcha.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| captcha.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| captcha.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| guid.enabled | bool | `false` | 启用guid |
| guid.name | string | `"guid-management"` | guid服务名 |
| server.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` | 启动参数 |
| server.args[1] | string | `"--port=8080"` | 启动参数 |
| server.args[2] | string | `"--enable-debug=true"` | 启动参数 |
| server.args[3] | string | `"--rm-config=true"` | 启动参数 |
| server.args[4] | string | `"--tls-key=/vault/secrets/server.key"` | 启动参数 |
| server.args[5] | string | `"--tls-cert=/vault/secrets/server.crt"` | 启动参数 |
| server.deployment.replicaCount | int | `0` | 副本数 |
| server.deployment.updateStrategy.rollingUpdate.maxSurge | int | `1` |  |
| server.deployment.updateStrategy.rollingUpdate.maxUnavailable | int | `0` |  |
| server.deployment.updateStrategy.type | string | `"RollingUpdate"` |  |
| server.image.pullPolicy | string | `"IfNotPresent"` |  |
| server.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/website-backend-specification-prod"` |  |
| server.image.tag | string | `"fix_zengchen1024-a08459"` |  |
| server.livenessProbe.failureThreshold | int | `3` |  |
| server.livenessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| server.livenessProbe.httpGet.port | int | `8080` |  |
| server.livenessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| server.livenessProbe.initialDelaySeconds | int | `20` |  |
| server.livenessProbe.periodSeconds | int | `10` |  |
| server.livenessProbe.successThreshold | int | `1` |  |
| server.livenessProbe.timeoutSeconds | int | `5` |  |
| server.name | string | `"server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-mongo.crt" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-mq.crt" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-pg.crt" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-mongo.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-mq.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-pg.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.server }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-mongo.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.mongoCrt }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-mq.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.kafkaCrt }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-pg.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.PgCrt }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.serverRedisCrt }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerKey }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| server.podLabels.app | string | `"server"` |  |
| server.readinessProbe.failureThreshold | int | `3` |  |
| server.readinessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| server.readinessProbe.httpGet.port | int | `8080` |  |
| server.readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| server.readinessProbe.initialDelaySeconds | int | `20` |  |
| server.readinessProbe.periodSeconds | int | `10` |  |
| server.readinessProbe.successThreshold | int | `1` |  |
| server.readinessProbe.timeoutSeconds | int | `5` |  |
| server.replicaCount | int | `10` |  |
| server.resources.limits.cpu | int | `4` |  |
| server.resources.limits.memory | string | `"4Gi"` |  |
| server.resources.requests.cpu | int | `4` |  |
| server.resources.requests.memory | string | `"4Gi"` |  |
| server.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| server.securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| server.securityContext.runAsUser | int | `1000` |  |
| server.service.port | int | `8080` |  |
| server.service.targetPort | int | `8080` |  |
| server.statefulset.replicaCount | int | `4` |  |
| server.statefulset.updateStrategy.type | string | `"RollingUpdate"` |  |
| server.volumeMounts[0].mountPath | string | `"/opt/data"` |  |
| server.volumeMounts[0].name | string | `"volume-data"` |  |
| server.volumes[0].name | string | `"token-vol"` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| server.volumes[1].name | string | `"volume-data"` |  |
| server.volumes[1].persistentVolumeClaim.claimName | string | `"unifiedbus-server-data-new"` |  |
| stat.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| stat.args[1] | string | `"--port=8080"` |  |
| stat.args[2] | string | `"--enable-debug=true"` |  |
| stat.args[3] | string | `"--rm-config=true"` |  |
| stat.args[4] | string | `"--tls-key=/vault/secrets/server.key"` |  |
| stat.args[5] | string | `"--tls-cert=/vault/secrets/server.crt"` |  |
| stat.enabled | bool | `true` |  |
| stat.image.pullPolicy | string | `"IfNotPresent"` |  |
| stat.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/website-backend-stat"` |  |
| stat.image.tag | string | `"main-bc3742"` |  |
| stat.livenessProbe.failureThreshold | int | `3` |  |
| stat.livenessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| stat.livenessProbe.httpGet.port | int | `8080` |  |
| stat.livenessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| stat.livenessProbe.initialDelaySeconds | int | `10` |  |
| stat.livenessProbe.periodSeconds | int | `10` |  |
| stat.livenessProbe.successThreshold | int | `1` |  |
| stat.name | string | `"website-backend-stat"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-perms-mongo.crt" | string | `"0400"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-secret-mongo.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}\n{{ .Data.data.statConf }}\n{{- end }}\n"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-template-mongo.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.mongoCrt }}\n{{- end }}\n"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.statRedisCrt }}\n{{- end }}\n"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerKey }}\n{{- end }}\n"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| stat.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| stat.podLabels.app | string | `"website-backend-stat"` |  |
| stat.readinessProbe.failureThreshold | int | `3` |  |
| stat.readinessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| stat.readinessProbe.httpGet.port | int | `8080` |  |
| stat.readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| stat.readinessProbe.initialDelaySeconds | int | `10` |  |
| stat.readinessProbe.periodSeconds | int | `10` |  |
| stat.readinessProbe.successThreshold | int | `1` |  |
| stat.replicaCount | int | `1` |  |
| stat.resources.limits.cpu | int | `2` |  |
| stat.resources.limits.memory | string | `"2Gi"` |  |
| stat.resources.requests.cpu | int | `1` |  |
| stat.resources.requests.memory | string | `"1Gi"` |  |
| stat.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| stat.securityContext.runAsUser | int | `1000` |  |
| stat.service.port | int | `8080` |  |
| stat.service.targetPort | int | `8080` |  |
| stat.volumeMounts | object | `{}` |  |
| stat.volumes[0].name | string | `"token-vol"` |  |
| stat.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| stat.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| stat.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| statement.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| statement.args[1] | string | `"--port=8080"` |  |
| statement.args[2] | string | `"--enable-debug=true"` |  |
| statement.args[3] | string | `"--rm-config=true"` |  |
| statement.args[4] | string | `"--tls-key=/vault/secrets/server.key"` |  |
| statement.args[5] | string | `"--tls-cert=/vault/secrets/server.crt"` |  |
| statement.image.pullPolicy | string | `"IfNotPresent"` |  |
| statement.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/unifiedbus/statement-management-prod"` |  |
| statement.image.tag | string | `"main-d44d34"` |  |
| statement.livenessProbe.failureThreshold | int | `3` |  |
| statement.livenessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| statement.livenessProbe.httpGet.port | int | `8080` |  |
| statement.livenessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| statement.livenessProbe.initialDelaySeconds | int | `20` |  |
| statement.livenessProbe.periodSeconds | int | `10` |  |
| statement.livenessProbe.successThreshold | int | `1` |  |
| statement.livenessProbe.timeoutSeconds | int | `5` |  |
| statement.name | string | `"statement-server"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/unifiedbus/unifiedbus-server"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/unifiedbus/domain-tls"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.statement }}\n{{- end }}\n"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/unifiedbus/unifiedbus-server\" -}}  \n{{ .Data.data.statementRedisCrt }}\n{{- end }}\n"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/unifiedbus/domain-tls\" -}}  \n{{ .Data.data.ServerKey }}\n{{- end }}\n"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| statement.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| statement.podLabels.app | string | `"statement-server"` |  |
| statement.readinessProbe.failureThreshold | int | `3` |  |
| statement.readinessProbe.httpGet.path | string | `"/internal/v1/heartbeat"` |  |
| statement.readinessProbe.httpGet.port | int | `8080` |  |
| statement.readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| statement.readinessProbe.initialDelaySeconds | int | `20` |  |
| statement.readinessProbe.periodSeconds | int | `10` |  |
| statement.readinessProbe.successThreshold | int | `1` |  |
| statement.readinessProbe.timeoutSeconds | int | `5` |  |
| statement.replicaCount | int | `2` |  |
| statement.resources.limits.cpu | int | `2` |  |
| statement.resources.limits.memory | string | `"2Gi"` |  |
| statement.resources.requests.cpu | int | `1` |  |
| statement.resources.requests.memory | string | `"1Gi"` |  |
| statement.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| statement.securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| statement.securityContext.runAsUser | int | `1000` |  |
| statement.service.port | int | `8080` |  |
| statement.service.targetPort | int | `8080` |  |
| statement.volumeMounts[0].mountPath | string | `"/home/app/statements"` |  |
| statement.volumeMounts[0].name | string | `"volume-data"` |  |
| statement.volumes[0].name | string | `"token-vol"` |  |
| statement.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| statement.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| statement.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| statement.volumes[1].name | string | `"volume-data"` |  |
| statement.volumes[1].persistentVolumeClaim.claimName | string | `"unifiedbus-statement-data"` |  |

## 变更历史

## 1.0.0 - 2025-8-11

### 说明
- 初始版本发布

## 1.0.12 - 2025-12-22

### 说明
- 增加guid和errata组件

## 1.0.13 - 2026-01-13

### 说明
- 增加guid定时任务