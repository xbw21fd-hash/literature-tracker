#!/usr/bin/env python3
"""
使用OpenClaw AI助手直接生成日报摘要
通过文件接口实现人机协作
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_daily_pages import render_daily_html, ensure_dirs

def prepare_daily_for_ai(date_str: str):
    """
    准备日报数据并输出到文件，等待AI助手处理
    这是第一阶段：系统准备请求
    """
    print(f"\n{'='*50}")
    print(f"📅 准备 {date_str} 的AI日报")
    print(f"{'='*50}")
    
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
    
    print(f"📊 文章数: {len(articles)}")
    
    # 创建输出目录
    output_dir = f"/tmp/literature_ai_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成处理请求文件
    request_file = f"{output_dir}/{date_str}_request.json"
    
    request_data = {
        "date": date_str,
        "articles_count": len(articles),
        "articles": articles,
        "instruction": f"请为{date_str}的文献生成中文摘要",
        "output_file": f"{output_dir}/{date_str}_response.json"
    }
    
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(request_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 请求文件已生成: {request_file}")
    print(f"⏳ 请AI助手读取该文件并生成摘要...")
    print(f"💡 生成后请保存到: {request_data['output_file']}")
    
    return request_file

def check_ai_response(date_str: str, max_wait: int = 60):
    """
    检查AI响应是否已生成
    这是第二阶段：等待AI完成
    """
    output_file = f"/tmp/literature_ai_output/{date_str}_response.json"
    
    print(f"\n⏳ 等待AI响应...")
    for i in range(max_wait):
        if os.path.exists(output_file):
            print(f"✅ AI响应已生成!")
            return output_file
        time.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"  已等待{i+1}秒...")
    
    print(f"⚠️ 等待超时，使用本地数据生成")
    return None

def generate_daily_with_local_ai(date_str: str):
    """
    使用本地数据生成日报（无需外部API）
    """
    print(f"\n{'='*50}")
    print(f"📅 生成 {date_str} 的日报（本地模式）")
    print(f"{'='*50}")
    
    # 加载数据
    data_file = f'ai_prompts/{date_str}_data.json'
    if not os.path.exists(data_file):
        print(f"❌ 数据文件不存在")
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    if not articles:
        print(f"⚠️ 无文章")
        return False
    
    print(f"📊 文章数: {len(articles)}")
    
    # 检查是否有AI生成的响应
    ai_response_file = f"ai_responses/{date_str}_response.json"
    if os.path.exists(ai_response_file):
        with open(ai_response_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        print(f"✅ 使用已有AI响应")
    else:
        # 构建本地summary（使用原文）
        full_list = []
        for art in articles:
            item = {
                'title_en': art.get('title'),
                'title_zh': art.get('title_zh') or art.get('title') or '待翻译',
                'abstract_zh': art.get('abstract_zh') or art.get('abstract', '')[:300],
                'summary': art.get('one_sentence_summary') or '点击查看原文了解详情',
                'link': art.get('link'),
                'journal': art.get('journal', ''),
                'authors': art.get('authors', []),
                'pub_date': art.get('pub_date', ''),
            }
            full_list.append(item)
        
        summary = {
            'date': date_str,
            'total': len(full_list),
            'overview': f"今日共收录{len(full_list)}篇文献。",
            'trends': '',
            'full_list': full_list,
            'generated_by': 'local'
        }
        print(f"⚠️ 使用本地数据（无AI翻译）")
    
    # 生成HTML
    ensure_dirs()
    html = render_daily_html(date_str, summary)
    with open(f'docs/daily/{date_str}.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ HTML已生成: docs/daily/{date_str}.html")
    
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python3 generate_with_local_ai.py YYYY-MM-DD")
        print("示例: python3 generate_with_local_ai.py 2026-04-13")
        sys.exit(1)
    
    date = sys.argv[1]
    success = generate_daily_with_local_ai(date)
    sys.exit(0 if success else 1)
