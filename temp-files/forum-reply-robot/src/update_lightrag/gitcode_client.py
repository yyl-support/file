"""
GitCode API 客户端（简化版，只保留增量更新需要的方法）
"""
import requests
import json
import time
from typing import Dict, List, Optional
import base64
from datetime import datetime
from src.ForumBot.logging_config import main_logger as logger


class GitCodeClient:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://api.gitcode.com/api/v5"
        self.owner = config.get('gitcode', {}).get('owner', 'openUBMC')
        self.repo = config.get('gitcode', {}).get('repo', 'docs')
        self.api_token = config.get('gitcode', {}).get('api_token', '')
        self.verify_ssl = config.get('gitcode', {}).get('verify_ssl', True)
        self.request_delay = config.get('gitcode', {}).get('request_delay', 0.5)
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'PRIVATE-TOKEN': self.api_token
        }
    
    def get_file_content(self, path: str, ref: str = 'main') -> Optional[str]:
        """
        获取文件内容
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/contents/{path}"
        params = {'ref': ref}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, 
                                   timeout=10, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()
            
            if data.get('encoding') == 'base64':
                content = base64.b64decode(data.get('content', '')).decode('utf-8')
                return content
            else:
                return data.get('content', '')
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取文件内容失败 {path}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析文件内容JSON失败 {path}: {e}")
            return None
    
    def get_commits_since(self, since: str, per_page: int = 100) -> List[Dict]:
        """
        获取指定时间后的提交列表（支持分页，获取所有提交）
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/commits"
        
        # 转换时间格式：将 +00:00 转换为 Z
        try:
            dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            since_formatted = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            logger.warning(f"时间格式转换失败，使用原始值: {e}")
            since_formatted = since
        
        all_commits = []
        page = 1
        
        try:
            logger.debug(f"获取 {since} 后的提交列表")
            
            while True:
                params = {'since': since_formatted, 'per_page': per_page, 'page': page}
                
                response = requests.get(url, headers=self.headers, params=params, 
                                       timeout=10, verify=self.verify_ssl)
                
                time.sleep(self.request_delay)
                
                if response.status_code != 200:
                    logger.error(f"获取提交列表失败: 状态码 {response.status_code}, 响应: {response.text[:200]}")
                    break
                
                data = response.json()
                
                if not isinstance(data, list):
                    logger.warning(f"获取提交列表返回格式异常")
                    break
                
                if len(data) == 0:
                    logger.debug(f"第 {page} 页无数据，分页结束")
                    break
                
                all_commits.extend(data)
                logger.debug(f"第 {page} 页获取 {len(data)} 个提交，累计 {len(all_commits)} 个")
                
                if len(data) < per_page:
                    logger.debug(f"第 {page} 页数据少于 {per_page} 条，分页结束")
                    break
                
                page += 1
            
            logger.info(f"找到 {len(all_commits)} 个提交")
            return all_commits
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取提交列表失败: {e}")
            return all_commits
        except json.JSONDecodeError as e:
            logger.error(f"解析提交列表JSON失败: {e}")
            return all_commits
    
    def get_compare_files(self, base: str, head: str) -> List[Dict]:
        """
        获取两个提交之间的变更文件列表
        """
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/compare/{base}...{head}"
        
        max_retries = 2
        retry_delay = 30
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"获取 {base[:8]}...{head[:8]} 之间的变更文件")
                response = requests.get(url, headers=self.headers, 
                                       timeout=10, verify=self.verify_ssl)
                
                time.sleep(self.request_delay)
                
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        logger.warning(f"API速率限制，等待 {retry_delay} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"API速率限制，已达到最大重试次数")
                        return []
                
                if response.status_code != 200:
                    logger.warning(f"获取变更文件失败: 状态码 {response.status_code}, URL: {url}")
                    logger.warning(f"响应内容: {response.text[:200]}")
                    return []
                
                data = response.json()
                
                # 解析 files 数组
                files = []
                if 'files' in data and isinstance(data['files'], list):
                    for file_info in data['files']:
                        if not isinstance(file_info, dict):
                            logger.warning(f"文件信息格式异常: {type(file_info)}")
                            continue
                        
                        filename = file_info.get('filename', '')
                        status = file_info.get('status', '')
                        if filename and filename.endswith('.md'):
                            files.append({
                                'filename': filename,
                                'status': status
                            })
                
                logger.debug(f"找到 {len(files)} 个变更文件")
                return files
                
            except requests.exceptions.RequestException as e:
                logger.error(f"获取变更文件失败: {e}")
                return []
            except json.JSONDecodeError as e:
                logger.error(f"解析变更文件JSON失败: {e}")
                return []
        
        return []