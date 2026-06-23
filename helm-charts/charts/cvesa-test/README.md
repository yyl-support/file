# cvesa

![Version: 1.0.1](https://img.shields.io/badge/Version-1.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

为openeuler官网提供安全公告等后端数据api。

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* openeuler每日漏洞信息的发布和修复状态跟踪
* openeuler每周发布安全公告
* 为openeuler官网安全公告提供后端api
* openeuler官网osv测评、兼容性列表数据的同步和展示

### 底层组件
* MySQL 5.7+，依赖`cves_go`库

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| yangwei | yangwei266@h-partners.com | yangwei999 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | 亲和策略 |
| autoscaling.enabled | bool | `false` | 是否启用自动扩缩容 |
| autoscaling.maxReplicas | int | `100` | 最大副本数 |
| autoscaling.minReplicas | int | `1` | 最小副本数 |
| autoscaling.targetCPUUtilizationPercentage | int | `80` | CPU使用率阈值 |
| cronjob | string | `"enable"` | 是否渲染cronjob资源 |
| env.const[0].name | string | `"DB_URL"` | 环境变量名 |
| env.const[0].value | string | `"172.16.1.73"` | 环境变量值 |
| env.secrets[0].key | string | `"db_user"` | 引用secret中的键名 |
| env.secrets[0].name | string | `"DB_USER"` | 环境变量名 |
| env.secrets[1].key | string | `"db_password"` |  |
| env.secrets[1].name | string | `"DB_PWD"` |  |
| env.secrets[2].key | string | `"ak_value"` |  |
| env.secrets[2].name | string | `"AK"` |  |
| env.secrets[3].key | string | `"sk_value"` |  |
| env.secrets[3].name | string | `"SK"` |  |
| env.secrets[4].key | string | `"upload_username"` |  |
| env.secrets[4].name | string | `"UPLOAD_USERNAME"` |  |
| env.secrets[5].key | string | `"upload_password"` |  |
| env.secrets[5].name | string | `"UPLOAD_PASSWORD"` |  |
| fullnameOverride | string | `"api-cve"` | 服务名，用于相关资源生成 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/cve-sa-backend/api-cve"` | 镜像名 |
| image.tag | string | `"main-91b561"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| ingress.annotations."kubernetes.io/ingress.class" | string | `"nginx"` | ingress类型 |
| ingress.annotations."nginx.ingress.kubernetes.io/configuration-snippet" | string | `"location /cve-security-notice-server/manager {\n  return 403;\n} \n"` | 自定义添加nginx配置项 |
| ingress.className | string | `"nginx"` | ingress类型 |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.hosts[0].host | string | `"api-cve.openeuler.org"` | 域名 |
| ingress.hosts[0].paths[0].path | string | `"/"` | 路径匹配规则 |
| ingress.hosts[0].paths[0].port | int | `8080` | service对外端口 |
| ingress.tls[0].hosts[0] | string | `"api-cve.openeuler.org"` | 域名 |
| ingress.tls[0].secretName | string | `"openeuler-api-cve-tls"` | tls secret名称 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.initialDelaySeconds | int | `10` | 容器初始化等待时间 |
| livenessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.tcpSocket.port | int | `8080` | 服务暴露端口 |
| livenessProbe.timeoutSeconds | int | `5` | 超时时间 |
| nameOverride | string | `"api-cve"` | 服务名，用于相关资源生成 |
| namespace | string | `"api-cve"` | 命名空间名称 |
| nodeSelector | object | `{}` | 节点选择标签 |
| podAnnotations | object | `{}` | 自定义声明项 |
| podSecurityContext.fsGroup | int | `1000` | 文件系统所属组 |
| readinessProbe.failureThreshold | int | `3` | 失败重试次数 |
| readinessProbe.initialDelaySeconds | int | `10` | 容器初始化等待时间 |
| readinessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| readinessProbe.successThreshold | int | `1` | 成功标志次数 |
| readinessProbe.tcpSocket.port | int | `8080` | 服务暴露端口 |
| readinessProbe.timeoutSeconds | int | `5` | 超时时间 |
| replicaCount | int | `2` | 容器副本数 |
| replicaCountCronjob | int | `1` | 定时任务容器副本数 |
| resources.limits.cpu | string | `"2000m"` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"2000Mi"` | 容器运行限制内存资源 |
| resources.requests.cpu | string | `"2000m"` | 容器运行最少所需CPU资源 |
| resources.requests.memory | string | `"2000Mi"` | 容器运行最少所需内存资源 |
| secretdefine.enabled | bool | `true` | 是否渲染secretdefine资源 |
| secretdefine.secret.ak_value.key | string | `"ak_value"` | 在Vault中引用的键名 |
| secretdefine.secret.ak_value.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| secretdefine.secret.db_password.key | string | `"db_password"` | 在Vault中引用的键名 |
| secretdefine.secret.db_password.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| secretdefine.secret.db_user.key | string | `"db_user"` | 在Vault中引用的键名 |
| secretdefine.secret.db_user.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| secretdefine.secret.sk_value.key | string | `"sk_value"` | 在Vault中引用的键名 |
| secretdefine.secret.sk_value.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| secretdefine.secret.upload_password.key | string | `"upload_password"` | 在Vault中引用的键名 |
| secretdefine.secret.upload_password.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| secretdefine.secret.upload_username.key | string | `"upload_username"` | 在Vault中引用的键名 |
| secretdefine.secret.upload_username.path | string | `"secrets/data/openeuler/api-cve"` | secret在vault中存放的路径 |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 移除Linux系统所有能力 |
| securityContext.runAsUser | int | `1000` | 限制容器运行的UID |
| service.ports.name | string | `"http"` | 端口名称 |
| service.ports.port | int | `8080` | service对外端口 |
| service.ports.protocol | string | `"TCP"` | 转发协议 |
| service.ports.targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| serviceAccount.annotations | object | `{}` | sa自定义声明项 |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa,默认false |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"api-cve"` | sa名称 |
| strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| tolerations | list | `[]` | 污点策略 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 8 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-8-4

### 说明
- 初始版本发布

## 1.0.3 - 2026-2-28

### 说明
- 1.0.3： 增加autoscale配置