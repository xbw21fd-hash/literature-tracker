#!/usr/bin/env python3
"""
增量索引模块 - 只更新变化的数据
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional

# 北京时间时区
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_time():
    """获取北京时间"""
    return datetime.now(BEIJING_TZ)

def format_beijing_time(dt=None):
    """格式化为北京时间字符串"""
    if dt is None:
        dt = get_beijing_time()
    return dt.strftime('%Y-%m-%d %H:%M:%S') + ' (北京时间)'


class IncrementalIndex:
    """增量索引管理器"""
    
    def __init__(self, index_path: str = 'data/index.json'):
        """
        初始化增量索引
        
        Args:
            index_path: 索引文件路径
        """
        self.index_path = index_path
        self.meta_path = index_path.replace('.json', '_meta.json')
        self._load_meta()
    
    def _load_meta(self):
        """加载元数据"""
        try:
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                self.meta = json.load(f)
        except FileNotFoundError:
            self.meta = {
                'last_update': None,
                'article_ids': [],
                'total_count': 0
            }
    
    def _save_meta(self):
        """保存元数据"""
        os.makedirs(os.path.dirname(self.meta_path), exist_ok=True)
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)
    
    def get_last_update_time(self) -> Optional[datetime]:
        """
        获取上次更新时间
        
        Returns:
            上次更新时间，如果没有则返回None
        """
        if self.meta.get('last_update'):
            return datetime.fromisoformat(self.meta['last_update'])
        return None
    
    def get_existing_ids(self) -> set:
        """
        获取已存在的文献ID集合
        
        Returns:
            文献ID集合
        """
        return set(self.meta.get('article_ids', []))
    
    def filter_new_articles(self, articles: List[Dict]) -> Tuple[List[Dict], int]:
        """
        过滤出新文献
        
        Args:
            articles: 待处理的文献列表
            
        Returns:
            (新文献列表, 跳过的数量)
        """
        existing_ids = self.get_existing_ids()
        
        new_articles = []
        skipped = 0
        
        for article in articles:
            article_id = article.get('id')
            if article_id and article_id in existing_ids:
                skipped += 1
            else:
                new_articles.append(article)
        
        return new_articles, skipped
    
    def load_existing_articles(self) -> List[Dict]:
        """
        加载现有文献
        
        Returns:
            现有文献列表
        """
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('articles', [])
        except FileNotFoundError:
            return []
    
    def merge_articles(self, existing: List[Dict], new: List[Dict]) -> List[Dict]:
        """
        合并新旧文献
        
        Args:
            existing: 现有文献列表
            new: 新文献列表
            
        Returns:
            合并后的文献列表
        """
        # 使用字典去重
        articles_dict = {a['id']: a for a in existing if a.get('id')}
        
        # 添加新文献
        for article in new:
            if article.get('id'):
                articles_dict[article['id']] = article
        
        # 按日期排序
        merged = list(articles_dict.values())
        merged.sort(key=lambda x: x.get('pub_date', ''), reverse=True)
        
        return merged
    
    def update_index(self, new_articles: List[Dict]) -> Dict:
        """
        更新索引
        
        Args:
            new_articles: 新文献列表
            
        Returns:
            统计信息 {'added': int, 'updated': int, 'skipped': int, 'total': int}
        """
        # 加载现有数据
        existing = self.load_existing_articles()
        existing_ids = {a['id'] for a in existing if a.get('id')}
        
        # 统计
        stats = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'total': 0
        }
        
        # 分类新文献
        to_add = []
        for article in new_articles:
            article_id = article.get('id')
            if not article_id:
                continue
            
            if article_id in existing_ids:
                # 已存在，检查是否需要更新
                stats['updated'] += 1
            else:
                to_add.append(article)
                stats['added'] += 1
        
        # 合并
        merged = self.merge_articles(existing, new_articles)
        stats['total'] = len(merged)
        
        # 保存索引
        self._save_index(merged)
        
        # 更新元数据（使用北京时间）
        self.meta['last_update'] = format_beijing_time()
        self.meta['article_ids'] = [a['id'] for a in merged if a.get('id')]
        self.meta['total_count'] = len(merged)
        self._save_meta()
        
        return stats
    
    def _save_index(self, articles: List[Dict]):
        """保存索引文件"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        data = {
            'total': len(articles),
            'last_update': format_beijing_time(),
            'articles': articles
        }
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_articles_since(self, since_date: str) -> List[Dict]:
        """
        获取指定日期之后的文献
        
        Args:
            since_date: 日期字符串 (YYYY-MM-DD)
            
        Returns:
            文献列表
        """
        articles = self.load_existing_articles()
        return [
            a for a in articles 
            if a.get('pub_date', '') >= since_date
        ]


def incremental_update(new_articles: List[Dict], index_path: str = 'data/index.json') -> Dict:
    """
    便捷函数：执行增量更新
    
    Args:
        new_articles: 新文献列表
        index_path: 索引文件路径
        
    Returns:
        统计信息
    """
    index = IncrementalIndex(index_path)
    
    # 过滤已存在的
    filtered, skipped = index.filter_new_articles(new_articles)
    
    if not filtered:
        print(f"📭 没有新文献需要添加（跳过 {skipped} 篇已存在）")
        return {'added': 0, 'updated': 0, 'skipped': skipped, 'total': index.meta.get('total_count', 0)}
    
    # 更新索引
    stats = index.update_index(filtered)
    stats['skipped'] = skipped
    
    print(f"📊 增量更新完成:")
    print(f"   新增: {stats['added']} 篇")
    print(f"   更新: {stats['updated']} 篇")
    print(f"   跳过: {stats['skipped']} 篇")
    print(f"   总计: {stats['total']} 篇")
    
    return stats


if __name__ == '__main__':
    # 测试
    index = IncrementalIndex()
    
    last_update = index.get_last_update_time()
    if last_update:
        print(f"上次更新: {last_update}")
    else:
        print("首次运行")
    
    existing = index.load_existing_articles()
    print(f"现有文献: {len(existing)} 篇")
