---
name: compare_papers
track: bonus
kind: live_api
provider: arXiv API
requires_env: [ARXIV_USER_AGENT]
inputs: [arxiv_urls, aspect]
outputs: [items, papers_compared]
side_effect: false
---
# compare_papers

So sánh trực tiếp phương pháp, kết quả, tập dữ liệu, hoặc hạn chế
giữa 2 hoặc nhiều bài báo khoa học trên arXiv. Tải PDF của mỗi bài,
trích xuất phần liên quan đến khía cạnh cần so sánh, và trả về dữ liệu
có cấu trúc để LLM phân tích đối chiếu.
