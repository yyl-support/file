# auth-center

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for audit server

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 功能点1，支持ABAC、RBAC等多种权限模型。
* 功能点2，基于权限模型，提供权限查询接口，用于权限统一管控。
* 功能点3，具备自动权限同步能力，通过编写插件代码，可以将权限信息汇聚到权限中心。

### 底层组件
该服务在启动和运行过程中依赖：
* **Database**: mysql
* **服务认证**: 统一账号服务
* **信息采集**: datastat、oneid-workbench

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| tfhddd | taofeihu1@huawei.com     | tfhddd |
| Zherphy | zhouyi198@h-partners.com | Zherphy |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| cronjob.annotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault agent容器 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-perms-application.properties" | string | `"0400"` | 配置文件权限设置 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-perms-ca.pem" | string | `"0400"` | 配置文件权限设置 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-secret-application.properties" | string | `"internal/data/infra-common/auth-center"` | 配置文件在vault中存放的路径 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-secret-ca.pem" | string | `"internal/data/infra-common/auth-center"` | 配置文件在vault中存放的路径 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-template-application.properties" | string | `"{{- with secret \"internal/data/infra-common/auth-center\" -}}  \n{{ .Data.data.cronjob }}\n{{- end }}\n"` | 配置文件在vault中的模板，默认为原文 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-template-ca.pem" | string | `"{{- with secret \"internal/data/infra-common/auth-center\" -}}  \n{{ .Data.data.mysqlCA }}\n{{- end }}\n"` | 配置文件在vault中的模板，默认为原文 |
| cronjob.annotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组id |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户id |
| cronjob.annotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| cronjob.annotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| cronjob.annotations."vault.hashicorp.com/role" | string | `"auth-center"` | vault权限角色名称 |
| cronjob.annotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent与server通信是否跳过tls验证 |
| cronjob.concurrencyPolicy | string | `"Forbid"` | 并发设置，默认禁止 |
| cronjob.healthCheck.path | string | `"/auth/checkService"` | 健康检查接口 |
| cronjob.healthCheck.port | int | `8080` | 服务暴露端口 |
| cronjob.healthCheck.scheme | string | `"HTTP"` | 健康检查通信协议 |
| cronjob.resources.limits.cpu | string | `"200m"` | 服务最大使用CPU资源数 |
| cronjob.resources.limits.memory | string | `"200Mi"` | 服务最大使用内存容量 |
| cronjob.resources.requests.cpu | string | `"200m"` | 服务最小需求CPU资源数 |
| cronjob.resources.requests.memory | string | `"200Mi"` | 服务最小需求内存容量 |
| cronjob.restartPolicy | string | `"OnFailure"` | 失败重试机制，默认OnFailure |
| cronjob.schedule | string | `"0 * * * *"` | 触发周期设置 |
| cronjob.securityContext.allowPrivilegeEscalation | bool | `false` | 是否允许提权操作，默认false |
| cronjob.securityContext.capabilities.drop[0] | string | `"ALL"` | 移除指定的linux系统操作 |
| cronjob.securityContext.readOnlyRootFilesystem | bool | `false` | 是否只读根文件系统 |
| cronjob.securityContext.runAsUser | int | `1001` | 限制容器以指定UID用户允运行 |
| cronjob.suspend | bool | `false` | 是否停止运行 |
| env[0].name | string | `"APPLICATION_PATH"` | 环境变量名 |
| env[0].value | string | `"/vault/secrets/application.properties"` | 配置文件绝对路径 |
| fullnameOverride | string | `"auth-center"` | 服务名，用于相关资源名称渲染 |
| healthCheck.path | string | `"/auth/checkService"` | 健康检查接口 |
| healthCheck.port | int | `8080` | 服务暴露端口 |
| healthCheck.scheme | string | `"HTTPS"` | 健康检查通信协议 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/auth-center-prod"` | 镜像名称 |
| image.tag | string | `"master-ebb22c"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓库访问凭证名称 |
| ingress.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` | ingress与服务之间的通信协议 |
| ingress.className | string | `"nginx"` | ingress class |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.host | string | `"auth-center.osinfra.cn"` | 域名 |
| initContainers[0].command[0] | string | `"/bin/bash"` | 初始化容器启动命令 |
| initContainers[0].command[1] | string | `"-c"` | 初始化容器启动命令 |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/; chown -R 1001:1001 /vault/secrets/; chmod g-s /vault/secrets/; ls -ld /vault/secrets/"` | 初始化容器启动命令 |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler:22.03-lts-sp3"` | 初始化容器镜像名 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| initContainers[0].name | string | `"init-openeuler"` | 初始化容器名 |
| istio.nslabel | object | `{}` | 启用istio时命名空间所需标签 |
| nameOverride | string | `""` | 服务名称，可被fullnameOverride覆盖 |
| namespace.enabled | bool | `true` | 是否渲染namespace资源 |
| namespace.name | string | `"auth-center"` | 命名空间名称 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-command-application.properties" | string | `"for count in 1 2 3; do if [ $(netstat -anlp | grep 8080| wc -l) -ge 1 ]; then echo \"success delete config\"; rm -rf /vault/secrets/*; break; else echo \"service not running skip\";sleep 10; fi done\n"` | 配置文件挂载时执行命令 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-application.properties" | string | `"0400"` | 配置文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-ca.pem" | string | `"0400"` | 配置文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-tls.pfx" | string | `"0400"` | 配置文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-application.properties" | string | `"internal/data/infra-common/auth-center"` | 配置文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-ca.pem" | string | `"internal/data/infra-common/auth-center"` | 配置文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-tls.pfx" | string | `"internal/data/infra-common/auth-center"` | 配置文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-application.properties" | string | `"{{- with secret \"internal/data/infra-common/auth-center\" -}}  \n{{ .Data.data.config }}\n{{- end }}\n"` | 配置文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-ca.pem" | string | `"{{- with secret \"internal/data/infra-common/auth-center\" -}}  \n{{ .Data.data.mysqlCA }}\n{{- end }}\n"` | 配置文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-tls.pfx" | string | `"{{- with secret \"internal/data/infra-common/auth-center\" -}}  \n{{ base64Decode .Data.data.tlspfx }}\n{{- end }}\n"` | 配置文件在vault中的模板，默认为原文 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"auth-center"` | vault权限角色名称 |
| podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` | vault周期性挂载时间设置 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent与server通信是否跳过tls验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 本地安全策略文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 安全策略文件类型 |
| replicaCount | int | `2` | 容器副本数量 |
| resources.limits.cpu | string | `"1"` | 服务最大使用CPU资源数 |
| resources.limits.memory | string | `"1Gi"` | 服务最大使用内存容量 |
| resources.requests.cpu | string | `"1"` | 服务最小需求CPU资源数 |
| resources.requests.memory | string | `"1Gi"` | 服务最小需求内存容量 |
| secret.crtKey | string | `"server.cert"` | vault中的key |
| secret.enabled | bool | `true` | 是否渲染secret资源 |
| secret.keyKey | string | `"server.key"` | vault中的key |
| secret.name | string | `"tls-secrets"` | secret资源名称 |
| secret.path | string | `"secrets/data/infra-common/osinfra-cn"` | secret在vault中存放的路径 |
| securityContext.allowPrivilegeEscalation | bool | `false` | 是否允许提权操作，默认false |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 移除指定的linux系统操作 |
| securityContext.runAsUser | int | `1001` | 限制容器以指定UID用户允运行 |
| service.ports[0].name | string | `"http-port"` | 端口名 |
| service.ports[0].port | int | `8080` | service对外端口 |
| service.ports[0].protocol | string | `"TCP"` | service转发协议 |
| service.ports[0].targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型，默认为ClusterIP |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"auth-center"` | sa名称 |
| strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `1` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumes[0].name | string | `"token-vol"` | 卷名 |
| volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | sa受众，默认为K8sApi |
| volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token过期时间 |
| volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 默认挂载路径下的文件名 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 8 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-11-6

### 说明
- 初始版本发布

## 1.0.1 - 2026-2-28

### 说明
- 1.0.1： 增加autoscale配置