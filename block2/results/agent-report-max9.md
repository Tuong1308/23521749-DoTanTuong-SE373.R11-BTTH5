# Báo cáo tải công việc: `data/workload.csv`

Script: `check_csv.py --max-hours 9` | exit 0

## Ngưỡng và người quá tải
- Ngưỡng: **9 giờ** (quá tải khi tổng giờ lớn hơn ngưỡng)
- Vượt ngưỡng: Không có ai

## Tổng giờ theo người (chỉ dòng hợp lệ)
| Owner | Tổng giờ | Vượt ngưỡng? |
|---|---|---|
| Lan | 9 | Không |
| Minh | 3 | Không |

Tổng giờ chỉ gồm các dòng hợp lệ; các dòng bị loại không được cộng và có thể làm tổng giờ thấp hơn thực tế.

## Dòng bị loại
| Line | task_id | Lý do | Mô tả |
|---|---|---|---|
| 5 | T04 | invalid_hours | hours 'abc' không phải số hữu hạn không âm. |
| 6 | T02 | duplicate_id | task_id T02 đã xuất hiện ở line 3. |
| 7 | T05 | missing_owner | owner trống. |

## Chất lượng dữ liệu (mọi dòng)
6 dòng; thiếu owner: 1; hours sai: 1; task_id lặp: 1 (T02).

## Khuyến nghị
Sửa nguồn: đổi `hours` của T04 (line 5) thành số hợp lệ, bổ sung owner cho T05 (line 7), và gán task_id duy nhất cho dòng lặp T02 (line 6) (không tự sửa file khi chỉ yêu cầu kiểm tra).