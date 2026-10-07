# Tiến độ lab Agent Tools & Skills (D05): ghi chú để làm tiếp

Cập nhật: 2026-10-07 19:08. Đề: `exercise-block-1.html` và `exercise-block-2.html` (pub.nndkhoa9.win/agentic-ai-engineering/d05-tool-use-skill-use/).
Nguyên tắc: **bám sát đề, không thêm bớt**. Làm trên bản sao, giữ nguyên project mẫu.

## Môi trường
- Model: **Groq `qwen/qwen3.8-27b`** (`OPENAI_BASE_URL=https://api.groq.com/openai/v1`). Gemini 3 bị lỗi `thought_signature`, Claude API hết credit.
- `.env` (không nộp) có ở: `stage-00-chat`, `stage-02-skills-block1`, `stage-03-bash-block2`, `stage-04-script-skill-block2`.
- Windows: `uv` nằm ở `C:\Users\Acer\.local\bin`. Nếu terminal không nhận `uv`, chạy `$env:Path = "C:\Users\Acer\.local\bin;$env:Path"`.
- **Block 2 bắt buộc chạy trong WSL** (Ubuntu, user `acer`). Mỗi terminal mới:
  ```bash
  export UV_PROJECT_ENVIRONMENT=$HOME/.venv-agent-lab
  cd /mnt/c/UIT/Agentic/agent-tools-skills-lab/stage-04-script-skill-block2
  uv run streamlit run app.py --server.port 8505
  ```
  Stage 03 chạy ở port 8504.
- Root `pyproject.toml` có thêm 4 bản sao trong `members`, kèm `uv.lock`.

## Block 1: XONG ✅
- Code: `stage-01-files-block1`, `stage-02-skills-block1`. Đã thêm tool `list_files` (`tools/files.py`, `tools/__init__.py`, `agent.py`) và skill `refund-policy`. `prompts.py` và `config.py` giữ bản gốc. Test: 49 và 58 passed.
- Bằng chứng: `block1/analysis.md` (đầy đủ), ảnh trong `block1/screenshots/`.
- Trace chính thức (stage-02-skills-block1/traces):
  - A: `20261007-180105_8b284404`
  - B sau khi đổi tên: `20261007-180332_47daef9a`
  - Thiếu thông tin: `20261007-180549_70ca2cc6`
- Stage 00: `stage-00-chat/traces/20261007-173247_9bc03040`
- File chính sách ở stage 02 workspace hiện **đang mang tên mới** (`cs-hoan-tien-cu.md`, `cs-hoan-tien-moi.md`). Muốn trả về tên gốc thì chạy `uv run python reset_workspace.py`.

## Block 2: đang làm
- Code xong: `stage-03-bash-block2` (chỉ thêm `workload.csv`) và `stage-04-script-skill-block2`:
  - `check_csv.py`: thêm `--max-hours`, `hours_by_owner`, `overloaded_owners`, `excluded_rows`.
  - `SKILL.md` và `report-template.md` (bản rút gọn 978 byte), đã đồng bộ sang `fixtures/`.
  - Test: 74 passed, kể cả trong WSL.
- JSON chạy script trực tiếp: `block2/results/` (ngưỡng 8, ngưỡng 9, trường hợp biên ngưỡng 0, `errors.txt`).
- Kết quả live đã ghi trong `block2/analysis.md`:
  - Stage 03 ✅ (Lan = 14, cộng trùng T02): trace `stage-03-bash-block2/traces/20261007-184125_1b89c8f5`
  - Stage 04 ngưỡng 8, lần 1 bị cắt báo cáo (template cũ dài): `184609_5b265cfb`. Lần 2 không hợp lệ do lỗi đồng bộ file: `185450_4b3f1383`
  - Stage 04 **ngưỡng 8 ✅**: `20261007-190101_86948ad2`, báo cáo `block2/results/agent-report-max8.md`
  - Stage 04 **ngưỡng 9 ✅**: `20261007-190437_10675312`, báo cáo `block2/results/agent-report-max9.md`

### CÒN LẠI
1. **Thiếu ngưỡng**: Cuộc trò chuyện mới, gửi *"Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải."*. Mong đợi agent hỏi ngưỡng. Ghi vào dòng "Thiếu ngưỡng" của bảng Stage 04 trong `block2/analysis.md`.
2. **File không tồn tại**: ví dụ *"Kiểm tra data/khong-co.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/khong-co.md."*. Mong đợi script exit 1 (stderr), agent báo không phân tích được, không bịa số liệu. Ghi vào dòng "File không tồn tại".
3. Rà lại `block2/analysis.md` (mục 4, câu hỏi cuối bài, đã có bản nháp).
4. Trước khi nộp: không nộp `.env`. Thu hồi các API key đã lộ trong chat (Gemini, Claude, Groq).

## Lưu ý cho Claude khi làm tiếp
- Đọc trace: tải bằng `device_stage_files` rồi tóm tắt bằng python (các event `tool_started` và `tool_finished`). Trace không lưu câu trả lời cuối, nên xin người dùng ảnh và nguyên văn câu trả lời.
- Khi ghi file về máy: **chép xong rồi mới `device_commit_files`, không chạy hai việc song song** (đã từng gây ghi đè bản cũ). Nên commit với `force: true`, sau đó kiểm tra kích thước file bằng `device_list_dir`.
- Không ghi được `.env` qua công cụ. Khi cần, đưa lệnh PowerShell để người dùng tự chạy.
