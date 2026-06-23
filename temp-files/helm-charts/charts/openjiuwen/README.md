# community-website

[community-website](https://github.com/opensourceways/helm-charts/tree/main/charts/community-website) community website for kubernetes deploy

![Version: 1.0.5](https://img.shields.io/badge/Version-4.14.0-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-1.14.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)

openjiuwen门户网站演示环境

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
静态资源展示

### 底层组件
该服务在启动和运行过程中依赖：
* **Database**: [MySQL 8.0+]
* **vault**: 配置文件挂载

### 维护者

| 名称        | 邮箱 | Github ID |
|-----------|------|-----------|
| zhengshangyi | zhangshangyi@huawei.com |  |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| env[0] | object | `{"name":"DET_URL","value":"https://example.com"}` | 环境变量DET_URL,用于检测容器是否启动成功,成功后则会删除配置文件 |
| global.appName | string | `"website"` | 应用名称 |
| image.pullPolicy | string | `"IfNotPresent"` | WEB容器镜像拉取策略 |
| image.pullSecret | string | `"swr-image-pull-secret"` | WEB容器镜像拉取密钥名 |
| image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/openeuler/openeuler"` | WEB容器镜像名 |
| image.tag | string | `"24.03"` | WEB容器镜像TAG,更新该字段即可完成新版本发布 |
| ingress.annotations | object | `{"nginx.ingress.kubernetes.io/backend-protocol":"HTTPS","nginx.ingress.kubernetes.io/proxy-body-size":"2m"}` | ingress 自定义声明项 |
| ingress.className | string | `"nginx"` | ingress class |
| ingress.enabled | bool | `true` | ingress启用标签 |
| ingress.host | string | `"example.com"` | 服务对外域名 |
| initContainers[0] | object | `{"command":["/bin/bash","-c","chmod 0700 /etc/nginx/cert/; chown -R 1000:1000 /etc/nginx/cert/; chmod g-s /etc/nginx/cert/; ls -ld /etc/nginx/cert/"],}` | 初始化容器启动命令,用于修改配置文件目录权限 |
| initContainers[0].image | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/openeuler:22.03-lts-sp3"` | 初始化容器镜像 |
| initContainers[0].imagePullPolicy | string | `"IfNotPresent"` | 初始化容器镜像拉取策略 |
| initContainers[0].name | string | `"init"` | 初始化容器名 |
| istio.enabled | bool | `false` | istio启用标签 |
| istio.gateway | string | `""` | istio网关配置 |
| istio.mtlsMode | string | `"DISABLE"` | istio网格间是否启用mtls,默认DISABLE |
| istio.nslabel | object | `{}` | istio命名空间资源标签,如需对接istio,则需要在namespace增加该标签 |
| istio.tlsMode | string | `"SIMPLE"` | istio虚拟后端tls模式,后端支持tls则使用SIMPLE,不支持则使用DISABLE |
| istio.virtualService | object | `{"host":"","http":[]}` | istio虚拟后端配置 |
| istio.virtualService.host | string | `""` | istio虚拟后端域名配置 |
| istio.virtualService.http | list | `[]` | istio虚拟后端http配置 |
| livenessProbe.failureThreshold | int | `3` | 失败重试次数 |
| livenessProbe.httpGet.httpHeaders[0] | object | `{"name":"Host","value":"example.com"}` | 自定义的 HTTP 头 |
| livenessProbe.httpGet.httpHeaders[0].value | string | `"example.com"` | 自定义的 HTTP 请求头内容 |
| livenessProbe.httpGet.path | string | `"/"` | 访问 HTTP 服务的路径 |
| livenessProbe.httpGet.port | int | `8080` | 容器的端口号 |
| livenessProbe.httpGet.scheme | string | `"HTTPS"` | 协议 |
| livenessProbe.initialDelaySeconds | int | `5` | 启动探测时间 |
| livenessProbe.periodSeconds | int | `20` | 执行探测的时间间隔 |
| livenessProbe.successThreshold | int | `1` | 成功探测次数 |
| livenessProbe.timeoutSeconds | int | `5` | 探测超时等待时间 |
| namespace.enabled | bool | `false` | 是否创建namespace资源: false/true |
| namespace.name | string | `"website"` | 命名空间 |
| podAnnotations."vault.hashicorp.com/agent-init-first" | string | `"true"` | vault agent作为init容器时,是否最先启动 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否启用vault inject功能,默认开启 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-abc.txt" | string | `"0400"` | 挂载配置文件abc.txt权限 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-dhparam.pem" | string | `"0400"` | 挂载配置文件dhparam.pem权限 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.crt" | string | `"0400"` | 挂载配置文件server.crt权限 |
| podAnnotations."vault.hashicorp.com/agent-inject-perms-server.key" | string | `"0400"` | 挂载配置文件server.key权限 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-abc.txt" | string | `"internal/data/example/ssl"` | 配置文件abc.txt在vault仓库中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-dhparam.pem" | string | `"internal/data/example/ssl"` | 配置文件dhparam.pem在vault仓库中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.crt" | string | `"internal/data/example/ssl"` | 配置文件server.crt在vault仓库中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-secret-server.key" | string | `"internal/data/example/ssl"` | 配置文件server.key在vault仓库中存放路径 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-abc.txt" | string | `"{{- with secret \"internal/data/example/ssl\" -}}\n{{ .Data.data.certificatePassword }}\n{{- end }}\n"` | 配置文件abc.txt渲染模版,默认为vault中存放原文格式 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-dhparam.pem" | string | `"{{- with secret \"internal/data/example/ssl\" -}}\n{{ .Data.data.dhparamPem }}\n{{- end }}\n"` | 配置文件dhparam.pem渲染模版,默认为vault中存放原文格式 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.crt" | string | `"{{- with secret \"internal/data/example/ssl\" -}}\n{{ .Data.data.ServerCrt }}\n{{- end }}\n"` | 配置文件server.crt渲染模版,默认为vault中存放原文格式 |
| podAnnotations."vault.hashicorp.com/agent-inject-template-server.key" | string | `"{{- with secret \"internal/data/example/ssl\" -}}\n{{ .Data.data.ServerKey }}\n{{- end }}\n"` | 配置文件server.key渲染模版,默认为vault中存放原文格式 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | vault agent是否作为init容器 |
| podAnnotations."vault.hashicorp.com/agent-run-as-group" | string | `"1000"` | vault agent容器运行用户组id |
| podAnnotations."vault.hashicorp.com/agent-run-as-user" | string | `"1000"` | vault agent容器运行用户id |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | vault agent挂载的sa资源名 |
| podAnnotations."vault.hashicorp.com/log-level" | string | `"warn"` | 设置vault agent容器日志等级 |
| podAnnotations."vault.hashicorp.com/role" | string | `"website"` | vault权限角色 |
| podAnnotations."vault.hashicorp.com/secret-volume-path" | string | `"/etc/nginx/cert/"` | 配置文件挂载目录 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | vault agent和vault server通信是否跳过tls验证,默认为true |
| podLabels.app | string | `"website"` | WEB容器标签 |
| readinessProbe.failureThreshold | int | `3` | 失败重试次数 |
| readinessProbe.httpGet.httpHeaders[0] | object | `{"name":"Host","value":"example.com"}` | 自定义的 HTTP 头 |
| readinessProbe.httpGet.httpHeaders[0].value | string | `"example.com"` | 自定义的 HTTP 请求头内容 |
| readinessProbe.httpGet.path | string | `"/"` | 访问 HTTP 服务的路径 |
| readinessProbe.httpGet.port | int | `8080` | 容器的端口号 |
| readinessProbe.httpGet.scheme | string | `"HTTPS"` | 协议 |
| readinessProbe.initialDelaySeconds | int | `5` | 启动探测时间 |
| readinessProbe.periodSeconds | int | `20` | 执行探测的时间间隔 |
| readinessProbe.successThreshold | int | `1` | 成功探测次数 |
| readinessProbe.timeoutSeconds | int | `5` | 探测超时等待时间 |
| replicaCount | int | `1` | 容器部署副本数 |
| resources.limits.cpu | int | `1` | 容器运行限制CPU资源 |
| resources.limits.memory | string | `"1Gi"` | 容器运行限制内存资源 |
| resources.requests.cpu | int | `1` | 容器运行所需CPU资源，最小值为1 |
| resources.requests.memory | string | `"1Gi"` | 容器运行所需内存资源，最小值为1Gi |
| secret.ca_crt_key | string | `"tls.cert"` | secret中创建的key,格式为[secret key]: [vault key] |
| secret.enable | bool | `true` | secret启用标签,如果启用ingress,则需要启用 |
| secret.name | string | `"test-tls"` | secret资源名 |
| secret.path | string | `"secrets/data/example/domain-tls"` | secret资源在vault中存放路径 |
| secret.tls_crt_key | string | `"tls.cert"` | secret中创建的key,格式为[secret key]: [vault key] |
| secret.tls_key_key | string | `"tls.key"` | secret中创建的key,格式为[secret key]: [vault key] |
| service.port | int | `8080` | 服务暴露端口,默认和targetPort保持一致 |
| service.portName | string | `"tls-1"` | 服务暴露端口名称,启用istio后,名称需要包含tls |
| service.targetPort | int | `8080` | 服务暴露端口 |
| service.type | string | `"ClusterIP"` | 服务类型:ClusterIP/NodePort/LoadBalancer,默认使用ClusterIP |
| serviceAccount.automount | bool | `false` | serviceaccount是否挂载进容器,默认取消挂载 |
| serviceAccount.create | bool | `true` | 是否创建sa |
| serviceAccount.name | string | `"website"` | serviceaccount名称 |
## 变更历史

## 1.0.0 - 2025-11-26

### 说明
- 初始版本发布