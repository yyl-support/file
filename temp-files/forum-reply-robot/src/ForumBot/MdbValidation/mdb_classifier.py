"""MDB 资源协作接口相关性分类器。

从 mdb_interface_compliance_check 项目移植，提供评审点级别的 MDB 相关性判断。
"""
from __future__ import annotations

import html as html_mod
import logging
import re
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

# ==================== MDB 相关性关键词 ====================

# 强特征关键词：几乎只出现在 MDB 资源协作接口帖子中
_MDB_STRONG_KEYWORDS = [
    "资源协作",
    "interface.schema",
    "path.schema",
    "bmc.kepler",
]

# 需要上下文验证的弱特征：必须出现在技术内容中，而非模板文字
_MDB_WEAK_KEYWORDS = [
    "资源树",
]

# MDB 特有技术词：在 Redfish 帖子中极少出现
_MDB_TECHNICAL_KEYWORDS = [
    "emitsChangedSignal",
    "Persistency",
    "bmc.studio",
    "app.json",
    "mdb_app",
    "LuaModule",
]

# 排除关键词：出现这些说明更可能是 Redfish 帖子而非 MDB 帖子
_REDFISH_EXCLUDE_KEYWORDS = [
    "redfish",
    "json-schema",
    "json schema",
    "odata",
    "@odata",
]

# 北向接口关键词
_NORTHBOUND_KEYWORDS = [
    "ipmi", "ipmi命令", "ipmi接口",
    "web接口", "web界面",
    "cli接口", "cli命令",
    "redfish接口", "北向接口", "snmp",
    "ipmcget", "ipmcset", "ipmitool", "netfn",
    "redfish", "webrest", "/ui/rest/", "ui/rest/",
]

# 模板区域标记
_TEMPLATE_SECTIONS = ["评审结论", "遗留问题"]

# 场景/方案段落标记
_SCENE_MARKER_RE = re.compile(r"^[*\s]*场景\s*\d+\s*[：:]", re.IGNORECASE)


# ==================== 辅助函数 ====================


def _strip_template_sections(text: str) -> str:
    """去除帖子底部的模板区域（评审结论、遗留问题之后的内容）。"""
    for marker in _TEMPLATE_SECTIONS:
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx]
    return text


def _strip_northbound_scenes(content: str) -> str:
    """从评审点内容中剥离北向接口相关的场景段落。"""
    lines = content.split("\n")
    result: list[str] = []
    in_nb_scene = False

    for line in lines:
        stripped = line.strip()
        if _SCENE_MARKER_RE.match(stripped):
            lower = stripped.lower()
            if any(kw in lower for kw in _NORTHBOUND_KEYWORDS):
                in_nb_scene = True
                continue
            in_nb_scene = False

        if not in_nb_scene:
            result.append(line)

    return "\n".join(result).strip()


def _has_northbound_intent(title: str, content: str) -> tuple[bool, str]:
    """判断帖子是否明显是关于北向接口设计而非资源协作接口。"""
    content_lower = content.lower()

    if "资源协作" in content_lower:
        return False, ""

    nb_hits = [kw for kw in _NORTHBOUND_KEYWORDS if kw.lower() in content_lower]
    if len(nb_hits) >= 2:
        return True, f"内容含多个北向关键词: {', '.join(nb_hits)}"

    nb_uri_patterns = ["/redfish/v1/", "/ui/rest/"]
    uri_hits = [p for p in nb_uri_patterns if p in content_lower]
    if uri_hits:
        return True, f"内容含北向URI路径: {', '.join(uri_hits)}"

    return False, ""


# ==================== HTML 工具 ====================


class _HTMLStripper(HTMLParser):
    """轻量 HTML → 纯文本转换器。"""

    _BLOCK_TAGS = {
        "address", "article", "aside", "blockquote", "br", "caption", "div",
        "dl", "dt", "dd", "figcaption", "figure", "footer", "form", "h1",
        "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "ol",
        "p", "pre", "section", "table", "tbody", "td", "tfoot", "th",
        "thead", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def _newline(self) -> None:
        if self._parts and not self._parts[-1].endswith("\n"):
            self._parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self._newline()

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._BLOCK_TAGS:
            self._newline()

    def handle_data(self, data: str) -> None:
        self._parts.append(html_mod.unescape(data))

    def get_text(self) -> str:
        text = "".join(self._parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def strip_html(raw: str) -> str:
    """去除 HTML 标签，保留纯文本。"""
    s = _HTMLStripper()
    s.feed(raw)
    s.close()
    return s.get_text()


def looks_like_html(text: str) -> bool:
    """判断文本是否看起来是 HTML。"""
    if "<p>" in text or "<div" in text or "<table" in text:
        return True
    if "<br>" in text or "<br/>" in text or "<h1" in text or "<h2" in text:
        return True
    if "<li" in text or "<ul" in text or "<ol" in text:
        return True
    if "<span" in text or "<a " in text or "<strong" in text or "<em" in text:
        return True
    if "&lt;" in text or "&gt;" in text or "&nbsp;" in text or "&amp;" in text:
        return True
    return False


def normalize_content(content: str) -> str:
    """将内容归一化为纯文本（如果是 HTML 则去除标签）。"""
    if looks_like_html(content):
        return strip_html(content)
    return content


# ==================== 主分类函数 ====================


def is_mdb_related(title: str, content: str) -> tuple[bool, str]:
    """判断帖子/评审点是否与 MDB 资源协作接口相关。

    分类策略：
    0. 标题含北向接口关键词（且不含"资源协作"）→ 非 MDB
    0.5 评审点标题以北向接口为主语 → 非 MDB
    1. 标题含强特征 → MDB 相关
    2. 技术内容（排除模板区域）含强特征 → MDB 相关
    3. 弱特征出现在含 bmc. 路径的上下文中 → MDB 相关
    4. MDB 特有技术词（且不含 Redfish 特征）→ MDB 相关
    5. 其他 → 非 MDB 相关

    Returns:
        (是否相关, 原因描述)
    """
    title_lower = title.lower()

    # Rule 0: 标题含北向接口关键词（且不含"资源协作"）
    if "资源协作" not in title_lower:
        for kw in _NORTHBOUND_KEYWORDS:
            if kw.lower() in title_lower:
                return False, f"标题含北向接口关键词: {kw}"

    # Rule 0.5: 评审点标题以北向接口为主语
    _NB_SUBJECT_KW = ["redfish", "webrest", "/ui/rest/", "ui/rest/"]
    _MDB_ACTIVE_PHRASES = [
        "新增资源协作接口", "变更资源协作接口",
        "新增资源协作属性", "变更资源协作属性",
        "新增资源协作方法", "变更资源协作方法",
        "新增资源树", "变更资源树",
    ]
    title_start = title_lower[:30]
    nb_as_subject = any(kw in title_start for kw in _NB_SUBJECT_KW)
    if nb_as_subject and not any(phrase in title_lower for phrase in _MDB_ACTIVE_PHRASES):
        return False, f"评审点标题以北向接口为主语: {title[:40]}"

    # Rule 1: 标题含强特征
    for kw in _MDB_STRONG_KEYWORDS:
        if kw.lower() in title_lower:
            tech_content = _strip_template_sections(content)
            tech_lower = tech_content.lower()
            has_nb_uri = "/ui/rest/" in tech_lower or "/redfish/v1/" in tech_lower
            has_mdb_path = "bmc.kepler" in tech_lower
            if has_nb_uri and not has_mdb_path:
                return False, "标题含资源协作但内容纯北向接口（无bmc.kepler路径）"
            return True, f"标题含强特征: {kw}"

    # Rule 2: 技术内容含强特征
    tech_content = _strip_template_sections(content)
    tech_text_lower = tech_content.lower()
    for kw in _MDB_STRONG_KEYWORDS:
        if kw.lower() in tech_text_lower:
            if kw == "bmc.kepler":
                is_nb, _ = _has_northbound_intent(title, tech_content)
                if is_nb:
                    continue
            return True, f"内容含强特征: {kw}"

    # Rule 3: 弱特征 + 上下文
    for kw in _MDB_WEAK_KEYWORDS:
        if kw.lower() in tech_text_lower:
            half_len = len(tech_text_lower) // 2
            first_half = tech_text_lower[:half_len]
            if "bmc.kepler" in first_half or "bmc." in title_lower:
                combined = title_lower + " " + tech_text_lower
                has_coop = "资源协作" in combined
                nb_in_context = any(nb in combined for nb in ["redfish", "/ui/rest/", "webrest"])
                if nb_in_context and not has_coop:
                    continue
                return True, f"内容含弱特征+上下文: {kw} + bmc.kepler"

    # Rule 4: MDB 特有技术词
    for kw in _MDB_TECHNICAL_KEYWORDS:
        if kw.lower() in tech_text_lower:
            redfish_hit = any(rf in tech_text_lower for rf in _REDFISH_EXCLUDE_KEYWORDS)
            if not redfish_hit:
                return True, f"包含MDB技术词: {kw}"

    return False, "未检测到 MDB 资源协作接口相关关键词"
