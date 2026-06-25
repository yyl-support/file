# Issue #921 RAG API 测试命令

> 替换 `<域名>` 为实际地址

```bash
BASE="https://<域名>"
TOKEN="<access_token>"
```

---

## 健康检查（无需 token）

```bash
curl -s $BASE/health
```

---

## OIDC 获取 token

浏览器访问：
```
$BASE/api/v1/rag/auth/authorize
```
→ OneID 登录 → 回调返回 JSON，复制 access_token

---

## 检索（POST，透传 /query）

```bash
curl -s -X POST $BASE/api/v1/rag/retrieve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"BMC 固件升级","only_need_context":true}'
```

## 文档状态统计（GET，透传）

```bash
curl -s $BASE/api/v1/rag/documents/status_counts \
  -H "Authorization: Bearer $TOKEN"
```

## 管道状态（GET，透传）

```bash
curl -s $BASE/api/v1/rag/documents/pipeline_status \
  -H "Authorization: Bearer $TOKEN"
```

## 分页文档列表（POST，透传）

```bash
curl -s -X POST $BASE/api/v1/rag/documents/paginated \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"page":1,"page_size":10}'
```

---

## 401 验证

```bash
# 无 token
curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/api/v1/rag/retrieve \
  -H "Content-Type: application/json" -d '{"query":"test"}'

# 假 token
curl -s -o /dev/null -w "%{http_code}" $BASE/api/v1/rag/documents/status_counts \
  -H "Authorization: Bearer fake123"
```

## 429 限流（循环 105 次，第 101 次起应为 429）

```bash
for i in $(seq 1 105); do
  curl -s -o /dev/null -w "$i:%{http_code} " $BASE/api/v1/rag/documents/status_counts \
    -H "Authorization: Bearer $TOKEN"
done
```
