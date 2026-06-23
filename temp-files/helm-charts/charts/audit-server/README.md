# audit-server

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

内容审核服务

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
本服务是一个统一内容审核平台，本质上是中台，将多个第三方审核能力封装为标准化服务，降低业务系统接入复杂度，同时提供灵活的审核策略配置能力。

主要提供以下功能：
1. 核心审核功能，服务目前提供三种模式：
    - 模式一：Moderation V3
    - 模式二：SCAS
    - 模式三：双重审核
2. 关键特性
    - 统一API接口：RESTful API设计，屏蔽底层审核工具差异
    - 灵活配置：通过YAML配置文件适配不同业务场景
    - 安全认证：基于Token的鉴权机制
    - 错误标准化：统一错误码和响应格式
    - 多环境部署：支持流水线部署，已有多平台配置案例
3. 服务能力
    - 适配不同审核策略：通过type参数区分审核场景（如头像、帖子、评论等）
    - 智能路由：根据配置自动选择审核引擎和策略
    - 结果聚合：在双重审核模式下合并多个审核源的结果
    - 健康监控：提供心跳检测接口确保服务可用性

### 底层组件
该服务在启动和运行中依赖：
* **vault**: [挂载服务所需的配置文件]

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
|钟源珂  | zhongyuanke@huawei.com | drizzlezyk |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| args[0] | string | `"--port=8000"` | 服务暴露端口 |
| args[1] | string | `"--config-file=/vault/secrets/application.yaml"` | 配置文件绝对路径 |
| args[2] | string | `"--enable_debug=true"` | 如果设置为True， Go语言代码控制日志系统（logrus）的调试级别为debug级别 |
| args[3] | string | `"--rm-cfg=true"` | 配置读入内存后，是否在磁盘中删除配置文件 |
| fullnameOverride | string | `"audit-server"` | 服务名称，用于相关资源定义 |
| healthCheck.path | string | `"/internal/heartbeat"` | 健康检查接口地址 |
| healthCheck.port | int | `8000` | 服务端口 |
| healthCheck.scheme | string | `"HTTP"` | 健康检查通信协议 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openfuyao/audit-server-prod"` | 镜像名 |
| image.tag | string | `"v1.14.0-6999c4"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓库访问凭证名称 |
| ingress.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTP"` | ingress与服务之间通信协议 |
| ingress.annotations."nginx.ingress.kubernetes.io/rewrite-target" | string | `"/$2"` | 路径重定向策略 |
| ingress.className | string | `"nginx"` | ingress class |
| ingress.enabled | bool | `false` | 是否使用Ingress |
| ingress.hosts[0].host | string | `""` | 服务域名 |
| ingress.hosts[0].paths[0].path | string | `"/openfuyao(/|$)(.*)"` | 转发路径 |
| ingress.hosts[0].paths[0].pathType | string | `"ImplementationSpecific"` | 路径匹配策略 |
| istio.nslabel | object | `{}` | 启用istio时命名空间的注入标签 |
| nameOverride | string | `""` | 服务名称，用于相关资源定义 |
| namespace | string | `"audit-server"` | 命名空间 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault注入 |
| podAnnotations."vault.hashicorp.com/agent-inject-command-application.yaml" | string | `"for count in 1 2 3; do if [ $(netstat -anlp | grep 8000| wc -l) -ge 1 ]; then echo \"success delete config\"; rm -rf /vault/secrets/*; break; else echo \"service not running skip\";sleep 10; fi done\n"` | 注入时执行命令 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-application.yaml" | string | `"0400"` | 配置文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-postgre.crt" | string | `"0400"` | 配置文件权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-application.yaml" | string | `"internal/data/openfuyao/audit-server"` | 配置文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-postgre.crt" | string | `"internal/data/openfuyao/audit-server"` | 配置文件在vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-application.yaml" | string | `"{{- with secret \"internal/data/openfuyao/audit-server\" -}}  \n{{ .Data.data.config }}\n{{- end }}\n"` | 配置文件在vault中的模板 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-postgre.crt" | string | `"{{- with secret \"internal/data/openfuyao/audit-server\" -}}  \n{{ .Data.data.pgsqlCA }}\n{{- end }}\n"` | 配置文件在vault中的模板 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"audit-server"` | vault权限角色 |
| podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` | 循环挂载间隔时间 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent与server通信是否跳过tls验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 自定义安全策略文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 策略文件类型 |
| replicaCount | int | `1` | 容器副本数 |
| resources.limits.cpu | string | `"500m"` | cpu最大限制 |
| resources.limits.memory | string | `"500Mi"` | 内存最大限制 |
| resources.requests.cpu | string | `"500m"` | cpu最小限制 |
| resources.requests.memory | string | `"500Mi"` | 内存最小限制 |
| securityContext.allowPrivilegeEscalation | bool | `false` | 是否允许提权操作 |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 移除所有linux权限操作 |
| securityContext.runAsUser | int | `1000` | 容器进程以UID 1000运行 |
| service.ports[0].name | string | `"http-port"` | 端口名称 |
| service.ports[0].port | int | `80` | service对外端口 |
| service.ports[0].protocol | string | `"TCP"` | 协议 |
| service.ports[0].targetPort | int | `8000` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型，默认为ClusterIP |
| serviceAccount.automount | bool | `false` | serviceaccount是否自动挂载 |
| serviceAccount.create | bool | `true` | 是否创建values资源 |
| serviceAccount.name | string | `"audit-server"` | serviceaccount名称 |
| strategy.rollingUpdate.maxSurge | int | `1` | 滚动更新最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 滚动更新最大不可用pod数 |
| strategy.type | string | `"RollingUpdate"` | 滚动更新策略 |
| volumes[0].name | string | `"token-vol"` | vault挂载卷名 |
| volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | token受众，默认为api |
| volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | 过期时间 |
| volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 挂载路径下的文件名 |

## 变更历史

## 1.0.0 - 2025-8-26

### 说明
- 初始版本发布

## 1.0.1 - 2025-12-18

### 说明
- 添加istio网关资源模板

## 1.0.2 - 2026-2-4

### 说明
- 添加deployment labels
- 添加ingress和secrets模板