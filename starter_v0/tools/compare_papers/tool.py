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
        raise ValueError(f"Invalid arXiv ID or URL: {value}")
    return match.group(1)


def _download_and_extract(arxiv_url: str, max_pages: int = 10, max_chars: int = 10000) -> tuple[str, str, str]:
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


def _extract_title(text: str) -> str:
    """Try to extract the paper title from the first few lines."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    # Title is usually in the first few non-empty lines, before authors
    if lines:
        return lines[0][:200]
    return "(Unknown title)"


def _extract_abstract(text: str) -> str:
    """Try to extract abstract from paper text."""
    patterns = [
        r"(?i)abstract\s*\n(.*?)(?:\n\s*(?:1\.?\s*introduction|keywords|index terms))",
        r"(?i)abstract[:\-—\s]+(.*?)(?:\n\s*(?:1\.?\s*introduction|keywords|index terms))",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()[:1500]
    return text[:1000]


def _extract_section(text: str, section_name: str) -> str:
    """Try to extract a specific section from paper text."""
    patterns = [
        rf"(?i)(?:\d+\.?\s*)?(?:{section_name})\s*\n(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
        rf"(?i)(?:{section_name})[:\-—\s]+(.*?)(?:\n\s*\d+\.?\s*[A-Z])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()[:2000]
    return ""


def _extract_aspect(text: str, aspect: str) -> str:
    """Extract content relevant to a specific comparison aspect."""
    if aspect == "methodology":
        content = _extract_section(text, "method(?:ology)?|approach|proposed|model")
        return content if content else _extract_abstract(text)
    elif aspect == "dataset":
        content = _extract_section(text, "data(?:set)?|corpus|benchmark")
        if not content:
            content = _extract_section(text, "experiment|setup|evaluation")
        return content if content else "(Không tìm được phần dataset riêng)"
    elif aspect == "results":
        content = _extract_section(text, "results?|experiments?|evaluation|performance")
        return content if content else _extract_abstract(text)
    elif aspect == "limitations":
        content = _extract_section(text, "limitation|weakness|future work|discussion")
        return content if content else "(Không tìm được phần limitations riêng)"
    else:
        return _extract_abstract(text)


def compare_papers(arxiv_urls: list[str] | None = None, aspect: str = "results") -> dict[str, Any]:
    """Compare multiple arXiv papers on a specific aspect (methodology, dataset, results, limitations)."""
    try:
        if not arxiv_urls or len(arxiv_urls) < 2:
            return err("compare_papers", ValueError("Cần ít nhất 2 bài báo để so sánh. Truyền vào danh sách arxiv_urls."))

        if len(arxiv_urls) > 5:
            arxiv_urls = arxiv_urls[:5]  # Limit to 5 papers

        aspect = aspect if aspect in {"methodology", "dataset", "results", "limitations"} else "results"

        paper_data: list[dict[str, Any]] = []
        for url in arxiv_urls:
            try:
                arxiv_id, text, pdf_url = _download_and_extract(url)
                title = _extract_title(text)
                aspect_text = _extract_aspect(text, aspect)
                paper_data.append({
                    "arxiv_id": arxiv_id,
                    "title": title,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "pdf_url": pdf_url,
                    "aspect_content": aspect_text,
                })
            except Exception as exc:
                paper_data.append({
                    "arxiv_id": url,
                    "title": "(Error loading paper)",
                    "url": url,
                    "error": str(exc),
                    "aspect_content": "",
                })

        # Build comparison items for the LLM
        items: list[dict[str, Any]] = []
        for paper in paper_data:
            items.append({
                "title": f"[{paper['arxiv_id']}] {paper.get('title', '')}",
                "url": paper["url"],
                "source": "arxiv.org",
                "summary": paper.get("aspect_content", paper.get("error", "")),
            })

        return {
            "tool": "compare_papers",
            "aspect": aspect,
            "paper_count": len(paper_data),
            "papers_compared": [p["arxiv_id"] for p in paper_data],
            "items": items,
        }
    except Exception as exc:
        return err("compare_papers", exc)
