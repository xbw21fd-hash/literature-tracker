"""
配置文件 - RSS文献追踪系统
"""

# RSS订阅源列表
RSS_FEEDS = [
    # 通用顶刊
    "https://www.nature.com/nature.rss",
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science",
    "https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv",
    "https://www.pnas.org/rss/Physics.xml",
    # APS
    "http://feeds.aps.org/rss/recent/prl.xml",
    "http://feeds.aps.org/rss/recent/prx.xml",
    "http://feeds.aps.org/rss/recent/rmp.xml",
    "http://feeds.aps.org/rss/recent/pra.xml",
    "http://feeds.aps.org/rss/recent/prb.xml",
    "http://feeds.aps.org/rss/recent/prresearch.xml",
    # 量子信息核心期刊
    "http://feeds.aps.org/rss/recent/prxquantum.xml",
    "https://quantum-journal.org/rss/",
    "https://www.nature.com/npjqi.rss",
    "https://iopscience.iop.org/journal/rss/2058-9565",
    # arXiv
    "https://rss.arxiv.org/rss/quant-ph",
    "https://rss.arxiv.org/rss/cond-mat",
    "https://rss.arxiv.org/rss/cond-mat.quant-gas",
    "https://rss.arxiv.org/rss/cs.IT",
]

# 多用户关键词配置
# 每个用户可以定义自己的关键词列表，用于在网页上筛选相关文献
USER_KEYWORDS = {
    "我的订阅": [
        "quantum information",
        "quantum error correct",
        "quantum entanglement",
        "quantum cryptograph",
        "quantum communication",
        "quantum teleport",
        "quantum many-body",
        "many-body",
        "quantum phase transition",
        "topological",
        "tensor network",
        "quantum simulation",
        "quantum metrology",
        "quantum sensing",
        "quantum Fisher",
        "Heisenberg limit",
        "quantum advantage",
        "Preskill",
        "Sisi Zhou",
        "Senrui Chen",
        "Hsin-Yuan Huang",
    ],
}

KEYWORDS = USER_KEYWORDS.get("我的订阅", [])

import os

# 邮件配置
# 优先从本地配置文件读取
_local_email_config = {}
try:
    from config.local import EMAIL_CONFIG as LOCAL_EMAIL_CONFIG
    _local_email_config = LOCAL_EMAIL_CONFIG
except ImportError:
    pass

EMAIL_CONFIG = {
    "recipient": "594836947@qq.com",
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender_email": _local_email_config.get("sender_email") or os.environ.get("EMAIL_SENDER", ""),  # 优先从config.local.py读取
    "sender_password": _local_email_config.get("sender_password") or os.environ.get("EMAIL_PASSWORD", ""),  # 优先从config.local.py读取
    "mode": "digest",  # 邮件模式: "full" 完整版（含摘要）, "digest" 摘要版（仅标题列表）
}

# 微信推送配置（Server酱）
# 优先从本地配置文件读取
_local_wechat_config = {}
try:
    from config.local import WECHAT_CONFIG as LOCAL_WECHAT_CONFIG
    _local_wechat_config = LOCAL_WECHAT_CONFIG
except ImportError:
    pass

WECHAT_CONFIG = {
    "enabled": _local_wechat_config.get("enabled", False),  # 是否启用微信推送
    "sendkey": _local_wechat_config.get("sendkey") or os.environ.get("SERVERCHAN_KEY", ""),  # Server酱SendKey，优先从config.local.py读取
}

# AI摘要配置
# 优先从本地配置文件读取，然后从环境变量读取
_local_ai_config = {}
try:
    from config.local import AI_CONFIG as LOCAL_AI_CONFIG
    _local_ai_config = LOCAL_AI_CONFIG
except ImportError:
    pass

AI_CONFIG = {
    "enabled": True,
    # provider 可选: aigw（默认，OpenAI-compatible gateway）、kimi、gemini、openrouter
    # Fallback / 回退 Kimi 配置: 将下行改为 "kimi" 即可切回
    # "provider": _local_ai_config.get("provider") or os.environ.get("AI_PROVIDER", "kimi"),
    "provider": _local_ai_config.get("provider") or os.environ.get("AI_PROVIDER", "aigw"),
    # API key：优先 AI_API_KEY，其次 KIMI_API_KEY，再其次 GEMINI_API_KEY（运行时注入，不可硬编码）
    "api_key": (
        _local_ai_config.get("api_key")
        or os.environ.get("AI_API_KEY")
        or os.environ.get("KIMI_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ),
    # model：aigw 默认 gpt-5.5
    # Fallback / 回退 Kimi 配置: "kimi-k2-turbo-preview"
    # "model": _local_ai_config.get("model") or os.environ.get("AI_MODEL", "kimi-k2-turbo-preview"),
    "model": _local_ai_config.get("model") or os.environ.get("AI_MODEL", "gpt-5.5"),
    # base_url：aigw gateway；切回 Kimi 时可删除此行（Kimi 用 KIMI_BASE_URL）
    # Fallback / 回退: "https://supercodex.space/v1"
    "base_url": _local_ai_config.get("base_url") or os.environ.get("AI_BASE_URL") or os.environ.get("OPENROUTER_BASE_URL", "https://aigw.sotatts.online/v1"),
}

# 去重配置
DEDUP_CONFIG = {
    "enabled": True,  # 是否启用去重
    "similarity_threshold": 0.98,  # 标题相似度阈值（0-1）
}

# GitHub配置
GITHUB_CONFIG = {
    "repo_name": "literature-tracker",
    "branch": "main",
    "pages_branch": "gh-pages",
}

# 数据文件路径
DATA_DIR = "data"
ARTICLES_DIR = "articles"
HISTORY_FILE = "data/history.json"
FAVORITES_FILE = "data/favorites.json"


# 核心关注（ML × ferro/凝聚态）开关与阈值
CORE_FOCUS_CONFIG = {
    "enabled": (os.environ.get("CORE_FOCUS_ENABLED", "1").strip().lower() not in ("0", "false", "no")),
    "daily_max_items": int(os.environ.get("CORE_FOCUS_DAILY_MAX", "8")),
    "weekly_max_items": int(os.environ.get("CORE_FOCUS_WEEKLY_MAX", "20")),
    "min_score": float(os.environ.get("CORE_FOCUS_MIN_SCORE", "0.60")),
}
