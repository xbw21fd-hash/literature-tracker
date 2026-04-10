#!/usr/bin/env python3
"""
用已筛选的数据生成日报HTML（跳过AI摘要）
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_daily_pages import render_daily_html, ensure_dirs

def generate_daily_html_only(date_str: str):
    """直接用数据文件生成HTML"""
    print(f"\n📅 生成 {date_str} 的日报HTML...")
    
    # 加载数据
    data_file = f'ai_prompts/{date_str}_data.json'
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在: {data_file}")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    if not articles:
        print(f"⚠️ {date_str} 无文章")
        return False
    
    print(f"  文章数: {len(articles)}")
    
    # 构建summary（不使用AI）
    summary = {
        'date': date_str,
        'total': len(articles),
        'overview': f"今日共收录{len(articles)}篇文献。",
        'trends': '',
        'full_list': [],
        'ml_highlights': [],
        'ferro_highlights': [],
        'generated_by': 'local'
    }
    
    for i, art in enumerate(articles, 1):
        item = {
            "title_en": art.get('title'),
            "title_zh": art.get('title_zh') or "待翻译",
            "abstract_zh": "",
            "summary": "",
            "link": art.get('link'),
            "journal": art.get("journal", ""),
            "authors": art.get("authors", []),
            "pub_date": art.get("pub_date", ""),
            "ai_score": art.get("ai_score"),
            "source_url": art.get("source_url", ""),
            "arxiv_category": art.get("arxiv_category", ""),
        }
        summary['full_list'].append(item)
    
    # 生成HTML
    ensure_dirs()
    html_content = render_daily_html(date_str, summary)
    
    html_file = f'docs/daily/{date_str}.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"  ✅ HTML已生成: {html_file}")
    
    return True

if __name__ == '__main__':
    dates = ['2026-04-01', '2026-04-02', '2026-04-03', '2026-04-06', '2026-04-08', '2026-04-09']
    
    print("=" * 50)
    print("生成日报HTML")
    print("=" * 50)
    
    for date_str in dates:
        generate_daily_html_only(date_str)
    
    print("\n" + "=" * 50)
    print("完成！")
    print("=" * 50)
