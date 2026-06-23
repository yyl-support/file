"""MDB 资源协作接口合规性校验器（LangChain 适配版）。

从 mdb_interface_compliance_check/compliance_checker.py 移植，LLM 调用从 openai.OpenAI
改为 LangChain ChatOpenAI，去除缓存机制。

复用 config.yaml 的 schema_validation 段 LLM 配置。
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

BLOCKING_SEVERITIES = {"shall", "must"}
WARNING_SEVERITIES = {"should", "may"}


def is_blocking_severity(severity: Any) -> bool:
    """Return True for severities that should fail overall compliance."""
    return str(severity or "").strip().lower() in BLOCKING_SEVERITIES

# ==================== 规则文件路径 ====================

RULES_DIR = Path(__file__).resolve().parent / "MdbRuleFiles"


def _parse_version(name: str) -> float:
    """从文件名提取版本号，支持小数如 v6、v6.1、v10.3。

    匹配 ``_v<数字>[.<数字>]`` 后缀，返回浮点版本号；
    无版本号的文件（如 ``mdb_compliance_rules.json``）返回 -1。
    """
    m = re.search(r"_v(\d+(?:\.\d+)?)\.json$", name, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return -1


def _find_rules_file() -> Path:
    """查找规则 JSON 文件（自动选择最高版本）。

    扫描 MdbRuleFiles 目录下 ``mdb_compliance_rules*.json`` 文件，
    提取版本号（支持 v3 / v5 / v6 / v6.1 等整数和小数），
    返回版本号最高的文件；无版本号的后备文件优先级最低。
    """
    candidates = sorted(
        RULES_DIR.glob("mdb_compliance_rules*.json"),
        key=lambda p: _parse_version(p.name),
        reverse=True,
    )
    if candidates:
        best = candidates[0]
        logger.info("[MDB] 自动选择规则文件: %s (版本 %.1f)", best.name, _parse_version(best.name))
        return best
    raise FileNotFoundError(f"MdbRuleFiles 目录中未找到规则文件：{RULES_DIR}")


# ==================== 规则加载 ====================


def load_rules(path: Path | str | None = None) -> list[dict[str, Any]]:
    """加载规则 JSON。同名 id 与必备字段会做基本校验。"""
    p = Path(path) if path else _find_rules_file()
    if not p.exists():
        raise FileNotFoundError(f"未找到规则文件：{p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"规则文件 {p} 必须是非空 JSON 数组")
    required = {"id", "category", "severity", "rule", "check", "rationale"}
    seen: set[str] = set()
    for i, r in enumerate(data):
        if not isinstance(r, dict):
            raise ValueError(f"规则 #{i} 不是对象")
        miss = required - set(r.keys())
        if miss:
            raise ValueError(f"规则 {r.get('id', f'#{i}')} 缺字段：{sorted(miss)}")
        rid = r["id"]
        if rid in seen:
            raise ValueError(f"规则 id 重复：{rid}")
        seen.add(rid)
    return data


def _split_legacy_ids(value: Any) -> list[str]:
    """Split a legacy_id field into individual IDs."""
    if not value:
        return []
    return [
        item.strip()
        for item in re.split(r"[、,，\s]+", str(value))
        if item.strip()
    ]


def build_rule_mappings(rules: list[dict[str, Any]]) -> dict[str, Any]:
    """从规则列表动态构建 legacy_id→id 映射和 domain 分组。"""
    legacy_to_new: dict[str, str] = {}
    for r in rules:
        for legacy_id in _split_legacy_ids(r.get("legacy_id")):
            legacy_to_new[legacy_id] = r["id"]
    domain_to_ids: dict[str, set[str]] = {}
    for r in rules:
        domain_to_ids.setdefault(r.get("domain_code", "OTHER"), set()).add(r["id"])
    return {"legacy_to_new": legacy_to_new, "domain_to_ids": domain_to_ids}


# ==================== Prompt ====================

LANGUAGE_REQUIREMENT = """## 语言要求（强制）

- 所有自然语言字段（`summary`、`advice`、`findings.evidence`、`findings.location`）**必须使用简体中文**输出。
- 英文术语（属性名、签名字符 `s`/`u`/`b`、`emitsChangedSignal`、`MessageId` 等）**保持原文**嵌入中文句中。
- JSON 字段名与 `compliant` / `true` / `false` 等枚举值保持原样。
"""

GENERAL_GUIDANCE = """## 检查总则

**检查对象**：评审帖**作者撰写**的 markdown 正文（含表格、列表、代码块、内嵌示例）。
**禁止**因为「这是讨论帖」「正文是模板复制」就一刀切判违规。规则中已写明的「豁免」与「触发条件」必须严格执行。

### 规则严重程度

- `shall`：以本次规则列表中每条规则的 `severity` 字段为准；被命中即 `compliant=false`，影响整体合规判定。
- `should` / `may`：被命中也 `compliant=false`，但仅作为警告，不影响 `overall_compliant`。
- 严重程度必须严格使用规则定义中的 `severity` 字段，不得擅自升级、降级或改写。

### 反误报通则（务必遵守）

1. **触发条件不满足直接判合规**：每条规则的 `check` 字段都写了「触发条件」/「适用范围」，若评审点正文不属于触发场景，**必须** `compliant=true`，不得因为「正文里没有这一项」就判违规。
2. **模板原样占位符**：`_xxx_`（前后各一个下划线包裹）、`_y_`、`_True_`、`_例如，xxx_`、`_PropertyValueTypeError_`、`_Prop1_`、`_Method1_`、`_Signal1_`、`_bmc.Xxx.Xxx.Xxx_` 等等，是从申报模板（topic/3817）原样复制的占位示例，**不得**作为违规依据。
3. **从宽原则**：判定不确定时，倾向 `compliant=true`，宁可漏报也不要误报。
4. **仅评估写出的内容**：评审点没写的字段不一定是违规，要先看规则是不是要求「必须有该字段」（shall）；should/may 一般只在已写出但写错时违规。
5. **跨规则串扰禁止**：rule_id 必须严格归属到本次输入的对应规则，不得把某条规则的检查点串到另一条规则。

### DBus 类型签名速查表（强制使用）

评审帖中出现的签名（Signature）字段遵循 D-Bus 类型系统。对单字符签名的含义，必须按以下对照表理解，不得根据字母猜测：

| 签名 | 类型 | 说明 |
| --- | --- | --- |
| b | boolean | 布尔值 |
| y | byte | 单字节 |
| n | int16 | 16 位有符号整数 |
| q | uint16 | 16 位无符号整数 |
| i | int32 | 32 位有符号整数 |
| u | uint32 | 32 位无符号整数 |
| x | int64 | 64 位有符号整数 |
| t | uint64 | 64 位无符号整数 |
| d | double | 双精度浮点 |
| s | string | UTF-8 字符串 |
| o | object path | D-Bus 对象路径 |
| g | signature | 类型签名本身 |
| v | variant | 变体类型 |
| a{...} | array | 字典数组，如 a{sv} |
| (...) | struct | 结构体，括号内为成员类型 |

把 `t` 解释为"文本"属于类型系统理解错误，不得以字符串语义评判 uint64 类型。

### 列名同义词词典（强制识别 —— 出现任意同义/历史列名都视作存在标准列）

| 标准列名 | 同义/历史列名 |
| --- | --- |
| 属性名称 | 属性名 / Property |
| 签名 | Signature / 类型签名 / 属性类型 / 类型 |
| 只读 | readonly / 属性读写 |
| 变化通知 | 变更通知 / emitsChangedSignal / 属性广播 / 广播 |
| 属性描述 | 属性说明 / 描述 / Description / 接口说明 |
| 访问权限 | 权限 / Access / 操作权限 / 读写&权限 |
| 属性来源 | 属性值来源 / 来源 |
| 持久化类型 | 持久化 |
| 易变属性 | 是否易变 / 易变 |
| 方法名称 | 方法名 / Method |
| 请求签名 | Request 签名 / 入参签名 |
| 响应签名 | Response 签名 / 出参签名 |
| 方法描述 | 方法说明 / 描述 / Description / 备注（无独立『方法描述』时） |
| 请求参数描述 | 请求参数 / 入参描述 |
| 响应参数描述 | 响应参数 / 响应体 / 出参描述 |
| 路径 | Path / 实现接口 |
| 接口影响 | 实现接口描述 / 接口描述 |
| CSR 配置影响 | CSR 影响 / CSR 配置 |
| 持久化影响 | 持久化 |
| 其他影响 | 其它影响 / 其他 |

碰到任意同义/历史列名必须视作存在标准列，**不得判缺列**。

### 多评审点共享上下文豁免（重要）

如果同一篇评审帖出现多个评审点（评审点 1 / 评审点 2 / ...）：
- **接口影响表**：评审点 1 已给出，评审点 2/3/... 即便没有重复给出该表，也判合规——属于同一帖子内继承上下文。
- **属性表/方法表/信号表的列结构**：仅当某个评审点**自己声明**了表但表头不全时才检查；评审点之间不强制要求字段对齐。
- **接口描述、变更原因等正文章节**：单评审点内不可缺失；跨评审点不强制重复。

### 列名/单元格容错

1. **列名加粗或斜体**（如 `**属性名称**`、`*属性名称*`、`_属性名称_`）：识别为同名列。
2. **变更前/变更后写在同一格**（如 `变更前: True 变更后: False`）：视为提供了变更对照，不判违规。
3. **单元格留空** 或填 `-` / `/` / `N/A`：仅在规则**明确要求该单元格非空**时才判违规；列存在但单元格空白不等于"列缺失"。
4. **表头列出现额外的扩展列**（如多了「附加说明」「场景」等）：从宽不算违规。

### CSR 属性只读与持久化的合理模式（禁止误判矛盾）

当属性同时满足以下条件时，**必须判合规，不得将其视为矛盾**：
- **属性来源** = CSR（配置寄存器/硬件配置）或类似硬件来源描述
- **只读** = true（或 "是" / "只读"）
- **持久化类型** = 掉电持久化（或类似持久保存的描述）

**原因**：CSR 配置值通过部署/烧录/配置工具在系统初始化阶段写入，运行时通过资源协作接口对外呈现为只读是合理的——应用层不应通过运行时 API 修改硬件配置。掉电持久化说明值存储在非易失存储中，掉电后仍然保持。三者共存是合法且常见的设计模式，不是矛盾。

### 整体合理兜底（shall 级降级保护）

判 `compliant=false` **且 severity=shall** 之前，先做一次自检：
- 评审帖是否有清晰的评审点结构（含编号或章节）？
- 是否给出至少一张属性/方法/信号/影响表，或对等的正文段落说明？
- 表中关键字段（属性名/签名/方法名/路径）是否齐备？
- 违规理由是否仅是「某一列缺失/某一格写法/单纯结构格式」这类边缘问题？

若**全部**为是，且违规理由属于结构性、非语义性问题，**禁止** 把它写成 shall 违规；应判 `compliant=true`，并在 summary 中简要说明触发条件不足或证据不足。不得通过改写 severity 来降级。

### 评审点章节识别提示

- 章节标题常见形式：`## 评审点1：xxx`、`## 评审点 1：xxx`、`### 新增属性`、`### 新增方法`、`### 新增信号`、`### 新增/变更接口影响`、`### 实现接口`。
- markdown 表格可能是标准 GFM 格式（`| 列 | 列 |` + 分隔行 `| --- | --- |`）也可能是 Discourse 简化格式（首尾无 `|`、分隔行如 `---|---|--`）。两种都要识别。
- 占位符行通常用斜体下划线包裹（`_xxx_`），表示是模板示例而非真实数据。
"""

STRICT_EVIDENCE_GUIDANCE = """## 严格证据门槛

- 对所有规则，只有在正文中能引用到具体片段且能指出位置时，才允许 `compliant=false`。
- 不得把"正文未提到""看起来缺少""没有看到"当作违规证据；触发条件不明确时必须判 `compliant=true`。
- `findings.evidence` 必须引用评审帖原文中的关键短句、表格单元格或字段名；不能写泛化结论。
"""


OUTPUT_SPEC = """## 输出格式

**只输出一个 JSON 数组**，首字符 `[`、末字符 `]`，不要 Markdown 代码围栏、不要 JSON 之外的任何文字。

每条规则对应一个对象，必含字段：

```json
{
  "rule_id": "MDB-XXX",
  "category": "<规则类别>",
  "severity": "shall|should|may",
  "compliant": true|false,
  "summary": "<一句话中文结论，与 compliant 同正同负>",
  "advice": "<compliant=false 时给出可执行的中文修复建议；compliant=true 时为 null>",
  "findings": [
    {"evidence": "<引用评审点正文的关键片段>", "location": "<出现位置（章节名/表格名/行号等）>"}
  ]
}
```

**一致性约束**：
- `compliant=true` 时，`summary` 必须是肯定性表述（如「合规」「未触发该规则」「评审点未涉及该场景」），`advice=null`，`findings` 可为空数组。
- `compliant=false` 时，`summary` 必须明确指出哪里违规，`advice` 必填且可执行，`findings` 至少 1 条。
- 数组长度 = 规则数；不得遗漏任何 rule_id；不得伪造未给定的 rule_id。
"""

BATCH_SYSTEM_PROMPT = (
    """你是一位资深 BMC 资源协作接口（mdb interface）评审专家，熟悉 openUBMC
论坛 Interface SIG 发布的三份核心规范：

1. 申报模板（topic/3817）：评审点编号、接口/属性/方法/信号表必填列、错误消息字段。
2. 设计合规性必检指南（topic/1862）：PascalCase 命名、单位后缀、emitsChangedSignal、enum/example/constraint、错误引擎、唯一 Id、标准接口继承。
3. 废弃处理规范（topic/2087）：deprecated 关键字、废弃原因/替代、持久化场景禁删除。

你的任务：阅读一份评审帖的 markdown 正文，**逐条**判定其是否符合给定的规则列表，不合规时给出可执行的中文修复建议。

"""
    + LANGUAGE_REQUIREMENT
    + GENERAL_GUIDANCE
    + STRICT_EVIDENCE_GUIDANCE
    + OUTPUT_SPEC
)


def _build_system_prompt(legacy_to_new: dict[str, str]) -> str:
    """构建系统 prompt，将旧格式规则 ID 替换为新格式。"""
    text = BATCH_SYSTEM_PROMPT
    # 按旧 ID 长度降序替换，避免短 ID 部分匹配长 ID。
    for old_id in sorted(legacy_to_new, key=len, reverse=True):
        text = text.replace(old_id, legacy_to_new[old_id])
    return text


BATCH_USER_PROMPT = """请检查以下评审帖正文是否符合所有规则：

---

## 待检查的所有规则

{rules_text}

---

## 评审帖

**标题**：{title}

**正文（markdown）**：
{body}

---

请输出 JSON 数组（共 {num_rules} 条，含全部 rule_id；compliant=false 时必填 advice）。勿使用 Markdown 围栏。
"""


# ==================== 规则分组 ====================

GENERIC_EVIDENCE_PATTERNS = (
    "not found", "missing", "not provided", "does not mention", "no evidence",
    "N/A", "-", "/", "未提供", "未说明", "未体现", "缺少", "没有", "无",
)

_MISSING_COLUMN_PATTERNS = (
    re.compile(r"缺少[「『\"'“”]?([^，。；;、\s「」『』\"'“”]+)[」』\"'“”]?(?:列|字段)"),
    re.compile(r"(?:未提供|未包含|没有)[「『\"'“”]?([^，。；;、\s「」『』\"'“”]+)[」』\"'“”]?(?:列|字段)"),
)


def group_rules_for_check(rules: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    """按 domain_code 将规则分成语义相关的批次，减少 prompt 稀释。"""
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for r in rules:
        by_domain.setdefault(r.get("domain_code", "OTHER"), []).append(r)
    return [(name, group) for name, group in sorted(by_domain.items())]


def format_rules_for_batch(rules: list[dict[str, Any]]) -> str:
    """把规则列表格式化为 prompt 中的纯文本块。"""
    parts: list[str] = []
    for i, r in enumerate(rules, 1):
        parts.append(
            f"**规则 {i}**\n"
            f"- ID: {r['id']}\n"
            f"- 类别: {r['category']}\n"
            f"- 严重程度: {r['severity']}\n"
            f"- 规则描述: {r['rule']}\n"
            f"- 检查要点: {r['check']}\n"
            f"- 规则理由: {r['rationale']}\n"
        )
    return "\n".join(parts)


# ==================== JSON 修复 ====================


def _extract_top_level_json_array(text: str) -> str | None:
    """从文本中提取与首个 `[` 闭合的顶层 JSON 数组子串。"""
    start = text.find("[")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    qc = ""
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == qc:
                in_str = False
            continue
        if c in ('"', "'"):
            in_str = True
            qc = c
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return text[start: i + 1]
    return None


def _repair_json_text(s: str) -> str:
    """常见 LLM 输出修复：BOM、弯引号、尾逗号。"""
    t = (
        s.replace("\ufeff", "")
        .replace("\u201c", '"').replace("\u201d", '"')
        .replace("\u2018", "'").replace("\u2019", "'")
    )
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r",\s*}", "}", t)
        t = re.sub(r",\s*]", "]", t)
    return t


def _extract_markdown_fence(text: str) -> str | None:
    for opener in ("```json", "```JSON", "```Json", "```"):
        idx = text.find(opener)
        if idx >= 0:
            start = idx + len(opener)
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
    return None


def _try_repair_truncated_array(text: str) -> str | None:
    """从末尾向前找最后一个完整的 `}`，截断后补 `]` 闭合。"""
    start = text.find("[")
    if start < 0:
        return None
    last_complete = -1
    depth_obj = 0
    depth_arr = 0
    in_str = False
    esc = False
    qc = ""
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == qc:
                in_str = False
            continue
        if c in ('"', "'"):
            in_str = True
            qc = c
            continue
        if c == "{":
            depth_obj += 1
        elif c == "}":
            depth_obj -= 1
            if depth_obj == 0 and depth_arr == 1:
                last_complete = i
        elif c == "[":
            depth_arr += 1
        elif c == "]":
            depth_arr -= 1
    if last_complete > start:
        return text[start: last_complete + 1].rstrip().rstrip(",") + "\n]"
    return None


def parse_batch_result(raw: str, rules: list[dict[str, Any]],
                       legacy_to_new: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """解析 LLM 返回的 JSON 数组；解析失败时为每条规则填充 error 占位。"""
    if not raw:
        return [_make_error_result(r, "empty response") for r in rules]
    cleaned = raw.strip()

    candidates: list[str] = [cleaned, _repair_json_text(cleaned)]
    fence = _extract_markdown_fence(cleaned)
    if fence:
        candidates.extend([fence, _repair_json_text(fence)])
    extracted = _extract_top_level_json_array(cleaned)
    if extracted:
        candidates.extend([extracted, _repair_json_text(extracted)])

    seen: set[str] = set()
    for cand in candidates:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            data = json.loads(cand)
            if isinstance(data, list):
                return _validate_and_fill(data, rules, legacy_to_new)
        except json.JSONDecodeError:
            continue

    repaired = _try_repair_truncated_array(cleaned)
    if repaired:
        for cand in (repaired, _repair_json_text(repaired)):
            try:
                data = json.loads(cand)
                if isinstance(data, list) and data:
                    logger.warning("LLM JSON 数组被截断，已修复到 %d/%d 条", len(data), len(rules))
                    return _validate_and_fill(data, rules, legacy_to_new)
            except json.JSONDecodeError:
                continue

    logger.warning("LLM 输出无法解析为 JSON 数组（长度 %d）：%s%s", len(cleaned), cleaned[:300], "..." if len(cleaned) > 300 else "")
    return [_make_error_result(r, "json_parse_failed") for r in rules]


def _make_error_result(rule: dict[str, Any], err: str) -> dict[str, Any]:
    return {
        "rule_id": rule["id"],
        "category": rule.get("category", ""),
        "severity": rule.get("severity", "shall"),
        "compliant": True,
        "summary": f"[解析失败] {err}",
        "advice": None,
        "findings": [],
        "error": err,
    }


def _validate_and_fill(results: list[dict[str, Any]], rules: list[dict[str, Any]],
                        legacy_to_new: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """对照规则 id 集合做缺失补齐 + compliant/summary 一致性修正。"""
    by_id: dict[str, dict[str, Any]] = {}
    for r in results:
        if not isinstance(r, dict):
            continue
        rid = r.get("rule_id") or r.get("id") or ""
        if rid:
            by_id[rid] = r
            if legacy_to_new and rid in legacy_to_new:
                by_id.setdefault(legacy_to_new[rid], r)

    fixed: list[dict[str, Any]] = []
    for rule in rules:
        rid = rule["id"]
        sev = rule.get("severity", "shall")
        category = rule.get("category", "")
        cur = by_id.get(rid)
        # 回退：LLM 可能返回旧格式 legacy_id
        for legacy_id in _split_legacy_ids(rule.get("legacy_id")):
            if cur is not None:
                break
            cur = by_id.get(legacy_id)
        if cur is None:
            fixed.append(_make_error_result(rule, "missing in response"))
            continue
        compliant = bool(cur.get("compliant", True))
        summary = str(cur.get("summary") or "")
        advice = cur.get("advice")
        findings = cur.get("findings") or []
        if not isinstance(findings, list):
            findings = []

        if not compliant and not summary:
            summary = "评审帖正文存在不符合规则的内容"
        if compliant:
            advice = None
        else:
            if advice in (None, ""):
                advice = "请按规则描述与检查要点修复评审帖正文"

        fixed.append({
            "rule_id": rid,
            "category": category,
            "severity": sev,
            "compliant": compliant,
            "summary": summary,
            "advice": advice,
            "findings": findings,
        })
    return fixed


# ==================== 误报防护 ====================


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _has_concrete_evidence(findings: list[Any]) -> bool:
    for item in findings:
        if not isinstance(item, dict):
            continue
        evidence = _norm_text(item.get("evidence"))
        location = _norm_text(item.get("location"))
        if len(evidence) < 8 or len(location) < 2:
            continue
        low = evidence.lower()
        generic = False
        for pattern in GENERIC_EVIDENCE_PATTERNS:
            p = pattern.lower()
            if (len(p) <= 2 and low == p) or (len(p) > 2 and p in low):
                generic = True
                break
        if generic:
            continue
        return True
    return False


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def _collect_result_text(result: dict[str, Any]) -> str:
    parts = [
        result.get("summary", ""),
        result.get("advice", ""),
    ]
    for item in result.get("findings") or []:
        if isinstance(item, dict):
            parts.append(item.get("evidence", ""))
            parts.append(item.get("location", ""))
    return "\n".join(str(p or "") for p in parts)


def _extract_claimed_missing_columns(result: dict[str, Any]) -> set[str]:
    """Extract column/field names from generic LLM statements like "缺少「访问权限」列"."""
    text = _collect_result_text(result)

    columns: set[str] = set()
    for pattern in _MISSING_COLUMN_PATTERNS:
        for match in pattern.finditer(text):
            name = (match.group(1) or "").strip(" ：:，,。.;；")
            if 1 < len(name) <= 30:
                columns.add(name)
    return columns


def _body_contains_column(body: str, column: str) -> bool:
    body_compact = _compact_text(body)
    column_compact = _compact_text(column)
    return bool(column_compact and column_compact in body_compact)


def _has_refuted_missing_column_claim(result: dict[str, Any], body: str) -> bool:
    claimed_columns = _extract_claimed_missing_columns(result)
    if not claimed_columns:
        return False
    return any(_body_contains_column(body, column) for column in claimed_columns)


_ABSENCE_CLAIM_TERMS = (
    "完全缺失", "缺失", "缺少", "未提供", "未包含", "没有提供", "没有", "无",
    "missing", "not provided", "not found", "does not contain",
)

_TABLE_SIGNATURES: tuple[tuple[tuple[str, ...], tuple[tuple[str, ...], ...]], ...] = (
    (
        ("属性表", "属性表格", "属性字段", "属性列表", "property table"),
        (
            ("属性名称", "属性名", "property"),
            ("签名", "signature", "类型签名", "属性类型", "类型"),
            ("只读", "readonly", "读写"),
            ("变化通知", "变更通知", "emitschangedsignal", "广播"),
            ("属性描述", "属性说明", "description", "描述"),
            ("访问权限", "权限", "access"),
        ),
    ),
    (
        ("方法表", "方法表格", "方法字段", "method table"),
        (
            ("方法名称", "方法名", "method"),
            ("请求签名", "request 签名", "入参签名"),
            ("响应签名", "response 签名", "出参签名"),
            ("方法描述", "方法说明", "description", "描述"),
        ),
    ),
    (
        ("信号表", "信号表格", "signal table"),
        (
            ("信号名称", "信号名", "signal"),
            ("签名", "signature", "类型"),
            ("信号描述", "信号说明", "description", "描述"),
        ),
    ),
    (
        ("影响表", "接口影响表", "接口影响", "impact table"),
        (
            ("路径", "path"),
            ("接口影响", "接口描述"),
            ("csr",),
            ("持久化",),
        ),
    ),
)


def _body_has_table_signature(body: str, header_groups: tuple[tuple[str, ...], ...]) -> bool:
    body_compact = _compact_text(body)
    if not body_compact:
        return False
    matched_groups = 0
    for aliases in header_groups:
        if any(_compact_text(alias) in body_compact for alias in aliases):
            matched_groups += 1
    return matched_groups >= 3


def _has_refuted_missing_table_claim(result: dict[str, Any], body: str) -> bool:
    """Suppress claims like "正文完全缺失属性表" when the body visibly contains that table."""
    claim_text = _compact_text(_collect_result_text(result))
    if not claim_text or not body:
        return False
    if not any(_compact_text(term) in claim_text for term in _ABSENCE_CLAIM_TERMS):
        return False

    for table_labels, header_groups in _TABLE_SIGNATURES:
        if any(_compact_text(label) in claim_text for label in table_labels):
            if _body_has_table_signature(body, header_groups):
                return True
    return False


_CONTRADICTION_TERMS = ("矛盾", "冲突", "不一致", "contradict", "inconsistent")
_RESET_PERSISTENCE_TERMS = ("复位持久化",)
_NON_BMC_RESET_TERMS = ("系统复位", "系统上下电", "上下电", "NPU复位", "部件复位", "设备复位", "Host复位", "hostreset")
_BMC_RESET_TERMS = ("BMC复位", "管理控制器复位", "bmcreset")
_RESET_CLEAR_TERMS = ("清零", "归零", "恢复为0", "恢复为 0", "置0", "置为0", "resetto0", "cleared")
_MISSING_RATIONALE_TERMS = ("缺少变更原因", "未提供变更原因", "没有说明变更原因", "变更原因缺失")
_RATIONALE_BODY_TERMS = ("为了", "防止", "避免", "保持", "用于", "场景", "预期", "导致", "影响", "支持", "提供")
_GENERIC_INTERFACE_PATH_CLAIM_TERMS = ("标题声明", "正文路径", "路径层级", "互相矛盾", "层级矛盾")
_GENERIC_INTERFACE_PATH_BODY_TERMS = ("实现接口", "路径描述", "资源协作路径", "新增接口影响")
_INFERRED_ENUM_DEFAULT_CLAIM_TERMS = (
    "默认值", "不在声明的枚举范围", "不在枚举范围", "不在候选集", "不在合法范围"
)
_EXPLICIT_ENUM_TERMS = ("枚举", "取值范围", "候选集", "合法值", "可选值", "enum")
_STATE_VALUE_EXPLANATION_PATTERN = re.compile(
    r"\d+\s*[：:]\s*[^，,；;|]+[，,；;]\s*\d+\s*[：:]\s*[^，,；;|]+[，,；;]\s*默认值\s*[：:]\s*\d+"
)


def _contains_any_compact(text: str, terms: tuple[str, ...]) -> bool:
    compact = _compact_text(text)
    return any(_compact_text(term) in compact for term in terms)


def _has_refuted_reset_persistence_contradiction_claim(result: dict[str, Any], body: str) -> bool:
    """Do not treat host/device reset clearing as contradicting reset persistence."""
    claim_text = _collect_result_text(result)
    if not claim_text or not body:
        return False
    if not _contains_any_compact(claim_text, _CONTRADICTION_TERMS):
        return False
    if not _contains_any_compact(claim_text + "\n" + body, _RESET_PERSISTENCE_TERMS):
        return False
    if not (
        _contains_any_compact(claim_text + "\n" + body, _NON_BMC_RESET_TERMS)
        and _contains_any_compact(claim_text + "\n" + body, _RESET_CLEAR_TERMS)
    ):
        return False

    # If the evidence explicitly says BMC/management-controller reset clears the value,
    # keep the finding; that is the reset domain normally implied by reset persistence.
    bmc_reset_clear = any(
        _compact_text(reset_term) in _compact_text(body)
        and _compact_text(clear_term) in _compact_text(body)
        for reset_term in _BMC_RESET_TERMS
        for clear_term in _RESET_CLEAR_TERMS
    )
    return not bmc_reset_clear


def _has_refuted_missing_change_rationale_claim(result: dict[str, Any], body: str) -> bool:
    """Suppress missing-rationale claims when the body gives a concrete reason/scenario."""
    claim_text = _collect_result_text(result)
    if not claim_text or not body:
        return False
    if not _contains_any_compact(claim_text, _MISSING_RATIONALE_TERMS):
        return False
    return _contains_any_compact(body, _RATIONALE_BODY_TERMS)


def _has_refuted_generic_interface_path_claim(result: dict[str, Any], body: str) -> bool:
    """Allow an abstract interface name to be implemented by more specific instance paths."""
    claim_text = _collect_result_text(result)
    if not claim_text or not body:
        return False
    if not _contains_any_compact(claim_text, _GENERIC_INTERFACE_PATH_CLAIM_TERMS):
        return False
    body_compact = _compact_text(body)
    if not all(_compact_text(term) in body_compact for term in _GENERIC_INTERFACE_PATH_BODY_TERMS[:2]):
        return False
    return bool(
        re.search(r"bmc\.kepler\.[A-Za-z0-9_.]+", body)
        and re.search(r"/bmc/kepler/.+", body)
    )


def _has_refuted_inferred_enum_default_claim(result: dict[str, Any], body: str) -> bool:
    """Do not infer a complete enum set from inline state-code explanations."""
    claim_text = _collect_result_text(result)
    if not claim_text or not body:
        return False
    if not _contains_any_compact(claim_text, ("默认值",)):
        return False
    if not _contains_any_compact(claim_text, _INFERRED_ENUM_DEFAULT_CLAIM_TERMS[1:]):
        return False
    if _contains_any_compact(body, _EXPLICIT_ENUM_TERMS):
        return False
    return bool(_STATE_VALUE_EXPLANATION_PATTERN.search(body))


def _apply_false_positive_guard(results: list[dict[str, Any]], body: str = "",
                                 sibling_context: str = "") -> list[dict[str, Any]]:
    """Suppress model findings contradicted by the body or missing concrete evidence."""
    guarded: list[dict[str, Any]] = []
    for r in results:
        if not r.get("compliant", True) and _has_refuted_missing_column_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "模型声称缺少的列在评审点正文中已出现，按误报压制"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "missing_column_claim_refuted_by_body"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and sibling_context and _has_refuted_missing_column_claim(r, sibling_context):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "模型声称缺少的列在同帖子其他MDB评审点正文中已出现，按误报压制"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "missing_column_claim_refuted_by_sibling_context"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and _has_refuted_missing_table_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "模型声称缺失的表格在评审点正文中已出现，按误报压制"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "missing_table_claim_refuted_by_body"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and sibling_context and _has_refuted_missing_table_claim(r, sibling_context):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "模型声称缺失的表格在同帖子其他MDB评审点中已出现，按误报压制"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "missing_table_claim_refuted_by_sibling_context"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and _has_refuted_reset_persistence_contradiction_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "模型将系统/设备复位清零误判为复位持久化矛盾，按误报压制"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "reset_persistence_domain_conflation"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and _has_refuted_missing_change_rationale_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "正文已提供变更原因或使用场景，影响说明不足应由建议性风险规则提示"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "change_rationale_present_in_body"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and _has_refuted_generic_interface_path_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "正文已说明通用接口由具体资源协作路径实现，接口名与实例路径不构成层级矛盾"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "generic_interface_implemented_by_instance_path"
            guarded.append(cur)
            continue

        if not r.get("compliant", True) and _has_refuted_inferred_enum_default_claim(r, body):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "正文只是解释状态码含义，未明确声明完整枚举范围，不能据此判默认值越界"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "state_code_explanation_not_complete_enum"
            guarded.append(cur)
            continue

        if (
            not r.get("compliant", True)
            and not _has_concrete_evidence(r.get("findings") or [])
        ):
            cur = dict(r)
            cur["compliant"] = True
            cur["summary"] = "证据不足，按从宽原则不判定该规则违规"
            cur["advice"] = None
            cur["findings"] = []
            cur["suppressed_reason"] = "insufficient_concrete_evidence"
            guarded.append(cur)
        else:
            guarded.append(r)
    return guarded


# ==================== LLM 客户端（LangChain 适配） ====================


class MdbComplianceChecker:
    """MDB 资源协作接口合规性检查器。

    使用 LangChain ChatOpenAI，复用 config.yaml 的 schema_validation 段配置。
    """

    def __init__(self, config: dict) -> None:
        """初始化检查器。

        Args:
            config: 完整的 config.yaml dict，从中取 schema_validation 段的 LLM 配置。
        """
        sv_cfg = config.get('schema_validation', {})
        self._model = sv_cfg.get('model', '')
        self._llm = ChatOpenAI(
            model=self._model,
            api_key=sv_cfg.get('api_key', ''),
            base_url=sv_cfg.get('base_url', ''),
            temperature=0.0,
            max_tokens=200000,
            timeout=900,
            max_retries=int(sv_cfg.get('max_retry', 3)),
        )
        self._rules = load_rules()
        mappings = build_rule_mappings(self._rules)
        self._legacy_to_new = mappings["legacy_to_new"]
        self._system_prompt = _build_system_prompt(self._legacy_to_new)
        self._rule_grouping = True
        self._body_max_chars = 1000000
        logger.info("[MDB Checker] 初始化完成: model=%s, 规则数=%d", self._model, len(self._rules))

    def _call_llm(self, system: str, user: str) -> str:
        """调用 LLM，返回响应文本。"""
        user_len = len(user)
        system_len = len(system)
        logger.info("[MDB LLM] 开始调用 model=%s, system_prompt=%d字符, user_prompt=%d字符",
                     self._model, system_len, user_len)
        t0 = time.time()
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = self._llm.invoke(messages)
        elapsed = round(time.time() - t0, 2)
        resp_text = response.content.strip() if response.content else ""
        logger.info("[MDB LLM] 调用完成: 耗时=%.2fs, 响应=%d字符", elapsed, len(resp_text))
        return resp_text

    def _truncate(self, text: str) -> str:
        n = self._body_max_chars
        if len(text) <= n:
            return text
        half = n // 2
        return text[:half] + "\n\n... [中间省略] ...\n\n" + text[-half:]

    def _check_review_point_grouped(
        self,
        title: str,
        body: str,
        rules: list[dict[str, Any]],
        sibling_context: str = "",
    ) -> dict[str, Any]:
        """分批调用 LLM 检查评审点。"""
        t0 = time.time()
        batches = group_rules_for_check(rules) if self._rule_grouping else [("all", rules)]
        body_text = self._truncate(body or "")
        all_results: list[dict[str, Any]] = []
        group_errors: list[dict[str, str]] = []

        for batch_idx, (group_name, group_rules) in enumerate(batches, 1):
            rules_text = format_rules_for_batch(group_rules)
            user_prompt = BATCH_USER_PROMPT.format(
                rules_text=rules_text,
                title=title or "(no title)",
                body=body_text,
                num_rules=len(group_rules),
            )
            logger.info("[MDB 批次 %d/%d] 开始检查分组 '%s' (%d条规则), body=%d字符",
                         batch_idx, len(batches), group_name, len(group_rules), len(body_text))
            try:
                raw = self._call_llm(self._system_prompt, user_prompt)
                error = None
            except Exception as e:
                logger.warning("LLM group %s call failed: %s", group_name, e)
                raw = ""
                error = f"{type(e).__name__}:{e}"
                group_errors.append({"group": group_name, "error": error})

            if raw:
                parsed = parse_batch_result(raw, group_rules, self._legacy_to_new)
                logger.info("[MDB 批次 %d/%d] 分组 '%s' 解析完成: %d条结果", batch_idx, len(batches), group_name, len(parsed))
            else:
                parsed = [_make_error_result(r, error or "empty") for r in group_rules]
                logger.warning("[MDB 批次 %d/%d] 分组 '%s' LLM返回为空", batch_idx, len(batches), group_name)
            all_results.extend(parsed)

        order = {r["id"]: i for i, r in enumerate(rules)}
        results = sorted(
            _apply_false_positive_guard(all_results, body_text, sibling_context),
            key=lambda r: order.get(r["rule_id"], 9999),
        )
        total = len(results)
        compliant = sum(1 for r in results if r["compliant"])
        failed_blocking = [r for r in results if not r["compliant"] and is_blocking_severity(r["severity"])]
        warning_should = [r for r in results if not r["compliant"] and r["severity"] in WARNING_SEVERITIES]
        error = "; ".join(f"{e['group']}:{e['error']}" for e in group_errors) or None

        elapsed_total = round(time.time() - t0, 2)
        logger.info("[MDB 检查完成] 总耗时=%.2fs, 合规=%d/%d, 失败(shall)=%d, 警告=%d",
                     elapsed_total, compliant, total, len(failed_blocking), len(warning_should))

        return {
            "total_rules": total,
            "compliant_rules": compliant,
            "failed_rules": len(failed_blocking),
            "warning_rules": len(warning_should),
            "overall_compliant": len(failed_blocking) == 0,
            "compliance_rate": f"{compliant / total * 100:.1f}%" if total else "0.0%",
            "results": results,
            "failed_rule_ids": [r["rule_id"] for r in failed_blocking],
            "warning_rule_ids": [r["rule_id"] for r in warning_should],
            "elapsed_seconds": round(time.time() - t0, 2),
            "llm_error": error,
        }

    def check_review_point(self, title: str, body: str, sibling_context: str = "") -> dict[str, Any]:
        """对一篇评审帖正文执行批量规则检查。

        Returns:
            与 Redfish check_review_point_compliance() 对齐的结构：
            {
                total_checks_num, failed_checks_num, result, error_details,
                total_rules, compliant_rules, failed_rules, warning_rules,
                overall_compliant, compliance_rate
            }
        """
        logger.info("[MDB] check_review_point 入口: title='%s', body=%d字符", (title or "")[:50], len(body or ""))
        mdb_result = self._check_review_point_grouped(title, body, self._rules, sibling_context)

        # 构建 error_details（与 Redfish 对齐）
        model_validation = []
        warning_details = []
        for r in mdb_result.get("results", []):
            if r.get("error"):
                continue
            if not r.get("compliant", True):
                entry = {
                    "rule_id": r.get("rule_id", "N/A"),
                    "rule": f"[{r.get('rule_id')}] {r.get('category')} (规则合规性检查)",
                    "message": r.get("summary", "N/A"),
                    "advice": r.get("advice", "请参考 MDB 资源协作接口规范要求进行修复"),
                }
                if is_blocking_severity(r.get("severity")):
                    model_validation.append(entry)
                else:
                    entry["advice"] = f"severity='{r.get('severity')}' 建议性规则，建议修改以提升规范符合性"
                    warning_details.append(entry)

        return {
            "total_checks_num": mdb_result["total_rules"],
            "failed_checks_num": mdb_result["failed_rules"],
            "error_details": {
                "STATIC_VALIDATION": [],
                "MODEL_VALIDATION": model_validation,
                "WARNING_DETAILS": warning_details,
            },
            "result": "pass" if mdb_result["overall_compliant"] else "fail",
            "total_rules": mdb_result["total_rules"],
            "compliant_rules": mdb_result["compliant_rules"],
            "failed_rules": mdb_result["failed_rules"],
            "warning_rules": mdb_result["warning_rules"],
            "overall_compliant": mdb_result["overall_compliant"],
            "compliance_rate": mdb_result["compliance_rate"],
        }
