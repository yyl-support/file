# community-summary

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
社区通用年终总结模版

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 支持通过OIDC接入第三方账号获取用户信息。

### 底层组件
该服务在启动和运行过程中依赖：
* **静态页面展示**: nginx
* **登录对接第三方平台**: oauth2-proxy

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| tfhddd | taofeihu1@huawei.com     | tfhddd |
| lishengbo | lishengbo@h-partners.com | lishengbo0907 |

### Helm chart values说明

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| community.name | string | `"mindspore"` | 社区名 |
| namespace.name | string | `"mindspore-summary"` | 命名空间 |
| oauth[0].args[0] | string | `"--provider=gitee"` | 启动参数 |
| oauth[0].args[10] | string | `"--custom-templates-dir=/bin/static/login"` | 启动参数 |
| oauth[0].args[11] | string | `"--custom-templates-sign-in=mindspore.html"` | 启动参数 |
| oauth[0].args[1] | string | `"--email-domain=*"` | 启动参数 |
| oauth[0].args[2] | string | `"--proxy-prefix=/oauth2"` | 启动参数 |
| oauth[0].args[3] | string | `"--skip-validate-email=true"` | 启动参数 |
| oauth[0].args[4] | string | `"--skip-auth-regex=^/agreement_ch.html"` | 启动参数 |
| oauth[0].args[5] | string | `"--skip-auth-regex=^/agreement_en.html"` | 启动参数 |
| oauth[0].args[6] | string | `"--upstream=http://mindspore-summary-service.community-summary.svc.cluster.local:8080"` | 启动参数 |
| oauth[0].args[7] | string | `"--http-address=0.0.0.0:4180"` | 启动参数 |
| oauth[0].args[8] | string | `"--cookie-expire=6h0m0s"` | 启动参数 |
| oauth[0].args[9] | string | `"--set-xauthrequest=true"` | 启动参数 |
| oauth[0].env[0].name | string | `"OAUTH2_PROXY_CLIENT_ID"` | 启动参数 |
| oauth[0].env[0].value | string | `"mindspre_client_id"` | 启动参数 |
| oauth[0].env[1].name | string | `"OAUTH2_PROXY_CLIENT_SECRET"` | 启动参数 |
| oauth[0].env[1].value | string | `"mindspre_client_secret"` | 启动参数 |
| oauth[0].env[2].name | string | `"OAUTH2_PROXY_COOKIE_SECRET"` | 启动参数 |
| oauth[0].env[2].value | string | `"mindspre_cookie_secret"` | 启动参数 |
| oauth[0].image.pullPolicy | string | `"Always"` | 镜像拉取策略 |
| oauth[0].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/oauth2-proxy"` | 镜像名 |
| oauth[0].image.tag | string | `"e7f02bd48036ba79e911412c1413d6677bf9cd6b"` | 镜像tag |
| oauth[0].ingress.annotations | string | `nil` | ingress声明项 |
| oauth[0].ingress.className | string | `"nginx"` | ingress class |
| oauth[0].ingress.host | string | `"summary-mindspore.test.osinfra.cn"` | 域名 |
| oauth[0].livenessProbe.failureThreshold | int | `3` | 健康检查参数 |
| oauth[0].livenessProbe.initialDelaySeconds | int | `5` | 健康检查参数 |
| oauth[0].livenessProbe.periodSeconds | int | `10` | 健康检查参数 |
| oauth[0].livenessProbe.successThreshold | int | `1` | 健康检查参数 |
| oauth[0].livenessProbe.tcpSocket.port | int | `4180` | 健康检查参数 |
| oauth[0].livenessProbe.timeoutSeconds | int | `5` | 健康检查参数 |
| oauth[0].podAnnotations | string | `nil` | pod声明项 |
| oauth[0].podLabels.k8s-app | string | `"mindspore-oauth2-proxy"` | pod标签 |
| oauth[0].provider | string | `"gitee"` | 对接第三方平台,可选gitee/gitcode/github |
| oauth[0].readinessProbe.failureThreshold | int | `3` | 健康检查参数 |
| oauth[0].readinessProbe.initialDelaySeconds | int | `5` | 健康检查参数 |
| oauth[0].readinessProbe.periodSeconds | int | `10` | 健康检查参数 |
| oauth[0].readinessProbe.successThreshold | int | `1` | 健康检查参数 |
| oauth[0].readinessProbe.tcpSocket.port | int | `4180` | 健康检查参数 |
| oauth[0].readinessProbe.timeoutSeconds | int | `5` | 健康检查参数 |
| oauth[0].replicaCount | int | `1` | 副本数 |
| oauth[0].resources | string | `nil` | 资源 |
| oauth[0].secret.name | string | `"mindspore-oauth-secrets"` | secret资源名 |
| oauth[0].secret.path | string | `"secrets/data/infra-test/community-summary"` | secret资源路径 |
| oauth[0].securityContext | string | `nil` | 安全策略 |
| oauth[0].service.port | int | `4180` | 端口号 |
| oauth[0].service.targetPort | int | `4180` | 端口号 |
| oauth[0].service.type | string | `"ClusterIP"` | 服务对外开放策略，仅集群内部访问 |
| oauth[0].strategy.rollingUpdate.maxSurge | int | `1` | 更新时最大超出副本数 |
| oauth[0].strategy.rollingUpdate.maxUnavailable | int | `0` | 更新时最大不可用副本数 |
| oauth[0].strategy.type | string | `"RollingUpdate"` | 更新策略 |
| oauth[0].volumeMounts | string | `nil` | 挂载路径 |
| oauth[0].volumes | string | `nil` | 挂载卷 |
| oauth[1].args[0] | string | `"--provider=github"` |  |
| oauth[1].args[10] | string | `"--custom-templates-dir=/bin/static/login"` |  |
| oauth[1].args[11] | string | `"--custom-templates-sign-in=mindspore.html"` |  |
| oauth[1].args[1] | string | `"--email-domain=*"` |  |
| oauth[1].args[2] | string | `"--proxy-prefix=/oauth2"` |  |
| oauth[1].args[3] | string | `"--skip-validate-email=true"` |  |
| oauth[1].args[4] | string | `"--skip-auth-regex=^/agreement_ch.html"` |  |
| oauth[1].args[5] | string | `"--skip-auth-regex=^/agreement_en.html"` |  |
| oauth[1].args[6] | string | `"--upstream=http://mindspore-summary-service.community-summary.svc.cluster.local:8080"` |  |
| oauth[1].args[7] | string | `"--http-address=0.0.0.0:4180"` |  |
| oauth[1].args[8] | string | `"--cookie-expire=6h0m0s"` |  |
| oauth[1].args[9] | string | `"--set-xauthrequest=true"` |  |
| oauth[1].env[0].name | string | `"OAUTH2_PROXY_CLIENT_ID"` |  |
| oauth[1].env[0].value | string | `"mindspre_github_client_id"` |  |
| oauth[1].env[1].name | string | `"OAUTH2_PROXY_CLIENT_SECRET"` |  |
| oauth[1].env[1].value | string | `"mindspre_github_client_secret"` |  |
| oauth[1].env[2].name | string | `"OAUTH2_PROXY_COOKIE_SECRET"` |  |
| oauth[1].env[2].value | string | `"mindspre_github_cookie_secret"` |  |
| oauth[1].image.pullPolicy | string | `"Always"` |  |
| oauth[1].image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/common/oauth2-proxy"` |  |
| oauth[1].image.tag | string | `"e7f02bd48036ba79e911412c1413d6677bf9cd6b"` |  |
| oauth[1].ingress.annotations | string | `nil` |  |
| oauth[1].ingress.className | string | `"nginx"` |  |
| oauth[1].ingress.host | string | `"summary-mindspore-github.test.osinfra.cn"` |  |
| oauth[1].livenessProbe.failureThreshold | int | `3` |  |
| oauth[1].livenessProbe.initialDelaySeconds | int | `5` |  |
| oauth[1].livenessProbe.periodSeconds | int | `10` |  |
| oauth[1].livenessProbe.successThreshold | int | `1` |  |
| oauth[1].livenessProbe.tcpSocket.port | int | `4180` |  |
| oauth[1].livenessProbe.timeoutSeconds | int | `5` |  |
| oauth[1].podAnnotations | string | `nil` |  |
| oauth[1].podLabels.k8s-app | string | `"mindspore-github-oauth2-proxy"` |  |
| oauth[1].provider | string | `"github"` |  |
| oauth[1].readinessProbe.failureThreshold | int | `3` |  |
| oauth[1].readinessProbe.initialDelaySeconds | int | `5` |  |
| oauth[1].readinessProbe.periodSeconds | int | `10` |  |
| oauth[1].readinessProbe.successThreshold | int | `1` |  |
| oauth[1].readinessProbe.tcpSocket.port | int | `4180` |  |
| oauth[1].readinessProbe.timeoutSeconds | int | `5` |  |
| oauth[1].replicaCount | int | `1` |  |
| oauth[1].resources | string | `nil` |  |
| oauth[1].secret.name | string | `"mindspore-oauth-github-secrets"` |  |
| oauth[1].secret.path | string | `"secrets/data/infra-test/community-summary"` |  |
| oauth[1].securityContext | string | `nil` |  |
| oauth[1].service.port | int | `4180` |  |
| oauth[1].service.targetPort | int | `4180` |  |
| oauth[1].service.type | string | `"ClusterIP"` |  |
| oauth[1].strategy.rollingUpdate.maxSurge | int | `1` |  |
| oauth[1].strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| oauth[1].strategy.type | string | `"RollingUpdate"` |  |
| oauth[1].volumeMounts | string | `nil` |  |
| oauth[1].volumes | string | `nil` |  |
| serviceAccount.automount | bool | `false` | 是否自动挂载sa |
| serviceAccount.name | string | `"community-summary"` | sa名称 |
| tls.enable | bool | `true` | 创建tls证书 |
| tls.secret.ca | string | `"tls.cert"` | vault中对应的键名 |
| tls.secret.key | string | `"tls.key"` | vault中对应的键名 |
| tls.secret.path | string | `"secrets/data/infra-test/domain-tls"` | secret资源在vault中存放路径 |
| website.env | string | `nil` |  |
| website.image.pullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像拉取密钥名 |
| website.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/mindspore/summary-test"` | 镜像名 |
| website.image.tag | string | `"v1.0.20251224113317"` | 镜像tag |
| website.livenessProbe.failureThreshold | int | `3` | 健康检查策略 |
| website.livenessProbe.initialDelaySeconds | int | `5` | 健康检查策略 |
| website.livenessProbe.periodSeconds | int | `10` | 健康检查策略 |
| website.livenessProbe.successThreshold | int | `1` | 健康检查策略 |
| website.livenessProbe.tcpSocket.port | int | `8080` | 健康检查策略 |
| website.livenessProbe.timeoutSeconds | int | `5` | 健康检查策略 |
| website.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault agent容器 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-abc.txt" | string | `"0400"` | 文件权限设置 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-dhparam.pem" | string | `"0400"` | 文件权限设置 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` | 文件权限设置 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` | 文件权限设置 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-abc.txt" | string | `"internal/data/infra-test/community-summary"` | 文件在vault中存放的路径 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-dhparam.pem" | string | `"internal/data/infra-test/community-summary"` | 文件在vault中存放的路径 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/infra-test/community-summary"` | 文件在vault中存放的路径 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/infra-test/community-summary"` | 文件在vault中存放的路径 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-abc.txt" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.certificatePassword }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-dhparam.pem" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.dhparamPem }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| website.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.ServerKey }}\n{{- end }}\n"` | 文件在vault中的模板，默认为原文 |
| website.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| website.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| website.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| website.podAnnotations."vault.hashicorp.com/role" | string | `"community-summary"` | vault权限角色名称 |
| website.podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/etc/nginx/cert/"` | 文件挂载在容器中的路径 |
| website.podLabels.app | string | `"mindspore-summary"` | pod标签 |
| website.podSecurityContext | string | `nil` | 安全策略 |
| website.readinessProbe.failureThreshold | int | `3` | 健康检查 |
| website.readinessProbe.initialDelaySeconds | int | `5` | 健康检查 |
| website.readinessProbe.periodSeconds | int | `10` | 健康检查 |
| website.readinessProbe.successThreshold | int | `1` | 健康检查 |
| website.readinessProbe.tcpSocket.port | int | `8080` | 健康检查 |
| website.readinessProbe.timeoutSeconds | int | `5` | 健康检查 |
| website.replicaCount | int | `1` | 健康检查 |
| website.resources.limits.cpu | string | `"500m"` | 资源 |
| website.resources.limits.memory | string | `"500Mi"` | 资源 |
| website.resources.requests.cpu | string | `"200m"` | 资源 |
| website.resources.requests.memory | string | `"200Mi"` | 资源 |
| website.securityContext | string | `nil` | 安全策略 |
| website.service.port | int | `8080` | 端口号 |
| website.service.portName | string | `"tls-1"` | 端口名 |
| website.service.targetPort | int | `8080` | 端口号 |
| website.service.type | string | `"ClusterIP"` | 服务对外暴露方式,仅集群内可访问 |
| website.strategy.rollingUpdate.maxSurge | int | `1` | 更新时最大超出副本数 |
| website.strategy.rollingUpdate.maxUnavailable | int | `0` | 更新时最大不可用副本数 |
| website.strategy.type | string | `"RollingUpdate"` | 更新策略 |
| website.volumeMounts | string | `nil` |  |
| website.volumes | string | `nil` |  |
| welcome.enabled | bool | `true` |  |
| welcome.env | string | `nil` |  |
| welcome.image.pullPolicy | string | `"IfNotPresent"` |  |
| welcome.image.pullSecret | string | `"huawei-swr-image-pull-secret"` |  |
| welcome.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/mindspore/summary-welcome-test"` |  |
| welcome.image.tag | string | `"2025-6115fc"` |  |
| welcome.ingress.annotations | string | `nil` |  |
| welcome.ingress.className | string | `"nginx"` |  |
| welcome.ingress.enabled | bool | `true` |  |
| welcome.ingress.host | string | `"summary-mindspore-welcome.test.osinfra.cn"` |  |
| welcome.livenessProbe.failureThreshold | int | `3` |  |
| welcome.livenessProbe.initialDelaySeconds | int | `5` |  |
| welcome.livenessProbe.periodSeconds | int | `10` |  |
| welcome.livenessProbe.successThreshold | int | `1` |  |
| welcome.livenessProbe.tcpSocket.port | int | `8080` |  |
| welcome.livenessProbe.timeoutSeconds | int | `5` |  |
| welcome.name | string | `"welcome"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-perms-abc.txt" | string | `"0400"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-perms-dhparam.pem" | string | `"0400"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-secret-abc.txt" | string | `"internal/data/infra-test/community-summary"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-secret-dhparam.pem" | string | `"internal/data/infra-test/community-summary"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/infra-test/community-summary"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/infra-test/community-summary"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-template-abc.txt" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.certificatePassword }}\n{{- end }}\n"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-template-dhparam.pem" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.dhparamPem }}\n{{- end }}\n"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/infra-test/community-summary\" -}}\n{{ .Data.data.ServerKey }}\n{{- end }}\n"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| welcome.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| welcome.podAnnotations."vault.hashicorp.com/role" | string | `"community-summary"` |  |
| welcome.podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/etc/nginx/cert/"` |  |
| welcome.podLabels.app | string | `"mindspore-summary-welcome"` |  |
| welcome.podSecurityContext | string | `nil` |  |
| welcome.readinessProbe.failureThreshold | int | `3` |  |
| welcome.readinessProbe.initialDelaySeconds | int | `5` |  |
| welcome.readinessProbe.periodSeconds | int | `10` |  |
| welcome.readinessProbe.successThreshold | int | `1` |  |
| welcome.readinessProbe.tcpSocket.port | int | `8080` |  |
| welcome.readinessProbe.timeoutSeconds | int | `5` |  |
| welcome.replicaCount | int | `1` |  |
| welcome.resources.limits.cpu | string | `"1"` |  |
| welcome.resources.limits.memory | string | `"1000Mi"` |  |
| welcome.resources.requests.cpu | string | `"1"` |  |
| welcome.resources.requests.memory | string | `"1000Mi"` |  |
| welcome.securityContext | string | `nil` |  |
| welcome.service.port | int | `8080` |  |
| welcome.service.portName | string | `"tls-1"` |  |
| welcome.service.targetPort | int | `8080` |  |
| welcome.service.type | string | `"ClusterIP"` |  |
| welcome.strategy.rollingUpdate.maxSurge | int | `1` |  |
| welcome.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| welcome.strategy.type | string | `"RollingUpdate"` |  |
| welcome.volumeMounts | string | `nil` |  |
| welcome.volumes | string | `nil` |  |

## 变更历史

## 1.0.0 - 2025-12-24

### 说明
- 初始版本发布

## 1.0.1 - 2025-12-29

### 说明
- 增加ingress转发规则适配