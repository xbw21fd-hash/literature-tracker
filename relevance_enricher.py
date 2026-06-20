#!/usr/bin/env python3
"""
AI摘要生成器 - 使用免费AI API生成每日文献摘要
支持: Gemini, OpenRouter (OpenAI-compatible)
修复: 解决 AI 在长列表中容易将链接与文章标题搞混的问题
"""

import os
import json
import time
import re
import requests
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from abc import ABC, abstractmethod
from urllib.parse import urlsplit, urlunsplit

try:
    from config import AI_CONFIG as DEFAULT_AI_CONFIG
except ImportError:
    DEFAULT_AI_CONFIG = {}

try:
    from json_repair import repair_json
except ImportError:
    repair_json = None


def _clamp_text(text: str, max_chars: int) -> str:
    if not text:
        return ""
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = 0
    cjk = 0
    for ch in text:
        if ch.isalpha() or '\u4e00' <= ch <= '\u9fff':
            letters += 1
            if '\u4e00' <= ch <= '\u9fff':
                cjk += 1
    return (cjk / letters) if letters else 0.0


def _looks_untranslated_title(candidate: str, english_title: str) -> bool:
    if not candidate:
        return False
    c = candidate.strip()
    if not c:
        return False
    if _cjk_ratio(c) < 0.3:
        return True
    def norm(s): return "".join((s or "").lower().split())[:60]
    if norm(c) == norm(english_title):
        return True
    return False


class AIProvider(ABC):
    @abstractmethod
    def call_api(self, prompt: str) -> str:
        pass


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.max_retries = 3

    def call_api(self, prompt: str) -> str:
        wait_max_seconds = int(os.environ.get("AI_WAIT_MAX_SECONDS", "0") or "0")
        wait_base_seconds = float(os.environ.get("AI_WAIT_BASE_SECONDS", "10") or "10")
        wait_max_sleep_seconds = float(os.environ.get("AI_WAIT_MAX_SLEEP_SECONDS", "300") or "300")

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192,
                "topP": 0.95,
                "topK": 40,
                "responseMimeType": "application/json"
            },
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"}
            ]
        }

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        start = time.monotonic()
        attempt = 0
        last_err: Optional[Exception] = None

        while True:
            attempt += 1
            try:
                response = requests.post(url, headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' not in result or not result['candidates']:
                        raise Exception("Gemini API返回空响应")
                    return result['candidates'][0]['content']['parts'][0]['text']
                if response.status_code in (429, 500, 502, 503, 504):
                    last_err = Exception(f"Gemini API错误 ({response.status_code}): {response.text}")
                else:
                    raise Exception(f"Gemini API错误 ({response.status_code}): {response.text}")
            except Exception as e:
                last_err = e

            elapsed = time.monotonic() - start
            if wait_max_seconds > 0:
                if elapsed >= wait_max_seconds:
                    raise last_err or Exception("Gemini API failed")
            else:
                if attempt >= self.max_retries:
                    raise last_err or Exception("Gemini API failed")

            sleep_s = min(wait_base_seconds * (2 ** max(0, attempt - 1)), wait_max_sleep_seconds)
            time.sleep(min(sleep_s, max(1.0, (wait_max_seconds - elapsed) if wait_max_seconds > 0 else sleep_s)))


class KimiClaudeCodeProvider(AIProvider):
    DEFAULT_BASE_URL = "https://api.kimi.com/coding"
    DEFAULT_MODEL = "kimi-k2-turbo-preview"

    def __init__(self, api_key: str, model: str = None):
        self.api_key = (api_key or "").strip()
        self.model = (
            model
            or os.environ.get("AI_MODEL")
            or os.environ.get("KIMI_MODEL")
            or self.DEFAULT_MODEL
        )
        base = (
            os.environ.get("KIMI_BASE_URL")
            or os.environ.get("AI_BASE_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        if base.endswith("/v1/messages"):
            self.endpoint = base
        elif base.endswith("/v1"):
            self.endpoint = f"{base}/messages"
        else:
            self.endpoint = f"{base}/v1/messages"
        self.timeout = int(os.environ.get("AI_TIMEOUT_SECONDS", "120"))
        self.max_retries = int(os.environ.get("AI_MAX_RETRIES", "3"))

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
            "user-agent": os.environ.get("KIMI_USER_AGENT", "claude-cli/1.0.60 (external, cli)"),
            "x-app": "cli",
            "x-stainless-lang": "js",
            "x-stainless-package-version": "0.60.0",
        }

    def call_api(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Kimi api_key is empty (set KIMI_API_KEY or AI_API_KEY).")

        wait_max_seconds = int(os.environ.get("AI_WAIT_MAX_SECONDS", "0") or "0")
        wait_base_seconds = float(os.environ.get("AI_WAIT_BASE_SECONDS", "10") or "10")
        wait_max_sleep_seconds = float(os.environ.get("AI_WAIT_MAX_SLEEP_SECONDS", "300") or "300")

        system_prompt = (
            "你是一位资深的量子信息/量子多体/量子计量方向研究员，擅长把英文学术文献压缩为"
            "精准、信息密度高、无套话的中文要点；严格按要求输出 JSON。"
        )
        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(os.environ.get("AI_MAX_TOKENS", "8192")),
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }

        start = time.monotonic()
        attempt = 0
        last_err: Optional[Exception] = None

        while True:
            attempt += 1
            response = None
            try:
                response = requests.post(
                    self.endpoint, headers=self._headers(), json=payload, timeout=self.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    blocks = data.get("content") or []
                    text_parts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
                    text = "".join(text_parts).strip()
                    if not text:
                        raise Exception(f"Kimi API 返回空文本: {data}")
                    return text
                if response.status_code in (401, 403):
                    raise Exception(f"Kimi API 鉴权失败 ({response.status_code}): {response.text}")
                if response.status_code in (429, 500, 502, 503, 504):
                    last_err = Exception(f"Kimi API错误 ({response.status_code}): {response.text}")
                else:
                    raise Exception(f"Kimi API错误 ({response.status_code}): {response.text}")
            except Exception as e:
                last_err = e

            elapsed = time.monotonic() - start
            if wait_max_seconds > 0:
                if elapsed >= wait_max_seconds:
                    raise last_err or Exception("Kimi API failed")
            else:
                if attempt >= self.max_retries:
                    raise last_err or Exception("Kimi API failed")

            retry_after = 0.0
            if response is not None:
                try:
                    ra = (response.headers.get("Retry-After") or "").strip()
                    if ra:
                        retry_after = float(ra)
                except Exception:
                    retry_after = 0.0

            sleep_s = min(wait_base_seconds * (2 ** max(0, attempt - 1)), wait_max_sleep_seconds)
            if retry_after > 0:
                sleep_s = max(sleep_s, retry_after)
            if wait_max_seconds > 0:
                remaining = max(0.0, wait_max_seconds - elapsed)
                sleep_s = min(sleep_s, max(1.0, remaining))
            time.sleep(sleep_s)


class OpenRouterProvider(AIProvider):
    def __init__(self, api_key: str, model: str = None):
        self.api_key = (api_key or "").strip()
        self.model = (
            model
            or os.environ.get("AI_MODEL")
            or os.environ.get("OPENROUTER_MODEL")
            or (DEFAULT_AI_CONFIG.get("model") if isinstance(DEFAULT_AI_CONFIG, dict) else None)
            or "gpt-5.4(auto)"
        )
        raw_base_url = (
            os.environ.get("AI_BASE_URL")
            or os.environ.get("OPENROUTER_BASE_URL")
            or (DEFAULT_AI_CONFIG.get("base_url") if isinstance(DEFAULT_AI_CONFIG, dict) else None)
            or "https://supercodex.space/v1"
        )
        self.base_url = normalize_chat_completions_url(raw_base_url)
        self.max_retries = int(os.environ.get("AI_MAX_RETRIES", "3"))
        self.timeout = int(os.environ.get("AI_TIMEOUT_SECONDS", "120"))

    def _headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        def _sanitize(v: Optional[str]) -> str:
            v = (v or "").strip()
            if "\r" in v or "\n" in v:
                return ""
            return v
        http_referer = _sanitize(os.environ.get("OPENROUTER_HTTP_REFERER") or os.environ.get("HTTP_REFERER"))
        x_title = _sanitize(os.environ.get("OPENROUTER_X_TITLE") or os.environ.get("X_TITLE"))
        if http_referer:
            headers["HTTP-Referer"] = http_referer
        if x_title:
            headers["X-Title"] = x_title
        return headers

    def call_api(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OpenRouter api_key is empty (set AI_API_KEY).")

        wait_max_seconds = int(os.environ.get("AI_WAIT_MAX_SECONDS", "0") or "0")
        wait_base_seconds = float(os.environ.get("AI_WAIT_BASE_SECONDS", "10") or "10")
        wait_max_sleep_seconds = float(os.environ.get("AI_WAIT_MAX_SLEEP_SECONDS", "300") or "300")
        json_mode_enabled = (os.environ.get("AI_RESPONSE_JSON", "") or "").strip().lower() in ("1", "true", "yes")

        start = time.monotonic()
        attempt = 0
        last_err: Optional[Exception] = None

        while True:
            attempt += 1
            response = None
            try:
                payload: Dict[str, Any] = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": int(os.environ.get("AI_MAX_TOKENS", "4096")),
                }
                if json_mode_enabled:
                    payload["response_format"] = {"type": "json_object"}

                response = requests.post(
                    self.base_url, headers=self._headers(), json=payload, timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices") or []
                    if not choices:
                        raise Exception("OpenRouter API返回空 choices")
                    msg = (choices[0] or {}).get("message") or {}
                    content = msg.get("content")
                    if not content:
                        raise Exception("OpenRouter API返回空 content")
                    return content

                if (
                    response.status_code == 400
                    and json_mode_enabled
                    and any(
                        token in response.text.lower()
                        for token in ("response_format", "json_object", "structured output", "not support")
                    )
                ):
                    print("⚠️ OpenRouter JSON mode unsupported by current model, retrying without response_format")
                    json_mode_enabled = False
                    attempt -= 1
                    continue

                if response.status_code in (429, 500, 502, 503, 504):
                    last_err = Exception(f"OpenRouter API错误 ({response.status_code}): {response.text}")
                else:
                    raise Exception(f"OpenRouter API错误 ({response.status_code}): {response.text}")
            except Exception as e:
                last_err = e

            elapsed = time.monotonic() - start
            if wait_max_seconds > 0:
                if elapsed >= wait_max_seconds:
                    raise last_err or Exception("OpenRouter API failed")
            else:
                if attempt >= self.max_retries:
                    raise last_err or Exception("OpenRouter API failed")

            retry_after = 0.0
            if response is not None:
                try:
                    ra = (response.headers.get("Retry-After") or "").strip()
                    if ra:
                        retry_after = float(ra)
                except Exception:
                    retry_after = 0.0

            sleep_s = min(wait_base_seconds * (2 ** max(0, attempt - 1)), wait_max_sleep_seconds)
            if retry_after > 0:
                sleep_s = max(sleep_s, retry_after)
            if wait_max_seconds > 0:
                remaining = max(0.0, wait_max_seconds - elapsed)
                sleep_s = min(sleep_s, max(1.0, remaining))
            time.sleep(sleep_s)


def normalize_chat_completions_url(raw_url: Optional[str]) -> str:
    default_url = "https://openrouter.ai/api/v1/chat/completions"
    candidate = (raw_url or "").strip()
    if not candidate:
        return default_url
    parsed = urlsplit(candidate)
    if not parsed.scheme or not parsed.netloc:
        return default_url
    normalized_path = parsed.path.rstrip("/")
    if not normalized_path:
        normalized_path = "/chat/completions"
    elif not (
        normalized_path.endswith("/chat/completions")
        or normalized_path.endswith("/completions")
    ):
        normalized_path = f"{normalized_path}/chat/completions"
    return urlunsplit((parsed.scheme, parsed.netloc, normalized_path, parsed.query, parsed.fragment))


def build_provider(api_provider: str, api_key: str, model: str = None) -> AIProvider:
    name = (api_provider or "").strip().lower()
    if name in ("kimi", "kimi-coding", "moonshot-coding", "kimi-claude"):
        return KimiClaudeCodeProvider(api_key=api_key, model=model)
    if name in ("openrouter", "open-router", "or"):
        return OpenRouterProvider(api_key=api_key, model=model)
    if name in ("aigw", "gpt5", "openai-gateway", "sota"):
        return OpenRouterProvider(api_key=api_key, model=model)
    gemini_model = model if model and "/" not in model else None
    return GeminiProvider(api_key=api_key, model=gemini_model)


class AISummarizer:
    def __init__(self, api_provider: str, api_key: str, model: str = None):
        model = (
            model
            or os.environ.get("AI_MODEL")
            or (DEFAULT_AI_CONFIG.get("model") if isinstance(DEFAULT_AI_CONFIG, dict) else None)
        )
        self.provider = build_provider(api_provider, api_key, model=model)
        self.provider_name = (api_provider or "gemini").strip().lower()

    def generate_daily_summary(self, articles: List[Dict], date: str) -> Dict:
        if not articles:
            return self.fallback_summary(articles, date)

        wait_max_seconds = int(os.environ.get("AI_DAILY_WAIT_MAX_SECONDS") or os.environ.get("AI_WAIT_MAX_SECONDS", "0") or "0")
        wait_base_seconds = float(os.environ.get("AI_DAILY_WAIT_BASE_SECONDS") or os.environ.get("AI_WAIT_BASE_SECONDS", "10") or "10")
        wait_max_sleep_seconds = float(os.environ.get("AI_DAILY_WAIT_MAX_SLEEP_SECONDS") or os.environ.get("AI_WAIT_MAX_SLEEP_SECONDS", "300") or "300")
        no_fallback = (os.environ.get("AI_DAILY_NO_FALLBACK") or os.environ.get("AI_NO_FALLBACK") or "").strip().lower() in ("1", "true", "yes")

        start = time.monotonic()
        attempt = 0
        last_err: Optional[Exception] = None

        while True:
            attempt += 1
            try:
                max_per_call = int(os.environ.get("AI_DAILY_MAX_PER_CALL", "40"))
                if len(articles) <= max_per_call:
                    prompt = self._build_prompt(articles, date)
                    response = self.provider.call_api(prompt)
                    summary = self._parse_response(response, articles, date)
                    if "summaries" not in summary:
                        summary["summaries"] = summary.get("full_list", [])
                    return summary

                chunks = [articles[i:i + max_per_call] for i in range(0, len(articles), max_per_call)]
                merged_full_list: List[Dict] = []
                merged_ml: List[Dict] = []
                merged_ferro: List[Dict] = []

                for chunk in chunks:
                    prompt = self._build_prompt(chunk, date)
                    response = self.provider.call_api(prompt)
                    part = self._parse_response(response, chunk, date)
                    merged_full_list.extend(part.get("full_list", []))
                    merged_ml.extend(part.get("ml_highlights", []))
                    merged_ferro.extend(part.get("ferro_highlights", []))

                def _dedup_by_link(items: List[Dict]) -> List[Dict]:
                    seen: set = set()
                    out: List[Dict] = []
                    for it in items:
                        key = it.get("link") or it.get("title_en")
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append(it)
                    return out

                merged_ml = _dedup_by_link(merged_ml)
                merged_ferro = _dedup_by_link(merged_ferro)
                overview, trends = self._build_overview_trends(articles, date)

                summary = {
                    "date": date,
                    "total": len(articles),
                    "overview": overview,
                    "trends": trends,
                    "full_list": merged_full_list,
                    "ml_highlights": merged_ml[:5],
                    "ferro_highlights": merged_ferro[:5],
                    "generated_by": self.provider_name,
                }
                summary["summaries"] = summary.get("full_list", [])
                return summary

            except Exception as e:
                last_err = e
                print(f"❌ AI 摘要生成失败 (attempt={attempt}): {e}")

                msg_lower = str(e).lower()
                is_fatal = (
                    isinstance(e, ValueError)
                    and ("api_key is empty" in msg_lower or "api key is empty" in msg_lower)
                ) or ("401" in msg_lower) or ("403" in msg_lower)

                if is_fatal:
                    if no_fallback:
                        raise last_err
                    return self.fallback_summary(articles, date)

                elapsed = time.monotonic() - start
                if wait_max_seconds > 0 and elapsed < wait_max_seconds:
                    sleep_s = min(wait_base_seconds * (2 ** max(0, attempt - 1)), wait_max_sleep_seconds)
                    remaining = max(0.0, wait_max_seconds - elapsed)
                    sleep_s = min(sleep_s, max(1.0, remaining))
                    print(f"⏳ 等待 {sleep_s:.0f}s 后重试（已等待 {elapsed:.0f}s / {wait_max_seconds}s）")
                    time.sleep(sleep_s)
                    continue

                if no_fallback:
                    raise last_err
                return self.fallback_summary(articles, date)

    def _build_overview_trends(self, articles: List[Dict], date: str) -> Tuple[str, str]:
        titles = []
        for i, a in enumerate(articles[:200], 1):
            t = a.get("title") or "Unknown Title"
            titles.append(f"[{i}] {t}")
        titles_str = "\n".join(titles)

        prompt = (
            f"你是一位资深量子信息/量子多体/量子计量方向研究员。请基于 {date} 的以下标题列表，"
            "输出今日文献的高信息密度总览与热点分析，面向同行读者。\n\n"
            f"标题列表：\n{titles_str}\n\n"
            "严格要求：\n"
            "- overview 2-3 句，必须包含具体的方法/体系/现象名称（如 surface code、tensor network、"
            "quantum Fisher information、trapped ion、superconducting qubit），"
            "不得使用 '本研究/具有重要意义/取得进展/为…提供新思路' 之类套话。\n"
            "- trends 3-5 句，列出 2-3 个真正的研究热点，每个热点写清 '方向 → 具体做法/现象 → 体现它的典型工作'。\n"
            "- 全中文，不输出任何英文。\n\n"
            "仅输出如下 JSON，禁止任何额外文字：\n"
            '{"overview": "...", "trends": "..."}'
        )

        wait_max_seconds = int(os.environ.get("AI_DAILY_WAIT_MAX_SECONDS") or os.environ.get("AI_WAIT_MAX_SECONDS", "0") or "0")
        wait_base_seconds = float(os.environ.get("AI_DAILY_WAIT_BASE_SECONDS") or os.environ.get("AI_WAIT_BASE_SECONDS", "10") or "10")
        wait_max_sleep_seconds = float(os.environ.get("AI_DAILY_WAIT_MAX_SLEEP_SECONDS") or os.environ.get("AI_WAIT_MAX_SLEEP_SECONDS", "300") or "300")

        start = time.monotonic()
        attempt = 0

        while True:
            attempt += 1
            try:
                response = self.provider.call_api(prompt)
                data = self._load_json_lenient(response, context="overview/trends")
                if not isinstance(data, dict):
                    raise ValueError("overview/trends: response is not an object")
                return data.get("overview", ""), data.get("trends", "")
            except Exception:
                if wait_max_seconds <= 0:
                    return "", ""
                elapsed = time.monotonic() - start
                if elapsed >= wait_max_seconds:
                    return "", ""
                sleep_s = min(wait_base_seconds * (2 ** max(0, attempt - 1)), wait_max_sleep_seconds)
                remaining = max(0.0, wait_max_seconds - elapsed)
                time.sleep(min(sleep_s, max(1.0, remaining)))

    def _build_prompt(self, articles: List[Dict], date: str) -> str:
        articles_text = []
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown Title')
            journal = article.get("journal", "")
            authors = article.get("authors", [])
            if isinstance(authors, list):
                authors = ", ".join([str(a) for a in authors[:6]]) + (" 等" if len(authors) > 6 else "")
            else:
                authors = str(authors or "")
            abstract = (article.get('abstract', ''))[:300]
            articles_text.append(
                f"[{i}] Title: {title}\nJournal: {journal}\nAuthors: {authors}\nAbstract: {abstract}\n"
            )

        articles_str = '\n'.join(articles_text)

        example_block = (
            "示例（仅示范风格，不要直接复制）：\n"
            "输入: [X] Title: Fault-tolerant quantum computation with surface codes\n"
            "      Abstract: We demonstrate logical qubit encoding with below-threshold error rates ...\n"
            "输出: {\n"
            '  "index": X,\n'
            '  "title_zh": "基于表面码的容错量子计算",\n'
            '  "abstract_zh": "实现低于阈值错误率的逻辑量子比特编码，物理错误率 0.1%，"'
            '"逻辑错误率 10^-6，为大规模容错量子计算奠定基础。",\n'
            '  "one_sentence_summary": "首次在实验中实现低于阈值的表面码逻辑量子比特。"\n'
            "}\n"
        )

        return (
            f"你将分析 {date} 的 {len(articles)} 篇学术文献（量子信息 / 量子多体 / 量子计量 / 量子计算方向），"
            "生成一份面向同行研究者的高信息密度中文日报。\n\n"
            f"【文献列表】（格式: [序号] Title / Journal / Authors / Abstract）\n{articles_str}\n\n"
            "【写作硬性要求】\n"
            "1. title_zh：**必须**把英文标题翻成中文，不超过 40 字。只有**化学式/专有名词/缩写**"
            "（如 qubit、surface code、DMRG、VQE、QAOA）可原样保留，其他英文词一律译成中文。"
            "**禁止**把 title_zh 填成英文原标题；若检测到输出的 title_zh 里中文字符占比 < 50%，视为违反要求。\n"
            "2. abstract_zh：用中文把摘要压缩成 ≤120 字的研究要点，必须写出：体系/方法/关键数值或结论，至少一项。"
            "禁止任何套话：'本研究/取得进展/具有重要意义/为…提供新思路' 等一律不允许。\n"
            "3. one_sentence_summary：一句话 ≤40 字，只写最有信息量的那一点（创新点或最强结论），不得空泛。\n"
            "4. 全部用中文；不输出链接；不得编造原文没有的数据。\n"
            "5. summaries 必须覆盖所有输入序号，index 严格一致。\n"
            "6. highlights：仅挑选 ≤3 篇**真正**最突出的工作。"
            "reason ≤25 字，必须落到具体方法/现象/结论，不得写 '重要进展/意义重大' 之流。\n\n"
            f"{example_block}\n"
            "【输出格式】只输出以下 JSON，不要任何额外文字、不要 markdown 代码块标记：\n"
            "{\n"
            '  "overview": "今日文献总览（中文，2-3句，含具体方向与代表性工作）",\n'
            '  "trends": "研究热点分析（中文，3-5句）",\n'
            '  "summaries": [\n'
            '    {"index": 1, "title_zh": "...", "abstract_zh": "...", "one_sentence_summary": "..."},\n'
            f'    ... (共 {len(articles)} 条)\n'
            "  ],\n"
            '  "highlights": [\n'
            '    {"index": <序号>, "reason": "具体亮点（≤25字）"}\n'
            "  ]\n"
            "}\n"
        )

    def _build_missing_summaries_prompt(self, original_articles: List[Dict], missing_indices: List[int], date: str) -> str:
        articles_text = []
        for idx in missing_indices:
            if idx < 1 or idx > len(original_articles):
                print(f"⚠️ 跳过无效索引 {idx} (有效范围: 1-{len(original_articles)})")
                continue
            article = original_articles[idx - 1]
            title = article.get('title', 'Unknown Title')
            journal = article.get("journal", "")
            authors = article.get("authors", [])
            if isinstance(authors, list):
                authors = ", ".join([str(a) for a in authors[:6]]) + (" 等" if len(authors) > 6 else "")
            else:
                authors = str(authors or "")
            abstract = (article.get('abstract', ''))[:300]
            articles_text.append(
                f"[{idx}] Title: {title}\nJournal: {journal}\nAuthors: {authors}\nAbstract: {abstract}\n"
            )

        articles_str = "\n".join(articles_text)
        return f"""你是一位专业的量子信息/量子多体/量子计量文献分析助手。请只补全以下 {date} 缺失的文献条目。

文献列表:
{articles_str}

请严格输出 JSON：
{{
  "summaries": [
    {{
      "index": 1,
      "title_zh": "中文标题（翻译原标题）",
      "abstract_zh": "摘要中文翻译（100字以内）",
      "one_sentence_summary": "一句话中文总结（突出研究亮点）"
    }}
  ]
}}

要求：
1. 只返回上面给出的缺失 index。
2. 每个 index 都必须返回 title_zh、abstract_zh 和 one_sentence_summary，且都使用中文。
3. 不要输出 JSON 以外的任何内容。
"""

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        value = (text or "").strip()
        if not value.startswith("```"):
            return value
        lines = value.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    @classmethod
    def _extract_json_object(cls, text: str) -> str:
        value = cls._strip_code_fence(text)
