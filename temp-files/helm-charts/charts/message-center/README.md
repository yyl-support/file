# message-center

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 0.1.0](https://img.shields.io/badge/AppVersion-0.1.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

A Helm chart for Message Center Services

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 采集各个上游系统消息，统一格式。
* 多种消息推送方式，通知用户。
### 底层组件
该服务在启动和运行过程中依赖：
* **Database**: postgresql, cassandra
* **消息队列**：kafka
### 维护者

| 名称           | 邮箱               | Github ID    |
|--------------|------------------|--------------|
| Hourunze | 1043170898@qq.com | Hourunze1997 |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| collectCronDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| collectCronDeployment.args[1] | string | `"--forum-config-file=/vault/secrets/forum_conf.yaml"` |  |
| collectCronDeployment.enabled | bool | `false` |  |
| collectCronDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| collectCronDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-collect-cron-prod"` |  |
| collectCronDeployment.image.tag | string | `"release_openeuler-96f512"` |  |
| collectCronDeployment.name | string | `"collect-cron-deployment"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-forum_conf.yaml" | string | `"0400"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-redis.crt" | string | `"0400"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-forum_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-redis.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.cronConf }}\n{{- end }}\n"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-forum_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.cronForumConf }}\n{{- end }}\n"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.kafkaCrt }}\n{{- end }}\n"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-redis.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.redisCrt }}\n{{- end }}\n"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| collectCronDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| collectCronDeployment.resources.limits.cpu | int | `2` |  |
| collectCronDeployment.resources.limits.memory | string | `"8Gi"` |  |
| collectCronDeployment.resources.requests.cpu | string | `"500m"` |  |
| collectCronDeployment.resources.requests.memory | string | `"500Mi"` |  |
| collectCronDeployment.strategy.rollingUpdate.maxUnavailable | int | `1` |  |
| collectCronDeployment.strategy.type | string | `"RollingUpdate"` |  |
| collectDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| collectDeployment.args[1] | string | `"--eur-build-config-file=/vault/secrets/eur_build_conf.yaml"` |  |
| collectDeployment.args[2] | string | `"--meeting-config-file=/vault/secrets/meeting_conf.yaml"` |  |
| collectDeployment.args[3] | string | `"--certification-config-file=/vault/secrets/certification_conf.yaml"` |  |
| collectDeployment.args[4] | string | `"--software-review-config-file=/vault/secrets/software_review_conf.yaml"` |  |
| collectDeployment.enabled | bool | `false` |  |
| collectDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| collectDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-collect-prod"` |  |
| collectDeployment.image.tag | string | `"release-openeuler-47690e"` |  |
| collectDeployment.name | string | `"collect-deployment"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-certification_conf.yaml" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-eur_build_conf.yaml" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka-hk.crt" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-meeting_conf.yaml" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-software_review_conf.yaml" | string | `"0400"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-certification_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-eur_build_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka-hk.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-meeting_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-software_re review_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-certification_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectCertification }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectConf }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-eur_build_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectEurBuildConf }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka-hk.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.kafkaHkCrt }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.kafkaCrt }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-meeting_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectMeetingConf }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-software_review_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectSoftwareReview }}\n{{- end }}\n"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| collectDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| collectDeployment.replicaCount | int | `1` |  |
| collectDeployment.resources.limits.cpu | int | `2` |  |
| collectDeployment.resources.limits.memory | string | `"8Gi"` |  |
| collectDeployment.resources.requests.cpu | string | `"500m"` |  |
| collectDeployment.resources.requests.memory | string | `"500Mi"` |  |
| collectDeployment.strategy.rollingUpdate.maxSurge | int | `1` |  |
| collectDeployment.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| collectDeployment.strategy.type | string | `"RollingUpdate"` |  |
| collectGithookDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| collectGithookDeployment.args[1] | string | `"--port=8080"` |  |
| collectGithookDeployment.args[2] | string | `"--handle-path=gitcode-hook"` |  |
| collectGithookDeployment.enabled | bool | `true` |  |
| collectGithookDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| collectGithookDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-collect-githook-test"` |  |
| collectGithookDeployment.image.tag | string | `"release-openfuyao-b8eb58"` |  |
| collectGithookDeployment.livenessProbe.failureThreshold | int | `3` |  |
| collectGithookDeployment.livenessProbe.initialDelaySeconds | int | `10` |  |
| collectGithookDeployment.livenessProbe.periodSeconds | int | `10` |  |
| collectGithookDeployment.livenessProbe.successThreshold | int | `1` |  |
| collectGithookDeployment.livenessProbe.tcpSocket.port | int | `8080` |  |
| collectGithookDeployment.livenessProbe.timeoutSeconds | int | `5` |  |
| collectGithookDeployment.name | string | `"collect-githook-deployment"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.collectConf }}\n{{- end }}\n"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.kafkaHkCrt }}\n{{- end }}\n"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| collectGithookDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| collectGithookDeployment.readinessProbe.failureThreshold | int | `3` |  |
| collectGithookDeployment.readinessProbe.initialDelaySeconds | int | `10` |  |
| collectGithookDeployment.readinessProbe.periodSeconds | int | `10` |  |
| collectGithookDeployment.readinessProbe.successThreshold | int | `1` |  |
| collectGithookDeployment.readinessProbe.tcpSocket.port | int | `8080` |  |
| collectGithookDeployment.readinessProbe.timeoutSeconds | int | `5` |  |
| collectGithookDeployment.replicaCount | int | `1` |  |
| collectGithookDeployment.resources.limits.cpu | int | `2` |  |
| collectGithookDeployment.resources.limits.memory | string | `"8Gi"` |  |
| collectGithookDeployment.resources.requests.cpu | string | `"500m"` |  |
| collectGithookDeployment.resources.requests.memory | string | `"500Mi"` |  |
| collectGithookDeployment.strategy.rollingUpdate.maxSurge | int | `1` |  |
| collectGithookDeployment.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| collectGithookDeployment.strategy.type | string | `"RollingUpdate"` |  |
| collectGithookService.app | string | `"collect-githook-deployment"` |  |
| collectGithookService.enabled | bool | `true` |  |
| collectGithookService.name | string | `"collect-githook-service"` |  |
| collectGithookService.port | int | `8080` |  |
| collectGithookService.portName | string | `"http-port"` |  |
| collectGithookService.targetPort | int | `8080` |  |
| collectGithookService.type | string | `"ClusterIP"` |  |
| imagePullSecrets.name | string | `"huawei-swr-image-pull-secret"` |  |
| istio.nslabel | object | `{}` |  |
| managerDeployment.app | string | `"manager"` |  |
| managerDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| managerDeployment.args[1] | string | `"--server-key=/vault/secrets/server.key"` |  |
| managerDeployment.args[2] | string | `"--server-cert=/vault/secrets/server.crt"` |  |
| managerDeployment.enabled | bool | `true` |  |
| managerDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| managerDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-manager-prod"` |  |
| managerDeployment.image.tag | string | `"release-openeuler-personal_center-02ca02"` |  |
| managerDeployment.livenessProbe.failureThreshold | int | `3` |  |
| managerDeployment.livenessProbe.httpGet.path | string | `"/message_center/health"` |  |
| managerDeployment.livenessProbe.httpGet.port | int | `8082` |  |
| managerDeployment.livenessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| managerDeployment.livenessProbe.initialDelaySeconds | int | `10` |  |
| managerDeployment.livenessProbe.periodSeconds | int | `10` |  |
| managerDeployment.livenessProbe.successThreshold | int | `1` |  |
| managerDeployment.livenessProbe.timeoutSeconds | int | `5` |  |
| managerDeployment.name | string | `"manager-deployment"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.managerConf }}\n{{- end }}\n"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.servercrt }}\n{{- end }}\n"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.serverkey }}\n{{- end }}\n"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| managerDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| managerDeployment.readinessProbe.failureThreshold | int | `3` |  |
| managerDeployment.readinessProbe.httpGet.path | string | `"/message_center/health"` |  |
| managerDeployment.readinessProbe.httpGet.port | int | `8082` |  |
| managerDeployment.readinessProbe.httpGet.scheme | string | `"HTTPS"` |  |
| managerDeployment.readinessProbe.initialDelaySeconds | int | `10` |  |
| managerDeployment.readinessProbe.periodSeconds | int | `10` |  |
| managerDeployment.readinessProbe.successThreshold | int | `1` |  |
| managerDeployment.readinessProbe.timeoutSeconds | int | `5` |  |
| managerDeployment.replicaCount | int | `1` |  |
| managerDeployment.resources.limits.cpu | int | `2` |  |
| managerDeployment.resources.limits.memory | string | `"8Gi"` |  |
| managerDeployment.resources.requests.cpu | string | `"500m"` |  |
| managerDeployment.resources.requests.memory | string | `"500Mi"` |  |
| managerDeployment.strategy.rollingUpdate.maxSurge | int | `1` |  |
| managerDeployment.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| managerDeployment.strategy.type | string | `"RollingUpdate"` |  |
| managerService.app | string | `"manager"` |  |
| managerService.enabled | bool | `true` |  |
| managerService.name | string | `"manager-service"` |  |
| managerService.port | int | `8082` |  |
| managerService.portName | string | `"http-port"` |  |
| managerService.targetPort | int | `8082` |  |
| managerService.type | string | `"ClusterIP"` |  |
| namespace | string | `"openfuyao-message-center"` |  |
| pushDeployment.app | string | `"push"` |  |
| pushDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| pushDeployment.args[1] | string | `"--gitee-config-file=/vault/secrets/gitee_conf.yaml"` |  |
| pushDeployment.enabled | bool | `true` |  |
| pushDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| pushDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-push-prod"` |  |
| pushDeployment.image.tag | string | `"release-openeuler-c6a9a8"` |  |
| pushDeployment.name | string | `"push-deployment"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-gitee_conf.yaml" | string | `"0400"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-gitee_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.pushConf }}\n{{- end }}\n"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-gitee_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.pushGiteeConf }}\n{{- end }}\n"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}\n{{ .Data.data.kafkaHkCrt }}\n{{- end }}\n"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| pushDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| pushDeployment.replicaCount | int | `1` |  |
| pushDeployment.resources.limits.cpu | int | `2` |  |
| pushDeployment.resources.limits.memory | string | `"8Gi"` |  |
| pushDeployment.resources.requests.cpu | string | `"500m"` |  |
| pushDeployment.resources.requests.memory | string | `"500Mi"` |  |
| pushDeployment.strategy.rollingUpdate.maxSurge | int | `1` |  |
| pushDeployment.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| pushDeployment.strategy.type | string | `"RollingUpdate"` |  |
| securityContext.allowPrivilegeEscalation | bool | `false` |  |
| securityContext.capabilities.drop[0] | string | `"ALL"` |  |
| securityContext.readOnlyRootFilesystem | bool | `true` |  |
| securityContext.runAsUser | int | `1000` |  |
| serviceAccount.name | string | `"openfuyao-message-center"` |  |
| transferDeployment.app | string | `"transfer"` |  |
| transferDeployment.args[0] | string | `"--config-file=/vault/secrets/conf.yaml"` |  |
| transferDeployment.args[1] | string | `"--gitee-config-file=/vault/secrets/gitee_conf.yaml"` |  |
| transferDeployment.enabled | bool | `true` |  |
| transferDeployment.image.pullPolicy | string | `"IfNotPresent"` |  |
| transferDeployment.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/message-center/message-transfer-test"` |  |
| transferDeployment.image.tag | string | `"release-openfuyao-39e6a8"` |  |
| transferDeployment.name | string | `"transfer-deployment"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-gitee_conf.yaml" | string | `"0400"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-perms-kafka.crt" | string | `"0400"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-gitee_conf.yaml" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-secret-kafka.crt" | string | `"internal/data/infra-test/openfuyao-message-center"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}  \n{{ .Data.data.transferConf }}\n{{- end }}\n"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-gitee_conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}  \n{{ .Data.data.transferGiteeConf }}\n{{- end }}\n"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-inject-template-kafka.crt" | string | `"{{- with secret \"internal/data/infra-test/openfuyao-message-center\" -}}  \n{{ .Data.data.kafkaHkCrt }}\n{{- end }}\n"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/role" | string | `"openfuyao-message-center"` |  |
| transferDeployment.podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` |  |
| transferDeployment.replicaCount | int | `1` |  |
| transferDeployment.resources.limits.cpu | int | `2` |  |
| transferDeployment.resources.limits.memory | string | `"8Gi"` |  |
| transferDeployment.resources.requests.cpu | string | `"500m"` |  |
| transferDeployment.resources.requests.memory | string | `"500Mi"` |  |
| transferDeployment.strategy.rollingUpdate.maxSurge | int | `1` |  |
| transferDeployment.strategy.rollingUpdate.maxUnavailable | int | `0` |  |
| transferDeployment.strategy.type | string | `"RollingUpdate"` |  |
| volumes[0].name | string | `"token-vol"` |  |
| volumes[0].projected.sources[0].serviceAccountToken.audience | string | `"api"` |  |
| volumes[0].projected.sources[0].serviceAccountToken.expirationSeconds | int | `600` |  |
| volumes[0].projected.sources[0].serviceAccountToken.path | string | `"token"` |  |
| autoscale.enabled | bool | `false` | 是否应用自动伸缩 |
| autoscale.start | string | `"30 0 * * *"` | 副本保持起始时间 |
| autoscale.end | string | `"55 23 * * *"` | 副本保持结束时间 |

## 变更历史

## 1.0.0 - 2025-9-23

### 说明
- 初始版本发布

## 1.0.1 - 2026-1-26
### 说明
- 添加deployment labels

## 1.0.2 - 2026-2-28

### 说明
- 增加autoscale配置