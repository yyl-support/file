# osi-task

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)


## 📖 服务介绍 (Service Overview)

用于各社区开源实习项目后端服务


### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
1. 统计注册人员信息, 区分学生导师权限
2. 提供命令行操作：领取任务，完成任务，取消任务等功能
3. 计算学生完成任务情况并统计

### 底层组件
* **Database**: [MySQL v1.6.0]

### 维护者

| 名称      |           邮箱              |  Github ID |
|-----------|-----------------------------|------------|
|   谢承志   |  xiechengzhi3@h-partners.com| 2511689622 |

### Helm chart values说明


| Key | Type | Default | Description |
|-----|------|---------|-------------|
| env[0].key | string | `"db-username"` | 环境变量值引用自secret中的key名 |
| env[0].name | string | `"DB_USER"` | 环境变量名 |
| env[1].key | string | `"db-passwd"` | 环境变量值引用自secret中的key名 |
| env[1].name | string | `"DB_PWD"` | 环境变量名 |
| env[2].key | string | `"db-uri"` | 环境变量值引用自secret中的key名 |
| env[2].name | string | `"DB_URI"` | 环境变量名 |
| env[3].key | string | `"aes-key"` | 环境变量值引用自secret中的key名 |
| env[3].name | string | `"AES_KEY"` | 环境变量名 |
| env[4].key | string | `"osi-hook-pwd"` | 环境变量值引用自secret中的key名 |
| env[4].name | string | `"OSI_HOOK_PWD"` | 环境变量名 |
| env[5].key | string | `"gitee-token"` | 环境变量值引用自secret中的key名 |
| env[5].name | string | `"GITEE_SRC_TOKEN"` | 环境变量名 |
| env[6].key | string | `"cve-email-sendaddr"` | 环境变量值引用自secret中的key名 |
| env[6].name | string | `"EMAIL_NAME"` | 环境变量名 |
| env[7].key | string | `"cve-email-password"` | 环境变量值引用自secret中的key名 |
| env[7].name | string | `"EMAIL_PWD"` | 环境变量名 |
| env[8].key | string | `"gitee-lookeng-token"` | 环境变量值引用自secret中的key名 |
| env[8].name | string | `"GITEE_LOOKENG_TOKEN"` | 环境变量名 |
| env[9].key | string | `"gitee-gauss-token"` | 环境变量值引用自secret中的key名 |
| env[9].name | string | `"GITEE_GAUSS_TOKEN"` | 环境变量名 |
| fullnameOverride | string | `"osi-task-gitcode"` | 服务资源名称 |
| image.pullPolicy | string | `"Always"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler/osi-task-manager-gitcode"` | 镜像名称 |
| image.tag | string | `"hot_test-d37ed7"` | 镜像tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| livenessProbe.failureThreshold | int | `5` | 健康检查失败重试次数 |
| livenessProbe.httpGet.path | string | `"/healthz/readiness"` | 检查接口 |
| livenessProbe.httpGet.port | int | `8080` | 健康检查端口号 |
| livenessProbe.initialDelaySeconds | int | `20` | 延迟加载时间 |
| livenessProbe.periodSeconds | int | `5` | 健康检查周期 |
| livenessProbe.timeoutSeconds | int | `10` | 健康检查超时 |
| nameOverride | string | `""` | 服务名 |
| namespace.name | string | `"osi-task-manager"` | 命名空间名称 |
| podAnnotations | object | `{}` | pod自定义声明项 |
| podLabels.app | string | `"osi-task-gitcode"` |  |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 配置seccomp配置文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 配置seccomp类型 |
| readinessProbe.failureThreshold | int | `5` | 健康检查失败重试次数 |
| readinessProbe.httpGet.path | string | `"/healthz/readiness"` | 检查接口 |
| readinessProbe.httpGet.port | int | `8080` | 健康检查端口号 |
| readinessProbe.initialDelaySeconds | int | `20` | 延迟加载时间 |
| readinessProbe.periodSeconds | int | `5` | 健康检查周期 |
| readinessProbe.timeoutSeconds | int | `10` | 健康检查超时 |
| replicas | int | `1` | pod副本数量 |
| resources.limits.cpu | string | `"2"` | 服务分配cpu资源 |
| resources.limits.memory | string | `"3Gi"` | 容器资源配置 |
| resources.requests.cpu | string | `"200m"` | 服务需求cpu资源 |
| resources.requests.memory | string | `"1Gi"` | 容器资源配置 |
| secret.keysMap.aes-key | string | `"aes-key"` | secret资源中的key名 |
| secret.keysMap.cve-email-password | string | `"cve-email-password"` | secret资源中的key名 |
| secret.keysMap.cve-email-sendaddr | string | `"cve-email-sendaddr"` | secret资源中的key名 |
| secret.keysMap.db-passwd | string | `"db-passwd"` | secret资源中的key名 |
| secret.keysMap.db-uri | string | `"db-uri"` | secret资源中的key名 |
| secret.keysMap.db-username | string | `"db-username"` | secret资源中的key名 |
| secret.keysMap.gitee-gauss-token | string | `"gitee-gauss-token"` | secret资源中的key名 |
| secret.keysMap.gitee-lookeng-token | string | `"gitee-lookeng-token"` | secret资源中的key名 |
| secret.keysMap.gitee-token | string | `"gitee-token"` | secret资源中的key名 |
| secret.keysMap.osi-hook-pwd | string | `"osi-hook-pwd"` | secret资源中的key名 |
| secret.name | string | `"osi-task-gitcode-secrets"` | secret名称 |
| secret.path | string | `"secrets/data/openeuler/osi-task-gitcode"` | 配置在vault中的存放路径 |
| servicePorts[0].name | string | `"httpport"` | 端口名 |
| servicePorts[0].port | int | `80` | service端口号 |
| servicePorts[0].protocol | string | `"TCP"` | 端口对应的协议 |
| servicePorts[0].targetPort | int | `8000` | 容器监听端口号 |
| serviceType | string | `"ClusterIP"` | 服务对外暴露范围，仅集群内可访问 |
| strategy.rollingUpdate.maxSurge | int | `1` | 滚动升级过程最大增加副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 升级类型 |

## 变更历史

## 1.0.0 - 2025-12-02

### 说明
- 初始版本发布

## 1.0.1 - 2026-1-30
### 说明
- 添加deployment label
