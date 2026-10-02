# 🎙️ TSS Studio — Tài Liệu Bản Nâng Cấp (ZeroTTS Mod)
### *Vietnamese Multi-Block Batch, Project Pipeline & Zero-Shot TTS Studio*

[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![ONNX Runtime](https://img.shields.io/badge/Inference-ONNX%20Runtime%20(CPU%2FGPU)-005CED.svg?logo=onnx&logoColor=white)](https://onnxruntime.ai/)
[![Cloud Ready](https://img.shields.io/badge/Cloud-Colab%20%7C%20Kaggle-F9AB00.svg?logo=googlecolab&logoColor=white)](COLAB_GUIDE.md)

---

## 📌 1. Giới Thiệu Tổng Quan (Overview)

**TSS Studio (ZeroTTS Mod)** là phiên bản mở rộng và hoàn thiện chuyên sâu xây dựng trên nền tảng kiến trúc **ZeroTTS** (Vietnamese Zero-Shot Text-to-Speech). Phiên bản này được thiết kế nhằm chuyển đổi mô hình TTS từ dạng thử nghiệm đơn lẻ thành một **hệ thống sản xuất âm thanh chuyên nghiệp (Audio Production Pipeline)**, hỗ trợ sản xuất audio sách nói, bài giảng e-learning, video kịch bản dài và xử lý hàng loạt dự án tự động.

### 🌟 So Sánh Tính Năng: Bản Gốc vs Bản Mod

| Hạng mục tính năng | Bản gốc ZeroTTS | Bản Nâng Cấp TSS Mod |
| :--- | :---: | :---: |
| **Sinh âm thanh cơ bản** | ✅ Từng câu / đoạn ngắn | ✅ Từng câu, đoạn ngắn & hàng loạt |
| **Chia nhỏ theo phân đoạn kịch bản** | ❌ Không hỗ trợ | ✅ Cú pháp thẻ `[Tag]` ngắt file độc lập |
| **Chèn khoảng lặng tùy biến** | ❌ Phải chèn dấu câu giả lập | ✅ Thẻ `[pause: 1.5s]` sinh silence chuẩn xác |
| **Bỏ qua câu đã đạt / Nháp** | ❌ Phải xóa thủ công văn bản | ✅ Thẻ `#[Tag]`, `![Tag]`, `[skip: Tag]` |
| **Xử lý chuỗi đa dự án (Multi-Project)** | ❌ Không hỗ trợ | ✅ Thẻ `$[Tên_Dự_Án]` tạo folder tự động |
| **Nạp file kịch bản** | ❌ Chỉ nhập tay ô text | ✅ Nạp trực tiếp tệp `.txt` và Word `.docx` |
| **Cơ chế phục hồi / Chống sập (Resume)** | ❌ Lỗi giữa chừng mất hết | ✅ `Skip Existing / Resume` & `try..except` per-block |
| **Tự động ghép nối (Concat Engine)** | ❌ Cần phần mềm bên thứ 3 | ✅ Tích hợp FFmpeg (WAV, MP3, FLAC, M4A, OGG) |
| **Timeline & Metadata Export** | ❌ Không có | ✅ Xuất file `_mapping.txt` và `info.json` chi tiết |
| **Giao diện Web (WebUI)** | 🟡 Gradio cơ bản | ✅ Standalone WebUI (FastAPI + HTML5/CSS3/JS) |
| **Quản lý lịch sử (History Viewer)** | ❌ Danh sách file rời rạc | ✅ Master-Detail Folder Viewer + Nối thủ công |
| **Môi trường Cloud (Colab / Kaggle)** | ❌ Cần tự cấu hình phức tạp | ✅ Sẵn sàng 1-Click (WebUI Tunnel & Headless Drive) |

---

## 🏷️ 2. Hệ Thống Cú Pháp Đầu Vào Nâng Cao (Input Syntax)

Hệ thống cung cấp bộ phân tích cú pháp linh hoạt (Regex Parser) cho phép điều khiển quy trình biên tập âm thanh chi tiết:

### 2.1. Phân đoạn đa khối `[Tên_Thẻ]`
- Mỗi thẻ `[Tag_Name]` đại diện cho một tệp âm thanh `.wav` độc lập.
- Mọi văn bản bên dưới thẻ (bao gồm cả các dòng xuống dòng Enter) được gộp chung vào audio của file đó cho đến khi gặp thẻ `[...]` tiếp theo.

```text
[Câu 1]
Xin chào các bạn đã đến với bài học hôm nay.
Chúc các bạn có một buổi học hiệu quả.

[Câu 2]
Chúng ta sẽ cùng tìm hiểu về khái niệm đầu tiên.
```

### 2.2. Chèn khoảng lặng tự nhiên `[pause: <thời gian>]`
- Hỗ trợ đơn vị giây (`s`) hoặc mili-giây (`ms`).
- Hệ thống chèn frame khoảng lặng âm thanh chuẩn (*silence frames*) vào đúng vị trí chỉ định mà không làm méo âm hay mất nhịp đọc.

```text
[Câu 1]
Xin chào quý vị khán giả. [pause: 1.5s] Sau đây là bản tin chính buổi tối.
Hãy cùng chờ xem trong [pause: 500ms] 3, 2, 1!
```

### 2.3. Ký hiệu bỏ qua chọn lọc (`#`, `!`, `skip:`)
- Dùng khi bạn chỉ muốn render lại một vài câu bị lỗi trong kịch bản dài mà không muốn tốn thời gian render lại những câu đã đạt chuẩn.

```text
#[Câu 1]
Đoạn này đã render chuẩn từ trước, hệ thống sẽ bỏ qua không tốn thời gian tính toán.

[Câu 2]
Đoạn này cần tạo lại âm thanh.

[skip: Đoạn nháp]
Ghi chú nội bộ dành cho biên tập viên, hệ thống sẽ tự động bỏ qua.
```

### 2.4. Chuỗi Đa Dự Án & Đa Thư Mục (`$[Tên_Thư_Mục]`)
- Cho phép chạy liên tiếp nhiều kịch bản/dự án khác nhau trong cùng 1 lần nhấn nút.
- Sử dụng cú pháp `$[Tên_thư_mục]` kèm chú thích tùy chọn `//...`:

```text
$[Bai_Hoc_01] // Dự án bài học số 1
    [Phan_1] Giới thiệu tổng quan về an toàn lao động.
    [Phan_2] Quy tắc sử dụng đồ bảo hộ cá nhân.

$[Bai_Hoc_02] // Dự án bài học số 2
    [Phan_1] Kỹ năng giao tiếp trong môi trường công sở.
    [Phan_2] Tóm tắt và bài tập thực hành.
```

### 2.5. Nạp tệp tài liệu `.txt` và `.docx`
- Hỗ trợ tải trực tiếp tệp văn bản thuần `.txt` hoặc tệp Microsoft Word `.docx`.
- Nếu tệp không chứa thẻ `$[...]`, tên tệp văn bản sẽ được tự động sử dụng làm tên thư mục dự án.

---

## 🛡️ 3. Cơ Chế Chống Sập & Phục Hồi Tiến Trình (Fault Tolerance & Resume)

Khi thực hiện chuyển đổi văn bản dài với hàng chục hoặc hàng trăm câu:

1. **Cô lập lỗi từng block (Isolated Block Rendering)**:
   - Mỗi block văn bản được bọc trong khối xử lý ngoại lệ `try...except` độc lập.
   - Nếu một câu gặp sự cố (ký tự lạ, lỗi suy luận), câu đó sẽ được đánh dấu `[FAILED]`, hệ thống **tiếp tục render các câu còn lại** mà không làm dừng toàn bộ hàng đợi.
2. **Chế độ xử lý tệp đã tồn tại (Existing Files Modes)**:
   - **`Ghi đè tất cả (Overwrite All)`**: Render lại và ghi đè toàn bộ các file cũ.
   - **`Bỏ qua file đã có / Chạy tiếp (Skip Existing / Resume)`**: Tự động phát hiện các câu đã có tệp `.wav` tương ứng trên đĩa và bỏ qua, chỉ render những câu chưa hoàn thành. Rất hữu ích khi bị mất điện, rớt mạng hoặc khởi động lại.
   - **`Ghi đè chọn lọc (Targeted Overwrite)`**: Kết hợp với cú pháp `#` để chỉ render chính xác câu chỉ định.

---

## 🔗 4. Hệ Thống Ghép Nối Âm Thanh & Xuất Metadata (Audio Merge & Export)

Sau khi tạo xong các câu đơn lẻ, bộ engine FFmpeg tích hợp sẵn sẽ tự động thực hiện ghép nối và tạo dữ liệu thời gian:

### 4.1. Định dạng xuất đa dạng & Tùy chọn Bitrate
Hệ thống hỗ trợ xuất tệp gộp `_FULL_MERGED.<ext>` với các chuẩn mã hóa:
- `WAV (PCM 16-bit Lossless)`: Giữ nguyên chất lượng gốc.
- `MP3 (320 kbps)`: Chuẩn nén chất lượng cao nhất cho sản xuất nội dung.
- `MP3 (192 kbps)` / `MP3 (128 kbps)`: Chuẩn phổ thông, tối ưu dung lượng tải nhanh.
- `FLAC (Lossless Compressed)`: Nén không suy hao dữ liệu.
- `M4A / AAC (256 kbps)`: Định dạng chuẩn cho hệ sinh thái Apple / Di động.
- `OGG / Vorbis (192 kbps)`: Phù hợp cho nhúng web và game engine.

### 4.2. Quy tắc lọc thông minh (Smart Concat Filter)
- Chỉ ghép các tệp có chỉ số phân đoạn `_\d+.wav` (ví dụ `01.wav`, `02.wav`).
- Tự động loại trừ các tệp `_FULL_MERGED` cũ nhằm tránh lỗi lặp đệ quy âm thanh.
- Tự động bỏ qua bước gộp nếu thư mục chỉ chứa đúng 1 tệp âm thanh duy nhất.

### 4.3. Tệp Ánh Xạ Mốc Thời Gian & Metadata
Mỗi thư mục kết quả tự động sinh 2 tệp phụ trợ cho khâu hậu kỳ dựng video / podcast:
1. **`<Tên_Dự_Án>_mapping.txt`**: Danh sách timeline trực quan dạng text:
   ```text
   [Bai_Hoc_01_01.wav] [00:00:00.000 -> 00:00:04.250] [Phan_1]
   [Bai_Hoc_01_02.wav] [00:00:04.250 -> 00:00:09.120] [Phan_2]
   ```
2. **`info.json`**: Cấu trúc JSON chi tiết chứa tổng thời lượng, giọng đọc, trạng thái và mốc bắt đầu/kết thúc tính theo giây và timestamp chuẩn.

---

## 🎨 5. Giao Diện WebUI Studio & Trình Xem Lịch Sử (Audio Viewer)

Giao diện được xây dựng hiện đại, trực quan, hỗ trợ đầy đủ các tính năng biên tập:

```text
webui/
├── server.py             # FastAPI backend server (CORS, SSE, Audio Streams)
├── engine.py             # Core logic: Parser, Inference, FFmpeg concat, Voice Manager
├── audio_stream.py       # Live audio streaming route
└── static/
    ├── index.html        # Giao diện Studio hiện đại
    ├── style.css         # Theme Dark/Light, responsive design, animations
    └── app.js            # Trình quản lý Player, Waveform visualizer, SSE listener
```

### Các Khối Tính Năng Nổi Bật Trên Giao Diện:
1. **Trình soạn thảo Kịch bản (Script Editor)**:
   - Hỗ trợ đổi tên thư mục tùy chỉnh hoặc tự động sinh timestamp.
   - Nút nạp nhanh kịch bản từ tệp `.txt` / `.docx`.
   - Nút phân tích trước kế hoạch render (Timeline & Preview Plan).
2. **Bảng Điều Khiển Giọng Đọc & Tham Số**:
   - Bộ chọn giọng tiếng Việt kèm thẻ phân loại vùng miền (Bắc / Trung / Nam) và giới tính.
   - Nút nghe thử giọng mẫu trước khi sinh.
   - Tùy chỉnh tham số suy luận: `Temperature`, `Top-K`, `Top-P`, `Repetition Penalty`, `CFG Scale`.
3. **Trình Quản Lý Lịch Sử 2 Cấp (Master-Detail History Viewer)**:
   - Danh sách Master: Hiển thị các thư mục dự án đã tạo kèm ngày giờ, tổng số câu, giọng đọc.
   - Danh sách Detail: Khi chọn thư mục, hiển thị toàn bộ các câu con và file gộp `_FULL_MERGED`.
   - Nút **`🔗 Nối bộ Audio này`**: Cho phép đổi định dạng tệp gộp và thực hiện nối lại thủ công bất cứ lúc nào.
   - Nút mở nhanh thư mục lưu trữ trên máy tính.

---

## 📁 6. Cấu Trúc Thư Mục Kết Quả (`outputs/`)

```text
outputs/
└── generated/
    ├── [Dự_Án_A]/
    │   ├── Dự_Án_A_01.wav             <- File audio phân đoạn 1
    │   ├── Dự_Án_A_02.wav             <- File audio phân đoạn 2
    │   ├── Dự_Án_A_03.wav             <- File audio phân đoạn 3
    │   ├── Dự_Án_A_FULL_MERGED.mp3    <- File tổng hợp đã nối
    │   ├── Dự_Án_A_mapping.txt        <- Timeline căn khớp hình ảnh/video
    │   └── info.json                  <- Dữ liệu metadata chi tiết
    └── [Dự_Án_B]/
        └── ...
```

---

## 🚀 7. Hướng Dẫn Cài Đặt & Sử Dụng

### 7.1. Chạy trên Máy Tính Cục Bộ (Windows 1-Click)
Dự án đã tích hợp sẵn script tự động kiểm tra môi trường, tải FFmpeg và nạp mô hình:
1. Nhấp đúp chuột vào file [`run_webui.bat`](run_webui.bat).
2. Script sẽ tự động:
   - Tạo môi trường ảo Python (`.venv` hoặc nhận diện Python Embed).
   - Tải `ffmpeg.exe` nếu máy chưa có.
   - Tải trọng số mô hình `ZeroTTS_model` từ Hugging Face.
   - Khởi động server WebUI tại địa chỉ: `http://localhost:7860`.

### 7.2. Chạy trên Google Colab (GPU T4 Miễn Phí)
Xem hướng dẫn chi tiết tại [`COLAB_GUIDE.md`](COLAB_GUIDE.md).
- **Đóng gói mã nguồn 1-click**: Chạy [`tao_file_zip_colab.bat`](tao_file_zip_colab.bat) để tạo file `TSS_Code.zip`.
- **Bản WebUI**: Mở [`ZeroTTS_Colab_FreeTier.ipynb`](ZeroTTS_Colab_FreeTier.ipynb) -> Chọn T4 GPU -> Run All -> Nhận đường link Cloudflare Tunnel để dùng.
- **Bản Headless**: Mở [`ZeroTTS_Colab_Headless.ipynb`](ZeroTTS_Colab_Headless.ipynb) -> Render trực tiếp danh sách file `.docx`/`.txt` vào Google Drive.

### 7.3. Chạy trên Kaggle (GPU T4 x2 / P100 Miễn Phí 30h/tuần)
Xem hướng dẫn chi tiết tại [`KAGGLE_GUIDE.md`](KAGGLE_GUIDE.md).
- Mở [`ZeroTTS_Kaggle_FreeTier.ipynb`](ZeroTTS_Kaggle_FreeTier.ipynb).
- Bật `Accelerator: GPU T4 x2` và `Internet: ON`.
- Run All để tự động clone mã nguồn từ GitHub và nhận link truy cập WebUI.

---

## 🎙️ 8. Danh Sách Gói Giọng Đọc Mặc Định (Voice Packs)

Các gói giọng được lưu trữ trong thư mục [`Voice_ZeroTTS_model/voices/`](Voice_ZeroTTS_model/voices/):

| Tên Giọng (Voice ID) | Tên Hiển Thị | Giới Tính | Vùng Miền / Đặc Điểm |
| :--- | :--- | :---: | :--- |
| `baotrang` | Bảo Trang | Nữ | Miền Bắc — Trầm ấm, diễn cảm, kể chuyện |
| `giahuy` | Gia Huy | Nam | Miền Bắc — Rõ ràng, tin tức, tài liệu |
| `hamy` | Hà My | Nữ | Miền Bắc — Nhẹ nhàng, trẻ trung, tự nhiên |
| `huuduc` | Hữu Đức | Nam | Miền Nam — Ấm áp, truyền cảm |
| `kimoanh` | Kim Oanh | Nữ | Miền Bắc — Truyền cảm, đọc truyện |
| `maichi` | Mai Chi | Nữ | Miền Bắc — Chuẩn mực, tin tức, đọc sách |
| `quangminh` | Quang Minh | Nam | Miền Bắc — Trầm, phát thanh viên |
| `tiendat` | Tiến Đạt | Nam | Miền Trung / Bắc — Tự nhiên, đối thoại |

---

## 🛠️ 9. API Reference Tóm Tắt (FastAPI Endpoints)

| Phương thức | Endpoint | Chức năng | Body / Params |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/generate` | Sinh âm thanh hàng loạt theo kịch bản | `GenerateRequest` (Text, Voice, Settings...) |
| `POST` | `/api/parse` | Phân tích cấu trúc kịch bản trước khi render | `ParseRequest` (`text`, `default_name`) |
| `POST` | `/api/upload` | Nạp nội dung từ file `.txt` / `.docx` | `UploadFileRequest` (`filename`, `base64`) |
| `GET` | `/api/voices` | Lấy danh sách giọng đọc và preview | Query: `tag` |
| `GET` | `/api/folders` | Lấy danh sách các thư mục dự án đã tạo | — |
| `GET` | `/api/folder_files` | Lấy danh sách file trong thư mục dự án | Query: `folder` |
| `POST` | `/api/concat` | Ghép nối lại các file trong thư mục thủ công | `ConcatRequest` (`folder_name`, `merged_format`) |
| `POST` | `/api/open_folder` | Mở thư mục kết quả trên Windows Explorer | `OpenFolderRequest` |

---

## 📄 10. Giấy Phép & Ghi Nhận (License & Credits)

- **Kiến trúc cốt lõi ZeroTTS**: Thuộc về [ZeroWeight AI](https://zeroweight.ai/) theo giấy phép MIT License.
- **Bản Mod TSS Studio**: Phát triển và đóng gói bởi **RevenantKitana** với các tính năng mở rộng phục vụ quy trình xử lý âm thanh tự động.
