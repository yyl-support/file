from flask import jsonify, g
from functools import wraps
from .logging_config import main_logger as logger


class RBACMiddleware:
    """角色鉴权：白名单校验（华为 maintainer、机器人）"""

    def __init__(self, config):
        self.config = config
        rbac_config = config.get('rbac', {})
        
        self.knowledge_upload_roles = rbac_config.get('knowledge_upload_roles', [
            'huawei_maintainer',
            'robot_service'
        ])
        self.role_claim_mapping = rbac_config.get('role_claim_mapping', {
            'huawei_maintainer': 'https://omapi.osinfra.cn/claims/roles'
        })

    def get_user_roles(self, user_info):
        """从用户信息中提取角色列表"""
        if not user_info:
            return []
        
        roles = []
        
        if 'roles' in user_info:
            roles.extend(user_info.get('roles', []))
        
        for claim_key in self.role_claim_mapping.values():
            if claim_key in user_info:
                claim_roles = user_info.get(claim_key, [])
                if isinstance(claim_roles, list):
                    roles.extend(claim_roles)
                elif isinstance(claim_roles, str):
                    roles.append(claim_roles)
        
        return roles

    def check_role(self, user_id, required_roles):
        """检查用户是否具有指定角色"""
        user_info = g.get('current_user', {})
        
        if not user_info:
            logger.warning(f"No user info found for user {user_id}")
            return False
        
        user_roles = self.get_user_roles(user_info)
        
        for role in required_roles:
            if role in user_roles:
                logger.info(f"User {user_id} has role {role}")
                return True
        
        logger.warning(f"User {user_id} lacks required roles: {required_roles}. User roles: {user_roles}")
        return False

    def require_role(self, required_roles=None):
        """角色鉴权装饰器"""
        if required_roles is None:
            required_roles = self.knowledge_upload_roles
        
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if not hasattr(g, 'current_user'):
                    return jsonify({
                        'error': 'TOKEN_MISSING',
                        'message': '请先完成 OneID 认证授权'
                    }), 401
                
                user_id = g.current_user.get('user_id')
                
                if not self.check_role(user_id, required_roles):
                    return jsonify({
                        'error': 'ROLE_DENIED',
                        'message': '您无权限执行此操作，仅华为 maintainer 或机器人可上传知识'
                    }), 403
                
                return f(*args, **kwargs)
            
            return decorated
        
        return decorator

    def require_maintainer(self, f):
        """华为maintainer角色装饰器"""
        return self.require_role(['huawei_maintainer', 'robot_service'])(f)

    def require_robot(self, f):
        """机器人角色装饰器"""
        return self.require_role(['robot_service'])(f)