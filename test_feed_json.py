import json, os, tempfile
from feed_builder import build_feed, prune_window, write_feed_json

def test_build_feed_shapes_items():
    aps = [{"source": "APS", "journal": "PRL", "title": "T", "title_zh": "标题",
            "summary": "s", "category": "AI×物理", "doc_id": "d1", "link": "http://x",
            "poster": {"image": "images/posters/d1.webp", "elements": {"研究问题": "q"}},
            "deep_analysis": "## 精读"}]
    arxiv = [{"source": "arxiv", "title": "A", "title_zh": "甲", "summary": "s2",
              "category": "磁性·自旋电子学", "link": "http://y", "image": "images/cards/h.webp"}]
    feed = build_feed(aps, arxiv, date="2026-05-28")
    assert feed["date"] == "2026-05-28"
    aps_item = [i for i in feed["items"] if i["source"] == "APS"][0]
    assert aps_item["poster_elements"]["研究问题"] == "q"
    assert aps_item["image"] == "images/posters/d1.webp"
    assert aps_item["deep_analysis"] == "## 精读"
    assert any(i["source"] == "arxiv" for i in feed["items"])

def test_prune_window_keeps_recent():
    feeds = [{"date": "2026-01-01", "items": []}, {"date": "2026-05-28", "items": []}]
    kept = prune_window(feeds, today="2026-05-30", window_days=60)
    assert len(kept) == 1 and kept[0]["date"] == "2026-05-28"

def test_write_feed_json_flattens_and_stamps_date():
    feeds = [{"date": "2026-05-28", "items": [
        {"source": "APS", "title_zh": "标题", "category": "AI×物理"}]}]
    path = os.path.join(tempfile.mkdtemp(), "feed.json")
    write_feed_json(feeds, path=path, today="2026-05-30", window_days=60)
    data = json.load(open(path, encoding="utf-8"))
    assert data["items"][0]["date"] == "2026-05-28"
    assert data["items"][0]["category"] == "AI×物理"

def test_write_feed_json_drops_out_of_window():
    feeds = [{"date": "2026-01-01", "items": [{"source": "APS", "title_zh": "old"}]},
             {"date": "2026-05-28", "items": [{"source": "APS", "title_zh": "new"}]}]
    path = os.path.join(tempfile.mkdtemp(), "feed.json")
    write_feed_json(feeds, path=path, today="2026-05-30", window_days=60)
    data = json.load(open(path, encoding="utf-8"))
    titles = [i["title_zh"] for i in data["items"]]
    assert "new" in titles and "old" not in titles

def test_normalize_link_doi_to_url():
    from feed_builder import normalize_link
    assert normalize_link("10.1103/766t-tqsy") == "https://doi.org/10.1103/766t-tqsy"
    assert normalize_link("http://arxiv.org/abs/2601.1") == "http://arxiv.org/abs/2601.1"
    assert normalize_link("https://x.com/a") == "https://x.com/a"
    assert normalize_link("") == ""

def test_aps_item_link_normalized_and_daily_url():
    from feed_builder import build_feed
    aps = [{"source": "APS", "title": "T", "title_zh": "标题", "doi": "10.1103/abc",
            "doc_id": "d1", "deep_analysis": "x"}]
    feed = build_feed(aps, [], date="2026-05-28")
    it = feed["items"][0]
    assert it["link"] == "https://doi.org/10.1103/abc"
    assert it["daily_url"] == "daily/2026-05-28.html"

def test_arxiv_item_daily_url():
    from feed_builder import build_feed
    feed = build_feed([], [{"source": "arxiv", "title": "A", "link": "http://arxiv.org/abs/1"}], date="2026-05-27")
    it = feed["items"][0]
    assert it["link"] == "http://arxiv.org/abs/1"
    assert it["daily_url"] == "daily/2026-05-27.html"


def test_arxiv_item_carries_deep_and_elements():
    # C1 regression: tier-2 arXiv records' deep_analysis/poster_elements must survive into feed
    from feed_builder import build_feed
    arxiv = [{"source": "arxiv", "title": "T", "title_zh": "标题", "category": "AI×物理",
              "link": "http://x", "image": "images/posters/ax1.webp",
              "poster_elements": {"研究问题": "q"}, "deep_analysis": "## 摘要级\n创新"}]
    feed = build_feed([], arxiv, date="2026-05-28")
    it = feed["items"][0]
    assert it["deep_analysis"].startswith("## 摘要级")
    assert it["poster_elements"]["研究问题"] == "q"
    assert it["image"] == "images/posters/ax1.webp"
    assert it["enriched"] is True
