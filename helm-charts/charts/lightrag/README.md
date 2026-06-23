# lightrag

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

A Helm chart for LightRAG, an efficient and lightweight RAG system

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| LightRAG Team |  |  |
| earayu | <earayu@gmail.com> |  |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/lightrag"` | 镜像名 |
| image.tag | string | `"v1.4.9.7"` | 镜像tag |
| persistence.enabled | bool | `true` | 是否启用持久存储 |
| persistence.accessModes | string | `ReadWriteOnce` | 访问模式，与存储类型有关 |
| persistence.storageClass | string | `csi-disk` | 存储类型 |
| persistence.inputs.size | string | `"30Gi"` | 磁盘容量 |
| persistence.ragStorage.size | string | `"50Gi"` | 磁盘容量 |
| replicaCount | int | `1` | Pod副本数 |
| resources.limits.cpu | string | `"2"` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"16Gi"` | 容器运行限制内存资源 |
| resources.requests.cpu | string | `"2"` | 容器运行最少所需CPU资源 |
| resources.requests.memory | string | `"8Gi"` | 容器运行最少所需内存资源 |
| secretPath | string | `"secrets/data/openubmc/lightrag"` | 配置文件在vault中存放路径 |
| service.port | int | `9621` | service对外端口 |
| service.targetPort | int | `9621` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 0.1.0 - 2025-10-27

### 说明
- 初始版本发布

## 1.0.0 - 2026-2-4

### 说明
- 支持pvc存储类自定义

## 1.0.1 - 2026-2-28

### 说明
- 增加autoscale配置

## 1.0.2 - 2026-3-09

### 说明
- 增加deployment自定义label