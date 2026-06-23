**统一账号服务**
# values配置介绍
```
global:
  namespace: 命名空间
  appName: 应用名
  appSubName: 服务名
replicaCount: 副本个数
revisionHistoryLimitCount: 历史版本留存限制
image:
  repository: 镜像仓地址
  tag: 镜像版本
  pullPolicy: 拉取策略
  pullSecret: 下载秘钥
containers:
  applicationPath: 应用的配置文件地址
  containerPort: 端口
  portsName: 端口名
resources:
  limits:
    cpu: CPU
    memory: 运行内存
  requests:
    cpu: CPU
    memory: 运行内存
probeHttpGet:
  path: 服务状态检测接口
  port: 检测端口
  scheme: HTTPS
vault:
  runAsUser: 运行的用户
ingress:
  enabled: 使能
  className: 对象名
  host: 对外的域名
  backendProtocol: "HTTPS"
  limitConnections: 最大连接数
  limitRPS: 每秒请求数
  port: 对外端口
service:
  type: ClusterIP
  port: 对外端口
  targetPort: 目标端口
secret:
  ca_crt_path: 证书地址
  ca_crt_key: 证书文件
  tls_crt_path: 证书地址
  tls_crt_key: 证书文件
  tls_key_path: 证书地址
  tls_key_key: 证书文件
```