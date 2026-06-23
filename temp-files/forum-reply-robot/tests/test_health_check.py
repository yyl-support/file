"""
Unit tests for /startup and /health endpoints
"""
import pytest
from flask import Flask
from unittest.mock import Mock, patch
import threading


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from main import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestStartupEndpoint:
    """Tests for /startup endpoint"""

    def test_startup_endpoint_returns_503_when_not_initialized(self, client):
        """Test that /startup returns 503 when service is not initialized"""
        with patch('main.service_initialized', False):
            response = client.get('/startup')
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'not_ready'
            assert 'startup in progress' in data['message']

    def test_startup_endpoint_returns_200_when_initialized(self, client):
        """Test that /startup returns 200 when service is initialized"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/startup')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ready'
            assert 'startup completed' in data['message']

    def test_startup_endpoint_returns_503_when_monitor_instance_none(self, client):
        """Test that /startup returns 503 when monitor_instance is None"""
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', None):
            response = client.get('/startup')
            assert response.status_code == 503

    def test_startup_endpoint_returns_200_even_if_thread_dead(self, client):
        """Test that /startup returns 200 even if monitor_thread is dead (startup only checks initialization)"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/startup')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ready'


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_endpoint_returns_503_when_not_initialized(self, client):
        """Test that /health returns 503 when service is not initialized"""
        with patch('main.service_initialized', False):
            response = client.get('/health')
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'unhealthy'

    def test_health_endpoint_returns_503_when_monitor_instance_none(self, client):
        """Test that /health returns 503 when monitor_instance is None"""
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', None), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health')
            assert response.status_code == 503

    def test_health_endpoint_returns_503_when_monitor_thread_none(self, client):
        """Test that /health returns 503 when monitor_thread is None"""
        mock_monitor = Mock()
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', None):
            response = client.get('/health')
            assert response.status_code == 503

    def test_health_endpoint_returns_503_when_thread_not_alive(self, client):
        """Test that /health returns 503 when monitor_thread is not alive"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health')
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'unhealthy'
            assert 'not running' in data['message']

    def test_health_endpoint_returns_200_when_all_components_healthy(self, client):
        """Test that /health returns 200 when all components are healthy"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'running normally' in data['message']

    def test_health_endpoint_returns_json_content_type(self, client):
        """Test that /health returns JSON content type"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health')
            assert response.content_type == 'application/json'


class TestHealthDetailEndpoint:
    """Tests for /health/detail endpoint"""

    def test_health_detail_returns_503_when_not_initialized(self, client):
        """Test that /health/detail returns 503 when not initialized"""
        with patch('main.service_initialized', False):
            response = client.get('/health/detail')
            assert response.status_code == 503
            data = response.get_json()
            assert data['status'] == 'unhealthy'
            assert 'components' in data

    def test_health_detail_returns_200_when_healthy(self, client):
        """Test that /health/detail returns 200 and detailed status"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health/detail')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert data['components']['service_initialized'] == True
            assert data['components']['monitor_instance'] == True
            assert data['components']['monitor_thread_alive'] == True

    def test_health_detail_shows_thread_status(self, client):
        """Test that /health/detail shows thread alive status"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            response = client.get('/health/detail')
            data = response.get_json()
            assert data['components']['monitor_thread_alive'] == False


class TestStartupVsHealthBehavior:
    """Tests to verify difference between /startup and /health behavior"""

    def test_startup_less_strict_than_health(self, client):
        """Test that /startup is less strict than /health (doesn't check thread alive)"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = False
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            startup_response = client.get('/startup')
            health_response = client.get('/health')
            
            assert startup_response.status_code == 200
            assert health_response.status_code == 503

    def test_both_endpoints_503_before_initialization(self, client):
        """Test that both endpoints return 503 before initialization"""
        with patch('main.service_initialized', False):
            startup_response = client.get('/startup')
            health_response = client.get('/health')
            
            assert startup_response.status_code == 503
            assert health_response.status_code == 503

    def test_both_endpoints_200_after_full_initialization(self, client):
        """Test that both endpoints return 200 after full initialization"""
        mock_monitor = Mock()
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        
        with patch('main.service_initialized', True), \
             patch('main.monitor_instance', mock_monitor), \
             patch('main.monitor_thread', mock_thread):
            startup_response = client.get('/startup')
            health_response = client.get('/health')
            
            assert startup_response.status_code == 200
            assert health_response.status_code == 200