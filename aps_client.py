"""APS 全文源 HTTP 客户端（basic-auth 浏览器）。所有 IO 失败均吞掉返回空，不阻塞主流程。"""
import os, re, json, datetime
from urllib.parse import quote
import requests

_DATE_RE = re.compile(r"prefix=APS%2F(\d{4}-\d{2}-\d{2})%2F")

class ApsClient:
    def __init__(self, base=None, user=None, password=None, timeout=40):
        self.base = (base or os.environ.get("APS_HTTP_BASE", "")).rstrip("/")
        self.user = user or os.environ.get("APS_HTTP_USER", "")
        self.password = password or os.environ.get("APS_HTTP_PASS", "")
        self.timeout = timeout

    @property
    def _auth(self):
        return (self.user, self.password) if self.user else None

    def _get(self, path):
        url = path if path.startswith("http") else f"{self.base}{path}"
        return requests.get(url, auth=self._auth, timeout=self.timeout, allow_redirects=True)

    def list_dates(self, window_days=30, today=None):
        try:
            r = self._get("/?prefix=APS%2F")
            found = sorted(set(_DATE_RE.findall(r.text)))
        except Exception as e:
            print(f"⚠️ APS list_dates failed: {e}"); return []
        if not found:
            return []
        today = today or datetime.date.today().isoformat()
        cutoff = (datetime.date.fromisoformat(today) - datetime.timedelta(days=window_days)).isoformat()
        return [d for d in found if d >= cutoff]

    def fetch_metadata(self, date):
        try:
            key = f"APS/{date}/metadata.jsonl"
            r = self._get(f"/download?key={quote(key)}")
            metas = []
            for line in r.content.decode("utf-8", "replace").splitlines():
                line = line.strip()
                if line:
                    try: metas.append(json.loads(line))
                    except Exception: pass
            return metas
        except Exception as e:
            print(f"⚠️ APS fetch_metadata {date} failed: {e}"); return []

    def fetch_markdown(self, meta):
        key = (meta or {}).get("markdown_oss_key") or ""
        if not key:
            return ""
        try:
            r = self._get(f"/download?key={quote(key)}")
            return r.content.decode("utf-8", "replace")
        except Exception as e:
            print(f"⚠️ APS fetch_markdown {key} failed: {e}"); return ""

    def list_images(self, meta):
        prefix = (meta or {}).get("image_oss_prefix") or ""
        if not prefix:
            return []
        m = re.search(r"aps-papers/(.+)$", prefix)
        if not m:
            return []
        oss_path = m.group(1)
        try:
            r = self._get(f"/?prefix={quote(oss_path)}")
            return re.findall(r"key=([^'\"]+\.(?:png|jpg|jpeg))", r.text)
        except Exception as e:
            print(f"⚠️ APS list_images failed: {e}"); return []
