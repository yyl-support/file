# signatrust

![Version: 4.0.1](https://img.shields.io/badge/Version-4.0.1-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
helm chart for signatrust

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能

### 底层组件

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| lianghaoxing | lianghaoxing1@huawei.com |  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| app.commonAnnotations | object | `{}` | pod声明字段 |
| app.deployment.autoscaler | string | `"true"` | 是否对接弹性伸缩副本 |
| app.enabled | bool | `true` | 启用app |
| app.image.pullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| app.image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| app.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/signatrust-app"` | 镜像名 |
| app.image.tag | string | `"62bcd11fb8cd8dc813108a9e35106de94ae5d224"` | 镜像TAG |
| app.ingress.backend.serviceName | string | `"website-service"` | ingress后端service名 |
| app.ingress.backend.servicePort | int | `80` | ingress后端service端口号 |
| app.ingress.className | string | `"nginx"` | ingress资源名 |
| app.ingress.host | string | `"signatrust.openubmc.cn"` | 域名 |
| app.ingress.path | string | `"/"` | ingress转发路径匹配规格 |
| app.ingress.pathtype | string | `"Prefix"` | 转发策略 |
| app.ingress.secretName | string | `"website-tls"` | ingress使用tls密钥名 |
| app.name | string | `"website"` | app资源名称 |
| app.probes.failureThreshold | int | `3` | 健康检查失败重试次数 |
| app.probes.initialDelaySeconds | int | `10` | 健康检查初始检查延迟时间 |
| app.probes.periodSeconds | int | `10` | 健康检查周期 |
| app.probes.successThreshold | int | `1` | 健康检查成功次数 |
| app.probes.timeoutSeconds | int | `5` | 健康检查超时 |
| app.replicas | int | `1` | 副本数 |
| app.resources.limits.cpu | string | `"1000m"` | 容器资源配置 |
| app.resources.limits.memory | string | `"1000Mi"` | 容器资源配置 |
| app.resources.requests.cpu | string | `"500m"` | 容器资源配置 |
| app.resources.requests.memory | string | `"500Mi"` | 容器资源配置 |
| app.service.name | string | `"http-port"` | app service端口名 |
| app.service.port | int | `80` | app service端口号 |
| app.service.protocol | string | `"TCP"` | app service端口对应的协议 |
| app.service.targetPort | int | `8080` | app service端口对应的后端容器端口号 |
| app.service.type | string | `"ClusterIP"` | 网络开放范围,集群内有效 |
| app.strategy.rollingUpdate.maxSurge | int | `1` | 滚动升级过程最大增加副本数 |
| app.strategy.rollingUpdate.maxUnavailable | int | `0` | 滚动升级过程允许减少副本数 |
| app.strategy.type | string | `"RollingUpdate"` | 升级类型 |
| client.command[0] | string | `"/bin/sh"` | 启动参数 |
| client.command[1] | string | `"-c"` | 启动参数 |
| client.command[2] | string | `"mkdir -p /Users/tommylike/Work/codes/rust-projects/signatrust/.data/tempdir\nsleep 100000000\n"` | 启动参数 |
| client.configmap.data.client | string | `"working_dir = \"/app/data/\"\nworker_threads = 8\nbuffer_size = 20480\nmax_concurrency = 100\n[server]\ndomain_name = \"signatrust.openubmc.cn\"\ntype = \"dns\"\nserver_address = \"signatrust-data-server-service.signatrust.svc.cluster.local\"\nserver_port = \"8088\"\n"` | client配置文件 |
| client.configmap.name | string | `"signatrust-client-configmap"` | client configmap资源名 |
| client.enabled | bool | `true` | 启用client |
| client.env.name | string | `"RUST_LOG"` | 环境变量名 |
| client.env.value | string | `"debug"` | 环境变量值 |
| client.image.pullPolicy | string | `"Always"` | 镜像拉取策略 |
| client.image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| client.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/signatrust-client"` | 镜像名 |
| client.image.tag | string | `"62bcd11fb8cd8dc813108a9e35106de94ae5d224"` | 镜像TAG |
| client.mounts.certCrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/client/server.crt"` | 配置文件挂载路径 |
| client.mounts.certCrt.subPath | string | `"ca-crt"` | 配置文件在secret资源中的key名称 |
| client.mounts.certKey.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/client/server.key"` | 配置文件挂载路径 |
| client.mounts.certKey.subPath | string | `"ca-key"` | 配置文件在secret资源中的key名称 |
| client.mounts.config.mountPath | string | `"/app/config/client.toml"` | 配置文件挂载路径 |
| client.mounts.config.subPath | string | `"client.toml"` | 配置文件在secret资源中的key名称 |
| client.mounts.data.mountPath | string | `"/app/data/"` | 硬盘挂载目录 |
| client.name | string | `"signatrust-client"` | client名称 |
| client.pvc.accessModes[0] | string | `"ReadWriteOnce"` | 硬盘挂载策略,单节点挂载 |
| client.pvc.name | string | `"signatrust-client-volume"` | pvc资源名 |
| client.pvc.size | string | `"10Gi"` | 硬盘容量 |
| client.pvc.storageClassName | string | `"csi-disk"` | 存储卷类型 |
| client.replicas | int | `1` | 副本数 |
| client.resources.limits.cpu | string | `"1000m"` | 容器资源配置 |
| client.resources.limits.memory | string | `"2000Mi"` | 容器资源配置 |
| client.resources.requests.cpu | string | `"1000m"` | 容器资源配置 |
| client.resources.requests.memory | string | `"2000Mi"` | 容器资源配置 |
| client.securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| client.securityContext.runAsGroup | int | `1000` | 安全策略，容器运行用户组uid |
| client.securityContext.runAsUser | int | `1000` | 安全策略，容器运行用户uid |
| client.strategy.type | string | `"Recreate"` | 副本更新策略 |
| client.volumes.configMapName | string | `"signatrust-client-configmap"` | client configmap资源名 |
| client.volumes.pvcName | string | `"signatrust-client-volume"` | client pvc资源名 |
| client.volumes.secretName | string | `"signatrust-secrets"` | client secret资源名 |
| controlAdmin.command[0] | string | `"sleep"` | 启动命令 |
| controlAdmin.command[1] | string | `"1000000"` | 启动命令  |
| controlAdmin.commonAnnotations | object | `{}` | control admin pod声明字段 |
| controlAdmin.deployment.autoscaler | string | `"true"` | 是否对接弹性伸缩副本服务 |
| controlAdmin.enabled | bool | `true` | 启用control admin |
| controlAdmin.env.name | string | `"RUST_LOG"` | 环境变量 |
| controlAdmin.env.value | string | `"debug"` | 环境变量值 |
| controlAdmin.image.pullPolicy | string | `"Always"` | 镜像拉取策略 |
| controlAdmin.image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| controlAdmin.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/signatrust-control-admin"` | 镜像名 |
| controlAdmin.image.tag | string | `"62bcd11fb8cd8dc813108a9e35106de94ae5d224"` | 镜像tag |
| controlAdmin.mounts.controlServer.mountPath | string | `"/app/config/server.toml"` | 配置文件挂载路径 |
| controlAdmin.mounts.controlServer.subPath | string | `"control-server-toml"` | 引用secret中的key |
| controlAdmin.mounts.key.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.key"` | 配置文件挂载路径 |
| controlAdmin.mounts.key.subPath | string | `"server-key"` | 引用secret中的key |
| controlAdmin.mounts.rootcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/ca_root.pem"` | 配置文件挂载路径 |
| controlAdmin.mounts.rootcrt.subPath | string | `"ca-root-pem"` | 引用secret中的key |
| controlAdmin.mounts.srvcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.crt"` | 配置文件挂载路径 |
| controlAdmin.mounts.srvcrt.subPath | string | `"server-crt"` | 引用secret中的key |
| controlAdmin.name | string | `"signatrust-control-admin"` | control admin 服务名 |
| controlAdmin.ports.containerPort | int | `8080` | 容器端口号 |
| controlAdmin.ports.name | string | `"http"` | 容器端口名 |
| controlAdmin.ports.protocol | string | `"TCP"` | 端口对应的协议 |
| controlAdmin.replicas | int | `1` | 副本数 |
| controlAdmin.resources.limits.cpu | string | `"1000m"` | 容器资源配置 |
| controlAdmin.resources.limits.memory | string | `"1000Mi"` | 容器资源配置 |
| controlAdmin.resources.requests.cpu | string | `"1000m"` | 容器资源配置 |
| controlAdmin.resources.requests.memory | string | `"1000Mi"` | 容器资源配置 |
| controlAdmin.securityContext.allowPrivilegeEscalation | bool | `false` | 安全策略，不允许提权 |
| controlAdmin.securityContext.runAsGroup | int | `1000` | 安全策略，容器运行用户组uid |
| controlAdmin.securityContext.runAsUser | int | `1000` | 安全策略，容器运行用户uid |
| controlAdmin.service.name | string | `"http-port"` | service端口名 |
| controlAdmin.service.port | int | `8080` | service端口号 |
| controlAdmin.service.protocol | string | `"TCP"` | 端口对应的协议 |
| controlAdmin.service.targetPort | int | `8080` | 容器端口号 |
| controlAdmin.service.type | string | `"ClusterIP"` | 服务对外暴露范围，仅集群内可访问 |
| controlAdmin.strategy.rollingUpdate.maxSurge | int | `1` | 滚动升级过程最大增加副本数 |
| controlAdmin.strategy.rollingUpdate.maxUnavailable | int | `0` | 滚动升级过程允许减少副本数 |
| controlAdmin.strategy.type | string | `"RollingUpdate"` | 升级类型 |
| controlAdmin.volumes.secretName | string | `"signatrust-secrets"` | secret资源名 |
| controlServer.container.command[0] | string | `"/app/control-server"` |  |
| controlServer.container.ports[0].containerPort | int | `8080` |  |
| controlServer.container.ports[0].name | string | `"http"` |  |
| controlServer.container.ports[0].protocol | string | `"TCP"` |  |
| controlServer.deployment.autoscaler | string | `"true"` |  |
| controlServer.enabled | bool | `true` |  |
| controlServer.env[0].name | string | `"RUST_LOG"` |  |
| controlServer.env[0].value | string | `"debug"` |  |
| controlServer.image.pullPolicy | string | `"Always"` |  |
| controlServer.image.pullSecret | string | `"huawei-swr-image-pull-secret"` |  |
| controlServer.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/signatrust-control-server"` |  |
| controlServer.image.tag | string | `"62bcd11fb8cd8dc813108a9e35106de94ae5d224"` |  |
| controlServer.initContainers[0].command[0] | string | `"sh"` |  |
| controlServer.initContainers[0].command[1] | string | `"-c"` |  |
| controlServer.initContainers[0].command[2] | string | `"until nslookup 192.168.1.193; do echo \"waiting for mysql service\"; sleep 2; done;"` |  |
| controlServer.initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/busybox:1.28"` |  |
| controlServer.initContainers[0].name | string | `"init-mysql"` |  |
| controlServer.initContainers[1].command[0] | string | `"/bin/sh"` |  |
| controlServer.initContainers[1].command[1] | string | `"-c"` |  |
| controlServer.initContainers[1].command[2] | string | `"git clone https://gitee.com/openeuler/signatrust\ncd signatrust\ngit checkout $CONTROL_SERVER_TAG\nsqlx database create\nsqlx migrate run\n"` |  |
| controlServer.initContainers[1].env[0].name | string | `"DATABASE_URL"` |  |
| controlServer.initContainers[1].env[0].valueFrom.secretKeyRef.key | string | `"DATABASE_URL"` |  |
| controlServer.initContainers[1].env[0].valueFrom.secretKeyRef.name | string | `"signatrust-secrets"` |  |
| controlServer.initContainers[1].env[1].name | string | `"CONTROL_SERVER_TAG"` |  |
| controlServer.initContainers[1].env[1].value | string | `"722fefdf307fa73c683795f9531cf2ef99448914"` |  |
| controlServer.initContainers[1].image | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/rust-sqlx:latest"` |  |
| controlServer.initContainers[1].name | string | `"prepare-table"` |  |
| controlServer.mounts.controlServer.mountPath | string | `"/app/config/server.toml"` |  |
| controlServer.mounts.controlServer.subPath | string | `"control-server-toml"` |  |
| controlServer.mounts.key.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.key"` |  |
| controlServer.mounts.key.subPath | string | `"server-key"` |  |
| controlServer.mounts.rootcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/ca_root.pem"` |  |
| controlServer.mounts.rootcrt.subPath | string | `"ca-root-pem"` |  |
| controlServer.mounts.srvcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.crt"` |  |
| controlServer.mounts.srvcrt.subPath | string | `"server-crt"` |  |
| controlServer.name | string | `"signatrust-control-server"` |  |
| controlServer.probes.liveness.failureThreshold | int | `3` |  |
| controlServer.probes.liveness.initialDelaySeconds | int | `5` |  |
| controlServer.probes.liveness.path | string | `"/api/health/"` |  |
| controlServer.probes.liveness.periodSeconds | int | `5` |  |
| controlServer.probes.liveness.port | int | `8080` |  |
| controlServer.probes.readiness.failureThreshold | int | `3` |  |
| controlServer.probes.readiness.initialDelaySeconds | int | `10` |  |
| controlServer.probes.readiness.path | string | `"/api/health/"` |  |
| controlServer.probes.readiness.periodSeconds | int | `5` |  |
| controlServer.probes.readiness.port | int | `8080` |  |
| controlServer.replicas | int | `1` |  |
| controlServer.resources.limits.cpu | string | `"1000m"` |  |
| controlServer.resources.limits.memory | string | `"1000Mi"` |  |
| controlServer.resources.requests.cpu | string | `"1000m"` |  |
| controlServer.resources.requests.memory | string | `"1000Mi"` |  |
| controlServer.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| controlServer.securityContext.runAsGroup | int | `1000` |  |
| controlServer.securityContext.runAsUser | int | `1000` |  |
| controlServer.service.name | string | `"http-port"` |  |
| controlServer.service.port | int | `8080` |  |
| controlServer.service.protocol | string | `"TCP"` |  |
| controlServer.service.targetPort | int | `8080` |  |
| controlServer.service.type | string | `"ClusterIP"` |  |
| controlServer.strategy.rollingUpdate.maxSurge | int | `1` |  |
| controlServer.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| controlServer.strategy.type | string | `"RollingUpdate"` |  |
| controlServer.volumes.secretName | string | `"signatrust-secrets"` |  |
| dataServer.LoadBalancer.annotations."kubernetes.io/elb.class" | string | `"union"` |  |
| dataServer.LoadBalancer.annotations."kubernetes.io/elb.id" | string | `"c59904ee-c772-4bcb-8a12-770fd080c79b"` |  |
| dataServer.LoadBalancer.annotations."kubernetes.io/elb.lb-algorithm" | string | `"ROUND_ROBIN"` |  |
| dataServer.LoadBalancer.enabled | bool | `true` |  |
| dataServer.LoadBalancer.ports[0].name | string | `"tcp-1"` |  |
| dataServer.LoadBalancer.ports[0].port | int | `8089` |  |
| dataServer.LoadBalancer.ports[0].protocol | string | `"TCP"` |  |
| dataServer.LoadBalancer.ports[0].targetPort | int | `8088` |  |
| dataServer.LoadBalancer.type | string | `"LoadBalancer"` |  |
| dataServer.container.command[0] | string | `"/app/data-server"` |  |
| dataServer.container.name | string | `"data-server"` |  |
| dataServer.container.ports[0].containerPort | int | `8088` |  |
| dataServer.container.ports[0].name | string | `"http"` |  |
| dataServer.container.ports[0].protocol | string | `"TCP"` |  |
| dataServer.enabled | bool | `true` |  |
| dataServer.env[0].name | string | `"RUST_LOG"` |  |
| dataServer.env[0].value | string | `"debug"` |  |
| dataServer.image.pullPolicy | string | `"Always"` |  |
| dataServer.image.pullSecret | string | `"huawei-swr-image-pull-secret"` |  |
| dataServer.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/signatrust-data-server"` |  |
| dataServer.image.tag | string | `"62bcd11fb8cd8dc813108a9e35106de94ae5d224"` |  |
| dataServer.initContainers[0].command[0] | string | `"sh"` |  |
| dataServer.initContainers[0].command[1] | string | `"-c"` |  |
| dataServer.initContainers[0].command[2] | string | `"until nslookup 192.168.1.193; do echo \"waiting for mysql service\"; sleep 2; done;"` |  |
| dataServer.initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/openubmc/signatrust/busybox:1.28"` |  |
| dataServer.initContainers[0].name | string | `"init-mysql"` |  |
| dataServer.mounts.controlServer.mountPath | string | `"/app/config/server.toml"` |  |
| dataServer.mounts.controlServer.subPath | string | `"control-server-toml"` |  |
| dataServer.mounts.key.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.key"` |  |
| dataServer.mounts.key.subPath | string | `"server-key"` |  |
| dataServer.mounts.rootcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/ca_root.pem"` |  |
| dataServer.mounts.rootcrt.subPath | string | `"ca-root-pem"` |  |
| dataServer.mounts.srvcrt.mountPath | string | `"/Users/tommylike/Work/codes/rust-projects/signatrust/.data/certs/server/server.crt"` |  |
| dataServer.mounts.srvcrt.subPath | string | `"server-crt"` |  |
| dataServer.name | string | `"signatrust-data-server"` |  |
| dataServer.nodeSelector.autoscaler | string | `"true"` |  |
| dataServer.replicas | int | `1` |  |
| dataServer.resources.limits.cpu | string | `"8000m"` |  |
| dataServer.resources.limits.memory | string | `"8000Mi"` |  |
| dataServer.resources.requests.cpu | string | `"1000m"` |  |
| dataServer.resources.requests.memory | string | `"1000Mi"` |  |
| dataServer.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| dataServer.securityContext.runAsGroup | int | `1000` |  |
| dataServer.securityContext.runAsUser | int | `1000` |  |
| dataServer.service.ports[0].name | string | `"tcp-1"` |  |
| dataServer.service.ports[0].port | int | `8088` |  |
| dataServer.service.ports[0].protocol | string | `"TCP"` |  |
| dataServer.service.ports[0].targetPort | int | `8088` |  |
| dataServer.service.type | string | `"ClusterIP"` |  |
| dataServer.strategy.rollingUpdate.maxSurge | int | `1` |  |
| dataServer.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| dataServer.strategy.type | string | `"RollingUpdate"` |  |
| dataServer.volumes.secretName | string | `"signatrust-secrets"` |  |
| database.database.clusterIP | string | `"None"` |  |
| database.database.component | string | `"signatrust-database"` |  |
| database.database.name | string | `"signatrust-database"` |  |
| database.database.port.name | string | `"database"` |  |
| database.database.port.port | int | `3306` |  |
| database.database.port.targetPort | int | `3306` |  |
| database.database.type | string | `"ClusterIP"` |  |
| database.enabled | bool | `false` |  |
| database.env[0].key | string | `"MYSQL_DATABASE"` |  |
| database.env[0].name | string | `"MYSQL_DATABASE"` |  |
| database.env[1].key | string | `"MYSQL_PASSWORD"` |  |
| database.env[1].name | string | `"MYSQL_PASSWORD"` |  |
| database.env[2].key | string | `"MYSQL_USER"` |  |
| database.env[2].name | string | `"MYSQL_USER"` |  |
| database.env[3].key | string | `"MYSQL_ROOT_PASSWORD"` |  |
| database.env[3].name | string | `"MYSQL_ROOT_PASSWORD"` |  |
| database.host | string | `"192.168.1.193"` |  |
| database.image.pullPolicy | string | `"Always"` |  |
| database.image.pullSecret | string | `"huawei-swr-image-pull-secret"` |  |
| database.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/signatrust/mysql"` |  |
| database.image.tag | string | `"8.0"` |  |
| database.mounts.mysql.mountPath | string | `"/var/lib/mysql"` |  |
| database.name | string | `"signatrust-database"` |  |
| database.probes.liveness.initialDelaySeconds | int | `10` |  |
| database.probes.liveness.periodSeconds | int | `10` |  |
| database.probes.liveness.port | int | `3306` |  |
| database.probes.readiness.failureThreshold | int | `3` |  |
| database.probes.readiness.initialDelaySeconds | int | `20` |  |
| database.probes.readiness.periodSeconds | int | `5` |  |
| database.probes.readiness.port | int | `3306` |  |
| database.probes.readiness.timeoutSeconds | int | `10` |  |
| database.pvc.accessModes[0] | string | `"ReadWriteOnce"` |  |
| database.pvc.mountPath | string | `"/var/lib/mysql"` |  |
| database.pvc.name | string | `"database-volume"` |  |
| database.pvc.size | string | `"10Gi"` |  |
| database.pvc.storageClassName | string | `"csi-disk"` |  |
| database.redis.component | string | `"signatrust-redis"` |  |
| database.redis.name | string | `"redis"` |  |
| database.redis.port.name | string | `"http"` |  |
| database.redis.port.port | int | `6379` |  |
| database.redis.port.protocol | string | `"TCP"` |  |
| database.redis.port.targetPort | int | `6379` |  |
| database.redis.type | string | `"ClusterIP"` |  |
| database.resources.limits.cpu | string | `"1000m"` |  |
| database.resources.limits.memory | string | `"1000Mi"` |  |
| database.resources.requests.cpu | string | `"1000m"` |  |
| database.resources.requests.memory | string | `"1000Mi"` |  |
| database.service.name | string | `"db"` |  |
| database.service.port | int | `3306` |  |
| database.service.protocol | string | `"TCP"` |  |
| database.strategy.type | string | `"Recreate"` |  |
| database.volumes.secretName | string | `"signatrust-secrets"` |  |
| global.autoscaler.enabled | bool | `false` |  |
| global.commonAnnotations | object | `{}` |  |
| global.namespace | string | `"signatrust"` |  |
| global.tolerations[0].effect | string | `"NoSchedule"` |  |
| global.tolerations[0].key | string | `"autoscale"` |  |
| global.tolerations[0].operator | string | `"Exists"` |  |
| ingress.annotations | object | `{}` |  |
| ingress.backend.serviceName | string | `"signatrust-control-server-service"` |  |
| ingress.backend.servicePort | int | `8080` |  |
| ingress.className | string | `"nginx"` |  |
| ingress.enabled | bool | `true` |  |
| ingress.host | string | `"signatrust.openubmc.cn"` |  |
| ingress.hosts | list | `[]` |  |
| ingress.path | string | `"/api"` |  |
| ingress.pathtype | string | `"Prefix"` |  |
| ingress.secretName | string | `"signatrust-tls"` |  |
| ingress.tls | list | `[]` |  |
| secret.data | object | `{}` |  |
| secret.name | string | `"signatrust-secrets"` |  |
| secret.secretdefine.DATABASE_URL.key | string | `"DATABASE_URL"` |  |
| secret.secretdefine.DATABASE_URL.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.MYSQL_DATABASE.key | string | `"MYSQL_DATABASE"` |  |
| secret.secretdefine.MYSQL_DATABASE.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.MYSQL_PASSWORD.key | string | `"MYSQL_PASSWORD"` |  |
| secret.secretdefine.MYSQL_PASSWORD.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.MYSQL_ROOT_PASSWORD.key | string | `"MYSQL_ROOT_PASSWORD"` |  |
| secret.secretdefine.MYSQL_ROOT_PASSWORD.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.MYSQL_USER.key | string | `"MYSQL_USER"` |  |
| secret.secretdefine.MYSQL_USER.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.ca-crt.key | string | `"tls.cert"` |  |
| secret.secretdefine.ca-crt.path | string | `"secrets/data/openubmc/openubmc-cn-tls"` |  |
| secret.secretdefine.ca-key.key | string | `"tls.key"` |  |
| secret.secretdefine.ca-key.path | string | `"secrets/data/openubmc/openubmc-cn-tls"` |  |
| secret.secretdefine.ca-root-pem.key | string | `"ca-root-pem"` |  |
| secret.secretdefine.ca-root-pem.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.control-server-toml.key | string | `"control-server-toml"` |  |
| secret.secretdefine.control-server-toml.path | string | `"secrets/data/openubmc/signatrust-prod"` |  |
| secret.secretdefine.server-crt.key | string | `"tls.cert"` |  |
| secret.secretdefine.server-crt.path | string | `"secrets/data/openubmc/openubmc-cn-tls"` |  |
| secret.secretdefine.server-key.key | string | `"tls.key"` |  |
| secret.secretdefine.server-key.path | string | `"secrets/data/openubmc/openubmc-cn-tls"` |  |
| secret.type | string | `"Opaque"` |  |

## 变更历史

## 1.0.0 - 2025-10-28

### 说明
- 初始版本发布

## 4.0.2 - 2025-12-11

### 说明
- control server 增加健康检查协议适配