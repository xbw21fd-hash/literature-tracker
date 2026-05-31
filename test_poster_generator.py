import os, tempfile
from unittest import mock
import poster_generator
from poster_generator import extract_elements, build_infographic_prompt, generate_poster

def test_extract_elements_parses_json():
    class P:
        def call_api(self, prompt):
            return ('```json\n{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v",'
                    '"title_zh":"","elements_en":{}}\n```')
    el = extract_elements({"title": "T"}, "body", provider=P())
    assert el["elements"]["创新方法"] == "m" and el["elements"]["应用价值"] == "v"

def test_extract_elements_returns_none_on_bad_json():
    class P:
        def call_api(self, prompt): return "not json at all"
    assert extract_elements({"title": "T"}, "body", provider=P()) is None

def test_extract_elements_none_provider():
    assert extract_elements({"title": "T"}, "body", provider=None) is None

def test_infographic_prompt_is_text_free_memphis():
    p = build_infographic_prompt({"method": "GNN potential"}, "Some Title")
    assert "Memphis" in p
    assert "16:9" in p
    assert "no chinese" in p.lower()

def test_generate_poster_calls_image():
    class P:
        def call_api(self, prompt):
            return ('{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v",'
                    '"title_zh":"","elements_en":{}}')
    d = tempfile.mkdtemp()
    with mock.patch.object(poster_generator, "generate_and_save",
                           side_effect=lambda prompt, out_path, **k: out_path):
        res = generate_poster({"title": "T", "doc_id": "d1"}, "body", provider=P(), out_dir=d)
    assert res["elements"]["创新方法"] == "m"
    assert res["image"].endswith("d1.webp")

def test_generate_poster_none_when_extract_fails():
    class P:
        def call_api(self, prompt): return "garbage"
    assert generate_poster({"title": "T", "doc_id": "d1"}, "body", provider=P()) is None

# --- New tests for elements_en / title_zh / infographic prompt ---

def test_extract_elements_returns_en_and_title_zh():
    class P:
        def call_api(self, prompt):
            return ('{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v",'
                    '"title_zh":"标题中文","elements_en":{"research_question":"RQ","method":"GNN potential",'
                    '"workflow":"train infer","result":"5x faster","value":"materials discovery"}}')
    out = extract_elements({"title": "T"}, "body", provider=P())
    assert out["elements"]["创新方法"] == "m"
    assert out["title_zh"] == "标题中文"
    assert out["elements_en"]["method"] == "GNN potential"

def test_extract_elements_back_compat_without_en():
    class P:
        def call_api(self, prompt):
            return '{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v"}'
    out = extract_elements({"title": "T"}, "body", provider=P())
    assert out["elements"]["研究问题"] == "q"
    assert out["title_zh"] == ""
    assert isinstance(out["elements_en"], dict)

def test_infographic_prompt_is_readable_english_no_chinese():
    p = build_infographic_prompt({"method": "GNN potential", "result": "5x faster"}, "Some Title")
    assert "infographic" in p.lower()
    assert "16:9" in p
    assert "no chinese" in p.lower()
    assert "do not invent" in p.lower() or "schematic" in p.lower()
    assert "GNN potential" in p

def test_generate_poster_returns_title_zh_and_image():
    import tempfile
    from unittest import mock
    class P:
        def call_api(self, prompt):
            return ('{"研究问题":"q","创新方法":"m","工作流程":"f","关键结果":"r","应用价值":"v",'
                    '"title_zh":"标题中文","elements_en":{"method":"GNN"}}')
    with mock.patch.object(poster_generator, "generate_and_save",
                           side_effect=lambda prompt, out_path, **k: out_path):
        res = poster_generator.generate_poster({"title": "T", "doc_id": "d1"}, "body",
                                               provider=P(), out_dir=tempfile.mkdtemp())
    assert res["title_zh"] == "标题中文"
    assert res["image"].endswith("d1.webp")
    assert res["elements"]["创新方法"] == "m"
