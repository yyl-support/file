# forum-reply-robot `.ai-flow/deploy/`

backlog Workflow Develop 第一段(preview)调用本仓 `preview.sh` 起**独立预览环境**。

> 本目录由 [`backlog/.ai-flow/scripts/gen-preview-hook.sh`](https://github.com/opensourceways/backlog/blob/main/.ai-flow/scripts/gen-preview-hook.sh) 生成,
> 模板 = [meeting-server `.ai-flow/deploy/`](https://github.com/opensourceways/meeting-server/tree/main/.ai-flow/deploy)(实测跑通)。
> **生成后需补全的 TODO**:`services.yaml` 的 sub 拓扑 / 底座库名;`test-sync/sync.sh` 里
> Vault key→文件名映射 + DB 块字段 + 非 Django 形态的 image/启动命令。

## 文件

| 文件                  | 干啥                                                                       |
| --------------------- | -------------------------------------------------------------------------- |
| `preview.sh`          | 验权 → 建 ns → 底座 PostgreSQL → 算改动子仓 → 调 sync.sh → 调 routes.sh → 网络诊断 |
| `services.yaml`       | 业务拓扑 + 底座 + test 归档坐标                                             |
| `test-sync/sync.sh`   | 单子仓:service.md 查 vault → 读 Vault → 改预览形态 → 烘 Secret → runtime-clone |
| `test-sync/routes.sh` | 同步 test ingress 路由拓扑成预览(共享 host)                                |

## Provenance(预览形态从哪来)

1. **`opensourceways/infra-common/service.md`**:按 `(子仓名, test, 社区)` 查 Vault path / 归档路径 / test ns
2. **Vault**(`vault.preview.test.osinfra.cn`):runner **userpass** 登录(backlog secret `VAULT_USERNAME/PASSWORD`),
   读真实 config(**不用 Vault Agent Injector**,改为烘 k8s Secret 挂 `/vault/secrets/`)
3. **test 归档仓**(`services.yaml test_archive`):routes.sh 拉各 sub ingress.yaml 改成预览路由

## config 改造规则(test → preview)

- **DB 块**(`secrets.yaml`):`HOST`→`postgresql-service.<ns>.svc.cluster.local`、`PORT`→5432、
  `USER`→postgres、`PASSWORD`→底座密码、`NAME`→底座库名(下划线;只改 host 不够)
- **app config**:`DEBUG=true`(跳 TLS PEM)、`IS_DELETE_CONFIG=false`(只读 Secret 删文件会 OSError)
- **域名**:`.test.osinfra.cn` → `.preview.test.osinfra.cn`

## 6 个坑

1. **Vault 403**:login 200 但 read 403 = policy 没授权读 `internal/data/infra-test/<svc>`,找 ops
2. **老 pod 不更新**:Secret 变了 Deployment 没变 → apply no-op → 必须 `kubectl rollout restart`
3. **nginx 正则 path 被拒**:`pathType: ImplementationSpecific` + 注解 `use-regex: "true"`
4. **DB 连不上**:host/port/user/password/name **全套**改写;`set -u` 下 `PG_PWD` 等变量要有默认值
5. **OSError: Read-only file system /vault/secrets/config**:`IS_DELETE_CONFIG=false`
6. **1049 Unknown database**:`DB.NAME` 改成底座库名(连字符 vs 下划线)

## 排障对照

- nginx 404(`<center>nginx</center>`) = 请求没到 pod(路由没建成);查 `kubectl get ingress`
- 503 = 路由 OK 但 pod 没 ready(CrashLoop);查 `kubectl logs`
- Django 404(`<!DOCTYPE html>`) = 到了 pod、app 在跑,只是该 path 没注册(正常)
- pod 连底座超时:查 `kubectl get endpoints/networkpolicy`、`kubectl get peerauthentication -A`、busybox nc 测端口
