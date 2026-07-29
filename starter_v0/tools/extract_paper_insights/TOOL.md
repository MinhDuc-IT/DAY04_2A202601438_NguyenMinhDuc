---
name: extract_paper_insights
track: bonus
kind: live_api
provider: arXiv API
requires_env: [ARXIV_USER_AGENT]
inputs: [arxiv_url, insights_needed]
outputs: [items, insights_found]
side_effect: false
---
# extract_paper_insights

Trích xuất các thông tin phân tích cốt lõi của một bài báo khoa học:
đóng góp chính (contributions), phương pháp (methodology), hạn chế
(limitations), tập dữ liệu (datasets), và hướng phát triển (future_work).
Mỗi phần được trích xuất riêng biệt bằng regex-based section parsing.
