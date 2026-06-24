# Issue #921 RAG API 测试命令

> 测试环境地址：lightrag.test.osinfra.cn

---

## 1. OIDC 授权（浏览器）

浏览器访问：
```
https://lightrag.test.osinfra.cn/api/v1/rag/auth/authorize
```

→ OneID 登录 → 授权 → 回调返回 JSON，复制 `access_token` 和 `refresh_token`。

---

## 2. 健康检查（无需 token）

```bash
curl https://lightrag.test.osinfra.cn/api/v1/rag/health
```

---

## 3. 检索

```bash
TOKEN="<access_token>"
BASE="https://lightrag.test.osinfra.cn"

curl -X POST $BASE/api/v1/rag/retrieve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "BMC 固件升级流程"}'
```

---

## 4. 分词

```bash
curl -X POST $BASE/api/v1/rag/tokenize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "鲲鹏服务器 BMC 管理芯片"}'
```

---

## 5. 无 token 返回 401

```bash
curl -X POST $BASE/api/v1/rag/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

预期：`{"error":"TOKEN_MISSING","message":"请先完成 OneID 认证授权"}`

---

## 6. 刷新 token

```bash
curl -X POST $BASE/api/v1/rag/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

## 7. 知识上传（仅 maintainer/robot）

```bash
curl -X POST $BASE/api/v1/rag/knowledge/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"
```

普通用户预期返回 403。

---

## 8. 限流验证（连续调用 101 次 retrieve）

```bash
for i in $(seq 1 101); do
  code=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST $BASE/api/v1/rag/retrieve \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}')
  echo "$i: $code"
done
```

第 101 次预期返回 429。
