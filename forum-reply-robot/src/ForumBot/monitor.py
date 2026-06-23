import time
import os
import pytz
import shutil
import subprocess  # nosec
from datetime import datetime
import re
from .forum_client import ForumClient
from .ai_processor import AIProcessor
from .data_processor import DataProcessor, format_search_results_as_json, parse_pre_audit_readiness
from .SchemaValidation.end_to_end_check import is_infrastructure_error_text, run_schema_check
from src.utils import load_config
from .logging_config import main_logger as logger
from .token_tracker import token_tracker
from .evaluation_hooks import get_evaluation_context, classify_question
from .prometheus_metrics import update_prometheus_metrics
import json

# 常量定义
KG_VOTE_THRESHOLD = 5  # 知识图谱链接的票数阈值
KG_HIGH_VOTE_MIN_COUNT = 4  # 达到票阈值链接的保留数量
KG_TOP_COUNT_IF_LOW_VOTE = 3  # 如果达到票阈值链接不足时保留的KG链接数量
MAX_LINKS = 5  # 最大链接数量
MAX_SEARCH_RESULTS = 5  # 最大搜索结果数量


def _get_non_replyable_review_reason(answer):
    if answer is None:
        return "empty"

    text = str(answer)
    if not text.strip():
        return "empty"

    if is_infrastructure_error_text(text):
        return "infrastructure_error"

    stripped = text.lstrip()
    if stripped.startswith(("处理失败:", "未知错误:")):
        return "processing_failure"

    return ""

class ForumMonitor:
    def __init__(self, config_file='config/config.yaml',config=None):
        # 如果提供了已加载的配置，则使用它；否则从文件加载
        if config is not None:
            self.config = config
        else:
            self.config = load_config(config_file)
        self.forum_client = ForumClient(self.config)
        self.ai_processor = AIProcessor(self.config)
        self.data_processor = DataProcessor(self.config)
        # 创建数据库表（只需要在启动时执行一次）
        self.data_processor.create_tables()
        # 获取git完整路径用于subprocess调用
        self.git_path = shutil.which('git')
        if not self.git_path:
            logger.warning("Git executable not found in PATH")
        logger.info("ForumMonitor 初始化完成")

    def start(self):
        """
        开始监控新帖子
        """
        csv_file = self.config['paths']['csv_file']
        check_interval = self.config['monitor']['check_interval']
        logger.info(f"开始监控新帖子，检查间隔: {check_interval}秒")
        while True:
            try:
                logger.info(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在检查新帖子...")
                self._check_new_topics(csv_file)
                # 检查预审帖子
                self._check_pre_audit_topics()
                time.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("\n监控任务已停止")
                break
            except Exception as e:
                logger.error(f"监控过程中发生错误: {e}")
                time.sleep(check_interval)


    def _check_new_topics(self, csv_file):
        """
        检查并处理新帖子
        """
        # 加载已存在的帖子数据
        existing_data = self.data_processor.load_existing_data(csv_file)
        if existing_data is None:
            logger.warning("数据库连接失败，无法加载已存在的帖子数据，跳过当前轮次。")
            return
        logger.info(f"已存在 {len(existing_data)} 个帖子")
        # 获取所有帖子的基本信息
        all_topics = self.forum_client.fetch_all_forum_topics()
        if not all_topics:
            logger.warning("新帖子数据为空。")
            return

        # 只需要检查ID是否存在，无需重复检查标签和时间
        new_topics = []
        for topic in all_topics:
            if int(topic['id']) not in existing_data:
                new_topics.append(topic)

        # # 新增逻辑：检查 forum_topics 表中存在但 processed_forum_topics 表中不存在的帖子
        # processed_ids = self.data_processor.get_processed_topic_ids()
        # unprocessed_topic_ids = self.data_processor.get_unprocessed_topics(processed_ids)

        # # 将未处理的帖子添加到 new_topics 列表中（基于ID匹配）
        # for topic in all_topics:
        #     if int(topic['id']) in unprocessed_topic_ids and topic not in new_topics:
        #         new_topics.append(topic)

        if new_topics:
            logger.info(f"发现 {len(new_topics)} 个新帖子!")

            # 只对新帖子获取详细信息
            new_topics_details = []
            for topic in new_topics:
                topic_id = topic['id']
                logger.info(f"正在获取帖子 {topic_id} 的详细信息...")
                topic_details = self.forum_client.fetch_topic_details(topic_id)
                if topic_details:
                    new_topics_details.append(topic_details)
                else:
                    logger.warning(f"无法获取帖子 {topic_id} 的详细信息")
                    return

            # 提取数据
            extracted_data = self.data_processor.extract_topic_data(new_topics_details)
            # 追加新帖子到CSV文件
            self.data_processor.append_to_csv(extracted_data, csv_file)
            if not self.data_processor.append_to_db(new_topics, 'forum_topics'):
                logger.error("数据库插入失败，跳过当前轮次处理。")
                return
            self._process_new_topics(extracted_data)
        else:
            logger.info("没有发现新帖子")


    def _generate_related_links(self, search_results, retrieval_data):
        """
               生成相关链接部分

               Args:
                   search_results: 搜索结果列表
                   retrieval_docs: 检索结果文档内容

               Returns:
                   str: 格式化的相关链接文本
               """

        # 从配置中获取基础URL
        forum_base_url = self.config.get('links', {}).get('forum_base_url', '')
        docs_base_url = self.config.get('links', {}).get('docs_base_url', '')

        # 存储所有唯一链接
        all_links = []
        # 存储已添加的topic_id，用于去重
        added_topic_ids = set()

        # 处理知识图谱链接
        kg_links = []
        kg_topic_ids = []
        chunk_content = retrieval_data.get('data', '').get('chunks', '')
        if chunk_content:
            try:

                for json_str in chunk_content:
                    try:
                        if 'file_path' in json_str:
                            file_path_entry = json_str['file_path']
                            # 分割多个文件路径
                            match = re.search(r'_(\d+)(?:_topic)?\.json$', file_path_entry.strip())
                            if match:
                                topic_id = int(match.group(1))
                                if topic_id < 10:
                                    continue
                                kg_link = f"{forum_base_url}/t/topic/{topic_id}"
                                if kg_link not in kg_links:
                                    kg_links.append(kg_link)
                                    added_topic_ids.add(topic_id)
                            # 如果已经收集到足够的链接（总共4个），就停止
                            if len(kg_links) >= KG_HIGH_VOTE_MIN_COUNT:
                                break
                    except Exception as e:
                        logger.warning(f"处理知识图谱链接时出错: {e}")
                        continue

            except Exception as e:
                logger.error(f"处理KG实体链接时出错: {e}")

        # 处理搜索结果链接（至少保留1个，最多保留5个）
        search_links = []
        search_topic_ids = []
        if search_results:
            # 最多取前5个搜索结果，但要过滤掉包含"news"的路径
            filtered_search_results = []
            for result in search_results:
                path = result.get('path', '')
                # 过滤掉包含"news"的路径
                if 'news' not in path.lower():
                    filtered_search_results.append(result)
                    # 如果已经收集到足够的链接（总共5个），就停止
                    if len(filtered_search_results) >= MAX_SEARCH_RESULTS:
                        break

            # 最多取前5个搜索结果
            for result in filtered_search_results:
                path = result.get('path', '')
                if path.startswith('/t/topic'):
                    # 提取topic_id
                    topic_match = re.search(r'/t/topic/(\d+)', path)
                    if topic_match:
                        topic_id = int(topic_match.group(1))
                        # 检查是否与知识图谱链接重复
                        if topic_id not in added_topic_ids:
                            full_url = forum_base_url + path
                            search_links.append(full_url)
                            search_topic_ids.append(topic_id)
                            added_topic_ids.add(topic_id)
                            # 如果已经收集到足够的链接（总共5个），就停止
                            if len(kg_links) + len(search_links) >= MAX_SEARCH_RESULTS:
                                break
                    else:
                        full_url = forum_base_url + path
                        search_links.append(full_url)
                        # 如果已经收集到足够的链接（总共5个），就停止
                        if len(kg_links) + len(search_links) >= MAX_SEARCH_RESULTS:
                            break
                elif path.startswith('http'):
                    # http开头的链接不拼接任何base_url
                    if path not in search_links:
                        search_links.append(path)
                    # 如果已经收集到足够的链接（总共5个），就停止
                    if len(kg_links) + len(search_links) >= MAX_SEARCH_RESULTS:
                        break
                else:
                    full_url = docs_base_url + path
                    full_url = full_url.replace(' ', '%20')
                    if full_url not in search_links:
                        search_links.append(full_url)
                    # 如果已经收集到足够的链接（总共5个），就停止
                    if len(kg_links) + len(search_links) >= MAX_SEARCH_RESULTS:
                        break

        # 组合链接，总共确保5个（如果可能的话）
        # 1. 先添加知识图谱链接
        all_links.extend(kg_links)

        # 2. 添加搜索链接，直到达到5个或者没有更多链接
        for link in search_links:
            if len(all_links) >= MAX_SEARCH_RESULTS:
                break
            if link not in all_links:
                all_links.append(link)

        # 3. 如果链接还不够5个，继续从搜索结果中补充（即使会重复知识图谱中的链接）
        if len(all_links) < MAX_LINKS and search_results:
            for result in search_results:
                if len(all_links) >= MAX_LINKS:
                    break
                path = result.get('path', '')
                if 'news' in path.lower():
                    continue
                if path.startswith('/t/topic'):
                    full_url = forum_base_url + path
                elif path.startswith('http'):
                    # http开头的链接不拼接任何base_url
                    full_url = path
                else:
                    full_url = docs_base_url + path
                # 避免完全相同的链接重复
                if full_url not in all_links:
                    all_links.append(full_url)

        # 4. 如果还是不够5个，从知识图谱中补充
        if len(all_links) < MAX_LINKS and kg_links:
            for i, link in enumerate(kg_links):
                if len(all_links) >= MAX_LINKS:
                    break
                # 避免完全相同的链接重复
                if link not in all_links:
                    all_links.append(link)

        # 最多保留5个链接
        all_links = all_links[:MAX_LINKS]

        # 格式化输出
        if all_links:
            formatted_links = []
            for i, link in enumerate(all_links, 1):
                formatted_links.append(f"{i}. {link}")
            return "相关链接：\n" + "\n".join(formatted_links)
        else:
            return ""

    def _process_new_topics(self, new_topics):
        """
        处理新帖子（生成摘要、搜索相关主题、回复等）
        """
        csv_file = self.config['paths']['csv_file']
        processed_csv_file = self.config['paths']['processed_csv_file']  # 获取新CSV文件路径
        answer_csv_file = self.config['paths']['answer_csv_file']
        for i, topic in enumerate(new_topics):
            topic_id = topic['id']
            logger.info(f"正在处理帖子 {topic_id} ({i + 1}/{len(new_topics)})")
            try:
                retrieval_results = []
                # 检查是否为提示词注入攻击
                is_injection = self.ai_processor.check_prompt_injection(topic['title'], topic['user_question'], topic_id)
                if is_injection.lower() == 'yes':
                    logger.info(f"帖子 {topic_id} 被识别为提示词注入攻击，跳过处理")
                    continue
                logger.info(f"正在为帖子 {topic_id} 生成摘要...")
                summary = self.ai_processor.summarize_text(topic['title'], topic['user_question'],topic_id)
                topic['summary_question'] = summary
                logger.info(f"帖子 {topic_id}:摘要: {summary}")

                # 基于摘要搜索相关主题
                logger.info(f"正在为帖子 {topic_id} 搜索相关主题...")
                search_results = self.forum_client.search_related_topics(
                    summary, topic_id
                )
                # 处理搜索结果
                if search_results:
                    logger.info(f"帖子 {topic_id} 搜索到 {len(search_results)} 个相关主题")
                    self.data_processor.process_search_results(topic_id, search_results, summary, max_results=10)
                else:
                    logger.info(f"帖子 {topic_id} 未搜索到相关主题")

                # 检索相关文档
                logger.info(f"正在为帖子 {topic_id} 检索相关文档...")
                try:
                    retrieval_result = self.forum_client.retrieve_documents_for_topic(topic)

                    # 检查retrieval_result是否为空或无效
                    if not retrieval_result or 'related_docs' not in retrieval_result:
                        logger.warning(f"帖子 {topic_id} 的检索结果为空，使用空字符串继续处理")
                        retrieval_result = {'topic_id': topic_id, 'related_docs': ''}
                        if not search_results:
                            logger.info(f"帖子 {topic_id} 既没有搜索结果也没有检索结果，跳过回答")
                            continue

                    retrieval_result['related_docs'], context_data = self.data_processor.format_search_results_for_prompt(
                        retrieval_result, search_results
                    )
                except Exception as e:
                    logger.error(f"帖子 {topic_id} 检索文档时发生异常: {e}，使用空字符串继续处理")
                    retrieval_result = {'topic_id': topic_id, 'related_docs': '','data':''}
                    context_data = format_search_results_as_json(search_results)
                    if not search_results:
                        logger.info(f"帖子 {topic_id} 既没有搜索结果也没有检索结果，跳过回答")
                        continue

                retrieval_results.append(retrieval_result)

                # 调大模型生成回答
                try:
                    answer = self.ai_processor.call_large_model(
                        retrieval_result['related_docs'],
                        topic['title'],
                        topic['user_question'],
                        topic_id
                    )
                    # 检查大模型是否正常返回答案
                    if answer.startswith("处理失败:") or answer.startswith("未知错误:"):
                        logger.info(f"帖子 {topic_id} 的大模型处理失败，跳过回复: {answer}")
                        continue
                except Exception as e:
                    logger.error(f"帖子 {topic_id} 调用大模型时发生异常: {e}，使用默认回答继续处理")
                    answer = "抱歉，暂时无法生成回答。"

                # 检查生成的答案与搜索结果是否相关
                is_relevant = self.ai_processor.check_answer_relevance(answer, context_data, topic_id)
                is_qualified = self.ai_processor.check_answer_quality(answer, topic['title'], topic['user_question'], topic_id)
                if is_relevant.lower() != 'yes':
                    topic['llm_answer'] = answer
                    token_usage = token_tracker.get_usage(topic_id)
                    # 每处理完1个topic就处理检索结果
                    self.data_processor.process_retrieval_results(retrieval_results)

                    single_topic_list = [topic]

                    # 将包含AI回答的数据写入CSV文件
                    self.data_processor.append_to_csv(single_topic_list, processed_csv_file)
                    self.data_processor.append_to_db(single_topic_list, 'processed_forum_topics')

                    # 将token使用量数据写入consume_tokens_topic表
                    self.data_processor.save_token_usage_to_db(topic_id, token_usage)
                    
                    ctx = get_evaluation_context()
                    category = classify_question(topic['title'], topic['user_question'])
                    evaluation_data = {
                        'retrieval_context': getattr(ctx, 'retrieval_context', None),
                        'retrieval_latency': getattr(ctx, 'retrieval_latency', 0.0),
                        'actual_output': getattr(ctx, 'actual_output', ''),
                        'generation_latency': getattr(ctx, 'generation_latency', 0.0),
                    }
                    
                    try:
                        self.data_processor.save_evaluation_sample(
                            topic_id=topic_id,
                            input_text=f"{topic['title']} {topic['user_question']}",
                            retrieval_context=evaluation_data['retrieval_context'],
                            actual_output=evaluation_data['actual_output'],
                            retrieval_latency=evaluation_data['retrieval_latency'],
                            generation_latency=evaluation_data['generation_latency'],
                            prompt_tokens=token_usage['prompt_tokens'],
                            completion_tokens=token_usage['completion_tokens'],
                            category=category
                        )
                    except Exception as e:
                        logger.warning(f"保存评估样本失败: {e}")
                    
                    try:
                        update_prometheus_metrics(evaluation_data)
                    except Exception as e:
                        logger.warning(f"更新Prometheus指标失败: {e}")
                    
                    logger.info(f"帖子 {topic_id} 的答案与搜索结果不相关，跳过回复")
                    continue
                if is_qualified.lower() != 'yes':
                    topic['llm_answer'] = answer
                    token_usage = token_tracker.get_usage(topic_id)
                    # 每处理完1个topic就处理检索结果
                    self.data_processor.process_retrieval_results(retrieval_results)

                    single_topic_list = [topic]

                    # 将包含AI回答的数据写入CSV文件
                    self.data_processor.append_to_csv(single_topic_list, processed_csv_file)
                    self.data_processor.append_to_db(single_topic_list, 'processed_forum_topics')

                    # 将token使用量数据写入consume_tokens_topic表
                    self.data_processor.save_token_usage_to_db(topic_id, token_usage)
                    
                    ctx = get_evaluation_context()
                    category = classify_question(topic['title'], topic['user_question'])
                    evaluation_data = {
                        'retrieval_context': getattr(ctx, 'retrieval_context', None),
                        'retrieval_latency': getattr(ctx, 'retrieval_latency', 0.0),
                        'actual_output': getattr(ctx, 'actual_output', ''),
                        'generation_latency': getattr(ctx, 'generation_latency', 0.0),
                    }
                    
                    try:
                        self.data_processor.save_evaluation_sample(
                            topic_id=topic_id,
                            input_text=f"{topic['title']} {topic['user_question']}",
                            retrieval_context=evaluation_data['retrieval_context'],
                            actual_output=evaluation_data['actual_output'],
                            retrieval_latency=evaluation_data['retrieval_latency'],
                            generation_latency=evaluation_data['generation_latency'],
                            prompt_tokens=token_usage['prompt_tokens'],
                            completion_tokens=token_usage['completion_tokens'],
                            category=category
                        )
                    except Exception as e:
                        logger.warning(f"保存评估样本失败: {e}")
                    
                    try:
                        update_prometheus_metrics(evaluation_data)
                    except Exception as e:
                        logger.warning(f"更新Prometheus指标失败: {e}")
                    
                    logger.info(f"帖子 {topic_id} 的答案不符合要求，跳过回复")
                    continue


                answer_summary = self.ai_processor.summarize_answer(answer, topic_id)
                if not answer_summary or answer_summary == "总结答案失败" or len(answer_summary) < 10:
                    answer_with_notice = "答案内容由AI生成，仅供参考：\n"  + answer + "\n\n"
                else:
                    # 在 reply_to_topic 调用前添加提示语
                    answer_with_notice = "答案内容由AI生成，仅供参考：\n" + answer_summary + "\n\n[details=\"点击此处查看详细分析解答\"]\n" + answer  + "\n[/details]"
                # 将生成的回答保存到topic中，后续写入CSV
                topic['llm_answer'] = answer_with_notice
                # 获取token使用量统计
                token_usage = token_tracker.get_usage(topic_id)
                logger.info(f"帖子 {topic_id} 回复内容已生成(Token使用: 总计{token_usage['total_tokens']})")
                # 为单个topic创建临时列表
                single_topic_list = [topic]

                # answer_data = [{
                #     'id': topic_id,
                #     'title': topic['title'],
                #     'llm_answer': answer_with_notice
                # }]

                reply_result = self.forum_client.reply_to_topic(topic_id, answer_with_notice)
                if reply_result['success']:
                    logger.info(f"帖子 {topic_id} 回复成功")
                else:
                    logger.error(f"帖子 {topic_id} 回复失败: {reply_result.get('error_message', '未知错误')}")

                # 每处理完1个topic就处理检索结果
                self.data_processor.process_retrieval_results(retrieval_results)

                # 将包含AI回答的数据写入CSV文件
                self.data_processor.append_to_csv(single_topic_list, processed_csv_file)
                # self.data_processor.append_to_answer_csv(answer_data, answer_csv_file)
                self.data_processor.append_to_db(single_topic_list, 'processed_forum_topics')

                # 将token使用量数据写入consume_tokens_topic表
                self.data_processor.save_token_usage_to_db(topic_id, token_usage)
                
                ctx = get_evaluation_context()
                category = classify_question(topic['title'], topic['user_question'])
                evaluation_data = {
                    'retrieval_context': getattr(ctx, 'retrieval_context', None),
                    'retrieval_latency': getattr(ctx, 'retrieval_latency', 0.0),
                    'actual_output': getattr(ctx, 'actual_output', ''),
                    'generation_latency': getattr(ctx, 'generation_latency', 0.0),
                }
                
                try:
                    self.data_processor.save_evaluation_sample(
                        topic_id=topic_id,
                        input_text=f"{topic['title']} {topic['user_question']}",
                        retrieval_context=evaluation_data['retrieval_context'],
                        actual_output=evaluation_data['actual_output'],
                        retrieval_latency=evaluation_data['retrieval_latency'],
                        generation_latency=evaluation_data['generation_latency'],
                        prompt_tokens=token_usage['prompt_tokens'],
                        completion_tokens=token_usage['completion_tokens'],
                        category=category
                    )
                except Exception as e:
                    logger.warning(f"保存评估样本失败: {e}")
                
                try:
                    update_prometheus_metrics(evaluation_data)
                except Exception as e:
                    logger.warning(f"更新Prometheus指标失败: {e}")
                #
                # # 同步到Git仓库
                # self._sync_csv_to_git_repo(answer_csv_file, topic_id)
                logger.info(f"已完成处理帖子 {topic_id} 并同步到Git仓库")
            except Exception as e:
                logger.error(f"处理帖子 {topic_id} 时发生错误: {e}")
                # 即使某个帖子处理失败，也继续处理下一个帖子
                continue

    def _sync_csv_to_git_repo(self, csv_file, topic_id=None):
        """
        将CSV文件同步到Git仓库并提交
        """
        try:
            # 从配置中获取Git相关参数
            git_repo_dir = self.config['git']['repo_dir']
            data_dir = self.config['git']['data_dir']
            branch = self.config['git']['branch']

            # 目标路径
            target_dir = os.path.join(git_repo_dir, data_dir)
            target_file = os.path.join(target_dir, os.path.basename(csv_file))

            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)

            # 复制文件并确保使用UTF-8 with BOM编码
            self._copy_csv_with_bom(csv_file, target_file)
            logger.info(f"CSV文件已复制到: {target_file}")

            # 检查Git仓库目录是否存在
            if not os.path.exists(git_repo_dir):
                logger.error(f"Git仓库目录不存在: {git_repo_dir}")
                return

            # 验证git路径和仓库目录
            if not isinstance(self.git_path, str) or not os.path.isabs(git_repo_dir):
                logger.error("Invalid git path or repository directory")
                return

            # 先执行git fetch获取远程更新
            if not self.git_path:
                logger.error("Git executable not found, cannot fetch")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "fetch"],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Git fetch 失败: {result.stderr}")
                return

            # 尝试切换到远程分支最新状态，避免冲突
            if not self.git_path:
                logger.error("Git executable not found, cannot reset")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "reset", "--hard", "origin/main"],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.warning(f"Git reset 失败: {result.stderr}")

            # 重新复制CSV文件（因为reset操作可能覆盖了它）
            self._copy_csv_with_bom(csv_file, target_file)

            # 添加特定的CSV文件到Git暂存区
            csv_relative_path = os.path.relpath(target_file, git_repo_dir).replace('\\', '/')
            # 验证文件路径，防止路径遍历攻击
            if '..' in csv_relative_path or not csv_relative_path.endswith('.csv'):
                logger.error(f"Invalid file path: {csv_relative_path}")
                return
            if not self.git_path:
                logger.error("Git executable not found, cannot add file")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "add", csv_relative_path],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Git add 失败: {result.stderr}")
                return

            # 检查是否有需要提交的更改
            if not self.git_path:
                logger.error("Git executable not found, cannot diff")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "diff", "--cached", "--exit-code"],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            # 如果diff返回1，说明有更改需要提交；如果返回0，说明没有更改
            if result.returncode == 0:
                logger.info("CSV文件没有变更，无需提交")
                return

            # 提交更改
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            commit_message = f"TopicID_{topic_id}_更新论坛问题回答_{timestamp}"

            # 验证commit message，防止命令注入
            if not isinstance(commit_message, str) or len(commit_message) > 1000:
                logger.error("Invalid commit message")
                return

            if not self.git_path:
                logger.error("Git executable not found, cannot commit")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "commit", "-m", commit_message],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Git commit 失败: {result.stderr}")
                return

            # 推送到远程仓库
            if not self.git_path:
                logger.error("Git executable not found, cannot push")
                return
            if not re.match(r'^[a-zA-Z0-9_-]+$', branch):
                logger.error(f"Invalid branch name: {branch}")
                return
            result = subprocess.run(  # nosec
                [self.git_path, "push", "origin", branch],
                cwd=git_repo_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Git push 失败: {result.stderr}")
                return

            logger.info("CSV文件已成功同步到Git仓库并推送")

        except Exception as e:
            logger.error(f"同步CSV文件到Git仓库时出错: {e}")

    def _copy_csv_with_bom(self, source_file, target_file):
        """
        复制CSV文件并确保使用UTF-8 with BOM编码
        """
        try:
            with open(source_file, 'r', encoding='utf-8') as src:
                content = src.read()

            # 写入目标文件，使用UTF-8 with BOM编码
            with open(target_file, 'w', encoding='utf-8-sig') as dst:
                dst.write(content)
        except Exception as e:
            logger.error(f"复制CSV文件时出错: {e}")
            # 如果出错，直接复制文件
            shutil.copy2(source_file, target_file)

    def _check_pre_audit_topics(self):
        """
        检查并处理预审帖子
        """
        # 检查是否配置了预审标签或预审类别路径
        pre_audit_tag = self.config.get('monitor', {}).get('pre_audit_tag', [])
        pre_audit_category_path = self.config.get('monitor', {}).get('pre_audit_category_path', [])

        if not pre_audit_tag and not pre_audit_category_path:
            return

        logger.info("[预审] 开始检查预审帖子...")

        # 加载 pre_audit_topics 表中已有的帖子ID（去重）
        existing_data = self.data_processor.load_pre_audit_existing_data()
        if existing_data is None:
            logger.warning("[预审] 数据库连接失败，跳过预审检查。")
            return

        # 使用 pre_audit_tag、pre_audit_cutoff_date 和 pre_audit_category_path 获取帖子列表
        all_topics = self.forum_client.fetch_all_forum_topics(
            tag_key='pre_audit_tag',
            cutoff_date_key='pre_audit_cutoff_date',
            category_path_key='pre_audit_category_path'
        )
        if not all_topics:
            logger.info("[预审] 没有获取到预审帖子。")
            return

        # 从配置读取标题过滤关键字
        filter_keywords = self.config.get('monitor', {}).get('pre_audit_title_filter_keywords', [])

        # 过滤出新的预审帖子（不在 pre_audit_topics 表中的）
        new_topics = []
        for topic in all_topics:
            # 标题过滤：跳过包含指定关键字的帖子
            title = topic.get('title', '')
            if filter_keywords and any(kw in title for kw in filter_keywords):
                continue
            if int(topic['id']) not in existing_data:
                new_topics.append(topic)

        if not new_topics:
            logger.info("[预审] 没有发现新的预审帖子。")
            return

        logger.info(f"[预审] 发现 {len(new_topics)} 个新的预审帖子")

        # 获取每个帖子的详细信息并处理
        for topic in new_topics:
            topic_id = topic['id']
            try:
                topic_details = self.forum_client.fetch_topic_details(topic_id)
                if not topic_details:
                    logger.warning(f"[预审] 无法获取帖子 {topic_id} 的详细信息，跳过")
                    continue

                # 提取帖子HTML内容，判断是否准备好AI预审
                html_content = ''
                posts = topic_details.get('post_stream', {}).get('posts', [])
                if posts:
                    html_content = posts[0].get('cooked', '')

                is_ready = parse_pre_audit_readiness(html_content, self.config)

                if is_ready is None:
                    continue
                if not is_ready:
                    logger.info(f'[预审] 帖子 {topic_id} 尚未准备好AI预审（值为"否"），跳过，下轮重试')
                    continue

                # 帖子标记为"是"，进行处理
                logger.info(f"[预审] 帖子 {topic_id} 已准备好AI预审，开始处理")

                # 先写入 pre_audit_topics 表（发现阶段去重）
                extracted_data = self.data_processor.extract_topic_data([topic_details])
                if not extracted_data:
                    logger.warning(f"[预审] 帖子 {topic_id} 数据提取失败，跳过")
                    continue

                self.data_processor.append_to_db([topic], 'pre_audit_topics')

                # 处理该预审帖子
                self._process_pre_audit_topic(extracted_data[0])

            except Exception as e:
                logger.error(f"[预审] 处理帖子 {topic_id} 时发生错误: {e}")
                continue

        logger.info("[预审] 预审帖子检查完成")

    def _process_pre_audit_topic(self, topic):
        """
        处理单个预审帖子（不执行搜索/检索，直接调用预审模型回答）
        """
        topic_id = topic['id']
        processed_csv_file = self.config['paths']['processed_csv_file']

        try:
            # 检查是否为提示词注入攻击
            is_injection = self.ai_processor.check_prompt_injection(
                topic['title'], topic['user_question'], topic_id
            )
            if is_injection.lower() == 'yes':
                logger.info(f"[预审] 帖子 {topic_id} 被识别为提示词注入攻击，跳过处理")
                # 即使跳过也记录到 processed 表，避免重复检测
                self.data_processor.append_to_db([topic], 'pre_audit_processed_topics')
                return

            # 直接调用 Schema 验证流程
            answer = run_schema_check(
                title=topic['title'],
                user_question=topic['user_question'],
                topic_id=str(topic_id),
                config=self.config
            )

            # 无效或基础设施异常结果不生成回复，避免把服务错误当成评审意见发出去
            non_replyable_reason = _get_non_replyable_review_reason(answer)
            if non_replyable_reason == "processing_failure":
                logger.error(f"[预审] 帖子 {topic_id} 预审模型处理失败: {answer}")
                return
            if non_replyable_reason == "infrastructure_error":
                logger.error(f"[预审] 帖子 {topic_id} 预审服务调用失败，跳过回复: {answer}")
                self.data_processor.append_to_db([topic], 'pre_audit_processed_topics')
                return
            if non_replyable_reason == "empty":
                logger.info(f"[预审] 帖子 {topic_id} 无相关评审点，跳过回复")
                self.data_processor.append_to_db([topic], 'pre_audit_processed_topics')
                return

            # 预审结果为结构化验证报告，跳过问答质量检查，直接生成回复

            # 生成回复内容
            answer_with_notice = "预审答案内容由AI生成，仅供参考：\n" + answer + "\n\n"

            topic['llm_answer'] = answer_with_notice
            token_usage = token_tracker.get_usage(topic_id)
            logger.info(f"[预审] 帖子 {topic_id} 回复内容已生成(Token使用: 总计{token_usage['total_tokens']})")

            # 回复帖子
            reply_result = self.forum_client.reply_to_topic(topic_id, answer_with_notice)
            if reply_result['success']:
                logger.info(f"[预审] 帖子 {topic_id} 回复成功")
            else:
                logger.error(f"[预审] 帖子 {topic_id} 回复失败: {reply_result.get('error_message', '未知错误')}")

            # 记录到 processed 表和 CSV
            single_topic_list = [topic]
            self.data_processor.append_to_csv(single_topic_list, processed_csv_file)
            self.data_processor.append_to_db(single_topic_list, 'pre_audit_processed_topics')
            self.data_processor.save_token_usage_to_db(topic_id, token_usage)

            logger.info(f"[预审] 已完成处理帖子 {topic_id}")

        except Exception as e:
            logger.error(f"[预审] 处理帖子 {topic_id} 时发生错误: {e}")
