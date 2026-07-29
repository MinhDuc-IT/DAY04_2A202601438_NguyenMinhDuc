from __future__ import annotations

import re
from typing import Any

from tools._shared import err


_METHOD_KW = [
    "method",
    "approach",
    "we propose",
    "we present",
    "architecture",
    "model",
    "framework",
    "algorithm",
    "objective",
    "loss",
    "training",
    "optimization",
    "implementation details",
]

_RESULT_KW = [
    "results",
    "we find",
    "we show",
    "achieve",
    "improve",
    "improved",
    "outperform",
    "accuracy",
    "f1",
    "bleu",
    "rouge",
    "mrr",
    "ndcg",
    "%",
    "significant",
]

_LIMITATION_KW = [
    "limitation",
    "limitations",
    "future work",
    "we leave",
    "does not",
    "however,",
    "weakness",
]


def _sentences(text: str) -> list[str]:
    # Split into sentences; keep it intentionally simple for robustness.
    parts = re.split(r"(?<=[.!?])\\s+", (text or "").strip())
    return [p.strip() for p in parts if p and p.strip()]


def _pick_by_keywords(sentences: list[str], keywords: list[str], *, max_bullets: int) -> list[str]:
    lower_kws = [k.lower() for k in keywords if k]
    scored: list[tuple[int, str]] = []
    for s in sentences:
        sl = s.lower()
        score = sum(1 for kw in lower_kws if kw and kw in sl)
        if score > 0:
            scored.append((score, s))

    if scored:
        # Sort by score (descending), then by appearance order (stable sort by original list)
        scored.sort(key=lambda x: (-x[0]))
        selected: list[str] = []
        seen: set[str] = set()
        for _, s in scored:
            if s not in seen:
                selected.append(s)
                seen.add(s)
            if len(selected) >= max_bullets:
                break
        return selected

    # Fallback: take earliest sentences to keep output non-empty.
    fallback: list[str] = []
    for s in sentences:
        if s not in fallback:
            fallback.append(s)
        if len(fallback) >= max_bullets:
            break
    return fallback


def _trim_bullets(items: list[str], *, max_bullets: int) -> list[str]:
    cleaned: list[str] = []
    for x in items:
        s = (x or "").strip().replace("\\n", " ")
        if not s:
            continue
        if len(s) > 240:
            s = s[:237] + "..."
        cleaned.append(s)
    return cleaned[: max(1, int(max_bullets or 5))]


def scout_paper_summary(
    paper_text: str = "",
    arxiv_id: str = "",
    title: str = "",
    max_bullets: int = 5,
) -> dict[str, Any]:
    try:
        if not (paper_text or "").strip():
            raise ValueError("paper_text is empty")

        max_bullets = max(1, int(max_bullets or 5))
        sentences = _sentences(paper_text)

        methods = _pick_by_keywords(sentences, _METHOD_KW, max_bullets=max_bullets)
        results = _pick_by_keywords(sentences, _RESULT_KW, max_bullets=max_bullets)

        # Limitations: usually sparse, so fallback to empty.
        limitations = _pick_by_keywords(sentences, _LIMITATION_KW, max_bullets=min(3, max_bullets))

        return {
            "tool": "paper_scout_summary",
            "arxiv_id": arxiv_id or "",
            "title": title or "",
            "methods": _trim_bullets(methods, max_bullets=max_bullets),
            "results": _trim_bullets(results, max_bullets=max_bullets),
            "limitations": _trim_bullets(limitations, max_bullets=min(3, max_bullets)),
        }
    except Exception as exc:
        return err("paper_scout_summary", exc)

