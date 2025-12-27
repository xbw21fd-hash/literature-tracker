"""
Zotero BibTeX 导入脚本
将 data/zotero.bib 中的文献导入到系统数据库中
"""

import re
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import os

# 尝试导入翻译模块
try:
    from translator import translate_text
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    print("⚠️ 翻译模块不可用，将跳过翻译")


class BibTeXParser:
    """BibTeX 文件解析器"""
    
    def __init__(self):
        self.entries = []
    
    def parse_file(self, filepath: str) -> List[Dict]:
        """解析 BibTeX 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[Dict]:
        """解析 BibTeX 内容"""
        entries = []
        
        # 匹配 @article{...} 或 @book{...} 等条目
        pattern = r'@(\w+)\s*\{([^,]+),\s*([\s\S]*?)(?=\n@|\Z)'
        matches = re.findall(pattern, content)
        
        for entry_type, entry_key, entry_body in matches:
            entry = self._parse_entry(entry_type, entry_key, entry_body)
            if entry and self._is_valid_entry(entry):
                entries.append(entry)
        
        return entries
    
    def _parse_entry(self, entry_type: str, entry_key: str, body: str) -> Optional[Dict]:
        """解析单个条目"""
        entry = {
            'type': entry_type.lower(),
            'key': entry_key.strip(),
            'raw_fields': {}
        }
        
        # 解析字段
        # 匹配 field = {value} 或 field = value 或 field = "value"
        field_pattern = r'(\w+)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|(\d+))'
        
        for match in re.finditer(field_pattern, body):
            field_name = match.group(1).lower()
            # 获取值（可能在不同的捕获组中）
            value = match.group(2) or match.group(3) or match.group(4) or ''
            value = self._clean_value(value)
            entry['raw_fields'][field_name] = value
        
        # 提取标准字段
        entry['title'] = entry['raw_fields'].get('title', '')
        entry['authors'] = self._parse_authors(entry['raw_fields'].get('author', ''))
        entry['journal'] = entry['raw_fields'].get('journal', entry['raw_fields'].get('booktitle', ''))
        entry['year'] = entry['raw_fields'].get('year', '')
        entry['month'] = entry['raw_fields'].get('month', '')
        entry['doi'] = entry['raw_fields'].get('doi', '')
        entry['abstract'] = entry['raw_fields'].get('abstract', '')
        entry['volume'] = entry['raw_fields'].get('volume', '')
        entry['number'] = entry['raw_fields'].get('number', '')
        entry['pages'] = entry['raw_fields'].get('pages', '')
        entry['annotation'] = entry['raw_fields'].get('annotation', '')  # TLDR
        
        return entry
    
    def _clean_value(self, value: str) -> str:
        """清理字段值"""
        if not value:
            return ''
        
        # 移除 LaTeX 命令
        value = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', value)
        value = re.sub(r'\{([^}]*)\}', r'\1', value)
        value = re.sub(r'\\(.)', r'\1', value)
        
        # 清理多余空白
        value = ' '.join(value.split())
        
        return value.strip()
    
    def _parse_authors(self, author_str: str) -> List[str]:
        """解析作者列表"""
        if not author_str:
            return []
        
        # 按 'and' 分割
        authors = re.split(r'\s+and\s+', author_str)
        
        cleaned_authors = []
        for author in authors:
            author = self._clean_value(author)
            if author:
                # 处理 "Last, First" 格式
                if ',' in author:
                    parts = author.split(',', 1)
                    author = f"{parts[1].strip()} {parts[0].strip()}"
                cleaned_authors.append(author)
        
        return cleaned_authors
    
    def _is_valid_entry(self, entry: Dict) -> bool:
        """检查条目是否有效"""
        # 必须有标题
        if not entry.get('title'):
            return False
        
        # 必须有期刊或会议名称
        if not entry.get('journal'):
            return False
        
        # 必须有年份
        if not entry.get('year'):
            return False
        
        return True


class ZoteroImporter:
    """Zotero 导入器"""
    
    def __init__(self, data_dir: str = 'data', articles_dir: str = 'articles'):
        self.data_dir = Path(data_dir)
        self.articles_dir = Path(articles_dir)
        self.history_file = self.data_dir / 'history.json'
        self.index_file = self.data_dir / 'index.json'
        self.parser = BibTeXParser()
        
        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)
        self.articles_dir.mkdir(exist_ok=True)
    
    def load_existing_data(self) -> Dict:
        """加载现有数据"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'articles': []}
    
    def load_history(self) -> Dict:
        """加载历史记录"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'articles': {}, 'last_update': None}
    
    def save_history(self, history: Dict):
        """保存历史记录"""
        history['last_update'] = datetime.now().isoformat()
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def generate_id(self, entry: Dict) -> str:
        """生成文献ID"""
        # 使用标题和DOI生成唯一ID
        unique_str = f"{entry.get('title', '')}{entry.get('doi', '')}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def entry_to_article(self, entry: Dict, translate: bool = False) -> Dict:
        """将BibTeX条目转换为文章格式"""
        article_id = self.generate_id(entry)
        
        # 构建发布日期
        year = entry.get('year', '')
        month = entry.get('month', '')
        pub_date = self._format_date(year, month)
        
        # 构建链接
        doi = entry.get('doi', '')
        link = f"https://doi.org/{doi}" if doi else ''
        
        # 获取摘要（优先使用annotation/TLDR，其次使用abstract）
        abstract = entry.get('annotation', '') or entry.get('abstract', '')
        
        article = {
            'id': article_id,
            'title': entry.get('title', ''),
            'title_zh': '',
            'abstract': abstract,
            'abstract_zh': '',
            'authors': entry.get('authors', []),
            'pub_date': pub_date,
            'journal': entry.get('journal', ''),
            'link': link,
            'source_url': 'zotero_import',
            'fetch_time': datetime.now().isoformat(),
            'is_favorite': False,
            'doi': doi,
            'volume': entry.get('volume', ''),
            'number': entry.get('number', ''),
            'pages': entry.get('pages', ''),
        }
        
        # 翻译标题和摘要
        if translate and HAS_TRANSLATOR:
            try:
                if article['title']:
                    article['title_zh'] = translate_text(article['title'])
                if article['abstract']:
                    article['abstract_zh'] = translate_text(article['abstract'])
            except Exception as e:
                print(f"  ⚠️ 翻译失败: {e}")
        
        return article
    
    def _format_date(self, year: str, month: str) -> str:
        """格式化日期"""
        if not year:
            return ''
        
        # 月份映射
        month_map = {
            'jan': '01', 'january': '01',
            'feb': '02', 'february': '02',
            'mar': '03', 'march': '03',
            'apr': '04', 'april': '04',
            'may': '05',
            'jun': '06', 'june': '06',
            'jul': '07', 'july': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12',
        }
        
        month_num = month_map.get(month.lower(), '01') if month else '01'
        
        return f"{year}-{month_num}-01"
    
    def import_bib_file(self, bib_path: str, translate: bool = False, skip_existing: bool = True) -> int:
        """导入BibTeX文件"""
        print(f"📖 解析文件: {bib_path}")
        
        # 解析BibTeX文件
        entries = self.parser.parse_file(bib_path)
        print(f"  找到 {len(entries)} 个有效条目")
        
        # 加载现有数据
        existing_data = self.load_existing_data()
        existing_ids = {a['id'] for a in existing_data.get('articles', [])}
        existing_titles = {a['title'].lower() for a in existing_data.get('articles', [])}
        
        history = self.load_history()
        
        # 导入新文献
        new_articles = []
        skipped = 0
        
        for i, entry in enumerate(entries, 1):
            article = self.entry_to_article(entry, translate=False)  # 先不翻译
            
            # 检查是否已存在
            if skip_existing:
                if article['id'] in existing_ids or article['title'].lower() in existing_titles:
                    skipped += 1
                    continue
            
            print(f"  [{i}/{len(entries)}] {article['title'][:60]}...")
            
            # 翻译（如果需要）
            if translate and HAS_TRANSLATOR:
                try:
                    if article['title']:
                        article['title_zh'] = translate_text(article['title'])
                        print(f"    → {article['title_zh'][:50]}...")
                except Exception as e:
                    print(f"    ⚠️ 翻译失败: {e}")
            
            new_articles.append(article)
            
            # 添加到历史记录
            history['articles'][article['id']] = article
        
        if new_articles:
            # 合并到现有数据
            all_articles = existing_data.get('articles', []) + new_articles
            
            # 按日期排序
            all_articles.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
            
            # 保存索引文件
            index_data = {
                'articles': all_articles,
                'total': len(all_articles),
                'last_update': datetime.now().isoformat(),
            }
            
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            # 保存历史记录
            self.save_history(history)
            
            # 生成Markdown文件
            for article in new_articles:
                self._save_article_markdown(article)
            
            print(f"\n✅ 导入完成!")
            print(f"  - 新增: {len(new_articles)} 篇")
            print(f"  - 跳过: {skipped} 篇 (已存在)")
            print(f"  - 总计: {len(all_articles)} 篇")
        else:
            print(f"\n⚠️ 没有新文献需要导入 (跳过 {skipped} 篇已存在)")
        
        return len(new_articles)
    
    def _save_article_markdown(self, article: Dict):
        """保存文章为Markdown文件"""
        filename = f"{article['pub_date']}_{article['id']}.md"
        filepath = self.articles_dir / filename
        
        authors_str = ', '.join(article.get('authors', [])) or '未知'
        
        content = f"""---
id: {article['id']}
title: "{article['title'].replace('"', "'")}"
title_zh: "{article.get('title_zh', '').replace('"', "'")}"
date: {article['pub_date']}
journal: "{article['journal']}"
authors: "{authors_str}"
link: "{article['link']}"
doi: "{article.get('doi', '')}"
---

# {article['title']}

## 中文标题
{article.get('title_zh', '（未翻译）')}

## 基本信息
- **期刊**: {article['journal']}
- **作者**: {authors_str}
- **发表日期**: {article['pub_date']}
- **DOI**: {article.get('doi', '')}
- **原文链接**: [{article['link']}]({article['link']})

## Abstract
{article.get('abstract', '（无摘要）')}

## 摘要（中文）
{article.get('abstract_zh', '（未翻译）')}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='导入Zotero BibTeX文件')
    parser.add_argument('--bib', default='data/zotero.bib', help='BibTeX文件路径')
    parser.add_argument('--translate', action='store_true', help='是否翻译标题')
    parser.add_argument('--force', action='store_true', help='强制导入（不跳过已存在的）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.bib):
        print(f"❌ 文件不存在: {args.bib}")
        return
    
    importer = ZoteroImporter()
    importer.import_bib_file(
        args.bib,
        translate=args.translate,
        skip_existing=not args.force
    )


if __name__ == '__main__':
    main()
