#!/usr/bin/env python3
"""
RSS生成器 - 生成标准RSS 2.0 feed
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape
from typing import List, Dict


class RSSGenerator:
    """RSS 2.0 Feed生成器"""
    
    def __init__(self, site_url: str, title: str, description: str):
        """
        初始化RSS生成器
        
        Args:
            site_url: 网站URL
            title: Feed标题
            description: Feed描述
        """
        self.site_url = site_url.rstrip('/')
        self.title = title
        self.description = description
    
    def generate_feed(self, articles: List[Dict], max_items: int = 100) -> str:
        """
        生成RSS XML内容
        
        Args:
            articles: 文献列表
            max_items: 最大条目数
            
        Returns:
            RSS XML字符串
        """
        # 按日期排序，取最新的
        sorted_articles = sorted(
            articles,
            key=lambda x: x.get('pub_date', ''),
            reverse=True
        )[:max_items]
        
        items_xml = '\n'.join(
            self._create_item(article) for article in sorted_articles
        )
        
        now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>{escape(self.title)}</title>
    <link>{escape(self.site_url)}</link>
    <description>{escape(self.description)}</description>
    <language>zh-CN</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="{escape(self.site_url)}/feed.xml" rel="self" type="application/rss+xml"/>
{items_xml}
</channel>
</rss>'''
    
    def _create_item(self, article: Dict) -> str:
        """
        创建单个RSS条目
        
        Args:
            article: 文献数据
            
        Returns:
            RSS item XML字符串
        """
        title = article.get('title_zh') or article.get('title', '无标题')
        link = article.get('link', '')
        description = article.get('abstract_zh') or article.get('abstract', '')
        pub_date = article.get('pub_date', '')
        journal = article.get('journal', '')
        
        # 格式化日期
        if pub_date:
            try:
                dt = datetime.strptime(pub_date, '%Y-%m-%d')
                pub_date_rfc = dt.strftime('%a, %d %b %Y 00:00:00 GMT')
            except:
                pub_date_rfc = ''
        else:
            pub_date_rfc = ''
        
        # 构建描述
        desc_parts = []
        if journal:
            desc_parts.append(f"📚 {journal}")
        if description:
            desc_parts.append(description[:500] + ('...' if len(description) > 500 else ''))
        
        full_description = '\n\n'.join(desc_parts)
        
        return f'''    <item>
        <title>{escape(title)}</title>
        <link>{escape(link)}</link>
        <description><![CDATA[{full_description}]]></description>
        <pubDate>{pub_date_rfc}</pubDate>
        <guid isPermaLink="true">{escape(link)}</guid>
    </item>'''
    
    def save_feed(self, articles: List[Dict], filepath: str, max_items: int = 100) -> bool:
        """
        保存RSS文件
        
        Args:
            articles: 文献列表
            filepath: 输出文件路径
            max_items: 最大条目数
            
        Returns:
            是否成功
        """
        try:
            xml_content = self.generate_feed(articles, max_items)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"✅ RSS feed已保存: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ RSS生成失败: {e}")
            return False


def generate_rss_feed(articles: List[Dict], output_path: str = 'docs/feed.xml'):
    """
    便捷函数：生成RSS feed
    
    Args:
        articles: 文献列表
        output_path: 输出路径
    """
    generator = RSSGenerator(
        site_url='https://your-username.github.io/literature-tracker',
        title='文献追踪系统',
        description='自动追踪机器学习、铁电、磁性等领域最新文献'
    )
    
    return generator.save_feed(articles, output_path)


if __name__ == '__main__':
    # 测试
    import json
    
    try:
        with open('docs/data/index.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        generate_rss_feed(articles)
        
    except FileNotFoundError:
        print("未找到数据文件，请先运行抓取脚本")
