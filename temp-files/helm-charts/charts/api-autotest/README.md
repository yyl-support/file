# api-autotest

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)


## 📖 服务介绍 (Service Overview)

自动化测试定时任务

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
gitcode迁移的数据验证

### 底层组件
该服务在启动和运行中依赖：
* **vault**: [挂载服务所需的配置文件]

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| guoxiaozhen | guoxiaozhen1@h-partners.com | guoxiaozhen0304 |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| cronjobs[0] | object | `{"annotations":{"vault.hashicorp.com/agent-inject-template-config.yaml":"{{- with secret \"internal/data/infra-test/api-autotest\" -}}  \n{{ .Data.data.cronjobOneConf }}\n{{- end }}\n"},"concurrencyPolicy":"Forbid","resources":{"limits":{"cpu":"1","memory":"4Gi"},"requests":{"cpu":"500m","memory":"1Gi"}},"restartPolicy":"OnFailure","schedule":"0 18 8 12 *","suspend":false}` | 是否停止运行 |
| cronjobs[0].annotations | object | `{"vault.hashicorp.com/agent-inject-template-config.yaml":"{{- with secret \"internal/data/infra-test/api-autotest\" -}}  \n{{ .Data.data.cronjobOneConf }}\n{{- end }}\n"}` | 自定义声明项 |
| cronjobs[0].concurrencyPolicy | string | `"Forbid"` | 并行触发设置，默认禁止 |
| cronjobs[0].resources.limits.cpu | string | `"1"` | 服务最大使用CPU资源数 |
| cronjobs[0].resources.limits.memory | string | `"4Gi"` | 服务最大使用内存容量 |
| cronjobs[0].resources.requests.cpu | string | `"500m"` | 服务最少使用的CPU资源数 |
| cronjobs[0].resources.requests.memory | string | `"1Gi"` | 服务最少使用内存容量 |
| cronjobs[0].restartPolicy | string | `"OnFailure"` | 重启机制设置 |
| cronjobs[0].schedule | string | `"0 18 8 12 *"` | 触发周期设置 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/api-autotest-cronjob"` | 镜像名称 |
| image.tag | string | `"gitcode_datacheck-033a75"` | 镜像Tag |
| imagePullSecrets[0] | object | `{"name":"huawei-swr-image-pull-secret"}` | 镜像仓访问凭证名称 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault inject功能,默认开启 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-config.yaml" | string | `"0400"` | 配置文件访问权限设置 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-config.yaml" | string | `"internal/data/infra-test/api-autotest"` | 配置文件在Vault中存放的路径 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | 设置vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"api-autotest"` | vault权限角色 |
| podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/app/check/config"` | 配置文件挂载到容器的路径 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent和vault server通信是否跳过tls验证,默认为true |
| serviceAccount.create | bool | `true` | 是否创建serviceAccount资源 |
| serviceAccount.name | string | `"api-autotest"` | serviceAccount名称 |
