import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ForumBot.image_processor import ImageProcessor


class TestImageProcessor:
    """测试 ImageProcessor 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'api': {
                'base_url': 'http://test.com',
                'api_key': 'test_key'
            },
            'image_processing': {
                'base_url': 'https://discuss.openubmc.cn',
                'model1': 'model1',
                'model2': 'model2',
                'model3': 'model3'
            }
        }

    @pytest.fixture
    def client(self, config):
        """创建 ImageProcessor 实例"""
        return ImageProcessor(config)

    def test_init(self, client, config):
        """测试初始化"""
        assert client.config == config
        assert len(client.model_list) == 3

    def test_extract_image_info_from_text_empty(self, client):
        """测试从空文本提取图像信息"""
        result = client.extract_image_info_from_text('')
        assert result == []

    def test_extract_image_info_from_text_no_images(self, client):
        """测试从没有图像的文本提取信息"""
        text = 'This is plain text without images'
        result = client.extract_image_info_from_text(text)
        assert result == []

    def test_extract_image_info_from_text_single_image(self, client):
        """测试从单个图像提取信息"""
        text = 'Text with [img: (image.jpg)]'
        result = client.extract_image_info_from_text(text)
        
        assert len(result) == 1
        assert result[0]['url'] == 'https://discuss.openubmc.cn/image.jpg'
        assert result[0]['original_tag'] == '[img: (image.jpg)]'

    def test_extract_image_info_from_text_multiple_images(self, client):
        """测试从多个图像提取信息"""
        text = 'Text with [img: (image1.jpg)] and [img: (image2.png)]'
        result = client.extract_image_info_from_text(text)
        
        assert len(result) == 2
        assert result[0]['url'] == 'https://discuss.openubmc.cn/image1.jpg'
        assert result[1]['url'] == 'https://discuss.openubmc.cn/image2.png'

    def test_extract_image_info_from_text_absolute_url(self, client):
        """测试绝对URL图像"""
        text = 'Text with [img: (https://example.com/image.jpg)]'
        result = client.extract_image_info_from_text(text)
        
        assert len(result) == 1
        assert result[0]['url'] == 'https://example.com/image.jpg'

    def test_process_image_content_user_avatar(self, client):
        """测试处理用户头像"""
        result = client.process_image_content('https://example.com/user_avatar.jpg', 'user_question')
        assert result == 'USER_AVATAR'

    def test_process_image_content_empty_url(self, client):
        """测试空URL"""
        result = client.process_image_content('', 'user_question')
        assert result == '无法获取图像内容'

    @patch('src.ForumBot.image_processor.ImageProcessor._call_multimodal_model')
    def test_process_image_content_user_question_context(self, mock_call, client):
        """测试用户问题上下文"""
        mock_call.return_value = 'Image description'
        
        result = client.process_image_content('https://example.com/image.jpg', 'user_question')
        
        assert result == 'Image description'
        mock_call.assert_called_once()

    @patch('src.ForumBot.image_processor.ImageProcessor._call_multimodal_model')
    def test_process_image_content_best_answer_context(self, mock_call, client):
        """测试最佳答案上下文"""
        mock_call.return_value = 'Image analysis'
        
        result = client.process_image_content('https://example.com/image.jpg', 'best_answer')
        
        assert result == 'Image analysis'
        mock_call.assert_called_once()

    @patch('src.ForumBot.image_processor.ImageProcessor._call_multimodal_model')
    def test_process_image_content_exception(self, mock_call, client):
        """测试处理异常"""
        mock_call.side_effect = Exception('Model error')
        
        result = client.process_image_content('https://example.com/image.jpg', 'user_question')
        
        assert result == '图像内容分析失败'

    @patch('src.ForumBot.image_processor.OpenAI')
    def test_call_multimodal_model_success(self, mock_openai, client):
        """测试成功调用多模态模型"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Image content description'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        # 替换client的client为mock
        original_client = client.client
        client.client = mock_client

        result = client._call_multimodal_model('https://example.com/image.jpg', 'Describe this image', 123)

        assert result == 'Image content description'
        
        # 恢复原始client
        client.client = original_client

    @patch('src.ForumBot.image_processor.OpenAI')
    def test_call_multimodal_model_retry(self, mock_openai, client):
        """测试多模型重试"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Success after retry'
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = [
            Exception('First model failed'),
            mock_response
        ]
        mock_openai.return_value = mock_client

        # 替换client的client为mock
        original_client = client.client
        client.client = mock_client

        result = client._call_multimodal_model('https://example.com/image.jpg', 'Describe this image', 123)

        assert result == 'Success after retry'
        assert mock_client.chat.completions.create.call_count == 2
        
        # 恢复原始client
        client.client = original_client

    @patch('src.ForumBot.image_processor.ImageProcessor.extract_image_info_from_text')
    @patch('src.ForumBot.image_processor.ImageProcessor.process_image_content')
    def test_enhance_text_with_image_descriptions_user_avatar(self, mock_process, mock_extract, client):
        """测试增强文本 - 用户头像"""
        mock_extract.return_value = [
            {'url': 'https://example.com/user_avatar.jpg', 'original_tag': '[img: (user_avatar.jpg)]'}
        ]
        mock_process.return_value = 'USER_AVATAR'

        text = 'Text with [img: (user_avatar.jpg)]'
        result = client.enhance_text_with_image_descriptions(text, 'user_question', 123)

        assert '[img: (user_avatar.jpg)]' not in result
        assert 'USER_AVATAR' not in result

    @patch('src.ForumBot.image_processor.ImageProcessor.extract_image_info_from_text')
    @patch('src.ForumBot.image_processor.ImageProcessor.process_image_content')
    def test_enhance_text_with_image_descriptions_normal_image(self, mock_process, mock_extract, client):
        """测试增强文本 - 正常图像"""
        mock_extract.return_value = [
            {'url': 'https://example.com/image.jpg', 'original_tag': '[img: (image.jpg)]'}
        ]
        mock_process.return_value = 'This is a screenshot of error log'

        text = 'Text with [img: (image.jpg)]'
        result = client.enhance_text_with_image_descriptions(text, 'user_question', 123)

        assert '[img: (image.jpg)]' not in result
        assert '[图片: This is a screenshot of error log]' in result

    @patch('src.ForumBot.image_processor.ImageProcessor.extract_image_info_from_text')
    def test_enhance_text_with_image_descriptions_no_images(self, mock_extract, client):
        """测试增强文本 - 没有图像"""
        mock_extract.return_value = []

        text = 'Plain text without images'
        result = client.enhance_text_with_image_descriptions(text, 'user_question', 123)

        assert result == text