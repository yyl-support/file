# oneid-workbench

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
A Helm chart for oneid workbench

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 功能点1，open API接口token管理。
* 功能点2，华为账号基本信息管理。
* 功能点3，华为账号第三方登录和绑定。

### 底层组件
该服务在启动和运行过程中依赖：
* **dapr**: dapr
* **database**: mysql、redis
* **服务认证**: 统一账号服务

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| tfhddd | taofeihu1@huawei.com     | tfhddd |
| Zherphy | zhouyi198@h-partners.com | Zherphy |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| daprd.image.repository | string | `"swr.cn-southwest-2.myhuaweicloud.com/ascend_infra/daprio/daprd"` | daprd镜像名 |
| daprd.image.tag | string | `"1.15.3"` | daprd镜像tag |
| env[0].name | string | `"APPLICATION_PATH"` | 环境变量名 |
| env[0].value | string | `"/vault/secrets/application.properties"` | 环境变量值 |
| fullnameOverride | string | `"ascend-oneid-workbench"` | 服务名 |
| healthCheck.path | string | `"/oneid-workbench/checkOmService"` | 健康检查接口 |
| healthCheck.port | int | `8080` | 健康检查端口号 |
| healthCheck.scheme | string | `"HTTPS"` | 健康检查协议 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-southwest-2.myhuaweicloud.com/ascend_infra/oneid-workbench-server"` | 镜像名 |
| image.tag | string | `"main-fb7801"` | 镜像tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥 |
| initContainers[0].command[0] | string | `"/bin/bash"` | 初始化容器启动命令 |
| initContainers[0].command[1] | string | `"-c"` | 初始化容器启动命令 |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/; chown -R 1001:1001 /vault/secrets/; chmod g-s /vault/secrets/; ls -ld /vault/secrets/"` | 初始化容器启动命令 |
| initContainers[0].image | string | `"swr.cn-southwest-2.myhuaweicloud.com/ascend_infra/openeuler:22.03-lts-sp3"` | 初始化容器镜像 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 初始化容器镜像拉取策略 |
| initContainers[0].name | string | `"init-openeuler"` | 初始化容器名 |
| istio.nslabel | object | `{}` | 命名空间istio标签,启用istio需配置该项 |
| nameOverride | string | `""` | 服务名 |
| namespace.enabled | bool | `false` | 可选,创建命名空间资源,若对接istio,则必须启用 |
| namespace.name | string | `"ascend-website"` | 命名空间 |
| podAnnotations."dapr.io/app-id" | string | `"ascend-oneid-workbench"` | 与dapr容器启动参数保持一致 |
| podAnnotations."dapr.io/disable-builtin-k8s-secret-store" | string | `"true"` |  |
| podAnnotations."dapr.io/enabled" | string | `"true"` | 启用dapr |
| podAnnotations."dapr.io/env" | string | `"GOMEMLIMIT=200MiB"` | dapr容器中go环境内存配置 |
| podAnnotations."dapr.io/sidecar-memory-limit" | string | `"300Mi"` | dapr容器内存资源限制 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-command-application.properties" | string | `"for count in 1 2 3; do if [ $(netstat -anlp | grep 8080| wc -l) -ge 1 ]; then echo \"success delete config\"; rm -rf /vault/secrets/*; break; else echo \"service not running skip\";sleep 10; fi done\n"` | 创建配置文件后自动执行命令 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-application.properties" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-ca.crt" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-components.yaml" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-tls.pfx" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-application.properties" | string | `"internal/data/ascend/ascend-server"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-ca.crt" | string | `"internal/data/ascend/ascend-server"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-components.yaml" | string | `"internal/data/ascend/ascend-server"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-tls.pfx" | string | `"internal/data/ascend/domain-tls"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-application.properties" | string | `"{{- with secret \"internal/data/ascend/ascend-server\" -}}  \n{{ .Data.data.AscendOneidWorkbenchConfig }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-ca.crt" | string | `"{{- with secret \"internal/data/ascend/ascend-server\" -}}  \n{{ .Data.data.AscendOneidWorkbenchRedis }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-components.yaml" | string | `"{{- with secret \"internal/data/ascend/ascend-server\" -}}  \n{{ .Data.data.AscendOneidWorkbenchComponent }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-tls.pfx" | string | `"{{- with secret \"internal/data/ascend/domain-tls\" -}}  \n{{ base64Decode .Data.data.tlspfx }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组 |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 容器挂载卷名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志打印等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"ascend-website"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` | vault agent刷新配置文件间隔 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| replicaCount | int | `1` | 副本数 |
| resources.limits.cpu | string | `"2"` | 容器资源配置 |
| resources.limits.memory | string | `"4Gi"` | 容器资源配置 |
| resources.requests.cpu | string | `"1"` | 容器资源配置 |
| resources.requests.memory | string | `"1Gi"` | 容器资源配置 |
| securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| securityContext.runAsUser | int | `1001` | 容器运行用户id |
| service.ports[0].name | string | `"http-port"` | 端口名 |
| service.ports[0].port | int | `8080` | 端口号 |
| service.ports[0].protocol | string | `"TCP"` | 端口协议 |
| service.ports[0].targetPort | int | `8080` | 容器监听端口号 |
| service.type | string | `"ClusterIP"` | service类型 |
| serviceAccount.automount | bool | `false` | 取消自动挂载sa token |
| serviceAccount.create | bool | `false` | 创建sa |
| serviceAccount.name | string | `"ascend-website"` | sa资源名 |
| strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本上限数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-11-6

### 说明
- 初始版本发布

## 1.0.1 - 2026-1-23

### 说明
- 增加deployment labels

## 1.0.2 - 2026-2-28

### 说明
- 增加autoscale配置