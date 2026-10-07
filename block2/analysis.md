# Block 2: Kiểm tra quá tải theo người

## 1. Thay đổi đã làm

Làm trên bản sao, giữ nguyên project mẫu:

| Bản sao | Tạo từ | Ghi chú |
|---|---|---|
| `stage-03-bash-block2/` | `stage-03-bash/` | Chỉ thêm dữ liệu `workload.csv`, không sửa code |
| `stage-04-script-skill-block2/` | `stage-04-script-skill/` | Sửa skill `csv-quality`, thêm dữ liệu và test |

Hai bản sao được thêm vào `members` trong `pyproject.toml` gốc (kèm `uv.lock`) và đổi `name` trong `pyproject.toml` riêng.

**Giới hạn của đề được giữ nguyên:**
- Không thêm tool, không sửa `agent.py`. `tools/`, `prompts.py`, `config.py` và `app.py` giống hệt bản gốc.
- Không viết cố định ngưỡng 8 hay kết quả trong script và skill. Test `test_csv_quality_skill_and_script_do_not_hardcode_threshold_or_results` kiểm tra điều này.
- So với bản gốc, `stage-04-script-skill-block2` chỉ khác ở:
  - `skills/csv-quality/*` (trong `workspace/` và `fixtures/`)
  - `data/workload*.csv`
  - `tests/test_check_csv.py`, `tests/test_agent.py`, `tests/test_skill_catalog.py`

### `scripts/check_csv.py`
Dùng lại phần đọc CSV (`csv.reader(strict=True)`), hàm `parse_hours()` và cách báo lỗi đầu vào (`InputError`, exit 1, stderr) của bản gốc.

- Thêm tham số **bắt buộc `--max-hours`**. Giá trị phải là số hữu hạn, không âm, và được kiểm tra bằng cùng quy tắc `parse_hours()`. Nếu thiếu hoặc sai giá trị, `argparse` ghi lỗi ra stderr với **exit 2**.
- Trong cùng vòng lặp kiểm tra chất lượng, mỗi dòng được gom **tập lý do loại**. Dòng nào không có lý do thì cộng `hours` vào `hours_by_owner[owner]`.
- Thêm 4 trường JSON, các trường cũ giữ nguyên:
  - `max_hours`: ngưỡng nhận từ CLI.
  - `hours_by_owner`: tổng giờ theo owner, sắp theo tên. Chỉ gồm owner có ít nhất một dòng được cộng.
  - `overloaded_owners`: danh sách `{owner, total_hours}` có `total_hours > max_hours`, sắp theo tên.
  - `excluded_rows`: danh sách `{line, task_id, reasons}`, sắp theo dòng. `task_id` rỗng ghi `null`. `reasons` theo thứ tự `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.
- Quy tắc tính:
  - Bỏ khoảng trắng đầu và cuối. Owner phân biệt hoa và thường.
  - Mỗi `task_id` chỉ giữ **lần xuất hiện đầu tiên**: `first_seen` ghi nhận ngay từ lần đầu, kể cả khi dòng đó không hợp lệ.
  - Giá trị 0 là hợp lệ. Dòng trống bị bỏ qua như bản gốc.
- Số nguyên được in là `9` thay vì `9.0`.

### `SKILL.md`
- `description` thêm nhiệm vụ: tính tổng giờ theo người và kiểm tra quá tải theo ngưỡng do người dùng cung cấp.
- Mục **Ngưỡng giờ**:
  - Lấy ngưỡng từ yêu cầu hiện tại và truyền đúng giá trị vào lệnh.
  - **Nếu thiếu ngưỡng thì hỏi lại và dừng.** Không tự chọn ngưỡng mặc định, không dùng ngưỡng từ cuộc trò chuyện cũ.
  - Quá tải khi tổng giờ **lớn hơn** ngưỡng.
- Lệnh chạy có thêm `--max-hours <ngưỡng>`.
- Mục kiểm tra kết quả mô tả các trường JSON mới và ý nghĩa exit code 0, 1, 2.
- Thêm mục **quy tắc tính** để agent giải thích đúng cho người dùng.
- Bỏ quy tắc cũ *"Không tính tổng giờ hay KPI khi còn dữ liệu lỗi"*. Thay bằng: lấy tổng giờ từ JSON và ghi rõ các dòng bị loại không được cộng.

### `references/report-template.md`
Báo cáo gồm: **ngưỡng và người quá tải**, **tổng giờ theo người** (có cột *Vượt ngưỡng?*), **dòng bị loại** (line, task_id, lý do, mô tả), **chất lượng dữ liệu** (các thống kê cũ trên mọi dòng) và **khuyến nghị**.

Template được **rút gọn sau lần chạy 1**. Bản đầu có 2 bảng trùng nhau ("Dòng bị loại" và "Chi tiết lỗi") cùng mục *Đánh giá* riêng, làm báo cáo dài quá giới hạn độ dài đầu ra của model, nên bị cắt (xem mục 3). Bản hiện tại gộp chi tiết lỗi vào bảng *Dòng bị loại* (thêm cột *Mô tả*), thống kê chất lượng viết thành một dòng, và `SKILL.md` yêu cầu báo cáo ngắn gọn, ghi bằng **một** lần `write_file`.

### Dữ liệu
- `data/workload.csv` nằm trong `workspace/` và `fixtures/` của cả stage 03 và stage 04.
- `data/workload-edge.csv` nằm trong stage 04.

## 2. Chạy script trực tiếp

Từ thư mục `stage-04-script-skill-block2`. Output đầy đủ ở `block2/results/`.

| Lệnh | Exit | `hours_by_owner` | `overloaded_owners` | `excluded_rows` |
|---|---|---|---|---|
| `--input workspace/data/workload.csv --max-hours 8` ([JSON](results/workload-max-8.json)) | 0 | `{"Lan": 9, "Minh": 3}` | `[{"owner": "Lan", "total_hours": 9}]` | dòng 5 `invalid_hours`, dòng 6 `duplicate_id`, dòng 7 `missing_owner` |
| `--input workspace/data/workload.csv --max-hours 9` ([JSON](results/workload-max-9.json)) | 0 | `{"Lan": 9, "Minh": 3}` | `[]` (9 không lớn hơn 9) | như trên |
| `--input workspace/data/workload-edge.csv --max-hours 0` ([JSON](results/workload-edge-max-0.json)) | 0 | `{"Minh": 0}` | `[]` | dòng 2 `invalid_hours`, dòng 3 `duplicate_id` (không cộng 5 giờ cho Lan) |
| `--input workspace/data/khong-co.csv --max-hours 8` ([log](results/errors.txt)) | **1** | | | stderr `ERROR: Không đọc được file …` |
| `--input workspace/data/workload.csv` (thiếu ngưỡng, [log](results/errors.txt)) | **2** | | | stderr `the following arguments are required: --max-hours` |

Thống kê chất lượng cũ vẫn tính trên mọi dòng: `row_count` 6, `missing_owner_count` 1, `invalid_hours_count` 1, `duplicate_ids` `["T02"]`.

### Kiểm thử tự động (`uv run pytest`, không cần API key)
- `stage-04-script-skill-block2`: **74 passed** (bản mẫu 61). Test mới trong `tests/test_check_csv.py`:
  - `test_first_occurrence_with_invalid_hours_still_wins_duplicate`: **trường hợp biên theo đề**. Dữ liệu `workload-edge.csv`, ngưỡng 0, kết quả `{"Minh": 0}`, không có Lan, loại dòng 2 và 3.
  - Ngưỡng 8 (Lan quá tải) và ngưỡng 9 (bằng ngưỡng thì không quá tải).
  - Đủ 5 mã lý do theo đúng thứ tự, bỏ khoảng trắng, không gộp owner khác hoa/thường.
  - Thiếu `--max-hours`, hoặc `--max-hours` là `-1`, `nan`, `inf`, `abc`, rỗng: exit khác 0, có stderr, stdout rỗng.
  - File không tồn tại: exit 1. Script không sửa file CSV đầu vào.
  - Các test cũ được cập nhật để truyền `--max-hours`.
- `stage-03-bash-block2`: **48 passed**, giống bản mẫu.
- Ghi chú: `tests/test_bash.py` và luồng agent có tool `bash` cần môi trường POSIX. Trên Windows chạy trong WSL2.

## 3. Kết quả chạy agent (live)

> Chạy trong WSL2 (Ubuntu), môi trường uv riêng `~/.venv-agent-lab`. Model `qwen/qwen3.8-27b` qua Groq (endpoint tương thích OpenAI). Mỗi trường hợp mở cuộc trò chuyện mới, không nhắc tên skill hay script.

### Stage 03: tính tổng giờ bằng Python qua Bash (`stage-03-bash-block2`)
- Câu hỏi: *"Dùng Python qua Bash để tính tổng hours theo owner trong data/workload.csv. Không chỉnh sửa file đầu vào. Cho biết cách xử lý dòng lỗi và task_id trùng."*
- Trace: `stage-03-bash-block2/traces/20261007-184125_1b89c8f5_turn01_112274a5.jsonl`. Gồm 5 model call, 4 tool call, 20 event.
- Ảnh: [`screenshots/stage03-workload.png`](screenshots/stage03-workload.png)

| seq | Tool call | Kết quả |
|---|---|---|
| 4–5 | `read_file data/workload.csv` | Đọc 6 dòng dữ liệu |
| 8–9 | `bash`: script Python viết inline bằng here-doc | **exit 1**: `SyntaxError` do escape `\"TỔNG\"` trong f-string, here-doc bị cắt (*"here-document … delimited by end-of-file"*) |
| 12–13 | `bash`: model tự sửa và chạy lại script | **exit 0**: `(trong) 2`, `Lan 14`, `Minh 3`, `TONG 19`. Dòng bị bỏ: dòng 5 T04 `hours='abc'` |
| 16–17 | `bash`: in `repr` nội dung file | Kiểm tra file không bị sửa |

**Đoạn lệnh quyết định cách cộng** (seq 12):
```python
for i, row in enumerate(csv.DictReader(f), start=2):
    ...
    try:
        hours = float(hrs)
    except ValueError:
        skipped.append(...); continue        # chỉ loại hours không phải số
    total[owner or '(trong)'] += hours       # không kiểm tra task_id trùng, gom owner rỗng vào "(trong)"
```

**Kết quả: Lan = 14 giờ.** Lan bị **cộng trùng dòng 6** (`T02,Lan,5`, lặp lại `task_id` T02 ở dòng 3): 4 (T01) + 5 (T02, dòng 3) + **5 (T02, dòng 6)** = 14. Script không có bước nào loại `task_id` trùng.

**Cách agent xử lý từng loại dòng lỗi** (theo lệnh và theo câu trả lời):

| Dòng | Lỗi | Stage 03 (model tự viết code) | Quy tắc của đề và script Stage 04 |
|---|---|---|---|
| 5 `T04,Minh,abc` | hours không phải số | Bỏ qua ✅ | Loại (`invalid_hours`) ✅ |
| 6 `T02,Lan,5` | `task_id` trùng | **Cộng thêm** ❌. Agent giải thích *"Không dedup, mỗi dòng là một bản ghi"* | Loại (`duplicate_id`) |
| 7 `T05,,2` | owner rỗng | **Gom vào nhóm "(trống)" = 2** ❌ | Loại (`missing_owner`) |
| Các kiểm tra khác | `hours` âm, NaN hoặc Infinity | Không kiểm tra: `float("nan")` và `float("-1")` vẫn được cộng | Loại (`invalid_hours`) |

**Nhận xét:**
- Kết quả tùy vào đoạn code model **tự viết ra trong lần chạy đó**. Lần này model chọn không loại trùng, gom owner rỗng thành một nhóm riêng, và ngay lần chạy đầu đã viết script lỗi cú pháp (seq 9, exit 1) rồi mới tự sửa. Model có nêu phương án loại trùng (Lan = 9) và hỏi lại người dùng, nhưng **kết luận mặc định vẫn là Lan = 14**.
- Quy tắc nghiệp vụ, ví dụ *"mỗi ID chỉ giữ lần đầu"*, không nằm ở đâu cả. Chạy lần khác, hoặc dùng model khác, có thể ra kết quả khác.
- Model tự kiểm tra file không bị sửa (seq 16–17) và **không ghi file đầu vào**, đúng yêu cầu.
- Đây là lý do Stage 04 chuyển quy tắc vào **script có test**: ID trùng, owner rỗng và hours không hợp lệ được xử lý tất định, lần nào cũng ra Lan 9 giờ.

### Stage 04 (`stage-04-script-skill-block2`)

#### Lần chạy 1, ngưỡng 8 (template bản đầu): số liệu đúng, báo cáo bị cắt
- Trace: `stage-04-script-skill-block2/traces/20261007-184609_5b265cfb_turn01_bdb187fe.jsonl` (6 model call, 6 tool call).
- Luồng: `read_file data/workload.csv` và `read_file skills/csv-quality/SKILL.md` → `bash: python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8` (exit 0) song song với `read_file …/report-template.md` → `write_file output/workload.md` **3 lần**.
- Báo cáo ([results/run1-workload-truncated.md](results/run1-workload-truncated.md)) có số liệu đúng:
  - Ngưỡng 8, **Lan 9 giờ vượt ngưỡng**, Minh 3 giờ.
  - Loại dòng 5 `invalid_hours`, dòng 6 `duplicate_id`, dòng 7 `missing_owner`.
- Nhưng cả 3 lần `write_file` đều bị cắt ở cùng một vị trí: nội dung dài 1007 ký tự, khoảng 400 token đầu ra, dừng giữa bảng "Chi tiết lỗi". Đây là giới hạn độ dài đầu ra của model và provider, không phải lỗi của script.
- Cách sửa (chỉ sửa skill): rút gọn template và yêu cầu ghi một lần (xem mục 1). Sau đó chạy lại.

#### Lần chạy 2, ngưỡng 8: không hợp lệ (lỗi đồng bộ file)
- Trace `20261007-185450_4b3f1383_turn01_e1239574.jsonl`. Lúc chạy, template mới **chưa được ghi đúng vào máy** (lỗi khi đồng bộ file), nên agent vẫn đọc template cũ: `read_file` trả 1318 ký tự. Báo cáo bị cắt 6 lần và dừng ở giới hạn `Model call limits exceeded: run limit (8/8)`. Không dùng lần chạy này làm bằng chứng.

#### Kết quả chính thức (template rút gọn)


| Trường hợp | Câu hỏi | Kết quả cần đạt | Trace | Kết quả thực tế |
|---|---|---|---|---|
| Ngưỡng 8 | *Kiểm tra data/workload.csv, người nào vượt 8 giờ? Ghi báo cáo vào output/workload.md.* | Lan 9 giờ, Minh 3 giờ, chỉ Lan quá tải. Loại dòng 5, 6, 7 | `20261007-190101_86948ad2_turn01_f4bd2eba.jsonl` | ✅ Lan (9 giờ) quá tải, Minh 3 giờ. Loại dòng 5 `invalid_hours`, dòng 6 `duplicate_id`, dòng 7 `missing_owner`. Báo cáo đầy đủ: [agent-report-max8.md](results/agent-report-max8.md). Ảnh: [stage04-max8.png](screenshots/stage04-max8.png) |
| Ngưỡng 9 | *Kiểm tra data/workload.csv, người nào vượt 9 giờ? Ghi báo cáo vào output/workload.md.* | Tổng giờ và dòng bị loại như trên. Không ai quá tải | `20261007-190437_10675312_turn01_b1054d3f.jsonl` | ✅ Không ai quá tải: Lan 9 giờ (*"bằng ngưỡng, không quá tải"*), Minh 3 giờ. Loại dòng 5, 6, 7 như ngưỡng 8. Lệnh `--max-hours 9`, ghi báo cáo một lần: [agent-report-max9.md](results/agent-report-max9.md). Ảnh: [stage04-max9.png](screenshots/stage04-max9.png) |
| Thiếu ngưỡng | *Tính tổng giờ theo người trong data/workload.csv và xác định người quá tải.* | Agent hỏi ngưỡng trước khi kết luận | `{…}` | `{…}` |
| File không tồn tại | `{…}` | Script ghi stderr, exit khác 0. Agent báo không phân tích được | `{…}` | `{…}` |

**Chi tiết ngưỡng 8** (4 model call, 4 tool call):
1. seq 4: `read_file skills/csv-quality/SKILL.md`. Agent tự nạp skill, câu hỏi không nhắc tên skill.
2. seq 8: `bash: python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8` (exit 0), song song với seq 9: `read_file …/report-template.md`.
3. seq 14: `write_file output/workload.md`, ghi **một lần**, 1014 byte, đầy đủ các mục của template.
4. Câu trả lời tóm tắt đúng ngưỡng, người quá tải và các dòng bị loại kèm lý do. Mọi con số khớp với JSON của script ([results/workload-max-8.json](results/workload-max-8.json)).

## 4. Câu hỏi cuối bài

**Phần nào do script tính, phần nào do model diễn giải?**

| Script tính (tất định, có test) | Model diễn giải |
|---|---|
| Đọc CSV, chuẩn hóa khoảng trắng, phát hiện lỗi từng dòng | Hiểu yêu cầu: có hỏi về quá tải không, ngưỡng là bao nhiêu, ghi báo cáo vào đâu |
| Quyết định dòng nào được cộng, gom lý do loại (`excluded_rows`) | Hỏi lại khi thiếu ngưỡng, dựa trên chỉ dẫn trong `SKILL.md` |
| Quy tắc ID trùng: giữ lần đầu, kể cả khi lần đầu không hợp lệ | Chọn đúng lệnh và truyền đúng `--max-hours` |
| Tổng giờ theo owner, so sánh `> max_hours`, danh sách quá tải | Đọc `exit_code` và `stderr`, phân biệt lỗi dữ liệu với lỗi thực thi |
| Thống kê chất lượng trên mọi dòng | Trình bày báo cáo theo `report-template.md`, giải thích lý do, đưa khuyến nghị |

Mọi **con số** đều do script tính. Model chỉ **chọn tham số, đọc kết quả và diễn đạt**. Ở Stage 03, khi model tự viết code Python để cộng giờ, cách xử lý dòng lỗi và ID trùng phụ thuộc vào đoạn code model tự viết ra trong từng lần chạy, nên có thể sai, ví dụ cộng trùng T02 thành Lan 14 giờ. Ở Stage 04, quy tắc nằm trong script và có test, nên lần chạy nào cũng cho cùng một kết quả.

**Nếu sửa script nhưng không cập nhật skill và reference, báo cáo có thể sai hoặc thiếu gì?**
- **Lệnh chạy sai:** `SKILL.md` cũ chạy script **không có `--max-hours`**. Script mới trả exit 2, agent không có kết quả, hoặc có thể tự đoán số.
- **Bỏ qua yêu cầu tính tổng giờ:** `SKILL.md` cũ có quy tắc *"Không tính tổng giờ hay KPI khi còn dữ liệu lỗi"*. Agent có thể từ chối tính, hoặc bỏ qua `hours_by_owner` dù script đã tính.
- **Không hỏi ngưỡng:** skill cũ không có quy tắc hỏi lại, nên agent có thể tự chọn ngưỡng hoặc dùng ngưỡng từ cuộc trò chuyện cũ.
- **Báo cáo thiếu trường:** `report-template.md` cũ không có ngưỡng, tổng giờ, người quá tải hay dòng bị loại. Agent điền theo template cũ thì báo cáo **thiếu đúng phần người dùng cần**. Hoặc agent tự chế cách trình bày, mỗi lần một kiểu.
- **Diễn giải sai:** skill cũ chỉ mô tả các trường JSON cũ, và chỉ có exit code 0 và 1. Agent có thể hiểu sai `excluded_rows` hoặc `overloaded_owners`, ví dụ coi bằng ngưỡng là quá tải. Agent cũng không biết exit 2 nghĩa là thiếu hoặc sai ngưỡng.

Script là **nguồn đúng của phép tính**. Skill và reference là **hợp đồng** cho model biết cách gọi script và cách đọc kết quả. Sửa một bên mà không sửa bên kia thì hợp đồng bị lệch.
