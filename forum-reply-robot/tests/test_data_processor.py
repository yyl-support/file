import pytest
import json
import re


def format_search_results_as_json(search_results):
    """
    将搜索结果格式化为JSON字符串
    """
    if not search_results:
        return ""
    json_objects = []
    for i in range(1, len(search_results) + 1):
        json_obj = {
            "id": i,
            "title": str(search_results[i - 1].get('title', '')),
            "textContent": str(search_results[i - 1].get('textContent', ''))
        }
        json_objects.append(json_obj)
    json_unit_str = json.dumps(json_objects, ensure_ascii=False)
    json_str = f"""
-----Search Result-----

```json
{json_unit_str}
```

"""
    return json_str


def extract_json_blocks(text, max_blocks=3):
    """
    从文本中提取由'''json和'''包裹的JSON格式内容
    """
    pattern = r"```json\s*(.*?)\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[:max_blocks]


class TestFormatSearchResultsAsJson:
    """测试 format_search_results_as_json 函数"""

    def test_format_search_results_empty(self):
        """测试空搜索结果"""
        result = format_search_results_as_json([])
        assert result == ""

    def test_format_search_results_single(self):
        """测试单个搜索结果"""
        search_results = [
            {
                'title': 'Test Title',
                'textContent': 'Test Content'
            }
        ]
        result = format_search_results_as_json(search_results)
        assert 'Test Title' in result
        assert 'Test Content' in result
        assert '-----Search Result-----' in result

    def test_format_search_results_multiple(self):
        """测试多个搜索结果"""
        search_results = [
            {
                'title': 'Title 1',
                'textContent': 'Content 1'
            },
            {
                'title': 'Title 2',
                'textContent': 'Content 2'
            }
        ]
        result = format_search_results_as_json(search_results)
        assert 'Title 1' in result
        assert 'Title 2' in result
        assert 'Content 1' in result
        assert 'Content 2' in result

    def test_format_search_results_with_missing_fields(self):
        """测试缺少字段的搜索结果"""
        search_results = [
            {
                'title': 'Only Title'
            },
            {
                'textContent': 'Only Content'
            }
        ]
        result = format_search_results_as_json(search_results)
        assert 'Only Title' in result
        assert 'Only Content' in result


class TestExtractJsonBlocks:
    """测试 extract_json_blocks 函数"""

    def test_extract_json_blocks_empty(self):
        """测试空文本"""
        result = extract_json_blocks("")
        assert result == []

    def test_extract_json_blocks_single(self):
        """测试单个JSON块"""
        text = '''```json
{"key": "value"}
```'''
        result = extract_json_blocks(text)
        assert len(result) == 1
        assert json.loads(result[0]) == {"key": "value"}

    def test_extract_json_blocks_multiple(self):
        """测试多个JSON块"""
        text = '''```json
{"key1": "value1"}
```
Some text
```json
{"key2": "value2"}
```'''
        result = extract_json_blocks(text)
        assert len(result) == 2
        assert json.loads(result[0]) == {"key1": "value1"}
        assert json.loads(result[1]) == {"key2": "value2"}

    def test_extract_json_blocks_max_blocks(self):
        """测试最大块数限制"""
        text = '''```json
{"key1": "value1"}
```
```json
{"key2": "value2"}
```
```json
{"key3": "value3"}
```
```json
{"key4": "value4"}
```'''
        result = extract_json_blocks(text, max_blocks=3)
        assert len(result) == 3

    def test_extract_json_blocks_no_json(self):
        """测试没有JSON块的文本"""
        text = "Just some text without JSON blocks"
        result = extract_json_blocks(text)
        assert result == []

    def test_extract_json_blocks_with_whitespace(self):
        """测试带空格的JSON块"""
        text = '''```json   
  {"key": "value"}   
```'''
        result = extract_json_blocks(text)
        assert len(result) == 1
        assert json.loads(result[0]) == {"key": "value"}