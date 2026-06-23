import pytest
import unittest.mock as mock
from flask import Flask, g
from src.ForumBot.rbac_middleware import RBACMiddleware


class TestRBACMiddleware:
    
    @pytest.fixture
    def rbac_config(self):
        return {
            'rbac': {
                'knowledge_upload_roles': ['huawei_maintainer', 'robot_service'],
                'role_claim_mapping': {
                    'huawei_maintainer': 'https://omapi.osinfra.cn/claims/roles'
                }
            }
        }
    
    @pytest.fixture
    def rbac_middleware(self, rbac_config):
        return RBACMiddleware(rbac_config)
    
    @pytest.fixture
    def app(self):
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test_secret_key'
        return app
    
    def test_rbac_middleware_initialization(self, rbac_middleware):
        assert 'huawei_maintainer' in rbac_middleware.knowledge_upload_roles
        assert 'robot_service' in rbac_middleware.knowledge_upload_roles
        assert rbac_middleware.role_claim_mapping is not None
    
    def test_get_user_roles_from_roles_field(self, rbac_middleware):
        user_info = {
            'roles': ['huawei_maintainer', 'other_role']
        }
        
        roles = rbac_middleware.get_user_roles(user_info)
        
        assert 'huawei_maintainer' in roles
        assert 'other_role' in roles
    
    def test_get_user_roles_from_claim_mapping(self, rbac_middleware):
        user_info = {
            'https://omapi.osinfra.cn/claims/roles': ['huawei_maintainer']
        }
        
        roles = rbac_middleware.get_user_roles(user_info)
        
        assert 'huawei_maintainer' in roles
    
    def test_get_user_roles_mixed_sources(self, rbac_middleware):
        user_info = {
            'roles': ['role1'],
            'https://omapi.osinfra.cn/claims/roles': ['huawei_maintainer']
        }
        
        roles = rbac_middleware.get_user_roles(user_info)
        
        assert 'role1' in roles
        assert 'huawei_maintainer' in roles
    
    def test_get_user_roles_claim_string(self, rbac_middleware):
        user_info = {
            'https://omapi.osinfra.cn/claims/roles': 'huawei_maintainer'
        }
        
        roles = rbac_middleware.get_user_roles(user_info)
        
        assert 'huawei_maintainer' in roles
    
    def test_get_user_roles_empty_info(self, rbac_middleware):
        roles = rbac_middleware.get_user_roles({})
        assert len(roles) == 0
    
    def test_get_user_roles_none_info(self, rbac_middleware):
        roles = rbac_middleware.get_user_roles(None)
        assert len(roles) == 0
    
    def test_check_role_success(self, rbac_middleware, app):
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['huawei_maintainer']
            }
            
            result = rbac_middleware.check_role('test_user', ['huawei_maintainer'])
            assert result is True
    
    def test_check_role_multiple_required(self, rbac_middleware, app):
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['robot_service']
            }
            
            result = rbac_middleware.check_role('test_user', ['huawei_maintainer', 'robot_service'])
            assert result is True
    
    def test_check_role_failure(self, rbac_middleware, app):
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['regular_user']
            }
            
            result = rbac_middleware.check_role('test_user', ['huawei_maintainer'])
            assert result is False
    
    def test_check_role_no_user_info(self, rbac_middleware, app):
        with app.test_request_context('/test'):
            result = rbac_middleware.check_role('test_user', ['huawei_maintainer'])
            assert result is False
    
    def test_require_role_decorator_success(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_role(['huawei_maintainer', 'robot_service'])(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['huawei_maintainer']
            }
            
            result = decorated()
            assert result['status'] == 'success'
    
    def test_require_role_decorator_failure(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_role(['huawei_maintainer'])(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['regular_user']
            }
            
            result = decorated()
            
            assert result[1] == 403
    
    def test_require_role_decorator_no_user(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_role(['huawei_maintainer'])(test_func)
        
        with app.test_request_context('/test'):
            result = decorated()
            
            assert result[1] == 401
    
    def test_require_role_default_roles(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_role()(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['huawei_maintainer']
            }
            
            result = decorated()
            assert result['status'] == 'success'
    
    def test_require_maintainer_success(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_maintainer(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['huawei_maintainer']
            }
            
            result = decorated()
            assert result['status'] == 'success'
    
    def test_require_robot_success(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_robot(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['robot_service']
            }
            
            result = decorated()
            assert result['status'] == 'success'
    
    def test_require_robot_failure(self, rbac_middleware, app):
        def test_func():
            return {'status': 'success'}
        
        decorated = rbac_middleware.require_robot(test_func)
        
        with app.test_request_context('/test'):
            g.current_user = {
                'user_id': 'test_user',
                'roles': ['huawei_maintainer']
            }
            
            result = decorated()
            
            assert result[1] == 403