"""链接归一化工具：裸 DOI → https://doi.org/...；http(s) 链接原样返回。

单一来源，被 generate_daily_pages 等模块复用（join APS doi 与 arxiv link）。
"""


def normalize_link(link):
    s = (link or "").strip()
    if not s:
        return ""
    if s.startswith("http://") or s.startswith("https://"):
        return s
    return f"https://doi.org/{s}"
