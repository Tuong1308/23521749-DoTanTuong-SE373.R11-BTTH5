# Báo cáo chất lượng dữ liệu và tải công việc: `data/workload.csv`

Công cụ: `skills/csv-quality/scripts/check_csv.py --max-hours 8` | exit code: 0

## Ngưỡng và người quá tải
- Ngưỡng: **8 giờ** (quá tải khi tổng giờ lớn hơn ngưỡng; bằng ngưỡng không quá tải)
- Người vượt ngưỡng: **Lan (9 giờ)**

## Tổng giờ theo người
Chỉ cộng các dòng hợp lệ; dòng bị loại không được cộng.

| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| Lan | 9 | Có |
| Minh | 3 | Không |

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Lý do |
|---|---|---|
| 5 | T04 | invalid_hours |
| 6 | T02 | duplicate_id |
| 7 | T05 | missing_owner |

## Tổng quan chất lượng (mọi dòng dữ liệu)
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | 6 |
| Dòng thiếu owner | 1 |
| Dòng hours không hợp lệ | 1 |
| Số task_id bị lặp (distinct) | 1 (T02) |

## Chi tiết lỗi
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| 5 | hours | invalid_hours | T04 | hours 'abc' không phải số hữu hạn không âm. |
| 6 |