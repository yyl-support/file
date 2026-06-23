# forum-reply-robot 账号接入分析

## 项目概述

forum-reply-robot 是一个自动监控论坛新帖子并智能回复的机器人系统，基于 Discourse 论坛 API + AI 大模型 + LightRAG 检索 + PostgreSQL 数据库构建。

## 账号接入方式总览

| 服务 | 认证方式 | 配置位置 | 代码位置 |
|------|---------|---------|---------|
| Discourse 论坛（回复） | HTTP Header: `Api-Key` + `Api-Username` | `config['posts']` | `forum_client.py:43-46` |
| Discourse 论坛（读取） | 无需认证（公开 API） | `config['forum']` | `data_processor.py:87` |
| AI 大模型（SiliconFlow） | OpenAI SDK: `api_key` | `config['api']` | `ai_processor.py:12-15` |
| PostgreSQL 数据库 | psycopg2: `user` + `password` + `sslmode` | `config['database']` | `data_processor.py:428-435` |
| 搜索服务 | HTTP Header: `source` + `referer` | `config['search']` | `forum_client.py:98-99` |
| LightRAG 检索服务 | 无显式认证（内部服务） | `config['retrieval']` | `forum_client.py:169-172` |

## 详细分析

### 1. Discourse 论坛接入

#### 回复接口（需认证）

```python
# forum_client.py:43-46
headers = {
    "Content-Type": "application/json",
    "Api-Key": self.config['posts']['api_key'],
    "Api-Username": self.config['posts']['api_username']
}
response = requests.post(
    f"{self.config['posts']['base_url']}/posts.json",
    headers=headers,
    data=json.dumps(payload),
    verify=verify_ssl,
    timeout=30
)
```

Discourse 论坛使用 **API Key + API Username** 的 Header 方式认证，这是 Discourse 官方推荐的管理员 API 接入方式。API Key 在 Discourse 后台管理面板生成，可设置不同的权限级别。

#### 读取接口（无需认证）

```python
# data_processor.py:87
response = requests.get(url, verify=verify_ssl, timeout=30)
```

读取帖子详情使用公开 REST API（`/t/{topic_id}.json`），不携带任何认证信息。

### 2. AI 大模型接入

```python
# ai_processor.py:12-15
self.client = OpenAI(
    base_url=config['api']['base_url'],      # https://api.siliconflow.cn/v1
    api_key=config['api']['api_key']
)
```

使用 OpenAI Python SDK 的兼容模式接入 SiliconFlow 平台，认证方式为标准 Bearer Token（SDK 内部自动添加 `Authorization: Bearer <api_key>`）。

涉及的大模型调用场景：
- 生成摘要（`summarize_text`）
- 提示词注入检测（`check_prompt_injection`）
- 答案相关性检查（`check_answer_relevance`）
- 答案质量检查（`check_answer_quality`）
- 生成回答（`call_large_model`）
- 总结答案（`summarize_answer`）

### 3. PostgreSQL 数据库接入

```python
# data_processor.py:428-435
db_params = {
    'host': self.config['database']['host'],
    'port': self.config['database']['port'],
    'database': self.config['database']['database'],
    'user': self.config['database']['user'],
    'password': self.config['database']['password'],
    'sslmode': self.config['database']['sslmode']
}
conn = psycopg2.connect(**db_params)
```

使用 psycopg2 标准用户名/密码认证，支持 SSL 连接模式（`sslmode`），连接按需建立并有指数退避重试机制。

### 4. 搜索服务接入

```python
# forum_client.py:98-99
headers = {
    "source": self.config['search']['source'],
    "referer": self.config['search']['referer']
}
```

搜索服务通过自定义 Header（`source` + `referer`）进行轻量级来源认证，无 API Key 机制。

### 5. LightRAG 检索服务接入

```python
# forum_client.py:169-172
base_url = self.config['retrieval']['base_url']
endpoint = self.config['retrieval']['query_endpoint']
url = f"{base_url}{endpoint}"
response = requests.post(url, json=payload, verify=verify_ssl, timeout=600)
```

LightRAG 为内部微服务，通过 JSON POST 请求调用，无显式认证机制，依赖网络隔离保障安全。

## 凭证安全保护机制

### 配置集中管理

所有凭证集中在 `config/config.yaml`，统一由 `src/utils.py:load_config()` 加载：

```yaml
api:
  base_url: 'https://api.siliconflow.cn/v1'
  api_key: '**********'
  model_name: 'Qwen/Qwen3-235B-A22B-Instruct-2507'
```

### 防泄露措施

| 措施 | 代码/配置位置 | 说明 |
|------|-------------|------|
| `.gitignore` 排除 config | `.gitignore:33-34` | 防止配置文件提交到 Git |
| 启动后删除配置文件 | `main.py:260` `delete_config_file()` | 防止敏感信息落盘 |
| Docker 文件权限 | `Dockerfile:95-102` | config 目录 `700`，文件 `600` |
| 非 root 用户运行 | `Dockerfile:105` `USER appuser` | 限制文件访问权限 |
| umask 设置 | `Dockerfile:17` | `umask 0027` 防止新文件过度开放 |
| 历史记录禁用 | `Dockerfile:19` | `set +o history` 防止命令历史泄露 |
| 编译器/调试器移除 | `Dockerfile:35-61` | 删除 gcc/pdb 等防止容器内调试 |

### 配置文件生命周期

```
Docker 构建时 → COPY config.yaml → chmod 600 → 
运行时 → load_config() → 读取到内存 → delete_config_file() → 文件删除
```

配置文件仅在启动瞬间存在于磁盘，加载到内存后立即删除，后续所有凭证引用均来自内存中的 `self.config` 字典。

## 认证流程图

```
┌─────────────────────────────────────────────────────────┐
│                    config/config.yaml                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ api_key  │ │ api_key  │ │ user/pwd │ │ api_key  │   │
│  │ (AI模型) │ │ (论坛)   │ │ (数据库) │ │ (搜索)   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │ load_config()
                       ▼
              ┌────────────────┐
              │  内存 config    │──── delete_config_file()
              │    字典对象     │     (删除磁盘文件)
              └────────┬───────┘
                       │
         ┌─────────────┼─────────────┬──────────────┐
         ▼             ▼             ▼              ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │OpenAI   │  │Discourse│  │psycopg2 │  │Search   │
    │Client   │  │Headers  │  │Connect  │  │Headers  │
    │(Bearer) │  │(Api-Key)│  │(user/pwd│  │(source) │
    └─────────┘  └─────────┘  └─────────┘  └─────────┘
         │             │             │              │
         ▼             ▼             ▼              ▼
    SiliconFlow   Discourse     PostgreSQL     内部搜索
      API           API           DB            服务
```