# hotopic

![Version: 1.0.0](https://img.shields.io/badge/Version-1.0.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 1.0.0](https://img.shields.io/badge/AppVersion-1.0.0-informational?style=flat-square)

## 📖 服务介绍 (Service Overview)
A Helm chart for hotopic

### 依赖
1. Kubernetes 1.21+
2. Helm 3.12.0+

### 核心功能
* 采集社区各个消息源的数据，进行过滤清洗总结，包括论坛、git、邮件列表等。
* 根据余弦相似度和图聚类方法，通过AI大模型帮助，得出最终的话题集。
* 提供评审界面给运营人员，方便快捷的操作热点话题。
### 底层组件
该服务在启动和运行过程中依赖：
* **Database**： postgresql，mongodb
### 维护者

| 名称       | 邮箱                | Github ID    |
|----------|-------------------|--------------|
| Hourunze | 1043170898@qq.com | Hourunze1997 |
| XuGuangyue | 2571374157@qq.com    | 123-prog      |

### Helm chart values说明
| Key | Type | Default | Description |
|-----|------|---------|-------------|
| backendServer.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/hotopic-website-backend-test"` | 镜像名 |
| backendServer.image.tag | string | `"hrz-0902-f7228d"` | 镜像Tag |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-perms-conf.yaml" | string | `"0400"` | 配置文件属性 |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-perms-mongo.crt" | string | `"0400"` | 证书文件属性 |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` | 配置文件在vault中存放路径 |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-secret-mongo.crt" | string | `"internal/data/infra-test/community-hot-topic"` | 证书文件在vault中存放路径 |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.server }}\n{{- end }}\n"` | 配置文件渲染模版 |
| backendServer.podAnnotations."vault.hashicorp.com/agent-inject-template-mongo.crt" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mongoCrt }}\n{{- end }}\n"` | 证书文件渲染模版 |
| backendServer.pvcName | string | `"hotopic-server-data"` | pvc名称 |
| host | string | `"hotopic-data.test.osinfra.cn"` | 域名 |
| hotopic.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/hotopic-data-clean-test"` | 镜像名 |
| hotopic.resources.limits.cpu | string | `"300m"` | 容器运行限制CPU资源 |
| hotopic.resources.limits.memory | string | `"500Mi"` | 容器运行限制内存资源 |
| hotopic.resources.requests.cpu | string | `"300m"` | 容器运行最少所需CPU资源 |
| hotopic.resources.requests.memory | string | `"500Mi"` | 容器运行最少所需内存资源 |
| hotopics[0].community | string | `"cann"` | 社区名 |
| hotopics[0].deploymentLabels | object | `{}` | deployment标签 |
| hotopics[0].imageTag | string | `"hrz_vllm-e42a0f"` | 镜像Tag |
| hotopics[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` | 配置文件在vault中存放路径 |
| hotopics[0].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.cannConfig }}\n{{- end }}\n"` | 配置文件渲染模版 |
| hotopics[0].podLabels.app | string | `"cann-hotopic-data-clean"` | pod标签 |
| hotopics[10].community | string | `"unifiedbus"` |  |
| hotopics[10].deploymentLabels | object | `{}` |  |
| hotopics[10].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[10].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[10].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.unifiedbusConfig }}\n{{- end }}\n"` |  |
| hotopics[10].podLabels.app | string | `"unifiedbus-hotopic-data-clean"` |  |
| hotopics[11].community | string | `"vllm"` |  |
| hotopics[11].deploymentLabels | object | `{}` |  |
| hotopics[11].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[11].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[11].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.vllmConfig }}\n{{- end }}\n"` |  |
| hotopics[11].podLabels.app | string | `"vllm-hotopic-data-clean"` |  |
| hotopics[12].community | string | `"mindspeed"` |  |
| hotopics[12].deploymentLabels | object | `{}` |  |
| hotopics[12].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[12].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[12].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindspeedConfig }}\n{{- end }}\n"` |  |
| hotopics[12].podLabels.app | string | `"mindspeed-hotopic-data-clean"` |  |
| hotopics[13].community | string | `"pytorch"` |  |
| hotopics[13].deploymentLabels | object | `{}` |  |
| hotopics[13].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[13].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[13].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.pytorchConfig }}\n{{- end }}\n"` |  |
| hotopics[13].podLabels.app | string | `"pytorch-hotopic-data-clean"` |  |
| hotopics[14].community | string | `"triton"` |  |
| hotopics[14].deploymentLabels | object | `{}` |  |
| hotopics[14].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[14].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[14].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.tritonConfig }}\n{{- end }}\n"` |  |
| hotopics[14].podLabels.app | string | `"triton-hotopic-data-clean"` |  |
| hotopics[15].community | string | `"sgl"` |  |
| hotopics[15].deploymentLabels | object | `{}` |  |
| hotopics[15].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[15].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[15].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.sglangConfig }}\n{{- end }}\n"` |  |
| hotopics[15].podLabels.app | string | `"sglang-hotopic-data-clean"` |  |
| hotopics[16].community | string | `"tilelang"` |  |
| hotopics[16].deploymentLabels | object | `{}` |  |
| hotopics[16].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[16].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[16].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.tilelangConfig }}\n{{- end }}\n"` |  |
| hotopics[16].podLabels.app | string | `"tilelang-hotopic-data-clean"` |  |
| hotopics[17].community | string | `"verl"` |  |
| hotopics[17].deploymentLabels | object | `{}` |  |
| hotopics[17].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[17].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[17].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.verlConfig }}\n{{- end }}\n"` |  |
| hotopics[17].podLabels.app | string | `"verl-hotopic-data-clean"` |  |
| hotopics[18].community | string | `"ascendnpuir"` |  |
| hotopics[18].deploymentLabels | object | `{}` |  |
| hotopics[18].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[18].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[18].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.ascendnpuirConfig }}\n{{- end }}\n"` |  |
| hotopics[18].podLabels.app | string | `"ascendnpuir-hotopic-data-clean"` |  |
| hotopics[19].community | string | `"openfuyao"` |  |
| hotopics[19].deploymentLabels | object | `{}` |  |
| hotopics[19].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[19].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[19].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openfuyaoConfig }}\n{{- end }}\n"` |  |
| hotopics[19].podLabels.app | string | `"openfuyao-hotopic-data-clean"` |  |
| hotopics[1].community | string | `"mindcluster"` |  |
| hotopics[1].deploymentLabels | object | `{}` |  |
| hotopics[1].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[1].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[1].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindclusterConfig }}\n{{- end }}\n"` |  |
| hotopics[1].podLabels.app | string | `"mindcluster-hotopic-data-clean"` |  |
| hotopics[20].community | string | `"cannopen"` |  |
| hotopics[20].deploymentLabels | object | `{}` |  |
| hotopics[20].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[20].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[20].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.cannopenConfig }}\n{{- end }}\n"` |  |
| hotopics[20].podLabels.app | string | `"cannopen-hotopic-data-clean"` |  |
| hotopics[2].community | string | `"mindie"` |  |
| hotopics[2].deploymentLabels | object | `{}` |  |
| hotopics[2].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[2].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[2].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindieConfig }}\n{{- end }}\n"` |  |
| hotopics[2].podLabels.app | string | `"mindie-hotopic-data-clean"` |  |
| hotopics[3].community | string | `"mindsdk"` |  |
| hotopics[3].deploymentLabels | object | `{}` |  |
| hotopics[3].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[3].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[3].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindsdkConfig }}\n{{- end }}\n"` |  |
| hotopics[3].podLabels.app | string | `"mindsdk-hotopic-data-clean"` |  |
| hotopics[4].community | string | `"mindspore"` |  |
| hotopics[4].deploymentLabels | object | `{}` |  |
| hotopics[4].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[4].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[4].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindsporeConfig }}\n{{- end }}\n"` |  |
| hotopics[4].podLabels.app | string | `"mindspore-hotopic-data-clean"` |  |
| hotopics[5].community | string | `"mindstudio"` |  |
| hotopics[5].deploymentLabels | object | `{}` |  |
| hotopics[5].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[5].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[5].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindstudioConfig }}\n{{- end }}\n"` |  |
| hotopics[5].podLabels.app | string | `"mindstudio-hotopic-data-clean"` |  |
| hotopics[6].community | string | `"openeuler"` |  |
| hotopics[6].deploymentLabels | object | `{}` |  |
| hotopics[6].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[6].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[6].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openeulerConfig }}\n{{- end }}\n"` |  |
| hotopics[6].podLabels.app | string | `"openeuler-hotopic-data-clean"` |  |
| hotopics[7].community | string | `"opengauss"` |  |
| hotopics[7].deploymentLabels | object | `{}` |  |
| hotopics[7].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[7].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[7].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.opengaussConfig }}\n{{- end }}\n"` |  |
| hotopics[7].podLabels.app | string | `"opengauss-hotopic-data-clean"` |  |
| hotopics[8].community | string | `"openubmc"` |  |
| hotopics[8].deploymentLabels | object | `{}` |  |
| hotopics[8].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[8].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[8].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openubmcConfig }}\n{{- end }}\n"` |  |
| hotopics[8].podLabels.app | string | `"openubmc-hotopic-data-clean"` |  |
| hotopics[9].community | string | `"pta"` |  |
| hotopics[9].deploymentLabels | object | `{}` |  |
| hotopics[9].imageTag | string | `"hrz_vllm-e42a0f"` |  |
| hotopics[9].podAnnotations."vault.hashicorp.com/agent-inject-secret-conf.yaml" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| hotopics[9].podAnnotations."vault.hashicorp.com/agent-inject-template-conf.yaml" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.ptaConfig }}\n{{- end }}\n"` |  |
| hotopics[9].podLabels.app | string | `"pta-hotopic-data-clean"` |  |
| imagePullSecret | string | `"huawei-swr-image-pull-secret"` | 镜像仓访问凭证名称 |
| mining.image.repository | string | `"swr.cn-north-4.myhuaweicloud.com/opensourceway/hotopic-mining-test"` | 镜像名 |
| mining.resources.limits.cpu | string | `"300m"` |  |
| mining.resources.limits.memory | string | `"800Mi"` |  |
| mining.resources.requests.cpu | string | `"300m"` |  |
| mining.resources.requests.memory | string | `"800Mi"` |  |
| minings[0].community | string | `"cann"` | 社区名 |
| minings[0].configMapName | string | `"cann-mining-config"` | configmap名称 |
| minings[0].deploymentLabels | object | `{}` | deployment标签 |
| minings[0].imageTag | string | `"main-1fab98"` | 镜像tag |
| minings[0].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` | 配置文件在vault中存放路径 |
| minings[0].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.cannMining }}\n{{- end }}\n"` | 配置文件渲染模版 |
| minings[0].podLabels.app | string | `"cann-hotopic-mining"` | pod标签 |
| minings[0].pvc.name | string | `"cann-hotopic-mining-data"` | pvc名称 |
| minings[10].community | string | `"unifiedbus"` |  |
| minings[10].configMapName | string | `"unifiedbus-mining-config"` |  |
| minings[10].deploymentLabels | object | `{}` |  |
| minings[10].imageTag | string | `"main-1fab98"` |  |
| minings[10].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[10].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.unifiedbusMining }}\n{{- end }}\n"` |  |
| minings[10].podLabels.app | string | `"unifiedbus-hotopic-mining"` |  |
| minings[10].pvc.name | string | `"unifiedbus-hotopic-mining-data"` |  |
| minings[11].community | string | `"vllm"` |  |
| minings[11].configMapName | string | `"vllm-mining-config"` |  |
| minings[11].deploymentLabels | object | `{}` |  |
| minings[11].imageTag | string | `"main-1fab98"` |  |
| minings[11].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[11].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.vllmMining }}\n{{- end }}\n"` |  |
| minings[11].podLabels.app | string | `"vllm-hotopic-mining"` |  |
| minings[11].pvc.name | string | `"vllm-hotopic-mining-data"` |  |
| minings[12].community | string | `"mindspeed"` |  |
| minings[12].configMapName | string | `"mindspeed-mining-config"` |  |
| minings[12].deploymentLabels | object | `{}` |  |
| minings[12].imageTag | string | `"main-1fab98"` |  |
| minings[12].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[12].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindspeedMining }}\n{{- end }}\n"` |  |
| minings[12].podLabels.app | string | `"mindspeed-hotopic-mining"` |  |
| minings[12].pvc.name | string | `"mindspeed-hotopic-mining-data"` |  |
| minings[13].community | string | `"pytorch"` |  |
| minings[13].configMapName | string | `"pytorch-mining-config"` |  |
| minings[13].deploymentLabels | object | `{}` |  |
| minings[13].imageTag | string | `"main-1fab98"` |  |
| minings[13].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[13].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.pytorchMining }}\n{{- end }}\n"` |  |
| minings[13].podLabels.app | string | `"pytorch-hotopic-mining"` |  |
| minings[13].pvc.name | string | `"pytorch-hotopic-mining-data"` |  |
| minings[14].community | string | `"triton"` |  |
| minings[14].configMapName | string | `"triton-mining-config"` |  |
| minings[14].deploymentLabels | object | `{}` |  |
| minings[14].imageTag | string | `"main-1fab98"` |  |
| minings[14].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[14].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.tritonMining }}\n{{- end }}\n"` |  |
| minings[14].podLabels.app | string | `"triton-hotopic-mining"` |  |
| minings[14].pvc.name | string | `"triton-hotopic-mining-data"` |  |
| minings[15].community | string | `"sglang"` |  |
| minings[15].configMapName | string | `"sglang-mining-config"` |  |
| minings[15].deploymentLabels | object | `{}` |  |
| minings[15].imageTag | string | `"main-1fab98"` |  |
| minings[15].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[15].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.sglangMining }}\n{{- end }}\n"` |  |
| minings[15].podLabels.app | string | `"sglang-hotopic-mining"` |  |
| minings[15].pvc.name | string | `"sglang-hotopic-mining-data"` |  |
| minings[16].community | string | `"ascendnpuir"` |  |
| minings[16].configMapName | string | `"ascendnpuir-mining-config"` |  |
| minings[16].deploymentLabels | object | `{}` |  |
| minings[16].imageTag | string | `"main-1fab98"` |  |
| minings[16].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[16].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.ascendnpuirMining }}\n{{- end }}\n"` |  |
| minings[16].podLabels.app | string | `"ascendnpuir-hotopic-mining"` |  |
| minings[16].pvc.name | string | `"ascendnpuir-hotopic-mining-data"` |  |
| minings[17].community | string | `"openfuyao"` |  |
| minings[17].configMapName | string | `"openfuyao-mining-config"` |  |
| minings[17].deploymentLabels | object | `{}` |  |
| minings[17].imageTag | string | `"main-1fab98"` |  |
| minings[17].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[17].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openfuyaoMining }}\n{{- end }}\n"` |  |
| minings[17].podLabels.app | string | `"openfuyao-hotopic-mining"` |  |
| minings[17].pvc.name | string | `"openfuyao-hotopic-mining-data"` |  |
| minings[18].community | string | `"tilelang"` |  |
| minings[18].configMapName | string | `"tilelang-mining-config"` |  |
| minings[18].deploymentLabels | object | `{}` |  |
| minings[18].imageTag | string | `"main-1fab98"` |  |
| minings[18].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[18].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.tilelangMining }}\n{{- end }}\n"` |  |
| minings[18].podLabels.app | string | `"tilelang-hotopic-mining"` |  |
| minings[18].pvc.name | string | `"tilelang-hotopic-mining-data"` |  |
| minings[19].community | string | `"verl"` |  |
| minings[19].configMapName | string | `"verl-mining-config"` |  |
| minings[19].deploymentLabels | object | `{}` |  |
| minings[19].imageTag | string | `"main-1fab98"` |  |
| minings[19].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[19].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.verlMining }}\n{{- end }}\n"` |  |
| minings[19].podLabels.app | string | `"verl-hotopic-mining"` |  |
| minings[19].pvc.name | string | `"verl-hotopic-mining-data"` |  |
| minings[1].community | string | `"mindcluster"` |  |
| minings[1].configMapName | string | `"mindcluster-mining-config"` |  |
| minings[1].deploymentLabels | object | `{}` |  |
| minings[1].imageTag | string | `"main-1fab98"` |  |
| minings[1].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[1].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindclusterMining }}\n{{- end }}\n"` |  |
| minings[1].podLabels.app | string | `"mindcluster-hotopic-mining"` |  |
| minings[1].pvc.name | string | `"mindcluster-hotopic-mining-data"` |  |
| minings[20].community | string | `"cannopen"` |  |
| minings[20].configMapName | string | `"cannopen-mining-config"` |  |
| minings[20].deploymentLabels | object | `{}` |  |
| minings[20].imageTag | string | `"main-1fab98"` |  |
| minings[20].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[20].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.cannopenMining }}\n{{- end }}\n"` |  |
| minings[20].podLabels.app | string | `"cannopen-hotopic-mining"` |  |
| minings[20].pvc.name | string | `"cannopen-hotopic-mining-data"` |  |
| minings[2].community | string | `"mindie"` |  |
| minings[2].configMapName | string | `"mindie-mining-config"` |  |
| minings[2].deploymentLabels | object | `{}` |  |
| minings[2].imageTag | string | `"main-1fab98"` |  |
| minings[2].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[2].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindieMining }}\n{{- end }}\n"` |  |
| minings[2].podLabels.app | string | `"mindie-hotopic-mining"` |  |
| minings[2].pvc.name | string | `"mindie-hotopic-mining-data"` |  |
| minings[3].community | string | `"mindsdk"` |  |
| minings[3].configMapName | string | `"mindsdk-mining-config"` |  |
| minings[3].deploymentLabels | object | `{}` |  |
| minings[3].imageTag | string | `"main-d9910f"` |  |
| minings[3].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[3].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindsdkMining }}\n{{- end }}\n"` |  |
| minings[3].podLabels.app | string | `"mindsdk-hotopic-mining"` |  |
| minings[3].pvc.name | string | `"mindsdk-hotopic-mining-data"` |  |
| minings[4].community | string | `"mindspore"` |  |
| minings[4].configMapName | string | `"mindspore-mining-config"` |  |
| minings[4].deploymentLabels | object | `{}` |  |
| minings[4].imageTag | string | `"main-1fab98"` |  |
| minings[4].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[4].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindsporeMining }}\n{{- end }}\n"` |  |
| minings[4].podLabels.app | string | `"mindspore-hotopic-mining"` |  |
| minings[4].pvc.name | string | `"mindspore-hotopic-mining-data"` |  |
| minings[5].community | string | `"mindstudio"` |  |
| minings[5].configMapName | string | `"mindstudio-mining-config"` |  |
| minings[5].deploymentLabels | object | `{}` |  |
| minings[5].imageTag | string | `"main-d9910f"` |  |
| minings[5].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[5].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.mindstudioMining }}\n{{- end }}\n"` |  |
| minings[5].podLabels.app | string | `"mindstudio-hotopic-mining"` |  |
| minings[5].pvc.name | string | `"mindstudio-hotopic-mining-data"` |  |
| minings[6].community | string | `"openeuler"` |  |
| minings[6].configMapName | string | `"openeuler-mining-config"` |  |
| minings[6].deploymentLabels | object | `{}` |  |
| minings[6].imageTag | string | `"main-1fab98"` |  |
| minings[6].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[6].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openeulerMining }}\n{{- end }}\n"` |  |
| minings[6].podLabels.app | string | `"openeuler-hotopic-mining"` |  |
| minings[6].pvc.name | string | `"openeuler-hotopic-mining-data"` |  |
| minings[7].community | string | `"opengauss"` |  |
| minings[7].configMapName | string | `"opengauss-mining-config"` |  |
| minings[7].deploymentLabels | object | `{}` |  |
| minings[7].imageTag | string | `"main-1fab98"` |  |
| minings[7].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[7].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.opengaussMining }}\n{{- end }}\n"` |  |
| minings[7].podLabels.app | string | `"opengauss-hotopic-mining"` |  |
| minings[7].pvc.name | string | `"opengauss-hotopic-mining-data"` |  |
| minings[8].community | string | `"openubmc"` |  |
| minings[8].configMapName | string | `"openubmc-mining-config"` |  |
| minings[8].deploymentLabels | object | `{}` |  |
| minings[8].imageTag | string | `"main-1fab98"` |  |
| minings[8].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[8].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.openubmcMining }}\n{{- end }}\n"` |  |
| minings[8].podLabels.app | string | `"openubmc-hotopic-mining"` |  |
| minings[8].pvc.name | string | `"openubmc-hotopic-mining-data"` |  |
| minings[9].community | string | `"pta"` |  |
| minings[9].configMapName | string | `"pta-mining-config"` |  |
| minings[9].deploymentLabels | object | `{}` |  |
| minings[9].imageTag | string | `"main-d9910f"` |  |
| minings[9].podAnnotations."vault.hashicorp.com/agent-inject-secret-config.ini" | string | `"internal/data/infra-test/community-hot-topic"` |  |
| minings[9].podAnnotations."vault.hashicorp.com/agent-inject-template-config.ini" | string | `"{{- with secret \"internal/data/infra-test/community-hot-topic\" -}}  \n{{ .Data.data.ptaMining }}\n{{- end }}\n"` |  |
| minings[9].podLabels.app | string | `"pta-hotopic-mining"` |  |
| minings[9].pvc.name | string | `"pta-hotopic-mining-data"` |  |
| namespace | string | `"community-hot-topic"` | 命名空间名称 |
| podAnnotations."vault.hashicorp.com/agent-inject" | string | `"true"` | 是否注入vault agent容器 |
| podAnnotations."vault.hashicorp.com/agent-pre-populate-only" | string | `"true"` | agent容器是否作为初始化容器 |
| podAnnotations."vault.hashicorp.com/agent-service-account-token-volume-name" | string | `"token-vol"` | sa token的卷名 |
| podAnnotations."vault.hashicorp.com/role" | string | `"community-hot-topic"` | vault权限角色 |
| podAnnotations."vault.hashicorp.com/tls-skip-verify" | string | `"true"` | agent与server通信是否跳过验证 |
| secrets.keysMap."ca.crt" | string | `"tls.cert"` | 对应在vault中的键名 |
| secrets.keysMap."tls.crt" | string | `"tls.cert"` | 对应在vault中的键名 |
| secrets.keysMap."tls.key" | string | `"tls.key"` | 对应在vault中的键名 |
| secrets.path | string | `"secrets/data/infra-test/domain-tls"` | 在vault中存放的路径 |
| serviceAccount.name | string | `"community-hot-topic"` | sa名称 |

## 变更历史

## 1.0.0 - 2025-10-28

### 说明
- 初始版本发布