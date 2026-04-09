#!/usr/bin/env python3
"""
本地Kimi AI摘要生成器
用于OpenClaw AI助手直接生成文献日报摘要
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from generate_daily_pages import (
    load_index_articles, load_relevant, load_summary_index,
    collect_daily_articles, ensure_dirs
)
from focus_filter import filter_focus_items, filter_daily_focus_items, focus_priority

# 路径配置
AI_PROMPTS_DIR = os.path.join(BASE_DIR, "ai_prompts")
DATA_DIR = os.path.join(BASE_DIR, "data")

def prepare_daily_data(date_str: str):
    """准备指定日期的文献数据"""
    
    # 加载数据
    index_path = os.path.join(DATA_DIR, "index.json")
    relevant_path = os.path.join(DATA_DIR, "ai_relevant.json")
    
    index_articles = load_index_articles(index_path)
    relevant_articles = load_relevant(relevant_path)
    
    # 收集当日文献
    collected = collect_daily_articles(index_articles, relevant_articles, date_str)
    
    return {
        "date": date_str,
        "raw_count": len(collected["raw_day_articles"]),
        "focused_count": len(collected["focused_articles"]),
        "daily_count": len(collected["daily_articles"]),
        "articles": collected["daily_articles"],
        "dropped": collected["dropped_articles"]
    }

def format_article_for_prompt(article: dict, index: int) -> str:
    """将文章格式化为prompt中的条目"""
    title = article.get('title_en') or article.get('title') or article.get('title_zh', '')
    title_zh = article.get('title_zh', '')
    journal = article.get('journal', '')
    authors = article.get('authors', [])
    author_str = ', '.join(authors[:3]) + (' et al.' if len(authors) > 3 else '') if authors else '未知'
    link = article.get('link', '')
    ai_score = article.get('ai_score', '')
    
    return f"""
[{index}] {title}
    中文标题: {title_zh}
    期刊: {journal}
    作者: {author_str}
    AI相关度: {ai_score}
    链接: {link}
"""

def build_ai_prompt(data: dict) -> str:
    """构建给AI的prompt"""
    date_str = data["date"]
    articles = data["articles"]
    
    # 限制40篇避免太长
    articles_text = "\n".join([
        format_article_for_prompt(a, i+1) for i, a in enumerate(articles[:40])
    ])
    
    prompt = f"""你是AI×Science文献分析专家。请为{date_str}的文献生成日报摘要。

【今日收录文献】（共{len(articles)}篇）
{articles_text}

请生成以下JSON格式的摘要：
{{
  "overview": "用3-4句话概括今日文献的整体特点，包括主要研究方向、热点主题、方法学进展等",
  "trends": "列出3-4个今日研究热点趋势，每点一句话",
  "full_list": [
    {{
      "title_en": "英文标题",
      "title_zh": "中文标题", 
      "summary": "一句话总结该论文的核心贡献",
      "journal": "期刊名称",
      "link": "原文链接",
      "authors": ["作者1", "作者2"],
      "ai_score": "AI相关度评分"
    }}
  ],
  "ml_highlights": [
    {{
      "title_en": "英文标题",
      "title_zh": "中文标题",
      "summary": "一句话总结",
      "reason": "为什么这篇值得关注（AI方法创新/重要应用/跨学科价值）",
      "journal": "期刊",
      "link": "链接",
      "authors": ["作者"],
      "ai_score": "AI相关度"
    }}
  ]
}}

注意事项：
1. overview要体现今日文献的整体特征和趋势
2. trends要提炼3-4个具体的研究热点方向
3. full_list包含所有文献，每篇用一句话概括
4. ml_highlights挑选最有价值的6篇左右，提供关注理由
5. 必须返回合法的JSON格式
"""
    return prompt

def save_prompt_for_ai(date_str: str, prompt: str):
    """保存prompt到文件，供AI读取"""
    os.makedirs(AI_PROMPTS_DIR, exist_ok=True)
    
    prompt_file = os.path.join(AI_PROMPTS_DIR, f"{date_str}_prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt)
    
    print(f"📝 Prompt已保存: {prompt_file}")
    return prompt_file

def main():
    """主函数 - 准备数据并生成prompt"""
    
    # 获取日期参数，默认为昨天
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
    
    print(f"📅 准备生成 {date_str} 的日报...")
    
    # 准备数据
    try:
        ensure_dirs()
        data = prepare_daily_data(date_str)
    except Exception as e:
        print(f"❌ 准备数据失败: {e}")
        sys.exit(1)
    
    print(f"📊 数据统计:")
    print(f"   - 原始文献: {data['raw_count']} 篇")
    print(f"   - 聚焦文献: {data['focused_count']} 篇") 
    print(f"   - 日报收录: {data['daily_count']} 篇")
    
    if data['daily_count'] == 0:
        print(f"⚠️ {date_str} 无文献，跳过")
        return
    
    # 构建prompt
    prompt = build_ai_prompt(data)
    prompt_file = save_prompt_for_ai(date_str, prompt)
    
    # 同时保存文章数据供后续使用
    data_file = os.path.join(AI_PROMPTS_DIR, f"{date_str}_data.json")
    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存数据文件失败: {e}")
        data_file = "N/A"
    
    print(f"\n✅ 数据准备完成!")
    print(f"📁 Prompt文件: {prompt_file}")
    if data_file != "N/A":
        print(f"📁 数据文件: {data_file}")
    print(f"\n💡 下一步：请AI助手读取prompt文件并生成JSON响应")
    print(f"   然后保存到: {os.path.join(BASE_DIR, 'ai_responses', f'{date_str}_response.json')}")

if __name__ == "__main__":
    main()
