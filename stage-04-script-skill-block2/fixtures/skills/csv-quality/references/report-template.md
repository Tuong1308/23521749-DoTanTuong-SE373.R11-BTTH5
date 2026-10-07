# Báo cáo tải công việc: `{đường dẫn CSV}`

Script: `check_csv.py --max-hours {max_hours}` | exit {exit_code}

## Ngưỡng và người quá tải
- Ngưỡng: **{max_hours} giờ** (quá tải khi tổng giờ lớn hơn ngưỡng)
- Vượt ngưỡng: {owner (total_hours giờ) từ overloaded_owners, hoặc "Không có ai"}

## Tổng giờ theo người (chỉ dòng hợp lệ)
| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| {owner} | {total_hours} | {Có/Không} |

## Dòng bị loại
| Line | task_id | Lý do | Mô tả |
|---|---|---|---|
| {line} | {task_id hoặc (trống)} | {reasons} | {message ngắn từ issues} |

## Chất lượng dữ liệu (mọi dòng)
{row_count} dòng; thiếu owner: {missing_owner_count}; hours sai: {invalid_hours_count}; task_id lặp: {duplicate_id_count} ({duplicate_ids}).

## Khuyến nghị
{Một dòng: sửa dữ liệu nguồn nào để tổng giờ đầy đủ; không tự sửa file}
