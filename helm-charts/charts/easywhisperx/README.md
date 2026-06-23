# easywhisperx

## 📖 服务介绍 (Service Overview)

A Helm chart for easywhisperx

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能

### 底层组件

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| chenglang | chenglang11@huawei.com |  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| annotations | object | `{}` | 自定义声明项
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| image.repository | string | `"opensourceways-w5peto.swr-pro.myhuaweicloud.com/opensourceways/easywhisperx-server"` | 镜像名 |
| image.tag | string | `"9c096194"` | 镜像tag |
| imagePullSecrets[0].name | string | `"huawei-swr-instance-image-pull-secret"` | 镜像仓访问凭证名称 |
| service.port | int | `8000` | 服务暴露端口 |
| service.name | string | `"http"` | 端口名 |
| replicaCount | int | `1` | pod副本数 |
| strategyType | string | `"Recreate"` | 更新策略 |
| fullnameOverride | string | `"easywhisperx"` | 服务名，用于相关资源渲染 |
| ingress.enabled | bool | `true` | 是否启用ingress |
| nameOverride | string | `""` | 服务名，用于相关资源渲染 |
| namespace | string | `"easywhisperx"` | 命名空间名称 |
| pvc.accessModes | string | `"ReadWriteMany"` | pvc访问模式 |
| pvc.annotations | object | `{}` | 自定义声明项 |
| pvc.enabled | bool | `true` | 是否渲染该pvc资源 |
| pvc.storage | string | `"1Gi"` | 磁盘容量 |
| pvc.storageClassName | string | `"sfsturbo-subpath-sc"` | 存储类型 |
| pvc.volumeMode | string | `"Filesystem"` | 卷模式 |
| resources.limits.cpu | string | `"1"` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"1Gi"` | 容器运行限制内存资源 |
| resources.requests.cpu | string | `"1"` | 容器运行最少所需CPU资源 |
| resources.requests.memory | string | `"1Gi"` | 容器运行最少所需内存资源 |
| volumeMounts[0].mountPath | string | `"r"` | 卷挂载在容器里的路径 |
| volumeMounts[0].name | string | `"data"` | 卷名 |
| volumes[0].name | string | `"data"` | 卷名 |
| volumes[0].persistentVolumeClaim.claimName | string | `""` | pvc名称 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2026-05-18

### 说明
- 初始版本发布