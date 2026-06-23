# version：1.0.32
# 增强版评审点提取（移植自 mdb_interface 项目）
# 变更：提取与分类解耦，不再内部过滤 Redfish 相关性
# 新增：支持编号摘要+详细描述匹配、中文数字、粗体格式等

import re

# ==================== 评审点标题正则 ====================

_CN_DIGITS = "一二三四五六七八九十"
_POINT_LABEL_RE = r"(?:评审点|决策点|review\s+point|decision\s+point)"
_POINTS_HEADING_RE = r"(?:评审点|决策点|review\s+points?|decision\s+points?)"
_REVIEW_POINT_TITLE_RE = re.compile(
    _POINT_LABEL_RE + r"[^\S\r\n]*(?:\d+|[" + _CN_DIGITS + r"]+)[^\S\r\n]*(?:[：:、.．]|\*|[^\S\r\n]|$)",
    re.IGNORECASE,
)
# 匹配 "评审点：title" 格式（无编号，冒号后紧跟标题文本）
_UNNUMBERED_REVIEW_POINT_RE = re.compile(
    _POINT_LABEL_RE + r"\s*[：:]\s*\S",
    re.IGNORECASE,
)
_NUMBERED_ITEM_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<num>\d+|[" + _CN_DIGITS + r"]+)\s*(?:\\?\.|[、．])\s*(?P<title>.+?)\s*$"
)
_SUMMARY_HEADING_RE = re.compile(r"^(?:#{1,3}\s+)?(?:.*\b)?" + _POINTS_HEADING_RE + r"\s*\*{0,2}\s*[：:]*\s*$", re.IGNORECASE)
_DETAIL_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+)?.*(?:详细(?:描述|信息|说明)|detailed\s+(?:description|information|explanation)|details)\s*[：:]*\s*$",
    re.IGNORECASE,
)
_HEADING_LEVEL_RE = re.compile(r"^(?P<marks>#{1,6})\s+")

_TEMPLATE_SECTIONS = ["评审结论", "遗留问题", "review conclusion", "remaining issues", "legacy issues", "open issues"]
_SECTION_BREAKS = {
    "评审结论",
    "遗留问题",
    "背景",
    "整体方案",
    "评审方案",
    "评审依据",
    "详细描述",
    "详细信息",
    "详细说明",
    "关联issue",
    "是否准备好AI预审",
    "background",
    "overall solution",
    "review solution",
    "review basis",
    "detailed description",
    "detailed information",
    "detailed explanation",
    "details",
    "related issue",
    "related issues",
    "review conclusion",
    "remaining issues",
    "legacy issues",
    "open issues",
    "ready for ai pre-review",
}


# ==================== 基础工具 ====================


def is_redfish_related(title, content):
    """检查评审点是否与 Redfish 相关（关键词匹配）。"""
    title_lower = title.lower() if title else ''
    content_lower = content.lower() if content else ''
    return 'redfish' in title_lower or 'redfish' in content_lower


def _strip_template_sections(text):
    """去除帖子底部的模板区域（评审结论、遗留问题之后的内容）。"""
    for marker in _TEMPLATE_SECTIONS:
        idx = text.find(marker)
        if idx >= 0:
            text = text[:idx]
    return text


def _strip_markdown_heading(line):
    """清理 markdown/html 标题装饰，保留可读文本。"""
    text = line.strip()
    text = re.sub(r"^#{1,6}\s*", "", text)
    text = re.sub(r"^>\s*", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[\]\([^)]+\)", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = text.strip("*_` \t")
    return text.strip()


def _plain_section_name(line):
    text = _strip_markdown_heading(line)
    text = text.rstrip("：:").strip()
    return text.lower()


def _is_summary_heading(line):
    return bool(_SUMMARY_HEADING_RE.match(line.strip()))


def _is_detail_heading(line):
    return bool(_DETAIL_HEADING_RE.match(line.strip()))


def _is_template_heading(line):
    name = _plain_section_name(line)
    return any(marker.lower() == name for marker in _TEMPLATE_SECTIONS)


def _is_section_break(line):
    name = _plain_section_name(line)
    return name in {section.lower() for section in _SECTION_BREAKS}


def _is_review_point_heading_start(text):
    stripped = text.lstrip()
    lower = stripped.lower()
    return (
        stripped.startswith("#")
        or stripped.startswith("**")
        or stripped.startswith("评审点")
        or stripped.startswith("决策点")
        or lower.startswith("review point")
        or lower.startswith("decision point")
        or stripped.startswith("<h")
    )


def _heading_level(line):
    m = _HEADING_LEVEL_RE.match(line)
    if not m:
        return None
    return len(m.group("marks"))


def _numbered_heading_match(line):
    text = _strip_markdown_heading(line)
    m = _NUMBERED_ITEM_RE.match(text)
    if m:
        return m
    m = re.match(
        _POINT_LABEL_RE + r"[^\S\r\n]*(?P<num>\d+|[" + _CN_DIGITS + r"]+)[^\S\r\n]*(?:[：:、.．]|\*)",
        text,
        re.IGNORECASE,
    )
    return m


def _normalize_num(num):
    """将编号归一化为阿拉伯数字字符串。"""
    _CN_DIGITS_MAP = {c: str(i + 1) for i, c in enumerate(_CN_DIGITS)}
    if num.isdigit():
        return num
    result = ""
    for ch in num:
        if ch in _CN_DIGITS_MAP:
            result += _CN_DIGITS_MAP[ch]
        elif ch.isdigit():
            result += ch
    return result or num


# ==================== 编号摘要 + 详细描述匹配 ====================


def _collect_numbered_summary_points(lines):
    """提取 `## 评审点` 摘要列表中的编号评审点。"""
    points = []
    in_summary = False
    summary_level = 0
    content_lines = []

    for line in lines:
        if _is_summary_heading(line):
            in_summary = True
            summary_level = _heading_level(line) or 2
            continue

        if not in_summary:
            continue

        level = _heading_level(line)
        if level is not None and level <= summary_level:
            if points and content_lines:
                points[-1]["content"] = "\n".join(content_lines).strip()
            break

        if _is_section_break(line):
            if points and content_lines:
                points[-1]["content"] = "\n".join(content_lines).strip()
            break

        match = _NUMBERED_ITEM_RE.match(line)
        if not match:
            hm = _numbered_heading_match(line)
            if hm:
                if points and content_lines:
                    points[-1]["content"] = "\n".join(content_lines).strip()
                content_lines = []
                num = hm.group("num")
                heading_title = _strip_markdown_heading(line)
                heading_title = re.sub(
                    r"^" + _POINT_LABEL_RE + r"[^\S\r\n]*(?:\d+|[" + _CN_DIGITS + r"]+)[^\S\r\n]*(?:[：:、.．])?\s*",
                    "", heading_title,
                    flags=re.IGNORECASE,
                ).strip()
                index = len(points) + 1
                points.append({"num": num, "title": f"评审点{index}：{heading_title}", "content": ""})
                continue
            if points:
                content_lines.append(line)
            continue

        if points and content_lines:
            points[-1]["content"] = "\n".join(content_lines).strip()
        content_lines = []

        num = match.group("num")
        title = match.group("title").strip()
        index = len(points) + 1
        points.append({"num": num, "title": f"评审点{index}：{title}", "content": ""})

    if points and content_lines:
        points[-1]["content"] = "\n".join(content_lines).strip()

    return points


def _collect_shared_detail_content(lines):
    """当详细描述区域没有标准编号章节时，收集整个详细描述区域的内容。"""
    detail_start = None
    for idx, line in enumerate(lines):
        if _is_detail_heading(line):
            detail_start = idx + 1
            break
    if detail_start is None:
        return ""

    content_lines = []
    for i in range(detail_start, len(lines)):
        line = lines[i]
        stripped = line.strip()
        if _is_section_break(line) and not _is_detail_heading(line):
            break
        if stripped.startswith("#"):
            heading_text = re.sub(r"^#{1,6}\s*", "", stripped)
            if not any(marker in heading_text for marker in _TEMPLATE_SECTIONS):
                content_lines.append(line)
                continue
            break
        content_lines.append(line)
    return "\n".join(content_lines).strip()


def _collect_detail_sections(lines):
    """提取 `详细描述` 之后的编号章节正文，按编号映射。"""
    detail_start = None
    detail_level = 0
    for idx, line in enumerate(lines):
        if _is_detail_heading(line):
            detail_start = idx + 1
            detail_level = _heading_level(line) or 2
            break
    if detail_start is None:
        return {}

    sections = {}
    i = detail_start
    while i < len(lines):
        line = lines[i]
        if _is_section_break(line) and not _is_detail_heading(line):
            break
        level = _heading_level(line)
        if level is not None and level <= detail_level and not _numbered_heading_match(line):
            break

        match = _numbered_heading_match(line)
        if not match:
            i += 1
            continue

        num = match.group("num")
        content_lines = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j]
            next_level = _heading_level(next_line)
            if next_level is not None and next_level <= (level or 2) and _numbered_heading_match(next_line):
                break
            if next_level is not None and next_level <= detail_level and not _numbered_heading_match(next_line):
                break
            if next_line.strip().startswith(">") and _numbered_heading_match(next_line):
                break
            if next_level is None and _numbered_heading_match(next_line):
                break
            content_lines.append(next_line)
            j += 1
        sections[num] = "\n".join(content_lines).strip()
        i = j
    return sections


def _detail_contains_review_point_titles(lines):
    detail_start = None
    for idx, line in enumerate(lines):
        if _is_detail_heading(line):
            detail_start = idx + 1
            break
    if detail_start is None:
        return False

    for line in lines[detail_start:]:
        if _is_section_break(line) and not _is_detail_heading(line):
            return False
        stripped = line.lstrip()
        if _REVIEW_POINT_TITLE_RE.search(line) and (
            _is_review_point_heading_start(stripped)
        ):
            return True
    return False


def _extract_numbered_summary_review_points(content):
    """提取编号摘要 + 详细描述匹配的评审点。"""
    lines = content.split("\n")
    summary_points = _collect_numbered_summary_points(lines)
    if not summary_points:
        return []

    detail_sections = _collect_detail_sections(lines)
    if not detail_sections:
        shared_detail = _collect_shared_detail_content(lines)
        return [
            {
                "title": point["title"],
                "content": f"{point['content']}\n\n{shared_detail}".strip() if shared_detail else point["content"],
            }
            for point in summary_points
        ]

    norm_sections = {_normalize_num(k): v for k, v in detail_sections.items()}
    points = []
    for point in summary_points:
        num = _normalize_num(point["num"])
        points.append({
            "title": point["title"],
            "content": norm_sections.get(num, point["content"]),
        })
    return points


def _extract_single_unnumbered_review_point(content):
    """提取只有 `评审点` 小节、但没有 `评审点1`/编号列表的单评审点帖子。"""
    lines = content.split("\n")
    summary_start = None
    for idx, line in enumerate(lines):
        if _is_summary_heading(line):
            summary_start = idx + 1
            break
    if summary_start is None:
        return []

    summary_lines = []
    for line in lines[summary_start:]:
        stripped = line.strip()
        if _is_detail_heading(line) or _is_section_break(line):
            break
        if _numbered_heading_match(line):
            return []
        if stripped:
            summary_lines.append(line)

    summary = "\n".join(summary_lines).strip()
    if not summary:
        return []

    if _detail_contains_review_point_titles(lines):
        return []

    detail = _collect_shared_detail_content(lines)
    title_seed = re.sub(r"\s+", " ", summary_lines[0]).strip()
    if len(title_seed) > 80:
        title_seed = title_seed[:77].rstrip() + "..."

    return [{
        "title": f"评审点1：{title_seed}",
        "content": f"{summary}\n\n{detail}".strip() if detail else summary,
    }]


# ==================== 主提取函数 ====================


def extract_all_review_points(content):
    """增强版评审点提取（提取与分类解耦）。

    支持格式：
      - Markdown: ## 评审点1：xxx
      - 粗体: **评审点1：xxx**
      - 纯文本: 评审点1：xxx
      - 编号摘要 + 详细描述段落匹配
      - HTML: <h2>评审点1：xxx</h2>

    Returns:
        list of {"title": "评审点N：xxx", "content": "正文内容"}
        提取所有评审点，不做相关性过滤。
    """
    content = _strip_template_sections(content)
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # 优先尝试编号摘要+详细描述匹配
    numbered_summary_points = _extract_numbered_summary_review_points(content)
    if numbered_summary_points:
        return numbered_summary_points

    single_unnumbered_point = _extract_single_unnumbered_review_point(content)
    if single_unnumbered_point:
        return single_unnumbered_point

    # 常规评审点提取（支持编号和无编号格式）
    lines = content.split("\n")
    points = []

    i = 0
    while i < len(lines):
        line = lines[i]
        match = _REVIEW_POINT_TITLE_RE.search(line)
        unnumbered_match = not match and _UNNUMBERED_REVIEW_POINT_RE.search(line)
        if match or unnumbered_match:
            stripped = line.lstrip()
            is_heading = _is_review_point_heading_start(stripped)
            if is_heading:
                title = line
                title = re.sub(r"^[#*\s]+", "", title)
                title = re.sub(r"<[^>]+>", "", title)
                title = re.sub(r"\*\*(.*?)\*\*", r"\1", title)
                title = title.strip()

                content_lines = []
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    next_stripped = next_line.strip()

                    if _REVIEW_POINT_TITLE_RE.search(next_line):
                        next_l = next_line.lstrip()
                        if (
                            _is_review_point_heading_start(next_l)
                        ):
                            break

                    if unnumbered_match and _UNNUMBERED_REVIEW_POINT_RE.search(next_line):
                        next_l = next_line.lstrip()
                        if (
                            _is_review_point_heading_start(next_l)
                        ):
                            break

                    if re.match(r"^#{1,2}\s", next_line) and not _REVIEW_POINT_TITLE_RE.search(next_line):
                        if _is_detail_heading(next_line):
                            j += 1
                            continue
                        break

                    if _is_section_break(next_stripped):
                        break

                    if re.match(r"^-{3,}\s*$", next_stripped):
                        break

                    content_lines.append(next_line)
                    j += 1

                body = "\n".join(content_lines).strip()
                if title or body:
                    points.append({"title": title, "content": body})
                i = j - 1
        i += 1

    return points


# ==================== 向后兼容 ====================


def extract_review_points_from_html(html_content):
    """向后兼容的提取函数（保留原有调用点）。

    内部调用 extract_all_review_points，不再做 Redfish 过滤。
    过滤由 end_to_end_check.py 中的分类逻辑完成。
    """
    return extract_all_review_points(html_content)
