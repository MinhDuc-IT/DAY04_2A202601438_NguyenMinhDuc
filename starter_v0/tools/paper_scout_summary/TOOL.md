---
name: paper_scout_summary
track: bonus
kind: local_formatter
provider: none
requires_env: []
inputs: [paper_text, arxiv_id, title, max_bullets]
outputs: [methods, results, limitations]
side_effect: false
requires_confirmation: false
---

Tool này trích xuất nhanh (heuristic) phần *Method* và *Results* từ `paper_text` (text tóm tắt/excerpt do `paper_text` tool trả về từ PDF).

Output dự kiến:
- `methods`: list[str] dạng bullet
- `results`: list[str] dạng bullet
- `limitations`: list[str] (có thể rỗng nếu không tìm thấy)

Gợi ý: nếu không thấy dấu hiệu rõ ràng trong excerpt, tool sẽ fallback sang các câu “liên quan” theo keyword.

