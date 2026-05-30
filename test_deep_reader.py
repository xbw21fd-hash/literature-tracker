import deep_reader
from deep_reader import build_deep_prompt, deep_read

def test_build_prompt_fills_placeholders():
    p = build_deep_prompt(title="T", authors="A", year="2026", context="BODY")
    assert "T" in p and "A" in p and "2026" in p and "BODY" in p
    assert "${context}" not in p

def test_build_prompt_truncates_long_context():
    big = "x" * 500000
    p = build_deep_prompt(title="T", authors="A", year="2026", context=big, max_chars=20000)
    assert len(p) < 60000

def test_build_prompt_formats_list_authors():
    p = build_deep_prompt(title="T", authors="['Alice', 'Bob']", year="2026", context="x")
    assert "Alice" in p and "Bob" in p
    assert "['Alice'" not in p  # the python-list literal string must be parsed, not shown raw

def test_deep_read_uses_provider():
    calls = {}
    class FakeProv:
        def call_api(self, prompt):
            calls["prompt"] = prompt
            return "## 第一部分：核心概览\n精读内容"
    out = deep_read({"title": "T", "authors": "['A']", "year": 2026},
                    "# Paper\nfull body", provider=FakeProv())
    assert "精读内容" in out
    assert "full body" in calls["prompt"]

def test_deep_read_swallows_provider_error():
    class Boom:
        def call_api(self, p): raise Exception("api down")
    assert deep_read({"title": "T"}, "body", provider=Boom()) == ""

def test_deep_read_empty_markdown_returns_empty():
    class P:
        def call_api(self, p): return "should not be called"
    assert deep_read({"title": "T"}, "", provider=P()) == ""
