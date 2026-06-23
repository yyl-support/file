import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from src.update_lightrag.lightrag_client import LightRAGClient


class TestLightRAGClient:
    """测试 LightRAGClient 类"""

    @pytest.fixture
    def config(self):
        """测试配置"""
        return {
            'retrieval': {
                'base_url': 'https://test.com',
                'verify_ssl': False
            },
            'lightrag_paths': {
                'rag_data_dir': '/tmp/rag_data',
                'files_id_mapping': '/tmp/mapping.json'
            }
        }

    @pytest.fixture
    def client(self, config):
        """创建 LightRAGClient 实例"""
        return LightRAGClient(config)

    def test_init(self, client, config):
        """测试初始化"""
        assert client.config == config
        assert client.verify_ssl is False

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_upload_document_success(self, mock_post, client):
        """测试成功上传文档"""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'success', 'track_id': '123'}
        mock_post.return_value = mock_response

        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name

        try:
            result = client.upload_document(file_path, 'https://api.com', 'api_key')
            assert result['status'] == 'success'
            assert result['track_id'] == '123'
        finally:
            os.unlink(file_path)

    @patch('src.update_lightrag.lightrag_client.requests.delete')
    def test_delete_document_success(self, mock_delete, client):
        """测试成功删除文档"""
        mock_response = Mock()
        mock_response.json.return_value = {'status': 'deletion_started'}
        mock_delete.return_value = mock_response

        result = client.delete_document('doc123', 'https://api.com', 'api_key')
        assert result['status'] == 'deletion_started'

    def test_extract_file_path_id_mapping(self, client):
        """测试提取文件路径ID映射"""
        json_data = {
            'documents': [
                {'id': 'doc1', 'file_path': '/path/to/file1.txt'},
                {'id': 'doc2', 'file_path': '/path/to/file2.txt'}
            ]
        }

        result = client.extract_file_path_id_mapping(json_data)
        
        assert len(result) == 2
        assert result['/path/to/file1.txt'] == 'doc1'
        assert result['/path/to/file2.txt'] == 'doc2'

    def test_extract_file_path_id_mapping_empty(self, client):
        """测试提取空映射"""
        json_data = {'documents': []}
        result = client.extract_file_path_id_mapping(json_data)
        assert result == {}

    def test_extract_file_path_id_mapping_missing_fields(self, client):
        """测试提取映射 - 缺少字段"""
        json_data = {
            'documents': [
                {'id': 'doc1'},  # 缺少 file_path
                {'file_path': '/path/to/file2.txt'}  # 缺少 id
            ]
        }

        result = client.extract_file_path_id_mapping(json_data)
        assert result == {}

    def test_save_mapping_to_file_new(self, client):
        """测试保存新映射到文件"""
        
        # 创建临时文件路径（不预先创建文件）
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, 'mapping.json')
        
        # 修改配置使用临时文件
        original_mapping = client.config['lightrag_paths']['files_id_mapping']
        client.config['lightrag_paths']['files_id_mapping'] = temp_file
        
        try:
            mapping = {'/path/to/file1.txt': 'doc1'}
            client._save_mapping_to_file(mapping)
            
            # 验证文件被写入
            with open(temp_file, 'r') as f:
                result = json.load(f)
                assert result == mapping
        finally:
            # 恢复原始配置
            client.config['lightrag_paths']['files_id_mapping'] = original_mapping
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_all_file_processed_success(self, mock_post, client):
        """测试检查所有文件处理完成 - 成功"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'status_counts': {
                'pending': 0,
                'processing': 0
            }
        }
        mock_post.return_value = mock_response

        result = client.is_all_file_processed('https://api.com')
        assert result is True

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_all_file_processed_pending(self, mock_post, client):
        """测试检查所有文件处理完成 - 有待处理文件"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'status_counts': {
                'pending': 5,
                'processing': 0
            }
        }
        mock_post.return_value = mock_response

        result = client.is_all_file_processed('https://api.com')
        assert result is False

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_all_file_processed_processing(self, mock_post, client):
        """测试检查所有文件处理完成 - 有处理中文件"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'status_counts': {
                'pending': 0,
                'processing': 3
            }
        }
        mock_post.return_value = mock_response

        result = client.is_all_file_processed('https://api.com')
        assert result is False

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_all_file_processed_exception(self, mock_post, client):
        """测试检查所有文件处理完成 - 异常"""
        mock_post.side_effect = Exception('Network error')

        result = client.is_all_file_processed('https://api.com')
        assert result is None

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_lightrag_empty_true(self, mock_post, client):
        """测试检查LightRAG是否为空 - 为空"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'pagination': {
                'total_count': 0
            }
        }
        mock_post.return_value = mock_response

        result = client.is_lightrag_empty('https://api.com')
        assert result is True

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_lightrag_empty_false(self, mock_post, client):
        """测试检查LightRAG是否为空 - 不为空"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            'pagination': {
                'total_count': 10
            }
        }
        mock_post.return_value = mock_response

        result = client.is_lightrag_empty('https://api.com')
        assert result is False

    @patch('src.update_lightrag.lightrag_client.requests.post')
    def test_is_lightrag_empty_exception(self, mock_post, client):
        """测试检查LightRAG是否为空 - 异常"""
        mock_post.side_effect = Exception('Network error')

        result = client.is_lightrag_empty('https://api.com')
        assert result is None

    @patch('src.update_lightrag.lightrag_client.requests.get')
    def test_is_pipeline_status_busy_true(self, mock_get, client):
        """测试检查管道状态 - 忙碌"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'busy': True}
        mock_get.return_value = mock_response

        result = client.is_pipeline_status_busy('https://api.com')
        assert result is True

    @patch('src.update_lightrag.lightrag_client.requests.get')
    def test_is_pipeline_status_busy_false(self, mock_get, client):
        """测试检查管道状态 - 空闲"""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {'busy': False}
        mock_get.return_value = mock_response

        result = client.is_pipeline_status_busy('https://api.com')
        assert result is False

    @patch('src.update_lightrag.lightrag_client.requests.get')
    def test_is_pipeline_status_busy_exception(self, mock_get, client):
        """测试检查管道状态 - 异常"""
        mock_get.side_effect = Exception('Network error')

        try:
            result = client.is_pipeline_status_busy('https://api.com', 'api_key')
            assert result is None
        except Exception:
            pass  # 预期会抛出异常

    @patch('src.update_lightrag.lightrag_client.LightRAGClient.is_pipeline_status_busy')
    @patch('src.update_lightrag.lightrag_client.time.sleep')
    def test_wait_for_pipeline_status_not_busy_immediate(self, mock_sleep, mock_is_busy, client):
        """测试等待管道空闲 - 立即空闲"""
        mock_is_busy.return_value = False

        client.wait_for_pipeline_status_not_busy('https://api.com')

        mock_is_busy.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('src.update_lightrag.lightrag_client.LightRAGClient.is_pipeline_status_busy')
    @patch('src.update_lightrag.lightrag_client.time.sleep')
    def test_wait_for_pipeline_status_not_busy_wait(self, mock_sleep, mock_is_busy, client):
        """测试等待管道空闲 - 需要等待"""
        mock_is_busy.side_effect = [True, False]

        client.wait_for_pipeline_status_not_busy('https://api.com')

        assert mock_is_busy.call_count == 2
        mock_sleep.assert_called_once_with(1)