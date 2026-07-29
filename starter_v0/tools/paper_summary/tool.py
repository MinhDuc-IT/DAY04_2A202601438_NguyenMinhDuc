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


def _download_and_extract(arxiv_url: str, max_pages: int = 10, max_chars: int = 15000) -> tuple[str, str, str]:
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


def _extract_abstract(text: str) -> str:
    """Try to extract the abstract section from paper text."""
    # Common patterns for abstract boundaries
    abstract_patterns = [
        r"(?i)abstract\s*\n(.*?)(?:\n\s*(?:1\.?\s*introduction|keywords|index terms))",
        r"(?i)abstract[:\-—\s]+(.*?)(?:\n\s*(?:1\.?\s*introduction|keywords|index terms))",
    ]
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    # Fallback: return first 1500 chars
    return text[:1500]


def _extract_section(text: str, section_name: str) -> str:
    """Try to extract a specific section from paper text."""
    patterns = [
        rf"(?i)(?:\d+\.?\s*)?(?:{section_name})\s*\n(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
        rf"(?i)(?:{section_name})[:\-—\s]+(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()[:3000]
    return ""


def summarize_paper(arxiv_url: str = "", focus_area: str = "all", length: str = "short") -> dict[str, Any]:
    """Summarize a paper from arXiv. Extracts and returns key sections for the LLM to summarize."""
    try:
        arxiv_id, text, pdf_url = _download_and_extract(arxiv_url)
        max_chars = 5000 if length == "short" else 12000

        sections: dict[str, str] = {}

        if focus_area == "all" or focus_area == "abstract":
            sections["abstract"] = _extract_abstract(text)

        if focus_area == "all" or focus_area == "methodology":
            method = _extract_section(text, "method(?:ology)?|approach|proposed")
            sections["methodology"] = method if method else "(Không tách được phần methodology riêng — xem toàn bộ text bên dưới)"

        if focus_area == "all" or focus_area == "results":
            results = _extract_section(text, "results?|experiments?|evaluation")
            sections["results"] = results if results else "(Không tách được phần results riêng)"

        if focus_area == "all" or focus_area == "conclusion":
            conclusion = _extract_section(text, "conclusion|summary|discussion")
            sections["conclusion"] = conclusion if conclusion else "(Không tách được phần conclusion riêng)"

        # Build summary content
        summary_parts: list[str] = []
        for sec_name, sec_text in sections.items():
            if sec_text and not sec_text.startswith("("):
                summary_parts.append(f"## {sec_name.upper()}\n{sec_text}")

        summary_text = "\n\n".join(summary_parts)
        if not summary_text.strip():
            summary_text = text[:max_chars]
        else:
            summary_text = summary_text[:max_chars]

        return {
            "tool": "paper_summary",
            "arxiv_id": arxiv_id,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": pdf_url,
            "focus_area": focus_area,
            "length": length,
            "sections_found": list(sections.keys()),
            "items": [{
                "title": f"Summary of arXiv paper {arxiv_id}",
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "source": "arxiv.org",
                "summary": summary_text,
            }],
        }
    except Exception as exc:
        return err("paper_summary", exc)
