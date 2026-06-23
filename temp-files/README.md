# forum-reply-robot

自动监控论坛新帖并调用大模型智能回复的机器人服务。

## 功能特性

- **新帖自动监控**：周期性轮询论坛，发现带指定标签/分类的新帖
- **AI 智能回复**：对问题帖进行摘要提取 → 站内搜索 + LightRAG 知识库检索 → 调用大模型生成回答 → 自动发帖回复
- **AI 预审回复**：对预审标签帖子，解析就绪状态后执行结构化合规校验（Redfish Schema + MDB 规则），将评审报告作为回复
- **安全防护**：提示词注入检测、答案相关性校验、质量校验三层把关，校验失败默认不回复
- **知识库管理**：基于 LightRAG 的 RAG 知识库，启动时全量初始化 + 每日定时增量更新
- **数据持久化**：PostgreSQL 存储处理记录、token 消耗；CSV 并行落盘
- **可观测性**：Prometheus metrics 导出、结构化 JSON 日志、健康检查接口

## 架构设计

### 进程模型

```
main()
 ├─ check_schema_files()          # SchemaFiles 目录检查（缺失则退出）
 ├─ check_mdb_rule_files()        # MdbRuleFiles 目录检查（缺失降级）
 ├─ load_config() → delete_config_file()  # 加载并立即删除配置文件
 ├─ [守护线程] initialization_worker()
 │    ├─ lightrag_data_init()      # 同步：LightRAG 全量初始化（失败则退出）
 │    ├─ initialize_service()      # 启动 ForumMonitor 轮询线程
 │    └─ lightrag_data_update_timer()  # 启动定时增量更新线程
 └─ [主线程] Flask 应用（健康检查/指标暴露），绑定内网私有 IP:5000
```

### 两条核心处理链路

#### 1. 常规问答回复链路

```
拉新帖列表 → 去重(DB) → 提示词注入检测 → 问题摘要
→ 站内搜索 + LightRAG 文档检索 → 大模型生成回答
→ 答案相关性校验 → 答案质量校验 → 组装回复(含折叠块)
→ 调用论坛 API 发帖 → 落库/写 CSV
```

#### 2. AI 预审回复链路

```
拉新帖列表 → 去重(DB) → 解析预审就绪状态
→ 结构化合规校验(Redfish Schema + MDB 规则)
→ 生成 Markdown 评审报告 → 调用论坛 API 发帖
```

**关键设计原则**：
- 逐帖容错：单帖异常不影响其他帖子（try/except continue）
- 校验从严：校验失败/出错默认不回复，避免发布低质量内容
- 去重以 DB 为权威：已处理 topic_id 记录在 `forum_topics` / `pre_audit_topics` 表
- 安全优先：用户输入用随机字符串包裹后喂给大模型；配置文件加载后立即删除

### 模块职责

| 模块 | 职责 |
|------|------|
| `src/ForumBot/monitor.py` | 编排核心：轮询主循环、链接拼接、回复组装、落库 |
| `src/ForumBot/forum_client.py` | 论坛 HTTP 客户端：拉帖、发帖、搜索、检索 |
| `src/ForumBot/ai_processor.py` | 大模型调用层：摘要、注入检测、相关性/质量校验、生成回答 |
| `src/ForumBot/data_processor.py` | 数据层：PostgreSQL/CSV 读写、HTML 解析、预审状态解析 |
| `src/ForumBot/SchemaValidation/` | Redfish 结构化校验子包 |
| `src/ForumBot/MdbValidation/` | MDB 合规校验子包 |
| `src/update_lightrag/` | 知识库维护：全量初始化 + 定时增量更新 |
| `src/evaluation/` | 离线评估：构建数据集、运行基线评估 |

## 项目结构

```
forum-reply-robot/
├── main.py                          # 生产入口
├── Dockerfile                       # 容器构建（非 root 加固）
├── requirements.txt                 # 生产依赖（精确版本）
├── config/
│   └── config.yaml                  # 运行配置（敏感，不入库）
├── src/
│   ├── utils.py                     # 通用工具
│   ├── ForumBot/                    # 核心业务包
│   │   ├── monitor.py               #   编排核心
│   │   ├── forum_client.py          #   论坛 HTTP 客户端
│   │   ├── ai_processor.py          #   大模型调用层
│   │   ├── data_processor.py        #   数据与解析层
│   │   ├── token_tracker.py         #   Token 用量跟踪
│   │   ├── logging_config.py        #   日志配置
│   │   ├── prometheus_metrics.py    #   Prometheus 指标
│   │   ├── SchemaValidation/        #   Redfish 结构化校验
│   │   └── MdbValidation/          #   MDB 合规校验
│   ├── update_lightrag/            # 知识库维护包
│   └── evaluation/                 # 离线评估
├── tests/                          # pytest 测试
│   ├── conftest.py                  #   测试基础设施（mock 注入）
│   ├── test_*.py                    #   单元测试
│   ├── schema_validation/           #   Redfish 校验测试
│   └── mdb_validation/             #   MDB 校验测试
├── .ai-flow/deploy/                # 部署编排
├── data/                           # 运行数据（运行时生成）
└── logs/                           # 运行日志（运行时生成）
```

## 环境要求

- **Python**: 3.9+
- **PostgreSQL**: 用于去重与处理记录存储
- **LightRAG 服务**: 知识库检索与灌入（需独立部署）
- **大模型 API**：OpenAI 兼容接口（如 SiliconFlow）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备配置

在 `config/config.yaml` 中填写运行配置。关键配置段：

```yaml
api:                    # 大模型 API（OpenAI 兼容）
  base_url: '...'
  api_key: '...'
  model_name: '...'
  model2_name: '...'    # 备用模型

posts:                  # 论坛发帖 API（Discourse 风格）
  base_url: '...'
  api_key: '...'
  api_username: '...'

database:               # PostgreSQL 连接
  host: '...'
  port: 5432
  dbname: '...'
  user: '...'
  password: '...'

monitor:                # 轮询配置
  poll_interval: 300    # 轮询间隔（秒）

retrieval:              # LightRAG 检索
  base_url: '...'

search:                 # 站内搜索
  base_url: '...'
```

**注意**：`config.yaml` 包含明文凭据，已被 `.gitignore` 忽略。服务启动后会立即删除该文件。

### 3. 准备 Schema 文件

Redfish Schema 文件不在本仓库中，需在构建/运行前拉取：

```bash
git clone <SchemaFiles仓库地址> src/ForumBot/SchemaValidation/SchemaFiles
```

MDB 规则文件同理（可选，缺失时降级跳过 MDB 校验）：

```bash
git clone <MDB规则仓库地址> src/ForumBot/MdbValidation/MdbRuleFiles
```

### 4. 启动服务

```bash
python main.py
```

服务启动后监听内网私有 IP（优先 `10.` 段，其次 `192.168.`）的 5000 端口。

### 5. 健康检查

| 端点 | 用途 | 正常返回 |
|------|------|---------|
| `GET /health` | 存活探针 | `200` |
| `GET /health/detail` | 组件级状态详情 | `200` |
| `GET /startup` | 启动探针（就绪前返回 `503`） | `200` |
| `GET /metrics` | Prometheus 指标 | `200` |

## 测试

### 测试框架与组织

项目使用 **pytest** 进行测试，共 40+ 测试文件，覆盖核心业务模块。

```
tests/
├── conftest.py                        # 测试基础设施
├── test_data_processor.py             # 数据处理层
├── test_data_processor_pre_audit.py   # 预审数据处理
├── test_forum_client.py               # 论坛客户端
├── test_monitor_pre_audit.py          # 预审监控逻辑
├── test_health_check.py               # 健康检查接口
├── test_main_initialization.py        # 主流程初始化
├── test_main_schema_files.py          # Schema 文件检查
├── test_utils.py                      # 工具函数
├── test_token_tracker.py              # Token 跟踪
├── test_prometheus_metrics.py         # Prometheus 指标
├── test_jsonb_registration.py         # JSONB 适配器注册
├── test_evaluation_*.py               # 离线评估
├── schema_validation/                 # Redfish 校验（9 个测试文件）
└── mdb_validation/                    # MDB 校验（3 个测试文件）
```

### 运行测试

```bash
# 运行全部测试
pytest

# 运行指定模块测试
pytest tests/schema_validation/

# 运行指定测试文件
pytest tests/test_data_processor.py

# 带详细输出
pytest -v

# 带覆盖率报告
pytest --cov=src --cov-report=term-missing
```

### 测试基础设施 (`tests/conftest.py`)

conftest.py 提供无需真实外部服务的测试环境：

- **自动路径注入**：将项目根目录、SchemaValidation、MdbValidation 加入 `sys.path`
- **数据库 Mock**：`psycopg2`/`psycopg2.extras` 替换为 dummy 模块
- **大模型 Mock**：`openai`、`langchain_openai`、`langchain_core` 替换为 dummy 实现，测试中未显式 mock 会抛出 `RuntimeError`
- **Web 框架 Mock**：`flask` 替换为 `DummyFlask`
- **HTML 解析**：`markdownify` 用 BeautifulSoup 模拟 Markdown 转换
- **Git 操作 Mock**：`git.Repo` 替换为 `DummyRepo`

### 编写集成测试

项目通过 conftest.py 的模块级 mock 机制实现"集成测试"——测试调用真实业务逻辑但隔离外部依赖。关键约定：

1. **外部服务调用需在测试中显式 mock**：
   ```python
   from unittest.mock import patch, Mock

   def test_my_feature():
       with patch('src.ForumBot.ai_processor.OpenAI') as mock_openai:
           mock_client = Mock()
           mock_client.chat.completions.create.return_value = Mock(
               choices=[Mock(message=Mock(content="mocked response"))]
           )
           mock_openai.return_value = mock_client
           # 执行业务逻辑...
   ```

2. **未 mock 的外部调用会报错**：conftest.py 中的 dummy 模块会抛出 `RuntimeError`，帮助发现遗漏的 mock。

3. **测试数据集**：对于需要真实数据的场景，可在 `tests/` 下放置 JSON fixture 文件。

## 容器化部署

### 构建镜像

```bash
docker build -t forum-reply-robot .
```

Dockerfile 特性：
- 基础镜像 `python:3.9-slim`
- 构建期从 GitCode 拉取 Schema/MDB 规则文件
- 非 root 用户 `appuser` 运行
- 安全加固：删除编译器、调试器、二进制工具

### 运行容器

```bash
docker run -d \
  -p 5000:5000 \
  -v /path/to/config.yaml:/app/config/config.yaml \
  forum-reply-robot
```

### Kubernetes 预览环境

`.ai-flow/deploy/` 提供基于 Backlog Workflow 的预览环境部署编排：

| 文件 | 用途 |
|------|------|
| `preview.sh` | 主部署脚本：验权 → 建命名空间 → 底座 PostgreSQL → 部署子服务 |
| `services.yaml` | 业务拓扑与底座配置 |
| `test-sync/sync.sh` | 单子服务部署：读 Vault 配置 → 改写预览形态 → 创建 Secret → runtime-clone |
| `test-sync/routes.sh` | 同步 test 环境 ingress 路由到预览 |

## 外部依赖关系

```
forum-reply-robot
    ├── 大模型 API (OpenAI 兼容)     ← 生成回答、校验
    ├── 论坛平台 API (Discourse)     ← 拉帖、发帖
    ├── 站内搜索服务                 ← 按摘要搜索相关主题
    ├── LightRAG 服务               ← 文档检索 + 知识库灌入
    ├── PostgreSQL                  ← 去重、处理记录存储
    └── GitCode                     ← Schema/MDB 规则文件拉取、知识源
```

所有外部端点与凭据均通过 `config/config.yaml` 配置。

## 安全说明

- `config/config.yaml` 含明文凭据/密钥，已被 `.gitignore` 忽略，**切勿提交到版本库**
- 服务启动后立即执行 `delete_config_file()` 删除配置文件，防止敏感信息长期落盘
- 用户输入（帖子内容）在传给大模型前用随机 UUID 字符串包裹，缓解提示词注入
- 注入检测/相关性/质量校验失败时从严默认（判为注入/不相关/不合格，宁可不回复）
- 容器以非 root 用户运行，已删除编译器和调试工具
