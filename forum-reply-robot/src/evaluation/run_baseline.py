import json
import os
import sys
import argparse
import re
from datetime import datetime
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config
from evaluation.templates import (
    ANSWER_RELEVANCY_TEMPLATE,
    FAITHFULNESS_TEMPLATE,
    CONTEXT_PRECISION_TEMPLATE,
)


def extract_score(response_text):
    try:
        match = re.search(r'(\d+\.?\d*)', response_text)
        if match:
            score = float(match.group(1))
            if score > 1.0:
                score = score / 10.0
            return max(0.0, min(1.0, score))
    except Exception:
        pass
    return 0.5


def llm_judge(client, model, prompt):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50,
        )
        return extract_score(response.choices[0].message.content)
    except Exception as e:
        print(f"LLM judge调用失败: {e}")
        return None


def normalize_retrieval_context(retrieval_context):
    if isinstance(retrieval_context, dict):
        return [str(v) for v in retrieval_context.values()]
    elif isinstance(retrieval_context, str):
        return [retrieval_context] if retrieval_context else []
    elif isinstance(retrieval_context, list):
        return [str(item) for item in retrieval_context]
    return []


def run_baseline_evaluation(
    dataset_path,
    config_path='config/config.yaml',
    output_dir='evaluation_reports'
):
    if not os.path.exists(dataset_path):
        print(f"数据集文件不存在：{dataset_path}")
        return None
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    config = load_config(config_path)
    api_config = config['api']
    
    model = api_config['model_name']
    base_url = api_config.get('base_url', 'https://api.openai.com/v1')
    api_key = api_config.get('api_key', '')
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    relevancy_scores = []
    faithfulness_scores = []
    precision_scores = []
    category_scores = {}
    
    for sample in dataset:
        input_text = sample['input']
        actual_output = sample.get('actual_output', '')
        retrieval_context = normalize_retrieval_context(
            sample.get('retrieval_context', [])
        )
        category = sample.get('category', '其他')
        
        retrieval_context_str = "\n".join(retrieval_context) if retrieval_context else "无检索上下文"
        
        relevancy_prompt = ANSWER_RELEVANCY_TEMPLATE.format(
            input=input_text,
            actual_output=actual_output
        )
        relevancy_score = llm_judge(client, model, relevancy_prompt)
        if relevancy_score is not None:
            relevancy_scores.append(relevancy_score)
        
        faithfulness_prompt = FAITHFULNESS_TEMPLATE.format(
            actual_output=actual_output,
            retrieval_context=retrieval_context_str
        )
        faithfulness_score = llm_judge(client, model, faithfulness_prompt)
        if faithfulness_score is not None:
            faithfulness_scores.append(faithfulness_score)
        
        precision_prompt = CONTEXT_PRECISION_TEMPLATE.format(
            retrieval_context=retrieval_context_str,
            input=input_text
        )
        precision_score = llm_judge(client, model, precision_prompt)
        if precision_score is not None:
            precision_scores.append(precision_score)
        
        if category not in category_scores:
            category_scores[category] = {
                'relevancy': [],
                'faithfulness': [],
                'precision': []
            }
        if relevancy_score:
            category_scores[category]['relevancy'].append(relevancy_score)
        if faithfulness_score:
            category_scores[category]['faithfulness'].append(faithfulness_score)
        if precision_score:
            category_scores[category]['precision'].append(precision_score)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(output_dir, f'baseline_{timestamp}.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# LightRAG 基线评测报告\n\n")
        f.write(f"**评测时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**数据集**: {dataset_path}\n\n")
        f.write(f"**样本总数**: {len(dataset)}\n\n")
        f.write(f"**评测模型**: {model}\n\n")
        f.write(f"**评测方法**: 轻量方案（LLM Judge，零额外依赖）\n\n")
        
        f.write("## 答案相关性指标\n\n")
        if relevancy_scores:
            avg_relevancy = sum(relevancy_scores) / len(relevancy_scores)
            min_relevancy = min(relevancy_scores)
            max_relevancy = max(relevancy_scores)
            passed_relevancy = sum(1 for s in relevancy_scores if s >= 0.7)
            
            f.write(f"- 平均得分: {avg_relevancy:.3f}\n")
            f.write(f"- 最低得分: {min_relevancy:.3f}\n")
            f.write(f"- 最高得分: {max_relevancy:.3f}\n")
            f.write(f"- 通过率（≥0.7）: {passed_relevancy}/{len(relevancy_scores)} ({passed_relevancy*100/len(relevancy_scores):.1f}%)\n\n")
        else:
            f.write("无有效评分\n\n")
        
        f.write("## 忠实性指标\n\n")
        if faithfulness_scores:
            avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores)
            min_faithfulness = min(faithfulness_scores)
            max_faithfulness = max(faithfulness_scores)
            passed_faithfulness = sum(1 for s in faithfulness_scores if s >= 0.7)
            
            f.write(f"- 平均得分: {avg_faithfulness:.3f}\n")
            f.write(f"- 最低得分: {min_faithfulness:.3f}\n")
            f.write(f"- 最高得分: {max_faithfulness:.3f}\n")
            f.write(f"- 通过率（≥0.7）: {passed_faithfulness}/{len(faithfulness_scores)} ({passed_faithfulness*100/len(faithfulness_scores):.1f}%)\n\n")
        else:
            f.write("无有效评分\n\n")
        
        f.write("## 上下文精确率指标\n\n")
        if precision_scores:
            avg_precision = sum(precision_scores) / len(precision_scores)
            min_precision = min(precision_scores)
            max_precision = max(precision_scores)
            passed_precision = sum(1 for s in precision_scores if s >= 0.7)
            
            f.write(f"- 平均得分: {avg_precision:.3f}\n")
            f.write(f"- 最低得分: {min_precision:.3f}\n")
            f.write(f"- 最高得分: {max_precision:.3f}\n")
            f.write(f"- 通过率（≥0.7）: {passed_precision}/{len(precision_scores)} ({passed_precision*100/len(precision_scores):.1f}%)\n\n")
        else:
            f.write("无有效评分\n\n")
        
        f.write("## 分类别统计\n\n")
        for category, scores in category_scores.items():
            f.write(f"### {category}\n\n")
            if scores['relevancy']:
                avg = sum(scores['relevancy']) / len(scores['relevancy'])
                f.write(f"- 答案相关性平均得分: {avg:.3f}\n")
            if scores['faithfulness']:
                avg = sum(scores['faithfulness']) / len(scores['faithfulness'])
                f.write(f"- 忠实性平均得分: {avg:.3f}\n")
            if scores['precision']:
                avg = sum(scores['precision']) / len(scores['precision'])
                f.write(f"- 上下文精确率平均得分: {avg:.3f}\n")
            f.write("\n")
        
        f.write("## 典型低分案例（答案相关性 < 0.5）\n\n")
        low_score_cases = []
        for i, (sample, score) in enumerate(zip(dataset[:10], relevancy_scores[:10])):
            if score and score < 0.5:
                low_score_cases.append({
                    'input': sample['input'][:200] if len(sample['input']) > 200 else sample['input'],
                    'score': score,
                    'category': sample.get('category', '其他')
                })
        
        if low_score_cases:
            for case in low_score_cases[:3]:
                f.write(f"**问题**: {case['input']}\n")
                f.write(f"**分类**: {case['category']}\n")
                f.write(f"**得分**: {case['score']:.3f}\n\n")
        else:
            f.write("无低分案例\n\n")
    
    print(f"基线评测报告已生成：{report_file}")
    return report_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='运行LightRAG基线评测（轻量方案）')
    parser.add_argument('dataset_path', type=str, help='评估数据集路径')
    parser.add_argument('--config', type=str, default='config/config.yaml', help='配置文件路径')
    parser.add_argument('--output_dir', type=str, default='evaluation_reports', help='报告输出目录')
    
    args = parser.parse_args()
    
    run_baseline_evaluation(
        dataset_path=args.dataset_path,
        config_path=args.config,
        output_dir=args.output_dir
    )