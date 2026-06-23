import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import json
import tempfile


class TestUpdateLightragImageProcessor:
    """测试 update_lightrag 模块的 ImageProcessor 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'api': {
                'base_url': 'http://test.com',
                'api_key': 'test_key'
            },
            'image_processing': {
                'model1': 'model1',
                'model2': 'model2',
                'model3': 'model3'
            },
            'lightrag_paths': {
                'rag_data_dir': '/tmp/test_rag_data'
            }
        }

    @pytest.fixture
    def processor(self, config):
        """创建 ImageProcessor 实例"""
        with patch('src.update_lightrag.image_processor.OpenAI'):
            from src.update_lightrag.image_processor import ImageProcessor
            return ImageProcessor(config)

    def test_init(self, processor, config):
        """测试初始化"""
        assert processor.config == config
        assert len(processor.model_list) == 3

    def test_process_image_from_files_not_exists(self, processor):
        """测试处理图片文件 - 文件列表不存在"""
        nonexistent_file = '/tmp/nonexistent_file_list.txt'
        
        result = processor.process_image_from_files(nonexistent_file)
        
        assert result is None

    def test_process_image_from_files_empty_list(self, processor):
        """测试处理图片文件 - 空文件列表"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('')
            file_list_path = f.name
        
        try:
            result = processor.process_image_from_files(file_list_path)
            
            assert result is None
        finally:
            os.unlink(file_list_path)

    def test_process_image_from_files_filter_topic_json(self, processor):
        """测试处理图片文件 - 只处理topic.json文件"""
        with tempfile.TemporaryDirectory() as rag_dir:
            processor.config['lightrag_paths']['rag_data_dir'] = rag_dir
            
            topic_json_path = os.path.join(rag_dir, 'test_topic.json')
            other_json_path = os.path.join(rag_dir, 'test_other.json')
            
            with open(topic_json_path, 'w', encoding='utf-8') as f:
                json.dump({'question': 'test question'}, f)
            with open(other_json_path, 'w', encoding='utf-8') as f:
                json.dump({'question': 'test question'}, f)
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('test_topic.json\n')
                f.write('test_other.json\n')
                file_list_path = f.name
            
            try:
                with patch.object(processor, 'process_image_content_from_json_file') as mock_process:
                    mock_process.return_value = None
                    
                    result = processor.process_image_from_files(file_list_path)

                    mock_process.assert_called_once()
                    assert os.path.normpath(mock_process.call_args[0][0]) == os.path.normpath(topic_json_path)
            finally:
                os.unlink(file_list_path)

    def test_process_image_from_files_skip_non_topic_json(self, processor):
        """测试处理图片文件 - 跳过非topic.json文件"""
        with tempfile.TemporaryDirectory() as rag_dir:
            processor.config['lightrag_paths']['rag_data_dir'] = rag_dir
            
            md_file_path = os.path.join(rag_dir, 'docs_zh_test.md')
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write('test content')
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('docs_zh_test.md\n')
                file_list_path = f.name
            
            try:
                with patch.object(processor, 'process_image_content_from_json_file') as mock_process:
                    mock_process.return_value = None
                    
                    result = processor.process_image_from_files(file_list_path)
                    
                    mock_process.assert_not_called()
            finally:
                os.unlink(file_list_path)

    def test_process_image_from_files_file_not_found(self, processor):
        """测试处理图片文件 - topic.json文件不存在"""
        with tempfile.TemporaryDirectory() as rag_dir:
            processor.config['lightrag_paths']['rag_data_dir'] = rag_dir
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('nonexistent_topic.json\n')
                file_list_path = f.name
            
            try:
                with patch.object(processor, 'process_image_content_from_json_file') as mock_process:
                    result = processor.process_image_from_files(file_list_path)
                    
                    mock_process.assert_not_called()
            finally:
                os.unlink(file_list_path)

    @patch('src.update_lightrag.image_processor.ImageProcessor.enhance_text_with_image_descriptions')
    def test_process_image_content_from_json_file_question(self, mock_enhance, processor):
        """测试从JSON文件处理图片内容 - 处理question"""
        mock_enhance.return_value = 'enhanced question'
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({'question': 'test question'}, f)
            json_file_path = f.name
        
        try:
            processor.process_image_content_from_json_file(json_file_path)
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['question'] == 'enhanced question'
        finally:
            os.unlink(json_file_path)

    @patch('src.update_lightrag.image_processor.ImageProcessor.enhance_text_with_image_descriptions')
    def test_process_image_content_from_json_file_reply_posts(self, mock_enhance, processor):
        """测试从JSON文件处理图片内容 - 处理reply_posts"""
        mock_enhance.return_value = 'enhanced reply'
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                'question': 'test question',
                'reply_posts': [{'text': 'test reply'}]
            }, f)
            json_file_path = f.name
        
        try:
            processor.process_image_content_from_json_file(json_file_path)
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data['reply_posts'][0]['text'] == 'enhanced reply'
        finally:
            os.unlink(json_file_path)

    @patch('src.update_lightrag.image_processor.ImageProcessor.enhance_text_with_image_descriptions')
    def test_process_image_content_from_json_file_empty_reply(self, mock_enhance, processor):
        """测试从JSON文件处理图片内容 - 空 reply_posts"""
        mock_enhance.return_value = 'enhanced'
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                'question': 'test question',
                'reply_posts': []
            }, f)
            json_file_path = f.name
        
        try:
            processor.process_image_content_from_json_file(json_file_path)
            
            mock_enhance.assert_called_once_with('test question')
        finally:
            os.unlink(json_file_path)

    def test_enhance_text_with_image_descriptions_no_images(self, processor):
        """测试增强文本内容 - 无图片"""
        text = 'Plain text without images'
        
        result = processor.enhance_text_with_image_descriptions(text)
        
        assert result == text

    @patch('src.update_lightrag.image_processor.ImageProcessor.process_image_content')
    def test_enhance_text_with_image_descriptions_with_image(self, mock_process, processor):
        """测试增强文本内容 - 包含图片"""
        mock_process.return_value = 'Image description'
        
        text = 'Check this image: https://example.com/test.png'
        
        result = processor.enhance_text_with_image_descriptions(text)
        
        assert '[图片: Image description]' in result
        assert 'https://example.com/test.png' not in result

    @patch('src.update_lightrag.image_processor.ImageProcessor.process_image_content')
    def test_enhance_text_with_image_descriptions_multiple_images(self, mock_process, processor):
        """测试增强文本内容 - 多个图片"""
        mock_process.side_effect = ['Desc 1', 'Desc 2']
        
        text = 'Image 1: https://example.com/img1.jpg and Image 2: https://example.com/img2.png'
        
        result = processor.enhance_text_with_image_descriptions(text)
        
        assert '[图片: Desc 1]' in result
        assert '[图片: Desc 2]' in result

    @patch('src.update_lightrag.image_processor.ImageProcessor._call_multimodel_model')
    def test_process_image_content_success(self, mock_call, processor):
        """测试处理图片内容 - 成功"""
        mock_call.return_value = 'Image content'
        
        result = processor.process_image_content('https://example.com/image.png')
        
        assert result == 'Image content'

    def test_process_image_content_empty_url(self, processor):
        """测试处理图片内容 - 空URL"""
        result = processor.process_image_content('')
        
        assert result == '无法获取图像内容'

    @patch('src.update_lightrag.image_processor.ImageProcessor._call_multimodel_model')
    def test_process_image_content_exception(self, mock_call, processor):
        """测试处理图片内容 - 异常"""
        mock_call.side_effect = Exception('Model error')
        
        result = processor.process_image_content('https://example.com/image.png')
        
        assert result == 'https://example.com/image.png'

    def test_call_multimodel_model_success(self, processor):
        """测试调用多模态模型 - 成功"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Image description'
        
        processor.client.chat.completions.create = Mock(return_value=mock_response)
        
        result = processor._call_multimodel_model('https://example.com/image.png', 'Describe this')
        
        assert result == 'Image description'
        processor.client.chat.completions.create.assert_called_once()

    def test_call_multimodel_model_retry_success(self, processor):
        """测试调用多模态模型 - 重试成功"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Success after retry'
        
        processor.client.chat.completions.create = Mock()
        processor.client.chat.completions.create.side_effect = [
            Exception('First model failed'),
            mock_response
        ]
        
        result = processor._call_multimodel_model('https://example.com/image.png', 'Describe this')
        
        assert result == 'Success after retry'
        assert processor.client.chat.completions.create.call_count == 2

    def test_call_multimodel_model_all_fail(self, processor):
        """测试调用多模态模型 - 所有模型失败"""
        processor.client.chat.completions.create = Mock()
        processor.client.chat.completions.create.side_effect = [
            Exception('Model 1 failed'),
            Exception('Model 2 failed'),
            Exception('Model 3 failed')
        ]
        
        with pytest.raises(Exception) as exc_info:
            processor._call_multimodel_model('https://example.com/image.png', 'Describe this')
        
        assert 'Model 3 failed' in str(exc_info.value)
        assert processor.client.chat.completions.create.call_count == 3
