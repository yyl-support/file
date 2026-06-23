# etherpad

![Version: 1.0.5](https://img.shields.io/badge/Version-1.0.5-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for etherpad

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能

### 底层组件

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
|  |  |  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| deployment.containerName | string | `"etherpad-lite"` | 容器名 |
| deployment.annotations | object | `{}` | 自定义声明项
| deployment.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| deployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/etherpad"` | 镜像名 |
| deployment.image.tag | string | `"openeuler-v1.9.7-sso-9629f0"` | 镜像tag |
| deployment.imagePullSecrets[0].name | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| deployment.labels.app | string | `"control-etherpad-v2"` | pod标签 |
| deployment.ports[0].containerPort | int | `9001` | 服务暴露端口 |
| deployment.ports[0].name | string | `"http"` | 端口名 |
| deployment.ports[0].protocol | string | `"TCP"` | 通信协议 |
| deployment.replicaCount | int | `1` | pod副本数 |
| deployment.strategyType | string | `"Recreate"` | 更新策略 |
| fullnameOverride | string | `"openeuler-etherpad"` | 服务名，用于相关资源渲染 |
| ingress.annotations."nginx.ingress.kubernetes.io/cors-allow-credentials" | string | `"false"` | 是否允许跨域请求携带认证信息 |
| ingress.annotations."nginx.ingress.kubernetes.io/server-snippet" | string | `"location ^~ /admin {\n  deny all;\n}\nlocation ^~ /stats {\n  deny all;\n}\n"` | 拦截高危接口请求 |
| ingress.className | string | `"nginx"` | ingress类型 |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.hosts[0].host | string | `"etherpad.openeuler.org"` | 域名 |
| ingress.hosts[0].paths[0].path | string | `"/"` | 匹配路径 |
| ingress.hosts[0].paths[0].pathType | string | `"Prefix"` | 匹配规则 |
| ingress.hosts[0].paths[0].portNumber | int | `9001` | service对外端口 |
| ingress.tlsHosts[0].host | string | `"etherpad.openeuler.org"` | 域名 |
| ingress.tlsHosts[0].secretsName | string | `"etherpad-openeuler-tls"` | tls secret名称 |
| istio.enabled | bool | `false` | 是否启用istio |
| istio.nslabel | object | `{}` | 启用istio时命名空间所需标签 |
| nameOverride | string | `""` | 服务名，用于相关资源渲染 |
| namespace | string | `"openeuler-etherpad"` | 命名空间名称 |
| pvc.ether-data-vol-v2.accessModes[0] | string | `"ReadWriteOnce"` | pvc访问模式 |
| pvc.ether-data-vol-v2.annotations | object | `{}` | 自定义声明项 |
| pvc.ether-data-vol-v2.enabled | bool | `true` | 是否渲染该pvc资源 |
| pvc.ether-data-vol-v2.labels | object | `{}` | pvc标签 |
| pvc.ether-data-vol-v2.storage | string | `"1Gi"` | 磁盘容量 |
| pvc.ether-data-vol-v2.storageClassName | string | `"csi-disk-sas"` | 存储类型 |
| pvc.ether-data-vol-v2.volumeMode | string | `"Filesystem"` | 卷模式 |
| pvc.ether-data-vol-v2.volumeName | string | `"pvc-9da11407-3848-4e7f-8a36-a71006dd7536"` | 卷名 |
| pvc.etherpad-plugin-vol.accessModes[0] | string | `"ReadWriteOnce"` |  |
| pvc.etherpad-plugin-vol.annotations."everest.io/disk-volume-type" | string | `"SSD"` |  |
| pvc.etherpad-plugin-vol.enabled | bool | `false` |  |
| pvc.etherpad-plugin-vol.labels."failure-domain.beta.kubernetes.io/region" | string | `"ap-southeast-1"` | 指定区域 |
| pvc.etherpad-plugin-vol.labels."failure-domain.beta.kubernetes.io/zone" | string | `"ap-southeast-1c"` | 指定可用区|
| pvc.etherpad-plugin-vol.storage | string | `"1Gi"` |  |
| pvc.etherpad-plugin-vol.storageClassName | string | `"csi-disk"` |  |
| pvc.etherpad-plugin-vol.volumeMode | string | `"Filesystem"` |  |
| pvc.etherpad-plugin-vol.volumeName | string | `""` |  |
| resources.limits.cpu | string | `"2"` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"4000Mi"` | 容器运行限制内存资源 |
| resources.requests.cpu | string | `"2"` | 容器运行最少所需CPU资源 |
| resources.requests.memory | string | `"4000Mi"` | 容器运行最少所需内存资源 |
| secretDefinitions.ether-secret-v2.enabled | bool | `true` | 是否渲染该secret资源 |
| secretDefinitions.ether-secret-v2.keysMap.admin_password.key | string | `"admin_password_v2"` | 在vault中对应的键名 |
| secretDefinitions.ether-secret-v2.keysMap.admin_password.path | string | `"secrets/data/infra-common/openeuler-etherpad"` | 在vault中存放的路径 |
| secretDefinitions.ether-secret-v2.keysMap.db_charset.key | string | `"db_charset_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_charset.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_host.key | string | `"db_host_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_host.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_name.key | string | `"db_name_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_name.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_password.key | string | `"db_password_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_password.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_port.key | string | `"db_port_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_port.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_type.key | string | `"db_type_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_type.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_user.key | string | `"db_user_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.db_user.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.env.key | string | `"env_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.env.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.issuer_client_id.key | string | `"issuer_client_id"` |  |
| secretDefinitions.ether-secret-v2.keysMap.issuer_client_id.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.issuer_client_secret.key | string | `"issuer_client_secret"` |  |
| secretDefinitions.ether-secret-v2.keysMap.issuer_client_secret.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.port.key | string | `"port_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.port.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.ether-secret-v2.keysMap.skin.key | string | `"skin_v2"` |  |
| secretDefinitions.ether-secret-v2.keysMap.skin.path | string | `"secrets/data/infra-common/openeuler-etherpad"` |  |
| secretDefinitions.etherpad-openeuler-tls.enabled | bool | `true` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."ca.crt".key | string | `"server.crt"` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."ca.crt".path | string | `"secrets/data/openeuler/openeuler-org-tls"` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."tls.crt".key | string | `"server.crt"` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."tls.crt".path | string | `"secrets/data/openeuler/openeuler-org-tls"` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."tls.key".key | string | `"server.key"` |  |
| secretDefinitions.etherpad-openeuler-tls.keysMap."tls.key".path | string | `"secrets/data/openeuler/openeuler-org-tls"` |  |
| service.ports[0].name | string | `"ether-http"` | 端口名 |
| service.ports[0].port | int | `9001` | service对外端口 |
| service.ports[0].protocol | string | `"TCP"` | 转发协议 |
| service.ports[0].targetPort | int | `9001` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | service类型 |
| volumeMounts[0].mountPath | string | `"/opt/etherpad-lite/var"` | 卷挂载在容器里的路径 |
| volumeMounts[0].name | string | `"data-volume"` | 卷名 |
| volumes[0].name | string | `"data-volume"` | 卷名 |
| volumes[0].persistentVolumeClaim.claimName | string | `"ether-data-vol-v2"` | pvc名称 |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-6-23

### 说明
- 初始版本发布

## 1.0.6 - 2026-1-22

### 说明
- 支持适配CCI弹性插件标签

## 1.0.7 - 2026-1-31

### 说明
- 环境变量改为Vault密钥挂载

## 1.0.8 - 2026-2-28

### 说明
- 添加autoscale配置