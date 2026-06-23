# forum-reply-robot `.ai-flow/deploy/test-sync/`

把 **test 环境真实部署形态**同步成**预览形态**,在独立预览集群里把改动子仓跑起来。
由 `gen-preview-hook.sh` 生成,详见上级 `../README.md` 的 Provenance + 6 坑。

## test → preview 改造点

| 维度      | test 环境              | 预览环境                                                              |
| --------- | ---------------------- | --------------------------------------------------------------------- |
| 集群      | infra-test-*           | `infra-hk-preview-cluster-003`(services/<svc>.yaml preview.cluster)             |
| namespace | service.md 固定值      | 服务专属 `community-robots`                                              |
| 配置来源  | Vault Agent sidecar    | runner userpass 读 Vault → 烘 k8s Secret 挂 `/vault/secrets/`         |
| DB        | 华为云托管 PostgreSQL       | 命名空间内底座 postgresql(`postgresql-service.community-robots.svc`)              |
| 域名      | `*.test.osinfra.cn`    | `*.preview.test.osinfra.cn`                                                 |
| 镜像/代码 | SWR 真实镜像           | runtime-clone:现拉 issue 分支源码跑,挂真实 Vault 配置                 |

## 待补全(生成后)

- `sync.sh` 里 `mapping = {}`:填本服务 Vault data 的 key→文件名(第一次跑看日志 `vault data keys:`)
- `sync.sh` 里 DB 块字段名(若不是 `DB.{HOST,PORT,USER,PASSWORD,NAME}` 结构)
- 非 Django 子仓:改 Deployment 的 image + 启动命令
