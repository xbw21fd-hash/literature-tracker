#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focus filtering for quantum information / many-body / metrology literature."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

# 量子信息/计算核心词
AI_TERMS: Tuple[str, ...] = (
    'quantum information', 'quantum computing', 'quantum computation',
    'quantum error correction', 'quantum error correcting', 'quantum error',
    'quantum channel', 'quantum circuit', 'quantum algorithm', 'quantum gate',
    'fault tolerant', 'fault-tolerant', 'qubit', 'qubits',
    'quantum communication', 'quantum cryptography', 'quantum key distribution', 'qkd',
    'quantum teleportation', 'quantum network', 'quantum memory', 'quantum repeater',
    'stabilizer code', 'surface code', 'toric code', 'ldpc',
    'quantum advantage', 'quantum supremacy', 'quantum machine learning',
    'variational quantum', 'vqe', 'qaoa',
    '量子信息', '量子计算', '量子纠错', '量子通信', '量子密码', '量子线路', '量子算法', '量子优势',
)

# 量子多体/计量/模拟核心词
PHYSICS_TERMS: Tuple[str, ...] = (
    'quantum many-body', 'many-body', 'quantum phase transition', 'quantum phase',
    'quantum simulation', 'quantum simulator',
    'entanglement', 'entangled', 'quantum entanglement', 'entanglement entropy',
    'tensor network', 'matrix product state', 'mps', 'dmrg',
    'topological order', 'topological phase', 'anyons', 'anyon',
    'quantum spin liquid', 'frustrated magnet',
    'quantum metrology', 'quantum sensing', 'quantum sensor',
    'quantum fisher information', 'heisenberg limit',
    'quantum benchmark', 'quantum tomography', 'quantum characterization',
    'open quantum system', 'lindblad', 'master equation', 'quantum decoherence',
    'quantum optics', 'cavity qed', 'circuit qed', 'quantum thermodynamics',
    'cold atoms', 'ultracold', 'optical lattice', 'bose-einstein condensate',
    'quantum hardware', 'superconducting qubit', 'trapped ion', 'photonic qubit',
    'spin qubit', 'nitrogen vacancy', 'nv center',
    'quantum', 'qubit',
    '量子多体', '量子相变', '量子模拟', '纠缠', '张量网络', '拓扑序',
    '量子自旋液体', '量子计量', '量子传感', '量子光学', '冷原子', '光晶格',
    '开放量子系统', '量子退相干', '量子硬件', '超导量子比特',
)

PHYSICS_CORE_TERMS: Tuple[str, ...] = PHYSICS_TERMS

DAILY_PHYSICS_TERMS: Tuple[str, ...] = (
    'quantum information', 'quantum computing', 'quantum error',
    'entanglement', 'qubit', 'quantum circuit', 'quantum algorithm',
    'quantum many-body', 'many-body', 'quantum phase',
    'tensor network', 'topological', 'quantum metrology', 'quantum sensing',
    'quantum simulation', 'quantum optics', 'open quantum',
)

CHEMISTRY_TERMS: Tuple[str, ...] = ()
CHEMISTRY_CORE_TERMS: Tuple[str, ...] = ()
MATERIALS_TERMS: Tuple[str, ...] = ()
MATERIALS_CORE_TERMS: Tuple[str, ...] = ()

SIMULATION_TERMS: Tuple[str, ...] = (
    'quantum simulation', 'quantum simulator', 'tensor network', 'dmrg',
    'matrix product state', 'quantum monte carlo', 'exact diagonalization',
    'density matrix', 'path integral',
)

SIMULATION_CORE_TERMS: Tuple[str, ...] = SIMULATION_TERMS
DAILY_SIMULATION_TERMS: Tuple[str, ...] = SIMULATION_TERMS

CURATED_JOURNAL_HINTS: Tuple[str, ...] = (
    'phys. rev. lett', 'physical review letters',
    'phys. rev. x', 'physical review x',
    'phys. rev. a', 'physical review a',
    'prx quantum', 'quantum',
    'nature', 'science', 'science advances',
    'nature physics', 'nature communications',
    'npj quantum', 'quantum science and technology',
    'new journal of physics', 'communications physics',
)

ALLOWED_ARXIV_PHYSICAL: Tuple[str, ...] = (
    'quant-ph', 'cond-mat', 'cs.it',
)

ALLOWED_ARXIV_AI: Tuple[str, ...] = (
    'cs.lg', 'stat.ml', 'cs.ai',
)

NEGATIVE_CLINICAL_TERMS: Tuple[str, ...] = (
    'patient', 'patients', 'clinical', 'biomedical', 'disease', 'cancer', 'tumor',
    'therapy', 'therapeutic', 'diagnosis', 'hospital', 'healthcare', 'medical',
    'drug', 'pharmac', 'pathology', 'radiology', 'epidemiology', 'oncology',
    '临床', '患者', '疾病', '癌', '肿瘤', '治疗', '诊断', '医院', '医学', '药物',
)

NEGATIVE_LIFE_SCIENCE_TERMS: Tuple[str, ...] = (
    'immune', 'immunology', 'protein', 'proteins', 'peptide',
    'dna', 'rna', 'genome', 'genomic', 'cell biology',
    'single-cell', 'stem cell', 'mouse', 'mice', 'vaccine', 'virus',
    'bacteria', 'microbiome',
    '免疫', '蛋白', '基因组', '单细胞', '小鼠', '疫苗', '病毒', '细菌',
)

NEGATIVE_SOCIAL_TERMS: Tuple[str, ...] = (
    'education', 'educational', 'student', 'students', 'school',
    'qualitative', 'cross-sectional', 'retrospective', 'survey',
    'sociology', 'public health', 'curriculum',
    '教育', '学生', '横断面', '回顾性', '调查', '公共卫生',
)


def _normalize_text(value: Any) -> str:
    return ' '.join(str(value or '').replace('\xa0', ' ').replace('\n', ' ').split()).lower()


def _item_text(item: Mapping[str, Any]) -> str:
    parts = [
        item.get('title') or item.get('title_en') or '',
        item.get('title_zh') or '',
        item.get('abstract') or '',
        item.get('abstract_zh') or '',
        item.get('summary') or '',
        item.get('journal') or '',
        item.get('source_url') or '',
        item.get('arxiv_category') or '',
    ]
    return _normalize_text(' '.join(parts))


def _item_title_focus_text(item: Mapping[str, Any]) -> str:
    parts = [
        item.get('title') or item.get('title_en') or '',
        item.get('title_zh') or '',
        item.get('journal') or '',
        item.get('arxiv_category') or '',
    ]
    return _normalize_text(' '.join(parts))


def _has_any(text: str, terms: Sequence[str], *, whole_term: bool = False) -> bool:
    for term in terms:
        if not term:
            continue
        if not whole_term or any(ord(ch) > 127 for ch in term):
            if term in text:
                return True
            continue
        pattern = rf'(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])'
        if re.search(pattern, text):
            return True
    return False


def analyze_focus(item: Mapping[str, Any]) -> Dict[str, bool]:
    text = _item_text(item)
    journal = _normalize_text(item.get('journal') or '')
    arxiv_category = _normalize_text(item.get('arxiv_category') or '')

    has_ai = _has_any(text, AI_TERMS)
    has_physics = _has_any(text, PHYSICS_TERMS)
    has_chemistry = False
    has_materials = False
    has_simulation = _has_any(text, SIMULATION_TERMS)

    strong_physics = has_physics
    strong_chemistry = False
    strong_materials = False
    strong_simulation = has_simulation

    curated_journal = _has_any(journal, CURATED_JOURNAL_HINTS)
    arxiv_physical = _has_any(arxiv_category, ALLOWED_ARXIV_PHYSICAL)
    arxiv_ai = _has_any(arxiv_category, ALLOWED_ARXIV_AI)

    clinical_biomed = _has_any(text, NEGATIVE_CLINICAL_TERMS, whole_term=True)
    life_science = clinical_biomed or _has_any(text, NEGATIVE_LIFE_SCIENCE_TERMS, whole_term=True)
    social = _has_any(text, NEGATIVE_SOCIAL_TERMS, whole_term=True)

    direct_science = has_physics or has_ai or has_simulation or (arxiv_physical and has_physics)
    journal_supported = curated_journal and (has_physics or has_ai)

    hard_offtopic = social or clinical_biomed or (life_science and not has_physics)
    target_domain = not hard_offtopic and (direct_science or journal_supported)
    ai_science = not hard_offtopic and has_ai and (has_physics or journal_supported)

    return {
        'has_ai': has_ai,
        'has_physics': has_physics,
        'has_chemistry': has_chemistry,
        'has_materials': has_materials,
        'has_simulation': has_simulation,
        'strong_physics': strong_physics,
        'strong_chemistry': strong_chemistry,
        'strong_materials': strong_materials,
        'strong_simulation': strong_simulation,
        'curated_journal': curated_journal,
        'arxiv_physical': arxiv_physical,
        'arxiv_ai': arxiv_ai,
        'clinical_biomed': clinical_biomed,
        'life_science': life_science,
        'social': social,
        'direct_science': direct_science,
        'hard_offtopic': hard_offtopic,
        'target_domain': target_domain,
        'ai_science': ai_science,
    }


def is_target_domain(item: Mapping[str, Any]) -> bool:
    return analyze_focus(item)['target_domain']


def is_hard_offtopic(item: Mapping[str, Any]) -> bool:
    return analyze_focus(item)['hard_offtopic']


def filter_focus_items(items: Iterable[Mapping[str, Any]]) -> Tuple[List[Mapping[str, Any]], List[Mapping[str, Any]]]:
    kept: List[Mapping[str, Any]] = []
    dropped: List[Mapping[str, Any]] = []
    for item in items:
        if is_target_domain(item):
            kept.append(item)
        else:
            dropped.append(item)
    return kept, dropped


TIER1_JOURNAL_HINTS: Tuple[str, ...] = (
    'phys. rev. lett', 'physical review letters',
    'phys. rev. x', 'physical review x',
    'phys. rev. a', 'physical review a',
    'prx quantum', 'quantum',
    'nature', 'science', 'science advances',
    'nature physics', 'nature communications',
    'npj quantum', 'quantum science and technology',
    'new journal of physics',
)

TIER2_JOURNAL_HINTS: Tuple[str, ...] = (
    'communications physics', 'annals of physics',
)

DAILY_TITLE_AI_TERMS: Tuple[str, ...] = (
    'quantum error', 'quantum circuit', 'quantum algorithm',
    'entanglement', 'qubit', 'quantum information', 'quantum computing',
)

DAILY_TITLE_PHYSICS_TERMS: Tuple[str, ...] = (
    'quantum', 'many-body', 'topological', 'tensor network',
    'quantum metrology', 'quantum sensing', 'quantum simulation',
    'open quantum', 'quantum optics',
)

DAILY_TITLE_CHEMISTRY_TERMS: Tuple[str, ...] = ()
DAILY_TITLE_MATERIALS_TERMS: Tuple[str, ...] = ()
DAILY_TITLE_SIMULATION_TERMS: Tuple[str, ...] = ()


def is_daily_focus(item: Mapping[str, Any]) -> bool:
    signals = analyze_focus(item)
    if not signals['target_domain']:
        return False
    title_text = _item_title_focus_text(item)
    abstract_text = (item.get('abstract') or item.get('summary') or '').lower()
    combined_text = title_text + ' ' + abstract_text
    all_keywords = (
        'quantum', 'qubit', 'entanglement', 'many-body',
        'topological', 'tensor network', 'quantum error',
        'quantum metrology', 'quantum sensing', 'quantum simulation',
        'quantum optics', 'open quantum', 'quantum information',
    )
    return _has_any(combined_text, all_keywords)


def daily_focus_priority(item: Mapping[str, Any]) -> tuple:
    signals = analyze_focus(item)
    title_text = _item_title_focus_text(item)
    title_has_ai = _has_any(title_text, DAILY_TITLE_AI_TERMS)
    title_has_physics = _has_any(title_text, DAILY_TITLE_PHYSICS_TERMS)
    title_core_science = title_has_physics
    if title_has_ai and title_core_science:
        band = 0
    elif title_has_ai:
        band = 1
    elif title_has_physics:
        band = 2
    else:
        band = 4
    return (band,)


def filter_daily_focus_items(
    items: Iterable[Mapping[str, Any]],
    *,
    min_keep: int = 12,
    max_keep: int = 60,
) -> Tuple[List[Mapping[str, Any]], List[Mapping[str, Any]]]:
    eligible = [item for item in items if is_daily_focus(item)]
    eligible = sorted(eligible, key=daily_focus_priority)

    def item_key(item: Mapping[str, Any]) -> str:
        return str(item.get('link') or item.get('title') or item.get('title_en') or item.get('title_zh') or '')

    selected: List[Mapping[str, Any]] = []
    selected_keys = set()

    def add(item: Mapping[str, Any]) -> None:
        key = item_key(item)
        if not key or key in selected_keys or len(selected) >= max_keep:
            return
        selected.append(item)
        selected_keys.add(key)

    for item in eligible:
        add(item)

    dropped = [item for item in items if item_key(item) not in selected_keys]
    return selected, dropped


def topic_bucket(item: Mapping[str, Any]) -> str:
    signals = analyze_focus(item)
    if signals['has_ai']:
        return 'quantum_info'
    if signals['has_physics']:
        return 'physics'
    if signals['has_simulation']:
        return 'methods'
    return 'other'


def focus_priority(item: Mapping[str, Any]) -> tuple:
    from focus_core import core_score
    signals = analyze_focus(item)
    bucket = topic_bucket(item)
    bucket_rank = {
        'quantum_info': 0,
        'physics': 1,
        'methods': 2,
        'other': 3,
    }.get(bucket, 4)
    try:
        ai_score = float(item.get('ai_score') or 0)
    except Exception:
        ai_score = 0.0
    journal = _normalize_text(item.get('journal') or '')
    is_arxiv = journal == 'arxiv'
    direct_bonus = 0 if signals['direct_science'] else 1
    cscore = core_score(item)
    return (
        0 if cscore > 0.0 else 1,
        -cscore,
        0 if signals['ai_science'] else 1,
        direct_bonus,
        bucket_rank,
        0 if is_arxiv else 1,
        -ai_score,
        _normalize_text(item.get('title') or item.get('title_zh') or ''),
    )
