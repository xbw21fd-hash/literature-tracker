# 日报条目富化 + 删除 TikTok Feed 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 删除不好用的 TikTok 式 `/feed`，把已有的深度分析+英文信息图+中文5要素合并回日报**每一条**，做成「浏览标题列表 → 一句话亮点+标签可分拣 → 点开看分析+一张图」的纯单列表。

**Architecture:** `run_deep.py` 继续富化并写 `arxiv_core_<date>.json`（AI 交叉）和 `aps_<date>.json`（APS 全文），但不再写 `feed.json`。`generate_daily_pages.py` 渲染时读这两个 JSON，按 `normalize_link` 合并进一个扁平、按 tier 排序、含图深析置顶、逐条可 `<details>` 展开的单列表。收藏复用现成 `bookmarks.js`。

**Tech Stack:** Python 3.11（stdlib 渲染，无模板引擎）、原生 JS（bookmarks.js）、GitHub Actions。本地测试 `python3 run_tests.py`（stdlib，无 pip）+ node jsdom。

**真实数据形状（已核实）：**
- `arxiv_core_<date>.json` 富化项 keys：`link, deep_analysis, image, poster{doc_id,elements,elements_en,image,title_zh}, poster_elements, category, title_zh, abstract, summary, journal, source, title`。同文件内未富化项无 `deep_analysis`/`image`。`image` 形如 `images/posters/<id>.webp`。
- `aps_<date>.json` 项 keys（部分）：`title, title_zh(常为 null), doi(裸 DOI 如 "10.1103/766t-tqsy"), link(常 null), category, deep_analysis, poster{doc_id,elements,image}, doc_id`。`poster.elements` 键为 `研究问题/创新方法/工作流程/关键结果/应用价值`。
- join 键：`normalize_link(link or doi)`（已有 `from feed_builder import normalize_link`，但 feed_builder 将被删 → 见 Task 1 把 `normalize_link` 迁出）。

---

## 文件结构

| 文件 | 责任 | 改动 |
|---|---|---|
| `link_utils.py` | `normalize_link` 单一归一化工具（从 feed_builder 迁出，去掉对将删模块的依赖） | 新建 |
| `run_deep.py` | 编排富化；不再写 feed.json | 改 |
| `generate_daily_pages.py` | 读富化 + 渲染单列表 | 改（核心） |
| `docs/index.html` `docs/sw.js` `docs/style.css` `weekly_summary.py` | 去 Feed/likes 引用 | 改 |
| `docs/feed.* docs/data/feed.json feed_builder.py docs/likes.* docs/test-feed.html docs/test-likes.html test_feed_json.py` | TikTok Feed + 点赞 | 删 |
| `test_daily_pages_render.py` `test_run_deep.py` | 测试 | 改 |

---

## Task 1: 迁出 `normalize_link`，run_deep 停写 feed.json

**Files:**
- Create: `link_utils.py`
- Modify: `feed_builder.py`（将删，但先让 normalize_link 有新家）, `run_deep.py:15,261-263`, `generate_daily_pages.py:27`
- Test: `test_link_utils.py`

- [ ] **Step 1: 写失败测试** `test_link_utils.py`

```python
from link_utils import normalize_link

def test_bare_doi_becomes_url():
    assert normalize_link("10.1103/766t-tqsy") == "https://doi.org/10.1103/766t-tqsy"

def test_http_link_unchanged():
    assert normalize_link("http://arxiv.org/abs/2601.001") == "http://arxiv.org/abs/2601.001"

def test_empty_returns_empty():
    assert normalize_link("") == ""
    assert normalize_link(None) == ""
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_link_utils.py -v`（或 `python3 run_tests.py`）
Expected: FAIL `ModuleNotFoundError: link_utils`

- [ ] **Step 3: 实现 `link_utils.py`**（把 feed_builder 现有逻辑搬来，先看原实现再复制）

```python
"""链接归一化：裸 DOI → https://doi.org/...；其余原样返回。"""
import re

_DOI_RE = re.compile(r'^10\.\d{4,9}/\S+$', re.I)

def normalize_link(link):
    s = (link or "").strip()
    if not s:
        return ""
    if _DOI_RE.match(s):
        return f"https://doi.org/{s}"
    return s
```

> 实现前先 `grep -n "def normalize_link" -A15 feed_builder.py`，若原逻辑更复杂（如去 `doi:` 前缀）务必照搬，勿简化。

- [ ] **Step 4: feed_builder 改为从 link_utils 复用（避免删除时丢实现）**

`feed_builder.py` 顶部把本地 `def normalize_link` 替换为 `from link_utils import normalize_link`（feed_builder 本任务尚不删，Task 2 才删）。

- [ ] **Step 5: `generate_daily_pages.py:27` 改 import**

```python
from link_utils import normalize_link
```
（删除 `from feed_builder import normalize_link`）

- [ ] **Step 6: run_deep 停写 feed.json**

`run_deep.py:15` 删 `from feed_builder import build_feed, write_feed_json`。
`run_deep.py:261-263` 删这三行（`write_feed_json(...)` / 注释 / `print("✅ ... feed.json written")`），改成：
```python
    print("✅ run_deep done (feed.json no longer written; enrichment lives in arxiv_core/aps)")
```
若 `_load_existing_feeds` / `build_feed` 仅服务 feed.json，连带删除其定义与调用（先 `grep -n "_load_existing_feeds\|build_feed" run_deep.py` 确认无其他用途）。

- [ ] **Step 7: 运行测试**

Run: `python3 run_tests.py`
Expected: link_utils 测试 PASS；run_deep import 不报错（`python3 -c "import run_deep"`）。

- [ ] **Step 8: 提交**

```bash
git add link_utils.py test_link_utils.py feed_builder.py run_deep.py generate_daily_pages.py
git commit -m "refactor: extract normalize_link to link_utils; run_deep stops writing feed.json"
```

---

## Task 2: 删除 TikTok Feed + 点赞前端，清理引用

**Files:**
- Delete: `docs/feed.html` `docs/feed.js` `docs/feed.css` `docs/data/feed.json` `feed_builder.py` `docs/test-feed.html` `test_feed_json.py` `docs/likes.js` `docs/likes.css` `docs/test-likes.html`
- Modify: `docs/index.html` `docs/sw.js` `docs/style.css` `weekly_summary.py` `generate_daily_pages.py`

- [ ] **Step 1: 删除文件**

```bash
git rm docs/feed.html docs/feed.js docs/feed.css docs/data/feed.json feed_builder.py \
       docs/test-feed.html test_feed_json.py docs/likes.js docs/likes.css docs/test-likes.html
```

- [ ] **Step 2: `docs/index.html` — feed-hero 换成每日摘要入口 + 去 likes 引用**

把 `<a class="feed-hero" href="feed.html">…</a>`（约 L106-113）整块替换为：
```html
        <a class="daily-hero-entry" href="daily/">
          <div class="feed-hero-emoji">📰</div>
          <div class="feed-hero-text">
            <div class="feed-hero-title">每日文献日报</div>
            <div class="feed-hero-sub">含图深度分析 · AI 交叉优先 · ⭐ 可收藏</div>
          </div>
          <div class="feed-hero-arrow">→</div>
        </a>
```
删除 `<link rel="stylesheet" href="likes.css" />` 与 `<script defer src="likes.js"></script>`（若存在）。`grep -n "likes\|feed.html\|feed.js" docs/index.html` 清干净（保留 `feed.xml` RSS 行）。

- [ ] **Step 3: `docs/style.css` — 复用 feed-hero 样式给 daily-hero-entry**

`grep -n "\.feed-hero" docs/style.css`，把选择器 `.feed-hero` 改为 `.feed-hero, .daily-hero-entry`（保留视觉，不删样式块）。

- [ ] **Step 4: `docs/sw.js` — precache 去掉 feed/likes**

`grep -n "feed\|likes" docs/sw.js`，从 precache 数组删除 `'feed.html' 'feed.js' 'feed.css' 'likes.js' 'likes.css'`（保留 `feed.xml`）。同时把 cache 版本号自增（如 `v3`→`v4`）以失效旧缓存。

- [ ] **Step 5: `generate_daily_pages.py` — 去 likes.css/js 注入 + 去 Feed 链接**

`<head>` 模板（约 L626-635）删 `<link rel="stylesheet" href="../likes.css" />` 与 `<script defer src="../likes.js"></script>`。
`render_deep_section` 将在 Task 6 整体移除；此处先不动。

- [ ] **Step 6: `weekly_summary.py` — 去 likes.css**

`grep -n "likes.css\|likes.js" weekly_summary.py`，删除对应注入行。

- [ ] **Step 7: 验证无活跃引用**

Run:
```bash
grep -rn "feed\.html\|feed\.js\|likes\.js\|likes\.css\|feed_builder\|write_feed_json\|docs/data/feed\.json" \
  --include=*.py --include=*.js --include=*.html . | grep -v "docs/daily/20" | grep -v "feed\.xml"
```
Expected: 无输出（`docs/daily/20*.html` 历史归档里的旧引用不算，留存）。

- [ ] **Step 8: 提交**

```bash
git add -A
git commit -m "feat: remove TikTok feed + likes UI; index points to daily report"
```

---

## Task 3: `load_enrichment` — 读 arxiv_core 建富化 map

**Files:**
- Modify: `generate_daily_pages.py`（新增模块级函数，置于 `build_tier2_candidates` 之后约 L345）
- Test: `test_daily_pages_render.py`（追加）

- [ ] **Step 1: 写失败测试**（追加到 `test_daily_pages_render.py`）

```python
def test_load_enrichment_keys_by_link_and_skips_plain(tmp_path=None):
    import json, os, tempfile
    from generate_daily_pages import load_enrichment
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    rows = [
        {"link": "http://arxiv.org/abs/1", "deep_analysis": "## 深析",
         "image": "images/posters/a.webp",
         "poster": {"elements": {"研究问题": "q", "创新方法": "m"}},
         "category": "AI×物理", "title_zh": "中文一"},
        {"link": "10.1103/xyz", "deep_analysis": "## 二", "poster": {"image": "images/posters/b.webp",
         "elements": {"关键结果": "r"}}, "category": "AI×化学·材料", "title_zh": "中文二"},
        {"link": "http://arxiv.org/abs/3", "summary": "no enrichment"},  # plain → skipped
    ]
    with open(os.path.join(d, "data", "arxiv_core_2026-06-01.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    cwd = os.getcwd()
    try:
        os.chdir(d)
        m = load_enrichment("2026-06-01")
    finally:
        os.chdir(cwd)
    assert "http://arxiv.org/abs/1" in m
    assert m["http://arxiv.org/abs/1"]["image"] == "images/posters/a.webp"
    assert m["http://arxiv.org/abs/1"]["elements"]["研究问题"] == "q"
    # bare DOI normalized as key
    assert "https://doi.org/10.1103/xyz" in m
    assert m["https://doi.org/10.1103/xyz"]["image"] == "images/posters/b.webp"
    # plain row (no deep, no image) skipped
    assert "http://arxiv.org/abs/3" not in m

def test_load_enrichment_missing_file_returns_empty():
    from generate_daily_pages import load_enrichment
    assert load_enrichment("1999-01-01") == {}
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_daily_pages_render.py -k load_enrichment -v`
Expected: FAIL `cannot import name 'load_enrichment'`

- [ ] **Step 3: 实现**（`generate_daily_pages.py`，模块级）

```python
def load_enrichment(date_str: str) -> Dict[str, Dict]:
    """读 data/arxiv_core_<date>.json → {normalize_link(link): enrich}。
    enrich = {deep_analysis, image, elements, category, title_zh}。
    仅返回真正带 deep_analysis 或 image 的行；缺文件/坏文件 → {}（安全降级）。"""
    out: Dict[str, Dict] = {}
    path = os.path.join("data", f"arxiv_core_{date_str}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            rows = json.load(f)
    except Exception:
        return out
    if not isinstance(rows, list):
        return out
    for r in rows:
        link = normalize_link((r.get("link") or "").strip())
        if not link:
            continue
        poster = r.get("poster") or {}
        image = r.get("image") or poster.get("image")
        deep = r.get("deep_analysis") or ""
        if not (deep or image):
            continue
        out[link] = {
            "deep_analysis": deep,
            "image": image,
            "elements": r.get("poster_elements") or poster.get("elements") or {},
            "category": r.get("category") or "",
            "title_zh": r.get("title_zh") or poster.get("title_zh") or "",
        }
    return out
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest test_daily_pages_render.py -k load_enrichment -v`
Expected: PASS（2 个）

- [ ] **Step 5: 提交**

```bash
git add generate_daily_pages.py test_daily_pages_render.py
git commit -m "feat: load_enrichment reads arxiv_core into link-keyed map"
```

---

## Task 4: `build_unified_items` — 合并 APS + full_list，附富化，按 tier 排序

**Files:**
- Modify: `generate_daily_pages.py`（模块级，紧接 `load_enrichment` 之后）
- Test: `test_daily_pages_render.py`（追加）

- [ ] **Step 1: 写失败测试**

```python
def test_build_unified_items_merges_and_sorts():
    from generate_daily_pages import build_unified_items
    full_list = [
        {"title": "Plain paper", "title_en": "Plain paper", "summary": "x",
         "link": "http://arxiv.org/abs/plain"},
        {"title": "AI cross arxiv", "title_en": "AI cross arxiv", "title_zh": "交叉",
         "summary": "y", "link": "http://arxiv.org/abs/cross"},
    ]
    enrich_map = {
        "http://arxiv.org/abs/cross": {"deep_analysis": "## d", "image": "images/posters/c.webp",
                                       "elements": {"研究问题": "q"}, "category": "AI×物理", "title_zh": "交叉"},
    }
    aps_items = [
        {"title": "APS fulltext", "title_zh": None, "doi": "10.1103/abc", "category": "软物质",
         "deep_analysis": "## aps", "poster": {"image": "images/posters/aps.webp",
                                               "elements": {"创新方法": "m"}}},
        {"title": "APS plain", "doi": "10.1103/plain", "poster": {}},  # no enrichment → skipped
    ]
    out = build_unified_items(full_list, enrich_map, aps_items)
    # APS full-text (tier 0) first, then AI-cross arxiv (tier 1), plain (tier 2) last
    tiers = [it["_tier"] for it in out]
    assert tiers == sorted(tiers)
    assert out[0]["_tier"] == 0 and out[0]["_enrich"]["image"] == "images/posters/aps.webp"
    assert out[0]["link"] == "https://doi.org/10.1103/abc"  # bare DOI normalized
    cross = next(it for it in out if it["link"] == "http://arxiv.org/abs/cross")
    assert cross["_tier"] == 1 and cross["_enrich"]["category"] == "AI×物理"
    plain = next(it for it in out if it["link"] == "http://arxiv.org/abs/plain")
    assert plain["_tier"] == 2 and plain["_enrich"] is None
    # APS-without-enrichment dropped (not in full_list, no deep/image)
    assert all("APS plain" != it.get("title") for it in out)

def test_build_unified_items_dedups_aps_already_in_full_list():
    from generate_daily_pages import build_unified_items
    # same paper appears both as APS (tier0) and in full_list → keep APS, drop full_list dup
    full_list = [{"title": "Dup", "link": "https://doi.org/10.1103/dup", "summary": "s"}]
    aps_items = [{"title": "Dup", "doi": "10.1103/dup", "deep_analysis": "d",
                  "poster": {"image": "p.webp"}}]
    out = build_unified_items(full_list, {}, aps_items)
    assert len(out) == 1 and out[0]["_tier"] == 0
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_daily_pages_render.py -k build_unified -v`
Expected: FAIL `cannot import name 'build_unified_items'`

- [ ] **Step 3: 实现**

```python
def build_unified_items(full_list, enrich_map, aps_items):
    """合并 APS 全文(tier0) + full_list(tier1 富化 / tier2 普通) 成一个扁平列表，
    按 (tier, focus_priority) 排序。每项注入 _tier 与 _enrich(dict|None)。"""
    items: List[Dict] = []
    seen = set()
    for a in (aps_items or []):
        link = normalize_link((a.get("link") or a.get("doi") or "").strip())
        poster = a.get("poster") or {}
        image = poster.get("image") or a.get("image")
        deep = a.get("deep_analysis") or ""
        if not (deep or image):
            continue  # APS 无富化 → 跳过（APS 不在 full_list，不会丢可展示内容）
        it = dict(a)
        it["link"] = link or it.get("link") or ""
        it["_tier"] = 0
        it["_enrich"] = {
            "deep_analysis": deep, "image": image,
            "elements": poster.get("elements") or {},
            "category": a.get("category") or "",
            "title_zh": a.get("title_zh") or poster.get("title_zh") or "",
        }
        items.append(it)
        if link:
            seen.add(link)
    for it0 in (full_list or []):
        link = normalize_link((it0.get("link") or "").strip())
        if link and link in seen:
            continue
        it = dict(it0)
        it["link"] = link or it0.get("link") or ""
        en = enrich_map.get(link) if link else None
        it["_tier"] = 1 if en else 2
        it["_enrich"] = en
        items.append(it)
        if link:
            seen.add(link)
    items.sort(key=lambda x: (x.get("_tier", 2), focus_priority(x)))
    return items
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest test_daily_pages_render.py -k build_unified -v`
Expected: PASS（2 个）

- [ ] **Step 5: 提交**

```bash
git add generate_daily_pages.py test_daily_pages_render.py
git commit -m "feat: build_unified_items merges APS + arxiv into tier-sorted list"
```

---

## Task 5: 模块级 `render_meta_chips` + `render_unified_item`（列表态 + 展开）

**Files:**
- Modify: `generate_daily_pages.py`（把嵌套 `render_meta_chips` 提到模块级；新增 `render_unified_item`）
- Test: `test_daily_pages_render.py`（追加）

- [ ] **Step 1: 写失败测试**

```python
def test_render_unified_item_enriched_has_details_and_image():
    from generate_daily_pages import render_unified_item
    item = {"title": "Cross", "title_en": "Cross", "title_zh": "交叉标题",
            "summary": "一句话亮点", "link": "http://arxiv.org/abs/cross", "journal": "arXiv",
            "_tier": 1, "_enrich": {"deep_analysis": "## 深析正文", "image": "images/posters/c.webp",
                                    "elements": {"研究问题": "q", "创新方法": "m", "工作流程": "f",
                                                 "关键结果": "r", "应用价值": "v"},
                                    "category": "AI×物理", "title_zh": "交叉标题"}}
    html = render_unified_item(item, 1)
    assert "交叉标题" in html
    assert "enrich-badge" in html and "含图深析" in html
    assert "<details" in html
    assert 'src="../images/posters/c.webp"' in html   # daily lives at docs/daily/ → ../ prefix
    assert "daily-deep-elements" in html and "研究问题" in html
    assert "深析正文" in html
    assert 'data-bookmark-key="http://arxiv.org/abs/cross"' in html
    assert "poster-overlay" not in html               # image/text separated, no overlay

def test_render_unified_item_plain_has_no_details():
    from generate_daily_pages import render_unified_item
    item = {"title": "Plain", "title_en": "Plain", "summary": "brief",
            "link": "http://x", "journal": "arXiv", "_tier": 2, "_enrich": None}
    html = render_unified_item(item, 2)
    assert "<details" not in html
    assert "enrich-badge" not in html
    assert "brief" in html  # 一句话亮点仍在列表态显示
    assert 'data-bookmark-key="http://x"' in html
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_daily_pages_render.py -k render_unified -v`
Expected: FAIL `cannot import name 'render_unified_item'`

- [ ] **Step 3a: 把 `render_meta_chips` 提到模块级**

在 `render_daily_html` 内找到嵌套 `def render_meta_chips(item)`（约 L433-450）与其上方 `topic_labels` dict（约 L408-414），剪切到模块级（置于 `render_unified_item` 之前）。把模块级版本签名设为 `def render_meta_chips(item: Dict) -> str:`，函数体内 `topic_labels` 引用改为模块级常量 `TOPIC_LABELS`。在模块级新增：
```python
TOPIC_LABELS = {
    "physics": "物理 / 凝聚态", "chemistry": "化学 / 分子",
    "materials": "材料 / 器件", "methods": "方法 / 工具", "other": "其他",
}
```
并把函数体里 `topic_labels.get(...)` 改为 `TOPIC_LABELS.get(...)`。`render_daily_html` 内若仍有对 `topic_labels`/`render_meta_chips` 的本地引用，删掉本地定义、改用模块级。

- [ ] **Step 3b: 实现 `render_unified_item`（模块级）**

```python
def render_unified_item(item: Dict, index: int) -> str:
    en = item.get("_enrich")
    title_en = (item.get("title_en") or item.get("title") or "").strip()
    title_zh = (item.get("title_zh") or (en or {}).get("title_zh") or "").strip()
    show_zh = bool(title_zh) and title_zh.casefold() != title_en.casefold()
    disp_zh = safe_text(title_zh if show_zh else title_en)
    title_en_block = (f'<div class="daily-paper-title-en">{safe_text(title_en)}</div>'
                      if show_zh and title_en else "")
    meta_html = render_meta_chips(item)
    highlight = (item.get("summary") or item.get("abstract_zh")
                 or item.get("one_sentence_summary") or "").strip()
    hl_html = (f'<p class="daily-paper-highlight"><strong>💡 亮点：</strong>{safe_text(highlight)}</p>'
               if highlight else "")
    link = safe_url(item.get("link") or "")
    badge = '<span class="enrich-badge">📊 含图深析</span>' if en else ""
    details = ""
    if en:
        img = en.get("image")
        img_src = img if (not img or str(img).startswith(("http", "/", "../"))) else f"../{img}"
        figure = (f'<div class="poster-figure"><img loading="lazy" src="{safe_text(img_src)}" '
                  f'onerror="this.style.display=\'none\'"></div>') if img else ""
        el = en.get("elements") or {}
        rows = "".join(
            f'<div class="poster-row"><b>{safe_text(k)}</b>{safe_text(el.get(k, ""))}</div>'
            for k in ["研究问题", "创新方法", "工作流程", "关键结果", "应用价值"] if el.get(k))
        elems = f'<div class="daily-deep-elements">{rows}</div>' if rows else ""
        deep = safe_text(en.get("deep_analysis") or "")
        deep_html = f'<div class="deep-body">{deep}</div>' if deep else ""
        details = (f'<details class="enrich-details"><summary>📖 展开分析 + 配图</summary>'
                   f'{figure}{elems}{deep_html}</details>')
    return f"""
    <li class="daily-paper-card" id="paper-{index}" data-bookmark-key="{link}">
        <span class="daily-paper-number">{index:02d}</span>
        <div class="daily-paper-body">
            <div class="daily-paper-head"><div class="daily-paper-titles">
                <div class="daily-paper-title-zh">{disp_zh}{badge}</div>
                {title_en_block}
            </div></div>
            <div class="daily-paper-meta">{meta_html}</div>
            {hl_html}
            {details}
            <div class="daily-paper-actions"><a class="daily-news-link" href="{link}" target="_blank" rel="noopener noreferrer">阅读原文 ↗</a></div>
        </div>
    </li>
    """
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest test_daily_pages_render.py -k "render_unified or render_meta or daily_render" -v`
Expected: render_unified PASS（2 个）；既有渲染测试不回归（render_meta_chips 仍可用）。

- [ ] **Step 5: 提交**

```bash
git add generate_daily_pages.py test_daily_pages_render.py
git commit -m "feat: module-level render_meta_chips + render_unified_item (collapsed + details)"
```

---

## Task 6: 接线 —— `render_daily_html` 用单列表替换 今日精读+交叉重点+分组速览

**Files:**
- Modify: `generate_daily_pages.py:382-840`（render_daily_html 主体、TOC、侧栏 stats、内联 CSS）
- Test: `test_daily_pages_render.py`（改既有断言）

- [ ] **Step 1: 改测试以反映单列表（替换 main() 内旧断言 + deep section 测试）**

把 `test_daily_pages_render.py` 顶部 `main()` 中这些断言：
```python
    assert "今日摘要" in html
    assert "交叉重点" in html
    assert "完整速览" in html
```
改为：
```python
    assert "今日摘要" in html
    assert "今日文献" in html          # 新单列表标题
    assert "测试中文标题" in html       # 条目仍渲染
```
删除以下三个函数（依赖被移除的 `render_deep_section`）：`test_daily_renders_deep_read_section`、`test_deep_section_has_feed_link_and_no_overlay`、`test_render_deep_section_empty_returns_empty`、`test_deep_section_empty_still_empty`。新增一个整合测试：
```python
def test_daily_html_unified_list_includes_enriched(tmp_path=None):
    import json, os, tempfile
    from generate_daily_pages import render_daily_html
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"))
    with open(os.path.join(d, "data", "arxiv_core_2026-06-01.json"), "w", encoding="utf-8") as f:
        json.dump([{"link": "http://arxiv.org/abs/x", "deep_analysis": "## 深",
                    "image": "images/posters/x.webp",
                    "poster": {"elements": {"研究问题": "q"}},
                    "category": "AI×物理", "title_zh": "交叉中文"}], f, ensure_ascii=False)
    summary = {"overview": "ov", "trends": "tr", "full_list": [
        {"title_en": "X", "title_zh": "交叉中文", "summary": "亮点",
         "link": "http://arxiv.org/abs/x", "journal": "arXiv"},
        {"title_en": "Plain", "summary": "普通", "link": "http://y", "journal": "arXiv"}]}
    cwd = os.getcwd()
    try:
        os.chdir(d)
        html = render_daily_html("2026-06-01", summary)
    finally:
        os.chdir(cwd)
    assert "今日文献" in html
    assert "enrich-badge" in html and "<details" in html
    assert "../images/posters/x.webp" in html
    assert "poster-overlay" not in html
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_daily_pages_render.py -k "unified_list_includes or main" -v`
Expected: FAIL（"今日文献" 未出现 / render_deep 测试已删但主体仍渲染旧结构）

- [ ] **Step 3: 改 `render_daily_html` 主体**

3a. 顶部（约 L385-399）：删 `aps_items` 读取块与 `deep_section_html = render_deep_section(...)`，改为：
```python
    aps_items: List[Dict] = []
    try:
        aps_path = os.path.join("data", f"aps_{date_str}.json")
        if os.path.exists(aps_path):
            with open(aps_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                aps_items = loaded
    except Exception:
        aps_items = []
    enrich_map = load_enrichment(date_str)
    items = summary.get("full_list") or summary.get("summaries") or []
    unified = build_unified_items(items, enrich_map, aps_items)
```
（保留 `items` 供下方 stats/tags 复用；`highlight_items`/`collect_focus_highlights` 不再需要 → 删其行。）

3b. 删除嵌套的 `render_focus_item`、`render_item`、`render_group`、`safe_summary_text`、本地 `render_meta_chips`/`topic_labels`（已模块化）、`focus_html`/`focus_section_html`、`highlight_keys`/`grouped_source_items`/`grouped_items`/`group_blocks`/`paper_section_html` 相关块（约 L416-545 区段）。改为单列表：
```python
    unified_html = "".join(render_unified_item(it, i) for i, it in enumerate(unified, 1)) \
        or '<li class="daily-summary-card"><p>今日无目标方向文献。</p></li>'
    enriched_count = sum(1 for it in unified if it.get("_enrich"))
```

3c. 侧栏 stats（约 L538-545 `bucket_stats`/`sidebar_stats`）改为：
```python
    sidebar_stats = (
        f"<div class='daily-sidebar-fact'><span>文献总数</span><strong>{len(unified)}</strong></div>"
        f"<div class='daily-sidebar-fact'><span>含图深析</span><strong>{enriched_count}</strong></div>"
        f"<div class='daily-sidebar-fact'><span>期刊数</span><strong>{journal_count}</strong></div>"
    )
```

3d. HTML 模板正文（约 L790-820）：把 `{deep_section_html}` 与 `<section id="papers">…{paper_section_html}…</section>` 与交叉重点 focus 段，替换为单一：
```python
        {render_core_section(summary.get('core_items', []) or [], summary.get('core_direction_note') or '')}
        <section id="papers" class="daily-section">
            <div class="daily-section-head">
                <span class="daily-section-index">📚</span>
                <h2 class="daily-section-title">今日文献</h2>
                <span class="daily-core-count">{len(unified)} 篇 · {enriched_count} 含图深析</span>
            </div>
            <ol class="daily-paper-list">{unified_html}</ol>
        </section>
```
（保留 `render_core_section` 与 `#core-focus`。删除模板里"交叉重点"小标题与其 `{focus_section_html}`。）

3e. TOC（约 L757-761 与 L831-834）：把含 `交叉重点`/`完整速览` 的锚点项替换为：
```python
      {('<a href="#core-focus">核心关注</a>' if summary.get('core_items') else '')}
      <a href="#papers">今日文献</a>
```
两处 TOC 都同步。删除引用已移除 section 的锚点。

- [ ] **Step 4: 内联 CSS 增 enrich 样式**

在内联 `<style>` 中 `.daily-deep-elements`（约 L629）附近追加：
```python
    .enrich-badge{{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;
      background:#e8f1ff;color:#1456b8;font-size:12px;font-weight:600;vertical-align:middle;}}
    .enrich-details{{margin:8px 0;border-top:1px dashed #e3e8f0;padding-top:8px;}}
    .enrich-details > summary{{cursor:pointer;color:#1456b8;font-weight:600;list-style:none;}}
    .enrich-details > summary::-webkit-details-marker{{display:none;}}
    .enrich-details .poster-figure img{{width:100%;border-radius:10px;margin:8px 0;}}
    .deep-body{{white-space:pre-wrap;font-size:14px;line-height:1.7;color:#333;margin-top:8px;}}
```
（`.daily-deep-elements`/`.poster-row`/`.poster-figure` 既有规则保留——它们原属 render_deep_section，现复用。）

- [ ] **Step 5: 运行测试**

Run: `python3 run_tests.py`
Expected: `test_daily_pages_render.py` 全 PASS（含新 unified 整合测试）；其余既有测试不回归（bs4 缺失导致的失败属本地正常）。

- [ ] **Step 6: 渲染冒烟（真实数据）**

Run:
```bash
python3 - <<'PY'
import json
from generate_daily_pages import render_daily_html
s = json.load(open("docs/daily/summaries.json"))
PY
python3 -c "import generate_daily_pages as g, json; \
html=g.render_daily_html('2026-06-01', g.load_summary_for('2026-06-01') if hasattr(g,'load_summary_for') else {'full_list':[],'overview':'','trends':''}); \
print('今日文献' in html, 'enrich-badge' in html)"
```
> 若无 `load_summary_for`，改用：手动构造 `summary` = 从 `docs/daily/2026-06-01.html` 对应的缓存（或直接信任 Step 5 的整合测试）。冒烟非阻塞，主验证以 run_tests 为准。

- [ ] **Step 7: 提交**

```bash
git add generate_daily_pages.py test_daily_pages_render.py
git commit -m "feat: daily page renders unified enriched single list (replaces feed)"
```

---

## Task 7: `--rerender-only` + 工作流 run_deep 后重渲染（同日见图）

**Files:**
- Modify: `generate_daily_pages.py`（main() 参数）, `.github/workflows/generate-deep.yml`
- Test: `test_daily_pages_render.py`（追加 argparse 行为轻测可选，主靠手测）

- [ ] **Step 1: 看现有 main() 参数**

Run: `grep -n "argparse\|add_argument\|--days\|--force\|def main" generate_daily_pages.py`
读懂现有 `--days`/`--force` 解析与主循环结构（约 L962-1090）。

- [ ] **Step 2: 加 `--rerender-only` 分支**

在 argparse 处加：
```python
    parser.add_argument("--rerender-only", action="store_true",
                        help="只重渲染已有日期的 HTML（复用 summaries.json 缓存的 overview/trends + 新鲜 arxiv_core/aps 富化），不调用 AI、不抓取。")
```
在 main() 主流程开头分支：当 `args.rerender_only` 为真时，遍历最近 `--days` 天（默认 4），对每个有 `summaries.json` 条目的日期，读回其缓存 summary（`load_summary_index()` + 对应 `docs/daily/<date>` 的源数据）并仅调用 `render_daily_html(date, summary)` 重写 `docs/daily/<date>.html`，跳过抓取/AI 摘要/RSS。实现细节：
```python
    if args.rerender_only:
        from datetime import datetime, timedelta
        idx = {e["date"]: e for e in load_summary_index().get("summaries", [])}
        days = args.days or 4
        base = beijing_today()
        base_dt = datetime.strptime(base, "%Y-%m-%d")
        n = 0
        for k in range(days):
            ds = (base_dt - timedelta(days=k)).strftime("%Y-%m-%d")
            summ = _load_cached_summary(ds)   # 见下
            if not summ:
                continue
            html = render_daily_html(ds, summ)
            with open(os.path.join("docs", "daily", f"{ds}.html"), "w", encoding="utf-8") as f:
                f.write(html)
            n += 1
        print(f"♻️  re-rendered {n} daily page(s) with fresh enrichment")
        return
```
新增 helper `_load_cached_summary(date_str)`：从既有持久化处取回当天 summary dict（含 full_list/overview/trends/core_items）。**实现前先 grep 确认 summary 落盘位置**——很可能是 `data/daily_summary_<date>.json` 或嵌在 `docs/daily/summaries.json`/`digest` 缓存。按真实位置实现；若日报 summary 未单独落盘，则改为从 `data/index.json`+`relevant` 重建（复用 `collect_daily_articles`）但**不调用 AI**（overview/trends 用 summaries.json 里已存的文本，缺则留空）。

> 关键约束：`--rerender-only` **绝不**触发 AI 调用（`AI_*` 不依赖）。验证：`grep` 路径确保分支内无 summarizer 调用。

- [ ] **Step 3: 手测 rerender 不调用 AI 且写出富化**

Run:
```bash
python3 generate_daily_pages.py --rerender-only --days 3
grep -c "enrich-badge\|今日文献" docs/daily/2026-06-01.html
```
Expected: 命令秒级完成（无网络/AI）；grep ≥1（该日有富化）。

- [ ] **Step 4: 工作流加重渲染步骤**

`.github/workflows/generate-deep.yml` 在 "Run deep pipeline" 步骤之后、"Commit and push" 之前，插入：
```yaml
      - name: Re-render daily pages with fresh enrichment
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
          AI_PROVIDER: aigw
          AI_MODEL: gpt-5.5
          AI_BASE_URL: ${{ secrets.AI_BASE_URL }}
        run: python generate_daily_pages.py --rerender-only --days 4
```
（env 保留以防 import 期需要，但分支逻辑不调用 AI。）

- [ ] **Step 5: 提交**

```bash
git add generate_daily_pages.py .github/workflows/generate-deep.yml
git commit -m "feat: --rerender-only re-renders daily HTML with fresh enrichment (same-day images)"
```

---

## Task 8: 全量回归 + 前端书签 jsdom + 收尾验证

**Files:**
- Modify: `test_run_deep.py`（去 feed 断言，若有）, `docs/index.html`（导航加收藏提示）
- Test: 全套

- [ ] **Step 1: `test_run_deep.py` 去 feed 相关**

`grep -n "feed\|write_feed" test_run_deep.py`，删除/改写任何断言 `write_feed_json`/`feed.json` 的测试；保留 arxiv_core/aps 富化测试。

- [ ] **Step 2: index 导航加「⭐ 我的收藏」提示**

`docs/index.html` 的 `.nav-links`（约 L116-120）加一项：
```html
                <a href="javascript:void(0)" class="nav-link" onclick="document.querySelector('.bookmark-fab')?.click()">⭐ 我的收藏</a>
```
（FAB 由 bookmarks.js 注入；点击触发其浮层。若 `.bookmark-fab` 选择器名不同，先 `grep -n "fab" docs/bookmarks.js` 用真实类名。）

- [ ] **Step 3: 全量 Python 测试**

Run: `python3 run_tests.py`
Expected: 全 PASS，除 bs4 缺失的已知本地失败（记录数量，确认与改动无关）。

- [ ] **Step 4: 前端 jsdom 书签测试**

Run: `node /tmp/run_fe.js docs/test-bookmarks.html`（若脚本不存在，按 memory `local-test-workflow` 重建 jsdom runner）
Expected: bookmarks.js 在含 `.daily-paper-card[data-bookmark-key]` 的 DOM 注入 ⭐ 且 FAB 浮层正常。

- [ ] **Step 5: 静态自检无残留 Feed 引用**

Run:
```bash
grep -rn "feed\.html\|feed\.js\|feed\.css\|likes\.js\|likes\.css\|write_feed_json\|feed_builder" \
  --include=*.py --include=*.js --include=*.html . | grep -v "docs/daily/20" | grep -v "feed\.xml"
```
Expected: 无输出。

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "test: drop feed assertions; index nav adds bookmarks entry"
```

---

## Self-Review（已执行）

- **Spec 覆盖**：A 删 Feed→Task1/2/8；B 富化单列表→Task3/4/5/6；C 收藏→Task2(index)/Task8(jsdom 验证，复用 bookmarks.js)；D 同日见图→Task7。全覆盖。
- **占位符**：无 TODO/TBD；每个 code step 给出完整代码。Task7 的 `_load_cached_summary` 显式要求"先 grep 真实落盘位置再实现"——这是必要的代码考古，非占位（已给两条 fallback 路径）。
- **类型/命名一致**：`normalize_link`(link_utils)、`load_enrichment`→`enrich_map`、`build_unified_items`(注入 `_tier`/`_enrich`)、`render_unified_item` 读 `_enrich`、`render_meta_chips`(模块级)、`TOPIC_LABELS`、CSS `enrich-badge`/`enrich-details`/`poster-figure`/`daily-deep-elements`/`deep-body` 跨任务一致。
- **风险点**：Task6 删除大段嵌套渲染函数——务必逐个确认无其他引用（`render_focus_item`/`render_group`/`safe_summary_text` 仅 render_daily_html 内部用）。Task7 summary 落盘位置需考古。

## 收尾（计划外但目标要求）

实现全绿后：`git push origin main` → 触发 `Generate Deep Read + Posters + Feed` workflow（其中 daily→run_deep→**rerender** 新链）→ 监控 run 成功 → 拉回验证 `docs/daily/<today>.html` 含 `今日文献` 单列表 + `enrich-badge` + 可展开图。APS 源若不可达则当天无 tier0，但 arxiv tier1 富化照常。
