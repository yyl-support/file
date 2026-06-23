# infra-radar

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
Helm chart for infrastructure radar

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
1. 获取基础设施各服务在华为云codearts流水线中各类问题统计数据
2. 获取基础设施各服务PR不规范操作的统计数据

### 底层组件
1. 数据库Mysql: 存储流水线执行结果、仓库信息

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| tangjia | tangjia30@huawei.com | TangJia025 |


## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| istio.enabled | bool | `false` |  |
| namespace.name | string | `"infra-radar"` |  |
| podSecurityContext | string | `nil` |  |
| secret.ca_crt_key | string | `"tls.cert"` | secret中创建的key,格式为[secret key]: [vault key] |
| secret.enable | bool | `true` | secret启用标签,如果启用ingress,则需要启用 |
| secret.name | string | `"infra-radar-website-tls"` | secret资源名 |
| secret.path | string | `"secrets/data/infra-test/domain-tls"` | secret资源在vault中存放路径 |
| secret.tls_crt_key | string | `"tls.cert"` | secret中创建的key,格式为[secret key]: [vault key] |
| secret.tls_key_key | string | `"tls.key"` | secret中创建的key,格式为[secret key]: [vault key] |
| server.args | string | `nil` |  |
| server.deploymentLabels."virtual-kubelet.io/burst-to-cci" | string | `"enforce"` |  |
| server.enabled | bool | `true` |  |
| server.image.pullPolicy | string | `"IfNotPresent"` |  |
| server.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/infra-radar-server"` |  |
| server.image.tag | string | `"main-e8dcd9"` |  |
| server.imagePullSecrets[0] | string | `"huawei-swr-image-pull-secret"` |  |
| server.ingress.host | string | `"radar.test.osinfra.cn"` |  |
| server.ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` |  |
| server.ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` |  |
| server.ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` |  |
| server.ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` |  |
| server.ingress.subpaths[0].annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"100"` |  |
| server.ingress.subpaths[0].name | string | `"api-server-ingress"` |  |
| server.ingress.subpaths[0].path | string | `"/infra-radar"` |  |
| server.ingress.subpaths[0].pathType | string | `"Prefix"` |  |
| server.ingress.subpaths[0].serviceName | string | `"server-service"` |  |
| server.ingress.subpaths[0].servicePort | int | `8080` |  |
| server.livenessProbe.failureThreshold | int | `3` |  |
| server.livenessProbe.httpGet.path | string | `"/infra-dadar/sayhello"` |  |
| server.livenessProbe.httpGet.port | int | `8080` |  |
| server.livenessProbe.httpGet.scheme | string | `"HTTP"` |  |
| server.livenessProbe.initialDelaySeconds | int | `5` |  |
| server.livenessProbe.periodSeconds | int | `10` |  |
| server.livenessProbe.successThreshold | int | `1` |  |
| server.livenessProbe.timeoutSeconds | int | `5` |  |
| server.name | string | `"server"` |  |
| server.nodeSelector | string | `nil` |  |
| server.podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-perms-app.yaml" | string | `"0400"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-secret-app.yaml" | string | `"internal/data/infra-test/infra-radar"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-inject-template-app.yaml" | string | `"{{- with secret \"internal/data/infra-test/infra-radar\" -}}\n{{ .Data.data.config }}\n{{- end }}\n"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| server.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| server.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| server.podAnnotations."vault.hashicorp.com/role" | string | `"infra-radar"` |  |
| server.podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/opt/app/infra-radar/config"` |  |
| server.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| server.podLabels.app | string | `"server"` |  |
| server.readinessProbe.failureThreshold | int | `3` |  |
| server.readinessProbe.httpGet.path | string | `"/infra-dadar/sayhello"` |  |
| server.readinessProbe.httpGet.port | int | `8080` |  |
| server.readinessProbe.httpGet.scheme | string | `"HTTP"` |  |
| server.readinessProbe.initialDelaySeconds | int | `5` |  |
| server.readinessProbe.periodSeconds | int | `10` |  |
| server.readinessProbe.successThreshold | int | `1` |  |
| server.readinessProbe.timeoutSeconds | int | `5` |  |
| server.replicaCount | int | `1` |  |
| server.resources.limits.cpu | int | `1` |  |
| server.resources.limits.memory | string | `"1Gi"` |  |
| server.resources.requests.cpu | int | `1` |  |
| server.resources.requests.memory | string | `"1Gi"` |  |
| server.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| server.securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| server.securityContext.runAsUser | int | `1000` |  |
| server.service.port | int | `8080` |  |
| server.service.targetPort | int | `8080` |  |
| server.updateStrategy.rollingUpdate.maxSurge | int | `1` |  |
| server.updateStrategy.rollingUpdate.maxUnavailable | int | `0` |  |
| server.updateStrategy.type | string | `"RollingUpdate"` |  |
| server.volumeMounts | string | `nil` |  |
| server.volumes[0].name | string | `"token-vol"` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| server.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| serviceAccount.automount | bool | `false` |  |
| serviceAccount.name | string | `"infra-radar"` |  |
| servicelinks.enable | bool | `false` |  |
| website.appName | string | `"website"` |  |
| website.autoscale.enabled | bool | `false` |  |
| website.autoscale.end | string | `"55 23 * * *"` |  |
| website.autoscale.start | string | `"30 8 * * *"` |  |
| website.deploymentLabels."virtual-kubelet.io/burst-to-cci" | string | `"enforce"` |  |
| website.enabled | bool | `true` |  |
| website.env[0].name | string | `"DET_URL"` |  |
| website.env[0].value | string | `"https://radar.test.osinfra.cn/"` |  |
| website.image.pullPolicy | string | `"IfNotPresent"` |  |
| website.image.pullSecret | string | `"huawei-swr-image-pull-secret"` |  |
| website.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/infra-radar-website"` |  |
| website.image.tag | string | `"main-e8dcd9"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/backend-protocol" | string | `"HTTPS"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/cors-allow-origin" | string | `"*"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/enable-cors" | string | `"true"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/limit-burst-multiplier" | string | `"1"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/limit-rpm" | string | `"1000"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/proxy-body-size" | string | `"10m"` |  |
| website.ingress.annotations."nginx.ingress.kubernetes.io/server-snippet" | string | `"location ^~ /favicon.ico {\n  return 404;\n}\n"` |  |
| website.ingress.className | string | `"nginx"` |  |
| website.ingress.enabled | bool | `true` |  |
| website.ingress.host | string | `"radar.test.osinfra.cn"` |  |
| website.initContainers[0].command[0] | string | `"/bin/bash"` |  |
| website.initContainers[0].command[1] | string | `"-c"` |  |
| website.initContainers[0].command[2] | string | `"chmod 0700 /etc/nginx/cert/; chown -R 1000:1000 /etc/nginx/cert/; chmod g-s /etc/nginx/cert/; ls -ld /etc/nginx/cert/"` |  |
| website.initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler:22.03-lts-sp3"` |  |
| website.initContainers[0].imagePullPolicy | string | `"IfNotPresent"` |  |
| website.initContainers[0].name | string | `"init"` |  |
| website.livenessProbe.failureThreshold | int | `3` |  |
| website.livenessProbe.httpGet.path | string | `"/"` |  |
| website.livenessProbe.httpGet.port | int | `8080` |  |
| website.livenessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| website.livenessProbe.initialDelaySeconds | int | `10` |  |
| website.livenessProbe.periodSeconds | int | `10` |  |
| website.livenessProbe.successThreshold | int | `1` |  |
| website.livenessProbe.timeoutSeconds | int | `10` |  |
| website.podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-command-abc.txt" | string | `"if [ $(netstat -anlp | grep 8080| wc -l) -ge 1 ]; then rm -rf /etc/nginx/cert/*; else echo \"service not running skip\"; fi\n"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-abc.txt" | string | `"0400"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-dhparam.pem" | string | `"0400"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-abc.txt" | string | `"internal/data/infra-test/test-osinfra-cn-tls-ssl"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-dhparam.pem" | string | `"internal/data/infra-test/test-osinfra-cn-tls-ssl"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/infra-test/test-osinfra-cn-tls-ssl"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/infra-test/test-osinfra-cn-tls-ssl"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-abc.txt" | string | `"{{- with secret \"internal/data/infra-test/test-osinfra-cn-tls-ssl\" -}}\n{{ .Data.data.certificatePassword }}\n{{- end }}\n"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-dhparam.pem" | string | `"{{- with secret \"internal/data/infra-test/test-osinfra-cn-tls-ssl\" -}}\n{{ .Data.data.dhparamPem }}\n{{- end }}\n"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/infra-test/test-osinfra-cn-tls-ssl\" -}}\n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/infra-test/test-osinfra-cn-tls-ssl\" -}}\n{{ .Data.data.ServerKey }}\n{{- end }}\n"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| website.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| website.podAnnotations."vault.hashicorp.com/role" | string | `"infra-radar"` |  |
| website.podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/etc/nginx/cert/"` |  |
| website.podAnnotations."vault.hashicorp.com/template-static-secret-render-interval" | string | `"5s"` |  |
| website.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| website.podLabels.app | string | `"website"` |  |
| website.readinessProbe.failureThreshold | int | `3` |  |
| website.readinessProbe.httpGet.path | string | `"/"` |  |
| website.readinessProbe.httpGet.port | int | `8080` |  |
| website.readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| website.readinessProbe.initialDelaySeconds | int | `10` |  |
| website.readinessProbe.periodSeconds | int | `10` |  |
| website.readinessProbe.successThreshold | int | `1` |  |
| website.readinessProbe.timeoutSeconds | int | `10` |  |
| website.replicaCount | int | `1` |  |
| website.resources.limits.cpu | int | `1` |  |
| website.resources.limits.memory | string | `"1Gi"` |  |
| website.resources.requests.cpu | int | `1` |  |
| website.resources.requests.memory | string | `"1Gi"` |  |
| website.securityContext.allowPrivilegeEscalation | bool | `false` |  |
| website.securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| website.securityContext.runAsUser | int | `1000` |  |
| website.service.port | int | `8080` |  |
| website.service.portName | string | `"http-1"` |  |
| website.service.targetPort | int | `8080` |  |
| website.service.type | string | `"ClusterIP"` |  |
| website.strategy.rollingUpdate.maxSurge | int | `1` |  |
| website.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| website.strategy.type | string | `"RollingUpdate"` |  |
| website.volumeMounts | list | `[]` |  |
| website.volumes[0].name | string | `"token-vol"` |  |
| website.volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| website.volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| website.volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |


