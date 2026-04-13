#!/usr/bin/env python3
"""
使用Kimi API生成日报（含AI摘要翻译）
"""
import os
import sys
import json
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_daily_pages import render_daily_html, ensure_dirs

class KimiProvider:
    """Kimi API Provider - 直接调用Moonshot API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.moonshot.cn/v1"
        self.model = "moonshot-v1-128k"
    
    def call_api(self, prompt: str) -> str:
        """调用Kimi API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 8000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"Kimi API错误 ({response.status_code}): {response.text}")

def generate_daily_with_kimi(date_str: str):
    """使用Kimi AI生成指定日期的完整日报"""
    print(f"\n{'='*50}")
    print(f"📅 生成 {date_str} 的Kimi AI日报")
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
    
    # 获取Kimi API配置
    api_key = os.environ.get('KIMI_API_KEY') or os.environ.get('KIMI_PLUGIN_API_KEY')
    
    if not api_key:
        print("❌ 未设置Kimi API密钥 (KIMI_API_KEY 或 KIMI_PLUGIN_API_KEY)")
        return False
    
    print(f"🤖 使用Kimi API生成摘要...")
    
    provider = KimiProvider(api_key)
    
    # 分批处理（每批10篇）
    batch_size = 10
    batches = [articles[i:i+batch_size] for i in range(0, len(articles), batch_size)]
    
    full_list = []
    
    for batch_idx, batch in enumerate(batches, 1):
        print(f"\n  处理第{batch_idx}/{len(batches)}批 ({len(batch)}篇)...")
        
        # 构建prompt
        articles_text = []
        for i, art in enumerate(batch, 1):
            articles_text.append(f"""
[{i}] 标题: {art.get('title', 'N/A')}
期刊: {art.get('journal', 'N/A')}
作者: {', '.join(art.get('authors', [])) if art.get('authors') else 'N/A'}
摘要: {art.get('abstract', 'N/A')[:500]}
""")
        
        prompt = f"""请为以下学术论文生成中文摘要和一句话总结。

{chr(10).join(articles_text)}

请用JSON格式返回，每篇文章包含：
- title_zh: 中文标题（简洁准确）
- abstract_zh: 摘要中文翻译（200字以内）
- summary: 一句话研究亮点（50字以内）

JSON格式：
{{
  "articles": [
    {{"title_zh": "...", "abstract_zh": "...", "summary": "..."}},
    ...
  ]
}}

只返回JSON，不要其他文字。"""
        
        try:
            response = provider.call_api(prompt)
            
            # 解析JSON
            try:
                result = json.loads(response)
            except:
                # 尝试从markdown代码块提取
                if '```json' in response:
                    response = response.split('```json')[1].split('```')[0]
                elif '```' in response:
                    response = response.split('```')[1].split('```')[0]
                result = json.loads(response.strip())
            
            translated = result.get('articles', [])
            
            # 合并结果
            for i, art in enumerate(batch):
                if i < len(translated):
                    t = translated[i]
                    full_list.append({
                        'title_en': art.get('title'),
                        'title_zh': t.get('title_zh') or art.get('title'),
                        'abstract_zh': t.get('abstract_zh') or art.get('abstract', '')[:200],
                        'summary': t.get('summary') or '点击查看原文了解详情',
                        'link': art.get('link'),
                        'journal': art.get('journal', ''),
                        'authors': art.get('authors', []),
                        'pub_date': art.get('pub_date', ''),
                    })
                else:
                    # 翻译缺失，使用原文
                    full_list.append({
                        'title_en': art.get('title'),
                        'title_zh': art.get('title'),
                        'abstract_zh': art.get('abstract', '')[:200],
                        'summary': '点击查看原文了解详情',
                        'link': art.get('link'),
                        'journal': art.get('journal', ''),
                        'authors': art.get('authors', []),
                        'pub_date': art.get('pub_date', ''),
                    })
            
            print(f"    ✅ 成功翻译{len(translated)}篇")
            
        except Exception as e:
            print(f"    ❌ API调用失败: {e}")
            # 使用原文作为fallback
            for art in batch:
                full_list.append({
                    'title_en': art.get('title'),
                    'title_zh': art.get('title'),
                    'abstract_zh': art.get('abstract', '')[:200],
                    'summary': '点击查看原文了解详情',
                    'link': art.get('link'),
                    'journal': art.get('journal', ''),
                    'authors': art.get('authors', []),
                    'pub_date': art.get('pub_date', ''),
                })
        
        time.sleep(1)  # 避免rate limit
    
    # 构建summary
    summary = {
        'date': date_str,
        'total': len(full_list),
        'overview': f"今日共收录{len(full_list)}篇文献。",
        'trends': '',
        'full_list': full_list,
        'generated_by': 'kimi'
    }
    
    # 保存响应
    os.makedirs('ai_responses', exist_ok=True)
    with open(f'ai_responses/{date_str}_response.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 响应已保存: ai_responses/{date_str}_response.json")
    
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
        print("用法: python3 generate_with_kimi.py YYYY-MM-DD")
        print("示例: python3 generate_with_kimi.py 2026-04-13")
        sys.exit(1)
    
    date = sys.argv[1]
    
    # 检查环境变量
    if not os.environ.get('KIMI_API_KEY') and not os.environ.get('KIMI_PLUGIN_API_KEY'):
        print("❌ 请先设置 KIMI_API_KEY 或 KIMI_PLUGIN_API_KEY 环境变量")
        sys.exit(1)
    
    success = generate_daily_with_kimi(date)
    sys.exit(0 if success else 1)
