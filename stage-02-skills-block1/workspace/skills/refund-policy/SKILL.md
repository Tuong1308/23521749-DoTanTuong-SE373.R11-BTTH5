---
name: refund-policy
description: Tra cứu chính sách hoàn tiền đúng phiên bản theo ngày mua và kết luận một đơn hàng có được hoàn tiền không, kèm số ngày đã qua và phí. Dùng khi người dùng hỏi có được hoàn tiền không, điều kiện, thời hạn hoặc phí hoàn tiền của đơn hàng đã mua.
---

# Refund policy

Kết luận hoàn tiền phải dựa trên tài liệu chính sách đọc được trong workspace ở cuộc trò chuyện hiện tại. Không trả lời từ kiến thức sẵn có, không dùng nội dung chính sách nhớ từ cuộc trò chuyện cũ.

## 1. Kiểm tra đủ thông tin

Cần đủ 3 thông tin trong câu hỏi:

- Ngày mua.
- Ngày yêu cầu hoàn tiền.
- Trạng thái kích hoạt sản phẩm (đã kích hoạt hay chưa).

Nếu thiếu bất kỳ thông tin nào: hỏi lại đúng thông tin còn thiếu và **dừng, chưa kết luận**. Không tự giả định, ví dụ không coi là "chưa kích hoạt" khi người dùng không nói. Không dùng ngày hiện tại của máy thay cho ngày yêu cầu hoàn. Ngày viết dạng dd/mm/yyyy (ngày/tháng/năm).

## 2. Tìm tài liệu chính sách

1. Gọi `list_files` với path `data/policies` để xem các tài liệu hiện có. Tên file có thể thay đổi giữa các lần: không đoán tên file, không dùng tên file từ cuộc trò chuyện trước.
2. Nếu có thư mục con, gọi `list_files` tiếp cho thư mục con đó.
3. Đọc **từng** file tài liệu bằng `read_file`, dùng đúng `path` trong kết quả `list_files`.
4. Nếu `list_files` hoặc `read_file` trả lỗi, hoặc thư mục không có tài liệu: báo cho người dùng và dừng, không kết luận.

## 3. Chọn chính sách theo ngày mua

- Trong nội dung mỗi tài liệu, tìm dòng phạm vi hiệu lực (ví dụ "Áp dụng cho ngày mua ...").
- Chọn tài liệu có phạm vi chứa **ngày mua**. Không chọn theo ngày yêu cầu hoàn, ngày hiện tại hay tên file.
- Đọc kỹ ranh giới: "trước ngày X" không bao gồm ngày X; "từ ngày X, bao gồm ngày này" có bao gồm ngày X.
- Nếu không tài liệu nào khớp, hoặc nhiều tài liệu cùng khớp: báo mâu thuẫn và liệt kê tài liệu liên quan, không tự chọn.

## 4. Tính và kết luận

1. Số ngày đã qua = ngày yêu cầu hoàn − ngày mua, tính theo ngày lịch. Ví dụ mua 01/10, yêu cầu 03/10 là 2 ngày. Khi qua ranh giới tháng, đếm đúng số ngày của tháng (tháng 9 có 30 ngày).
2. Nếu ngày yêu cầu hoàn trước ngày mua: báo dữ liệu không hợp lệ và hỏi lại.
3. Điều kiện thời gian: số ngày đã qua **nhỏ hơn hoặc bằng** thời hạn trong tài liệu. Bằng đúng thời hạn vẫn đủ điều kiện.
4. Áp dụng các điều kiện khác ghi trong tài liệu, ví dụ sản phẩm đã kích hoạt.
5. Đủ mọi điều kiện: **đủ điều kiện**, nêu phí theo tài liệu (nếu tài liệu ghi không thu phí thì ghi "Không thu phí"). Thiếu một điều kiện: **không đủ điều kiện**, nêu lý do, phí ghi "Không áp dụng".
6. Thời hạn, điều kiện, phí đều lấy từ tài liệu đã chọn; không tự thêm điều kiện không có trong tài liệu.

## 5. Trả lời

Đọc template `references/answer-template.md` trong thư mục skill này, tức `skills/refund-policy/references/answer-template.md`, rồi trả lời theo đúng cấu trúc đó. Chỉ viết kết luận **sau khi** đã so sánh xong số ngày với thời hạn và kiểm tra mọi điều kiện ở bước 4; kết luận phải khớp với các phép so sánh đó. Câu trả lời chỉ có một kết luận, không tự sửa giữa chừng. Mục căn cứ ghi đường dẫn tài liệu đúng như kết quả `list_files`/`read_file`. Chỉ ghi file khi người dùng yêu cầu.
