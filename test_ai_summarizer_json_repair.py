#!/usr/bin/env python3
"""
Deterministic sanity test (no network):
- Verify malformed JSON from model output can be repaired.
"""

from ai_summarizer import AISummarizer


def main() -> int:
    malformed = """```json
{
  "overview": "总览",
  "trends": "热点",
  "summaries": [
    {
      "index": 1,
      "title_zh": "测试标题一",
      "one_sentence_summary": "测试总结一"
    }
    {
      "index": 2,
      "title_zh": "测试标题二",
      "one_sentence_summary": "测试总结二",
    }
  ],
  "highlights": [
    {
      "index": 1,
      "reason": "重点"
    },
  ],
}
```"""

    data = AISummarizer._load_json_lenient(malformed, context="unit-test")
    assert data["overview"] == "总览"
    assert len(data["summaries"]) == 2
    assert data["summaries"][1]["index"] == 2
    assert data["summaries"][1]["title_zh"] == "测试标题二"
    assert data["highlights"][0]["reason"] == "重点"

    print("[OK] ai_summarizer lenient JSON repair sanity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
