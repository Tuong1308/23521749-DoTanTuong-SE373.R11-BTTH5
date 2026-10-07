---
name: csv-quality
description: Kiểm tra chất lượng file CSV danh sách công việc (cột task_id, owner, hours), tính tổng giờ theo người và xác định người quá tải theo ngưỡng giờ do người dùng cung cấp, bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra, rà soát chất lượng dữ liệu CSV công việc, tính tổng giờ theo người hoặc kiểm tra ai quá tải.
---

# CSV quality

Kiểm tra chất lượng CSV công việc và tính tổng giờ theo người bằng script, không tự đếm hay tự cộng bằng mắt.

## Ngưỡng giờ (`--max-hours`)

Script bắt buộc tham số `--max-hours` (số hữu hạn, không âm).

- Lấy ngưỡng từ **yêu cầu hiện tại** của người dùng, ví dụ "ai vượt N giờ" thì truyền `--max-hours N`. Truyền đúng giá trị người dùng nêu.
- Nếu người dùng **chưa nêu ngưỡng**: hỏi lại ngưỡng giờ và **dừng**, chưa chạy script, chưa kết luận ai quá tải. Không tự chọn ngưỡng mặc định, không dùng ngưỡng từ cuộc trò chuyện cũ hay từ ví dụ trong tài liệu.
- Quá tải khi tổng giờ **lớn hơn** ngưỡng; tổng giờ bằng ngưỡng **không** quá tải. Danh sách quá tải lấy từ `overloaded_owners` của script.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours <ngưỡng người dùng nêu>`

Không cần đọc source script để chạy. Chỉ đọc `scripts/check_csv.py` khi cần hiểu một hành vi mà phần dưới không mô tả.

## Kiểm tra kết quả

- `exit_code` 0: phân tích thành công. `stdout` là JSON gồm:
  - Thống kê chất lượng trên **mọi** dòng dữ liệu: `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.
  - `max_hours`: ngưỡng đã truyền.
  - `hours_by_owner`: tổng giờ theo owner, chỉ gồm owner có ít nhất một dòng được cộng.
  - `overloaded_owners`: danh sách `{owner, total_hours}` vượt ngưỡng, sắp theo tên.
  - `excluded_rows`: các dòng không được cộng, mỗi dòng `{line, task_id, reasons}`. Mã lý do: `wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`.
  - Dữ liệu có lỗi chất lượng, có dòng bị loại hoặc có người quá tải vẫn là exit 0.
- `exit_code` 1: **lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse). Đọc `stderr`, báo lỗi cho người dùng. Không bịa thống kê, tổng giờ hay danh sách quá tải, không ghi báo cáo như thể đã phân tích.
- `exit_code` 2: thiếu `--max-hours` hoặc ngưỡng không hợp lệ. Đọc `stderr`; hỏi lại người dùng ngưỡng hợp lệ, không tự sửa giá trị.
- `timed_out` true hoặc `ok` false: lệnh không chạy xong; báo lỗi, không suy đoán kết quả.
- Phân biệt rõ **lỗi dữ liệu** (nằm trong `issues`/`excluded_rows`, script vẫn chạy thành công) với **lỗi thực thi** (exit khác 0).

## Quy tắc tính (do script thực hiện, dùng để giải thích cho người dùng)

- Bỏ khoảng trắng đầu/cuối ở `task_id`, `owner`, `hours`. Owner khác tên hoặc khác hoa/thường là hai người khác nhau.
- Chỉ cộng dòng có đúng số trường, `task_id` không rỗng, `owner` không rỗng và `hours` là số hữu hạn không âm (0 hợp lệ).
- Mỗi `task_id` chỉ giữ lần xuất hiện đầu tiên; các lần sau bị loại (`duplicate_id`), kể cả khi lần đầu không hợp lệ. Không lấy dòng trùng phía sau để thay thế.

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này, tức `skills/csv-quality/references/report-template.md`. Viết **ngắn gọn, đúng các mục của template**, không thêm mục hay bảng ngoài template; mỗi dòng bị loại chỉ liệt kê một lần (trong bảng *Dòng bị loại*). Ghi báo cáo bằng **một** lần `write_file`.
2. Lấy mọi con số từ JSON của script: ngưỡng, tổng giờ, người quá tải, dòng bị loại, thống kê chất lượng. Không tự cộng lại hay sửa số. Mỗi issue và mỗi dòng bị loại ghi line number (header là line 1).
3. Không sửa file CSV khi người dùng chỉ yêu cầu kiểm tra. Có thể đề xuất cách sửa trong mục khuyến nghị.
4. Ghi rõ tổng giờ chỉ gồm các dòng hợp lệ; các dòng bị loại không được cộng và có thể làm tổng giờ thấp hơn thực tế.
5. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (mặc định `output/csv-quality.md`), rồi trả lời đường dẫn và tóm tắt ngắn: ngưỡng, ai quá tải, các dòng bị loại.
