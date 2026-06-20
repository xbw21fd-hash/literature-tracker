"""
Batch relevance analyser for quantum information/many-body/metrology focus.

Design goals:
- High recall: prefer including borderline cases rather than missing relevant papers.
- Batch API calls to keep GitHub Actions runtime reasonable.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from ai_summarizer import build_provider
from focus_filter import is_daily_focus


def _extract_json(text: str) -> Any:
    import re

    m = re.search(r"\{[\s\S]*\}", text or "")
    if not m:
        raise ValueError("No JSON object found")
    return json.loads(m.group())


def batch_analyze_relevance(
    articles: List[Dict[str, Any]],
    *,
    provider_name: str,
    api_key: str,
    model: Optional[str] = None,
    batch_size: int = 16,
) -> List[Dict[str, Any]]:
    """
    Returns a list of analysis dicts aligned with the input order.

    Each result:
      {
        "is_relevant": bool,
        "score": int (0-10),
        "explanation": str (zh),
        "detailed_summary": str (zh)
      }
    """

    provider_name = (provider_name or "").strip().lower() or "gemini"
    api_key = (api_key or "").strip()
    model = (model or "").strip() or None

    if not api_key:
        return [
            {
                "is_relevant": False,
                "score": 0,
                "explanation": "未配置 AI_API_KEY，跳过相关性分析",
                "detailed_summary": "",
            }
            for _ in articles
        ]

    provider = build_provider(provider_name, api_key, model=model)

    results: List[Dict[str, Any]] = []
    for start in range(0, len(articles), batch_size):
        batch = articles[start : start + batch_size]
        prompt = _build_prompt(batch)
        try:
            text = provider.call_api(prompt)
            data = _extract_json(text)
            mapping = _parse_items(data)
        except Exception:
            mapping = {}

        for i in range(1, len(batch) + 1):
            item = mapping.get(i)
            if not item:
                article = batch[i - 1]
                fallback_rel = is_daily_focus(article)
                results.append(
                    {
                        "is_relevant": fallback_rel,
                        "score": 6 if fallback_rel else 0,
                        "explanation": "AI 返回不完整，已按本地量子信息/多体/计量规则回退判定。",
                        "detailed_summary": "",
                    }
                )
                continue
            results.append(item)

    return results


def _build_prompt(batch: List[Dict[str, Any]]) -> str:
    lines = []
    for i, a in enumerate(batch, 1):
        title = (a.get("title") or "").strip()
        journal = (a.get("journal") or "").strip()
        authors = a.get("authors") or []
        if isinstance(authors, list):
            authors_str = ", ".join([str(x) for x in authors[:6]]) + (" 等" if len(authors) > 6 else "")
        else:
            authors_str = str(authors or "")
        abstract = (a.get("abstract") or "").strip()
        abstract = abstract[:600]
        lines.append(f"[{i}] Title: {title}\nJournal: {journal}\nAuthors: {authors_str}\nAbstract: {abstract}\n")

    joined = "\n".join(lines)

    return f"""你是一位研究助理，专注于量子信息/量子多体/量子计量/量子计算方向。

请逐条判断以下论文是否与"量子信息/量子多体/量子计量/量子计算"相关。

高召回要求：
- 宁可多收录，也不要漏掉潜在相关论文。
- 只要论文可能涉及：量子纠错/容错量子计算/量子信道/量子算法/量子电路；量子多体系统/量子相变/张量网络/拓扑序；量子计量/量子传感/量子Fisher信息；量子模拟/冷原子/光晶格；开放量子系统/量子退相干；量子光学/腔QED/电路QED；量子硬件/超导量子比特/离子阱/光子量子比特，都应判为相关。
- 纯临床医学、生物医学、公共卫生、教育、社会科学等判为不相关；纯经典机器学习/材料科学/凝聚态（无量子信息内容）也判为不相关。

输入列表：
{joined}

请严格输出 JSON（不要 markdown，不要多余解释），并且 items 必须覆盖全部输入序号：
{{
  "items": [
    {{
      "index": 1,
      "is_relevant": true,
      "score": 0,
      "explanation": "中文1-2句，说明为何相关/不相关",
      "detailed_summary": "中文3-4句，总结研究对象、方法（量子信息/多体/计量方法）、主要发现与启发"
    }}
  ]
}}

注意：除 is_relevant/score 外，其余字段必须是简体中文。"""


def _parse_items(data: Any) -> Dict[int, Dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        items = data["items"]
    else:
        raise ValueError("Unexpected JSON schema")

    mapping: Dict[int, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            idx = int(item.get("index"))
        except Exception:
            continue
        mapping[idx] = {
            "is_relevant": bool(item.get("is_relevant", False)),
            "score": int(item.get("score", 0) or 0),
            "explanation": str(item.get("explanation", "") or ""),
            "detailed_summary": str(item.get("detailed_summary", "") or ""),
        }
    return mapping
