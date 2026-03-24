#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate daily summary pages for GitHub Pages.

- Input (preferred): data/index.json (keyword-filtered global index)
  - Fallback: data/ai_relevant.json (created by run_optimized_sync)
- Output:
  - docs/daily/YYYY-MM-DD.html
  - docs/daily/summaries.json
"""
import os
import json
import html
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import hashlib

from ai_summarizer import AISummarizer


def beijing_today() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime('%Y-%m-%d')

def beijing_yesterday() -> str:
    tz = timezone(timedelta(hours=8))
    return (datetime.now(tz) - timedelta(days=1)).strftime('%Y-%m-%d')


def safe_text(value: str) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def safe_url(value: str) -> str:
    url = (value or "").strip()
    if not url:
        return "#"
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            return "#"
    except Exception:
        return "#"
    return html.escape(url, quote=True)

def format_authors(authors) -> str:
    if not authors:
        return ""
    if isinstance(authors, list):
        names = [str(a).replace("\n", " ").strip() for a in authors if str(a).strip()]
        if len(names) <= 6:
            return ", ".join(names)
        return ", ".join(names[:6]) + f" 等{len(names)}位作者"
    return str(authors).replace("\n", " ").strip()

def arxiv_badge(item: Dict) -> str:
    """Return a readable arXiv category badge from item fields."""
    journal = (item.get("journal") or "").strip()
    if journal.lower() != "arxiv":
        return ""
    cat = (item.get("arxiv_category") or "").strip()
    if not cat:
        # fallback: infer from source_url
        src = (item.get("source_url") or "").strip()
        marker = "/rss/"
        if marker in src:
            cat = src.split(marker, 1)[1].strip()
    if not cat:
        return ""
    return cat

def load_relevant(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def load_index_articles(path: str = "data/index.json") -> List[Dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        return data.get("articles", []) or []
    except Exception:
        return []


def ensure_dirs():
    os.makedirs('docs/daily', exist_ok=True)

def digest_links(articles: List[Dict]) -> str:
    links = sorted({(a.get("link") or "").strip() for a in articles if (a.get("link") or "").strip()})
    raw = "\n".join(links).encode("utf-8")
    return hashlib.md5(raw).hexdigest()

def render_daily_html(date_str: str, summary: Dict) -> str:
    items = summary.get("full_list") or summary.get("summaries") or []
    def render_item(item: Dict) -> str:
        journal = safe_text(item.get("journal", ""))
        arxiv_cat = safe_text(arxiv_badge(item))
        authors = safe_text(format_authors(item.get("authors")))
        ai_score = item.get("ai_score")
        meta_parts = []
        if journal:
            if arxiv_cat:
                meta_parts.append(f"<span class='meta-journal'>📖 {journal} / {arxiv_cat}</span>")
            else:
                meta_parts.append(f"<span class='meta-journal'>📖 {journal}</span>")
        if authors:
            meta_parts.append(f"<span class='meta-authors'>👤 {authors}</span>")
        if ai_score is not None and str(ai_score).strip() != "":
            meta_parts.append(f"<span class='meta-score'>🔥 {safe_text(ai_score)}</span>")
        meta_html = f"<div class='article-meta'>{' | '.join(meta_parts)}</div>" if meta_parts else ""

        return f"""
        <div class=\"article-card\">
            <div class=\"article-header\">
                <div class=\"article-title-en\">{safe_text(item.get('title_en',''))}</div>
                <div class=\"article-title-zh\">{safe_text(item.get('title_zh',''))}</div>
            </div>
            {meta_html}
            <div class=\"article-summary\">{safe_text(item.get('summary',''))}</div>
            <div class=\"article-link\"><a href=\"{safe_url(item.get('link',''))}\" target=\"_blank\" rel=\"noopener noreferrer\">🔗 原文链接</a></div>
        </div>
        """

    items_html = "".join(render_item(item) for item in items)

    overview = safe_text(summary.get('overview', ''))
    trends = safe_text(summary.get('trends', ''))

    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{date_str} 每日摘要 - 文献追踪系统</title>
  <link rel=\"stylesheet\" href=\"../style.css\" />
	  <style>
	    .daily-container {{ max-width: 960px; margin: 0 auto; padding: 20px; }}
	    .section {{ margin: 18px 0; padding: 16px; background: var(--bg-card); border-radius: 12px; box-shadow: var(--shadow-md); }}
	    .article-card {{ margin: 14px 0; padding: 16px; background: var(--bg-card); border-radius: 12px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-color); }}
	    .article-title-en {{ font-weight: 600; margin-bottom: 6px; }}
	    .article-title-zh {{ color: var(--text-secondary); margin-bottom: 8px; }}
	    .article-meta {{ color: var(--text-muted); font-size: 0.92em; margin: 6px 0 10px; }}
	    .article-summary {{ color: var(--text-primary); }}
	    .article-link a {{ color: var(--accent-primary); text-decoration: none; }}
	    .article-link a:hover {{ text-decoration: underline; }}
	    .back-link {{ display: inline-block; margin-bottom: 14px; color: var(--accent-primary); text-decoration: none; }}
	    .back-link:hover {{ text-decoration: underline; }}
	  </style>
</head>
<body>
  <div class=\"daily-container\">
    <a href=\"../index.html\" class=\"back-link\">← 返回主页</a>
    <h1>📰 {date_str} 每日文献摘要</h1>
    <div class=\"section\"><strong>总览：</strong> {overview}</div>
    <div class=\"section\"><strong>热点：</strong> {trends}</div>
    <div class=\"section\">
      <h2>今日文献（每日摘要）</h2>
      {items_html if items_html else '<p>今日无文献</p>'}
    </div>
  </div>
</body>
</html>
"""


def update_index(date_str: str, total: int):
    index_path = os.path.join('docs/daily', 'summaries.json')
    data = {"summaries": []}
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {"summaries": []}
    summaries = [s for s in data.get('summaries', []) if s.get('date') != date_str]
    summaries.insert(0, {"date": date_str, "file": f"{date_str}.html", "total": total})
    data["summaries"] = summaries[:120]
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_summary_index() -> Dict:
    index_path = os.path.join("docs/daily", "summaries.json")
    if not os.path.exists(index_path):
        return {"summaries": []}
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f) or {"summaries": []}
    except Exception:
        return {"summaries": []}

def save_summary_index(summaries: List[Dict]):
    index_path = os.path.join("docs/daily", "summaries.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"summaries": summaries}, f, ensure_ascii=False, indent=2)

def preserve_existing_entry(prev: Dict, date_str: str) -> Dict:
    preserved = dict(prev or {})
    preserved["date"] = date_str
    preserved["file"] = preserved.get("file") or f"{date_str}.html"
    if "total" not in preserved:
        preserved["total"] = 0
    return preserved

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=None, help='YYYY-MM-DD (Beijing). 默认使用北京时间昨天以保证日报完整。')
    parser.add_argument('--days', default="1", help='生成最近 N 天（包含 --date 指定的日期）。用于补回漏抓/晚到数据。')
    parser.add_argument('--force', action='store_true', help='强制重新生成（忽略 summaries.json 中的 digest/total 缓存）。')
    args = parser.parse_args()

    # 默认生成“北京时间昨天”的日报：与 Actions 的抓取频率 (08:00/20:00) 匹配，避免当天数据不全导致“摘要缺失/为0”。
    date_str = args.date or beijing_yesterday()
    try:
        days = max(1, int(str(args.days).strip()))
    except Exception:
        days = 1

    ensure_dirs()

    # Prefer full daily list from index.json, but always union with ai_relevant.json
    # to avoid omitting focus-relevant papers.
    index_articles = load_index_articles("data/index.json")
    relevant_articles = load_relevant("data/ai_relevant.json")

    existing_index = load_summary_index()
    existing_items = existing_index.get("summaries", []) or []
    existing_by_date = {s.get("date"): s for s in existing_items if isinstance(s, dict) and s.get("date")}

    new_entries: List[Dict] = []
    api_key = os.environ.get('AI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    provider = os.environ.get('AI_PROVIDER') or 'openrouter'
    summarizer = AISummarizer(provider, api_key) if api_key else None

    base_dt = datetime.strptime(date_str, "%Y-%m-%d")
    # Generate newest -> oldest to keep logs intuitive.
    for i in range(days):
        day_dt = base_dt - timedelta(days=i)
        day_str = day_dt.strftime("%Y-%m-%d")

        relevant_day = [a for a in relevant_articles if (a.get("pub_date") or "").startswith(day_str)]
        relevant_links = {a.get("link") for a in relevant_day if a.get("link")}

        index_day = [
            a for a in index_articles
            if (a.get("pub_date") or "").startswith(day_str) and (a.get("link") not in relevant_links)
        ]

        # Relevant first
        day_articles = relevant_day + index_day

        total = len(day_articles)
        digest = digest_links(day_articles) if day_articles else ""

        out_path = os.path.join("docs/daily", f"{day_str}.html")
        prev = existing_by_date.get(day_str) or {}
        prev_digest = str(prev.get("digest") or "")
        prev_total = prev.get("total")

        should_skip = (
            (not args.force)
            and os.path.exists(out_path)
            and prev_digest
            and prev_digest == digest
            and isinstance(prev_total, int)
            and prev_total == total
        )

        if should_skip:
            print(f"⏭️  Skip daily page (unchanged): {out_path}")
            new_entries.append({"date": day_str, "file": f"{day_str}.html", "total": total, "digest": digest})
        else:
            try:
                if not day_articles:
                    # still generate empty page so index shows date
                    summary = {"date": day_str, "total": 0, "overview": "今日无文献", "trends": "", "summaries": []}
                else:
                    if summarizer is None:
                        raise ValueError("AI_API_KEY is empty; cannot generate daily summary")
                    summary = summarizer.generate_daily_summary(day_articles, day_str)

                page_html = render_daily_html(day_str, summary)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(page_html)
                print(f"✅ Daily page generated: {out_path}")
                new_entries.append({"date": day_str, "file": f"{day_str}.html", "total": total, "digest": digest})
            except Exception as exc:
                has_existing_page = os.path.exists(out_path)
                if has_existing_page:
                    print(f"⚠️ Daily page generation failed for {day_str}, preserving existing page: {exc}")
                    new_entries.append(preserve_existing_entry(prev, day_str))
                else:
                    print(f"⚠️ Daily page generation failed for {day_str}, skipping this date for now: {exc}")

    # Merge index entries: update our generated dates, keep others, then sort by date desc.
    updated_dates = {e.get("date") for e in new_entries if e.get("date")}
    merged = [e for e in existing_items if e.get("date") not in updated_dates]
    merged.extend(new_entries)
    merged = [e for e in merged if isinstance(e, dict) and e.get("date")]
    merged.sort(key=lambda x: x.get("date") or "", reverse=True)
    save_summary_index(merged[:120])


if __name__ == '__main__':
    main()
