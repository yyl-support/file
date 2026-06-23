"""
Redfish 接口合规性检查器（批量优化版）
使用 LangChain + ModelScope API，一次性批量检查所有规则，大幅减少 API 调用次数
"""

# version: 1.0.31

import re
import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, List
from redfish_common import Config

# LangChain 导入
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ==================== 规则数据加载（外置 JSON）====================
# 规则数据已从代码中剥离，统一存放在 SchemaFiles/redfish_compliance_rules.json，
# 实现 prompt（位于本文件）与规则数据（数据文件）的解耦。
COMPLIANCE_RULES_FILE = Path(Config.SCHEMA_DIR) / "redfish_compliance_rules.json"


def _load_compliance_rules(path: Path = COMPLIANCE_RULES_FILE) -> List[Dict[str, Any]]:
    """从外置 JSON 加载 Redfish 合规性规则列表。

    JSON 顶层必须为数组；每条规则需包含 id/category/severity/rule/check/rationale。
    """
    if not path.exists():
        raise FileNotFoundError(
            f"未找到 Redfish 合规性规则文件：{path}。"
            f"请确认 SchemaFiles 目录下存在 redfish_compliance_rules.json。"
        )
    with open(path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    if not isinstance(rules, list) or not rules:
        raise ValueError(f"规则文件 {path} 必须是非空 JSON 数组")
    required_fields = {"id", "rule", "check"}
    seen_ids = set()
    for idx, item in enumerate(rules):
        if not isinstance(item, dict):
            raise ValueError(f"规则文件第 {idx} 条不是对象：{item!r}")
        missing = required_fields - set(item.keys())
        if missing:
            raise ValueError(f"规则 {item.get('id', f'#{idx}')} 缺少字段：{sorted(missing)}")
        rid = item["id"]
        if rid in seen_ids:
            raise ValueError(f"规则 id 重复：{rid}")
        seen_ids.add(rid)
    return rules


REDFISH_COMPLIANCE_RULES = _load_compliance_rules()


# ==================== RULE-001 前置内容替换 ====================
RULE_001_PREPROCESS_REPLACEMENTS = [
    ("SubsystemVenderID", "SubsystemVendorID"),
    ("VenderID", "VendorID"),
    ("Vender", "Vendor"),
    ("vender", "vendor"),
    ("InterChassAuthentication", "InterChassisAuthentication"),
    ("Smnp", "Snmp"),
]

_OPENUBMC_PLACEHOLDER = "XopenUBMCPlaceholderX"


def preprocess_content_for_rule001(text: str) -> str:
    """对评审点内容做 RULE-001 规避词前置替换。"""
    for old, new in RULE_001_PREPROCESS_REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace("openUBMC", _OPENUBMC_PLACEHOLDER)
    return text


def postprocess_results_for_rule001(results: List[Dict]) -> List[Dict]:
    """将 LLM 返回结果中的占位符还原为原始词汇。"""
    raw = json.dumps(results, ensure_ascii=False)
    raw = raw.replace(_OPENUBMC_PLACEHOLDER, "openUBMC")
    return json.loads(raw)


# ==================== RULE-001 静态补充检查 ====================
import re as _re

_TABLE_TYPE_PATTERNS = [
    (_re.compile(r'\|\s*\b(bool|Bool)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了非标准类型名 '{match}'，应改为规范关键字 'boolean'。",
     "将类型列中的 '{match}' 修改为 Redfish 规范要求的 'boolean'。"),
    (_re.compile(r'\|\s*\b(Boolean)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，Redfish 原始类型须为小写。",
     "将类型列中的 '{match}' 修改为小写 'boolean'。"),
    (_re.compile(r'\|\s*\b(String)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，Redfish 原始类型须为小写。",
     "将类型列中的 '{match}' 修改为小写 'string'。"),
    (_re.compile(r'\|\s*\b(Integer)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，Redfish 原始类型须为小写。",
     "将类型列中的 '{match}' 修改为小写 'integer'。"),
    (_re.compile(r'\|\s*\b(Number)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，Redfish 原始类型须为小写。",
     "将类型列中的 '{match}' 修改为小写 'number'。"),
    (_re.compile(r'\|\s*\b(Int)\b\s*[\|,\s]', _re.MULTILINE),
     "表格类型列使用了非标准类型名 '{match}'，应改为 'integer'。",
     "将类型列中的 '{match}' 修改为 'integer'。"),
]

_PROSE_BOOL_PATTERN = _re.compile(r'(?<![a-zA-Z])(bool|Bool)(?![eE])', _re.MULTILINE)

_TAB_TYPE_PATTERNS = [
    (_re.compile(r'\t(bool|Bool)\t', _re.MULTILINE),
     "表格类型列使用了非标准类型名 '{match}'，应改为 'boolean'。",
     "将类型列中的 '{match}' 修改为 'boolean'。"),
    (_re.compile(r'\t(Boolean)\t', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，应改为 'boolean'。",
     "将 '{match}' 修改为小写 'boolean'。"),
    (_re.compile(r'\t(String)\t', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，应改为 'string'。",
     "将 '{match}' 修改为小写 'string'。"),
    (_re.compile(r'\t(Integer)\t', _re.MULTILINE),
     "表格类型列使用了大写类型名 '{match}'，应改为 'integer'。",
     "将 '{match}' 修改为小写 'integer'。"),
    (_re.compile(r'\t(Int)\t', _re.MULTILINE),
     "表格类型列使用了非标准类型名 '{match}'，应改为 'integer'。",
     "将 '{match}' 修改为 'integer'。"),
]

_ODATA_TYPO_PATTERN = _re.compile(r'@data\.id', _re.IGNORECASE)

_ACTION_SPACE_PATTERN = _re.compile(
    r'\b([A-Z][a-zA-Z0-9]+)\.\s+([A-Z][a-zA-Z0-9]+)\b'
)

_URI_SEGMENT_PATTERN = _re.compile(
    r'/redfish/v1(?:/([^/\s{}\[\]]+))+', _re.IGNORECASE
)
_URI_LOWERCASE_WHITELIST = {'redfish', 'oem', 'openubmc', 'v1', '$metadata'}

_URI_TEMPLATE_DUP_PATTERN = _re.compile(r'\{(\w+?)(\1)+\}')

_KNOWN_WRONG_PLURALS = {
    # 注意：'Storages' 在 Redfish URI 中是合法资源名（如 /redfish/v1/Systems/{id}/Storages），不应判违规
    'Memorys': 'Memory',
    'Bioss': 'Bios',
    'Chassiss': 'Chassis',
    'Thermals': 'Thermal',
    'Powers': 'Power',
    'Assemblys': 'Assembly',
}

_KNOWN_TYPOS = [
    (_re.compile(r'(?<![a-zA-Z])(NetworkAdapterse)(?![a-zA-Z])'),
     "拼写错误 '{match}'，应为 'NetworkAdapters'。",
     "将 '{match}' 修正为 'NetworkAdapters'。"),
    (_re.compile(r'(?<![a-zA-Z])(Mangers)(?![a-zA-Z])'),
     "拼写错误 '{match}'，应为 'Managers'。",
     "将 '{match}' 修正为 'Managers'。"),
    (_re.compile(r'(?<![a-zA-Z])(Proccesor|Processer|Processsor)(?![a-zA-Z])', _re.IGNORECASE),
     "拼写错误 '{match}'，应为 'Processor'/'Processors'。",
     "将 '{match}' 修正为正确的拼写。"),
    (_re.compile(r'(?<![a-zA-Z])(Chasis)(?![a-zA-Z])'),
     "拼写错误 '{match}'，应为 'Chassis'。",
     "将 '{match}' 修正为 'Chassis'。"),
    (_re.compile(r'(?<![a-zA-Z])(Certifcate|Certiifcate|Certificte)(?![a-zA-Z])', _re.IGNORECASE),
     "拼写错误 '{match}'，应为 'Certificate'。",
     "将 '{match}' 修正为 'Certificate'。"),
    (_re.compile(r'(?<![a-zA-Z])(Eithernet|Etherntet)(?![a-zA-Z])', _re.IGNORECASE),
     "拼写错误 '{match}'，应为 'Ethernet'。",
     "将 '{match}' 修正为 'Ethernet'。"),
]

_ABBREV_PAIRS = [
    ('Comp', 'Component'),
    ('Auth', 'Authentication'),
    ('Config', 'Configuration'),
    ('Info', 'Information'),
    ('Mgmt', 'Management'),
    ('Cert', 'Certificate'),
    ('Addr', 'Address'),
    ('Temp', 'Temperature'),
    ('Proc', 'Processor'),
    ('Sys', 'System'),
]

_NONSTANDARD_RESOURCE_NAMES = {
    # 注意：'Temperature' 在新厂商扩展的 URI 中可能合法（如自定义传感器分组），不强制改为 'Thermal'
}


def static_postcheck_rule001(
    results: List[Dict],
    review_point_title: str,
    review_point_content: str,
) -> List[Dict]:
    """对 LLM 结果做 RULE-001 静态补充检查。

    扫描评审点原文，若发现 LLM 漏检的高频 RULE-001 违规模式，
    将 RULE-001 的 compliant 修正为 False 并补充 findings/advice。
    """
    combined_text = (review_point_title or '') + '\n' + (review_point_content or '')

    extra_findings: List[Dict[str, str]] = []
    seen_msgs: set = set()

    def _add(msg: str, adv: str) -> None:
        if msg not in seen_msgs:
            seen_msgs.add(msg)
            extra_findings.append({'message': msg, 'advice': adv})

    # 1a. 表格列非标准类型名（| 分隔）
    for pattern, msg_tpl, advice_tpl in _TABLE_TYPE_PATTERNS:
        m = pattern.search(combined_text)
        if m:
            matched = m.group(1)
            _add(msg_tpl.format(match=matched), advice_tpl.format(match=matched))

    # 1b. Tab 分隔表格非标准类型名
    for pattern, msg_tpl, advice_tpl in _TAB_TYPE_PATTERNS:
        m = pattern.search(combined_text)
        if m:
            matched = m.group(1)
            _add(msg_tpl.format(match=matched), advice_tpl.format(match=matched))

    # 1c. 正文中的 bool/Bool
    if _PROSE_BOOL_PATTERN.search(combined_text):
        m = _PROSE_BOOL_PATTERN.search(combined_text)
        matched = m.group(1)
        _add(
            f"正文中使用了非标准类型名 '{matched}'，Redfish 规范要求使用 'boolean'。",
            f"将 '{matched}' 修改为 'boolean'。"
        )

    # 2. @data.id 缺少 o
    if _ODATA_TYPO_PATTERN.search(combined_text):
        _add(
            "导航属性写成 '@data.id'，缺少字母 'o'，应为 '@odata.id'。",
            "将 '@data.id' 修正为 '@odata.id'。"
        )

    # 3. Action 名称点号后有空格
    for m in _ACTION_SPACE_PATTERN.finditer(combined_text):
        full = m.group(0)
        ns, act = m.group(1), m.group(2)
        if any(kw in combined_text for kw in ['Action', 'action', '/Actions/']):
            _add(
                f"Action 名称 '{full}' 点号后存在空格，不符合 PascalCase 规范。",
                f"将 '{full}' 修正为 '{ns}.{act}'（移除点号后的空格）。"
            )
            break

    # 4. URI 路径段小写检查
    for uri_match in _re.finditer(r'/redfish/v1/[^\s,;）)]*', combined_text):
        uri_str = uri_match.group(0)
        segments = uri_str.split('/')
        for seg in segments[3:]:
            if not seg or seg.startswith('{') or seg.startswith('$'):
                continue
            if seg.lower() in _URI_LOWERCASE_WHITELIST:
                continue
            if not seg.isalpha():
                continue
            if seg[0].islower() and not seg.startswith('v') and '_' not in seg:
                _add(
                    f"URI 路径段 '{seg}' 首字母小写，不符合 Redfish PascalCase 命名规范。",
                    f"将 URI 中的 '{seg}' 修改为 '{seg[0].upper() + seg[1:]}'。"
                )
                break

    # 5. URI 模板参数名重复
    for m in _URI_TEMPLATE_DUP_PATTERN.finditer(combined_text):
        full = m.group(0)
        _add(
            f"URI 模板参数 '{full}' 存在重复拼接错误。",
            f"修正 URI 模板参数 '{full}'。"
        )

    # 6. URI 中非标准复数形式
    for wrong, correct in _KNOWN_WRONG_PLURALS.items():
        if _re.search(r'/redfish/v1/.*/' + wrong + r'(?:/|\s|$)', combined_text):
            _add(
                f"URI 中使用了非标准资源名 '{wrong}'，Redfish 标准资源名为 '{correct}'。",
                f"将 URI 中的 '{wrong}' 修改为 '{correct}'。"
            )

    # 7. 常见拼写错误
    for pattern, msg_tpl, advice_tpl in _KNOWN_TYPOS:
        m = pattern.search(combined_text)
        if m:
            matched = m.group(1)
            _add(msg_tpl.format(match=matched), advice_tpl.format(match=matched))

    # 8. 属性名缩写不一致
    pascal_words = set(_re.findall(r'(?<![a-zA-Z])([A-Z][a-zA-Z]{3,})(?![a-zA-Z])', combined_text))
    for abbr, full in _ABBREV_PAIRS:
        abbr_names = [w for w in pascal_words if w.startswith(abbr) and not w.startswith(full)]
        full_names = [w for w in pascal_words if w.startswith(full)]
        if abbr_names and full_names:
            for an in abbr_names:
                suffix = an[len(abbr):]
                matching_full = [fn for fn in full_names if fn.endswith(suffix)]
                if matching_full:
                    _add(
                        f"属性名 '{an}' 使用了缩写 '{abbr}'，与同文档中的 '{matching_full[0]}' 不一致。",
                        f"将 '{an}' 修改为 '{matching_full[0]}' 以保持命名一致性。"
                    )

    # 9. URI 中非标准 Redfish 资源名
    for wrong_name, (correct_name, desc) in _NONSTANDARD_RESOURCE_NAMES.items():
        pattern = _re.compile(r'/redfish/v1/[^/\s]*/[^/\s]*/' + wrong_name + r'(?:/|\s|$|#)')
        if pattern.search(combined_text):
            _add(
                f"URI 中使用了非标准资源名 '{wrong_name}'。{desc}。",
                f"将 URI 中的 '{wrong_name}' 修改为 '{correct_name}'。"
            )

    if not extra_findings:
        return results

    for r in results:
        if r.get('rule_id') == 'RULE-001' and r.get('compliant', False):
            all_msgs = [f['message'] for f in extra_findings]
            all_advices = [f['advice'] for f in extra_findings]
            r['compliant'] = False
            r['summary'] = '静态补充检查发现命名规范违规：' + '；'.join(all_msgs)
            r['advice'] = ' '.join(all_advices)
            existing = r.get('findings', [])
            if isinstance(existing, list):
                existing.extend(all_msgs)
            else:
                r['findings'] = all_msgs
            break

    return results


def create_llm(model: str = None, temperature: float = 0.1):
    """创建 LLM 实例，配置从 Config 类读取（来源 config.yaml）"""
    return ChatOpenAI(
        model=model or Config.MODELSCOPE_MODEL,
        api_key=Config.MODELSCOPE_API_KEY,
        base_url=Config.MODELSCOPE_BASE_URL,
        temperature=temperature,
        max_tokens=262144,
        timeout=900,
        max_retries=2,
    )


# ==================== 批量规则检测 ====================

# 优化：批量检查的系统提示
BATCH_CHECK_SYSTEM_PROMPT = """你是一位 Redfish 接口规范专家。你的任务是检查给定的 Redfish 评审点内容是否符合所有规则要求。

## 语言要求（强制）

- 所有自然语言字段（包括 `summary`、`advice`、`findings.message`、`findings.evidence`、`findings.location` 等）**必须使用简体中文**输出。
- **严禁**出现整段英文 `summary` 或 `advice`；即便输入评审点为纯英文，也必须用中文撰写解释与建议。
- 英文术语（OData 关键字、HTTP 方法、属性名、URI 段、JSON 片段、报错原文等）**保持原文**嵌入中文句子中，不要翻译这些标识符；JSON 的字段名与 `compliant`/`true`/`false` 等枚举值同样保持原样。

## 检查方法

1. 仔细阅读评审点内容（资源描述）
2. 根据每条规则逐一检查评审点内容是否符合规范
3. 判断每条规则是否符合
4. 对于不符合的规则，**必须提供具体的修改建议**

## 检查原则

**【核心原则】只检查评审点content内容，不检查LLM生成的URI示例或响应！**

规则检查的目标是评估评审点规范本身是否合规，而不是评估LLM生成的实现是否正确。LLM生成的URI示例可能有错误，这不应该影响对评审点规范合规性的判断。

**总体原则：当评审点内容存在以下情况时，应判定为不合规（compliant=false）：**
- 明确违反了规则中明确禁止的行为
- 缺少规则中明确要求的元素
- 描述不清可能导致实现歧义

**特别注意事项：**
- **【重要】RULE-001 命名规范检查的特殊规则**：
  - RULE-001 检查：a)属性名是否符合 PascalCase 格式（首字母大写驼峰命名）；b)**物理量属性名是否包含标准单位后缀**（见下方标准单位后缀表）；c)**拼写错误检查**（包括属性名、类型名、URI参数名等所有命名的拼写，拼写检查由RULE-001负责，RULE-004不检查拼写）；d)**【重要】Redfish 原始类型名大小写检查**：评审点表格的「数据类型」列中出现的 Redfish 原始类型名（string、boolean、integer、number、array、object、null）必须使用小写形式。如果出现大写开头的类型名（如 String、Boolean、Integer、Number、Array、Object、Bool、Int 等），这是拼写/大小写错误，必须标记为违规
  - **标准单位后缀表**（这些后缀都是符合规范的）：
    - 功率：**Watts**（**PowerWatts、ConsumedPowerWatts、PowerAverageWatts、PowerPeakWatts** 都是合规的，Watts 是标准功率单位后缀）
    - 电压：Volts（ReadingVolts、VoltageVolts）
    - 电量：kWh（EnergykWh）
    - 温度：Celsius（TemperatureCelsius）
    - 压力：kPa、Pa（PressurekPa、DeltaPressurekPa）
    - 转速：RPM（RotationSpeedRPM）
    - 带宽：Mbps、Gbps（PortSpeedMbps、LinkSpeedGbps）
    - 频率：MHz、GHz（ProcessorSpeedMHz）
    - 时间：Milliseconds、Seconds、Minutes、Hours、Days、Weeks、Months、Years
    - 数据量：Bytes、KiB、MiB、GiB、TiB（MemoryBytes、MemorySizeMiB、TotalCapacityGiB）
    - 百分比：Percent、Percentage（PowerLoadPercent、TaskPercentage）
    - 计数：Count（ProcessorCount、DriveCount）
    - 状态：State、Status、Mode（PowerState、HealthStatus、OperationMode）
  - RULE-001 **绝对不检查**：**语义清晰性、具体性或描述是否充分**（如 Type、Content、Value、Stage、Status、Name 等通用名称只要符合PascalCase就是合规的，RULE-001不检查名称是否语义清晰、具体、是否容易混淆、是否足够描述性等问题。即使名称是"Stage"这样可能被认为不够描述性的名称，只要符合PascalCase格式，就不应标记为违规）；**标准Redfish Schema中已定义的属性名**：如ConsumedPowerWatt（标准ProcessorMetrics Schema属性）等，即使其单位后缀使用单数形式（Watt而非Watts）也不应标记为违规。RULE-001只检查新增或修改的自定义属性
  - **例外（不检查PascalCase）**：a)**Action请求参数、函数参数、URL查询参数**（如filepath、protocol、biosactivemode、systemid、managerid、timeout、supply_source_value、ForceUpdate、ImageUri、TransferProtocol等）：这些不是资源属性名，RULE-001**完全不检查**Action请求参数的命名格式。无论 Action 请求参数使用任何命名格式——下划线（supply_source_value）、全小写、camelCase（首字母小写驼峰）、PascalCase（首字母大写驼峰）还是其他格式——RULE-001 都不检查，也不会建议修改。**即使Action请求参数在表格中列出，也不应判定为违规**；b)包含特殊符号的表达式（Members[{、}]、[0]、.key、Slot.Lanes、PCIeDevice.Lanes、**SPDM{、Issuer{、Subject{、Oem.{**等）；这些符号用于表示数组元素、对象属性引用、嵌套结构或Schema格式，不是属性名本身的问题，RULE-001不检查；c)完全大写的缩写（ID、URI、HTTP、SNMP等）；d)**特定词汇**（openUBMC、Smnp、InterChassAuthentication）；e)**vender拼写**：`vender`是项目中`vendor`的有效拼写变体，与`vendor`等同，包含`Vender`的属性名（如VenderID、SubsystemVenderID、VenderType）是合规的，不应被标记为拼写错误；f)单位前缀正确使用（k小写、M/G/T大写，如EnergykWh、EnergyMB、FrequencyMHz、PortSpeedGbps）；g)单位后缀大小写灵活（SpeedRpm/SpeedRPM、TemperatureCelsius/TemperatureCELSIUS）；h)**标准Redfish Schema中已定义的属性名**：**ConsumedPowerWatt是标准Redfish ProcessorMetrics Schema中定义的属性**（已deprecated，但仍然是标准属性），即使它使用单数Watt而非复数Watts，也不应标记为违规。RULE-001只检查**新增或修改的自定义属性**是否符合命名规范，标准Schema中已存在的属性名（无论是否符合命名规范）都不应被检查
  - **interval/period/duration/timeout属性的单位后缀规则**：包含**Interval/Period/Duration/Timeout等时间相关词根**的属性**可以使用单位后缀**来明确表示时间单位，如 CurrentPollingIntervalInSeconds、UpdateIntervalInMilliseconds、RetryPeriodInSeconds、EstimatedDurationInMinutes、EjectTimeoutInMilliseconds 等。**这些带单位后缀的属性名都是合规的**，且是推荐的做法（明确时间单位）。不带单位后缀的 interval 属性名（如 CurrentPollingInterval、UpdateInterval）也是合规的。
  - **不需要单位后缀的属性类型**：a)包含Count/Number的计数属性（ProcessorCount、DriveCount）；b)包含State/Status/Mode的状态属性（PowerState、HealthStatus、OperationMode）；c)包含Percent/Percentage的百分比属性（TaskPercentage、UtilizationPercentage）；d)无量纲属性（StatusCode、Ratio）
  - **使用标准单位后缀（包括复合单位）的属性名是合规的**：DeltaPressurekPa（kPa千帕）、EnergykWh（kWh千瓦时）、ProcessorSpeedMHz（MHz兆赫）、CurrentSpeedGbps（Gbps吉比特每秒）、PortSpeedMbps（Mbps兆比特每秒）、LocalMemoryBandwidthBytes（Bytes字节）、TotalMemoryBytes（Bytes字节）、MemorySizeMiB（MiB兆字节）等都是符合规范的。**任何使用Gbps、Mbps、kPa、kWh、MHz、GHz、Bytes、KiB、MiB、GiB、TiB等标准单位后缀的属性名都不应被标记为违规**。**特别注意：Bytes是标准的字节单位后缀，任何以Bytes结尾的属性名都是符合规范的**。**绝对不要将Bytes错误地解析为By，Bytes本身就是一个完整的单位后缀，不能拆分**
  - **RULE-001 不检查 URI 格式结构问题**：URI 格式结构问题（如缺少 v1 层级、路径分隔符错误）由 RULE-004 负责检查。但 **URI 中的拼写/命名问题由 RULE-001 负责**，包括：a)**URI 路径段的大小写问题**（如 /redfish/v1/systems 中的 systems 应为 Systems）；b)**URI 路径段的拼写错误**（如 /redfish/v1/Systm 中的 Systm 应为 System）。**【重要例外：Storages 和 Storage 都是合法的】**：Storages 作为存储资源的复数形式，在任何 URI 深度都是合法的（如 `/redfish/v1/Systems/{id}/Storages/{id}`）。Storage 和 Storages 混用也不违规。**不要将 Storages 标记为需要改为 Storage 的违规**。RULE-004 只检查 URI 格式结构，不检查拼写/命名。
  - RULE-001 不检查units标注的具体内容（如属性名包含Bytes，不应检查其units标注是否为"Bytes"），units标注是属性说明的一部分，不是属性名命名规范的一部分；**units 列中的 By、B 与 Bytes 均表示字节含义，不得将 By 判为拼写错误**
  - **【⚠️ RULE-001 易漏检清单 — 必须逐项核对】**：❶ 类型列有 `bool`/`Bool`/`Boolean`/`String`/`Integer`/`Number` 等非小写类型名？❷ 属性名有 camelCase（首字母小写如 `fanMode`/`bootOrder`）？❸ JSON 示例中 `state`/`health` 首字母小写？❹ Action 名称点号后空格（如 `Power. SetPsu`）？❺ `@data.id`（少 `o`）？❻ 拼写错误（`NetworkAdapterse`/`Certifacates`）？❼ 属性名缩写不一致？❽ URI 路径段小写（如 `/storage/`）？
- **【重要】RULE-012 敏感信息检查的特殊规则**：
  - RULE-012 允许：通用厂商名（如Nvidia、Intel、AMD）用于示例说明；存储语境下的 **PMC、RAID、HBA** 等通用技术词（无具体型号/料号）不视为敏感型号
  - RULE-012 不违规：a)仅使用通用厂商名；b)示例性质的描述；c)PMC/RAID/HBA 等未绑定具体型号时
  - RULE-012 违规：a)具体专有型号；b)内部项目代号；c)定制型号
- **【重要】RULE-010 数据类型规范检查的特殊规则**：
  - RULE-010 检查：**只检查类型与示例值的一致性**：声明的类型与示例值/枚举值的数据类型是否一致；**特别注意integer与number的区别以及JSON格式**：integer类型必须是整数且不能加引号（如1、100、0，写成"1"是错误的字符串格式）；number类型可以是整数或小数且不能加引号（如1、1.5、100.75，写成"1.5"是错误的字符串格式）；string类型必须加引号（如"GPU1"）；如果类型声明为integer/number但示例值加了引号（字符串格式）或示例值是小数（仅针对integer），则RULE-010违规
  - RULE-010 也检查：**类型声明的语义正确性**：是否符合Redfish Schema的语义要求（如TrustedComponents根据Redfish Schema应为array，如果声明为string则违规）
  - **例外情况**：a)当示例值为"/"时，跳过该属性的类型一致性检查（"/"常用于表示路径分隔符或默认路径）；b)**duration类型属性可以声明为string或duration**：如EstimatedDuration、EjectTimeout等包含Duration/Timeout等时间词根的属性，可以声明为string类型（因为duration用ISO8601格式字符串表示，如PT1H），也可以声明为duration类型，两者都是合规的
  - **RULE-010 绝对不检查：类型名的拼写或大小写问题**（如interger、String、Boolean等由RULE-001负责）；属性名单位后缀、单位标注等命名相关问题（由RULE-001负责）
  - RULE-010 不检查：**类型名的拼写或大小写**（如interger应为integer、String应为string、Boolean应为boolean等，这些都是拼写/大小写问题，由RULE-001负责）；属性名的单复数形式（由RULE-001负责）；属性名的PascalCase格式（由RULE-001负责）；**属性名拼写相关问题**（由RULE-001负责）；**枚举（enum）类型的属性类型正确性**（只有明确声明为enum/枚举类型时，由RULE-008负责）；Schema内部的引用问题（如$ref、anyOf等）；示例值是否在枚举范围内
  - 示例1：表格说"BandwidthPercent: integer"但示例值为"1"（字符串格式）或45.5（小数）→ 类型声明为integer但示例值是字符串或小数，RULE-010违规 ✗（正确格式应为"BandwidthPercent": 1）
  - 示例2：表格说"PhysicalContext: string, 枚举值: [PowerSupply]"，Schema示例值为"test" → "test"是字符串，与string类型一致 → RULE-010合规 ✓
  - 示例3：表格说"TrustedComponents: string" → 根据Redfish Schema应为array，但声明为string → RULE-010违规 ✗
  - 示例4：表格说"Target: string, value: \"/\"" → 示例值为"/"，跳过RULE-010类型一致性检查 ✓
  - 示例5：表格说"EstimatedDuration: string"或"EjectTimeout: duration" → duration相关属性可以声明为string或duration类型，都是合规的 ✓
  - 绝对不要检查：a)Schema中的$ref、anyOf等引用问题；b)示例值是否在枚举范围内；c)**Schema中的patternProperties**：patternProperties是用于匹配动态属性名（如@odata.id、@Redfish.Deprecated等Oem扩展属性）的模式匹配规则，其类型数组（如["array","boolean","number","null","object","string"]）表示允许匹配的扩展属性可以是这些类型之一，这**不是**具体属性的类型定义。**不要将patternProperties中的类型数组误判为具体属性的类型定义问题**，具体属性的类型由其自身的type字段或$ref引用的定义决定。这不是RULE-010的检查范围！
- **【重要】RULE-008 枚举设计检查的特殊规则**：
  - RULE-008 检查：**只检查评审点或Schema明确声明为enum/枚举类型的属性**。只有当属性被明确声明为enum/枚举类型时，RULE-008才检查其类型是否为string
  - RULE-008 不检查：**普通string类型的取值范围**。如果评审点只是说明string类型的取值范围（如取值可为"Disabled"、"Enabled"、"Ethernet"），这只是取值说明，不是枚举类型，RULE-008不检查
  - RULE-008 不检查：**Schema中定义的类型**。如果Schema定义某属性为boolean或anyOf允许boolean，评审点如实记录Schema的定义不应被标记为违规
  - RULE-008 重点：只检查真正的枚举（enum）类型，不检查普通string类型的取值范围说明
- **【重要】RULE-013 Unknown枚举值描述检查的特殊规则**：
  - RULE-013 检查的是：Unknown枚举值本身的含义描述
  - RULE-013 合格描述包括：a)说明Unknown代表的状态（如"Unknown通信丢失或故障等无法及时获取到状态"）；b)说明返回Unknown的条件；c)说明属性可见性（如"硬件不支持时不显示"也有效）
  - 以下描述都是合格的："Unknown通信丢失或故障等无法及时获取到状态"、"Unknown未知，硬件不支持的场景不显示"、"当设备状态无法确定时返回Unknown"→这些都是有效的Unknown值说明
- **【重要】RULE-004 URI资源连通性与路径规范检查**：
  - **【核心职责区分】RULE-004 vs RULE-001**：
    - **RULE-004 只检查 URI 格式结构问题**：如缺少 v1 层级、路径分隔符错误、路径层级结构错误等
    - **RULE-001 负责 URI 中的拼写/命名错误**：如 PascalCase 大小写错误（systems vs Systems）、复数形式错误（）、拼写错误（Systm vs System）等
    - **RULE-004 绝对不检查**：URI 中的大小写、复数形式、拼写等问题，这些都属于 RULE-001 的职责
  - **检查范围**：只检查**已有/修改的标准资源**的URI格式，**不检查新增标准资源**
  - RULE-004 检查两个维度：1)评审点是否提供了URI或路径信息；2)URI格式结构是否正确
  - **URI存在性**：如果评审点提供了完整的资源URI（如"资源URI: /redfish/v1/Managers/manager_id/EnergySavingService"），则判定为合规；完全没有提供任何URI或路径信息时，判定为违规
  - **URI格式检查**（RULE-004 的核心职责）：只检查以下 URI 格式结构问题：
    - **缺少 v1 层级**：URI 应该是 /redfish/v1/... 而不是 /redfish/...
    - **路径分隔符错误**：应该使用 / 而不是 \\
    - **路径层级结构**：至少应该有 /redfish/v1/{ServiceRoot} 的基本结构
    - **第4层及更深的层级不进行检查**（允许任意自定义资源名称）
  - **RULE-004 不检查的内容（这些由 RULE-001 负责）**：
    - ❌ **大小写问题**：如 /redfish/v1/systems（systems 小写）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **复数形式问题**：如 /redfish/v1/systems（应为 Systems）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **拼写问题**：如 /redfish/v1/Systm（Systm 拼写错误）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **PascalCase 格式问题**：如 /redfish/v1/systems/managerid（大小写不符合 PascalCase）→ 这是 RULE-001 的拼写/命名检查
  - RULE-004 允许：a)Oem扩展路径；b)新增资源有说明；c)语义化的资源名称（如Temperature、Power、Voltage、Fan、Thermal、PowerSupply、Drive等）；d)**新增标准资源**（评审点标题或内容明确说明是新增、添加标准资源）；e)**第4层及更深层级**的任何资源名称；f)**URI参数使用冒号格式:managerid或花括号格式{managerid}**；g)**评审点明确说明和解释的 URI 设计格式**（如评审点说明采用\"协议名+ID\"的命名模式，如Snmp1、Syslog1、Smtp1等，这是有设计说明的格式，不应判定为违规）；h)**厂商自定义的资源ID命名格式**，只要评审点提供了明确的命名规则说明；i)**URI 中的大小写、复数形式、拼写等问题**（这些由 RULE-001 负责，RULE-004 不检查）
  - RULE-004 违规示例（只检查格式结构问题）：
    - ❌ 缺少 v1 层级：/redfish/Systems → 应为 /redfish/v1/Systems
    - ❌ 路径分隔符错误：\\redfish\\v1\\Systems → 应使用 /
    - ❌ 路径结构不完整：/redfish → 缺少 v1 和 ServiceRoot
  - **重点**：RULE-004 只检查 URI 格式结构问题（缺少v1、分隔符错误、层级结构错误）。URI 中的大小写、复数形式、拼写等问题完全由 RULE-001 负责，RULE-004 绝不检查。对于新增标准资源，不进行RULE-004检测。
- 如果评审点提到了属性名或URI，要检查是否符合规范
- **对于 severity="must" 的规则**：即使评审点没有提到某些必需元素，也应检查是否存在这些必需元素。如果评审点描述了一个资源但缺少必需字段（如@odata.id、Id、Name等），应判定为不合规
- **对于 severity="should" 的规则**：如果评审点没有提到相关元素，不判定为违规（只检查提到的内容）
- 常见缩写（TX/RX/LED/UUID/GUID/Comp/Max/Min等）保持大写是符合规范的

## 【特别强调】RULE-004 与 RULE-001 的绝对职责划分

**务必严格遵守以下职责划分，任何混淆都将导致检查结果错误！**

### RULE-004 的绝对禁区（绝对不能检查的内容）

RULE-004 **绝对禁止**检查以下内容，这些**完全**由 RULE-001 负责：

| 禁止检查的内容 | 示例 | 负责规则 |
|--------------|------|---------|
| URI 路径段的大小写 | /redfish/v1/systems（systems 应为 Systems） | RULE-001 |
| URI 路径段的复数形式 |  | RULE-001 |
| URI 路径段的拼写错误 | /redfish/v1/Systm（Systm 应为 System） | RULE-001 |
| URI 参数的命名格式 | /redfish/v1/Systems/:managerid（managerid 大小写） | RULE-001 |
| PascalCase 格式问题 | 任何关于"是否符合PascalCase"的判断 | RULE-001 |
| 资源名称的语义问题 | 如"名称不够描述性"、"容易混淆"等 | RULE-001 |

**RULE-004 只能检查以下格式结构问题**：
1. 是否缺少 v1 层级（/redfish/Systems 缺少 v1）
2. 路径分隔符是否正确（\\ vs /）
3. 路径层级结构是否完整

### RULE-001 的职责（包括 URI 中的拼写/命名）

RULE-001 **必须检查**以下内容：
1. 资源属性名是否符合 PascalCase
2. URI 路径段的大小写、拼写、复数形式
3. 所有命名的拼写错误（属性名、类型名、URI 参数名等）

### 检查时的判断标准

当检查 RULE-004 时，如果问题涉及以下关键词，**必须**判定为 RULE-001 的职责，RULE-004 **不能**标记为违规：
- "PascalCase"、"大小写"、"复数形式"、"拼写"、"命名格式"
- "首字母大写"、"小写"、"复数"、"单数"
- "systems"、"Processors" 等具体命名问题

**RULE-004 的 summary 绝对不能包含**：
- "PascalCase"、"大小写"、"复数"、"拼写"、"命名"等关键词
- 任何关于命名格式的判断或建议

**【新增资源判断示例】**

以下是明确的新增资源，RULE-004 **必须判定为合规（compliant=true）**：

| 评审点内容示例 | 是否新增资源 | RULE-004 判定 |
|--------------|------------|-------------|
| "新增 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "添加 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "扩展 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "创建 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "新增 ThermalEquipment 相关资源集合" | 是 | 合规（compliant=true） |
| "属于redfish接口获取ThermalEquipment相关资源集合信息" | 是 | 合规（compliant=true） |
| "在 /redfish/v1 下新增 Ports 资源" | 是 | 合规（compliant=true） |
| "添加 Snmp1 资源" | 是 | 合规（compliant=true） |

**判断方法**：如果评审点标题或内容中包含以下任一情况，即判定为新增资源：
- 中文关键词：新增、添加、扩展、创建、提供、包含、属于...接口
- 英文关键词：New、Add、Extend、Create、Provide、Include、...related resources
- URI 在 /redfish/v1 下但不是标准服务根节点（如 /redfish/v1/ThermalEquipment）

**重要**：对于新增资源，RULE-004 只检查是否包含 /redfish/v1/ 层级，只要包含 v1 层级就合规，不再检查第3层是否为标准服务根节点。

如果评审点的 URI 存在命名格式问题（如 systems），RULE-004 应该判定为 **合规（compliant=true）**，因为这是 RULE-001 的职责。

## 输出格式

**【最高优先级】仅输出 JSON**：你的完整回复必须且仅能是一个 JSON 数组——第一个非空白字符必须是 `[`，最后一个非空白字符必须是 `]`。不要在 JSON 前后输出说明文字、标题或 Markdown 代码围栏；若需思考请在内心完成，最终只输出可被 `json.loads` 直接解析的数组。

请严格按以下 JSON 格式输出**所有规则的检测结果**（注意：输出一个 JSON 数组，包含所有规则的检查结果）：

```json
[
  {{
    "rule_id": "RULE-001",
    "rule_category": "必需属性",
    "rule_description": "所有 Redfish 资源必须包含 @odata.id、@odata.type、Id、Name 属性",
    "compliant": true,
    "severity": "must",
    "findings": [
      {{
        "property": "@odata.id",
        "status": "pass",
        "expected": "必须存在",
        "actual": "已存在",
        "message": "属性存在，符合要求"
      }}
    ],
    "summary": "所有必需属性都存在，符合规范要求",
    "advice": null
  }},
  {{
    "rule_id": "RULE-002",
    "rule_category": "命名规范",
    "rule_description": "所有属性名必须使用 PascalCase",
    "compliant": false,
    "severity": "must",
    "findings": [
      {{
        "property": "customProperty",
        "status": "fail",
        "expected": "PascalCase 格式",
        "actual": "camelCase 格式",
        "message": "属性名不符合 PascalCase 规范"
      }}
    ],
    "summary": "发现属性 customProperty 使用了 camelCase，不符合 PascalCase 规范",
    "advice": "将 customProperty 修改为 CustomProperty，确保属性名首字母大写"
  }}
]
```

### 修改建议(advice)的要求

**当 compliant=false 时，必须提供 advice 字段，建议应具体可执行：**

1. **具体指向问题位置**：明确指出哪个属性或哪段代码有问题
2. **提供修改方案**：给出具体的修改示例或修改步骤
3. **引用规范依据**：必要时引用 Redfish 规范的具体条款

**advice 示例格式：**

| 问题类型 | advice 示例 |
|---------|------------|
| 缺少必需属性 | "添加 Id 属性：\"Id\": \"GraphicsController1\"" |
| 属性名不符合规范 | "将 customProperty 修改为 CustomProperty" |
| 属性值类型错误 | "将 Name 的值从数字 1 改为字符串 \"GraphicsController\"" |
| 缺少 @odata.id | "添加 @odata.id: \"/redfish/v1/Systems/1/GraphicsControllers\"" |
| OEM 扩展位置错误 | "将 customField 移至 Oem.OemPropertyName 路径下" |
| 单位缺失 | "在 PowerConsumption 属性值后添加单位：\"120 Watts\"" |

**当 compliant=true 时，advice 设为 null。**

### 重要说明
1. **必须返回所有规则的检查结果**，不要遗漏任何规则
2. 输出格式必须是 JSON 数组
3. 每个结果对象必须包含 rule_id 字段，且必须与输入的规则 ID 对应
4. findings 数组包含所有相关的检查点
5. summary 是对该规则检查的总体评价（1-2句话）
6. **compliant=false 时必须提供具体可执行的修改建议**
7. **【关键】RULE-004 新增资源豁免**：
   - 如果评审点明确说明是新增资源（标题或内容包含"新增"、"添加"、"扩展"、"创建"、"New"、"Add"、"Extend"、"Create"等关键词），RULE-004 **必须**判定为合规（compliant=true）
   - 新增资源的 URI 可以是任何合理的设计，如 /redfish/v1/ThermalEquipment、/redfish/v1/Snmp1 等
   - 不要对新增资源的 URI 结构进行限制，只要包含 /redfish/v1/ 层级即可
8. **【关键】compliant 字段必须与 summary 内容一致**：
   - **compliant=true**：summary 必须是正面的、肯定的表述，如"符合规范"、"满足要求"、"通过"、"无问题"等
   - **compliant=false**：summary 必须指出具体问题，如"不符合"、"缺少"、"未包含"、"格式错误"等
   - **禁止不一致情况**：
     - ❌ compliant=true 但 summary 说"不符合"、"有错误"
     - ❌ compliant=false 但 summary 说"符合规范"、"满足要求"、"URI格式正确"
   - 如果 summary 说"符合规范"或"满足要求"，compliant **必须**是 true
   - 如果 summary 说"不符合"或"存在问题"，compliant **必须**是 false
9. **summary 表述规范**：
   - 当 compliant=true 时，使用肯定的、清晰的表达，如："评审点中的属性命名符合规范"、"所有属性名均符合 PascalCase 要求"
   - 避免使用双重否定或模糊表达，如："未包含不符合"、"没有发现问题"
   - 当 compliant=false 时，直接指出问题，如："属性名 sensorValue 不符合 PascalCase 规范"
   - **特别注意**：如果评审点内容中已经明确说明"符合规范"、"使用正确"等表述，在 summary 中应直接引用评审点的表述，如"评审点已明确说明状态码使用符合规范"，而不是写成"检测到状态码符合规范"
   - 当评审点明确说明某个实践符合规范时，summary 应表述为"评审点已说明XX符合规范要求"而非"检测到XX符合规范"

10. **【关键】RULE-004 新增资源判断标准（必须遵守）**：
    - **第一步：判断是否为新增资源**
      - 如果评审点标题或内容包含以下任一关键词，即判定为新增资源：
        - 中文：新增、添加、扩展、创建、提供、包含、属于...接口、获取...资源集合
        - 英文：New、Add、Extend、Create、Provide、Include、...related resources、...collection
      - 例如："新增 ThermalEquipment 资源"、"属于redfish接口获取ThermalEquipment相关资源集合信息"
    - **第二步：如果是新增资源**
      - RULE-004 **必须**判定为 **合规（compliant=true）**
      - summary 应该是："评审点为新增资源，URI 格式符合新增资源要求" 或类似表述
      - **绝对不要**说："ThermalEquipment 不应作为第3层资源"、"Ports 应为单数 Port" 等标准资源判断
    - **第三步：如果不是新增资源（已有/修改的标准资源）**
      - 才检查 URI 格式结构问题（缺少 v1、分隔符错误）
"""

# 优化：批量检查的用户提示模板
BATCH_CHECK_USER_PROMPT = """请检查以下 Redfish 接口响应是否符合所有规则：

---

## 待检查的所有规则

{rules_text}

---

## 待检查的 Redfish 响应

**URI**: {uri}
**资源类型**: {resource_type}

**响应内容**:
```json
{payload}
```

---

请对每条规则进行检查，返回包含所有规则检测结果的 JSON 数组。注意：
1. 数组中每个元素对应一条规则的检查结果
2. 必须包含所有 {num_rules} 条规则的检查结果
3. rule_id 必须与上述规则列表中的 ID 完全对应
4. **对于不符合规则的项(compliant=false)，必须提供具体的修改建议(advice)**
5. **【特别提醒】RULE-004 新增资源豁免**：如果评审点标题或内容包含"新增"、"添加"、"扩展"、"创建"、"New"、"Add"、"Extend"、"Create"等关键词，说明这是新增资源，则 RULE-004 **必须**判定为合规（compliant=true），任何 URI 设计都是允许的。
6. **【特别提醒】RULE-004 只检查 URI 格式结构问题**：RULE-004 只检查 URI 格式结构问题（缺少v1层级、分隔符错误），不检查命名格式问题（PascalCase、大小写、拼写等由 RULE-001 负责）。
7. **【输出】正文只能是合法 JSON 数组**，不要包裹在 \\\`\\\`\\\` 代码块中，不要在 JSON 外写任何字符。"""


def format_rules_for_batch(rules: List[Dict]) -> str:
    """将规则列表格式化为批量检查的文本格式"""
    rules_text = ""
    for i, rule in enumerate(rules, 1):
        # 使用 str() 转换并转义可能的格式化字符
        rule_id = str(rule.get('id', ''))
        category = str(rule.get('category', ''))
        severity = str(rule.get('severity', ''))
        rule_desc = str(rule.get('rule', '')).replace('{', '{{').replace('}', '}}')
        check_point = str(rule.get('check', '')).replace('{', '{{').replace('}', '}}')
        rationale = str(rule.get('rationale', '')).replace('{', '{{').replace('}', '}}')

        rules_text += f"""
**规则 {i}**
- ID: {rule_id}
- 类别: {category}
- 严重程度: {severity}
- 规则描述: {rule_desc}
- 检查要点: {check_point}
- 规则理由: {rationale}

"""
    return rules_text


def extract_top_level_json_array(text: str) -> Optional[str]:
    """从文本中提取与首个 `[` 配平的顶层 JSON 数组子串（避免 rfind 截断嵌套内容失败）。"""
    start = text.find("[")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    quote_char = ""
    for i in range(start, len(text)):
        c = text[i]
        if in_string:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote_char:
                in_string = False
            continue
        if c in ('"', "'"):
            in_string = True
            quote_char = c
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def repair_json_text(s: str) -> str:
    """常见 LLM 输出修复：BOM、弯引号、尾逗号。"""
    t = (
        s.replace("\ufeff", "")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )
    prev = None
    while prev != t:
        prev = t
        t = re.sub(r",\s*}", "}", t)
        t = re.sub(r",\s*]", "]", t)
    return t


def extract_markdown_json_fence(text: str) -> Optional[str]:
    """提取 ```json ... ``` 或首个 ``` ... ``` 代码块内容。"""
    for opener in ("```json", "```JSON", "```Json"):
        idx = text.find(opener)
        if idx >= 0:
            start = idx + len(opener)
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
    return None


def _try_parse_rule_results(raw: str, rules: List[Dict]) -> Optional[List[Dict]]:
    """尝试将字符串解析为规则结果列表并校验。"""
    chunks: List[str] = []
    stripped = raw.strip()
    if stripped:
        chunks.append(stripped)
        chunks.append(repair_json_text(stripped))
    extracted = extract_top_level_json_array(raw)
    if extracted:
        chunks.append(extracted)
        chunks.append(repair_json_text(extracted))
    seen = set()
    for chunk in chunks:
        if not chunk or chunk in seen:
            continue
        seen.add(chunk)
        try:
            data = json.loads(chunk)
            if isinstance(data, list):
                return validate_and_fix_results(data, rules)
        except json.JSONDecodeError:
            continue
    return None


def parse_batch_check_result(response_text: str, rules: List[Dict]) -> List[Dict]:
    """解析批量规则检测结果

    Args:
        response_text: LLM 返回的响应文本
        rules: 原始规则列表，用于验证和补全

    Returns:
        解析后的结果列表
    """
    if not response_text:
        return [create_error_result(rule, "Empty response") for rule in rules]

    cleaned_text = response_text.strip()

    tried: List[str] = [cleaned_text]
    fence = extract_markdown_json_fence(cleaned_text)
    if fence:
        tried.append(fence)

    for candidate in tried:
        parsed = _try_parse_rule_results(candidate, rules)
        if parsed is not None:
            return parsed

    return [
        create_error_result(
            rule, f"Failed to parse response. Response preview: {cleaned_text[:200]}..."
        )
        for rule in rules
    ]


def validate_and_fix_results(results: List[Dict], rules: List[Dict]) -> List[Dict]:
    """验证和修复检测结果

    确保返回的结果包含所有规则，并且格式正确
    修复 LLM 输出中 compliant 字段与 summary 内容不一致的问题
    """
    validated_results = []
    rule_ids_found = set()

    # 首先处理成功解析的结果
    for result in results:
        if isinstance(result, dict):
            rule_id = result.get("rule_id", "")
            rule_ids_found.add(rule_id)

            # 获取原始字段
            compliant = result.get("compliant", False)
            summary = result.get("summary", "")
            advice = result.get("advice", None)

            # 【简单后处理】只修复明显不一致的情况
            # 如果 summary 明确表示合规，但 compliant=false，修正为 compliant=true
            if not compliant:
                # 明确的合规关键词（必须在 summary 中出现）
                explicit_compliant_keywords = [
                    "符合规范", "满足要求", "格式正确", "符合要求",
                    "无问题", "通过检查", "符合标准",
                    # 添加更多关键词
                    "符合", "正确", "无错误", "未发现", "不存在",
                    "符合 Redfish 要求", "符合规范要求", "格式符合"
                ]
                # 如果 summary 包含任何一个合规关键词，且 advice 为 null
                if advice is None and any(kw in summary for kw in explicit_compliant_keywords):
                    compliant = True

            # 确保所有必需字段都存在
            validated_results.append(
                {
                    "rule_id": rule_id,
                    "category": result.get("rule_category", result.get("category", "")),
                    "rule": result.get("rule_description", result.get("rule", "")),
                    "severity": result.get("severity", "info"),
                    "compliant": compliant,
                    "findings": result.get("findings", []),
                    "summary": summary,
                    "advice": advice,
                }
            )

    # 检查是否有规则缺失，如果有则添加错误结果
    for rule in rules:
        rule_id = rule.get("id", "")
        if rule_id not in rule_ids_found:
            validated_results.append(
                {
                    "rule_id": rule_id,
                    "category": rule.get("category", ""),
                    "rule": rule.get("rule", ""),
                    "severity": rule.get("severity", "info"),
                    "compliant": False,
                    "findings": [],
                    "summary": f"规则检查结果缺失，可能是 LLM 输出不完整",
                    "error": "Rule result missing from LLM output",
                }
            )

    return validated_results


def create_error_result(rule: Dict, error_message: str) -> Dict:
    """创建错误结果"""
    return {
        "rule_id": rule.get("id", "UNKNOWN"),
        "category": rule.get("category", ""),
        "rule": rule.get("rule", ""),
        "severity": rule.get("severity", "info"),
        "compliant": False,
        "error": error_message,
        "summary": f"检查失败: {error_message}",
        "findings": [],
    }


def check_all_rules_batch(
    rules: List[Dict],
    uri: str,
    payload: Dict,
    resource_type: Optional[str] = None,
    review_point_title: Optional[str] = None,
    review_point_content: Optional[str] = None,
    model: str = None,
    save_result: bool = True,
) -> Dict:
    """批量检查所有规则（一次 API 调用）

    Args:
        rules: 规则列表
        uri: Redfish 资源 URI
        payload: Redfish 响应数据
        resource_type: 资源类型（可选）
        review_point_title: 评审点标题（可选）
        review_point_content: 评审点内容（可选，如果提供则优先检查评审点内容）
        model: 使用的模型名称
        save_result: 是否保存结果

    Returns:
        总检测结果
    """
    # 如果提供了 review_point_content，优先使用评审点内容进行检查
    if review_point_content is not None and review_point_title is not None:
        return check_review_point_compliance(rules, review_point_title, review_point_content, model, save_result)

    if resource_type is None:
        odata_type = payload.get("@odata.type", "")
        resource_type = (
            "#{}".format(odata_type.split(".")[-2]) if "." in odata_type else "#Unknown"
        )

    print("\n" + "=" * 60)
    print("REDFISH RULE-BASED COMPLIANCE CHECKING (BATCH MODE)")
    print("=" * 60)
    print(f"\n[URI] {uri}")
    print(f"[总检测数] {len(rules)} 条规则")

    # 准备批量检查的输入
    rules_text = format_rules_for_batch(rules)
    payload_json = json.dumps(payload, indent=2, ensure_ascii=False)

    try:
        # 直接构造完整的 prompt 字符串，避免 ChatPromptTemplate 的占位符解析问题
        llm = create_llm(model=model, temperature=0.1)
        full_prompt = BATCH_CHECK_SYSTEM_PROMPT + """

请检查以下 Redfish 接口响应是否符合所有规则：

---

## 待检查的所有规则

""" + rules_text + """

---

## 待检查的 Redfish 响应

**URI**: """ + str(uri) + """
**资源类型**: """ + str(resource_type) + """

**响应内容**:
```json
""" + payload_json + """
```

----

请对每条规则进行检查，返回包含所有规则检测结果的 JSON 数组。注意：
1. 数组中每个元素对应一条规则的检查结果
2. 必须包含所有 """ + str(len(rules)) + """ 条规则的检查结果
3. rule_id 必须与上述规则列表中的 ID 完全对应
4. **对于不符合规则的项(compliant=false)，必须提供具体的修改建议(advice)**
"""

        # 一次性调用检查所有规则
        print("\n[API] 正在调用模型进行批量检查...")
        response_text = llm.invoke(full_prompt).content

        # 添加延迟以避免速率限制
        time.sleep(5)

        # 解析批量结果
        print("[API] 响应已接收，正在解析...")
        results = parse_batch_check_result(response_text, rules)

        # 检查是否有规则缺失
        if len(results) < len(rules):
            print(f"[警告] 预期 {len(rules)} 条规则，实际解析到 {len(results)} 条结果")

    except Exception as e:
        print(f"[错误] 批量检查失败: {e}")
        print(f"[错误] 异常详情:\n{traceback.format_exc()}")
        # 如果批量检查失败，返回所有规则的错误结果
        results = [create_error_result(rule, str(e)) for rule in rules]

    # 后处理：验证和修复检测结果（修复 LLM 输出中 compliant 与 summary 不一致的问题）
    results = validate_and_fix_results(results, rules)

    # 打印简要结果
    for r in results:
        if "error" in r:
            print(
                f"  [{r.get('rule_id')}] [X] 错误: {r.get('error', 'Unknown')[:50]}..."
            )
        else:
            status_icon = (
                "[OK]"
                if r.get("compliant")
                else "[FAIL]" if r.get("severity") == "must" else "[WARN]"
            )
            summary = r.get("summary", "N/A")
            print(f"  [{r.get('rule_id')}] {status_icon} {summary[:60]}...")
            # 对于不合规的规则，打印修改建议
            if not r.get("compliant") and r.get("advice"):
                advice = r.get("advice", "")
                print("      [*] 修改建议: " + str(advice))

    # 汇总结果
    total = len(results)
    compliant = sum(1 for r in results if r.get("compliant") and "error" not in r)

    # 收集失败规则的详细信息
    failed_rules_list = []
    for r in results:
        if not r.get("compliant") and r.get("severity") == "must" and "error" not in r:
            failed_rules_list.append(
                {
                    "rule_id": r.get("rule_id", "N/A"),
                    "category": r.get("category", "N/A"),
                    "rule": r.get("rule", "N/A"),
                    "summary": r.get("summary", "N/A"),
                    "advice": r.get("advice", "请参考 Redfish 规范要求进行修复"),
                    "findings": r.get("findings", []),
                }
            )
    failed = len(failed_rules_list)

    # 收集警告规则的详细信息
    warning_rules_list = []
    for r in results:
        if (
            not r.get("compliant")
            and r.get("severity") in ["should", "may"]
            and "error" not in r
        ):
            warning_rules_list.append(
                {
                    "rule_id": r.get("rule_id", "N/A"),
                    "category": r.get("category", "N/A"),
                    "rule": r.get("rule", "N/A"),
                    "summary": r.get("summary", "N/A"),
                }
            )
    warnings = len(warning_rules_list)

    # 按照 1.json 模板格式构建模型检测错误详情
    model_validation_errors = []
    for failed_rule in failed_rules_list:
        rule_id = failed_rule.get("rule_id", "N/A")
        category = failed_rule.get("category", "N/A")
        summary_text = failed_rule.get("summary", "N/A")
        advice_text = failed_rule.get("advice", "请参考 Redfish 规范要求进行修复")

        model_validation_errors.append(
            {
                "rule": f"[{rule_id}] {category} (规则合规性检查)",
                "message": summary_text,
                "advice": advice_text,
            }
        )

    # 构建 warning_details（severity="should"或"may"的规则）
    warning_details_errors = []
    for warning_rule in warning_rules_list:
        rule_id = warning_rule.get("rule_id", "N/A")
        category = warning_rule.get("category", "N/A")
        summary_text = warning_rule.get("summary", "N/A")

        warning_details_errors.append(
            {
                "rule": f"[{rule_id}] {category} (警告)",
                "message": summary_text,
                "advice": f"这是一个 severity='should' 的建议性规则，建议修改以提升规范符合性",
            }
        )

    # 静态验证: RULE-013 通过 MODEL_VALIDATION 的 prompt 检查，不进行代码硬检查
    static_validation_errors = []

    # 构建嵌套的 error_details 结构
    error_details = {
        "STATIC_VALIDATION": static_validation_errors,
        "MODEL_VALIDATION": model_validation_errors,
        "WARNING_DETAILS": warning_details_errors,
    }

    result_status = "pass" if failed == 0 else "fail"

    summary = {
        "uri": uri,
        "resource_type": resource_type,
        "total_checks_num": len(rules),  # 模型检测规则数量（动态取自传入的 rules）
        "failed_checks_num": failed,  # 模型检测失败数量
        "error_details": error_details,
        "result": result_status,
    }

    # 打印汇总统计
    print(f"\n  总检测数: {total}")
    print(f"  通过: {compliant}")
    print(f"  失败: {failed}")
    print(f"  警告: {warnings}")
    print(f"  合规率: {compliant/total*100:.1f}%")
    print(f"  总体合规: {'[OK] 是' if failed == 0 else '[FAIL] 否'}")

    # 保存结果
    if save_result:
        output_file = f"rule_check_result_{resource_type}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Results saved to: {output_file}")

    return summary


# 新增：基于评审点内容的检查
CHECK_REVIEW_POINT_SYSTEM_PROMPT = """你是一位 Redfish 接口规范专家。你的任务是检查给定的评审点（资源描述）是否符合 Redfish 规范要求。

## 语言要求（强制）

- 所有自然语言字段（包括 `summary`、`advice`、`findings.message`、`findings.evidence`、`findings.location` 等）**必须使用简体中文**输出。
- **严禁**出现整段英文 `summary` 或 `advice`；即便输入评审点为纯英文，也必须用中文撰写解释与建议。
- 英文术语（OData 关键字、HTTP 方法、属性名、URI 段、JSON 片段、报错原文等）**保持原文**嵌入中文句子中，不要翻译这些标识符；JSON 的字段名与 `compliant`/`true`/`false` 等枚举值同样保持原样。

## 检查方法

1. 仔细阅读评审点内容，理解其描述的资源、属性、接口等
2. 根据每条规则逐一检查评审点的描述是否符合 Redfish 规范
3. 判断每条规则是否符合
4. 对于不符合的规则，**必须提供具体的修改建议**

## 检查原则

**【核心原则】只检查评审点content内容，不检查任何LLM生成的URI示例或响应！**

规则检查的目标是评估评审点规范本身是否合规。评审点content是原始的规范要求，而LLM生成的URI示例只是对规范的一种实现示例。即使LLM生成的示例有错误（如缩写、拼写错误等），这也不应该影响对评审点规范本身合规性的判断。

**总体原则：当评审点内容存在以下情况时，应判定为不合规（compliant=false）：**
- 明确违反了规则中明确禁止的行为
- 缺少规则中明确要求的元素
- 描述不清可能导致实现歧义

**特别注意事项：**
- **【重要】RULE-001 命名规范检查的特殊规则**：
  - RULE-001 检查：a)属性名是否符合 PascalCase 格式（首字母大写驼峰命名）；b)**物理量属性名是否包含标准单位后缀**（见下方标准单位后缀表）；c)**拼写错误检查**（包括属性名、类型名、URI参数名等所有命名的拼写，拼写检查由RULE-001负责，RULE-004不检查拼写）；d)**【重要】Redfish 原始类型名大小写检查**：评审点表格的「数据类型」列中出现的 Redfish 原始类型名（string、boolean、integer、number、array、object、null）必须使用小写形式。如果出现大写开头的类型名（如 String、Boolean、Integer、Number、Array、Object、Bool、Int 等），这是拼写/大小写错误，必须标记为违规
  - **标准单位后缀表**（这些后缀都是符合规范的）：
    - 功率：**Watts**（**PowerWatts、ConsumedPowerWatts、PowerAverageWatts、PowerPeakWatts** 都是合规的，Watts 是标准功率单位后缀）
    - 电压：Volts（ReadingVolts、VoltageVolts）
    - 电量：kWh（EnergykWh）
    - 温度：Celsius（TemperatureCelsius）
    - 压力：kPa、Pa（PressurekPa、DeltaPressurekPa）
    - 转速：RPM（RotationSpeedRPM）
    - 带宽：Mbps、Gbps（PortSpeedMbps、LinkSpeedGbps）
    - 频率：MHz、GHz（ProcessorSpeedMHz）
    - 时间：Milliseconds、Seconds、Minutes、Hours、Days、Weeks、Months、Years
    - 数据量：Bytes、KiB、MiB、GiB、TiB（MemoryBytes、MemorySizeMiB、TotalCapacityGiB）
    - 百分比：Percent、Percentage（PowerLoadPercent、TaskPercentage）
    - 计数：Count（ProcessorCount、DriveCount）
    - 状态：State、Status、Mode（PowerState、HealthStatus、OperationMode）
  - RULE-001 **绝对不检查**：**语义清晰性、具体性或描述是否充分**（如 Type、Content、Value、Stage、Status、Name 等通用名称只要符合PascalCase就是合规的，RULE-001不检查名称是否语义清晰、具体、是否容易混淆、是否足够描述性等问题。即使名称是"Stage"这样可能被认为不够描述性的名称，只要符合PascalCase格式，就不应标记为违规）；**标准Redfish Schema中已定义的属性名**：如ConsumedPowerWatt（标准ProcessorMetrics Schema属性）等，即使其单位后缀使用单数形式（Watt而非Watts）也不应标记为违规。RULE-001只检查新增或修改的自定义属性
  - **例外（不检查PascalCase）**：a)**Action请求参数、函数参数、URL查询参数**（如filepath、protocol、biosactivemode、systemid、managerid、timeout、supply_source_value、ForceUpdate、ImageUri、TransferProtocol等）：这些不是资源属性名，RULE-001**完全不检查**Action请求参数的命名格式。无论 Action 请求参数使用任何命名格式——下划线（supply_source_value）、全小写、camelCase（首字母小写驼峰）、PascalCase（首字母大写驼峰）还是其他格式——RULE-001 都不检查，也不会建议修改。**即使Action请求参数在表格中列出，也不应判定为违规**；b)包含特殊符号的表达式（Members[{、}]、[0]、.key、Slot.Lanes、PCIeDevice.Lanes、**SPDM{、Issuer{、Subject{、Oem.{**等）；这些符号用于表示数组元素、对象属性引用、嵌套结构或Schema格式，不是属性名本身的问题，RULE-001不检查；c)完全大写的缩写（ID、URI、HTTP、SNMP等）；d)**特定词汇**（openUBMC、Smnp、InterChassAuthentication）；e)**vender拼写**：`vender`是项目中`vendor`的有效拼写变体，与`vendor`等同，包含`Vender`的属性名（如VenderID、SubsystemVenderID、VenderType）是合规的，不应被标记为拼写错误；f)单位前缀正确使用（k小写、M/G/T大写，如EnergykWh、EnergyMB、FrequencyMHz、PortSpeedGbps）；g)单位后缀大小写灵活（SpeedRpm/SpeedRPM、TemperatureCelsius/TemperatureCELSIUS）；h)**标准Redfish Schema中已定义的属性名**：**ConsumedPowerWatt是标准Redfish ProcessorMetrics Schema中定义的属性**（已deprecated，但仍然是标准属性），即使它使用单数Watt而非复数Watts，也不应标记为违规。RULE-001只检查**新增或修改的自定义属性**是否符合命名规范，标准Schema中已存在的属性名（无论是否符合命名规范）都不应被检查
  - **interval/period/duration/timeout属性的单位后缀规则**：包含**Interval/Period/Duration/Timeout等时间相关词根**的属性**可以使用单位后缀**来明确表示时间单位，如 CurrentPollingIntervalInSeconds、UpdateIntervalInMilliseconds、RetryPeriodInSeconds、EstimatedDurationInMinutes、EjectTimeoutInMilliseconds 等。**这些带单位后缀的属性名都是合规的**，且是推荐的做法（明确时间单位）。不带单位后缀的 interval 属性名（如 CurrentPollingInterval、UpdateInterval）也是合规的。
  - **不需要单位后缀的属性类型**：a)包含Count/Number的计数属性（ProcessorCount、DriveCount）；b)包含State/Status/Mode的状态属性（PowerState、HealthStatus、OperationMode）；c)包含Percent/Percentage的百分比属性（TaskPercentage、UtilizationPercentage）；d)无量纲属性（StatusCode、Ratio）
  - **使用标准单位后缀（包括复合单位）的属性名是合规的**：DeltaPressurekPa（kPa千帕）、EnergykWh（kWh千瓦时）、ProcessorSpeedMHz（MHz兆赫）、CurrentSpeedGbps（Gbps吉比特每秒）、PortSpeedMbps（Mbps兆比特每秒）、LocalMemoryBandwidthBytes（Bytes字节）、TotalMemoryBytes（Bytes字节）、MemorySizeMiB（MiB兆字节）等都是符合规范的。**任何使用Gbps、Mbps、kPa、kWh、MHz、GHz、Bytes、KiB、MiB、GiB、TiB等标准单位后缀的属性名都不应被标记为违规**。**特别注意：Bytes是标准的字节单位后缀，任何以Bytes结尾的属性名都是符合规范的**。**绝对不要将Bytes错误地解析为By，Bytes本身就是一个完整的单位后缀，不能拆分**
  - **RULE-001 不检查 URI 格式结构问题**：URI 格式结构问题（如缺少 v1 层级、路径分隔符错误）由 RULE-004 负责检查。但 **URI 中的拼写/命名问题由 RULE-001 负责**，包括：a)**URI 路径段的大小写问题**（如 /redfish/v1/systems 中的 systems 应为 Systems）；b)**URI 路径段的拼写错误**（如 /redfish/v1/Systm 中的 Systm 应为 System）。**【重要例外：Storages 和 Storage 都是合法的】**：Storages 作为存储资源的复数形式，在任何 URI 深度都是合法的（如 `/redfish/v1/Systems/{id}/Storages/{id}`）。Storage 和 Storages 混用也不违规。**不要将 Storages 标记为需要改为 Storage 的违规**。RULE-004 只检查 URI 格式结构，不检查拼写/命名。
  - RULE-001 不检查units标注的具体内容（如属性名包含Bytes，不应检查其units标注是否为"Bytes"），units标注是属性说明的一部分，不是属性名命名规范的一部分；**units 列中的 By、B 与 Bytes 均表示字节含义，不得将 By 判为拼写错误**
  - **【⚠️ RULE-001 易漏检清单 — 必须逐项核对】**：❶ 类型列有 `bool`/`Bool`/`Boolean`/`String`/`Integer`/`Number` 等非小写类型名？❷ 属性名有 camelCase（首字母小写如 `fanMode`/`bootOrder`）？❸ JSON 示例中 `state`/`health` 首字母小写？❹ Action 名称点号后空格（如 `Power. SetPsu`）？❺ `@data.id`（少 `o`）？❻ 拼写错误（`NetworkAdapterse`/`Certifacates`）？❼ 属性名缩写不一致？❽ URI 路径段小写（如 `/storage/`）？
- **【重要】RULE-012 敏感信息检查的特殊规则**：
  - RULE-012 允许：通用厂商名（如Nvidia、Intel、AMD）用于示例说明；存储语境下的 **PMC、RAID、HBA** 等通用技术词（无具体型号/料号）不视为敏感型号
  - RULE-012 不违规：a)仅使用通用厂商名；b)示例性质的描述；c)PMC/RAID/HBA 等未绑定具体型号时
  - RULE-012 违规：a)具体专有型号；b)内部项目代号；c)定制型号
- **【重要】RULE-010 数据类型规范检查的特殊规则**：
  - RULE-010 检查：**只检查类型与示例值的一致性**：声明的类型与示例值/枚举值的数据类型是否一致；**特别注意integer与number的区别以及JSON格式**：integer类型必须是整数且不能加引号（如1、100、0，写成"1"是错误的字符串格式）；number类型可以是整数或小数且不能加引号（如1、1.5、100.75，写成"1.5"是错误的字符串格式）；string类型必须加引号（如"GPU1"）；如果类型声明为integer/number但示例值加了引号（字符串格式）或示例值是小数（仅针对integer），则RULE-010违规
  - RULE-010 也检查：**类型声明的语义正确性**：是否符合Redfish Schema的语义要求（如TrustedComponents根据Redfish Schema应为array，如果声明为string则违规）
  - **例外情况**：a)当示例值为"/"时，跳过该属性的类型一致性检查（"/"常用于表示路径分隔符或默认路径）；b)**duration类型属性可以声明为string或duration**：如EstimatedDuration、EjectTimeout等包含Duration/Timeout等时间词根的属性，可以声明为string类型（因为duration用ISO8601格式字符串表示，如PT1H），也可以声明为duration类型，两者都是合规的
  - **RULE-010 绝对不检查：类型名的拼写或大小写问题**（如interger、String、Boolean等由RULE-001负责）；属性名单位后缀、单位标注等命名相关问题（由RULE-001负责）
  - RULE-010 不检查：**类型名的拼写或大小写**（如interger应为integer、String应为string、Boolean应为boolean等，这些都是拼写/大小写问题，由RULE-001负责）；属性名的单复数形式（由RULE-001负责）；属性名的PascalCase格式（由RULE-001负责）；**属性名拼写相关问题**（由RULE-001负责）；**枚举（enum）类型的属性类型正确性**（只有明确声明为enum/枚举类型时，由RULE-008负责）；Schema内部的引用问题（如$ref、anyOf等）；示例值是否在枚举范围内
  - 示例1：表格说"BandwidthPercent: integer"但示例值为"1"（字符串格式）或45.5（小数）→ 类型声明为integer但示例值是字符串或小数，RULE-010违规 ✗（正确格式应为"BandwidthPercent": 1）
  - 示例2：表格说"PhysicalContext: string, 枚举值: [PowerSupply]"，Schema示例值为"test" → "test"是字符串，与string类型一致 → RULE-010合规 ✓
  - 示例3：表格说"TrustedComponents: string" → 根据Redfish Schema应为array，但声明为string → RULE-010违规 ✗
  - 示例4：表格说"Target: string, value: \"/\"" → 示例值为"/"，跳过RULE-010类型一致性检查 ✓
  - 示例5：表格说"EstimatedDuration: string"或"EjectTimeout: duration" → duration相关属性可以声明为string或duration类型，都是合规的 ✓
  - 绝对不要检查：a)Schema中的$ref、anyOf等引用问题；b)示例值是否在枚举范围内；c)**Schema中的patternProperties**：patternProperties是用于匹配动态属性名（如@odata.id、@Redfish.Deprecated等Oem扩展属性）的模式匹配规则，其类型数组（如["array","boolean","number","null","object","string"]）表示允许匹配的扩展属性可以是这些类型之一，这**不是**具体属性的类型定义。**不要将patternProperties中的类型数组误判为具体属性的类型定义问题**，具体属性的类型由其自身的type字段或$ref引用的定义决定。这不是RULE-010的检查范围！
- **【重要】RULE-008 枚举设计检查的特殊规则**：
  - RULE-008 检查：**只检查评审点或Schema明确声明为enum/枚举类型的属性**。只有当属性被明确声明为enum/枚举类型时，RULE-008才检查其类型是否为string
  - RULE-008 不检查：**普通string类型的取值范围**。如果评审点只是说明string类型的取值范围（如取值可为"Disabled"、"Enabled"、"Ethernet"），这只是取值说明，不是枚举类型，RULE-008不检查
  - RULE-008 不检查：**Schema中定义的类型**。如果Schema定义某属性为boolean或anyOf允许boolean，评审点如实记录Schema的定义不应被标记为违规
  - RULE-008 重点：只检查真正的枚举（enum）类型，不检查普通string类型的取值范围说明
- **【重要】RULE-013 Unknown枚举值描述检查的特殊规则**：
  - RULE-013 检查的是：Unknown枚举值本身的含义描述
  - RULE-013 合格描述包括：a)说明Unknown代表的状态（如"Unknown通信丢失或故障等无法及时获取到状态"）；b)说明返回Unknown的条件；c)说明属性可见性（如"硬件不支持时不显示"也有效）
  - 以下描述都是合格的："Unknown通信丢失或故障等无法及时获取到状态"、"Unknown未知，硬件不支持的场景不显示"、"当设备状态无法确定时返回Unknown"→这些都是有效的Unknown值说明
- **【重要】RULE-004 URI资源连通性与路径规范检查**：
  - **【核心职责区分】RULE-004 vs RULE-001**：
    - **RULE-004 只检查 URI 格式结构问题**：如缺少 v1 层级、路径分隔符错误、路径层级结构错误等
    - **RULE-001 负责 URI 中的拼写/命名错误**：如 PascalCase 大小写错误（systems vs Systems）、复数形式错误（）、拼写错误（Systm vs System）等
    - **RULE-004 绝对不检查**：URI 中的大小写、复数形式、拼写等问题，这些都属于 RULE-001 的职责
  - **检查范围**：只检查**已有/修改的标准资源**的URI格式，**不检查新增标准资源**
  - RULE-004 检查两个维度：1)评审点是否提供了URI或路径信息；2)URI格式结构是否正确
  - **URI存在性**：如果评审点提供了完整的资源URI（如"资源URI: /redfish/v1/Managers/manager_id/EnergySavingService"），则判定为合规；完全没有提供任何URI或路径信息时，判定为违规
  - **URI格式检查**（RULE-004 的核心职责）：只检查以下 URI 格式结构问题：
    - **缺少 v1 层级**：URI 应该是 /redfish/v1/... 而不是 /redfish/...
    - **路径分隔符错误**：应该使用 / 而不是 \\
    - **路径层级结构**：至少应该有 /redfish/v1/{ServiceRoot} 的基本结构
    - **第4层及更深的层级不进行检查**（允许任意自定义资源名称）
  - **RULE-004 不检查的内容（这些由 RULE-001 负责）**：
    - ❌ **大小写问题**：如 /redfish/v1/systems（systems 小写）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **复数形式问题**：如 /redfish/v1/systems（应为 Systems）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **拼写问题**：如 /redfish/v1/Systm（Systm 拼写错误）→ 这是 RULE-001 的拼写/命名检查
    - ❌ **PascalCase 格式问题**：如 /redfish/v1/systems/managerid（大小写不符合 PascalCase）→ 这是 RULE-001 的拼写/命名检查
  - RULE-004 允许：a)Oem扩展路径；b)新增资源有说明；c)语义化的资源名称（如Temperature、Power、Voltage、Fan、Thermal、PowerSupply、Drive等）；d)**新增标准资源**（评审点标题或内容明确说明是新增、添加标准资源）；e)**第4层及更深层级**的任何资源名称；f)**URI参数使用冒号格式:managerid或花括号格式{managerid}**；g)**评审点明确说明和解释的 URI 设计格式**（如评审点说明采用\"协议名+ID\"的命名模式，如Snmp1、Syslog1、Smtp1等，这是有设计说明的格式，不应判定为违规）；h)**厂商自定义的资源ID命名格式**，只要评审点提供了明确的命名规则说明；i)**URI 中的大小写、复数形式、拼写等问题**（这些由 RULE-001 负责，RULE-004 不检查）
  - RULE-004 违规示例（只检查格式结构问题）：
    - ❌ 缺少 v1 层级：/redfish/Systems → 应为 /redfish/v1/Systems
    - ❌ 路径分隔符错误：\\redfish\\v1\\Systems → 应使用 /
    - ❌ 路径结构不完整：/redfish → 缺少 v1 和 ServiceRoot
  - **重点**：RULE-004 只检查 URI 格式结构问题（缺少v1、分隔符错误、层级结构错误）。URI 中的大小写、复数形式、拼写等问题完全由 RULE-001 负责，RULE-004 绝不检查。对于新增标准资源，不进行RULE-004检测。
- 如果评审点提到了属性名或URI，要检查是否符合规范
- **对于 severity="must" 的规则**：即使评审点没有提到某些必需元素，也应检查是否存在这些必需元素。如果评审点描述了一个资源但缺少必需字段（如@odata.id、Id、Name等），应判定为不合规
- **对于 severity="should" 的规则**：如果评审点没有提到相关元素，不判定为违规（只检查提到的内容）
- 常见缩写（TX/RX/LED/UUID/GUID/Comp/Max/Min等）保持大写是符合规范的

## 【特别强调】RULE-004 与 RULE-001 的绝对职责划分

**务必严格遵守以下职责划分，任何混淆都将导致检查结果错误！**

### RULE-004 的绝对禁区（绝对不能检查的内容）

RULE-004 **绝对禁止**检查以下内容，这些**完全**由 RULE-001 负责：

| 禁止检查的内容 | 示例 | 负责规则 |
|--------------|------|---------|
| URI 路径段的大小写 | /redfish/v1/systems（systems 应为 Systems） | RULE-001 |
| URI 路径段的复数形式 |  | RULE-001 |
| URI 路径段的拼写错误 | /redfish/v1/Systm（Systm 应为 System） | RULE-001 |
| URI 参数的命名格式 | /redfish/v1/Systems/:managerid（managerid 大小写） | RULE-001 |
| PascalCase 格式问题 | 任何关于"是否符合PascalCase"的判断 | RULE-001 |
| 资源名称的语义问题 | 如"名称不够描述性"、"容易混淆"等 | RULE-001 |

**RULE-004 只能检查以下格式结构问题**：
1. 是否缺少 v1 层级（/redfish/Systems 缺少 v1）
2. 路径分隔符是否正确（\\ vs /）
3. 路径层级结构是否完整

### RULE-001 的职责（包括 URI 中的拼写/命名）

RULE-001 **必须检查**以下内容：
1. 资源属性名是否符合 PascalCase
2. URI 路径段的大小写、拼写、复数形式
3. 所有命名的拼写错误（属性名、类型名、URI 参数名等）

### 检查时的判断标准

当检查 RULE-004 时，如果问题涉及以下关键词，**必须**判定为 RULE-001 的职责，RULE-004 **不能**标记为违规：
- "PascalCase"、"大小写"、"复数形式"、"拼写"、"命名格式"
- "首字母大写"、"小写"、"复数"、"单数"
- "systems"、"Processors" 等具体命名问题

**RULE-004 的 summary 绝对不能包含**：
- "PascalCase"、"大小写"、"复数"、"拼写"、"命名"等关键词
- 任何关于命名格式的判断或建议

**【新增资源判断示例】**

以下是明确的新增资源，RULE-004 **必须判定为合规（compliant=true）**：

| 评审点内容示例 | 是否新增资源 | RULE-004 判定 |
|--------------|------------|-------------|
| "新增 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "添加 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "扩展 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "创建 ThermalEquipment 资源" | 是 | 合规（compliant=true） |
| "新增 ThermalEquipment 相关资源集合" | 是 | 合规（compliant=true） |
| "属于redfish接口获取ThermalEquipment相关资源集合信息" | 是 | 合规（compliant=true） |
| "在 /redfish/v1 下新增 Ports 资源" | 是 | 合规（compliant=true） |
| "添加 Snmp1 资源" | 是 | 合规（compliant=true） |

**判断方法**：如果评审点标题或内容中包含以下任一情况，即判定为新增资源：
- 中文关键词：新增、添加、扩展、创建、提供、包含、属于...接口
- 英文关键词：New、Add、Extend、Create、Provide、Include、...related resources
- URI 在 /redfish/v1 下但不是标准服务根节点（如 /redfish/v1/ThermalEquipment）

**重要**：对于新增资源，RULE-004 只检查是否包含 /redfish/v1/ 层级，只要包含 v1 层级就合规，不再检查第3层是否为标准服务根节点。

如果评审点的 URI 存在命名格式问题（如 systems），RULE-004 应该判定为 **合规（compliant=true）**，因为这是 RULE-001 的职责。

## 输出格式

**【最高优先级】仅输出 JSON**：你的完整回复必须且仅能是一个 JSON 数组——第一个非空白字符必须是 `[`，最后一个非空白字符必须是 `]`。不要在 JSON 前后输出说明文字、标题或 Markdown 代码围栏；若需思考请在内心完成，最终只输出可被 `json.loads` 直接解析的数组。

请严格按以下 JSON 格式输出**所有规则的检测结果**（注意：输出一个 JSON 数组，包含所有规则的检查结果）：

```json
[
  {{
    "rule_id": "RULE-001",
    "rule_category": "必需属性",
    "rule_description": "所有 Redfish 资源必须包含 @odata.id、@odata.type、Id、Name 属性",
    "compliant": true,
    "severity": "must",
    "findings": [
      {{
        "property": "资源描述",
        "status": "pass",
        "expected": "必须描述标准属性",
        "actual": "已包含标准属性描述",
        "message": "评审点包含了标准必需属性"
      }}
    ],
    "summary": "评审点描述符合规范要求",
    "advice": null
  }}
]
```

### 修改建议(advice)的要求

**当 compliant=false 时，必须提供 advice 字段，建议应具体可执行：**

1. **具体指出问题位置**：明确指出评审点描述中的哪个部分有问题
2. **提供修改方案**：给出具体的修改建议
3. **引用规范依据**：必要时引用 Redfish 规范的具体条款

**当 compliant=true 时，advice 设为 null。**

### 重要说明
1. **必须返回所有规则的检查结果**，不要遗漏任何规则
2. 输出格式必须是 JSON 数组
3. 每个结果对象必须包含 rule_id 字段，且必须与输入的规则 ID 对应
4. summary 是对该规则检查的总体评价（1-2句话）
5. **compliant=false 时必须提供具体可执行的修改建议**
6. **summary 表述规范**：
   - 当 compliant=true 时，使用肯定的、清晰的表达，如："评审点中的属性命名符合规范"、"所有属性名均符合 PascalCase 要求"
   - 避免使用双重否定或模糊表达，如："未包含不符合"、"没有发现问题"
   - 当 compliant=false 时，直接指出问题，如："属性名 sensorValue 不符合 PascalCase 规范"
7. **【重要】severity 与 compliant 的关系**：
   - **severity="must" 的规则**：如果评审点违反了规则，compliant 必须设为 false
   - **severity="should" 的规则**：即使评审点违反了规则，compliant 也应该设为 true（因为这只是建议性要求，不是强制要求），但在 summary 中说明问题和建议
   - **severity="may" 的规则**：compliant 始终为 true（因为这是可选要求）
   - **判断违规的严重程度**：只有 severity="must" 的规则违反时才判定为不合规（compliant=false），severity="should" 或 "may" 的规则违反不影响总体合规性判断
"""

CHECK_REVIEW_POINT_USER_PROMPT = """请检查以下评审点（资源描述）是否符合所有 Redfish 规范：

---

## 待检查的所有规则

{rules_text}

---

## 评审点信息

**评审点标题**: {review_point_title}

**评审点内容**:
{review_point_content}

---

请对每条规则进行检查，返回包含所有规则检测结果的 JSON 数组。注意：
1. 数组中每个元素对应一条规则的检查结果
2. 必须包含所有 {num_rules} 条规则的检查结果
3. rule_id 必须与上述规则列表中的 ID 完全对应
4. **对于不符合规则的项(compliant=false)，必须提供具体的修改建议(advice)**
5. **【特别提醒】RULE-004 新增资源豁免**：如果评审点标题或内容包含"新增"、"添加"、"扩展"、"创建"、"New"、"Add"、"Extend"、"Create"等关键词，说明这是新增资源，则 RULE-004 **必须**判定为合规（compliant=true），任何 URI 设计都是允许的。
6. **【特别提醒】RULE-004 只检查 URI 格式结构问题**：RULE-004 只检查 URI 格式结构问题（缺少v1层级、分隔符错误），不检查命名格式问题（PascalCase、大小写、拼写等由 RULE-001 负责）。
7. **【输出】正文只能是合法 JSON 数组**，不要包裹在 \\\`\\\`\\\` 代码块中，不要在 JSON 外写任何字符。"""


def check_review_point_compliance(
    rules: List[Dict],
    review_point_title: str,
    review_point_content: str,
    model: str = None,
    save_result: bool = False,
) -> Dict:
    """基于评审点内容检查 Redfish 规范合规性（不依赖生成的 URI 示例）

    Args:
        rules: 规则列表
        review_point_title: 评审点标题
        review_point_content: 评审点内容（从原帖子提取）
        model: 使用的模型名称
        save_result: 是否保存结果

    Returns:
        总检测结果
    """
    print("\n" + "=" * 60)
    print("REDFISH REVIEW POINT COMPLIANCE CHECKING")
    print("=" * 60)
    print(f"\n[评审点] {review_point_title}")
    print(f"[总检测数] {len(rules)} 条规则")

    # RULE-001 前置替换：将已知规避词替换为规范写法，仅影响送入 LLM 的副本
    llm_title = preprocess_content_for_rule001(review_point_title)
    llm_content = preprocess_content_for_rule001(review_point_content)

    # 准备批量检查的输入
    rules_text = format_rules_for_batch(rules)

    try:
        # 创建检查链
        llm = create_llm(model=model, temperature=0.1)
        # 直接构造完整的 prompt 字符串，避免 ChatPromptTemplate 的占位符解析问题
        full_prompt = CHECK_REVIEW_POINT_SYSTEM_PROMPT + """

请检查以下评审点（资源描述）是否符合所有 Redfish 规范：

---

## 待检查的所有规则

""" + rules_text + """

---

## 评审点信息

**评审点标题**: """ + str(llm_title) + """

**评审点内容**:
""" + str(llm_content) + """

---

请对每条规则进行检查，返回包含所有规则检测结果的 JSON 数组。注意：
1. 数组中每个元素对应一条规则的检查结果
2. 必须包含所有 """ + str(len(rules)) + """ 条规则的检查结果
3. rule_id 必须与上述规则列表中的 ID 完全对应
4. **对于不符合规则的项(compliant=false)，必须提供具体的修改建议(advice)**
"""

        print("\n[API] 正在调用模型进行评审点合规性检查...")
        response_text = llm.invoke(full_prompt).content

        # 添加延迟以避免速率限制
        time.sleep(5)

        # 解析结果
        print("[API] 响应已接收，正在解析...")
        results = parse_batch_check_result(response_text, rules)

        # 检查是否有规则缺失
        if len(results) < len(rules):
            print(f"[警告] 预期 {len(rules)} 条规则，实际解析到 {len(results)} 条结果")

    except Exception as e:
        print(f"[错误] 评审点检查失败: {e}")
        print(f"[错误] 异常详情:\n{traceback.format_exc()}")
        # 如果检查失败，返回所有规则的错误结果
        results = [create_error_result(rule, str(e)) for rule in rules]

    # RULE-001 后处理：将占位符还原为原始词汇
    results = postprocess_results_for_rule001(results)

    # 后处理：验证和修复检测结果（修复 LLM 输出中 compliant 与 summary 不一致的问题）
    results = validate_and_fix_results(results, rules)

    # RULE-001 静态补充检查：对原文做正则扫描，补充 LLM 漏检的高频模式
    results = static_postcheck_rule001(results, review_point_title, review_point_content)

    # 打印简要结果
    for r in results:
        if "error" in r:
            print(
                f"  [{r.get('rule_id')}] [X] 错误: {r.get('error', 'Unknown')[:50]}..."
            )
        else:
            status_icon = (
                "[OK]"
                if r.get("compliant")
                else "[FAIL]" if r.get("severity") == "must" else "[WARN]"
            )
            summary = r.get("summary", "N/A")
            print(f"  [{r.get('rule_id')}] {status_icon} {summary[:60]}...")
            # 对于不合规的规则，打印修改建议
            if not r.get("compliant") and r.get("advice"):
                advice = r.get("advice", "")
                print("      [*] 修改建议: " + str(advice))

    # 汇总结果
    total = len(results)
    compliant = sum(1 for r in results if r.get("compliant") and "error" not in r)

    # 收集失败规则的详细信息
    failed_rules_list = []
    for r in results:
        if not r.get("compliant") and r.get("severity") == "must" and "error" not in r:
            failed_rules_list.append(
                {
                    "rule_id": r.get("rule_id", "N/A"),
                    "category": r.get("category", "N/A"),
                    "rule": r.get("rule", "N/A"),
                    "summary": r.get("summary", "N/A"),
                    "advice": r.get("advice", "请参考 Redfish 规范要求进行修复"),
                    "findings": r.get("findings", []),
                }
            )
    failed = len(failed_rules_list)

    # 收集警告规则的详细信息
    warning_rules_list = []
    for r in results:
        if (
            not r.get("compliant")
            and r.get("severity") in ["should", "may"]
            and "error" not in r
        ):
            warning_rules_list.append(
                {
                    "rule_id": r.get("rule_id", "N/A"),
                    "category": r.get("category", "N/A"),
                    "rule": r.get("rule", "N/A"),
                    "summary": r.get("summary", "N/A"),
                }
            )
    warnings = len(warning_rules_list)

    # 按照 1.json 模板格式构建模型检测错误详情
    model_validation_errors = []
    for failed_rule in failed_rules_list:
        rule_id = failed_rule.get("rule_id", "N/A")
        category = failed_rule.get("category", "N/A")
        summary_text = failed_rule.get("summary", "N/A")
        advice_text = failed_rule.get("advice", "请参考 Redfish 规范要求进行修复")

        model_validation_errors.append(
            {
                "rule": f"[{rule_id}] {category} (规则合规性检查)",
                "message": summary_text,
                "advice": advice_text,
            }
        )

    # 构建 warning_details（severity="should"或"may"的规则）
    warning_details_errors = []
    for warning_rule in warning_rules_list:
        rule_id = warning_rule.get("rule_id", "N/A")
        category = warning_rule.get("category", "N/A")
        summary_text = warning_rule.get("summary", "N/A")

        warning_details_errors.append(
            {
                "rule": f"[{rule_id}] {category} (警告)",
                "message": summary_text,
                "advice": f"这是一个 severity='should' 的建议性规则，建议修改以提升规范符合性",
            }
        )

    # 静态验证: RULE-013 通过 MODEL_VALIDATION 的 prompt 检查，不进行代码硬检查
    static_validation_errors = []

    # 构建嵌套的 error_details 结构
    error_details = {
        "STATIC_VALIDATION": static_validation_errors,
        "MODEL_VALIDATION": model_validation_errors,
        "WARNING_DETAILS": warning_details_errors,
    }

    result_status = "pass" if failed == 0 else "fail"

    summary = {
        "review_point_title": review_point_title,
        "total_checks_num": len(rules),
        "failed_checks_num": failed,
        "error_details": error_details,
        "result": result_status,
        "total_rules": total,
        "compliant_rules": compliant,
        "failed_rules": failed,
        "warning_rules": warnings,
        "compliance_rate": f"{compliant/total*100:.1f}%",
        "overall_compliant": failed == 0,
    }

    # 打印汇总统计
    print(f"\n  总检测数: {total}")
    print(f"  通过: {compliant}")
    print(f"  失败: {failed}")
    print(f"  警告: {warnings}")
    print(f"  合规率: {compliant/total*100:.1f}%")
    print(f"  总体合规: {'[OK] 是' if failed == 0 else '[FAIL] 否'}")

    # 保存结果
    if save_result:
        safe_title = (
            review_point_title.replace("：", "_")
            .replace("/", "_")
            .replace("\\", "_")[:50]
        )
        output_file = f"review_point_check_result_{safe_title}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Results saved to: {output_file}")

    return summary


# 向后兼容：保留旧的函数名，但使用批量实现
def check_all_rules(*args, **kwargs):
    """检查所有规则（向后兼容接口，内部使用批量实现）"""
    return check_all_rules_batch(*args, **kwargs)

