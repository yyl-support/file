"""
使用 GitPython 包获取文档（全量更新）
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import git
from src.ForumBot.logging_config import main_logger as logger
from src.utils import delete_directory


class GitCodeFullFetcher:
    def __init__(self, config):
        self.config = config
        self.gitcode_config = config.get('gitcode', {})
        
        # Git 配置
        self.owner = self.gitcode_config.get('owner', 'openUBMC')
        self.repo = self.gitcode_config.get('repo', 'docs')
        self.base_path = self.gitcode_config.get('base_path', 'docs/zh/development')
        self.branch = 'main'
        
        # 本地配置
        self.git_repo_url = f"https://gitcode.com/{self.owner}/{self.repo}.git"
        self.local_repo_dir = str(Path('gitcode_docs_repo').resolve())
        self.output_dir = str(config['lightrag_paths']['rag_data_dir'])
        self.update_files_path = config['lightrag_paths']['new_rag_files']
        
        # 跳过的目录（从配置读取，默认为 ['images']）
        self.skip_dirs = set(self.gitcode_config.get('skip_dirs', ['images']))
    
    def clone_or_pull_repo(self) -> bool:
        """
        克隆或拉取仓库（使用 GitPython）
        """
        logger.info(f"准备获取仓库: {self.git_repo_url}")
        
        try:
            if os.path.exists(self.local_repo_dir):
                logger.info(f"本地仓库已存在，执行 git pull")
                repo = git.Repo(self.local_repo_dir)
                origin = repo.remotes.origin
                origin.pull(self.branch)
                logger.info("Git pull 成功")
                return True
            else:
                logger.info(f"本地仓库不存在，执行 git clone")
                git.Repo.clone_from(
                    self.git_repo_url,
                    self.local_repo_dir,
                    branch=self.branch,
                    depth=1
                )
                logger.info("Git clone 成功")
                return True
        except git.exc.GitCommandError as e:
            logger.error(f"Git 命令失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Git 操作异常: {e}")
            return False
    
    def traverse_markdown_files(self, target_dir: str) -> List[Dict]:
        """
        遍历目标目录下的所有 markdown 文件
        """
        logger.info(f"开始遍历目录: {target_dir}")
        all_files = []
        
        target_path = os.path.join(self.local_repo_dir, target_dir)
        
        if not os.path.exists(target_path):
            logger.error(f"目标目录不存在: {target_path}")
            return all_files
        
        for root, dirs, files in os.walk(target_path):
            # 跳过黑名单目录
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            
            for file in files:
                if file.endswith('.md'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.local_repo_dir)
                    
                    all_files.append({
                        'path': rel_path.replace(os.sep, '/'),
                        'name': file,
                        'full_path': full_path
                    })
        
        logger.info(f"找到 {len(all_files)} 个 markdown 文件")
        return all_files
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        读取文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            logger.warning(f"文件编码不是UTF-8 {file_path}")
            return None
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None
    
    def get_file_path(self, file_info: Dict) -> Optional[str]:
        """
        获取保存到rag_data_dir的文件路径
        文件名从docs开始的路径+文件名
        """
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            return None
        
        file_path = file_info['path']

        # 从docs开始生成文件名（包含docs）
        if file_path.startswith('docs'):
            safe_filename = file_path.replace('/', '_')
        else:
            safe_filename = os.path.basename(file_path)
        
        local_path = os.path.join(self.output_dir, safe_filename)
        
        # 复制文件到目标目录
        try:
            content = self.read_file_content(file_info['full_path'])
            if content:
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.debug(f"保存文件: {safe_filename}")
                return local_path
        except Exception as e:
            logger.error(f"保存文件失败 {safe_filename}: {e}")
        
        return None
    
    def fetch_and_save_all_files(self) -> List[str]:
        """
        使用 GitPython 获取并保存所有文件
        """
        logger.info("开始使用 GitCode 全量获取文档")
        
        # 克隆或拉取仓库
        if not self.clone_or_pull_repo():
            logger.error("获取仓库失败")
            return []
        
        # 遍历目标目录
        files = self.traverse_markdown_files(self.base_path)
        if not files:
            logger.warning("未找到任何 markdown 文件")
            return []
        
        # 处理文件
        saved_files = []
        failed_files = []
        
        logger.info(f"开始处理 {len(files)} 个文件")
        
        for i, file_info in enumerate(files, 1):
            file_name = file_info['name']
            full_path = file_info['full_path']
            
            logger.info(f"[{i}/{len(files)}] 处理: {file_name}")
            
            # 验证文件可读
            if not self.read_file_content(full_path):
                failed_files.append(file_name)
                logger.warning(f"  ✗ 读取文件失败")
                continue
            
            # 获取文件路径
            local_path = self.get_file_path(file_info)
            if local_path:
                saved_files.append(local_path)
                logger.debug(f"  ✓ 文件有效")
            else:
                failed_files.append(file_name)
                logger.warning(f"  ✗ 获取路径失败")

        logger.info(f"GitCode 全量获取完成:")
        logger.info(f"  成功: {len(saved_files)} 个文件")
        logger.info(f"  失败: {len(failed_files)} 个文件")

        if failed_files:
            logger.warning(f"失败的文件: {failed_files[:10]}")

        delete_directory(self.local_repo_dir)

        return saved_files
