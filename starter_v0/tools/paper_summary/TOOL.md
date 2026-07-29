---
name: paper_summary
track: bonus
kind: live_api
provider: arXiv API
requires_env: [ARXIV_USER_AGENT]
inputs: [arxiv_url, focus_area, length]
outputs: [items, sections_found]
side_effect: false
---
# paper_summary

Tóm tắt nội dung chính của một bài báo khoa học trên arXiv.
Tải PDF, trích xuất text, và phân tách theo các phần (abstract,
methodology, results, conclusion). Hỗ trợ tập trung vào một
phần cụ thể hoặc tóm tắt toàn bộ.
