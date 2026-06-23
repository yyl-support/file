# forum-reply-robot OIDC 认证切换指南

## 1. 背景与目标

### 1.1 当前认证方式

当前工程通过 Discourse 论坛的 `Api-Key` + `Api-Username` Header 硬编码方式认证，所有凭证集中在 `config/config.yaml` 中，启动后删除文件防止泄露。

| 服务 | 当前认证方式 |
|------|------------|
| Discourse 论坛（回复） | HTTP Header: `Api-Key` + `Api-Username` |
| Discourse 论坛（读取） | 无需认证 |
| AI 大模型 | OpenAI SDK: `api_key` (Bearer Token) |
| PostgreSQL | psycopg2: `user` + `password` |
| 搜索/检索服务 | 自定义 Header / 无显式认证 |

### 1.2 切换目标

将 Discourse 论坛的回复认证从 `Api-Key` 硬编码方式切换为 **openEuler OneID OIDC** 认证，使用 Bearer Token 替代静态 API Key。

### 1.3 OIDC 协议关键信息

| 项目 | 值 |
|------|---|
| 授权端点 | `https://omapi.osinfra.cn/oneid/oidc/authorize` |
| Token 端点 | `https://omapi.osinfra.cn/oneid/oidc/token` |
| 用户信息端点 | `https://omapi.osinfra.cn/oneid/oidc/user` |
| access_token 有效期 | **120 秒（2 分钟）** |
| refresh_token 有效期 | 单次使用，刷新后返回新的 |
| 支持模式 | 授权码模式（authorization_code）、密码模式（password）、刷新模式（refresh_token） |
| scope 必须包含 | `openid profile` |
| 获取 refresh_token | scope 中必须包含 `offline_access` |

## 2. 方案选型

### 2.1 为什么选择密码模式

本工程为纯后端服务机器人，无用户浏览器参与，不适合授权码模式（需要 redirect_uri 回调跳转）。OIDC 文档明确支持密码模式：

```
POST https://omapi.osinfra.cn/oneid/oidc/token
    ?grant_type=password
    &redirect_uri=http://localhost:8080
    &account=<账号>
    &password=<密码>
    &scope=openid profile offline_access
    &client_id=<client_id>
    &client_secret=<client_secret>
```

### 2.2 授权码模式不适用原因

- 授权码模式要求浏览器跳转到 `redirect_uri`，本工程无 Web 前端
- 本工程在 Docker 容器中以 `appuser` 后台运行，无法处理浏览器回调
- 需要持续自动运行，不能依赖人工交互完成授权

### 2.3 最终方案

**密码模式获取初始 token + refresh_token 自动续期**：

1. 启动时通过密码模式获取 `access_token` + `refresh_token`
2. 每次 API 调用前检查 token 是否即将过期
3. 过期或即将过期时通过 `refresh_token` 自动续期
4. 续期后立即更新内存中的 `access_token` 和 `refresh_token`

## 3. 改造详情

### 3.1 配置文件变更

#### config.yaml 新增 OIDC 配置段

```yaml
oidc:
  base_url: "https://omapi.osinfra.cn/oneid/oidc"
  client_id: "xxxxxxxxxxx"          # OneID 注册的 app id
  client_secret: "xxxxxxxxxxx"      # OneID 注册的 app 密钥
  account: "bot_account"            # 机器人账号
  password: "bot_password"          # 机器人账号密码
  scope: "openid profile offline_access"
  redirect_uri: "http://localhost:8080"  # 密码模式必填但实际不跳转
  token_refresh_threshold: 60       # token 剩余有效期低于此值(秒)时主动刷新
```

#### config.yaml 删除旧配置

```yaml
# 以下字段删除：
posts:
  api_key: '**********'            # 删除
  api_username: 'bot_username'     # 删除
```

保留 `posts.base_url` 和 `posts.verify_ssl`，因为回复接口的 URL 和 SSL 设置仍然需要。

### 3.2 新增 OIDC Client 模块

#### 文件路径：`src/ForumBot/oidc_client.py`

```python
import requests
import time
import threading
from .logging_config import main_logger as logger


class OIDCClient:
    def __init__(self, config):
        self.config = config
        self.oidc_config = config.get('oidc', {})
        self.base_url = self.oidc_config.get('base_url', '')
        self.client_id = self.oidc_config.get('client_id', '')
        self.client_secret = self.oidc_config.get('client_secret', '')
        self.account = self.oidc_config.get('account', '')
        self.password = self.oidc_config.get('password', '')
        self.scope = self.oidc_config.get('scope', 'openid profile offline_access')
        self.redirect_uri = self.oidc_config.get('redirect_uri', 'http://localhost:8080')
        self.refresh_threshold = self.oidc_config.get('token_refresh_threshold', 60)

        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = 0
        self._username = None
        self._lock = threading.Lock()

        self._init_tokens()

    def _init_tokens(self):
        logger.info("OIDC: 通过密码模式获取初始 token")
        result = self._request_token_password()
        if result:
            self._update_tokens(result)
            self._fetch_username()
            logger.info("OIDC: 初始 token 获取成功")
        else:
            logger.error("OIDC: 初始 token 获取失败")

    def _request_token_password(self):
        url = f"{self.base_url}/token"
        params = {
            'grant_type': 'password',
            'redirect_uri': self.redirect_uri,
            'account': self.account,
            'password': self.password,
            'scope': self.scope,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        try:
            response = requests.post(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"OIDC: 密码模式请求失败, status={response.status_code}, body={response.text}")
                return None
        except Exception as e:
            logger.error(f"OIDC: 密码模式请求异常: {e}")
            return None

    def _request_token_refresh(self):
        url = f"{self.base_url}/token"
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        try:
            response = requests.post(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"OIDC: refresh_token 请求失败, status={response.status_code}, body={response.text}")
                return None
        except Exception as e:
            logger.error(f"OIDC: refresh_token 请求异常: {e}")
            return None

    def _update_tokens(self, result):
        self._access_token = result.get('access_token')
        self._refresh_token = result.get('refresh_token')
        expires_in = result.get('expires_in', 120)
        self._token_expires_at = time.time() + expires_in
        logger.info(f"OIDC: token 已更新, expires_in={expires_in}s, expires_at={self._token_expires_at}")

    def _fetch_username(self):
        url = f"{self.base_url}/user"
        headers = {
            'Authorization': f'Bearer {self._access_token}'
        }
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json().get('data', {})
                self._username = data.get('username') or data.get('preferred_username') or data.get('nickname')
                logger.info(f"OIDC: 获取用户名成功: {self._username}")
            else:
                logger.error(f"OIDC: 获取用户信息失败, status={response.status_code}")
                self._username = self.account
        except Exception as e:
            logger.error(f"OIDC: 获取用户信息异常: {e}")
            self._username = self.account

    def get_access_token(self):
        with self._lock:
            remaining = self._token_expires_at - time.time()
            if remaining < self.refresh_threshold:
                logger.info(f"OIDC: token 即将过期(剩余{remaining:.0f}s)，主动刷新")
                self._refresh_access_token()
            return self._access_token

    def get_username(self):
        with self._lock:
            if self._username is None:
                self._fetch_username()
            return self._username

    def _refresh_access_token(self):
        if self._refresh_token:
            result = self._request_token_refresh()
            if result:
                self._update_tokens(result)
                self._fetch_username()
                return
        logger.warning("OIDC: refresh_token 刷新失败，回退到密码模式重新获取")
        result = self._request_token_password()
        if result:
            self._update_tokens(result)
            self._fetch_username()
        else:
            logger.error("OIDC: 密码模式回退也失败，token 可能不可用")
```

### 3.3 forum_client.py 改造

#### reply_to_topic 方法

```python
# 原代码 (forum_client.py:43-46)
headers = {
    "Content-Type": "application/json",
    "Api-Key": self.config['posts']['api_key'],
    "Api-Username": self.config['posts']['api_username']
}

# 新代码
def reply_to_topic(self, topic_id, reply_content):
    logger.info(f"正在回复主题 {topic_id}")
    verify_ssl = self.config.get('posts', {}).get('verify_ssl', True)
    access_token = self.oidc_client.get_access_token()
    username = self.oidc_client.get_username()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Api-Username": username
    }
    payload = {
        "topic_id": topic_id,
        "raw": reply_content
    }
    try:
        response = requests.post(
            f"{self.config['posts']['base_url']}/posts.json",
            headers=headers,
            data=json.dumps(payload),
            verify=verify_ssl,
            timeout=30
        )
        if response.status_code == 200:
            logger.info(f"主题 {topic_id} 回复成功")
            return {"success": True, "data": response.json()}
        elif response.status_code == 401:
            logger.warning(f"主题 {topic_id} 回复认证失败(401)，尝试刷新 token 后重试")
            self.oidc_client._refresh_access_token()
            access_token = self.oidc_client.get_access_token()
            headers["Authorization"] = f"Bearer {access_token}"
            response = requests.post(
                f"{self.config['posts']['base_url']}/posts.json",
                headers=headers,
                data=json.dumps(payload),
                verify=verify_ssl,
                timeout=30
            )
            if response.status_code == 200:
                logger.info(f"主题 {topic_id} 重试回复成功")
                return {"success": True, "data": response.json()}
            else:
                logger.error(f"主题 {topic_id} 重试回复仍失败, status={response.status_code}")
                return {"success": False, "status_code": response.status_code, "error_message": response.text}
        else:
            logger.error(f"主题 {topic_id} 回复失败，状态码: {response.status_code}")
            return {"success": False, "status_code": response.status_code, "error_message": response.text}
    except Exception as e:
        logger.error(f"主题 {topic_id} 回复请求发送失败: {e}")
        return {"success": False, "error": f"请求发送失败: {e}"}
```

#### ForumClient 初始化

```python
# 原代码 (forum_client.py:15-16)
class ForumClient:
    def __init__(self, config):
        self.config = config

# 新代码
from .oidc_client import OIDCClient

class ForumClient:
    def __init__(self, config):
        self.config = config
        self.oidc_client = OIDCClient(config)
```

### 3.4 monitor.py 改造

```python
# 原代码 (monitor.py:49)
self.forum_client = ForumClient(self.config)

# 无需修改，ForumClient 内部已自动初始化 OIDCClient
self.forum_client = ForumClient(self.config)
```

### 3.5 .gitignore 变更

无需额外修改，`config/config.yaml` 已在 `.gitignore` 中排除，OIDC 凭证同样位于该文件中，启动后 `delete_config_file()` 会删除整个文件。

### 3.6 Dockerfile 变更

无需额外修改，现有安全措施已覆盖 OIDC 凭证保护：

| 安全措施 | 覆盖范围 |
|---------|---------|
| `chmod 600 config.yaml` | OIDC client_secret/password 与原 api_key 同级保护 |
| `USER appuser` | 非 root 运行 |
| `delete_config_file()` | 启动后删除包含 OIDC 凭证的配置文件 |
| `umask 0027` | 新文件权限受限 |

## 4. Token 生命周期管理

### 4.1 关键约束

| 约束 | 影响 |
|------|------|
| access_token 有效期仅 120 秒 | 必须 2 分钟内使用或刷新 |
| refresh_token 单次使用 | 刷新后必须立即存储新的 refresh_token |
| refresh_token 刷新后过期时间不变 | 长时间运行后 refresh_token 也会过期，需回退密码模式 |
| code 仅能使用一次 | 密码模式不受此限制 |

### 4.2 刷新策略

```
┌─────────────────────────────────────────────────────────────┐
│                    Token 生命周期                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 启动                                                     │
│     │                                                        │
│     ▼                                                        │
│  密码模式 → access_token(120s) + refresh_token              │
│     │                                                        │
│     ▼                                                        │
│  每次 reply_to_topic() 调用前:                                │
│     │                                                        │
│     ├─ 剩余有效期 >= 60s → 直接使用                           │
│     │                                                        │
│     ├─ 剩余有效期 < 60s → refresh_token 刷新                  │
│     │   │                                                    │
│     │   ├─ 成功 → 新 access_token + 新 refresh_token         │
│     │   │                                                    │
│     │   └─ 失败 → 回退密码模式重新获取                        │
│     │       │                                                │
│     │       ├─ 成功 → 新 access_token + 新 refresh_token      │
│     │       │                                                │
│     │       └─ 失败 → 记录错误，等待下一轮监控循环重试         │
│     │                                                        │
│     ▼                                                        │
│  调用 Discourse API (Authorization: Bearer <token>)          │
│     │                                                        │
│     ├─ 200 成功                                               │
│     │                                                        │
│     ├─ 401 认证失败 → 立即刷新 token 重试一次                 │
│     │                                                        │
│     └─ 其他错误 → 按原逻辑处理                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 refresh_token 过期回退

OIDC 文档注明："使用 refresh_token 后，返回新的 access_token 和新的 refresh_token。原来的 refresh_token 失效，但过期时间不变。"

这意味着 refresh_token 有一个绝对过期时间。当 refresh_token 也过期时，必须回退到密码模式重新获取全套 token。`OIDCClient` 已实现此回退逻辑。

## 5. OIDC 与 Discourse API 的兼容性

### 5.1 Discourse OIDC 支持情况

Discourse 论坛原生支持 OIDC 登录，通过 OneID OIDC 获取的 Bearer Token 可以用于 Discourse API 调用，前提是：

1. Discourse 管理后台已配置 OneID 作为 OIDC Provider
2. 用户通过 OneID 登录 Discourse 后，Discourse 会将 OIDC token 与内部用户映射
3. 回复帖子时 `Authorization: Bearer <oidc_access_token>` 需要 Discourse 侧验证此 token

### 5.2 需要确认的前置条件

| 前置条件 | 确认方式 |
|---------|---------|
| Discourse 是否已接入 OneID OIDC Provider | 检查 Discourse 管理后台 Settings → Login → OIDC |
| OIDC token 是否被 Discourse API 识别 | 用 OIDC Bearer token 试调 `GET /posts.json` |
| Api-Username 是否仍需保留 | 部分 Discourse 版本要求同时传 Bearer token + Api-Username |
| bot 账号是否在 OneID 注册 | 确认 bot_account 在 OneID 系统中存在 |

### 5.3 兼容模式

如果 Discourse 不直接接受 OIDC Bearer Token，可采用**兼容模式**：

- 用 OIDC 密码模式登录获取 OneID access_token
- 用 OneID 用户信息（username）调用 Discourse 内部 API 生成 Discourse Api-Key
- 用 Discourse Api-Key 回复帖子

此方案相当于用 OIDC 替代了人工登录 Discourse 后台创建 Api-Key 的步骤。

## 6. 切换步骤清单

### 6.1 准备阶段

| 步骤 | 操作 | 负责人 |
|------|------|--------|
| 1 | 在 OneID 注册应用，获取 `client_id` 和 `client_secret` | 运维 |
| 2 | 在 OneID 创建机器人账号，获取 `account` 和 `password` | 运维 |
| 3 | 确认 Discourse 是否已接入 OneID OIDC Provider | 运维 |
| 4 | 用 OIDC Bearer token 测试 Discourse API 是否接受 | 开发 |
| 5 | 确认 `Api-Username` 是否仍需保留 | 开发 |

### 6.2 开发阶段

| 步骤 | 操作 | 涉及文件 |
|------|------|---------|
| 1 | 新增 `oidc` 配置段，删除 `posts.api_key` 和 `posts.api_username` | `config/config.yaml` |
| 2 | 新建 `OIDCClient` 类，封装密码模式获取/刷新 token/获取用户信息 | `src/ForumBot/oidc_client.py`（新建） |
| 3 | `ForumClient.__init__` 初始化 `OIDCClient` | `src/ForumBot/forum_client.py` |
| 4 | `reply_to_topic` 改用 Bearer Token + 401 重试逻辑 | `src/ForumBot/forum_client.py` |
| 5 | `ForumMonitor.__init__` 无需修改（ForumClient 内部已接管） | `src/ForumBot/monitor.py` |

### 6.3 测试阶段

| 步骤 | 测试内容 |
|------|---------|
| 1 | OIDC 密码模式能否成功获取 access_token + refresh_token |
| 2 | OIDC 用户信息接口能否返回 username |
| 3 | Bearer Token + Api-Username 能否成功回复 Discourse 帖子 |
| 4 | 401 认证失败后自动刷新 token 重试是否生效 |
| 5 | refresh_token 过期后回退密码模式是否正常 |
| 6 | 长时间运行（超过 refresh_token 绝对过期时间）后回退是否正常 |
| 7 | `delete_config_file()` 删除 OIDC 凭证后功能是否正常（内存持有） |

### 6.4 部署阶段

| 步骤 | 操作 |
|------|------|
| 1 | 更新 Docker 镜像，包含新的 oidc_client.py |
| 2 | 更新 config.yaml 模板，包含 oidc 配置段 |
| 3 | 部署到容器，注入包含 OIDC 凭证的 config.yaml |
| 4 | 启动服务，观察 OIDC 初始化日志 |
| 5 | 监控 token 刷新频率和回退情况 |

## 7. 回退方案

如果 OIDC 认证在生产环境中出现问题（如 OneID 服务不可用、Discourse 不接受 OIDC token 等），可以快速回退：

1. 在 `config.yaml` 中恢复 `posts.api_key` 和 `posts.api_username`
2. 在 `ForumClient.__init__` 中根据配置判断是否使用 OIDC：

```python
class ForumClient:
    def __init__(self, config):
        self.config = config
        oidc_config = config.get('oidc', {})
        if oidc_config and oidc_config.get('client_id'):
            self.oidc_client = OIDCClient(config)
            self._use_oidc = True
        else:
            self._use_oidc = False

    def reply_to_topic(self, topic_id, reply_content):
        if self._use_oidc:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.oidc_client.get_access_token()}",
                "Api-Username": self.oidc_client.get_username()
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "Api-Key": self.config['posts']['api_key'],
                "Api-Username": self.config['posts']['api_username']
            }
```

3. 通过配置切换即可在 OIDC 和 Api-Key 之间平滑切换，无需修改代码

## 8. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| access_token 仅 120 秒有效 | 高频刷新可能影响回复延迟 | 刷新阈值设 60s，提前刷新避免请求中过期 |
| refresh_token 有绝对过期时间 | 长时间运行后可能无法续期 | 回退密码模式重新获取 |
| OneID 服务不可用 | 机器人完全无法回复 | 监控 OIDC 健康状态，报警通知运维 |
| 密码模式暴露账号密码 | 凭证泄露风险 | 沿用 delete_config_file() + chmod 600 |
| Discourse 不接受 OIDC token | API 调用 401 | 采用兼容模式（OIDC 登录 → 获取 Discourse Api-Key） |
| OIDC 与 Api-Key 并存期冲突 | 配置混乱 | 配置中明确标记使用哪种模式 |

## 9. 新旧流程对比

### 9.1 当前流程

```
启动 → load_config()
     → config['posts']['api_key'] 内存常驻
     → ForumClient 初始化 (静态 Api-Key)
     → reply_to_topic() 每次直接使用 Api-Key
     → 无过期风险，无需刷新
```

### 9.2 OIDC 流程

```
启动 → load_config()
     → OIDCClient.__init__()
         → 密码模式 POST /oneid/oidc/token
         → 获取 access_token + refresh_token
         → GET /oneid/oidc/user 获取 username
     → ForumClient 初始化 (持有 OIDCClient)
     → reply_to_topic()
         → oidc_client.get_access_token()
             → 检查剩余有效期
             → < 60s → refresh_token 刷新
                 → 失败 → 回退密码模式
             → >= 60s → 直接使用
         → Authorization: Bearer <token>
         → 401 → 刷新 token 重试一次
     → delete_config_file() (删除 OIDC 凭证文件)
```