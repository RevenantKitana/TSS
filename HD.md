# 📥 1. INPUT TEXT (Người dùng nhập vào Editor)

[Câu 1]
Xin chào các bạn. [pause: 1.5s] Đây là câu hỏi đầu tiên.

[Câu 2]
Hãy chọn đáp án đúng nhất. Thời gian suy nghĩ bắt đầu!

#[Bỏ qua]
Đoạn này nháp, hệ thống tự động bỏ qua không đọc. Dùng khi muốn tạo lại 1 vài câu trong text nhưng câu này đã đạt không cần sửa

[Kết Thúc]
Chúc các bạn làm bài tốt!

# ⚙️ 2. PHÂN TÍCH TỰ ĐỘNG (Timeline & Kế hoạch Render)

| STT | Thẻ Tag       | Trạng thái | Thời lượng | Chi tiết xử lý                              |
|:---:|:--------------|:----------:|:----------:|:--------------------------------------------|
| 01  | `[Câu 1]`     | ✅ RENDER   | 5.2s       | Sinh tiếng + chèn 1.5s khoảng lặng ở giữa   |
| 02  | `[Câu 2]`     | ✅ RENDER   | 4.8s       | Sinh tiếng   |
| 03  | `#[Bỏ qua]`   | ⏭️ SKIPPED  | 0.0s       | Bỏ qua (không tốn thời gian sinh âm thanh)  |
| 04  | `[Kết Thúc]`  | ✅ RENDER   | 2.5s       | Sinh tiếng kết bài                          |

# 📤 3. KẾT QUẢ ĐẦU RA (Thư mục dự án outputs/)

outputs/batch_du_an_01/
├── 01_Câu_1.wav         <- Âm thanh riêng phân đoạn 1
├── 02_Câu_2.wav         <- Âm thanh riêng phân đoạn 2
├── 03_Kết_Thúc.wav      <- Âm thanh riêng phân đoạn 4, đoạn 3 được bỏ qua
└── _FULL_MERGED.mp3     <- File tổng nối tự động (Tổng độ dài: ~12.5s)

------
Input text có thể rất rất dài, nhưng việc chia câu theo [ Câu ] vẫn là 1 file độc lập, sau đó mới gộp lại thành 1 file hoàn chỉnh để tối ưu thời gian. Khi kết thúc thì gộp tất cả lại để thành 1 file hoàn chỉnh.