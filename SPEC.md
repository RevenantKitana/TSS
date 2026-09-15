# THIẾT LẬP VÀ ĐẶC TẢ KỸ THUẬT: BATCH TEXT-TO-AUDIO & AUDIO VIEWER (ZeroTTS)

---

## 1. TỔNG QUAN
Tài liệu này đặc tả yêu cầu và giải pháp kỹ thuật cho tính năng **Batch Text-to-Audio**, **Quản lý Thư mục Dự án Tùy chỉnh**, **Cơ chế Ghi đè / Chống sập tiến trình**, và **Trình xem Lịch sử dạng Thư mục (Folder-based Audio Viewer)** trong ứng dụng ZeroTTS.

---

## 2. CÚ PHÁP ĐẦU VÀO (INPUT SYNTAX & PARSING)

### 2.1. Phân đoạn đa dòng theo thẻ `[...]`
* **Văn bản đầu vào:** Được chia thành các khối (Block) dựa theo các nhãn `[Tag_Name]`.
* **Quy tắc ngắt file:**
  * Chỉ khi gặp thẻ `[...]` tiếp theo (hoặc kết thúc văn bản) thì hệ thống mới ngắt sang tệp audio mới.
  * Mọi dòng văn bản nằm bên dưới thẻ `[Tag_Name]` (kể cả có nhiều dấu xuống dòng Enter) đều được gộp chung vào cùng một tệp âm thanh.

**Ví dụ đầu vào:**
```text
[Text 1] Đây là dòng 1 của đoạn 1.
Đây là dòng 2 của đoạn 1 nằm trên dòng mới.
Nó vẫn sẽ được gộp chung vào audio của File 1.

[Text 2] Đây là câu đầu tiên của đoạn 2.
Và đây là câu thứ hai của đoạn 2.
```

### 2.2. Ký hiệu bỏ qua thủ công (Manual Skip)
* Để bỏ qua không render một hoặc một số block (ví dụ khi đoạn đó đã render thành công trước đó), thêm ký hiệu `#`, `!`, hoặc từ khóa `skip:` ở trước thẻ:
```text
#[Text 2] Đoạn này sẽ bị bỏ qua không tạo audio.
[skip: Text 3] Đoạn này cũng sẽ bị bỏ qua.
```

### 2.3. Xử lý ngoại lệ đầu vào
* Nếu phần đầu văn bản có nội dung đứng trước thẻ `[...]` đầu tiên, nội dung đó sẽ được gộp chung (nối vào đầu) câu/đoạn của thẻ `[...]` đầu tiên chứ **không chia thành file Text 1 riêng biệt**.
* Nếu toàn bộ văn bản không chứa thẻ `[...]` nào, hệ thống gán nhãn mặc định `[Text 1]` cho duy nhất 1 block duy nhất.

---

## 3. CẤU TRÚC ĐẦU RA & QUẢN LÝ THƯ MỤC (OUTPUT STRUCTURE)

### 3.1. Ô nhập tên tùy chọn (Custom Folder Name)
* Giao diện bổ sung ô `Tên thư mục / Tiền tố tùy chọn` (ví dụ: `dự_án_1`).
* **Fallback:** Nếu để trống, hệ thống tự động sinh tên dạng `batch_YYYYMMDD_HHMMSS`.

### 3.2. Cấu trúc lưu trữ trên đĩa
* **Khi có từ 2 thẻ `[...]` trở lên:** Đầu ra được lưu trữ trong thư mục riêng: `outputs\generated\<tên_tùy_chọn>\`
* **Khi chỉ có 1 thẻ `[...]` hoặc 0 thẻ:** Đầu ra được xuất trực tiếp vào **thư mục gốc** `outputs\generated\` (dưới tên `<tên_tùy_chọn>.wav` hoặc `YYYYMMDD_HHMMSS_<giọng>.wav`) chứ không tự tạo thư mục con.

Bao gồm các tệp thành phần (cho chế độ Batch đa block):
1. **Tệp Audio (.wav):** `tên_tùy_chọn_01.wav`, `tên_tùy_chọn_02.wav`,... (đánh số chỉ số có dạng `01`, `02`... để sắp xếp đúng thứ tự).
2. **Tệp Ánh xá (.txt):** `<tên_tùy_chọn>_mapping.txt` chứa danh sách kèm mốc thời gian Timeline (`[Start_Time -> End_Time]`):
   ```text
   [tên_tùy_chọn_01.wav] [00:00:00.000 -> 00:00:03.500] [Text 1]
   [tên_tùy_chọn_02.wav] [00:00:03.500 -> 00:00:07.700] [Text 2]
   ```
3. **Tệp Metadata tổng (.json):** `info.json` lưu thông tin chi tiết mốc thời gian (Timeline Start/End/Duration):
   ```json
   {
     "folder_name": "tên_tùy_chọn",
     "created_at": "2026-09-15 09:00:00",
     "voice": "maichi",
     "total_items": 2,
     "total_duration_sec": 7.7,
     "total_duration_timestamp": "00:00:07.700",
     "items": [
       {
         "index": 1,
         "file": "tên_tùy_chọn_01.wav",
         "tag": "Text 1",
         "start_sec": 0.0,
         "end_sec": 3.5,
         "duration_sec": 3.5,
         "start_timestamp": "00:00:00.000",
         "end_timestamp": "00:00:03.500",
         "status": "SUCCESS"
       },
       {
         "index": 2,
         "file": "tên_tùy_chọn_02.wav",
         "tag": "Text 2",
         "start_sec": 3.5,
         "end_sec": 7.7,
         "duration_sec": 4.2,
         "start_timestamp": "00:00:03.500",
         "end_timestamp": "00:00:07.700",
         "status": "SUCCESS"
       }
     ]
   }
   ```

---

## 4. CƠ CHẾ GHI ĐÈ & KHẢ NĂNG CHỐNG SẬP (OVERWRITE & RESILIENCE)

### 4.1. Chế độ xử lý tệp đã tồn tại (Existing Files Mode)
Cung cấp tùy chọn trên giao diện:
1. **Ghi đè tất cả (`Overwrite All`):** Render lại và ghi đè toàn bộ tệp `.wav` cũ có cùng tên.
2. **Bỏ qua file đã có / Chạy tiếp (`Skip Existing / Resume`):** Tự động bỏ qua các câu đã tạo file `.wav` sẵn, chỉ render các câu chưa có (giúp tiếp tục công việc khi rớt mạng/mất điện).
3. **Ghi đè chọn lọc (`Targeted Overwrite`):** Kết hợp cú pháp `#` ở Input để chọn đúng câu bị lỗi cần render lại.

### 4.2. Xử lý lỗi trong quá trình render (Fault Tolerance)
* Quá trình tạo âm thanh cho từng block được bọc trong khối `try...except`.
* Nếu 1 câu bị lỗi render (vỡ tiếng, lỗi ký tự...), hệ thống ghi nhận trạng thái `[FAILED]`, **bỏ qua câu lỗi và tiếp tục render các câu còn lại** mà không làm ngắt toàn bộ tiến trình.

---

## 5. GIAO DIỆN AUDIO VIEWER DẠNG THƯ MỤC (FOLDER-BASED AUDIO VIEWER)

### 5.1. Cấu trúc hiển thị 2 cấp (Master-Detail View)
Thay vì liệt kê tràn ngập các tệp `.wav` riêng lẻ, giao diện Lịch sử (History / Audio Viewer) được tổ chức theo từng Thư mục Batch:

1. **Danh sách Master (Thư mục đợt render):**
   * Mỗi thẻ hiển thị: `📁 <tên_tùy_chọn>` | `Số câu: XX` | `Giọng: maichi` | `Ngày tạo`.
2. **Danh sách Detail (Chi tiết các câu):**
   * Bấm vào 1 Thư mục $\rightarrow$ nạp danh sách các tệp audio thuộc thư mục đó vào danh sách thả xuống (`Dropdown`).
   * Chọn câu nào $\rightarrow$ phát audio tương ứng trên Trình phát Audio chính (Player).

---

## 6. NỐI TỆP AUDIO (AUDIO CONCATENATION & MERGING)

### 6.1. Quy tắc Đặt tên & Phân biệt Tệp Nối
* Tệp sau khi nối gộp tất cả các câu sẽ được đặt tên theo mở rộng định dạng đã chọn: `<tên_tùy_chọn>_FULL_MERGED.<ext>` (ví dụ `.mp3`, `.wav`, `.flac`, `.m4a`, `.ogg`).
* **Quy tắc lọc (Filter Rule):** Khi trình nối thực hiện quét các tệp âm thanh phân đoạn trong thư mục:
  * Chỉ nhận các tệp phân đoạn có đuôi số dạng `_\d+.wav` (ví dụ `_01.wav`, `_02.wav`).
  * **Tự động loại trừ** mọi tệp chứa hậu tố `_FULL_MERGED.*` hoặc `_merged` để tránh bị lặp chèn tệp gộp vào chính nó.
  * **Không nối (Skip Merge):** Nếu thư mục chỉ chứa **1 tệp audio duy nhất** (hoặc 0 tệp), hệ thống sẽ không thực hiện nối và không tạo tệp `_FULL_MERGED`.

### 6.2. Danh sách Định dạng & Bitrate Xuất Tệp Gộp (Export Formats)
Hệ thống sử dụng FFmpeg (`ffmpeg/bin/ffmpeg.exe` local hoặc FFmpeg hệ thống) để mã hóa xuất tệp gộp với các tùy chọn:
1. `WAV (PCM 16-bit Lossless)` - `.wav` (Mặc định)
2. `MP3 (320 kbps)` - `.mp3` (Chất lượng cao nhất)
3. `MP3 (192 kbps)` - `.mp3` (Chất lượng trung bình)
4. `MP3 (128 kbps)` - `.mp3` (Tiêu chuẩn / Tiết kiệm dung lượng)
5. `FLAC (Lossless Compressed)` - `.flac` (Nén không mất chất lượng)
6. `M4A / AAC (256 kbps)` - `.m4a` (AAC chuẩn Apple)
7. `OGG / Vorbis (192 kbps)` - `.ogg`

### 6.3. Tính năng Nối Tự động & Thủ công
1. **Tự động nối sau khi tạo (Auto-Merge Option):** 
   * Trên UI có ô tích `Tự động nối các tệp audio sau khi tạo`.
   * Ngay sau khi hoàn thành tạo tất cả các câu lẻ, engine sẽ tự động mã hóa nối và tạo tệp `_FULL_MERGED.<ext>`.
2. **Nút Nối thủ công trên Audio Viewer (Manual Merge Button):**
   * Trong giao diện Lịch sử, cho phép chọn định dạng mong muốn và bấm nút **🔗 Nối bộ Audio này**, hệ thống sẽ mã hóa tệp gộp mới và nạp phát ngay trên trình phát chính.

---

## 7. KẾ HOẠCH TỔNG THỂ CÁC THÀNH PHẦN CẦN CHỈNH SỬA

| File | Nội dung điều chỉnh |
| :--- | :--- |
| `webui/engine.py` | Viết regex parser tách block `[...]`, bổ sung tạo folder + file `info.json` + `mapping.txt`, thêm kiểm tra `Skip Existing`, `try...except` per-block, định vị `ffmpeg.exe` và hàm nối `concat_folder_audio` đa định dạng. |
| `webui/app.py` | Thêm field `Tên thư mục tùy chọn`, Checkbox `Auto-Merge`, Dropdown `Định dạng tệp nối`, Radio `Existing Files Action`, nút `🔗 Nối bộ Audio này` trên History UI. |


