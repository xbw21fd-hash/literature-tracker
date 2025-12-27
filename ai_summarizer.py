#!/usr/bin/env python3
"""
AI摘要生成器 - 使用免费AI API生成每日文献摘要
支持: Gemini, SiliconFlow, Groq, DeepSeek
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

try:
    from config import AI_CONFIG as DEFAULT_AI_CONFIG
except ImportError:
    DEFAULT_AI_CONFIG = {}


class AIProvider(ABC):
    """AI提供商基类"""
    
    @abstractmethod
    def call_api(self, prompt: str) -> str:
        pass


class GeminiProvider(AIProvider):
    """Google Gemini API"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        # 支持从环境变量读取模型，默认使用 gemini-3.0-flash
        self.model = model or os.environ.get('GEMINI_MODEL', 'gemini-3-flash-preview')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.max_retries = 3
    
    def call_api(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
                "topP": 0.95,
                "topK": 40,
                "responseMimeType": "application/json"
            },
            # 使用 BLOCK_ONLY_HIGH 更稳定，BLOCK_NONE 在某些区域可能不支持
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        }
        
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=120
                )
                
                if response.status_code == 429:
                    # 速率限制，等待后重试
                    import time
                    wait_time = (attempt + 1) * 10
                    print(f"⏳ API速率限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg = error_data['error'].get('message', error_msg)
                    except:
                        pass
                    raise Exception(f"Gemini API错误 ({response.status_code}): {error_msg}")
                
                result = response.json()
                
                # 检查是否有候选响应
                if 'candidates' not in result or len(result['candidates']) == 0:
                    # 检查是否有 promptFeedback 说明被阻止的原因
                    if 'promptFeedback' in result:
                        block_reason = result['promptFeedback'].get('blockReason', '未知原因')
                        raise Exception(f"请求被阻止: {block_reason}")
                    raise Exception("Gemini API返回空响应")
                
                candidate = result['candidates'][0]
                
                # 检查是否被安全过滤
                finish_reason = candidate.get('finishReason', '')
                if finish_reason == 'SAFETY':
                    safety_ratings = candidate.get('safetyRatings', [])
                    raise Exception(f"响应被安全过滤器阻止: {safety_ratings}")
                
                # 提取文本
                if 'content' not in candidate or 'parts' not in candidate['content']:
                    raise Exception(f"响应格式异常，finishReason: {finish_reason}")
                
                return candidate['content']['parts'][0]['text']
                
            except requests.exceptions.Timeout:
                last_error = "请求超时"
                print(f"⚠️ 请求超时，重试 {attempt + 1}/{self.max_retries}")
                continue
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接错误: {e}"
                print(f"⚠️ 连接错误，重试 {attempt + 1}/{self.max_retries}")
                import time
                time.sleep(5)
                continue
            except Exception as e:
                # 非网络错误，直接抛出
                raise
        
        raise Exception(f"API调用失败，已重试{self.max_retries}次: {last_error}")


class SiliconFlowProvider(AIProvider):
    """SiliconFlow API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    def call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class GroqProvider(AIProvider):
    """Groq API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.1-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class DeepSeekProvider(AIProvider):
    """DeepSeek API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def call_api(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 4096
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]


class AISummarizer:
    """AI摘要生成器"""
    
    PROVIDERS = {
        'gemini': GeminiProvider,
        'siliconflow': SiliconFlowProvider,
        'groq': GroqProvider,
        'deepseek': DeepSeekProvider
    }
    
    def __init__(self, api_provider: str, api_key: str):
        """
        初始化AI摘要生成器
        
        Args:
            api_provider: 'gemini' | 'siliconflow' | 'groq' | 'deepseek'
            api_key: API密钥
        """
        if api_provider not in self.PROVIDERS:
            raise ValueError(f"不支持的API提供商: {api_provider}")
        
        self.provider = self.PROVIDERS[api_provider](api_key)
        self.provider_name = api_provider
    
    def generate_daily_summary(self, articles: List[Dict], date: str) -> Dict:
        """
        生成每日摘要
        
        Args:
            articles: 当日文献列表
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            摘要数据字典
        """
        if not articles:
            return self.fallback_summary(articles, date)
        
        try:
            prompt = self._build_prompt(articles, date)
            response = self.provider.call_api(prompt)
            
            # 解析AI响应
            summary = self._parse_response(response, articles, date)
            return summary
            
        except Exception as e:
            print(f"❌ AI API调用失败: {e}")
            return self.fallback_summary(articles, date)
    
    def _build_prompt(self, articles: List[Dict], date: str) -> str:
        """构建提示词"""
        
        # 准备文献信息
        articles_text = []
        for i, article in enumerate(articles[:30], 1):  # 限制数量避免超长
            title = article.get('title_zh') or article.get('title', '')
            journal = article.get('journal', '未知期刊')
            link = article.get('link', '')
            abstract = (article.get('abstract_zh') or article.get('abstract', ''))[:300]
            
            articles_text.append(f"""
{i}. 标题: {title}
   期刊: {journal}
   链接: {link}
   摘要: {abstract}...
""")
        
        articles_str = '\n'.join(articles_text)
        
        return f"""你是一位专业的科研文献分析助手。请分析以下{date}的{len(articles)}篇新文献，生成一份结构化的每日摘要报告。

文献列表:
{articles_str}

请按以下格式输出（使用JSON格式）:
{{
    "overview": "今日文献总览，包括总数、主要研究方向等（2-3句话）",
    "trends": "研究热点和趋势分析（3-5句话）",
    "highlights": [
        {{
            "title": "文献标题",
            "journal": "期刊名",
            "link": "原文链接",
            "summary": "一句话核心要点（不超过50字）",
            "reason": "推荐理由（不超过30字）"
        }}
    ],
    "by_topic": {{
        "主题1": ["文献序号1", "文献序号2"],
        "主题2": ["文献序号3"]
    }}
}}

要求:
1. highlights中选择5-10篇最值得关注的文献
2. 每篇文献的summary要精炼准确
3. by_topic按研究主题分组
4. 确保所有链接都是原始文献链接
5. 使用中文输出"""
    
    def _parse_response(self, response: str, articles: List[Dict], date: str) -> Dict:
        """解析AI响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("无法解析JSON")
            
            # 补充完整信息
            return {
                'date': date,
                'total': len(articles),
                'ai_related': sum(1 for a in articles if self._is_ai_related(a)),
                'overview': data.get('overview', ''),
                'trends': data.get('trends', ''),
                'highlights': data.get('highlights', []),
                'by_topic': data.get('by_topic', {}),
                'articles': articles,
                'generated_by': self.provider_name
            }
            
        except Exception as e:
            print(f"解析响应失败: {e}")
            return self.fallback_summary(articles, date)
    
    def _is_ai_related(self, article: Dict) -> bool:
        """判断是否AI相关"""
        text = ' '.join([
            article.get('title', ''),
            article.get('abstract', '')
        ]).lower()
        
        ai_keywords = ['machine', 'learn', 'neural', 'network', 'deep learning', 'ai']
        return any(kw in text for kw in ai_keywords)
    
    def fallback_summary(self, articles: List[Dict], date: str) -> Dict:
        """API失败时的降级摘要"""
        ai_count = sum(1 for a in articles if self._is_ai_related(a))
        
        # 按期刊分组
        by_journal = {}
        for article in articles:
            journal = article.get('journal', '其他')
            if journal not in by_journal:
                by_journal[journal] = []
            by_journal[journal].append({
                'title': article.get('title_zh') or article.get('title', ''),
                'link': article.get('link', '')
            })
        
        return {
            'date': date,
            'total': len(articles),
            'ai_related': ai_count,
            'overview': f"今日共收录{len(articles)}篇文献，其中AI相关{ai_count}篇。",
            'trends': '（AI分析暂不可用，显示基础统计）',
            'highlights': [
                {
                    'title': a.get('title_zh') or a.get('title', ''),
                    'journal': a.get('journal', ''),
                    'link': a.get('link', ''),
                    'summary': (a.get('abstract_zh') or a.get('abstract', ''))[:100] + '...',
                    'reason': '新发表文献'
                }
                for a in articles[:10]
            ],
            'by_journal': by_journal,
            'articles': articles,
            'generated_by': 'fallback'
        }
    
    def save_summary_html(self, summary: Dict, output_dir: str = 'docs/daily') -> str:
        """
        保存摘要为HTML文件
        
        Args:
            summary: 摘要数据
            output_dir: 输出目录
            
        Returns:
            输出文件路径
        """
        date = summary['date']
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{date}.html")
        
        # 生成高亮文献HTML
        highlights_html = ''
        for h in summary.get('highlights', []):
            highlights_html += f'''
            <div class="highlight-card">
                <h4><a href="{h.get('link', '#')}" target="_blank">{h.get('title', '')}</a></h4>
                <div class="highlight-meta">📚 {h.get('journal', '')}</div>
                <p class="highlight-summary">{h.get('summary', '')}</p>
                <div class="highlight-reason">💡 {h.get('reason', '')}</div>
            </div>
            '''
        
        # 生成完整HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日摘要 - {date}</title>
    <link rel="stylesheet" href="../style.css">
    <style>
        .summary-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .summary-header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary-stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: var(--bg-card);
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: var(--accent-primary);
        }}
        .stat-label {{
            color: var(--text-muted);
            font-size: 0.9em;
        }}
        .section {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-md);
        }}
        .section h3 {{
            margin-bottom: 15px;
            color: var(--text-primary);
        }}
        .highlight-card {{
            border-left: 4px solid var(--accent-primary);
            padding: 15px;
            margin-bottom: 15px;
            background: var(--bg-primary);
            border-radius: 0 8px 8px 0;
        }}
        .highlight-card h4 {{
            margin: 0 0 8px 0;
        }}
        .highlight-card h4 a {{
            color: var(--text-primary);
            text-decoration: none;
        }}
        .highlight-card h4 a:hover {{
            color: var(--accent-primary);
        }}
        .highlight-meta {{
            font-size: 0.85em;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        .highlight-summary {{
            color: var(--text-secondary);
            margin: 8px 0;
        }}
        .highlight-reason {{
            font-size: 0.85em;
            color: var(--color-ai-tag);
        }}
        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: var(--accent-primary);
            text-decoration: none;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
        .generated-by {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85em;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="summary-container">
        <a href="../index.html" class="back-link">← 返回主页</a>
        
        <div class="summary-header">
            <h1>📰 每日文献摘要</h1>
            <h2>{date}</h2>
        </div>
        
        <div class="summary-stats">
            <div class="stat-box">
                <div class="stat-value">{summary.get('total', 0)}</div>
                <div class="stat-label">总文献数</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{summary.get('ai_related', 0)}</div>
                <div class="stat-label">AI相关</div>
            </div>
        </div>
        
        <div class="section">
            <h3>📊 今日总览</h3>
            <p>{summary.get('overview', '')}</p>
        </div>
        
        <div class="section">
            <h3>🔥 研究趋势</h3>
            <p>{summary.get('trends', '')}</p>
        </div>
        
        <div class="section">
            <h3>⭐ 重点推荐</h3>
            {highlights_html}
        </div>
        
        <div class="generated-by">
            由 {summary.get('generated_by', 'AI')} 生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    
    <script>
        // 主题支持
        const theme = localStorage.getItem('literature_theme') || 'light';
        document.documentElement.setAttribute('data-theme', theme);
    </script>
</body>
</html>'''
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ 每日摘要已保存: {filepath}")
        return filepath


def generate_daily_summary(articles: List[Dict], date: str = None, 
                          api_provider: str = None, api_key: str = None) -> Optional[str]:
    """
    便捷函数：生成每日摘要
    
    Args:
        articles: 文献列表
        date: 日期，默认今天
        api_provider: API提供商
        api_key: API密钥
        
    Returns:
        输出文件路径
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # 筛选当日文献
    today_articles = [
        a for a in articles 
        if a.get('pub_date', '').startswith(date)
    ]
    
    if not today_articles:
        print(f"📭 {date} 没有新文献")
        return None
    
    # 获取API配置
    if not api_provider:
        api_provider = (
            os.environ.get('AI_PROVIDER')
            or DEFAULT_AI_CONFIG.get('provider')
            or 'gemini'
        )
    if not api_key:
        api_key = os.environ.get('AI_API_KEY', '') or DEFAULT_AI_CONFIG.get('api_key', '')
    
    if not api_key:
        print("⚠️ 未配置AI API密钥，使用降级摘要")
        summarizer = AISummarizer.__new__(AISummarizer)
        summarizer.provider_name = 'fallback'
        summary = summarizer.fallback_summary(today_articles, date)
    else:
        summarizer = AISummarizer(api_provider, api_key)
        summary = summarizer.generate_daily_summary(today_articles, date)
    
    return summarizer.save_summary_html(summary)


if __name__ == '__main__':
    import sys
    
    # 测试
    try:
        with open('docs/data/index.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        
        # 使用命令行参数或环境变量
        date = sys.argv[1] if len(sys.argv) > 1 else None
        generate_daily_summary(articles, date)
        
    except FileNotFoundError:
        print("未找到数据文件，请先运行抓取脚本")
