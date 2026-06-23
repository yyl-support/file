# image-scanning

![Version: 1.0.2](https://img.shields.io/badge/Version-1.0.2-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
为容器镜像提供漏洞扫描服务

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 手动构建trivy工具链，以支持把openeuler作为操作系统的镜像的扫描
* 从代码平台的配置文件同步需要扫描的镜像信息
* 拉取镜像，并利用trivy工具扫描漏洞
* 将扫描结果上传至代码平台

### 底层组件
* PostgreSQL 14+，依赖`image_scanning`库
### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| yangwei | yangwei266@h-partners.com | yangwei999 |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | 亲和策略 |
| args[0] | string | `"--config-file=/vault/secrets/config.yaml"` | 配置文件绝对路径 |
| env[0].name | string | `"TZ"` | 环境变量名 |
| env[0].value | string | `"Asia/Shanghai"` | 环境变量值 |
| fullnameOverride | string | `"image-scanning"` | 服务名称 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/image-scanning"` | 镜像名 |
| image.tag | string | `"dev-505671"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| initContainers[0].command[0] | string | `"/bin/bash"` | 启动命令 |
| initContainers[0].command[1] | string | `"-c"` | 启动命令 |
| initContainers[0].command[2] | string | `"chmod 0700 /vault/secrets/; chown -R 1000:1000 /vault/secrets/; chmod g-s /vault/secrets/; ls -ld /vault/secrets/"` | 启动命令 |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler:22.03-lts-sp3"` | 初始化容器镜像名 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| initContainers[0].name | string | `"init-openeuler"` | 容器名称 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.httpGet.path | string | `"/"` | 健康检查接口 |
| livenessProbe.httpGet.port | int | `8080` | 服务暴露端口 |
| livenessProbe.httpGet.scheme | string | `"HTTP"` | 请求协议 |
| livenessProbe.initialDelaySeconds | int | `20` | 容器初始化等待时间 |
| livenessProbe.periodSeconds | int | `10` | 触发检查的间隔时间 |
| livenessProbe.successThreshold | int | `1` | 成功标志次数 |
| livenessProbe.timeoutSeconds | int | `10` | 超时时间 |
| nameOverride | string | `"image-scanning"` | 服务名称 |
| namespace | string | `"image-scanning"` | 命名空间名称 |
| nodeSelector."kubernetes.io/arch" | string | `"amd64"` | 节点选择标签 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-config.yaml" | string | `"0400"` | 配置文件属性 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-config.yaml" | string | `"internal/data/openeuler/image-scanning"` | 配置文件在vault中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-config.yaml" | string | `"{{- with secret \"internal/data/openeuler/image-scanning\" -}} \n{{ .Data.data.conf }}\n{{- end }}\n"` | 配置文件渲染模版 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | agent容器运行用户组 |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | agent容器运行用户 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | sa token名称 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"image-scanning"` | vault权限角色 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | agent与server通信是否跳过验证 |
| podSecurityContext.seccompProfile.localhostProfile | string | `"infra-seccomp.json"` | 安全策略文件名 |
| podSecurityContext.seccompProfile.type | string | `"Localhost"` | 安全策略文件类型 |
| pvc.accessModes | string | `"ReadWriteOnce"` | pvc访问模式 |
| pvc.enabled | bool | `true` | 是否渲染pvc资源 |
| pvc.name | string | `"image-scanning-data-storage"` | pvc名称 |
| pvc.storage | string | `"1Ti"` | 磁盘容量 |
| pvc.storageClassName | string | `"csi-disk"` | 存储类型 |
| pvc.volumeMode | string | `"Filesystem"` | 卷模式 |
| pvc.volumeName | object | `{}` | 卷名 |
| readinessProbe.failureThreshold | int | `3` |  |
| readinessProbe.httpGet.path | string | `"/"` |  |
| readinessProbe.httpGet.port | int | `8080` |  |
| readinessProbe.httpGet.scheme | string | `"HTTP"` |  |
| readinessProbe.initialDelaySeconds | int | `20` |  |
| readinessProbe.periodSeconds | int | `10` |  |
| readinessProbe.successThreshold | int | `1` |  |
| readinessProbe.timeoutSeconds | int | `10` |  |
| replicaCount | int | `1` | pod副本数 |
| resources.limits.cpu | string | `"2000m"` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"16Gi"` | 容器运行限制内存资源 |
| resources.requests.cpu | string | `"2000m"` | 容器运行最少所需CPU资源 |
| resources.requests.memory | string | `"12Gi"` | 容器运行最少所需内存资源 |
| securityContext.capabilities.drop[0] | string | `"ALL"` | 移除所有linux能力 |
| securityContext.runAsUser | int | `1000` | 限制容器运行的UID |
| serviceAccount.annotations | object | `{}` | sa自定义声明项 |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa |
| serviceAccount.create | bool | `true` | 是否渲染sa资源 |
| serviceAccount.name | string | `"image-scanning"` | sa名称 |
| strategy.type | string | `"Recreate"` | 更新策略 |
| tolerations | list | `[]` | 污点策略 |
| volumeMounts[0].mountPath | string | `"/opt/app/persistent"` | 挂载在容器中的路径 |
| volumeMounts[0].name | string | `"data-vol"` | 卷名 |
| volumes[0].name | string | `"token-vol"` | 卷名 |
| volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` | sa受众 |
| volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` | 过期时间 |
| volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` | 挂载路径下的文件名 |
| volumes[1].name | string | `"data-vol"` | 卷名 |
| volumes[1].persistentVolumeClaim.claimName | string | `"image-scanning-data-storage"` | pvc名称 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-9-3

### 说明
- 初始版本发布

## 1.0.3 - 2026-2-28

### 说明
- 添加autoscale配置