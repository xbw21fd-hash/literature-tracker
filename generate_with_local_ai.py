#!/usr/bin/env python3
"""
完整的日报生成流程 - 使用本地AI生成的摘要
"""

import os
import sys
import json
import shutil

# 获取项目根目录（使用相对路径）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from generate_daily_pages import (
    load_index_articles, load_relevant, load_summary_index, save_summary_index,
    collect_daily_articles, ensure_dirs, render_daily_html,
    sync_daily_rss_feeds, enhance_daily_archive, preserve_existing_entry
)
from focus_filter import filter_focus_items, filter_daily_focus_items, focus_priority

# 路径配置
AI_RESPONSES_DIR = os.path.join(BASE_DIR, "ai_responses")
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DAILY_DIR = os.path.join(BASE_DIR, "docs", "daily")

def generate_daily_with_local_ai(date_str: str, force: bool = False):
    """使用本地AI响应生成日报"""
    
    print(f"📅 生成 {date_str} 的日报...")
    
    # 检查AI响应是否存在
    response_file = os.path.join(AI_RESPONSES_DIR, f"{date_str}_response.json")
    if not os.path.exists(response_file):
        print(f"❌ 未找到AI响应文件: {response_file}")
        print(f"💡 请先运行: python3 prepare_ai_prompt.py {date_str}")
        print(f"   然后让我生成摘要并保存到上述路径")
        return False
    
    # 加载AI摘要 - 添加异常处理
    try:
        with open(response_file, "r", encoding="utf-8") as f:
            ai_summary = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 文件不存在: {response_file}")
        return False
    except Exception as e:
        print(f"❌ 加载AI响应文件失败: {e}")
        return False
    
    # 验证必要字段
    if not isinstance(ai_summary, dict):
        print(f"❌ AI响应格式错误: 应为字典，实际为 {type(ai_summary)}")
        return False
    
    # 添加统计信息
    try:
        index_articles = load_index_articles(os.path.join(DATA_DIR, "index.json"))
        relevant_articles = load_relevant(os.path.join(DATA_DIR, "ai_relevant.json"))
        collected = collect_daily_articles(index_articles, relevant_articles, date_str)
    except Exception as e:
        print(f"⚠️ 加载文章数据失败: {e}，使用默认值")
        collected = {
            "dropped_articles": [],
            "raw_day_articles": [],
            "focused_articles": ai_summary.get("full_list", []) or ai_summary.get("summaries", [])
        }
    
    ai_summary["date"] = date_str
    ai_summary["excluded_count"] = len(collected.get("dropped_articles", []))
    ai_summary["raw_total"] = len(collected.get("raw_day_articles", []))
    ai_summary["focused_total"] = len(collected.get("focused_articles", []))
    
    # 确保summaries字段存在（兼容）
    if "summaries" not in ai_summary:
        ai_summary["summaries"] = ai_summary.get("full_list", [])
    
    # 生成HTML
    try:
        ensure_dirs()
        out_path = os.path.join(DOCS_DAILY_DIR, f"{date_str}.html")
        
        page_html = render_daily_html(date_str, ai_summary)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)
        
        print(f"✅ 日报已生成: {out_path}")
    except Exception as e:
        print(f"❌ 生成HTML失败: {e}")
        return False
    
    # 更新索引
    try:
        existing_index = load_summary_index()
        existing_items = existing_index.get("summaries", []) or []
        
        total = len(ai_summary.get("full_list", []))
        # 使用更安全的方式计算digest
        try:
            full_list = ai_summary.get("full_list", [])
            digest = hash(json.dumps(full_list, sort_keys=True, default=str)) % (2**32)
        except Exception:
            digest = hash(str(full_list)) % (2**32)
        
        new_entry = {"date": date_str, "file": f"{date_str}.html", "total": total, "digest": str(digest)}
        
        # 合并索引
        updated_dates = {new_entry.get("date")}
        merged = [e for e in existing_items if e.get("date") not in updated_dates]
        merged.append(new_entry)
        merged = [e for e in merged if isinstance(e, dict) and e.get("date")]
        merged.sort(key=lambda x: x.get("date") or "", reverse=True)
        save_summary_index(merged[:120])
    except Exception as e:
        print(f"⚠️ 更新索引失败: {e}")
        # 非致命错误，继续执行
    
    # 同步RSS
    try:
        rss_changed = sync_daily_rss_feeds(index_articles, relevant_articles, merged[:120])
        print(f"📡 同步了 {rss_changed} 个RSS feed")
    except Exception as e:
        print(f"⚠️ 同步RSS失败: {e}")
    
    # 增强导航
    try:
        summaries_path = os.path.join(DOCS_DAILY_DIR, "summaries.json")
        enhanced = enhance_daily_archive(summaries_path)
        print(f"🧭 增强了 {enhanced} 个页面的导航")
    except Exception as e:
        print(f"⚠️ 增强导航失败: {e}")
    
    return True

def main():
    """主函数"""
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
    else:
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")
    
    force = "--force" in sys.argv
    
    success = generate_daily_with_local_ai(date_str, force)
    
    if success:
        print(f"\n🎉 {date_str} 日报生成完成!")
        print(f"📄 文件: docs/daily/{date_str}.html")
        print(f"🌐 预览: https://hongyu-yu.github.io/literature-tracker/daily/{date_str}.html")
    else:
        print(f"\n❌ 生成失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
