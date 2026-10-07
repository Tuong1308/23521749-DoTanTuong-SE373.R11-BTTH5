# Báo cáo tải công việc: `data/workload.csv`

Script: `check_csv.py --max-hours 8` | exit 0

## Ngưỡng và người quá tải
- Ngưỡng: **8 giờ** (quá tải khi tổng giờ lớn hơn ngưỡng)
- Vượt ngưỡng: Lan (9 giờ)

## Tổng giờ theo người (chỉ dòng hợp lệ)
| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| Lan | 9 | Có |
| Minh | 3 | Không |

## Dòng bị loại
| Line | task_id | Lý do | Mô tả |
|---|---|---|---|
| 5 | T04 | invalid_hours | hours 'abc' không phải số hữu hạn không âm. |
| 6 | T02 | duplicate_id | task_id T02 đã xuất hiện ở line 3. |
| 7 | T05 | missing_owner | owner trống. |

## Chất lượng dữ liệu (mọi dòng)
6 dòng; thiếu owner: 1; hours sai: 1; task_id lặp: 1 (["T02"]).

## Khuyến nghị
Sửa dữ liệu nguồn: nhập hours hợp lệ cho T04 (line 5), đặt owner cho T05 (line 7) và đổi task_id trùng T02 (line 6) để tổng giờ đầy đủ; không tự sửa file.