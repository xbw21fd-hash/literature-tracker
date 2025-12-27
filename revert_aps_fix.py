#!/usr/bin/env python3
"""
将错误归类为APS的期刊名恢复
"""

import json

def revert_aps_in_index():
    """恢复 docs/data/index.json 中的APS归类"""
    filepath = "docs/data/index.json"
    
    print(f"正在恢复 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    articles = data.get('articles', [])
    reverted_count = 0
    
    for article in articles:
        # 如果期刊是APS，尝试从source_url推断具体期刊
        if article.get('journal') == 'APS':
            source_url = article.get('source_url', '')
            
            # 根据URL推断具体期刊
            if 'prl.xml' in source_url or '/prl/' in source_url:
                article['journal'] = 'Phys. Rev. Lett.'
                reverted_count += 1
            elif 'prb.xml' in source_url or '/prb/' in source_url:
                article['journal'] = 'Phys. Rev. B'
                reverted_count += 1
            elif 'prx.xml' in source_url or '/prx/' in source_url:
                article['journal'] = 'Phys. Rev. X'
                reverted_count += 1
            elif 'prmaterials.xml' in source_url or '/prmaterials/' in source_url:
                article['journal'] = 'Phys. Rev. Materials'
                reverted_count += 1
            elif 'prresearch.xml' in source_url or '/prresearch/' in source_url:
                article['journal'] = 'Phys. Rev. Research'
                reverted_count += 1
            elif 'prxenergy.xml' in source_url or '/prxenergy/' in source_url:
                article['journal'] = 'PRX Energy'
                reverted_count += 1
            elif 'rmp.xml' in source_url or '/rmp/' in source_url:
                article['journal'] = 'Rev. Mod. Phys.'
                reverted_count += 1
            elif 'prapplied.xml' in source_url or '/prapplied/' in source_url:
                article['journal'] = 'Phys. Rev. Applied'
                reverted_count += 1
            elif 'physics.xml' in source_url or '/physics/' in source_url:
                article['journal'] = 'Physics'
                reverted_count += 1
    
    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 完成！共恢复 {reverted_count} 篇文献的期刊名称")

if __name__ == '__main__':
    revert_aps_in_index()
