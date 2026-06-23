# mail

![Version: 1.0.13](https://img.shields.io/badge/Version-1.0.13-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for maillist

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
| affinity | object | `{}` | 亲和策略 |
| cronjob.concurrencyPolicy | string | `"Forbid"` | 并发策略 |
| cronjob.enabled | bool | `true` | 是否渲染cronjob资源 |
| cronjob.env.secretRef.keys[0].key | string | `"mailman-api-url"` | 对应在secret中的键名 |
| cronjob.env.secretRef.keys[0].name | string | `"mailman_url"` | 环境变量名 |
| cronjob.env.secretRef.keys[1].key | string | `"mailman_core_user"` |  |
| cronjob.env.secretRef.keys[1].name | string | `"mailman_username"` |  |
| cronjob.env.secretRef.keys[2].key | string | `"mailman_core_password"` |  |
| cronjob.env.secretRef.keys[2].name | string | `"mailman_password"` |  |
| cronjob.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/app-mailman/clean-pending-subscription"` | 镜像名 |
| cronjob.image.tag | string | `"4a229e7f654a4ba58ca0df6c84d81ed0e011ab701702451209"` | 镜像Tag |
| cronjob.name | string | `"scan-subscribe-pending-cronjob"` | cronjob名称 |
| cronjob.resources.limits.cpu | string | `"1000m"` | 容器运行限制CPU资源 |
| cronjob.resources.limits.memory | string | `"1000Mi"` | 容器运行限制内存资源 |
| cronjob.resources.requests.cpu | string | `"500m"` | 容器运行最少所需CPU资源 |
| cronjob.resources.requests.memory | string | `"500Mi"` | 容器运行最少所需内存资源 |
| cronjob.restartPolicy | string | `"OnFailure"` | 重启策略 |
| cronjob.schedule | string | `"0 0 * * *"` | 触发周期设置 |
| exim4.configmapName | string | `"exim-configmap"` | configmap名称 |
| exim4.image.imagePullPolicy | string | `"IfNotPresent"` | 镜像拉取策略 |
| exim4.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/app-mailman/mailman-exim-new-build"` | 镜像名 |
| exim4.image.tag | string | `"4af76116d521a0d926744d654dce452236aca28f1761045074"` | 镜像Tag |
| exim4.name | string | `"mailman-exim4"` | 服务名称 |
| exim4.nodeSelector | object | `{}` | 节点选择标签 |
| exim4.podLabels.app | string | `"mail-suit-service"` | pod标签 |
| exim4.podLabels.component | string | `"mail-exim4-service"` | pod标签 |
| exim4.pvc.accessMode | string | `"ReadWriteOnce"` | pvc访问模式 |
| exim4.pvc.name | string | `"exim-log-data"` | pvc名称 |
| exim4.pvc.storage | string | `"100Gi"` | 磁盘容量 |
| exim4.pvc.storageClass | string | `"csi-disk"` | 存储类型 |
| exim4.replicas | int | `1` | pod副本数 |
| exim4.resources.limits.cpu | string | `"4"` |  |
| exim4.resources.limits.memory | string | `"4Gi"` |  |
| exim4.resources.requests.cpu | string | `"4"` |  |
| exim4.resources.requests.memory | string | `"4Gi"` |  |
| exim4.service.elbClass | string | `"union"` | ELB类型 |
| exim4.service.elbId | string | `"9d356ff2-070e-445a-bcc1-c468b51e0213"` | ELB资源ID |
| exim4.service.name | string | `"mailman-exim4-service"` | service名称 |
| exim4.service.ports[0].name | string | `"exim4-port"` | 端口名称 |
| exim4.service.ports[0].port | int | `25` | service对外端口 |
| exim4.service.ports[0].protocol | string | `"TCP"` | 转发协议 |
| exim4.service.ports[0].targetPort | int | `25` | 服务暴露端口 |
| exim4.service.ports[1].name | string | `"exim4-port-2"` |  |
| exim4.service.ports[1].port | int | `465` |  |
| exim4.service.ports[1].protocol | string | `"TCP"` |  |
| exim4.service.ports[1].targetPort | int | `465` |  |
| exim4.service.type | string | `"LoadBalancer"` | service类型 |
| exim4.volumeMounts[0].mountPath | string | `"/opt/mailman/"` | 挂载在容器中的路径 |
| exim4.volumeMounts[0].name | string | `"mailman-core-data"` | 卷名 |
| exim4.volumeMounts[1].mountPath | string | `"/var/log/exim/"` |  |
| exim4.volumeMounts[1].name | string | `"mailman-exim4-log"` |  |
| exim4.volumeMounts[2].mountPath | string | `"/etc/exim/passwd"` |  |
| exim4.volumeMounts[2].name | string | `"mailman-secrets"` |  |
| exim4.volumeMounts[2].subPath | string | `"exim4_credential"` | 文件名 |
| exim4.volumeMounts[3].mountPath | string | `"/etc/exim/dkim/openeuler.key"` |  |
| exim4.volumeMounts[3].name | string | `"mta-dkim-secret"` |  |
| exim4.volumeMounts[3].subPath | string | `"dkim_key"` |  |
| exim4.volumeMounts[4].mountPath | string | `"/etc/exim/ssl_pool/openeuler.org.crt"` |  |
| exim4.volumeMounts[4].name | string | `"exim4-tls-secret"` |  |
| exim4.volumeMounts[4].subPath | string | `"openeuler_org_crt"` |  |
| exim4.volumeMounts[5].mountPath | string | `"/etc/exim/ssl_pool/openeuler.org.key"` |  |
| exim4.volumeMounts[5].name | string | `"exim4-tls-secret"` |  |
| exim4.volumeMounts[5].subPath | string | `"openeuler_org_key"` |  |
| exim4.volumeMounts[6].mountPath | string | `"/etc/exim/exim.conf"` |  |
| exim4.volumeMounts[6].name | string | `"exim-config"` |  |
| exim4.volumeMounts[6].subPath | string | `"exim_conf"` |  |
| exim4.volumes[0].name | string | `"mailman-core-data"` | 卷名 |
| exim4.volumes[0].persistentVolumeClaim.claimName | string | `"config-vol"` | pvc名称 |
| exim4.volumes[1].name | string | `"mailman-exim4-log"` |  |
| exim4.volumes[1].persistentVolumeClaim.claimName | string | `"exim-log-data"` |  |
| exim4.volumes[2].name | string | `"mta-dkim-secret"` |  |
| exim4.volumes[2].secret.secretName | string | `"mailman-secrets"` | secret名称 |
| exim4.volumes[3].name | string | `"mailman-secrets"` |  |
| exim4.volumes[3].secret.secretName | string | `"mailman-secrets"` |  |
| exim4.volumes[4].name | string | `"exim4-tls-secret"` |  |
| exim4.volumes[4].secret.secretName | string | `"mailman-cert-secrets"` |  |
| exim4.volumes[5].configMap.name | string | `"exim-configmap"` | configmap名称 |
| exim4.volumes[5].name | string | `"exim-config"` |  |
| host | string | `"mailweb.openeuler.org"` | 域名 |
| ingress.enabled | bool | `true` | 是否启用ingress |
| ingress.name | string | `"mailweb-ingress"` | ingress名称 |
| ingress.secretName | string | `"mailweb-tls"` | tls secret名称 |
| istio.enabled | bool | `false` | 是否启用istio |
| istio.exim4Annotation | object | `{}` | 自定义声明项 |
| istio.gateway | string | `"istio-system/istio-gateway-https"` | gateway名称 |
| istio.http | object | `{}` | 路径转发配置 |
| istio.mailcoreAnnotation | object | `{}` | 自定义声明项 |
| istio.mtlsMode | string | `"DISABLE"` | mtls模式开关 |
| istio.nslabel | object | `{}` | 启用istio时命名空间所需标签 |
| istio.tls.mode | string | `"SIMPLE"` | tls模式开关 |
| mailcore.env.secretRef.keys[0].key | string | `"database_type"` |  |
| mailcore.env.secretRef.keys[0].name | string | `"DATABASE_TYPE"` |  |
| mailcore.env.secretRef.keys[10].key | string | `"mailcore_mta"` |  |
| mailcore.env.secretRef.keys[10].name | string | `"MTA"` |  |
| mailcore.env.secretRef.keys[11].key | string | `"mailcore_smtp_port"` |  |
| mailcore.env.secretRef.keys[11].name | string | `"SMTP_PORT"` |  |
| mailcore.env.secretRef.keys[1].key | string | `"database_class"` |  |
| mailcore.env.secretRef.keys[1].name | string | `"DATABASE_CLASS"` |  |
| mailcore.env.secretRef.keys[2].key | string | `"mailman_core_user"` |  |
| mailcore.env.secretRef.keys[2].name | string | `"MAILMAN_REST_USER"` |  |
| mailcore.env.secretRef.keys[3].key | string | `"mailman_core_password"` |  |
| mailcore.env.secretRef.keys[3].name | string | `"MAILMAN_REST_PASSWORD"` |  |
| mailcore.env.secretRef.keys[4].key | string | `"hyperkitty_api_key"` |  |
| mailcore.env.secretRef.keys[4].name | string | `"HYPERKITTY_API_KEY"` |  |
| mailcore.env.secretRef.keys[5].key | string | `"exim4_credential_username"` |  |
| mailcore.env.secretRef.keys[5].name | string | `"EMAIL_HOST_USER"` |  |
| mailcore.env.secretRef.keys[6].key | string | `"exim4_credential_password"` |  |
| mailcore.env.secretRef.keys[6].name | string | `"EMAIL_HOST_PASSWORD"` |  |
| mailcore.env.secretRef.keys[7].key | string | `"mailcore_mm_hostname"` |  |
| mailcore.env.secretRef.keys[7].name | string | `"MM_HOSTNAME"` |  |
| mailcore.env.secretRef.keys[8].key | string | `"mailcore_rest_port"` |  |
| mailcore.env.secretRef.keys[8].name | string | `"MAILMAN_REST_PORT"` |  |
| mailcore.env.secretRef.keys[9].key | string | `"mailcore_database_url"` |  |
| mailcore.env.secretRef.keys[9].name | string | `"DATABASE_URL"` |  |
| mailcore.env.secretRef.name | string | `"mailman-secrets"` | secret名称 |
| mailcore.image.imagePullPolicy | string | `"IfNotPresent"` |  |
| mailcore.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/app-mailman/mailman-core-new-build"` |  |
| mailcore.image.tag | string | `"0d995da03cd978a16d0730caa6d36846313bceb91740095397"` |  |
| mailcore.name | string | `"mailman-core"` |  |
| mailcore.nodeSelector | object | `{}` |  |
| mailcore.podLabels.app | string | `"mail-suit-service"` |  |
| mailcore.podLabels.component | string | `"mail-core-service"` |  |
| mailcore.pvc.accessMode | string | `"ReadWriteMany"` |  |
| mailcore.pvc.name | string | `"config-vol"` |  |
| mailcore.pvc.storage | string | `"500Gi"` |  |
| mailcore.pvc.storageClass | string | `"csi-sfsturbo"` |  |
| mailcore.replicas | int | `1` |  |
| mailcore.resources.limits.cpu | string | `"4"` |  |
| mailcore.resources.limits.memory | string | `"4Gi"` |  |
| mailcore.resources.requests.cpu | string | `"4"` |  |
| mailcore.resources.requests.memory | string | `"4Gi"` |  |
| mailcore.service.name | string | `"mailman-core-service"` |  |
| mailcore.service.ports[0].name | string | `"core-service"` |  |
| mailcore.service.ports[0].port | int | `8001` |  |
| mailcore.service.ports[0].protocol | string | `"TCP"` |  |
| mailcore.service.ports[0].targetPort | int | `8001` |  |
| mailcore.service.ports[1].name | string | `"core-service-2"` |  |
| mailcore.service.ports[1].port | int | `8024` |  |
| mailcore.service.ports[1].protocol | string | `"TCP"` |  |
| mailcore.service.ports[1].targetPort | int | `8024` |  |
| mailcore.service.type | string | `"ClusterIP"` |  |
| mailweb.env.plainValues[0].name | string | `"PRIVACY_LINK"` | 环境变量名 |
| mailweb.env.plainValues[0].value | string | `"https://www.openeuler.org/en/other/privacy/"` | 环境变量值 |
| mailweb.env.plainValues[1].name | string | `"CONDUCT_LINK"` |  |
| mailweb.env.plainValues[1].value | string | `"https://www.openeuler.org/en/community/conduct/"` |  |
| mailweb.env.plainValues[2].name | string | `"MAILMAN_ADMIN_USER"` |  |
| mailweb.env.plainValues[2].value | string | `"openeuler"` |  |
| mailweb.env.secretRef.keys[0].key | string | `"database_type"` |  |
| mailweb.env.secretRef.keys[0].name | string | `"DATABASE_TYPE"` |  |
| mailweb.env.secretRef.keys[10].key | string | `"mailweb_smtp_host"` |  |
| mailweb.env.secretRef.keys[10].name | string | `"SMTP_HOST"` |  |
| mailweb.env.secretRef.keys[11].key | string | `"mailweb_smtp_port"` |  |
| mailweb.env.secretRef.keys[11].name | string | `"SMTP_PORT"` |  |
| mailweb.env.secretRef.keys[12].key | string | `"mailweb_django_allowed_hosts"` |  |
| mailweb.env.secretRef.keys[12].name | string | `"DJANGO_ALLOWED_HOSTS"` |  |
| mailweb.env.secretRef.keys[13].key | string | `"mailweb_postorius_template_base_url"` |  |
| mailweb.env.secretRef.keys[13].name | string | `"POSTORIUS_TEMPLATE_BASE_URL"` |  |
| mailweb.env.secretRef.keys[14].key | string | `"mailweb_database_url"` |  |
| mailweb.env.secretRef.keys[14].name | string | `"DATABASE_URL"` |  |
| mailweb.env.secretRef.keys[15].key | string | `"mailweb_redis_ip"` |  |
| mailweb.env.secretRef.keys[15].name | string | `"redis_ip"` |  |
| mailweb.env.secretRef.keys[16].key | string | `"mailweb_redis_port"` |  |
| mailweb.env.secretRef.keys[16].name | string | `"redis_port"` |  |
| mailweb.env.secretRef.keys[17].key | string | `"mailweb_redis_password"` |  |
| mailweb.env.secretRef.keys[17].name | string | `"redis_password"` |  |
| mailweb.env.secretRef.keys[18].key | string | `"DATA_STORAGE_LOCATION"` |  |
| mailweb.env.secretRef.keys[18].name | string | `"DATA_STORAGE_LOCATION"` |  |
| mailweb.env.secretRef.keys[19].key | string | `"DATA_STORAGE_COMMUNITY"` |  |
| mailweb.env.secretRef.keys[19].name | string | `"DATA_STORAGE_COMMUNITY"` |  |
| mailweb.env.secretRef.keys[1].key | string | `"hyperkitty_api_key"` |  |
| mailweb.env.secretRef.keys[1].name | string | `"HYPERKITTY_API_KEY"` |  |
| mailweb.env.secretRef.keys[2].key | string | `"secret_key"` |  |
| mailweb.env.secretRef.keys[2].name | string | `"SECRET_KEY"` |  |
| mailweb.env.secretRef.keys[3].key | string | `"mailman_core_user"` |  |
| mailweb.env.secretRef.keys[3].name | string | `"MAILMAN_REST_USER"` |  |
| mailweb.env.secretRef.keys[4].key | string | `"mailman_core_password"` |  |
| mailweb.env.secretRef.keys[4].name | string | `"MAILMAN_REST_PASSWORD"` |  |
| mailweb.env.secretRef.keys[5].key | string | `"mailman_admin_email"` |  |
| mailweb.env.secretRef.keys[5].name | string | `"MAILMAN_ADMIN_EMAIL"` |  |
| mailweb.env.secretRef.keys[6].key | string | `"exim4_credential_username"` |  |
| mailweb.env.secretRef.keys[6].name | string | `"SMTP_HOST_USER"` |  |
| mailweb.env.secretRef.keys[7].key | string | `"exim4_credential_password"` |  |
| mailweb.env.secretRef.keys[7].name | string | `"SMTP_HOST_PASSWORD"` |  |
| mailweb.env.secretRef.keys[8].key | string | `"mailweb_server_from_domain"` |  |
| mailweb.env.secretRef.keys[8].name | string | `"SERVE_FROM_DOMAIN"` |  |
| mailweb.env.secretRef.keys[9].key | string | `"mailweb_server_web_domain"` |  |
| mailweb.env.secretRef.keys[9].name | string | `"SERVE_WEB_DOMAIN"` |  |
| mailweb.env.secretRef.name | string | `"mailman-secrets"` |  |
| mailweb.image.imagePullPolicy | string | `"Always"` |  |
| mailweb.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/app-mailman/mailman-web-new-build"` |  |
| mailweb.image.tag | string | `"b70fe4b2feb2d335fb591c975c54348d6a6f0d911740470898"` |  |
| mailweb.name | string | `"mailman-web"` |  |
| mailweb.nodeSelector | object | `{}` |  |
| mailweb.podLabels.app | string | `"mail-suit-service"` |  |
| mailweb.podLabels.component | string | `"mail-web-service"` |  |
| mailweb.replicas | int | `2` |  |
| mailweb.resources.limits.cpu | string | `"4"` |  |
| mailweb.resources.limits.memory | string | `"12000Mi"` |  |
| mailweb.resources.requests.cpu | string | `"1"` |  |
| mailweb.resources.requests.memory | string | `"2000Mi"` |  |
| mailweb.service.name | string | `"mailman-web-service"` |  |
| mailweb.service.portNumber | int | `80` |  |
| mailweb.service.ports[0].name | string | `"website-port-uwsgi-http"` |  |
| mailweb.service.ports[0].port | int | `8000` |  |
| mailweb.service.ports[0].protocol | string | `"TCP"` |  |
| mailweb.service.ports[0].targetPort | int | `8000` |  |
| mailweb.service.ports[1].name | string | `"website-port-http"` |  |
| mailweb.service.ports[1].port | int | `80` |  |
| mailweb.service.ports[1].protocol | string | `"TCP"` |  |
| mailweb.service.ports[1].targetPort | int | `80` |  |
| mailweb.service.type | string | `"ClusterIP"` |  |
| mailweb.strategy.rollingUpdate.maxSurge | int | `1` |  |
| mailweb.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| mailweb.strategy.type | string | `"RollingUpdate"` |  |
| mailwebSecrets.keysMap.DATA_STORAGE_COMMUNITY | string | `"DATA_STORAGE_COMMUNITY"` | 对应在vault中的键名 |
| mailwebSecrets.keysMap.DATA_STORAGE_LOCATION | string | `"DATA_STORAGE_LOCATION"` |  |
| mailwebSecrets.keysMap.database_class | string | `"database_class"` |  |
| mailwebSecrets.keysMap.database_type | string | `"database_type"` |  |
| mailwebSecrets.keysMap.dkim_key | string | `"dkim_key"` |  |
| mailwebSecrets.keysMap.exim4_credential | string | `"exim4_credential"` |  |
| mailwebSecrets.keysMap.exim4_credential_password | string | `"exim4_credential_splitted_password"` |  |
| mailwebSecrets.keysMap.exim4_credential_username | string | `"exim4_credential_splitted_username"` |  |
| mailwebSecrets.keysMap.hyperkitty_api_key | string | `"hyperkitty_api_key"` |  |
| mailwebSecrets.keysMap.mailcore_database_url | string | `"mailweb_database_url"` |  |
| mailwebSecrets.keysMap.mailcore_mm_hostname | string | `"mailcore_mm_hostname"` |  |
| mailwebSecrets.keysMap.mailcore_mta | string | `"mailcore_mta"` |  |
| mailwebSecrets.keysMap.mailcore_rest_port | string | `"mailcore_rest_port"` |  |
| mailwebSecrets.keysMap.mailcore_smtp_port | string | `"mailweb_smtp_port"` |  |
| mailwebSecrets.keysMap.mailman-api-url | string | `"mailman_api_url"` |  |
| mailwebSecrets.keysMap.mailman_admin_email | string | `"mailman_admin_email"` |  |
| mailwebSecrets.keysMap.mailman_core_password | string | `"mailman_core_password"` |  |
| mailwebSecrets.keysMap.mailman_core_user | string | `"mailman_core_user"` |  |
| mailwebSecrets.keysMap.mailweb_database_url | string | `"mailweb_database_url"` |  |
| mailwebSecrets.keysMap.mailweb_django_allowed_hosts | string | `"mailweb_django_allowed_hosts"` |  |
| mailwebSecrets.keysMap.mailweb_postorius_template_base_url | string | `"mailweb_postorius_template_base_url"` |  |
| mailwebSecrets.keysMap.mailweb_redis_ip | string | `"mailweb_redis_ip"` |  |
| mailwebSecrets.keysMap.mailweb_redis_password | string | `"mailweb_redis_password"` |  |
| mailwebSecrets.keysMap.mailweb_redis_port | string | `"mailweb_redis_port"` |  |
| mailwebSecrets.keysMap.mailweb_server_from_domain | string | `"mailweb_server_from_domain"` |  |
| mailwebSecrets.keysMap.mailweb_server_web_domain | string | `"mailweb_server_web_domain"` |  |
| mailwebSecrets.keysMap.mailweb_smtp_host | string | `"mailweb_smtp_host"` |  |
| mailwebSecrets.keysMap.mailweb_smtp_port | string | `"mailweb_smtp_port"` |  |
| mailwebSecrets.keysMap.postgres_password | string | `"postgres_password"` |  |
| mailwebSecrets.keysMap.postgres_user | string | `"postgres_user"` |  |
| mailwebSecrets.keysMap.secret_key | string | `"secret_key"` |  |
| mailwebSecrets.name | string | `"mailman-secrets"` |  |
| mailwebSecrets.path | string | `"secrets/data/openeuler/mail_secrets_new"` |  |
| namespace.enabled | bool | `false` | 是否渲染namespace资源 |
| namespace.name | string | `"mail"` | 命名空间名称 |
| nginxWeb.configmapName | string | `"mailman-nginx-configmap"` | configmap名称 |
| nginxWeb.image.imagePullPolicy | string | `"IfNotPresent"` |  |
| nginxWeb.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler/nginx"` |  |
| nginxWeb.image.tag | string | `"latest"` |  |
| nginxWeb.resources.limits.cpu | string | `"1"` |  |
| nginxWeb.resources.limits.memory | string | `"1Gi"` |  |
| nginxWeb.resources.requests.cpu | string | `"1"` |  |
| nginxWeb.resources.requests.memory | string | `"1Gi"` |  |
| tls.secrets[0].keysMap.openeuler_org_crt | string | `"server.crt"` | 对应在vault中的键名 |
| tls.secrets[0].keysMap.openeuler_org_key | string | `"server.key"` | 对应在vault中的键名 |
| tls.secrets[0].name | string | `"mailman-cert-secrets"` |  |
| tls.secrets[0].path | string | `"secrets/data/openeuler/openeuler-org-tls"` |  |
| tls.secrets[1].keysMap."ca.crt" | string | `"server.crt"` |  |
| tls.secrets[1].keysMap."tls.crt" | string | `"server.crt"` |  |
| tls.secrets[1].keysMap."tls.key" | string | `"server.key"` |  |
| tls.secrets[1].name | string | `"mailweb-tls"` |  |
| tls.secrets[1].path | string | `"secrets/data/openeuler/openeuler-org-tls"` |  |

## 变更历史

## 1.0.0 - 2025-7-28

### 说明
- 初始版本发布

## 1.0.14 - 2026-3-09

### 说明
- 增加自定义deployment label