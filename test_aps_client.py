import json
from unittest import mock
import aps_client
from aps_client import ApsClient

class FakeResp:
    def __init__(self, text="", content=b"", status=200, headers=None, url=""):
        self.text = text; self.content = content; self.status_code = status
        self.headers = headers or {}; self.url = url
    def raise_for_status(self):
        if self.status_code >= 400: raise Exception(self.status_code)

def test_list_dates_parses_folder_links():
    html = ("<a href='/browse?prefix=APS%2F2026-05-27%2F'>2026-05-27/</a>"
            "<a href='/browse?prefix=APS%2F2026-05-28%2F'>2026-05-28/</a>"
            "<a href='/browse?prefix=APS%2Fbegin%2F'>begin/</a>")
    with mock.patch.object(aps_client.requests, "get", return_value=FakeResp(text=html)):
        c = ApsClient(base="http://h", user="u", password="p")
        dates = c.list_dates(window_days=3650, today="2026-05-30")
    assert "2026-05-28" in dates and "2026-05-27" in dates
    assert "begin" not in dates

def test_fetch_metadata_follows_redirect_jsonl():
    jsonl = ('{"title":"A","journal":"PRL","has_full_text":true,"markdown_oss_key":"k1","doc_id":"d1"}\n'
             '{"title":"B","journal":"PRX","has_full_text":true,"markdown_oss_key":"k2","doc_id":"d2"}\n')
    with mock.patch.object(aps_client.requests, "get", return_value=FakeResp(content=jsonl.encode())):
        c = ApsClient(base="http://h", user="u", password="p")
        metas = c.fetch_metadata("2026-05-28")
    assert len(metas) == 2 and metas[0]["doc_id"] == "d1"

def test_fetch_markdown_returns_text():
    with mock.patch.object(aps_client.requests, "get", return_value=FakeResp(content=b"# Title\n\nbody")):
        c = ApsClient(base="http://h", user="u", password="p")
        md = c.fetch_markdown({"markdown_oss_key": "APS/2026-05-28/markdown/d1/d1.md"})
    assert md.startswith("# Title")

def test_errors_are_swallowed():
    def boom(*a, **k): raise Exception("network down")
    with mock.patch.object(aps_client.requests, "get", side_effect=boom):
        c = ApsClient(base="http://h", user="u", password="p")
        assert c.fetch_metadata("2026-05-28") == []
        assert c.fetch_markdown({"markdown_oss_key": "k"}) == ""
