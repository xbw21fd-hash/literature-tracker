# arxiv 全文苏格拉底深读 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 AI 交叉/核心 arxiv 论文的日报分析从「短摘要解析」升级为「抓全文(HTML 优先/PDF 兜底) + 完整苏格拉底深读」，每篇都有具体分析。

**Architecture:** 新模块 `arxiv_fulltext.py` 负责 ID 解析 + HTML/PDF 抓取 + 全文获取编排（网络层可 monkeypatch 测试）。`run_deep.py` 的 tier-2 富化改为先取全文再 `deep_read()`，带 `analysis_mode`/`ft_attempts` 幂等升级。`generate_daily_pages.py` 加 `md_to_html` 把长苏格拉底文本渲染成结构化 HTML。

**Tech Stack:** Python 3.11（stdlib + requests + pdfminer.six(仅 CI)）。本地测试 `python3 run_tests.py`（stdlib，无 pip）。pdfminer/bs4/feedparser 本地缺包失败属已知，非回归。

**严格测试要求（用户强调）：** 每个纯函数都要有完整正/负/边界用例；网络层一律 monkeypatch 注入，绝不触网；幂等/升级判定要覆盖「全文完成 / 摘要未满 attempts / attempts 封顶 / 旧记录无字段」全分支。

---

## 文件结构

| 文件 | 责任 |
|---|---|
| `arxiv_fulltext.py`（新） | `arxiv_id` 解析、`html_to_text`(stdlib)、`extract_pdf_text`(pdfminer)、`_get_text`/`_get_bytes`(requests, 可 patch)、`fetch_fulltext` 编排 |
| `run_deep.py`（改） | `_tier2_complete`、`_enrich_arxiv_tier2_one`(全文深读)、`process_arxiv_tier2`(分流)、workers env |
| `generate_daily_pages.py`（改） | `md_to_html`、`render_unified_item` deep-body |
| `requirements.txt`（改） | 加 `pdfminer.six` |
| `.github/workflows/generate-deep.yml`（改） | 预算/workers env |
| `test_arxiv_fulltext.py`（新）/`test_run_deep.py`/`test_daily_pages_render.py` | 测试 |

---

## Task 1: `arxiv_fulltext.arxiv_id` — 链接 → arxiv ID

**Files:**
- Create: `arxiv_fulltext.py`
- Test: `test_arxiv_fulltext.py`

- [ ] **Step 1: 写失败测试** `test_arxiv_fulltext.py`

```python
from arxiv_fulltext import arxiv_id


def test_arxiv_id_from_abs():
    assert arxiv_id("https://arxiv.org/abs/2606.04803") == "2606.04803"

def test_arxiv_id_from_pdf_and_html():
    assert arxiv_id("https://arxiv.org/pdf/2606.04803") == "2606.04803"
    assert arxiv_id("https://arxiv.org/html/2606.04803") == "2606.04803"

def test_arxiv_id_strips_version():
    assert arxiv_id("https://arxiv.org/abs/2606.04803v2") == "2606.04803"

def test_arxiv_id_bare_and_5digit():
    assert arxiv_id("2406.04520") == "2406.04520"
    assert arxiv_id("https://arxiv.org/abs/2501.01234") == "2501.01234"

def test_arxiv_id_old_style():
    assert arxiv_id("https://arxiv.org/abs/cond-mat/0703470") == "cond-mat/0703470"

def test_arxiv_id_empty_or_nonarxiv():
    assert arxiv_id("") == ""
    assert arxiv_id(None) == ""
    assert arxiv_id("https://doi.org/10.1103/abc") == ""


if __name__ == "__main__":
    import inspect, sys
    g = dict(globals())
    fns = [v for k, v in g.items() if k.startswith("test_") and inspect.isfunction(v)]
    for f in fns:
        f()
    print(f"[OK] arxiv_fulltext {len(fns)} tests")
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 test_arxiv_fulltext.py`
Expected: FAIL `ModuleNotFoundError: No module named 'arxiv_fulltext'`

- [ ] **Step 3: 实现 `arxiv_id`**（`arxiv_fulltext.py` 起头）

```python
"""arxiv 全文获取：HTML(arxiv/ar5iv) 优先，PDF(pdfminer) 兜底。网络层可 monkeypatch 测试。"""
import re
import io

_NEW_ID = re.compile(r'(\d{4}\.\d{4,5})')
_OLD_ID = re.compile(r'arxiv\.org/(?:abs|pdf|html)/([a-z\-]+/\d{7})', re.I)


def arxiv_id(link):
    """从 arxiv 链接/裸 ID 解析 arxiv 标识；非 arxiv → ""。"""
    s = (link or "").strip()
    if not s:
        return ""
    m = _OLD_ID.search(s)
    if m:
        return m.group(1)
    # 仅当像 arxiv 链接或裸 ID 时才接受新式数字 ID（避免误抓 DOI 里的数字）
    if "arxiv.org" in s or re.fullmatch(r'\d{4}\.\d{4,5}(v\d+)?', s):
        m = _NEW_ID.search(s)
        if m:
            return m.group(1)
    return ""
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 test_arxiv_fulltext.py`
Expected: PASS（输出 `[OK] arxiv_fulltext 6 tests`）

- [ ] **Step 5: 提交**

```bash
git add arxiv_fulltext.py test_arxiv_fulltext.py
git commit -m "feat(arxiv): arxiv_id parses abs/pdf/html/version/bare/old-style links"
```

---

## Task 2: `html_to_text` — stdlib HTML 抽正文

**Files:**
- Modify: `arxiv_fulltext.py`
- Test: `test_arxiv_fulltext.py`（追加）

- [ ] **Step 1: 写失败测试**（追加到 `test_arxiv_fulltext.py`，放在 `if __name__` 之前）

```python
def test_html_to_text_extracts_visible_and_skips_script_style():
    from arxiv_fulltext import html_to_text
    html = ("<html><head><style>.x{color:red}</style>"
            "<script>var a=1;</script></head><body>"
            "<nav>导航不要</nav><p>第一段正文 alpha</p>"
            "<div>第二段 beta</div><footer>页脚不要</footer></body></html>")
    txt = html_to_text(html)
    assert "第一段正文 alpha" in txt
    assert "第二段 beta" in txt
    assert "color:red" not in txt
    assert "var a=1" not in txt
    assert "导航不要" not in txt
    assert "页脚不要" not in txt

def test_html_to_text_empty():
    from arxiv_fulltext import html_to_text
    assert html_to_text("") == ""
    assert html_to_text("<body></body>").strip() == ""
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 test_arxiv_fulltext.py`
Expected: FAIL `ImportError: cannot import name 'html_to_text'`

- [ ] **Step 3: 实现**（追加到 `arxiv_fulltext.py`）

```python
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "header", "footer", "noscript"}

    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            s = data.strip()
            if s:
                self.parts.append(s)


def html_to_text(html):
    p = _TextExtractor()
    try:
        p.feed(html or "")
    except Exception:
        pass
    return re.sub(r'[ \t]+', ' ', " ".join(p.parts)).strip()
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 test_arxiv_fulltext.py`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add arxiv_fulltext.py test_arxiv_fulltext.py
git commit -m "feat(arxiv): html_to_text strips script/style/nav, extracts body text"
```

---

## Task 3: `fetch_fulltext` 编排 + `extract_pdf_text` + 网络层

**Files:**
- Modify: `arxiv_fulltext.py`
- Test: `test_arxiv_fulltext.py`（追加）

- [ ] **Step 1: 写失败测试**（追加，覆盖 HTML 命中 / HTML 太短落 PDF / 全失败 / min_chars 阈值）

```python
def test_fetch_fulltext_html_hit(monkeypatch=None):
    import arxiv_fulltext as af
    long_body = "正文内容 " * 1000  # >4000 chars
    af._get_text = lambda url: f"<body><p>{long_body}</p></body>" if "html" in url else None
    af._get_bytes = lambda url: (_ for _ in ()).throw(AssertionError("PDF must not be fetched when HTML suffices"))
    text, mode = af.fetch_fulltext("https://arxiv.org/abs/2406.04520")
    assert mode == "html"
    assert "正文内容" in text

def test_fetch_fulltext_html_too_short_falls_to_pdf():
    import arxiv_fulltext as af
    af._get_text = lambda url: "<body><p>太短的摘要占位</p></body>"  # < min_chars
    af._get_bytes = lambda url: b"%PDF-FAKE"
    af.extract_pdf_text = lambda b: "PDF 提取的全文 " * 1000  # >4000
    text, mode = af.fetch_fulltext("https://arxiv.org/abs/2606.04803")
    assert mode == "pdf"
    assert "PDF 提取的全文" in text

def test_fetch_fulltext_all_fail_returns_empty():
    import arxiv_fulltext as af
    af._get_text = lambda url: None
    af._get_bytes = lambda url: None
    assert af.fetch_fulltext("https://arxiv.org/abs/2606.04803") == ("", "")

def test_fetch_fulltext_truncates_to_max_chars():
    import arxiv_fulltext as af
    af._get_text = lambda url: "<body><p>" + ("a" * 100000) + "</p></body>"
    text, mode = af.fetch_fulltext("https://arxiv.org/abs/2406.04520", max_chars=5000)
    assert mode == "html" and len(text) <= 5000

def test_fetch_fulltext_non_arxiv_returns_empty():
    import arxiv_fulltext as af
    assert af.fetch_fulltext("https://doi.org/10.1/x") == ("", "")
```

> 注：测试直接替换模块级 `af._get_text`/`af._get_bytes`/`af.extract_pdf_text`。实现里 `fetch_fulltext` **必须通过模块全局名引用**这三者（即 `_get_text(url)` 而非 import 局部别名），否则 monkeypatch 不生效。

- [ ] **Step 2: 运行确认失败**

Run: `python3 test_arxiv_fulltext.py`
Expected: FAIL `ImportError: cannot import name 'fetch_fulltext'`

- [ ] **Step 3: 实现**（追加到 `arxiv_fulltext.py`）

```python
_UA = "literature-tracker/1.0 (+https://github.com/Hongyu-yu/literature-tracker)"
MIN_FULLTEXT_CHARS = 4000


def _get_text(url):
    """GET → 文本；失败 → None。可被测试 monkeypatch。"""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=30, allow_redirects=True)
        if r.status_code == 200 and r.text:
            return r.text
    except Exception as e:
        print(f"⚠️ arxiv html GET failed {url}: {e}")
    return None


def _get_bytes(url):
    """GET → bytes；失败 → None。可被测试 monkeypatch。"""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": _UA}, timeout=45, allow_redirects=True)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception as e:
        print(f"⚠️ arxiv pdf GET failed {url}: {e}")
    return None


def extract_pdf_text(pdf_bytes):
    """pdfminer.six 提取 PDF 文本；缺包/失败 → ""。可被测试 monkeypatch。"""
    if not pdf_bytes:
        return ""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception as e:
        print(f"⚠️ pdf extract failed: {e}")
        return ""


def fetch_fulltext(link, max_chars=40000, min_chars=MIN_FULLTEXT_CHARS):
    """返回 (text, mode)；mode ∈ {"html","pdf",""}。失败/非 arxiv → ("","")。"""
    aid = arxiv_id(link)
    if not aid:
        return ("", "")
    for url in (f"https://arxiv.org/html/{aid}", f"https://ar5iv.org/abs/{aid}"):
        html = _get_text(url)
        if html:
            txt = html_to_text(html)
            if len(txt) >= min_chars:
                return (txt[:max_chars], "html")
    pdf = _get_bytes(f"https://arxiv.org/pdf/{aid}")
    if pdf:
        txt = extract_pdf_text(pdf)
        if len(txt) >= min_chars:
            return (txt[:max_chars], "pdf")
    return ("", "")
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 test_arxiv_fulltext.py`
Expected: PASS（全部 test_* 通过）

- [ ] **Step 5: 提交**

```bash
git add arxiv_fulltext.py test_arxiv_fulltext.py
git commit -m "feat(arxiv): fetch_fulltext HTML-first + PDF fallback with min-length gate"
```

---

## Task 4: `run_deep._tier2_complete` — 幂等/升级判定

**Files:**
- Modify: `run_deep.py`（新增函数，置于 `_deep_complete_abstract` 之后）
- Test: `test_run_deep.py`（追加）

- [ ] **Step 1: 写失败测试**（追加到 `test_run_deep.py`）

```python
def test_tier2_complete_fulltext_done():
    import run_deep
    rec = {"deep_analysis": "## 深析\n第五部分：创新评估 " + "x" * 3500,
           "analysis_mode": "html", "ft_attempts": 1}
    assert run_deep._tier2_complete(rec) is True

def test_tier2_complete_pdf_done():
    import run_deep
    rec = {"deep_analysis": "创新评估 " + "y" * 3500, "analysis_mode": "pdf", "ft_attempts": 1}
    assert run_deep._tier2_complete(rec) is True

def test_tier2_complete_abstract_not_done_until_attempts_cap():
    import run_deep
    short = "## 概览\n创新性判断：" + "z" * 200  # 有"创新", >120, <3000
    assert run_deep._tier2_complete({"deep_analysis": short, "analysis_mode": "abstract", "ft_attempts": 1}) is False
    assert run_deep._tier2_complete({"deep_analysis": short, "analysis_mode": "abstract", "ft_attempts": 3}) is True

def test_tier2_complete_legacy_record_not_done():
    # 旧缓存：无 analysis_mode / 无 ft_attempts → 待升级，不算完成
    import run_deep
    legacy = {"deep_analysis": "## 概览\n创新性判断：" + "z" * 200}
    assert run_deep._tier2_complete(legacy) is False

def test_tier2_complete_empty_or_none():
    import run_deep
    assert run_deep._tier2_complete(None) is False
    assert run_deep._tier2_complete({"deep_analysis": ""}) is False

def test_tier2_complete_fulltext_too_short_not_done():
    # 全文模式但正文 <3000（截断/失败）→ 未完成，继续重试（直到 attempts 封顶）
    import run_deep
    rec = {"deep_analysis": "创新 " + "x" * 100, "analysis_mode": "html", "ft_attempts": 1}
    assert run_deep._tier2_complete(rec) is False
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_run_deep.py -k tier2_complete -v`（或 `python3 run_tests.py`）
Expected: FAIL `module 'run_deep' has no attribute '_tier2_complete'`

- [ ] **Step 3: 实现**（`run_deep.py`，紧接 `_deep_complete_abstract` 之后）

```python
def _tier2_complete(rec):
    """tier-2 富化完成判定（支持全文升级 + attempts 封顶防无限重处理）。
    - 全文模式(html/pdf) 且含"创新" 且 ≥3000 字 → 完成。
    - 否则继续尝试升级全文；attempts≥3 且含"创新" 且 ≥120 字 → 接受(摘要)定稿。
    - 旧缓存(无 mode/attempts) → 未完成(待升级)。"""
    if not rec:
        return False
    text = rec.get("deep_analysis") or ""
    if not text:
        return False
    attempts = int(rec.get("ft_attempts") or 0)
    mode = rec.get("analysis_mode") or "abstract"
    if mode in ("html", "pdf") and ("创新" in text) and len(text) >= 3000:
        return True
    if attempts >= 3 and ("创新" in text) and len(text) >= 120:
        return True
    return False
```

- [ ] **Step 4: 运行确认通过**

Run: `python3 -m pytest test_run_deep.py -k tier2_complete -v`
Expected: PASS（6 个）

- [ ] **Step 5: 提交**

```bash
git add run_deep.py test_run_deep.py
git commit -m "feat(deep): _tier2_complete idempotency with full-text upgrade + attempt cap"
```

---

## Task 5: `_enrich_arxiv_tier2_one` 改用全文深读 + `process_arxiv_tier2` 分流

**Files:**
- Modify: `run_deep.py`（`_enrich_arxiv_tier2_one`、`process_arxiv_tier2` 分流行）
- Test: `test_run_deep.py`（追加 + 改既有 tier2 测试）

- [ ] **Step 1: 写失败测试**（追加到 `test_run_deep.py`）

```python
def test_enrich_tier2_uses_fulltext_deepread_when_available():
    import run_deep, arxiv_fulltext, tempfile
    from unittest import mock
    cand = {"title": "ML for magnet", "abstract": "abs", "link": "https://arxiv.org/abs/2406.04520",
            "category": "AI×物理"}
    class P:
        def call_api(self, p):
            # poster JSON prompt vs deep-read prompt
            if ("研究问题" in p) or ("JSON" in p):
                return '{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v","title_zh":"标题"}'
            return "## 全文苏格拉底\n第五部分：创新评估 " + "z" * 3500
    with mock.patch.object(arxiv_fulltext, "fetch_fulltext", return_value=("FULLTEXT BODY " * 500, "html")), \
         mock.patch.object(run_deep, "generate_and_save", side_effect=lambda prompt, out_path, **k: out_path):
        rec = run_deep._enrich_arxiv_tier2_one(cand, P(), tempfile.mkdtemp())
    assert rec["analysis_mode"] == "html"
    assert "创新评估" in rec["deep_analysis"] and len(rec["deep_analysis"]) >= 3000
    assert rec["ft_attempts"] == 1
    assert run_deep._tier2_complete(rec) is True

def test_enrich_tier2_falls_back_to_abstract_and_increments_attempts():
    import run_deep, arxiv_fulltext, tempfile
    from unittest import mock
    cand = {"title": "P", "abstract": "neural network spin", "link": "https://arxiv.org/abs/2606.99999",
            "category": "AI×物理"}
    class P:
        def call_api(self, p):
            if ("研究问题" in p) or ("JSON" in p):
                return '{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v"}'
            return "## 摘要级\n创新性判断 " + "z" * 200
    cached = {"ft_attempts": 1}  # 此前已尝试 1 次
    with mock.patch.object(arxiv_fulltext, "fetch_fulltext", return_value=("", "")), \
         mock.patch.object(run_deep, "generate_and_save", side_effect=lambda prompt, out_path, **k: out_path):
        rec = run_deep._enrich_arxiv_tier2_one(cand, P(), tempfile.mkdtemp(), cached=cached)
    assert rec["analysis_mode"] == "abstract"
    assert rec["ft_attempts"] == 2

def test_enrich_tier2_returns_cached_when_complete():
    import run_deep, arxiv_fulltext
    from unittest import mock
    done = {"deep_analysis": "创新评估 " + "x" * 3500, "analysis_mode": "html", "ft_attempts": 1,
            "poster": {"image": "p.webp"}}
    with mock.patch.object(arxiv_fulltext, "fetch_fulltext",
                           side_effect=AssertionError("must not refetch a complete record")):
        rec = run_deep._enrich_arxiv_tier2_one({"link": "https://arxiv.org/abs/2406.04520"},
                                               provider=None, out_dir="x", cached=done)
    assert rec is done
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_run_deep.py -k "enrich_tier2" -v`
Expected: FAIL（旧 `_enrich_arxiv_tier2_one` 无 `analysis_mode`/`ft_attempts`，且仍调 abstract_read）

- [ ] **Step 3: 实现**（替换 `run_deep.py` 的 `_enrich_arxiv_tier2_one` 整函数）

```python
def _enrich_arxiv_tier2_one(cand, provider, out_dir, cached=None):
    if cached and _tier2_complete(cached):
        return cached
    import hashlib
    from arxiv_fulltext import fetch_fulltext
    rec = dict(cand)
    rec["source"] = "arxiv"
    rec["category"] = cand.get("category") or classify(cand, provider=provider)
    doc_id = "ax" + hashlib.sha1((cand.get("link") or cand.get("title", "")).encode("utf-8")).hexdigest()[:14]
    meta = {"title": cand.get("title", ""), "authors": cand.get("authors"),
            "year": cand.get("year"), "doc_id": doc_id}
    fulltext, mode = fetch_fulltext(cand.get("link") or "")
    prev_attempts = int((cached or {}).get("ft_attempts") or 0)
    if fulltext:
        rec["deep_analysis"] = deep_read(meta, fulltext, provider=provider)
        rec["analysis_mode"] = mode
        poster_src = fulltext
    else:
        abs_txt = cand.get("abstract") or cand.get("summary") or ""
        rec["deep_analysis"] = abstract_read(cand, abs_txt, provider=provider) if abs_txt else ""
        rec["analysis_mode"] = "abstract"
        poster_src = abs_txt
    rec["ft_attempts"] = prev_attempts + 1
    poster = (cached or {}).get("poster") or (
        generate_poster(meta, poster_src, provider=provider, out_dir=out_dir) if poster_src else None)
    rec["poster"] = poster
    rec["image"] = (poster or {}).get("image")
    rec["poster_elements"] = (poster or {}).get("elements")
    if poster and poster.get("title_zh") and not rec.get("title_zh"):
        rec["title_zh"] = poster["title_zh"]
    return rec
```

- [ ] **Step 4: `process_arxiv_tier2` 分流改用 `_tier2_complete`**

在 `run_deep.py` 的 `process_arxiv_tier2` 内，把：
```python
        (cached if (prev and _deep_complete_abstract(prev.get("deep_analysis"))) else fresh).append((c, prev))
```
改为：
```python
        (cached if (prev and _tier2_complete(prev)) else fresh).append((c, prev))
```

- [ ] **Step 5: 修既有 tier2 回归测试**

既有 `test_process_arxiv_tier2_enriches_and_budgets` 与 `test_tier2_short_abstract_analysis_is_complete_not_reprocessed` 依赖旧 abstract 行为。前者：provider 现在会被 `fetch_fulltext` 先调用——需 monkeypatch `fetch_fulltext` 返回 `("","")` 使其走 abstract 路径，断言不变（仍 enrich+budget）。后者：旧语义「短摘要即完成」已被 `_tier2_complete` 取代为「attempts≥3 才定稿」——改其 cache 记录为 `{"deep_analysis": short, "analysis_mode":"abstract", "ft_attempts":3, "poster":{"image":"x.webp"}}` 使其判为完成、不重处理。在两个测试体首部加：
```python
    import arxiv_fulltext
    from unittest import mock
    # （test_process_arxiv_tier2_enriches_and_budgets 内，with 块加一层）
    with mock.patch.object(arxiv_fulltext, "fetch_fulltext", return_value=("", "")), \
         mock.patch.object(run_deep, "generate_and_save", side_effect=lambda prompt, out_path, **k: out_path):
        out, used = run_deep.process_arxiv_tier2(...)
```
对 `test_tier2_short_abstract_analysis_is_complete_not_reprocessed`：把其 `cache` 的值改为带 `"analysis_mode":"abstract","ft_attempts":3`，并把断言保留 `used == 0`。

- [ ] **Step 6: 运行确认通过**

Run: `python3 run_tests.py 2>&1 | grep -E "passed|failed"`
Expected: 新增 enrich/tier2_complete 测试 PASS；既有 tier2 测试改写后 PASS；无新回归（bs4/feedparser/pdfminer 本地缺包失败属已知）。

- [ ] **Step 7: 提交**

```bash
git add run_deep.py test_run_deep.py
git commit -m "feat(deep): tier-2 enrich fetches full text + Socratic deep_read; idempotent upgrade"
```

---

## Task 6: `md_to_html` + render deep-body 结构化

**Files:**
- Modify: `generate_daily_pages.py`（新增 `md_to_html`；`render_unified_item` deep-body；去 `.deep-body` pre-wrap）
- Test: `test_daily_pages_render.py`（追加）

- [ ] **Step 1: 写失败测试**（追加到 `test_daily_pages_render.py`）

```python
def test_md_to_html_headers_bold_lists_and_escapes():
    from generate_daily_pages import md_to_html
    md = ("## 第一部分：核心概览\n"
          "这是 **关键** 贡献。\n"
          "- 要点一\n- 要点二\n"
          "### 小节\n普通段落 <script>alert(1)</script>")
    html = md_to_html(md)
    assert "<h2" in html and "第一部分：核心概览" in html
    assert "<h3" in html and "小节" in html
    assert "<strong>关键</strong>" in html
    assert "<li>要点一</li>" in html and "<li>要点二</li>" in html
    # 注入转义：原始 <script> 不得出现，应被转义
    assert "<script>alert(1)" not in html
    assert "&lt;script&gt;" in html

def test_md_to_html_empty():
    from generate_daily_pages import md_to_html
    assert md_to_html("") == ""
    assert md_to_html(None) == ""

def test_render_unified_item_deep_body_is_structured_html():
    from generate_daily_pages import render_unified_item
    item = {"title_en": "E", "title_zh": "标题", "summary": "亮点", "link": "http://x",
            "journal": "arXiv", "_tier": 1,
            "_enrich": {"deep_analysis": "## 核心概览\n**粗体**要点", "image": "images/posters/x.webp",
                        "elements": {"研究问题": "q"}, "category": "AI×物理", "title_zh": "标题"}}
    html = render_unified_item(item, 1)
    assert "<h2" in html and "<strong>粗体</strong>" in html
    assert "## 核心概览" not in html  # 不再字面输出 markdown 标记
```

- [ ] **Step 2: 运行确认失败**

Run: `python3 -m pytest test_daily_pages_render.py -k "md_to_html or deep_body" -v`
Expected: FAIL `cannot import name 'md_to_html'`

- [ ] **Step 3: 实现 `md_to_html`**（`generate_daily_pages.py`，置于 `render_unified_item` 之前）

```python
def md_to_html(text):
    """把苏格拉底深析的轻量 markdown 渲染成安全 HTML。
    支持 #/##/### 标题、**粗体**、- / 数字. 列表、空行分段；
    先对每行 safe_text 转义，再套白名单标签，杜绝注入。"""
    if not text:
        return ""
    import re as _re
    lines = str(text).split("\n")
    out = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def inline(s):
        s = safe_text(s)  # 先转义
        s = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)  # 在转义后的文本上加粗
        return s

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_list()
            continue
        m = _re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            close_list()
            level = len(m.group(1)) + 1  # # → h2, ## → h3, ### → h4
            level = min(level, 4)
            out.append(f"<h{level} class='deep-h'>{inline(m.group(2))}</h{level}>")
            continue
        m = _re.match(r'^\s*(?:[-*]|\d+\.)\s+(.*)$', line)
        if m:
            if not in_list:
                out.append("<ul class='deep-ul'>")
                in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            continue
        close_list()
        out.append(f"<p>{inline(line)}</p>")
    close_list()
    return "".join(out)
```

- [ ] **Step 4: `render_unified_item` 用 `md_to_html` 渲染 deep-body**

在 `generate_daily_pages.py` 的 `render_unified_item` 内，把：
```python
        deep = safe_text(en.get("deep_analysis") or "")
        deep_html = f'<div class="deep-body">{deep}</div>' if deep else ""
```
改为：
```python
        deep = en.get("deep_analysis") or ""
        deep_html = f'<div class="deep-body">{md_to_html(deep)}</div>' if deep else ""
```

- [ ] **Step 5: 去掉 `.deep-body` 的 pre-wrap（现在是结构化 HTML）**

在内联 `<style>` 找到：
```python
    .deep-body{{white-space:pre-wrap;font-size:14px;line-height:1.6;}}
```
改为：
```python
    .deep-body{{font-size:14px;line-height:1.7;}}
    .deep-body .deep-h{{font-size:15px;margin:10px 0 4px;color:#1456b8;}}
    .deep-body .deep-ul{{margin:4px 0 4px 18px;}} .deep-body p{{margin:6px 0;}}
```

- [ ] **Step 6: 运行确认通过**

Run: `python3 -m pytest test_daily_pages_render.py -k "md_to_html or deep_body or render_unified" -v`
Expected: PASS。再 `python3 run_tests.py` 确认 `test_daily_pages_render.py` 全过、无回归。

- [ ] **Step 7: 提交**

```bash
git add generate_daily_pages.py test_daily_pages_render.py
git commit -m "feat(daily): md_to_html renders long Socratic analysis as structured HTML"
```

---

## Task 7: 依赖 + CI 预算/workers

**Files:**
- Modify: `requirements.txt`, `.github/workflows/generate-deep.yml`

- [ ] **Step 1: requirements 加 pdfminer.six**

`requirements.txt` 末尾加一行：
```
pdfminer.six>=20221105
```

- [ ] **Step 2: 验证 run_deep 仍能 import（pdfminer 仅在 extract_pdf_text 内惰性 import）**

Run: `python3 -c "import run_deep, arxiv_fulltext; print('import OK')"`
Expected: `import OK`（本地无 pdfminer 也不应在 import 期报错——pdfminer 仅在 `extract_pdf_text` 函数体内 import）

- [ ] **Step 3: generate-deep.yml run_deep 步骤加预算/workers env**

在 `.github/workflows/generate-deep.yml` 的 "Run deep pipeline" 步骤 `env:` 块内（`AI_MAX_RETRIES` 同级）加：
```yaml
          DEEP_MAX_NEW_PER_RUN: "24"
          DEEP_WORKERS: "6"
```

- [ ] **Step 4: 确认 run_deep 读取这两个 env**

`grep -n "DEEP_MAX_NEW_PER_RUN\|DEEP_WORKERS" run_deep.py` 应已存在（`budget = int(os.environ.get("DEEP_MAX_NEW_PER_RUN","14"))`、`workers = int(os.environ.get("DEEP_WORKERS","5"))`）。若 workers 默认仍是硬编码 5 且未读 env，则改为：
```python
    workers = int(os.environ.get("DEEP_WORKERS", "6"))
```

- [ ] **Step 5: YAML 校验 + 提交**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/generate-deep.yml')); print('yaml OK')"`
Expected: `yaml OK`

```bash
git add requirements.txt .github/workflows/generate-deep.yml run_deep.py
git commit -m "chore(ci): add pdfminer.six; bump deep budget=24 workers=6 for full-text reads"
```

---

## Task 8: 全量回归 + 端到端冒烟

**Files:** 测试/验证（不改实现，除非发现缺陷）

- [ ] **Step 1: 全量本地测试**

Run: `python3 run_tests.py 2>&1 | grep -E "passed|failed"`
Expected: 全 PASS，除 bs4/feedparser/pdfminer 本地缺包导致的已知 import 失败（记录数量，确认与本次改动无关）。

- [ ] **Step 2: arxiv_fulltext 离线冒烟（无网，注入式）**

Run:
```bash
python3 - <<'PY'
import arxiv_fulltext as af
af._get_text = lambda u: "<body><p>" + ("正文 "*1000) + "</p></body>" if "html" in u else None
af._get_bytes = lambda u: None
t, m = af.fetch_fulltext("https://arxiv.org/abs/2406.04520")
print("mode", m, "len", len(t), "ok", m=="html" and len(t)>4000)
PY
```
Expected: `mode html len ... ok True`

- [ ] **Step 3: 渲染冒烟——长苏格拉底深析渲染为结构化 HTML**

Run:
```bash
python3 - <<'PY'
from generate_daily_pages import render_unified_item
deep = "## 第一部分：核心概览\n**关键**贡献。\n- 要点A\n- 要点B\n### 第五部分：创新评估\n相对前人首次实现。"
item = {"title_en":"E","title_zh":"测试标题","summary":"亮点","link":"http://x","journal":"arXiv","_tier":1,
        "_enrich":{"deep_analysis":deep,"image":"images/posters/x.webp","elements":{"研究问题":"q"},
                   "category":"AI×物理","title_zh":"测试标题"}}
h = render_unified_item(item,1)
print("h2:", "<h2" in h, "| strong:", "<strong>关键</strong>" in h, "| li:", "<li>要点A</li>" in h,
      "| no literal ##:", "## 第一部分" not in h)
PY
```
Expected: 全部 True。

- [ ] **Step 4: 静态自检——run_deep 不在 import 期依赖 pdfminer/网络**

Run: `python3 -c "import run_deep, arxiv_fulltext, generate_daily_pages; print('all import OK')"`
Expected: `all import OK`

- [ ] **Step 5: 提交（若 step 有修正）**

```bash
git add -A
git commit -m "test: full regression + offline smoke for arxiv full-text Socratic" --allow-empty
```

---

## Self-Review（已执行）

- **Spec 覆盖**：WS1 全文源→Task1/2/3；WS2 接线→Task4/5；依赖/CI→Task7；md 渲染→Task6；测试→每任务 + Task8。全覆盖。
- **占位符**：无 TODO/TBD；每个 code step 给出完整代码。Task5 step5 明确改两个既有测试的具体做法（非"类似处理"）。
- **类型/命名一致**：`arxiv_id`/`html_to_text`/`extract_pdf_text`/`_get_text`/`_get_bytes`/`fetch_fulltext`(返回 `(text,mode)`)、`_tier2_complete(rec)`、`analysis_mode`∈{html,pdf,abstract}、`ft_attempts`、`md_to_html` 跨任务一致。`fetch_fulltext` 完整性阈值 3000 与 `_tier2_complete` 一致；min_chars 4000 与 spec 一致。
- **测试严格性（用户强调）**：每个纯函数含正/负/边界；网络全 monkeypatch；`_tier2_complete` 覆盖 全文完成/摘要未满/attempts 封顶/旧记录/空 五分支；`md_to_html` 含注入转义用例。
- **风险**：Task5 改既有两个 tier2 测试——务必按 step5 精确改，否则误判回归。pdfminer 本地不可测——Task8 step1 明确将其 import 失败归入已知项。

## 收尾（计划外但需做）

实现全绿后：push → 触发 generate-deep（budget=24）→ 监控成功 → 拉回验证 `arxiv_core_<date>.json` 出现 `analysis_mode:"pdf"`(或 html) + `deep_analysis`≥3000 含「第五部分：创新评估」→ 线上日报 AI 交叉条目展开见结构化全文苏格拉底深析。旧摘要版随后续轮升级。
