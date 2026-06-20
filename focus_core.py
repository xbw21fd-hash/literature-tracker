#!/usr/bin/env python3
"""Core-focus classifier: 量子信息/量子多体/量子计量 方向判定，纯函数，无外部依赖。"""

from typing import Any, Dict, Mapping, Optional, Tuple

# —— 量子信息/计算侧 ——
CORE_METHOD_TERMS: Tuple[str, ...] = (
    "quantum information", "quantum computing", "quantum computation",
    "quantum error correction", "quantum error correcting",
    "quantum channel", "quantum circuit", "quantum algorithm",
    "fault tolerant", "fault-tolerant", "qubit", "qubits",
    "quantum gate", "quantum communication", "quantum cryptography",
    "quantum key distribution", "qkd", "quantum teleportation",
    "quantum network", "quantum memory", "quantum repeater",
    "stabilizer code", "surface code", "toric code", "ldpc",
    "quantum advantage", "quantum supremacy",
    "量子信息", "量子计算", "量子纠错", "量子通信", "量子密码",
    "量子线路", "量子算法", "量子优势", "容错量子",
)

# —— 量子多体/计量侧 ——
CORE_FERRO_TERMS: Tuple[str, ...] = (
    "quantum many-body", "many-body", "quantum phase transition",
    "quantum simulation", "quantum simulator",
    "entanglement", "entangled", "quantum entanglement",
    "tensor network", "matrix product state", "mps", "dmrg",
    "topological order", "topological phase", "anyons", "anyon",
    "quantum spin liquid", "frustrated magnet",
    "quantum metrology", "quantum sensing", "quantum sensor",
    "quantum fisher information", "heisenberg limit",
    "quantum benchmark", "quantum tomography",
    "open quantum system", "lindblad", "master equation",
    "quantum optics", "cavity qed", "circuit qed",
    "cold atoms", "ultracold", "optical lattice", "bose-einstein",
    "量子多体", "量子相变", "量子模拟", "纠缠", "张量网络",
    "拓扑序", "量子自旋液体", "量子计量", "量子传感",
    "量子光学", "冷原子", "光晶格",
)

# ── Taxonomy ────────────────────────────────────────────────────────────────
TAXONOMY: Dict[str, Dict[str, Any]] = {
    "量子纠错·容错": {
        "terms": ["quantum error correction", "fault tolerant", "fault-tolerant",
                  "stabilizer code", "surface code", "toric code", "ldpc",
                  "quantum error", "logical qubit", "decoder"],
        "domain": ["qubit", "quantum", "noise", "threshold", "syndrome"],
        "tier": 1,
    },
    "量子信息·通信": {
        "terms": ["quantum information", "quantum communication", "quantum cryptography",
                  "quantum key distribution", "qkd", "quantum teleportation",
                  "quantum network", "quantum channel", "entanglement distillation"],
        "domain": ["quantum", "entanglement", "fidelity", "protocol"],
        "tier": 1,
    },
    "量子计算·算法": {
        "terms": ["quantum computing", "quantum algorithm", "quantum circuit",
                  "quantum gate", "quantum advantage", "quantum supremacy",
                  "variational quantum", "vqe", "qaoa", "quantum machine learning"],
        "domain": ["qubit", "quantum", "complexity", "speedup"],
        "tier": 1,
    },
    "量子多体·拓扑": {
        "terms": ["quantum many-body", "many-body", "quantum phase transition",
                  "tensor network", "matrix product state", "dmrg",
                  "topological order", "topological phase", "anyons",
                  "quantum spin liquid", "entanglement entropy"],
        "domain": ["quantum", "lattice", "hamiltonian", "ground state"],
        "tier": 2,
    },
    "量子计量·传感": {
        "terms": ["quantum metrology", "quantum sensing", "quantum sensor",
                  "quantum fisher information", "heisenberg limit",
                  "quantum benchmark", "quantum tomography",
                  "parameter estimation", "quantum enhanced"],
        "domain": ["quantum", "precision", "measurement", "noise"],
        "tier": 2,
    },
    "量子模拟": {
        "terms": ["quantum simulation", "quantum simulator", "cold atoms",
                  "ultracold", "optical lattice", "bose-einstein", "hubbard model",
                  "cavity qed", "circuit qed"],
        "domain": ["quantum", "hamiltonian", "lattice", "many-body"],
        "tier": 2,
    },
    "开放量子系统·量子光学": {
        "terms": ["open quantum system", "lindblad", "master equation",
                  "quantum optics", "quantum decoherence", "dissipative",
                  "quantum noise", "quantum thermodynamics"],
        "domain": ["quantum", "bath", "environment", "photon"],
        "tier": 2,
    },
    "量子硬件·实验": {
        "terms": ["superconducting qubit", "trapped ion", "photonic qubit",
                  "spin qubit", "nitrogen vacancy", "nv center",
                  "quantum hardware", "quantum processor", "coherence time"],
        "tier": 3,
    },
}

_TAXONOMY_TIER: Dict[str, int] = {cat: spec["tier"] for cat, spec in TAXONOMY.items()}

_CURATED_HIGH_HINTS: Tuple[str, ...] = (
    "nature", "science", "phys. rev. lett", "physical review letters",
    "phys. rev. x", "physical review x", "prx quantum", "quantum",
    "nature physics", "nature communications", "npj quantum",
    "physical review a", "new journal of physics",
)


def _text(article: Any) -> str:
    if not article:
        return ""
    return " ".join(str(article.get(k, "") or "") for k in ("title", "summary", "abstract")).lower()


def classify_taxonomy(article: Any) -> str:
    txt = _text(article)
    if not txt.strip():
        return "其他"
    best: Optional[str] = None
    best_tier = 99
    for cat, spec in TAXONOMY.items():
        terms_hit = any(t in txt for t in spec["terms"])
        domain_hit = ("domain" not in spec) or any(d in txt for d in spec["domain"])
        if terms_hit and domain_hit and spec["tier"] < best_tier:
            best, best_tier = cat, spec["tier"]
    return best or "其他"


def _normalize(text: Any) -> str:
    return " ".join(str(text or "").replace("\xa0", " ").replace("\n", " ").split()).lower()


def _item_fulltext(item: Mapping[str, Any]) -> str:
    parts = [
        item.get("title") or item.get("title_en") or "",
        item.get("title_zh") or "",
        item.get("abstract") or "",
        item.get("abstract_zh") or "",
    ]
    return _normalize(" ".join(parts))


def _item_title_text(item: Mapping[str, Any]) -> str:
    return _normalize(
        " ".join([item.get("title") or item.get("title_en") or "", item.get("title_zh") or ""])
    )


def _has_any(text: str, terms: Tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def is_core_focus(item: Mapping[str, Any]) -> bool:
    """核心关注 = 命中量子信息/多体/计量方向。"""
    if not item:
        return False
    text = _item_fulltext(item)
    if _has_any(text, CORE_METHOD_TERMS) or _has_any(text, CORE_FERRO_TERMS):
        return True
    cat = classify_taxonomy(item)
    return cat != "其他" and _TAXONOMY_TIER.get(cat, 99) <= 2


def core_score(item: Mapping[str, Any]) -> float:
    """0.0 ~ 1.0；未命中核心关注时返回 0.0。"""
    if not item:
        return 0.0
    if not is_core_focus(item):
        return 0.0
    title = _item_title_text(item)
    score = 0.5
    if _has_any(title, CORE_METHOD_TERMS):
        score += 0.15
    if _has_any(title, CORE_FERRO_TERMS):
        score += 0.15
    text = _item_fulltext(item)
    # 量子纠错 + 多体 组合加成
    if _has_any(text, ("quantum error", "fault tolerant", "surface code")) and \
       _has_any(text, ("many-body", "topological", "entanglement")):
        score += 0.10
    # arXiv quant-ph 加成
    src = _normalize(item.get("source_url") or item.get("arxiv_category") or "")
    if "quant-ph" in src:
        score += 0.05
    # 高分期刊加成
    journal = _normalize(item.get("journal") or "")
    if any(hint in journal for hint in _CURATED_HIGH_HINTS):
        score += 0.05
    # Taxonomy tier bonus
    cat = classify_taxonomy(item)
    tier = _TAXONOMY_TIER.get(cat, 99)
    if tier == 1:
        score += 0.10
    elif tier == 2:
        score += 0.05
    elif tier == 3:
        score += 0.01
    return min(1.0, round(score, 3))
