"""
使用 GitCode API 方式获取文档（增量更新）
只获取上次更新时间以来的提交记录，从提交记录里获取变更的文件
"""
import os
import json
from typing import List, Dict, Optional, Union
from .gitcode_client import GitCodeClient
from src.ForumBot.logging_config import main_logger as logger


class GitCodeAPIIncrementFetcher:
    def __init__(self, config):
        self.config = config
        self.gitcode_client = GitCodeClient(config)
        self.base_path = config.get('gitcode', {}).get('base_path', 'docs/zh/development')
        self.output_dir = config['lightrag_paths']['rag_data_dir']
        self.update_files_path = config['lightrag_paths']['new_rag_files']
        self.delete_files_path = config['lightrag_paths'].get('delete_rag_files_id', '')
        self.skip_dirs = config.get('gitcode', {}).get('skip_dirs', ['images'])

    def get_updated_files_by_commits(self, last_check_time: str) -> tuple[List[str], List[str]]:
        """
        获取自上次检查以来更新的文件（基于提交，使用 GitCode API）
        """
        logger.info(f"检查自 {last_check_time} 以来的更新文件（基于 GitCode API）")

        # 获取指定时间后的提交列表
        commits = self.gitcode_client.get_commits_since(last_check_time)
        if not commits:
            logger.info("没有找到新的提交")
            return [], []

        # 获取这些提交中更新的文件
        updated_files = set()
        deleted_files = set()

        for i, commit in enumerate(commits, 1):
            commit_sha = commit.get('sha', '')
            commit_msg = commit.get('commit', {}).get('message', '')

            logger.debug(f"[{i}/{len(commits)}] 处理提交: {commit_sha[:8]}")
            logger.debug(f"  消息: {commit_msg[:60]}")

            # 获取该提交的父提交
            parents = commit.get('parents', [])
            if not parents:
                logger.warning(f"提交 {commit_sha[:8]} 没有父提交，跳过")
                continue

            # 使用 compare API 获取变更文件
            base_sha = parents[0].get('sha', '')
            if not base_sha:
                logger.warning(f"无法获取父提交 SHA，跳过")
                continue

            files = self.gitcode_client.get_compare_files(base_sha, commit_sha)

            # 过滤：只保留 base_path 下的文件，跳过配置的目录
            for file_info in files:
                if not isinstance(file_info, dict):
                    logger.warning(f"文件信息格式异常: {type(file_info)}")
                    continue

                file_path = file_info.get('filename', '')
                status = file_info.get('status', '')

                if not file_path:
                    continue

                if not file_path.startswith(self.base_path):
                    continue

                if any(f'/{skip_dir}/' in file_path for skip_dir in self.skip_dirs):
                    continue

                if status in ('deleted', 'removed'):
                    deleted_files.add(file_path)
                    logger.info(f"    - 删除: {os.path.basename(file_path)} ({status})")
                else:
                    updated_files.add(file_path)
                    logger.debug(f"    - {os.path.basename(file_path)} ({status})")

        updated_files_list = sorted(list(updated_files))
        deleted_files_list = sorted(list(deleted_files))
        logger.info(f"找到 {len(updated_files_list)} 个更新文件, {len(deleted_files_list)} 个删除文件")
        return updated_files_list, deleted_files_list

    def fetch_file_content(self, file_path: str) -> Optional[Dict]:
        """
        获取单个文件内容
        """
        content = self.gitcode_client.get_file_content(file_path)

        if content is None:
            logger.warning(f"获取文件内容失败: {file_path}")
            return None

        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'content': content,
            'sha': '',
            'last_commit_sha': '',
            'last_commit_date': '',
            'last_commit_message': ''
        }

    def save_file_to_local(self, file_data: Dict) -> Optional[str]:
        """
        保存文件到本地（原始md格式）
        文件名从docs开始的路径+文件名
        """
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            return None

        try:
            file_path = file_data['file_path']
            file_name = file_data['file_name']
            content = file_data['content']

            # 从docs开始生成文件名（包含docs）
            if file_path.startswith('docs'):
                safe_filename = file_path.replace('/', '_')
            else:
                safe_filename = file_name

            local_path = str(os.path.join(self.output_dir, safe_filename))

            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"保存文件: {safe_filename}")
            return local_path
        except Exception as e:
            logger.error(f"保存文件失败 {file_data['file_name']}: {e}")
            return None

    def _get_safe_filename(self, file_path: str) -> str:
        """从文件路径生成安全的文件名"""
        if file_path.startswith('docs'):
            return file_path.replace('/', '_')
        return os.path.basename(file_path)

    def _append_to_file(self, file_path: str, item: str) -> None:
        """追加写入文件"""
        if not file_path:
            return
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(f"{item}\n")
        except Exception as e:
            logger.error(f"写入文件失败: {e}")

    def fetch_and_save_updated_files(self, mapping_file, last_check_time: str) -> List[str]:
        logger.info("开始增量获取 GitCode 文档（使用 GitCode API 方式）")

        updated_files, deleted_files = self.get_updated_files_by_commits(last_check_time)

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                file_mapping = json.load(f)
        except FileNotFoundError:
            logger.error(f"Mapping文件 {mapping_file} 不存在")
            return []
        except json.JSONDecodeError:
            logger.error(f"Mapping文件 {mapping_file} 格式错误")
            return []

        saved_files = []
        failed_files = []
        updated_count = 0
        
        # 处理删除的文件
        for file_path in deleted_files:
            safe_filename = self._get_safe_filename(file_path)
            if safe_filename in file_mapping:
                self._append_to_file(self.delete_files_path, file_mapping[safe_filename])
        
        if not updated_files:
            logger.info("没有更新的文件")
            return []
        
        logger.info(f"开始处理 {len(updated_files)} 个更新文件")
        
        for i, file_path in enumerate(updated_files, 1):
            file_name = os.path.basename(file_path)
            logger.info(f"[{i}/{len(updated_files)}] 处理: {file_name}")
            
            safe_filename = self._get_safe_filename(file_path)
            
            file_data = self.fetch_file_content(file_path)
            if not file_data:
                failed_files.append(file_name)
                logger.warning(f"  ✗ 获取文件内容失败")
                continue
            
            local_filename = self.save_file_to_local(file_data)
            if local_filename:
                saved_files.append(local_filename)
                self._append_to_file(self.update_files_path, safe_filename)
                if safe_filename in file_mapping:
                    self._append_to_file(self.delete_files_path, file_mapping[safe_filename])
                updated_count += 1
                logger.debug(f"  ✓ 保存成功")
            else:
                failed_files.append(file_name)
                logger.warning(f"  ✗ 保存失败")
        
        logger.info(f"GitCode API 方式增量获取完成:")
        logger.info(f"  成功: {len(saved_files)} 个文件")
        logger.info(f"  失败: {len(failed_files)} 个文件")
        logger.info(f"  删除: {len(deleted_files)} 个文件")
        logger.info(f"  更新: {updated_count} 个文件")
        
        if failed_files:
            logger.warning(f"失败的文件: {failed_files[:10]}")
        
        return saved_files
