#!/usr/bin/env python3
"""
修复期刊名称脚本
- 移除 "Recent Articles in " 前缀
- 将包含 "Phys. Rev." 的期刊统一为 "APS"
"""

import json
import os

def fix_journal_name(journal):
    """修复单个期刊名称"""
    if not journal:
        return journal
    
    # 移除 "Recent Articles in " 前缀
    if journal.startswith("Recent Articles in "):
        journal = journal.replace("Recent Articles in ", "")
    
    return journal

def fix_index_json():
    """修复 docs/data/index.json"""
    filepath = "docs/data/index.json"
    
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    print(f"正在修复 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    fixed_count = 0
    
    for article in articles:
        old_journal = article.get('journal', '')
        new_journal = fix_journal_name(old_journal)
        
        if old_journal != new_journal:
            article['journal'] = new_journal
            fixed_count += 1
            print(f"  修复: '{old_journal}' -> '{new_journal}'")
    
    # 保存修复后的数据
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成！共修复 {fixed_count} 篇文献的期刊名称")

def fix_history_json():
    """修复 data/history.json"""
    filepath = "data/history.json"
    
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    print(f"\n正在修复 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查数据格式
    if isinstance(data, dict):
        articles = data.get('articles', [])
    elif isinstance(data, list):
        articles = data
    else:
        print("数据格式不支持")
        return
    
    fixed_count = 0
    
    for article in articles:
        if isinstance(article, dict):
            old_journal = article.get('journal', '')
            new_journal = fix_journal_name(old_journal)
            
            if old_journal != new_journal:
                article['journal'] = new_journal
                fixed_count += 1
    
    # 保存修复后的数据
    with open(filepath, 'w', encoding='utf-8') as f:
        if isinstance(data, dict):
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 完成！共修复 {fixed_count} 篇文献的期刊名称")

if __name__ == '__main__':
    fix_index_json()
    fix_history_json()
    print("\n🎉 所有数据已修复完成！")
