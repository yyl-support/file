import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import psycopg2


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def build_evaluation_dataset(
    days=30,
    similarity_threshold=0.9,
    min_samples_per_category=50,
    max_samples_per_category=100,
    output_dir='evaluation_datasets',
    config_path='config/config.yaml'
):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils import load_config
    
    try:
        config = load_config(config_path)
        db_config = config['database']
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            sslmode=db_config.get('sslmode', 'prefer')
        )
        
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT topic_id, input, retrieval_context, actual_output, category, created_at
            FROM evaluation_samples
            WHERE created_at > %s
            ORDER BY created_at DESC
        """, (cutoff_date,))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"数据库查询失败: {e}")
        return None
    
    if not rows:
        print("未找到符合条件的评估样本")
        return None
    
    deduplicated = []
    seen_inputs = []
    
    for row in rows:
        topic_id, input_text, retrieval_context, actual_output, category, created_at = row
        is_duplicate = False
        
        for seen_input in seen_inputs:
            if similar(input_text, seen_input) > similarity_threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_inputs.append(input_text)
            
            if isinstance(retrieval_context, dict):
                retrieval_context_list = retrieval_context
            elif isinstance(retrieval_context, str):
                retrieval_context_list = [retrieval_context]
            else:
                retrieval_context_list = retrieval_context if retrieval_context else []
            
            deduplicated.append({
                'input': input_text,
                'retrieval_context': retrieval_context_list,
                'actual_output': actual_output or '',
                'category': category or '其他',
                'topic_id': topic_id
            })
    
    categories = {}
    for sample in deduplicated:
        cat = sample['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(sample)
    
    final_dataset = []
    import random
    
    for cat, samples in categories.items():
        if len(samples) < min_samples_per_category:
            final_dataset.extend(samples)
        else:
            sampled_count = min(len(samples), max_samples_per_category)
            sampled = random.sample(samples, sampled_count)
            final_dataset.extend(sampled)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'evaluation_dataset_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"评估数据集已生成：{output_file}")
    print(f"总样本数：{len(final_dataset)}")
    for cat, samples in categories.items():
        print(f"  - {cat}: {len([s for s in final_dataset if s['category'] == cat])} 条")
    
    return output_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='构建评估数据集')
    parser.add_argument('--days', type=int, default=30, help='查询最近多少天的数据')
    parser.add_argument('--similarity_threshold', type=float, default=0.9, help='去重相似度阈值')
    parser.add_argument('--min_samples', type=int, default=50, help='每类最小样本数')
    parser.add_argument('--max_samples', type=int, default=100, help='每类最大样本数')
    parser.add_argument('--output_dir', type=str, default='evaluation_datasets', help='输出目录')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    build_evaluation_dataset(
        days=args.days,
        similarity_threshold=args.similarity_threshold,
        min_samples_per_category=args.min_samples,
        max_samples_per_category=args.max_samples,
        output_dir=args.output_dir,
        config_path=args.config
    )