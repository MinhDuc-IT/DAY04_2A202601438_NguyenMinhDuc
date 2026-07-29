from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

import requests

from tools._shared import ROOT, TIMEOUT, err


ARXIV_DIR = ROOT / "arxiv_papers"
ARXIV_MIN_INTERVAL_SECONDS = 3.0
_last_arxiv_request_at = 0.0


def _arxiv_user_agent() -> str:
    return os.getenv("ARXIV_USER_AGENT", "AI20k-Day04-Research-Agent/1.0 (educational lab; contact: local)")


def _rate_limit_arxiv() -> None:
    global _last_arxiv_request_at
    elapsed = time.monotonic() - _last_arxiv_request_at
    if elapsed < ARXIV_MIN_INTERVAL_SECONDS:
        time.sleep(ARXIV_MIN_INTERVAL_SECONDS - elapsed)
    _last_arxiv_request_at = time.monotonic()


def _arxiv_id(value: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5}(?:v\d+)?)", value or "")
    if not match:
        raise ValueError("Invalid arXiv ID or URL")
    return match.group(1)


def _download_and_extract(arxiv_url: str, max_pages: int = 15, max_chars: int = 18000) -> tuple[str, str, str]:
    """Download PDF from arXiv and extract text. Returns (arxiv_id, text, pdf_url)."""
    arxiv_id = _arxiv_id(arxiv_url)
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    ARXIV_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ARXIV_DIR / f"{arxiv_id}.pdf"

    # Download if not cached
    if not output_path.exists():
        _rate_limit_arxiv()
        response = requests.get(pdf_url, headers={"User-Agent": _arxiv_user_agent()}, timeout=TIMEOUT, stream=True)
        response.raise_for_status()
        with output_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    # Extract text
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf first: pip install pypdf") from exc

    reader = PdfReader(str(output_path))
    page_count = len(reader.pages)
    pages_to_read = min(max(1, int(max_pages)), page_count)
    parts: list[str] = []
    for page in reader.pages[:pages_to_read]:
        parts.append(page.extract_text() or "")
    text = "\n\n".join(part for part in parts if part.strip())
    return arxiv_id, text[:max_chars], pdf_url


def _extract_section(text: str, section_name: str, max_len: int = 3000) -> str:
    """Try to extract a specific section from paper text."""
    patterns = [
        rf"(?i)(?:\d+\.?\s*)?(?:{section_name})\s*\n(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
        rf"(?i)(?:{section_name})[:\-—\s]+(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()[:max_len]
    return ""


def _extract_contributions(text: str) -> str:
    """Extract main contributions of the paper."""
    # Contributions are usually listed in the introduction
    patterns = [
        r"(?i)(?:our |main |key )?contributions?\s*(?:are|include|of this).*?(?:\n.*?){1,10}",
        r"(?i)(?:we |this paper |this work )\s*(?:propose|present|introduce|contribute).*?(?:\.\s*\n)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(0).strip()[:2500]

    # Fallback: look in abstract + introduction
    intro = _extract_section(text, "introduction")
    abstract_match = re.search(r"(?i)abstract\s*\n(.*?)(?:\n\s*(?:1\.?\s*introduction|keywords))", text, re.DOTALL)
    abstract = abstract_match.group(1).strip()[:1500] if abstract_match else ""

    if intro:
        return f"[Từ Abstract]\n{abstract}\n\n[Từ Introduction]\n{intro[:1500]}"
    return abstract if abstract else text[:2000]


def _extract_methodology(text: str) -> str:
    """Extract methodology/approach used in the paper."""
    section = _extract_section(text, "method(?:ology)?|approach|proposed|model|framework|architecture")
    if section:
        return section
    # Fallback: try to get from broader context
    section = _extract_section(text, "system|design|implementation")
    return section if section else "(Không tách được phần methodology riêng — vui lòng xem toàn bộ nội dung paper)"


def _extract_limitations(text: str) -> str:
    """Extract limitations and weaknesses discussed in the paper."""
    section = _extract_section(text, "limitation|weakness|shortcoming")
    if section:
        return section

    # Try in conclusion/discussion sections
    conclusion = _extract_section(text, "conclusion|discussion|future work")
    if conclusion:
        # Look for limitation keywords within conclusion
        limit_patterns = [
            r"(?i)(?:however|limitation|drawback|weakness|shortcoming|challenge|issue|despite).*?(?:\.\s)",
        ]
        findings: list[str] = []
        for pattern in limit_patterns:
            matches = re.findall(pattern, conclusion, re.DOTALL)
            findings.extend(matches)
        if findings:
            return "\n".join(f.strip() for f in findings[:5])
        return f"[Từ Conclusion/Discussion]\n{conclusion}"

    return "(Không tìm được phần limitations rõ ràng trong bài báo)"


def _extract_datasets(text: str) -> str:
    """Extract information about datasets used."""
    section = _extract_section(text, "data(?:set)?|corpus|benchmark")
    if section:
        return section
    section = _extract_section(text, "experiment(?:al)? setup|evaluation setup|training")
    return section if section else "(Không tìm được thông tin dataset riêng)"


def _extract_future_work(text: str) -> str:
    """Extract future work directions."""
    section = _extract_section(text, "future work|future direction|outlook")
    if section:
        return section
    conclusion = _extract_section(text, "conclusion|discussion")
    if conclusion:
        future_patterns = [
            r"(?i)(?:future|further|next|plan to|will|intend|aim to).*?(?:\.\s)",
        ]
        findings: list[str] = []
        for pattern in future_patterns:
            matches = re.findall(pattern, conclusion, re.DOTALL)
            findings.extend(matches)
        if findings:
            return "\n".join(f.strip() for f in findings[:5])
    return "(Không tìm được thông tin future work rõ ràng)"


# Mapping from insight type to extraction function
_INSIGHT_EXTRACTORS = {
    "contributions": _extract_contributions,
    "methodology": _extract_methodology,
    "limitations": _extract_limitations,
    "datasets": _extract_datasets,
    "future_work": _extract_future_work,
}

VALID_INSIGHTS = set(_INSIGHT_EXTRACTORS.keys())


def extract_paper_insights(
    arxiv_url: str = "",
    insights_needed: list[str] | None = None,
) -> dict[str, Any]:
    """Extract specific analytical insights from an arXiv paper (contributions, methodology, limitations, etc.)."""
    try:
        if insights_needed is None:
            insights_needed = ["contributions", "methodology", "limitations"]

        # Validate and filter insights
        insights_needed = [i for i in insights_needed if i in VALID_INSIGHTS]
        if not insights_needed:
            insights_needed = ["contributions", "methodology", "limitations"]

        arxiv_id, text, pdf_url = _download_and_extract(arxiv_url)

        extracted: dict[str, str] = {}
        for insight_type in insights_needed:
            extractor = _INSIGHT_EXTRACTORS[insight_type]
            extracted[insight_type] = extractor(text)

        # Build structured output
        summary_parts: list[str] = []
        for insight_type, content in extracted.items():
            label = {
                "contributions": "ĐÓNG GÓP CHÍNH",
                "methodology": "PHƯƠNG PHÁP",
                "limitations": "HẠN CHẾ",
                "datasets": "TẬP DỮ LIỆU",
                "future_work": "HƯỚNG PHÁT TRIỂN",
            }.get(insight_type, insight_type.upper())
            summary_parts.append(f"## {label}\n{content}")

        summary_text = "\n\n".join(summary_parts)

        return {
            "tool": "extract_paper_insights",
            "arxiv_id": arxiv_id,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": pdf_url,
            "insights_requested": insights_needed,
            "insights_found": list(extracted.keys()),
            "items": [{
                "title": f"Insights from arXiv paper {arxiv_id}",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "arxiv.org",
                "summary": summary_text,
            }],
        }
    except Exception as exc:
        return err("extract_paper_insights", exc)
