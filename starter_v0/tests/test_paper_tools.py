"""
Unit tests cho 3 tool mới: paper_summary, compare_papers, extract_paper_insights.

Chạy:
    python -m pytest tests/test_paper_tools.py -v

Tất cả API calls (arXiv download) đều được mock — không cần mạng.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fake paper text giả lập nội dung một bài báo khoa học
# ---------------------------------------------------------------------------
FAKE_PAPER_TEXT = textwrap.dedent("""\
    Attention Is All You Need

    Ashish Vaswani, Noam Shazeer, Niki Parmar

    Abstract
    The dominant sequence transduction models are based on complex recurrent or
    convolutional neural networks that include an encoder and a decoder. The best
    performing models also connect the encoder and decoder through an attention
    mechanism. We propose a new simple network architecture, the Transformer,
    based solely on attention mechanisms, dispensing with recurrence and convolutions
    entirely. The Transformer allows for significantly more parallelization and can
    reach a new state of the art in translation quality.

    Keywords: transformer, attention, sequence-to-sequence

    1 Introduction
    Recurrent neural networks, long short-term memory and gated recurrent neural
    networks in particular, have been firmly established as state of the art approaches
    in sequence modeling and transduction problems. Our contributions are as follows:
    We propose a novel architecture based purely on attention. We show that the
    Transformer generalizes well to other tasks. We achieve new state of the art on
    English-to-German and English-to-French translation.

    2 Methodology
    The Transformer follows an encoder-decoder structure using stacked self-attention
    and point-wise, fully connected layers for both the encoder and decoder. The encoder
    maps an input sequence of symbol representations to a sequence of continuous
    representations. The decoder then generates an output sequence of symbols one
    element at a time. Multi-head attention allows the model to jointly attend to
    information from different representation subspaces at different positions.

    3 Results
    On the WMT 2014 English-to-German translation task, the big transformer model
    outperforms the best previously reported models including ensembles by more than
    2.0 BLEU, establishing a new state-of-the-art BLEU score of 28.4. On the WMT 2014
    English-to-French translation task, our model establishes a new single-model
    state-of-the-art BLEU score of 41.0.

    4 Dataset
    We trained on the standard WMT 2014 English-German dataset consisting of about
    4.5 million sentence pairs. For English-French, we used the significantly larger
    WMT 2014 English-French dataset consisting of 36M sentence pairs.

    5 Limitations
    The Transformer has a fixed context window and cannot process arbitrarily long
    sequences. Self-attention has quadratic complexity with respect to the sequence
    length. The model requires significant computational resources for training.

    6 Conclusion
    In this work, we presented the Transformer, the first sequence transduction model
    based entirely on attention. Future work includes applying the Transformer to
    other modalities such as images, audio, and video.
""")

FAKE_PAPER_TEXT_2 = textwrap.dedent("""\
    BERT: Pre-training of Deep Bidirectional Transformers

    Jacob Devlin, Ming-Wei Chang

    Abstract
    We introduce a new language representation model called BERT, which stands for
    Bidirectional Encoder Representations from Transformers. BERT is designed to
    pre-train deep bidirectional representations by jointly conditioning on both
    left and right context in all layers.

    1 Introduction
    Language model pre-training has been shown to be effective for improving many
    natural language processing tasks.

    2 Methodology
    BERT uses a masked language model (MLM) pre-training objective. Unlike previous
    models, BERT is designed to pre-train deep bidirectional representations from
    unlabeled text. The model is fine-tuned with just one additional output layer.

    3 Results
    BERT obtains new state-of-the-art results on eleven natural language processing
    tasks, including pushing the GLUE score to 80.5, MultiNLI accuracy to 86.7,
    SQuAD v1.1 F1 to 93.2 and SQuAD v2.0 F1 to 83.1.

    4 Limitations
    BERT's pre-training is computationally expensive. The model size makes it
    difficult to deploy in resource-constrained environments.

    5 Conclusion
    We showed that rich, unsupervised pre-training is an integral part of many
    language understanding systems.
""")


# ---------------------------------------------------------------------------
# Import tool modules directly to avoid name collision with functions
# ---------------------------------------------------------------------------
from tools.paper_summary import tool as paper_summary_mod
from tools.compare_papers import tool as compare_papers_mod
from tools.extract_paper_insights import tool as extract_insights_mod


# ---------------------------------------------------------------------------
# Helper: fake _download_and_extract
# ---------------------------------------------------------------------------
def _fake_download_paper1(arxiv_url: str, max_pages: int = 10, max_chars: int = 15000):
    return "1706.03762", FAKE_PAPER_TEXT[:max_chars], "https://arxiv.org/pdf/1706.03762.pdf"


def _fake_download_paper2(arxiv_url: str, max_pages: int = 10, max_chars: int = 15000):
    return "1810.04805", FAKE_PAPER_TEXT_2[:max_chars], "https://arxiv.org/pdf/1810.04805.pdf"


def _fake_download_dispatch(arxiv_url: str, max_pages: int = 10, max_chars: int = 10000):
    """Route to different fake texts based on arxiv_url."""
    if "1706" in arxiv_url:
        return "1706.03762", FAKE_PAPER_TEXT[:max_chars], "https://arxiv.org/pdf/1706.03762.pdf"
    else:
        return "1810.04805", FAKE_PAPER_TEXT_2[:max_chars], "https://arxiv.org/pdf/1810.04805.pdf"


# ===========================================================================
# TEST: paper_summary
# ===========================================================================
class TestPaperSummary:
    """Tests cho tool paper_summary (summarize_paper)."""

    @patch.object(paper_summary_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_summary_all_sections(self, mock_dl: MagicMock) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="1706.03762", focus_area="all", length="short")

        assert result["tool"] == "paper_summary"
        assert result["arxiv_id"] == "1706.03762"
        assert "error" not in result
        assert len(result["items"]) == 1
        assert result["focus_area"] == "all"
        assert "abstract" in result["sections_found"]
        mock_dl.assert_called_once()

    @patch.object(paper_summary_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_summary_focus_methodology(self, mock_dl: MagicMock) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="1706.03762", focus_area="methodology")

        assert result["tool"] == "paper_summary"
        assert "error" not in result
        assert "methodology" in result["sections_found"]
        assert "abstract" not in result["sections_found"]

    @patch.object(paper_summary_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_summary_detailed_length(self, mock_dl: MagicMock) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="1706.03762", focus_area="all", length="detailed")

        assert result["length"] == "detailed"
        assert "error" not in result

    def test_summary_invalid_arxiv_url(self) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="not-a-valid-url")

        assert "error" in result
        assert result["tool"] == "paper_summary"

    @patch.object(paper_summary_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_summary_items_have_required_keys(self, mock_dl: MagicMock) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="1706.03762")
        item = result["items"][0]

        assert "title" in item
        assert "url" in item
        assert "source" in item
        assert "summary" in item
        assert item["source"] == "arxiv.org"


# ===========================================================================
# TEST: compare_papers
# ===========================================================================
class TestComparePapers:
    """Tests cho tool compare_papers."""

    @patch.object(compare_papers_mod, "_download_and_extract", side_effect=_fake_download_dispatch)
    def test_compare_two_papers_results(self, mock_dl: MagicMock) -> None:
        result = compare_papers_mod.compare_papers(
            arxiv_urls=["1706.03762", "1810.04805"],
            aspect="results",
        )

        assert result["tool"] == "compare_papers"
        assert "error" not in result
        assert result["paper_count"] == 2
        assert len(result["items"]) == 2
        assert result["aspect"] == "results"
        assert "1706.03762" in result["papers_compared"]
        assert "1810.04805" in result["papers_compared"]

    @patch.object(compare_papers_mod, "_download_and_extract", side_effect=_fake_download_dispatch)
    def test_compare_methodology(self, mock_dl: MagicMock) -> None:
        result = compare_papers_mod.compare_papers(
            arxiv_urls=["1706.03762", "1810.04805"],
            aspect="methodology",
        )

        assert result["aspect"] == "methodology"
        assert "error" not in result
        for item in result["items"]:
            assert item["summary"]

    def test_compare_less_than_two_papers(self) -> None:
        result = compare_papers_mod.compare_papers(arxiv_urls=["1706.03762"])

        assert "error" in result

    def test_compare_no_papers(self) -> None:
        result = compare_papers_mod.compare_papers(arxiv_urls=None)

        assert "error" in result

    @patch.object(compare_papers_mod, "_download_and_extract", side_effect=_fake_download_dispatch)
    def test_compare_invalid_aspect_defaults_to_results(self, mock_dl: MagicMock) -> None:
        result = compare_papers_mod.compare_papers(
            arxiv_urls=["1706.03762", "1810.04805"],
            aspect="invalid_aspect",
        )

        assert result["aspect"] == "results"

    @patch.object(compare_papers_mod, "_download_and_extract", side_effect=_fake_download_dispatch)
    def test_compare_max_five_papers(self, mock_dl: MagicMock) -> None:
        urls = [f"1706.0376{i}" for i in range(7)]
        result = compare_papers_mod.compare_papers(arxiv_urls=urls)

        assert result["paper_count"] <= 5


# ===========================================================================
# TEST: extract_paper_insights
# ===========================================================================
class TestExtractPaperInsights:
    """Tests cho tool extract_paper_insights."""

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_default_insights(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(arxiv_url="1706.03762")

        assert result["tool"] == "extract_paper_insights"
        assert "error" not in result
        assert result["arxiv_id"] == "1706.03762"
        assert set(result["insights_requested"]) == {"contributions", "methodology", "limitations"}
        assert len(result["items"]) == 1

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_specific_insights(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["datasets", "future_work"],
        )

        assert "error" not in result
        assert set(result["insights_requested"]) == {"datasets", "future_work"}
        assert set(result["insights_found"]) == {"datasets", "future_work"}

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_contributions_extracted(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["contributions"],
        )

        summary = result["items"][0]["summary"]
        assert "ĐÓNG GÓP CHÍNH" in summary

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_limitations_extracted(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["limitations"],
        )

        summary = result["items"][0]["summary"]
        assert "HẠN CHẾ" in summary

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_methodology_extracted(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["methodology"],
        )

        summary = result["items"][0]["summary"]
        assert "PHƯƠNG PHÁP" in summary

    def test_invalid_arxiv_url(self) -> None:
        result = extract_insights_mod.extract_paper_insights(arxiv_url="invalid")

        assert "error" in result
        assert result["tool"] == "extract_paper_insights"

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_invalid_insight_names_fallback_to_defaults(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["nonexistent_thing", "another_fake"],
        )

        assert "error" not in result
        assert set(result["insights_requested"]) == {"contributions", "methodology", "limitations"}

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_all_five_insights(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(
            arxiv_url="1706.03762",
            insights_needed=["contributions", "methodology", "limitations", "datasets", "future_work"],
        )

        assert "error" not in result
        assert len(result["insights_found"]) == 5
        summary = result["items"][0]["summary"]
        assert "ĐÓNG GÓP CHÍNH" in summary
        assert "PHƯƠNG PHÁP" in summary
        assert "HẠN CHẾ" in summary
        assert "TẬP DỮ LIỆU" in summary
        assert "HƯỚNG PHÁT TRIỂN" in summary


# ===========================================================================
# TEST: Output format consistency (chung cho cả 3 tools)
# ===========================================================================
class TestOutputFormatConsistency:
    """Kiểm tra output format nhất quán giữa 3 tools — phù hợp với format tool."""

    @patch.object(paper_summary_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_summary_output_has_items(self, mock_dl: MagicMock) -> None:
        result = paper_summary_mod.summarize_paper(arxiv_url="1706.03762")
        self._assert_valid_output(result)

    @patch.object(compare_papers_mod, "_download_and_extract", side_effect=_fake_download_dispatch)
    def test_compare_output_has_items(self, mock_dl: MagicMock) -> None:
        result = compare_papers_mod.compare_papers(arxiv_urls=["1706.03762", "1810.04805"])
        self._assert_valid_output(result)

    @patch.object(extract_insights_mod, "_download_and_extract", side_effect=_fake_download_paper1)
    def test_insights_output_has_items(self, mock_dl: MagicMock) -> None:
        result = extract_insights_mod.extract_paper_insights(arxiv_url="1706.03762")
        self._assert_valid_output(result)

    def _assert_valid_output(self, result: dict[str, Any]) -> None:
        """Mỗi tool output phải có 'tool', 'items', và items phải có title/url/source/summary."""
        assert "tool" in result
        assert "items" in result, f"Missing 'items' in result: {result}"
        assert isinstance(result["items"], list)
        assert len(result["items"]) >= 1
        for item in result["items"]:
            assert "title" in item
            assert "url" in item
            assert "source" in item
            assert "summary" in item
