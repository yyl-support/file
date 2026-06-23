# om-webserver

![Version: 1.0.2](https://img.shields.io/badge/Version-1.0.2-informational?style=flat-square) ![AppVersion: feature-6fda1a](https://img.shields.io/badge/AppVersion-feature--6fda1a-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
A Helm chart for om-webserver Service

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 功能点1，支持账号注册、登录等能力。
* 功能点2，支持通过OIDC接入第三方账号。
* 功能点3，支持将账号服务接入指定的平台。
* 功能点4，支持会话管理能力。

### 底层组件
该服务在启动和运行过程中依赖：
* **缓存**: redis
* **主体账号**: authing/华为账号
* **信息采集**: datastat
* **敏感信息检查**: 云安工

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| tfhddd | taofeihu1@huawei.com     | tfhddd |
| Zherphy | zhouyi198@h-partners.com | Zherphy |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| containers.applicationPath | string | `"xxx/application.properties"` | 配置文件挂载路径 |
| containers.containerPort | string | `"XXX"` | 容器端口号 |
| containers.portsName | string | `"omwebserver"` | 容器端口名 |
| global.appName | string | `"comon-omwebserver"` | 服务名 |
| global.appSubName | string | `"om-webserver"` | 服务别名 |
| global.namespace | string | `"comon-omwebserver"` | 命名空间 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.pullSecret | string | `"SECRET"` | 镜像拉取密钥名 |
| image.repository | string | `"xxx.com/om/om-webserver"` | 镜像名 |
| image.tag | string | `"release-om-webserver"` | 镜像tag |
| ingress.backendProtocol | string | `"HTTPS"` | 后端协议 |
| ingress.className | string | `"nginx"` | ingress类型名 |
| ingress.enabled | bool | `true` | 启用ingress |
| ingress.host | string | `"XXX.cn"` | 服务对外域名 |
| ingress.limitConnections | string | `"400"` | ingress限速策略 |
| ingress.limitRPS | string | `"400"` | ingress限速策略 |
| ingress.port | int | `80` | ingress配置的service端口号 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-application.properties" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-tls.pfx" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-application.properties" | string | `"XXX/comon-omwebserver"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"XXX/comon-omwebserver"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-tls.pfx" | string | `"XXX/comon-omwebserver"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-application.properties" | string | `"{{- with secret \"XXX/comon-omwebserver\" -}}  \n{{ .Data.data.application }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"XXX/comon-omwebserver\" -}}  \n{{ .Data.data.redis }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-tls.pfx" | string | `"{{- with secret \"XXX/comon-omwebserver\" -}}  \n{{ base64Decode .Data.data.tlspfx }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"XXX"` | vault agent容器运行用户组 |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"XXX"` | vault agent容器运行用户 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 容器挂载卷名 |
| podAnnotations."vault.hashicorp.com/role" | string | `"comon-omwebserver"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/XXX/om-webserver"` | 配置文件挂载目录 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| probeHttpGet.path | string | `"/oneid/checkOmService"` | 健康检查接口 |
| probeHttpGet.port | string | `"XXX"` | 健康检查端口 |
| probeHttpGet.scheme | string | `"HTTPS"` | 健康检查协议 |
| replicaCount | int | `2` | 副本数 |
| resources.limits.cpu | string | `"1000m"` | 容器资源配置 |
| resources.limits.memory | string | `"2000Mi"` | 容器资源配置 |
| resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| resources.requests.memory | string | `"1000Mi"` | 容器资源配置 |
| revisionHistoryLimitCount | int | `4` | 保留版本记录数 |
| secret.ca_crt_key | string | `"XXX"` | secret资源中的key名称 |
| secret.ca_crt_path | string | `"XXX"` | secret资源中的key在vault中存放路径 |
| secret.tls_crt_key | string | `"XXX"` | secret资源中的key名称 |
| secret.tls_crt_path | string | `"XXX"` | secret资源中的key在vault中存放路径 |
| secret.tls_key_key | string | `"XXX"` | secret资源中的key名称 |
| secret.tls_key_path | string | `"XXX"` | secret资源中的key在vault中存放路径 |
| service.port | int | `80` | service端口 |
| service.targetPort | int | `8080` | 容器端口号 |
| service.type | string | `"ClusterIP"` | service类型 |
| vault.runAsUser | string | `"XXX"` | vault agent容器运行用户 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-6-5

### 说明
- 初始版本发布

## 1.0.3 - 2026-1-27

### 说明
- 增加deployment labels

## 1.0.4 - 2026-2-28

### 说明
- 增加autoscale配置