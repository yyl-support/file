"""MDB 分类器单元测试。"""
import pytest

from src.ForumBot.MdbValidation.mdb_classifier import (
    is_mdb_related,
    strip_html,
    looks_like_html,
    normalize_content,
    _strip_template_sections,
    _strip_northbound_scenes,
    _has_northbound_intent,
)


# ==================== strip_html / looks_like_html / normalize_content ====================


class TestStripHtml:
    def test_basic_tags(self):
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_nested_divs(self):
        result = strip_html("<div>one</div><div>two</div>")
        assert "one" in result and "two" in result

    def test_entities(self):
        assert strip_html("&lt;tag&gt;") == "<tag>"

    def test_empty_string(self):
        assert strip_html("") == ""

    def test_no_html(self):
        assert strip_html("plain text") == "plain text"


class TestLooksLikeHtml:
    def test_paragraph(self):
        assert looks_like_html("<p>text</p>") is True

    def test_div(self):
        assert looks_like_html("<div>text</div>") is True

    def test_br(self):
        assert looks_like_html("line1<br>line2") is True

    def test_entities(self):
        assert looks_like_html("a &lt; b") is True

    def test_plain_text(self):
        assert looks_like_html("just plain text") is False


class TestNormalizeContent:
    def test_html_input(self):
        result = normalize_content("<p>Hello</p>")
        assert "Hello" in result
        assert "<p>" not in result

    def test_plain_input(self):
        assert normalize_content("plain") == "plain"


# ==================== _strip_template_sections ====================


class TestStripTemplateSections:
    def test_strips_review_conclusion(self):
        text = "main content\n评审结论\nsome conclusion"
        assert "评审结论" not in _strip_template_sections(text)
        assert "main content" in _strip_template_sections(text)

    def test_strips_leftover_issues(self):
        text = "main content\n遗留问题\nissues"
        assert "遗留问题" not in _strip_template_sections(text)

    def test_no_template(self):
        text = "just content"
        assert _strip_template_sections(text) == text


# ==================== _strip_northbound_scenes ====================


class TestStripNorthboundScenes:
    def test_strips_redfish_scene(self):
        content = "场景1：Redfish接口调用\n一些北向内容\n场景2：资源协作\n一些内容"
        result = _strip_northbound_scenes(content)
        assert "北向内容" not in result
        assert "资源协作" in result

    def test_keeps_non_nb_scene(self):
        content = "场景1：资源协作接口\n一些内容"
        result = _strip_northbound_scenes(content)
        assert "资源协作" in result


# ==================== _has_northbound_intent ====================


class TestHasNorthboundIntent:
    def test_with_coop_keyword(self):
        is_nb, reason = _has_northbound_intent("标题", "包含资源协作的内容")
        assert is_nb is False

    def test_multiple_nb_keywords(self):
        is_nb, reason = _has_northbound_intent("标题", "redfish接口和web接口的调用")
        assert is_nb is True

    def test_nb_uri_paths(self):
        is_nb, reason = _has_northbound_intent("标题", "调用 /redfish/v1/ 接口")
        assert is_nb is True

    def test_no_nb_intent(self):
        is_nb, reason = _has_northbound_intent("标题", "普通MDB资源协作内容 bmc.kepler")
        assert is_nb is False


# ==================== is_mdb_related 主分类函数 ====================


class TestIsMdbRelated:
    """测试 is_mdb_related() 的各类场景。"""

    # --- 不相关的 ---

    def test_unrelated_content(self):
        related, reason = is_mdb_related("普通帖子", "这是一篇与接口无关的帖子")
        assert related is False

    def test_redfish_only(self):
        related, reason = is_mdb_related("Redfish接口设计", "使用Redfish API获取服务器信息")
        assert related is False

    def test_northbound_title_excluded(self):
        related, reason = is_mdb_related("Redfish接口新增属性", "内容描述")
        assert related is False

    # --- 强特征：标题含关键词 ---

    def test_strong_keyword_in_title_resource_cooperation(self):
        related, reason = is_mdb_related(
            "新增资源协作接口",
            "接口路径 bmc.kepler.xxx.yyy"
        )
        assert related is True
        assert "强特征" in reason

    def test_strong_keyword_in_title_interface_schema(self):
        related, reason = is_mdb_related(
            "interface.schema 校验",
            "描述内容"
        )
        assert related is True

    def test_strong_keyword_bmc_kepler_in_title(self):
        related, reason = is_mdb_related(
            "bmc.kepler 接口路径",
            "描述内容"
        )
        assert related is True

    # --- 强特征：内容含关键词 ---

    def test_strong_keyword_in_content(self):
        related, reason = is_mdb_related(
            "普通标题",
            "该接口遵循资源协作规范进行设计"
        )
        assert related is True
        assert "强特征" in reason

    def test_strong_keyword_bmc_kepler_in_content(self):
        related, reason = is_mdb_related(
            "接口评审",
            "路径为 bmc.kepler.xxx.yyy.zzz"
        )
        assert related is True

    # --- 北向接口排除 ---

    def test_title_with_northbound_keyword_excluded(self):
        """标题含北向关键词（且无"资源协作"）应排除。"""
        related, reason = is_mdb_related(
            "Web接口新增属性",
            "一些内容"
        )
        assert related is False

    def test_northbound_subject_excluded(self):
        """评审点标题以北向接口为主语应排除。"""
        related, reason = is_mdb_related(
            "redfish 新增接口属性设计",
            "内容描述"
        )
        assert related is False

    def test_coop_keyword_overrides_northbound(self):
        """含"资源协作"时，北向关键词不排除。"""
        related, reason = is_mdb_related(
            "资源协作接口新增属性",
            "路径 bmc.kepler.xxx"
        )
        assert related is True

    # --- 弱特征 + 上下文 ---

    def test_weak_keyword_with_context(self):
        related, reason = is_mdb_related(
            "bmc.xxx 资源树设计",
            "这是一个普通的资源树描述内容，前半部分提到了资源树结构"
        )
        # 标题含 bmc.，内容含弱特征"资源树"
        assert related is True

    # --- MDB 技术词 ---

    def test_technical_keyword_emitsChangedSignal(self):
        related, reason = is_mdb_related(
            "接口设计",
            "emitsChangedSignal 设置为 true"
        )
        assert related is True
        assert "技术词" in reason

    def test_technical_keyword_bmc_studio(self):
        related, reason = is_mdb_related(
            "接口设计",
            "使用 bmc.studio 工具开发"
        )
        assert related is True

    def test_technical_keyword_with_redfish_excluded(self):
        """含 Redfish 特征时，MDB 技术词不触发。"""
        related, reason = is_mdb_related(
            "接口设计",
            "emitsChangedSignal 与 redfish 的关系"
        )
        assert related is False

    # --- 模板区域排除 ---

    def test_template_section_ignored(self):
        """模板区域（评审结论后）的关键词不应影响分类。"""
        content = "普通内容\n评审结论\n本接口遵循资源协作规范"
        related, reason = is_mdb_related("普通标题", content)
        assert related is False

    # --- 纯北向内容但有 bmc.kepler ---

    def test_strong_keyword_with_pure_northbound_content(self):
        """标题含强特征但内容纯北向（无bmc.kepler）应排除。"""
        related, reason = is_mdb_related(
            "资源协作接口设计",
            "/ui/rest/ 和 /redfish/v1/ 的调用方式"
        )
        assert related is False
