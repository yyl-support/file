# patchwork

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

A Helm chart for patchwork
## 📖 服务介绍 (Service Overview)

> Patchwork是一个将补丁邮件自动转换为Pull Request的工具，目前主要服务于https://gitee.com/openeuler/kernel仓库的开发者。
### 依赖
1. Kubernetes 1.19+
2. Helm 3.2.0+


### 核心功能
* 用户发送补丁邮件到指定的邮件列表，根据补丁邮件自动在openeuler/kernel仓库创建对应的Pull Request，并发送邮件通知用户。

### 底层组件
该服务在启动和运行过程中依赖：
* **Database**: PostgreSQL 12.22
* 依赖邮件列表服务和dovecot服务

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| fuyong | fuyong@h-partners.com | Coopermasaaki |

## 部署说明

### Helm chart values说明

| 参数名 | 参数类型 | 默认值 | 描述 |
|-----|------|---------|-------------|
| cronjobs[0] | object | `{"affinityExpressions":[{"key":"app","operator":"In","values":["patchwork"]}],"annotations":{},"concurrencyPolicy":"Forbid","name":"patch2pr","resources":{"limits":{"cpu":"200m","memory":"2Gi"},"requests":{"cpu":"200m","memory":"2Gi"}},"restartPolicy":"OnFailure","schedule":"*/5 * * * *","suspend":false}` | 定时任务名称 |
| cronjobs[0].annotations | object | `{}` | 自定义声明项 |
| cronjobs[0].concurrencyPolicy | string | `"Forbid"` | 并发策略，一般为Forbid |
| cronjobs[0].resources.limits.cpu | string | `"200m"` | 服务分配cpu资源 |
| cronjobs[0].resources.limits.memory | string | `"2Gi"` | 服务分配内存资源 |
| cronjobs[0].resources.requests.cpu | string | `"200m"` | 服务需求cpu资源 |
| cronjobs[0].resources.requests.memory | string | `"2Gi"` | 服务需求内存资源 |
| cronjobs[0].restartPolicy | string | `"OnFailure"` | 失败重试设置 |
| cronjobs[0].schedule | string | `"*/5 * * * *"` | 触发周期设定 |
| cronjobs[0].suspend | bool | `false` | 是否停止运行 |
| cronjobs[1].affinityExpressions[0].key | string | `"app"` |  |
| cronjobs[1].affinityExpressions[0].operator | string | `"In"` |  |
| cronjobs[1].affinityExpressions[0].values[0] | string | `"patchwork"` |  |
| cronjobs[1].annotations | object | `{}` | 自定义声明项 |
| cronjobs[1].concurrencyPolicy | string | `"Forbid"` | 并发策略，一般为Forbid |
| cronjobs[1].name | string | `"refresh-repos"` |  |
| cronjobs[1].resources.limits.cpu | string | `"200m"` | 服务分配cpu资源 |
| cronjobs[1].resources.limits.memory | string | `"2Gi"` | 服务分配内存资源 |
| cronjobs[1].resources.requests.cpu | string | `"200m"` | 服务需求cpu资源 |
| cronjobs[1].resources.requests.memory | string | `"2Gi"` | 服务需求内存资源 |
| cronjobs[1].restartPolicy | string | `"OnFailure"` | 失败重试设置 |
| cronjobs[1].schedule | string | `"0 2 * * *"` | 触发周期设定 |
| cronjobs[1].suspend | bool | `false` | 是否停止运行 |
| deployment.command | list | `["/bin/sh","-c","python manage.py makemigrations\npython manage.py migrate\npython manage.py loaddata default_tags default_states\npython manage.py collectstatic\npython manage.py runserver 0.0.0.0:8000\n"]` | pod启动命令 |
| deployment.name | string | `"patchwork"` | deployment资源名称 |
| deployment.podLabels | object | `{"app":"pathwork"}` | pod标签 |
| deployment.replicas | int | `1` | pod副本数量 |
| deployment.resources.limits.cpu | string | `"2"` | 服务分配cpu资源 |
| deployment.resources.limits.memory | string | `"3Gi"` | 服务分配内存资源 |
| deployment.resources.requests.cpu | string | `"200m"` | 服务需求cpu资源 |
| deployment.resources.requests.memory | string | `"1Gi"` | 服务需求内存资源 |
| env | list | `[{"key":"DATABASE_NAME","name":"DATABASE_NAME"},{"key":"DATABASE_HOST","name":"DATABASE_HOST"},{"key":"DATABASE_USER","name":"DATABASE_USER"},{"key":"DATABASE_PASSWORD","name":"DATABASE_PASSWORD"},{"key":"DATABASE_PORT","name":"DATABASE_PORT"},{"key":"EMAIL_HOST","name":"EMAIL_HOST"},{"key":"EMAIL_PORT","name":"EMAIL_PORT"},{"key":"EMAIL_HOST_USER","name":"EMAIL_HOST_USER"},{"key":"EMAIL_HOST_PASSWORD","name":"EMAIL_HOST_PASSWORD"},{"key":"DJANGO_SECRET_KEY","name":"DJANGO_SECRET_KEY"},{"key":"PATCHWORK_SERVER","name":"PATCHWORK_SERVER"},{"key":"PATCHWORK_TOKEN","name":"PATCHWORK_TOKEN"},{"key":"REPO_OWNER","name":"REPO_OWNER"},{"key":"GITEE_TOKEN","name":"GITEE_TOKEN"},{"key":"GITEE_TOKEN_NOT_CI_BOT","name":"GITEE_TOKEN_NOT_CI_BOT"},{"key":"SEND_EMAIL_HOST","name":"SEND_EMAIL_HOST"},{"key":"SEND_EMAIL_HOST_USER","name":"SEND_EMAIL_HOST_USER"},{"key":"SEND_EMAIL_HOST_PASSWORD","name":"SEND_EMAIL_HOST_PASSWORD"},{"key":"SEND_EMAIL_PORT","name":"SEND_EMAIL_PORT"},{"key":"CI_BOT_EMAIL","name":"CI_BOT_EMAIL"},{"key":"CI_BOT_NAME","name":"CI_BOT_NAME"},{"key":"SRC_OPENEULER_KERNEL_HOST","name":"SRC_OPENEULER_KERNEL_HOST"},{"key":"SRC_OPENEULER_KERNEL_PASS","name":"SRC_OPENEULER_KERNEL_PASS"},{"key":"OPENEULER_KERNEL_HOST","name":"OPENEULER_KERNEL_HOST"},{"key":"OPENEULER_KERNEL_PASS","name":"OPENEULER_KERNEL_PASS"},{"key":"IMAP_SERVER","name":"IMAP_SERVER"},{"key":"IMAP_PORT","name":"IMAP_PORT"},{"key":"SEND_EMAIL_DOMAIN","name":"SEND_EMAIL_DOMAIN"},{"key":"SRC_OPENEULER_KERNEL_HOST","name":"SRC_OPENEULER_KERNEL_HOST"},{"key":"SRC_OPENEULER_KERNEL_PASS","name":"SRC_OPENEULER_KERNEL_PASS"}]` | 环境变量数组 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/patchwork/patchwork-gitcode"` | 镜像名称 |
| image.tag | string | `"fuyong-dev-b0d109"` | 镜像Tag |
| imagePullSecrets | list | `[{"name":"huawei-swr-image-pull-secret"}]` | 镜像仓库访问凭证名称 |
| livenessProbe.failureThreshold | int | `5` | 探测失败的重试次数 |
| livenessProbe.initialDelaySeconds | int | `20` | 延迟加载时间 |
| livenessProbe.periodSeconds | int | `5` | 重试时间间隔 |
| livenessProbe.tcpSocket.port | int | `8000` | tcp探测端口号 |
| livenessProbe.timeoutSeconds | int | `10` | 超时时间设置 |
| namespace.name | string | `"patchwork"` | 命名空间名称 |
| podAnnotations | object | `{}` | pod自定义声明项 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` |  |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` |  |
| pvc.accessModes | string | `"ReadWriteOnce"` | 访问模式，与磁盘类型有关 |
| pvc.name | string | `"patchwork-pvc"` | pvc名称 |
| pvc.storage | string | `"50Gi"` | 磁盘容量 |
| pvc.storageClass | string | `"csi-disk"` | 存储类型 |
| readinessProbe.failureThreshold | int | `5` | 探测失败的重试次数 |
| readinessProbe.initialDelaySeconds | int | `20` | 延迟加载时间 |
| readinessProbe.periodSeconds | int | `5` | 重试时间间隔 |
| readinessProbe.tcpSocket.port | int | `8000` | tcp探测端口号 |
| readinessProbe.timeoutSeconds | int | `10` | 超时时间设置 |
| secret.keysMap | object | `{"CI_BOT_EMAIL":"CI_BOT_EMAIL","CI_BOT_NAME":"CI_BOT_NAME","DATABASE_HOST":"DATABASE_HOST","DATABASE_NAME":"DATABASE_NAME","DATABASE_PASSWORD":"DATABASE_PASSWORD","DATABASE_PORT":"DATABASE_PORT","DATABASE_USER":"DATABASE_USER","DJANGO_SECRET_KEY":"DJANGO_SECRET_KEY","EMAIL_HOST":"EMAIL_HOST","EMAIL_HOST_PASSWORD":"EMAIL_HOST_PASSWORD","EMAIL_HOST_USER":"EMAIL_HOST_USER","EMAIL_PORT":"EMAIL_PORT","GITEE_TOKEN":"GITEE_TOKEN","GITEE_TOKEN_NOT_CI_BOT":"GITEE_TOKEN_NOT_CI_BOT","IMAP_PORT":"IMAP_PORT","IMAP_SERVER":"IMAP_SERVER","OPENEULER_KERNEL_HOST":"OPENEULER_KERNEL_HOST","OPENEULER_KERNEL_PASS":"OPENEULER_KERNEL_PASS","PATCHWORK_SERVER":"PATCHWORK_SERVER","PATCHWORK_TOKEN":"PATCHWORK_TOKEN","REPO_OWNER":"REPO_OWNER","SEND_EMAIL_DOMAIN":"SEND_EMAIL_DOMAIN","SEND_EMAIL_HOST":"SEND_EMAIL_HOST","SEND_EMAIL_HOST_PASSWORD":"SEND_EMAIL_HOST_PASSWORD","SEND_EMAIL_HOST_USER":"SEND_EMAIL_HOST_USER","SEND_EMAIL_PORT":"SEND_EMAIL_PORT","SRC_OPENEULER_KERNEL_HOST":"SRC_OPENEULER_KERNEL_HOST","SRC_OPENEULER_KERNEL_PASS":"SRC_OPENEULER_KERNEL_PASS"}` | secret key在vault中key的对应关系 |
| secret.name | string | `"patchwork-secrets"` | secret名称 |
| secret.path | string | `"secrets/data/openeuler/patchwork-gitcode"` | secret在vault中的存放路径 |
| service.name | string | `"patchwork"` | service名称 |
| service.ports[0].name | string | `"httpport"` |  |
| service.ports[0].port | int | `80` | 对外访问端口 |
| service.ports[0].protocol | string | `"TCP"` | 转发通信协议 |
| service.ports[0].targetPort | int | `8000` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本上限数 |
| strategy.rollingUpdate.maxUnavailable | int | `0` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumeMounts[0] | object | `{"mountPath":"/home/patches","name":"patchwork-file-volume"}` | 挂载路径 |
| volumeMounts[0].name | string | `"patchwork-file-volume"` | 挂载卷名 |
| volumeMounts[1].mountPath | string | `"/home/patchwork/repositories_branches_map.yaml"` |  |
| volumeMounts[1].name | string | `"patchwork-configmap"` | 挂载卷名 |
| volumeMounts[1].subPath | string | `"repositories_branches_map.yaml"` |  |
| volumes[0] | object | `{"name":"patchwork-file-volume","persistentVolumeClaim":{"claimName":"patchwork-pvc"}}` | 挂载卷名 |
| volumes[1].configMap.name | string | `"patchwork-configmap"` | configmap资源名称 |
| volumes[1].name | string | `"patchwork-configmap"` |  |



## 变更历史

## 1.0.0 - 2025-12-03

### 说明
- 初始版本发布

## 1.0.1 - 2025-12-22

### 说明
- 修改模板一处错误

