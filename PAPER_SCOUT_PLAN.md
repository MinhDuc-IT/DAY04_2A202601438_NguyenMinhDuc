| Tên | Mã học viên |
|---|---|
| System Prompt (Role 1) | TBD |
| Eval (Role 2) | TBD |
| Tools (Role 3) | TBD |
| UI/UX (Role 4) | TBD |

## Paper Scout Lab Plan (Day04 Lab v2)

Mục tiêu: build research agent để

1. tìm paper (arXiv),
2. đọc nội dung,
3. tóm tắt _method_ + _results_,
   trong khung lab: evidence-driven tool routing, eval loop v0 -> v1/v2/v3, thêm tool mới, viết 10 case group eval, và UI demo có tool trace + transcript.

---

## Phần việc tổng thể (sequence chạy bắt buộc)

1. Setup + preflight provider
   - Chạy từ `starter_v0/`.
   - `python scripts/preflight_provider.py --provider openrouter` (hoặc provider bạn dùng).

2. Baseline `v0` (không đổi base eval)
   - `python run_eval.py --provider openrouter --version v0 --suite base --eval-cases data/eval_base.json`
   - Lưu và xem run JSON để biết fail ở routing/args/boundary/missing info.

3. Xây “Paper scout tool pipeline”
   - Topic -> `papers` -> `clarify` chọn arXiv id/url -> `paper_text` -> tool mới `paper_scout_summary` -> `format`.

4. Implement tool mới + smoke test tool mới (bắt buộc)
   - Tạo `tools/<tool_name>/TOOL.md` + `tool.py`
   - Đăng ký trong `tools/__init__.py`
   - Khai báo trong `artifacts/tools.yaml`
   - Smoke test tool mới bằng gọi trực tiếp qua `TOOL_FUNCTIONS`.

5. 3 vòng tối ưu `v1`, `v2`, `v3` (chỉ sửa 1 giả thuyết mỗi lần)
   - Mỗi lần chỉ sửa `artifacts/system_prompt.md` và/hoặc `artifacts/tools.yaml`.
   - Trước mỗi version: chỉnh đúng 1 giả thuyết.
   - Chạy base eval:
     - `python run_eval.py --provider openrouter --version v1 --suite base --eval-cases data/eval_base.json`
     - `python run_eval.py --provider openrouter --version v2 --suite base --eval-cases data/eval_base.json`
     - `python run_eval.py --provider openrouter --version v3 --suite base --eval-cases data/eval_base.json`
   - Mỗi lần chạy xong: cập nhật `artifacts/version_log.csv`.

6. Viết group eval cases (đúng 10 case)
   - Sửa `starter_v0/data/eval_group.json`: 5 single-turn + 5 multi-turn.
   - Mỗi case: `id`, `phase: "B"`, `failure_type`, `expect` (`tool_calls` hoặc `no_tool`), và `metadata.what_it_tests`.

7. Chạy group eval (bắt bằng evidence)
   - `python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json`

8. Chat live + transcript
   - `python chat.py --provider openrouter --version v3`
   - Test ít nhất 3 lượt: (a) discovery topic, (b) thiếu info -> hỏi lại, (c) cung cấp arXiv id -> đọc + tóm tắt.

9. UI/UX demo + hoàn thiện `artifacts/REPORT.md`
   - Phần A: xong trước deadline (16:30).
   - Phần B: hoàn thiện sau.

---

## Chiến lược viết eval ổn định (tránh phụ thuộc arXiv id động)

- Discovery theo topic:
  - Expect chủ yếu: `papers(...)`.
  - Nếu cần đọc full text: dùng `clarify` để user chọn arXiv id/url, để tránh expect `paper_text` với id không chắc.

- Case đọc full text:
  - Cho user cung cấp arXiv id/url cố định (deterministic), expect `paper_text(arxiv_url=...)` và tool mới `paper_scout_summary(...)`.

---

## Chia việc theo 4 role

### Role 1: System Prompt (chịu trách nhiệm routing + boundary + multi-turn)

**Input cần dùng**

- `starter_v0/artifacts/system_prompt.md`
- `starter_v0/artifacts/tools.yaml`
- Contract tool: core vs bonus, và boundary `clarify`.

**Việc cần làm**

1. Viết rule routing cho paper scout:
   - “find/search paper” + topic/keyword -> gọi `papers`.
   - “read/summarize” nhưng thiếu arXiv id/url -> gọi `clarify` (response_type `text` hoặc `choice`).
   - Khi có arXiv id/url -> gọi `paper_text` rồi gọi tool mới `paper_scout_summary`.
   - Luôn ensure agent ưu tiên “không tự đoán” khi thiếu định danh.

2. Multi-turn handling:
   - Carryover tham số user đưa ra (vd `max_results`, giới hạn độ dài tóm tắt) nếu schema tool hỗ trợ.
   - Correction: user đổi arXiv id/title -> pipeline cập nhật lại `paper_text`.
   - Switch tool: topic khác -> chạy lại `papers` (nếu cần).

3. Boundary:
   - Giữ nguyên boundary kiểu nhạy cảm (nếu có hành động publish/send) bằng `clarify(response_type="yes_no")`.
   - Với paper scout thường không cần action, nhưng prompt vẫn giữ nguyên nguyên tắc chung từ lab.

**Deliverable**

- Bản cập nhật `starter_v0/artifacts/system_prompt.md` sẵn sàng cho vòng v1/v2/v3.

---

### Role 2: Eval (chịu trách nhiệm viết 10 case group eval + đảm bảo deterministic)

**Input cần dùng**

- `starter_v0/data/eval_group.json` (trống có chủ đích)
- Schema mẫu: `starter_v0/samples/eval_group.schema.example.json`
- Hiểu tool names + args của team (đặc biệt tool mới).

**Việc cần làm**

1. Viết đúng **10 cases**:
   - 5 single-turn (dùng `query`)
   - 5 multi-turn (dùng `turns`, phần tử cuối là user turn được chấm)
   - `phase: "B"`
   - `failure_type` thuộc: `wrong_tool`, `wrong_arg_value`, `wrong_boundary`, `unnecessary_tool`, `out_of_scope`, `missing_info`
   - `expect` gồm:
     - `tool_calls`: danh sách tool dự kiến agent gọi (kèm args subset)
     - hoặc `no_tool: true`
   - `metadata.what_it_tests`: mô tả ngắn gọn mục tiêu đánh giá.

2. Áp dụng chiến lược deterministic:
   - Topic discovery cases: expect `papers(...)` và có thể expect `clarify(...)` để chọn paper.
   - Read full text cases: user cung cấp arXiv id/url cố định -> expect `paper_text(arxiv_url=...)`.
   - Case “missing info”: expect `clarify(...)` thay vì gọi `paper_text`.
   - Out-of-scope/meta: expect `no_tool`.

3. Đảm bảo tool mới `paper_scout_summary` có mặt đúng ở những case read-based (vì đây là phần core paper scout value).

**Deliverable**

- Cập nhật `starter_v0/data/eval_group.json` (đủ 10 case, chạy pass ở vòng group eval sau khi v1/v2/v3 ổn).

---

### Role 3: Tools (chịu trách nhiệm tạo tool mới + đăng ký + smoke test)

**Input cần dùng**

- `starter_v0/tools/*` (đặc biệt `papers` và `paper_text` để hiểu output format)
- `starter_v0/tools/__init__.py`
- `starter_v0/artifacts/tools.yaml`
- Guide: `TOOL-SETUP.md`

**Việc cần làm**

1. Tạo tool mới để trích _Method/Results_ từ `paper_text`:
   - Tạo thư mục `starter_v0/tools/paper_scout_summary/` (tên tùy chọn, miễn nhất quán)
   - Thêm `TOOL.md`:
     - Frontmatter: name, track (bonus hoặc core), kind (`local_formatter`/`local_knowledge`), inputs/outputs, requires_confirmation=false
   - Thêm `tool.py`:
     - Nhận input theo schema đã chọn
     - Parse/heuristic để trích method/results (có thể dùng regex + section detection theo cấu trúc phổ biến, hoặc extract từ text theo pattern)
     - Trả về cấu trúc dict nhất quán để `format` hiển thị dễ

2. Đăng ký tool mới:
   - Update `starter_v0/tools/__init__.py` (registry `TOOL_FUNCTIONS`)
   - Update `starter_v0/artifacts/tools.yaml` (declaration schema đúng với tool.py)

3. Smoke test tool mới (bắt buộc theo guide):
   - Gọi trực tiếp qua `TOOL_FUNCTIONS` với input demo an toàn
   - PASS khi: registry tìm thấy tool, args hợp lệ, và output có đủ fields quan trọng.

**Deliverable**

- Tool mới hoạt động + có declaration đồng bộ (không mismatch name/schema).

---

### Role 4: UI/UX (chịu trách nhiệm UI demo: tool trace + transcript + digest format)

**Input cần dùng**

- `starter_v0/chat.py` (để tái sử dụng agent loop và lưu transcript)
- `starter_v0/chức năng logging` theo transcript/run

**Việc cần làm**

1. Chọn framework mặc định theo guide: Streamlit.
   - Nếu dùng Streamlit:
     - thêm `streamlit>=1.30.0` vào `starter_v0/requirements.txt`
     - tạo `starter_v0/app.py`

2. UI flow chính:
   - Input: `topic` hoặc `arxiv_id/url`
   - Tùy chọn: `top_k`, `focus` (methods/results), `max_summary_chars` (nếu tool/schema có)
   - Nút chạy: gọi `run_model_tool_loop` giống trong `chat.py`
   - Hiển thị:
     - Request + final response
     - Tool trace theo từng round: tool name, args, result/error
     - Transcript (để demo bằng evidence)

3. Rendering digest “paper scout”:
   - Method: bullets
   - Results: bullets
   - (Optional) Limitations/caveats
   - Nếu tool mới trả structure, UI chỉ việc format ra markdown/sections.

4. Evidence cho demo:
   - Cho thấy cùng một scenario chạy qua nhiều version (v0 -> v1/v2/v3) để thấy cải thiện rõ ràng (đặc biệt ở routing paper flow).

**Deliverable**

- UI chạy được local và có tool trace/transcript rõ ràng.
