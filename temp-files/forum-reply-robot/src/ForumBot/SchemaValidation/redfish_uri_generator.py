#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redfish URI 生成器模块

提供根据评审点生成 URI 示例的功能，包括：
- LLM API 调用
- Prompt 构建
- JSON 解析和验证
"""

import httpx
import json
import logging
import re
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from redfish_common import Config, save_json, URIGenerationError


logger = logging.getLogger(__name__)


class URIGenerator:
    """URI 示例生成器"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化生成器

        Args:
            api_key: API 密钥（默认从环境变量读取）
            base_url: API 基础 URL（默认从环境变量读取）
            model: 模型名称（默认从环境变量读取）
        """
        self.api_key = api_key or Config.MODELSCOPE_API_KEY
        self.base_url = base_url or Config.MODELSCOPE_BASE_URL
        self.model = model or Config.MODELSCOPE_MODEL

        if not self.api_key:
            raise URIGenerationError("MODELSCOPE_API_KEY 未设置，请检查 config.yaml 的 schema_validation 配置")
        if not self.base_url:
            raise URIGenerationError("MODELSCOPE_BASE_URL 未设置，请检查 config.yaml 的 schema_validation 配置")
        if not self.model:
            raise URIGenerationError("MODELSCOPE_MODEL 未设置，请检查 config.yaml 的 schema_validation 配置")

        logger.info(f"使用模型: {self.model}")
        logger.info(f"API Base URL: {self.base_url}")

    def _create_llm(self) -> ChatOpenAI:
        """创建 LLM 实例"""
        # 创建自定义 httpx client 来捕获响应
        class LoggingClient(httpx.Client):
            def send(self, request, **kwargs):
                response = super().send(request, **kwargs)
                logger.info(f"响应状态码: {response.status_code}")
                try:
                    response_text = response.text
                    logger.info(f"响应内容长度: {len(response_text)} 字符")
                    # 记录前500字符用于调试
                    if response_text:
                        preview = response_text[:500] if len(response_text) > 500 else response_text
                        logger.info(f"响应预览: {preview}")
                    try:
                        response_json = response.json()
                        logger.info(f"响应JSON键: {list(response_json.keys())}")
                        if 'choices' in response_json:
                            logger.info(f"choices值: {response_json['choices']}")
                        if 'error' in response_json:
                            logger.error(f"API error字段: {response_json['error']}")
                        if 'status' in response_json:
                            logger.error(f"API status: {response_json.get('status')}")
                        if 'msg' in response_json:
                            logger.error(f"API msg: {response_json.get('msg')}")
                        if 'body' in response_json:
                            logger.error(f"API body: {response_json.get('body')}")
                    except Exception as je:
                        logger.error(f"解析JSON失败: {je}")
                except Exception as e:
                    logger.error(f"解析响应失败: {e}")
                return response

        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=LoggingClient(),
            timeout=900,
            max_retries=0  # 禁用自动重试，便于看到实际错误
        )

    def build_prompt(self, review_point: Dict[str, str]) -> str:
        """
        构建生成 URI 示例的 prompt

        Args:
            review_point: 包含 title 和 content 的评审点字典

        Returns:
            构建好的 prompt 字符串
        """
        prompt = f"""你是一个Redfish API专家。请根据以下资源描述，生成一个符合Redfish规范的JSON返回体示例。

资源描述：
{review_point['content']}

重要要求：
1. 生成完整的JSON格式的HTTP响应体
2. 包含所有必需属性，属性名必须完全正确：
   - @odata.context (注意拼写：odata不是odbtype)
   - @odata.id (注意拼写：odata)
   - @odata.type (注意拼写：odata不是odbtype)

3. 【关键】严格按照资源描述中指定的属性类型生成示例值：

**基础类型：**
   - string: 使用字符串值（如 "GPU1", "PowerSupply"）
   - integer/number: 使用数值（如 1, 42, 100.5）
   - boolean: 使用 true 或 false

**object 类型：**
   - 使用对象格式 {{...}}
   - 包含所有二级属性作为键值对
   - 示例: {{"Reading": 23.7, "DataSourceUri": ""}}

**array 类型（特别注意）：**
   - 必须使用数组格式 [...]
   - 即使只有一个元素，也必须用数组
   - 数组中每个元素是包含所有二级属性的对象
   - 示例（FanSpeedsPercent 为 array）:
     "FanSpeedsPercent": [
         {{"DataSourceUri": "/sensors/fan1", "DeviceName": "FAN1", "Reading": 4050}},
         {{"DataSourceUri": "/sensors/fan2", "DeviceName": "FAN2", "Reading": 4200}}
     ]
   - 错误示例: "FanSpeedsPercent": {{"DataSourceUri": "..."}} ← 这是 object，不是 array！

4. 默认值处理：
   - string 类型默认值为空字符串 ""（英文半角双引号）
   - number 类型默认值为 0
   - array/object 类型如有默认值按表格要求填写

5. 保持JSON格式正确且可解析
6. 只返回JSON内容，不要添加任何解释或说明
7. 【特别重要】确保属性名拼写正确：@odata.type 不是 @odbtype，@odata.id 不是 @odb.id

请严格按照类型要求生成JSON示例："""
        return prompt

    def parse_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        从 LLM 响应中解析 JSON

        Args:
            response: LLM 返回的文本

        Returns:
            解析后的 JSON 对象，失败返回 None
        """
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取第一个 { ... } 块
        brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def generate(
        self,
        review_point: Dict[str, str],
        output_file: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成 URI 返回体示例

        Args:
            review_point: 包含 title 和 content 的评审点字典
            output_file: 输出文件路径（可选）

        Returns:
            生成的 JSON 对象，失败返回 None
        """
        prompt = self.build_prompt(review_point)

        try:
            llm = self._create_llm()
            response_message = llm.invoke(prompt)
            response = response_message.content

            logger.info(f"API 响应已接收，长度: {len(response)} 字符")

        except Exception as e:
            error_str = str(e)
            logger.error(f"API调用异常: {error_str}")
            logger.error(f"异常类型: {type(e).__name__}")

            # 尝试从错误消息中提取 API 错误信息
            # langchain 错误格式: "Received response with null value for `choices`. ... Full response keys: [...]"
            keys_match = re.search(r"Full response keys: \[([^\]]+)\]", error_str)
            if keys_match:
                keys_str = keys_match.group(1)
                logger.error(f"API响应键: {keys_str}")

            # 检查是否是 API 错误响应
            if any(kw in error_str for kw in ['status', 'msg', 'body', 'error_code']):
                logger.error(f"API 调用出错: {error_str}")

                # 尝试提取错误信息
                status_match = re.search(r"['\"]status['\"]\\s*:\\s*['\"]([^'\"]+)['\"]", error_str)

                # 尝试提取错误信息
                status_match = re.search(r"['\"]status['\"]\\s*:\\s*['\"]([^'\"]+)['\"]", error_str)
                msg_match = re.search(r"['\"]msg['\"]\\s*:\\s*['\"]([^'\"]+)['\"]", error_str)

                if status_match:
                    logger.error(f"  状态码: {status_match.group(1)}")
                if msg_match:
                    logger.error(f"  错误消息: {msg_match.group(1)}")

            raise URIGenerationError(f"API 调用失败: {e}")

        # 解析 JSON
        uri_sample = self.parse_json_from_response(response)

        if not uri_sample:
            logger.error(f"无法从响应中解析有效的 JSON")
            logger.debug(f"响应内容: {response[:500]}...")
            return None

        # 保存到文件
        if output_file:
            save_json(uri_sample, output_file)
            logger.info(f"URI 示例已保存到: {output_file}")

        return uri_sample


