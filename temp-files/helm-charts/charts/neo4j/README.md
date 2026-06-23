# neo4j

![Version: 2025.8.0](https://img.shields.io/badge/Version-2025.8.0-informational?style=flat-square) ![AppVersion: 2025.08.0](https://img.shields.io/badge/AppVersion-2025.08.0-informational?style=flat-square)

Neo4j is the world's leading graph database

**Homepage:** <https://www.neo4j.com>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| bfeshti | <bledi.feshti@neotechnology.com> |  |
| Rigert Alekaj | <rigert.alekaj@neo4j.com> |  |

## Source Code

* <https://github.com/neo4j/neo4j>
* <https://github.com/neo4j/docker-neo4j>

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| additionalVolumeMounts | list | `[]` |  |
| additionalVolumes | list | `[]` |  |
| analytics.enabled | bool | `false` |  |
| analytics.type.name | string | `"primary"` |  |
| apoc_config | object | `{}` |  |
| apoc_credentials | object | `{}` |  |
| clusterDomain | string | `"cluster.local"` |  |
| config."dbms.security.tls_reload_enabled" | string | `"true"` |  |
| config."internal.dbms.sharded_property_database.enabled" | string | `"false"` |  |
| config."server.config.strict_validation.enabled" | string | `"false"` |  |
| containerSecurityContext.capabilities.drop[0] | string | `"ALL"` |  |
| containerSecurityContext.runAsGroup | int | `7474` |  |
| containerSecurityContext.runAsNonRoot | bool | `true` |  |
| containerSecurityContext.runAsUser | int | `7474` |  |
| disableLookups | bool | `true` |  |
| env | object | `{}` |  |
| fullnameOverride | string | `""` |  |
| image.customImage | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/neo4j:2025.08.0"` |  |
| image.imagePullPolicy | string | `"IfNotPresent"` |  |
| image.imagePullSecrets[0] | string | `"huawei-swr-image-pull-secret"` |  |
| image.registry | string | `""` |  |
| image.repository | string | `""` |  |
| image.tag | string | `""` |  |
| jvm.additionalJvmArguments | list | `[]` |  |
| jvm.useNeo4jDefaultJvmArguments | bool | `true` |  |
| ldapPasswordFromSecret | string | `""` |  |
| ldapPasswordMountPath | string | `""` |  |
| livenessProbe.failureThreshold | int | `40` |  |
| livenessProbe.periodSeconds | int | `5` |  |
| livenessProbe.tcpSocket.port | int | `7687` |  |
| livenessProbe.timeoutSeconds | int | `10` |  |
| logInitialPassword | bool | `true` |  |
| logging.serverLogsXml | string | `""` |  |
| logging.userLogsXml | string | `""` |  |
| nameOverride | string | `""` |  |
| neo4j.acceptLicenseAgreement | string | `"no"` |  |
| neo4j.edition | string | `"community"` |  |
| neo4j.labels | string | `nil` |  |
| neo4j.name | string | `"my-standalone"` |  |
| neo4j.offlineMaintenanceModeEnabled | bool | `false` |  |
| neo4j.operations.enableServer | bool | `false` |  |
| neo4j.operations.image | string | `"neo4j/helm-charts-operations:2025.8.0"` |  |
| neo4j.operations.labels | object | `{}` |  |
| neo4j.operations.protocol | string | `"neo4j"` |  |
| neo4j.password | string | `""` |  |
| neo4j.passwordFromSecret | string | `""` |  |
| neo4j.resources.cpu | string | `"0.5"` |  |
| neo4j.resources.memory | string | `"2Gi"` |  |
| nodeSelector | object | `{}` |  |
| podDisruptionBudget.enabled | bool | `false` |  |
| podDisruptionBudget.labels | object | `{}` |  |
| podDisruptionBudget.matchExpressions | list | `[]` |  |
| podDisruptionBudget.matchLabels | object | `{}` |  |
| podDisruptionBudget.maxUnavailable | string | `""` |  |
| podDisruptionBudget.minAvailable | string | `""` |  |
| podSpec.annotations | object | `{}` |  |
| podSpec.containers | list | `[]` |  |
| podSpec.dnsPolicy | string | `"ClusterFirst"` |  |
| podSpec.initContainers | list | `[]` |  |
| podSpec.loadbalancer | string | `"include"` |  |
| podSpec.nodeAffinity | object | `{}` |  |
| podSpec.podAntiAffinity | bool | `true` |  |
| podSpec.priorityClassName | string | `""` |  |
| podSpec.serviceAccountName | string | `""` |  |
| podSpec.terminationGracePeriodSeconds | int | `3600` |  |
| podSpec.tolerations | list | `[]` |  |
| podSpec.topologySpreadConstraints | list | `[]` |  |
| readinessProbe.failureThreshold | int | `20` |  |
| readinessProbe.periodSeconds | int | `5` |  |
| readinessProbe.tcpSocket.port | int | `7687` |  |
| readinessProbe.timeoutSeconds | int | `10` |  |
| secretMounts | object | `{}` |  |
| securityContext.fsGroup | int | `7474` |  |
| securityContext.fsGroupChangePolicy | string | `"Always"` |  |
| securityContext.runAsGroup | int | `7474` |  |
| securityContext.runAsNonRoot | bool | `true` |  |
| securityContext.runAsUser | int | `7474` |  |
| serviceMonitor.enabled | bool | `false` |  |
| serviceMonitor.interval | string | `""` |  |
| serviceMonitor.jobLabel | string | `""` |  |
| serviceMonitor.labels | object | `{}` |  |
| serviceMonitor.namespaceSelector | object | `{}` |  |
| serviceMonitor.path | string | `""` |  |
| serviceMonitor.port | string | `""` |  |
| serviceMonitor.selector | object | `{}` |  |
| serviceMonitor.targetLabels | list | `[]` |  |
| services.admin.annotations | object | `{}` |  |
| services.admin.enabled | bool | `true` |  |
| services.admin.spec.type | string | `"ClusterIP"` |  |
| services.default.annotations | object | `{}` |  |
| services.internals.annotations | object | `{}` |  |
| services.internals.enabled | bool | `false` |  |
| services.internals.spec.type | string | `"ClusterIP"` |  |
| services.neo4j.annotations | object | `{}` |  |
| services.neo4j.cleanup.enabled | bool | `true` |  |
| services.neo4j.cleanup.image.digest | string | `""` |  |
| services.neo4j.cleanup.image.imagePullPolicy | string | `"IfNotPresent"` |  |
| services.neo4j.cleanup.image.registry | string | `"registry.k8s.io"` |  |
| services.neo4j.cleanup.image.repository | string | `"kubernetes/kubectl"` |  |
| services.neo4j.cleanup.image.tag | string | `""` |  |
| services.neo4j.cleanup.podAnnotations."sidecar.istio.io/inject" | string | `"false"` |  |
| services.neo4j.enabled | bool | `true` |  |
| services.neo4j.multiCluster | bool | `false` |  |
| services.neo4j.ports.backup.enabled | bool | `false` |  |
| services.neo4j.ports.bolt.enabled | bool | `true` |  |
| services.neo4j.ports.http.enabled | bool | `true` |  |
| services.neo4j.ports.https.enabled | bool | `true` |  |
| services.neo4j.selector."helm.neo4j.com/neo4j.loadbalancer" | string | `"include"` |  |
| services.neo4j.spec.type | string | `"LoadBalancer"` |  |
| ssl.bolt.privateKey.secretName | string | `nil` |  |
| ssl.bolt.privateKey.subPath | string | `nil` |  |
| ssl.bolt.publicCertificate.secretName | string | `nil` |  |
| ssl.bolt.publicCertificate.subPath | string | `nil` |  |
| ssl.bolt.revokedCerts.sources | list | `[]` |  |
| ssl.bolt.trustedCerts.sources | list | `[]` |  |
| ssl.cluster.privateKey.secretName | string | `nil` |  |
| ssl.cluster.privateKey.subPath | string | `nil` |  |
| ssl.cluster.publicCertificate.secretName | string | `nil` |  |
| ssl.cluster.publicCertificate.subPath | string | `nil` |  |
| ssl.cluster.revokedCerts.sources | list | `[]` |  |
| ssl.cluster.trustedCerts.sources | list | `[]` |  |
| ssl.https.privateKey.secretName | string | `nil` |  |
| ssl.https.privateKey.subPath | string | `nil` |  |
| ssl.https.publicCertificate.secretName | string | `nil` |  |
| ssl.https.publicCertificate.subPath | string | `nil` |  |
| ssl.https.revokedCerts.sources | list | `[]` |  |
| ssl.https.trustedCerts.sources | list | `[]` |  |
| startupProbe.failureThreshold | int | `1000` |  |
| startupProbe.periodSeconds | int | `5` |  |
| startupProbe.tcpSocket.port | int | `7687` |  |
| statefulset.metadata.annotations | string | `nil` |  |
| volumes.backups.disableSubPathExpr | bool | `false` |  |
| volumes.backups.labels | object | `{}` |  |
| volumes.backups.mode | string | `"share"` |  |
| volumes.backups.share.name | string | `"data"` |  |
| volumes.data.defaultStorageClass.accessModes[0] | string | `"ReadWriteOnce"` |  |
| volumes.data.defaultStorageClass.requests.storage | string | `"10Gi"` |  |
| volumes.data.disableSubPathExpr | bool | `false` |  |
| volumes.data.dynamic.accessModes[0] | string | `"ReadWriteOnce"` |  |
| volumes.data.dynamic.requests.storage | string | `"100Gi"` |  |
| volumes.data.dynamic.storageClassName | string | `"csi-disk"` |  |
| volumes.data.labels."failure-domain.beta.kubernetes.io/region" | string | `"ap-southeast-1"` |  |
| volumes.data.labels."failure-domain.beta.kubernetes.io/zone" | string | `"ap-southeast-1a"` |  |
| volumes.data.mode | string | `"dynamic"` |  |
| volumes.data.selector.accessModes[0] | string | `"ReadWriteOnce"` |  |
| volumes.data.selector.requests.storage | string | `"100Gi"` |  |
| volumes.data.selector.selectorTemplate.matchLabels."helm.neo4j.com/volume-role" | string | `"data"` |  |
| volumes.data.selector.selectorTemplate.matchLabels.app | string | `"{{ .Values.neo4j.name }}"` |  |
| volumes.data.selector.storageClassName | string | `"manual"` |  |
| volumes.data.volume.setOwnerAndGroupWritableFilePermissions | bool | `false` |  |
| volumes.data.volumeClaimTemplate | object | `{}` |  |
| volumes.import.disableSubPathExpr | bool | `false` |  |
| volumes.import.labels | object | `{}` |  |
| volumes.import.mode | string | `"share"` |  |
| volumes.import.share.name | string | `"data"` |  |
| volumes.licenses.disableSubPathExpr | bool | `false` |  |
| volumes.licenses.labels | object | `{}` |  |
| volumes.licenses.mode | string | `"share"` |  |
| volumes.licenses.share.name | string | `"data"` |  |
| volumes.logs.disableSubPathExpr | bool | `false` |  |
| volumes.logs.labels | object | `{}` |  |
| volumes.logs.mode | string | `"share"` |  |
| volumes.logs.share.name | string | `"data"` |  |
| volumes.metrics.disableSubPathExpr | bool | `false` |  |
| volumes.metrics.labels | object | `{}` |  |
| volumes.metrics.mode | string | `"share"` |  |
| volumes.metrics.share.name | string | `"data"` |  |

