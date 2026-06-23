
## 📖 服务介绍 (Service Overview)

A Helm chart for sync-model

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 功能点1，
* 功能点2，
* 功能点3，

### 底层组件
该服务在启动和运行过程中依赖：
* 持久存储

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| zhongyuanke |    | drizzlezyk |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| fullnameOverride | string | `""` | 服务名，用于相关资源名称渲染 |
| image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略，默认为IfNotPresent |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/sync-model"` | 镜像名称 |
| image.tag | string | `"master-ebb22c"` | 镜像Tag |
| imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓库访问凭证名称 |
| ingress.className | string | `"nginx"` | ingress class |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.host | string | `""` | 域名 |
| istio.nslabel | object | `{}` | 启用istio时命名空间所需标签 |
| nameOverride | string | `""` | 服务名称，可被fullnameOverride覆盖 |
| namespace.enabled | bool | `true` | 是否渲染namespace资源 |
| namespace.name | string | `""` | 命名空间名称 |
| replicaCount | int | `1` | 容器副本数量 |
| resources.limits.cpu | string | `"1"` | 服务最大使用CPU资源数 |
| resources.limits.memory | string | `"1Gi"` | 服务最大使用内存容量 |
| resources.requests.cpu | string | `"1"` | 服务最小需求CPU资源数 |
| resources.requests.memory | string | `"1Gi"` | 服务最小需求内存容量 |
| secret.crtKey | string | `"server.cert"` | vault中的key |
| secret.enabled | bool | `true` | 是否渲染secret资源 |
| secret.keyKey | string | `"server.key"` | vault中的key |
| secret.name | string | `"tls-secrets"` | secret资源名称 |
| secret.path | string | `"secrets/data/infra-common/osinfra-cn"` | secret在vault中存放的路径 |
| service.ports[0].name | string | `"http-port"` | 端口名 |
| service.ports[0].port | int | `8080` | service对外端口 |
| service.ports[0].protocol | string | `"TCP"` | service转发协议 |
| service.ports[0].targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型，默认为ClusterIP |
| strategy.rollingUpdate.maxSurge | int | `1` | 最大超出副本数 |
| strategy.rollingUpdate.maxUnavailable | int | `1` | 最大不可用副本数 |
| strategy.type | string | `"RollingUpdate"` | 更新策略 |
| volumeMounts[0].mountPath | string | `"/repo/opengauss"` | 挂载路径 |
| volumeMounts[0].name | string | `"data-volume"` | 卷名 |
| volumes[0].name | string | `"data-volume"` | 卷名 |
| volumes[0].persistentVolumeClaim.claimName | string | `"pvc-sync-model"` | pvc名称 |
| pvc.name | string | `"pvc-sync-model"` | pvc名称 |
| pvc.accessModes | string | `"ReadWriteMany"` | 访问模式 |
| pvc.size | string | `"100Gi"` | 容量大小 |
| pvc.storageClass | string | `"sfsturbo-subpath-sc"` | 存储类型 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |


## 变更历史

## 1.0.0 - 2026-3-26

### 说明
- 初始版本发布

## 1.0.1 - 2026-4-21

### 说明
- 移除deployment，autoscale模板，增加cronjob模板