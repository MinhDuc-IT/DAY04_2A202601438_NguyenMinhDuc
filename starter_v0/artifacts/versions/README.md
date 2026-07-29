# Artifact version snapshots

Mỗi thư mục `v0/`, `v1/`, `v2/`, `v3/` chứa snapshot của:
- `system_prompt.md`
- `tools.yaml`

UI (`app.py`) load đúng snapshot khi bạn chọn version.

## Workflow khuyến nghị

Sau mỗi vòng tối ưu (trước khi chạy eval version tiếp theo), copy file đã sửa vào đúng thư mục:

```cmd
copy artifacts\system_prompt.md artifacts\versions\v1\system_prompt.md
copy artifacts\tools.yaml artifacts\versions\v1\tools.yaml
```

Hoặc chỉ copy file bạn đã thay đổi (prompt hoặc tools).

## Lưu ý

- `artifacts/system_prompt.md` và `artifacts/tools.yaml` ở root là bản **đang active** (dùng cho `run_eval.py` / `chat.py` mặc định).
- Snapshot trong `versions/` dùng để so sánh và demo trên UI giữa các version.
