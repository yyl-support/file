import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
from src.ForumBot.logging_config import main_logger as logger

class ForumDataFetcher:
    def __init__(self, config):
        self.config = config

    def fetch_one_page_data(self, page):
        """
        获取单页论坛数据
        """
        params = {
            'page': page,
            'no_definitions': True,
        }

        verify_ssl = self.config.get('lightrag_forum_data', {}).get('verify_ssl', True)
        response = requests.get(
            f"{self.config['lightrag_forum_data']['base_url']}/latest.json",
            params=params,
            timeout=10,
            verify=verify_ssl
        )
        response.raise_for_status()
        return response.json()

    def extract_posts_data(self, posts_data):
        """
        提取帖子数据
        """
        posts = []
        for post in posts_data:
            user_name = post['username']
            topic_closed = post['topic_accepted_answer']
            is_solution = post['accepted_answer']
            body_cooked = post['cooked']
            soup = BeautifulSoup(body_cooked, 'html.parser')

            text_content = soup.get_text()
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)

            text_content = text_content.strip()

            links = []
            for link in soup.find_all('a', href=True):
                links.append(link['href'])

            if links:
                text = f'content: {text_content}\nlinks: {", ".join(links)}'
            else:
                text = text_content

            post_url = post['post_url']
            posts.append({
                'user_name': user_name,
                'topic_closed': topic_closed,
                'is_solution': is_solution,
                'post_url': post_url,
                'text': text,
            })
        return posts

    def get_one_topic_content(self, topic):
        """
        获取单条话题内容
        """
        topic_id = topic['id']
        topic_title = topic['title']
        topic_url = f"{self.config['lightrag_forum_data']['base_url']}/t/{topic_id}.json"

        safe_title = re.sub(r'[^\w\s-]', '', topic_title).strip()
        safe_title = re.sub(r'[-\s]+', '_', safe_title)  # Replace spaces and hyphens with underscores
        max_title_length = 140  # 限制文件名长度
        if len(safe_title) > max_title_length:
            safe_title = safe_title[:max_title_length].rstrip('_')
        file_name = f'{safe_title}_{topic_id}_topic.json'
        params = {
            'track_visit': True,
            'forceLoad': True,
        }
        verify_ssl = self.config.get('lightrag_forum_data', {}).get('verify_ssl', True)
        try:
            response = requests.get(
                topic_url,
                params=params,
                timeout=10,
                verify=verify_ssl
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取话题内容失败（话题ID {topic_id}）: {e}")
            return None

        post_json_data = response.json()
        question = ''
        best_answer_url = ''
        topic_user_name = ''
        reply_posts = []
        if post_json_data.get('post_stream'):
            post_data = post_json_data['post_stream']['posts']
            posts = self.extract_posts_data(post_data)
            question = f'{topic_title} - {posts[0]["text"]}' if posts else ''
            topic_user_name = posts[0]['user_name']
            for post in posts[1:] if len(posts) > 1 else []:
                if post['user_name'] == self.config['posts']['api_username'] and not post['is_solution']:
                    continue
                # 检查是否为解决方案
                if post['is_solution']:
                    best_answer_url = post['post_url']
                reply_posts.append(post)

        write_data = {
            'topic_id': topic_id,
            'question': question,
            'topic_user_name': topic_user_name,
            'best_answer_url': best_answer_url,
            'reply_posts': reply_posts,
        }

        # Ensure the directory exists
        rag_dir = self.config['lightrag_paths']['rag_data_dir']
        try:
            if not os.path.exists(rag_dir):
                os.makedirs(rag_dir)
        except OSError as e:
            logger.error(f"创建目录失败 {rag_dir}: {e}")
            raise

        with open(f'{rag_dir}/{file_name}', 'w', encoding='utf-8') as f:
            json.dump(write_data, f, ensure_ascii=False, indent=4)

        return write_data

    def extract_one_page_topic_data(self, page):
        """提取单页论坛话题数据"""
        data = self.fetch_one_page_data(page)
        topics = data.get('topic_list', {}).get('topics', [])

        for topic in topics:
            self.get_one_topic_content(topic)
            time.sleep(0.5)

        return topics

    def get_all_forum_topics_name_file(self, all_file_name_output):
        all_filenames = []

        page = 0
        while True:
            try:
                data = self.fetch_one_page_data(page)
                topics = data.get('topic_list', {}).get('topics', [])

                if not topics:
                    logger.info(f"第{page + 1}页无更多主题，停止获取")
                    break

                for topic in topics:
                    topic_id = topic['id']
                    topic_title = topic['title']

                    # 生成文件名，与get_one_topic_content中逻辑一致
                    safe_title = re.sub(r'[^\w\s-]', '', topic_title).strip()
                    safe_title = re.sub(r'[-\s]+', '_', safe_title)
                    max_title_length = 140
                    if len(safe_title) > max_title_length:
                        safe_title = safe_title[:max_title_length].rstrip('_')

                    file_name = f'{safe_title}_{topic_id}_topic.json'
                    all_filenames.append(file_name)

            except requests.exceptions.RequestException as e:
                logger.error(f"获取第{page + 1}页数据失败: {e}")
                return
            except Exception as e:
                logger.error(f"处理第{page + 1}页数据时发生错误: {e}")
                return

            logger.info(f"从第 {page} 页提取了 {len(topics)} 个topic")
            page += 1
            time.sleep(0.5)  # 请求间隔，避免过于频繁

        # 将所有文件名写入文件
        try:
            with open(all_file_name_output, 'w', encoding='utf-8') as f:
                for filename in sorted(all_filenames):
                    f.write(f"{filename}\n")
            logger.info(f"已将 {len(all_filenames)} 个帖子文件名写入 {all_file_name_output}")
        except IOError as e:
            logger.error(f"写入文件失败 {all_file_name_output}: {e}")
            raise