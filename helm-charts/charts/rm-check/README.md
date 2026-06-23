# rm-check

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
用于解析readme文件并使用prompt模板通过大模型对readme文件进行打分

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
1. 下载各仓库中的readme文件并解析
2. 将解析结果通过大模型进行评分
3. 将评分结果存储，并用于数据展示

### 底层组件
* **Database**: [PgSQL 2.9.11]

### 维护者

|  名称     |            邮箱              | Github ID |
|-----------|------------------------------|-----------|
|  谢承志   |  xiechengzhi3@h-partners.com | 2511689622 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| cronjob.annotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 配置是否注入vault agent容器 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-perms-config.yaml" | string | `"0400"` | 配置文件属性 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-secret-config.yaml" | string | `"internal/data/infra-common/rm-check"` | 配置文件在vault中存放路径 |
| cronjob.annotations."vault.hashicorp.com/agent-inject-template-config.yaml" | string | `"{{- with secret \"internal/data/infra-common/rm-check\" -}}  \n{{ .Data.data.cronjob }}\n{{- end }}\n"` | 配置文件渲染模版 |
| cronjob.annotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | 配置vault agent是否只注入为初始化容器 |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-group" | string | `"1001"` | vault agent容器运行用户组 |
| cronjob.annotations."vault.hashicorp.com/agent-run-as-user" | string | `"1001"` | vault agent容器运行用户 |
| cronjob.annotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | 容器挂载卷名 |
| cronjob.annotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志打印等级 |
| cronjob.annotations."vault.hashicorp.com/role" | string | `"rm-check"` | 配置 Vault Agent 自动身份验证方法使用的 Vault 角色 |
| cronjob.annotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | 配置vault agent跳过tls验证 |
| cronjob.concurrencyPolicy | string | `"Forbid"` | 禁止cronjob并发运行 |
| cronjob.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| cronjob.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/rm-check"` | 镜像名 |
| cronjob.image.tag | string | `"main-921596"` | 镜像tag |
| cronjob.resources.limits.cpu | string | `"2"` | 容器资源配置 |
| cronjob.resources.limits.memory | string | `"2Gi"` | 容器资源配置 |
| cronjob.resources.requests.cpu | string | `"1"` | 容器资源配置 |
| cronjob.resources.requests.memory | string | `"2Gi"` | 容器资源配置 |
| cronjob.restartPolicy | string | `"OnFailure"` | 容器重启策略 |
| cronjob.schedule | string | `"0 0 * * *"` | 定时器触发周期 |
| cronjob.securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| cronjob.securityContext.capabilities.drop[0] | string | `"ALL"` | 安全策略，去除所有权限 |
| cronjob.securityContext.readOnlyRootFilesystem | bool | `false` | 文件系统只读 |
| cronjob.securityContext.runAsUser | int | `1001` | 容器运行用户id |
| cronjob.suspend | bool | `false` | 定时任务是否暂停 |
| cronjob.volumes[0].name | string | `"token-vol"` | 容器挂载卷名 |
| cronjob.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | Token 的预期接收方 |
| cronjob.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | token有效期 |
| cronjob.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 生成的 Token 文件在挂载目录中的文件名 |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| serviceAccount.automount | bool | `false` | 取消自动挂载sa token |
| serviceAccount.create | bool | `true` | 创建sa |
| serviceAccount.name | string | `"rm-check"` | sa资源名 |

## 变更历史

## 1.0.0 - 2025-11-19

### 说明
- 初始版本发布
