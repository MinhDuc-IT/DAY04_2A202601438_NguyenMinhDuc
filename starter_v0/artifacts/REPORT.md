# Day 04 Lab v2 Report — Research Paper Scout

> File này gồm 2 phần:
> - **PHẦN A — Giới thiệu agent**: tóm tắt nhanh để team khác hiểu agent, tool, và cách thử.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng version, failure, eval, chat dựa trên log thật.

## Team

- **Team:** Research Paper Scout
- **Members:**
  | Tên | Mã học viên | Role |
  |---|---|---|
  | Ngô Huy Hoàn | 2A202601925 | tools |
  | Ngô Văn Kiệt | 2A202601524 | eval |
  | Phạm Văn Vinh | 2A202601988 | system prompt |
  | Nguyễn Minh Đức | 2A202601438 | UI/UX |
- **Provider/model:** `openrouter` / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent hỗ trợ **tìm kiếm tin tức / mạng xã hội / web**, **đọc URL**, và **khám phá bài báo arXiv** — tóm tắt phương pháp–kết quả, so sánh nhiều paper, hoặc trích xuất insights có cấu trúc. Agent tuân thủ policy xác nhận trước hành động ghi (gửi Telegram) và hỏi lại khi thiếu thông tin thiết yếu.

**Link dùng thử (truy cập được trong showdown):**

> Chạy local: `cd starter_v0 && .venv\Scripts\activate && streamlit run app.py`  
> URL: `http://localhost:8501` (demo trực tiếp trên máy trình chiếu)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin hoặc cần xác nhận | không |
| timeline | Lấy bài đăng gần đây của một tài khoản X/Twitter | không |
| social_search | Tìm kiếm trên mạng xã hội theo từ khóa | không |
| lookup | Tra cứu web (general / news, có timeframe) | không |
| fetch | Lấy nội dung từ một URL | không |
| format | Trình bày dữ liệu đã có thành digest có cấu trúc | không |
| send | Gửi văn bản (cần xác nhận trước) | không |
| policy | Tìm trong tài liệu nội bộ | không |
| papers | Tìm bài báo khoa học trên arXiv | không (built-in) |
| paper_text | Lấy nội dung text thô từ PDF arXiv | không (built-in) |
| **paper_summary** | Tóm tắt abstract / methodology / results / conclusion | **có** |
| **compare_papers** | So sánh 2+ paper theo methodology, dataset, results, limitations | **có** |
| **extract_paper_insights** | Trích xuất contributions, limitations, datasets, future work | **có** |

## A3. Câu hỏi mẫu để thử

1. *Find 3 arXiv papers about retrieval augmented generation evaluation, then read one paper and summarize method/results.*
2. *So sánh phương pháp của hai paper arXiv 2309.15217v2 và 2411.18583v1.*
3. *Trích xuất contributions và limitations từ paper https://arxiv.org/abs/2309.15217v2.*
4. *Tìm tin AI mới nhất trong tuần qua trên web.*
5. *Đăng bản tin này lên Telegram giúp mình.* (kiểm tra agent có hỏi xác nhận `yes_no` trước khi gửi)

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Paper Scout — tìm + tóm tắt RAG eval | `papers(max_results=3)` → `paper_summary(arxiv_url=2309.15217v2, focus_area=methodology/results)` | v0–v2: prompt mơ hồ; v3: prompt đầy đủ → output có cấu trúc Method/Results rõ hơn | `transcripts/v3_openrouter_20260729T164050859715.transcript.json` |
| Xác nhận trước khi gửi Telegram | `clarify(response_type=yes_no)` — **không** gọi `send` ngay | v0 gọi `send` trực tiếp; v3 gọi `clarify` nhưng còn sai `response_type` | `runs/v0_B_base_openrouter_20260729T173758857322.json` (R12 FAIL) vs `runs/v3_B_base_openrouter_20260729T174141379022.json` (R12 FAIL nhẹ hơn) |
| Thiếu URL → hỏi lại | `clarify(question=…)` | v0 gọi `fetch` khi chưa có URL; v3 routing đúng | v0 R11 vs v3 R11 (PASS) |
| Out of scope — viết code | Không gọi tool | v0/v1 gọi tool sai; v3 từ chối đúng | v0 R14 FAIL → v3 R14 PASS |
| Song song web + tweets | `lookup` + `social_search` cùng lượt | v0 sai args (`topic`, `query`); v3 đạt trên hầu hết case parallel | v0 R13 FAIL; v3 R13 PASS |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases = 0`, `measured_cases = total_cases` (20 case, suite `base`). Tất cả run dưới đây thỏa điều kiện.

## B1. Version evidence

Nguồn: `artifacts/version_log.csv` (UI demo) và `runs/*_B_base_openrouter_20260729T17*.json` (eval chính thức).

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline: prompt mơ hồ (`versions/v0`), `tools.yaml` chưa có tool paper mới | Điểm xuất phát trên base suite | case_accuracy | — | 0.70 | `runs/v0_B_base_openrouter_20260729T173758857322.json` |
| v1 | Thêm 3 tool mới (`paper_summary`, `compare_papers`, `extract_paper_insights`); prompt vẫn baseline | Tool paper không cải thiện base routing Twitter/web | case_accuracy | 0.70 | 0.65 | `runs/v1_B_base_openrouter_20260729T173851815992.json` |
| v2 | Cải thiện prompt (routing Twitter/web/news, missing info); giữ paper tools | Prompt tốt hơn → routing_accuracy tăng | tool_routing_accuracy | 0.75 | 0.95 | `runs/v2_B_base_openrouter_20260729T174020894681.json` |
| v3 | Prompt đầy đủ (boundary confirm, parallel tools, out-of-scope); tools hoàn chỉnh | Policy đầy đủ → case_accuracy cao nhất | case_accuracy | 0.70 (v0) | **0.90** | `runs/v3_B_base_openrouter_20260729T174141379022.json` |

**Tóm tắt metric theo version (suite base, 20 cases):**

| Version | case_accuracy | tool_routing_accuracy | argument_accuracy |
|---|---:|---:|---:|
| v0 | 0.70 | 0.75 | 0.70 |
| v1 | 0.65 | 0.75 | 0.65 |
| v2 | 0.70 | 0.95 | 0.70 |
| v3 | **0.90** | **0.95** | **0.90** |

**UI demo transcripts** (cùng scenario Paper Scout, artifact hash có thể khác eval snapshots):  
`transcripts/v0_…172524….json` → `v1_…172653….json` → `v2_…172727….json` → `v3_…164050….json`

## B2. Failure analysis

### v0 — 6 case FAIL (baseline)

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send` | Gọi tool khi câu hỏi ngoài phạm vi | Thêm rule out-of-scope trong `system_prompt.md` |
| R10_missing_handle | missing_info | `timeline` | Thiếu handle nhưng đoán thay vì `clarify` | Policy missing identifier → `clarify` |
| R11_missing_url | missing_info | `fetch` | Thiếu URL nhưng vẫn fetch | Cùng policy missing info |
| R12_confirm_before_send | wrong_boundary | `send` | Gửi Telegram không xác nhận | Confirmation boundary + `clarify(yes_no)` |
| R13_parallel_web_and_tweets | wrong_tool | `lookup`, `social_search` | Sai `query`/`topic` args | Mô tả args rõ trong prompt + `tools.yaml` |
| R14_out_of_scope_coding | out_of_scope | `send` | Gọi tool cho yêu cầu viết code | Out-of-scope direct answer |

### v3 — 2 case FAIL (còn lại)

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R12_confirm_before_send | wrong_boundary | `clarify(response_type=text)` | Đã hỏi nhưng dùng `text` thay vì `yes_no` | Nhấn mạnh trong prompt: Telegram → `yes_no` trước, hỏi nội dung sau |
| M06_switch_tool | wrong_tool | `lookup`, `social_search` (extra) | User đổi sang web-only nhưng vẫn gọi `social_search` | Thêm rule “latest instruction overrides” + chỉ gọi tool phù hợp turn mới |

## B3. Team eval cases

File `data/eval_group.json` — **10 case Paper Scout** (Ngô Văn Kiệt — eval):

- 5 single-turn (`query`): G01–G05
- 5 multi-turn (`turns`): G06–G10

Chạy: `python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json`

### Single-turn (G01–G05)

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_papers_routing | Tìm paper arXiv, trích `max_results=5` | `papers(max_results=5)` | *(chưa chạy)* |
| G02_paper_summary_focus | Tóm tắt methodology khi đã có URL | `paper_summary(arxiv_url, focus_area=methodology)` | *(chưa chạy)* |
| G03_compare_papers | So sánh methodology 2 paper | `compare_papers(aspect=methodology)` | *(chưa chạy)* |
| G04_extract_insights | Trích contributions + limitations | `extract_paper_insights(insights_needed=[contributions, limitations])` | *(chưa chạy)* |
| G05_missing_arxiv_url | Thiếu URL/ID paper | `clarify(response_type=text)` | *(chưa chạy)* |

### Multi-turn (G06–G10)

| Case ID | What It Tests | Expected Tool/Behavior (latest turn) | Result |
|---|---|---|---|
| G06_clarify_then_summary | Có URL rồi mới tóm tắt methodology chi tiết | `paper_summary(focus_area=methodology, length=detailed)` | *(chưa chạy)* |
| G07_scout_then_summarize | Ngữ cảnh scout trước, turn cuối tóm tắt paper cụ thể | `paper_summary(arxiv_url)` — không gọi `papers` lại | *(chưa chạy)* |
| G08_correction_focus_area | Sửa focus sang results + detailed | `paper_summary(focus_area=results, length=detailed)` | *(chưa chạy)* |
| G09_switch_to_insights | Bỏ compare, chuyển extract limitations | `extract_paper_insights(insights_needed=[limitations])` | *(chưa chạy)* |
| G10_correction_max_results | Carry chủ đề, sửa số lượng 10→3 | `papers(max_results=3)` | *(chưa chạy)* |

## B4. Live chat evidence

Scenario chính: *"Find 3 arXiv papers about retrieval augmented generation evaluation, then read one paper and summarize method/results."*

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Paper Scout (1 turn) | v0 | `papers(query=…, max_results=3)` → `paper_summary(arxiv_url=2309.15217v2)` | `transcripts/v0_openrouter_20260729T172524491019.transcript.json` | answered — 3 papers + tóm tắt Ragas |
| Paper Scout (1 turn) | v1 | Cùng pipeline | `transcripts/v1_openrouter_20260729T172653501237.transcript.json` | answered — wording khác, tool giống |
| Paper Scout (1 turn) | v2 | Cùng pipeline | `transcripts/v2_openrouter_20260729T172727503925.transcript.json` | answered — output ngắn hơn |
| Paper Scout (1 turn) | v3 | `papers` → `paper_summary`; prompt_hash khác v0–v2 | `transcripts/v3_openrouter_20260729T164050859715.transcript.json` | answered — Method/Results có cấu trúc |
| Confirm Telegram | v0 eval | `send` (sai) | `runs/v0_…173758….json` R12 | FAIL |
| Confirm Telegram | v3 eval | `clarify(response_type=text)` | `runs/v3_…174141….json` R12 | FAIL (gần đúng) |
| Switch tool multi-turn | v3 eval | `lookup` + extra `social_search` | `runs/v3_…174141….json` M06 | FAIL |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên — `paper_summary` | `transcripts/v3_openrouter_20260729T164050859715.transcript.json` | Tải PDF arXiv 2309.15217v2, tách sections, trả về Method + Results | Cần `ARXIV_USER_AGENT`; PDF lớn có thể timeout — giới hạn `max_pages` |
| Bonus: tool mới thứ 2 — `compare_papers` | `tools/compare_papers/TOOL.md`, khai báo `artifacts/tools.yaml` | So sánh methodology/dataset/results/limitations giữa 2+ URL | Phụ thuộc chất lượng trích xuất PDF; cần đủ `arxiv_urls` |
| Bonus: tool mới thứ 3 — `extract_paper_insights` | `tools/extract_paper_insights/TOOL.md` | Trích contributions, limitations, datasets, future_work có cấu trúc | Không thay thế đọc full paper khi cần trích dẫn chính xác |
| Optional built-in — `papers` | Cùng transcript v3 | Tìm 3610 kết quả, trả top 3 relevance cho query RAG eval | Rate limit arXiv API |
| Optional built-in — `clarify` / `lookup` / `social_search` | `runs/v3_B_base_openrouter_20260729T174141379022.json` | 18/20 case PASS trên base suite | R12/M06 cần tinh chỉnh prompt thêm |

## B6. Reflection

- **Fix thuộc `system_prompt.md`:**
  - Out-of-scope → trả lời trực tiếp, không gọi tool (v0 R08/R14 → v3 PASS).
  - Missing identifier → `clarify` thay vì đoán (v0 R10/R11 → v3 PASS).
  - Confirmation boundary cho Telegram → `clarify(yes_no)` trước `send` (v0 R12 gọi `send` → v3 đã `clarify` nhưng còn sai `response_type`).
  - Parallel web+tweets và “latest instruction overrides” (M06 vẫn FAIL ở v3).

- **Fix thuộc `tools.yaml`:**
  - Thêm mô tả + enum rõ cho `paper_summary`, `compare_papers`, `extract_paper_insights`.
  - Làm rõ `lookup.topic`, `social_search.search_type`, `clarify.response_type` để model chọn args đúng (R13 ở v0).

- **Cần review thủ công:**
  - Tool execution thành công nhưng nội dung tóm tắt paper có đủ chính xác không (eval chỉ chấm routing/args).
  - UI transcripts v0–v2 từng dùng cùng artifact hash — cần re-record sau khi snapshot `versions/v0..v2` đã tách biệt.

- **Cải thiện tiếp:**
  - Chạy suite `group` trên `eval_group.json` (v3) và cập nhật cột Result ở B3.
  - Sửa R12 (`yes_no` cho mọi Telegram post) và M06 (bỏ `social_search` khi user chuyển sang web-only).
  - Thêm demo `compare_papers` / `extract_paper_insights` trên UI để showcase đủ 3 tool mới.
