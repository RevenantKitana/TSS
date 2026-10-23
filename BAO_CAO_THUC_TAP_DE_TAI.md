# 📘 BÁO CÁO KỸ THUẬT & ĐỐI CHIẾU ĐỀ TÀI: TSS STUDIO (ZEROTTS MOD)
### *Hệ thống Tự Động Hóa Sản Xuất Âm Thanh Quy Mô Lớn Dựa Trên Mô Hình Zero-Shot TTS Tiếng Việt*

---

## 📑 MỤC LỤC
1. [Xác Lập Đề Tài & Tính Phù Hợp Cho Báo Cáo Thực Tập](#1-xác-lập-đề-tài--tính-phù-hợp-cho-báo-cáo-thực-tập)
2. [Bảng Ma Trận Đối Chiếu: Bản Gốc vs Bản Phát Triển](#2-bảng-ma-trận-đối-chiếu-bản-gốc-vs-bản-phát-triển)
3. [Phân Tích Chi Tiết 8 Trọng Tâm Kỹ Thuật Đã Phát Triển](#3-phân-tích-chi-tiết-8-trọng-tâm-kỹ-thuật-đã-phát-triển)
   - 3.1. [Kiến Trúc Giao Diện & Trải Nghiệm (WebUI Studio)](#31-kiến-trúc-giao-diện--trải-nghiệm-webui-studio)
   - 3.2. [Cú Pháp Kịch Bản & Tiền Xử Lý Ngôn Ngữ](#32-cú-pháp-kịch-bản--tiền-xử-lý-ngôn-ngữ)
   - 3.3. [Thuật Toán Cắt Đoạn Thích Ứng (Adaptive Chunker)](#33-thuật-toán-cắt-đoạn-thích-ứng-adaptive-chunker)
   - 3.4. [Cơ Chế Chịu Lỗi & Phục Hồi Tiến Trình (Fault-Tolerance & Resume)](#34-cơ-chế-chịu-lỗi--phục-hồi-tiến-trình-fault-tolerance--resume)
   - 3.5. [Hệ Thống Ghép Nối Âm Thanh & Xuất Metadata Timeline](#35-hệ-thống-ghép-nối-âm-thanh--xuất-metadata-timeline)
   - 3.6. [Bảo Mật, Xác Thực & Phân Vùng Lưu Trữ Đa Cấp](#36-bảo-mật-xác-thực--phân-vùng-lưu-trữ-đa-cấp)
   - 3.7. [Tối Ưu Hóa Bộ Suy Luận & Quản Lý Giọng Nói](#37-tối-ưu-hóa-bộ-suy-luận--quản-lý-giọng-nói)
   - 3.8. [Bộ Công Cụ Triển Khai Tự Động Hóa (DevOps & Cloud Notebooks)](#38-bộ-công-cụ-triển-khai-tự-động-hóa-devops--cloud-notebooks)
4. [Đánh Giá Quy Mô & Tính Thực Tiễn Ứng Dụng](#4-đánh-giá-quy-mô--tính-thực-tiễn-ứng-dụng)
5. [Khung Sườn Báo Cáo Thực Tập Chuẩn Học Thuật (5 Chương)](#5-khung-sườn-báo-cáo-thực-tập-chuẩn-học-thuật-5-chương)

---

## 1. XÁC LẬP ĐỀ TÀI & TÍNH PHÙ HỢP CHO BÁO CÁO THỰC TẬP

### 1.1. Lý do chọn đề tài
* **Thực trạng:** Mô hình Text-to-Speech (TTS) mã nguồn mở tiếng Việt như [ZeroTTS](https://github.com/zeroweight-ai/ZeroTTS) sở hữu khả năng nhân bản giọng đọc (Zero-shot Voice Cloning) và tốc độ suy luận nhanh trên CPU/GPU. Tuy nhiên, bản gốc chỉ dừng lại ở mức độ thư viện thử nghiệm (*Proof of Concept - PoC*), chưa thể đưa vào ứng dụng sản xuất công nghiệp do thiếu: công cụ chia đoạn kịch bản dài, cơ chế chống sập khi gặp lỗi, quy trình tự động ghép nối âm thanh, giao diện quản lý lịch sử và lớp bảo mật phân quyền.
* **Mục tiêu nghiên cứu:** Xây dựng một hệ thống **Audio Production Pipeline** hoàn chỉnh trên nền tảng ZeroTTS, biến động cơ TTS thô thành một giải pháp phần mềm chuyên nghiệp phục vụ sản xuất sách nói, bài giảng điện tử (e-learning) và tự động hóa video.

### 1.2. Tên đề tài khuyến nghị
1. **Hướng Kỹ thuật phần mềm & Xử lý đa phương tiện (Khuyên dùng):**
   > *"Nghiên cứu và phát triển hệ thống tự động hóa sản xuất âm thanh quy mô lớn dựa trên mô hình Zero-Shot TTS tiếng Việt"*
2. **Hướng Kiến trúc hệ thống & MLOps:**
   > *"Thiết kế và triển khai nền tảng Text-to-Speech dạng dịch vụ (TTS-as-a-Service) với cơ chế chịu lỗi và cách ly lưu trữ đa cấp"*
3. **Hướng Ứng dụng nghiệp vụ:**
   > *"Xây dựng hệ thống Studio chuyển đổi văn bản thành giọng nói phục vụ quy trình sản xuất sách nói và bài giảng điện tử"*

---

## 2. BẢNG MA TRẬN ĐỐI CHIẾU: BẢN GỐC VS BẢN PHÁT TRIỂN

| Hạng mục so sánh | Bản gốc ZeroTTS (`zeroweight-ai`) | Bản Nâng Cấp TSS Studio (Codebase của bạn) |
| :--- | :--- | :--- |
| **Mục tiêu hệ thống** | Thư viện suy luận AI cơ bản | Nền tảng Studio sản xuất âm thanh hoàn chỉnh |
| **Giao diện Web** | Gradio mẫu (`gradio>=4.44.0`) | SPA chuyên nghiệp: HTML5/CSS3/JS + FastAPI REST Server |
| **Giao tiếp Realtime** | Polling cơ bản của Gradio | Server-Sent Events (SSE) truyền trực tiếp log và thanh tiến trình |
| **Quản lý Lịch sử** | Danh sách file phẳng, rời rạc | Master-Detail Folder Viewer, phân cấp theo từng dự án |
| **Cú pháp Kịch bản** | Chỉ nhận văn bản thuần thô sơ | Hỗ trợ thẻ `[Tag]`, `[pause: ...]`, `#[skip]`, `$[Dự_Án]` |
| **Hỗ trợ định dạng nạp** | Nhập tay qua ô Textbox | Nạp trực tiếp file `.txt` và Microsoft Word `.docx` |
| **Thuật toán cắt văn bản** | Cắt thô theo ký tự cố định | `AdaptiveChunker`: 4 Preset, tìm ranh giới 2 chiều, retry thông minh |
| **Chống sập (Fault-Tolerance)** | Lỗi 1 câu làm dừng toàn bộ tiến trình | Bọc `try..except` độc lập từng block, chế độ **Skip Existing / Resume** |
| **Hậu kỳ & Ghép nối** | ❌ Không hỗ trợ | ✅ Tích hợp FFmpeg tự ghép `_FULL_MERGED` (WAV, MP3, FLAC, M4A, OGG) |
| **Dữ liệu Timeline** | ❌ Không có | ✅ Tự động trích xuất `_mapping.txt` và `info.json` mốc thời gian |
| **Xác thực & Bảo mật** | ❌ Không có | ✅ Phân quyền API Key, Rate-limiting, cách ly 2-tier (Key vs Guest) |
| **Tăng tốc phần cứng** | Thủ công cấu hình ONNX Runtime | Tự động phát hiện & preload CUDA/cuDNN, tự động fallback về CPU |
| **Triển khai tự động** | Dòng lệnh `pip install` thủ công | Script 1-Click: Windows (`.bat`), Linux Daemon (`.sh`), Colab & Kaggle |

---

## 3. PHÂN TÍCH CHI TIẾT 8 TRỌNG TÂM KỸ THUẬT ĐÃ PHÁT TRIỂN

### 3.1. Kiến Trúc Giao Diện & Trải Nghiệm (WebUI Studio)
* **Bản gốc:** Sử dụng framework Gradio qua file [`webui/app.py`](file:///e:/Tools/TSS-main/webui/app.py). Giao diện có độ trễ lớn, khó tùy biến sâu và không hỗ trợ các tính năng hậu kỳ.
* **Sau khi phát triển:**
  * **Frontend SPA độc lập:** Xây dựng hơn 4.300 dòng mã nguồn tại thư mục [`webui/static/`](file:///e:/Tools/TSS-main/webui/static/) gồm:
    * [`index.html`](file:///e:/Tools/TSS-main/webui/static/index.html): Cấu trúc giao diện Studio hiện đại.
    * [`style.css`](file:///e:/Tools/TSS-main/webui/static/style.css): Hệ thống theme Dark/Light, responsive, micro-animations.
    * [`app.js`](file:///e:/Tools/TSS-main/webui/static/app.js): Trình phát âm thanh tích hợp Waveform visualizer, kết nối SSE.
  * **Backend chuyên dụng:** [`webui/server.py`](file:///e:/Tools/TSS-main/webui/server.py) viết bằng **FastAPI**, cung cấp hệ thống REST API hoàn chỉnh (`/api/generate`, `/api/parse`, `/api/upload`, `/api/folders`, `/api/concat`...).
  * **Master-Detail History Viewer:** Quản lý lịch sử trực quan theo cấu trúc cây thư mục, cho phép nghe thử từng câu, tải file tổng hợp và thực hiện ghép nối lại tức thì.

### 3.2. Cú Pháp Kịch Bản & Tiền Xử Lý Ngôn Ngữ
* **Bản gốc:** Văn bản đầu vào chỉ là chuỗi text đơn thuần.
* **Sau khi phát triển:**
  * Xây dựng bộ Parser Regex đa tầng trong [`webui/engine.py`](file:///e:/Tools/TSS-main/webui/engine.py) và [`src/zerotts/chunking.py`](file:///e:/Tools/TSS-main/src/zerotts/chunking.py):
    * `[Tag_Name]`: Phân tách kịch bản thành các khối audio riêng biệt.
    * `[pause: 1.5s]` / `[wait: 500ms]`: Tự động chèn frame khoảng lặng âm thanh chuẩn xác (*silence frames*) vào đúng vị trí chỉ định mà không làm méo âm.
    * `#[Tag]` / `[skip: Tag]`: Bỏ qua các đoạn nháp hoặc các câu đã render đạt chuẩn từ trước.
    * `$[Tên_Dự_Án]`: Gom nhóm hàng chục phân đoạn vào các thư mục dự án tương ứng.
    * Tích hợp thư viện `python-docx` để nạp trực tiếp tài liệu Word.

### 3.3. Thuật Toán Cắt Đoạn Thích Ứng (Adaptive Chunker)
* **Bản gốc:** Cắt câu đơn giản dựa trên độ dài chuỗi hoặc dấu ngắt câu cơ bản trong [`src/zerotts/chunking.py`](file:///e:/Tools/TSS-main/src/zerotts/chunking.py), dễ gây mất chữ hoặc nuốt từ ở ranh giới.
* **Sau khi phát triển:**
  * Bổ sung module độc lập [`src/zerotts/adaptive_chunker.py`](file:///e:/Tools/TSS-main/src/zerotts/adaptive_chunker.py) (~480 dòng code):
    * **Bidirectional Boundary Search:** Tìm kiếm ranh giới tối ưu 2 chiều theo thứ tự ưu tiên: *Sentence* (`. ! ? …`) ➔ *Clause* (`, ; : —`) ➔ *Word* ➔ *Hard Cut*.
    * **4 Preset cấu hình:** `Small` (256 ký tự), `Medium` (384 ký tự), `Large` (512 ký tự), `X-Large` (768 ký tự).
    * **No-gap, No-overlap:** Đảm bảo bảo toàn 100% nội dung gốc của văn bản.
    * **Render Orchestrator:** Cơ chế tự động băm nhỏ riêng khối bị lỗi (*Adaptive Sub-chunking*) và thử lại (*retry*) tự động khi quá trình suy luận gặp trục trặc.

### 3.4. Cơ Chế Chịu Lỗi & Phục Hồi Tiến Trình (Fault-Tolerance & Resume)
* **Bản gốc:** Vòng lặp đơn luồng. Khi sinh kịch bản dài gồm 50-100 câu, chỉ cần 1 câu bị lỗi ký tự hoặc tràn bộ nhớ đệm, chương trình sẽ lập tức thoát, gây mất toàn bộ kết quả đã sinh.
* **Sau khi phát triển:**
  * **Cô lập ngoại lệ từng block:** Mỗi câu được bọc riêng trong khối `try...except`. Nếu một câu thất bại, hệ thống ghi nhận trạng thái `[FAILED]` và tiếp tục chạy hết toàn bộ các câu còn lại.
  * **Chế độ Skip Existing / Resume:** Tự động đối chiếu các tệp `.wav` đã có sẵn trên ổ đĩa. Khi gặp sự cố mạng hoặc khởi động lại tiến trình, hệ thống chỉ sinh tiếp những câu còn thiếu, tiết kiệm đáng kể thời gian và tài nguyên tính toán.

### 3.5. Hệ Thống Ghép Nối Âm Thanh & Xuất Metadata Timeline
* **Bản gốc:** Chỉ tạo ra các file `.wav` lẻ tẻ, không có công cụ hậu kỳ.
* **Sau khi phát triển:**
  * **Engine FFmpeg tích hợp sẵn:**
    * Tự động ghép nối các câu đơn lẻ thành tệp tổng hợp `_FULL_MERGED`.
    * Đa dạng hóa định dạng xuất xưởng: `WAV Lossless`, `MP3 (320, 192, 128 kbps)`, `FLAC`, `M4A (AAC)`, `OGG`.
    * Bộ lọc thông minh tự động loại bỏ các tệp `_FULL_MERGED` cũ để ngăn lỗi lặp âm vô tận.
  * **Xuất dữ liệu thời gian phục vụ dựng video:**
    * **`_mapping.txt`:** Xuất timeline định dạng mốc chuẩn `[00:00:00.000 -> 00:00:04.250]`.
    * **`info.json`:** Xuất metadata cấu trúc chi tiết (thời lượng, timestamp từng câu, cấu hình giọng đọc, trạng thái hoàn thành).

### 3.6. Bảo Mật, Xác Thực & Phân Vùng Lưu Trữ Đa Cấp
* **Bản gốc:** Không hỗ trợ bảo mật; bất kỳ ai truy cập cũng có thể làm nghẽn tiến trình hoặc can thiệp dữ liệu.
* **Sau khi phát triển:**
  * Bổ sung module xác thực và phân quyền trong [`webui/auth.py`](file:///e:/Tools/TSS-main/webui/auth.py) và [`webui/manage_keys.py`](file:///e:/Tools/TSS-main/webui/manage_keys.py):
    * **Key Users (Thành viên):** Được cấp API Key, sở hữu thư mục lưu trữ vĩnh viễn (`outputs/keys/<storage_slug>/`), miễn nhiễm với cơ chế dọn dẹp tự động.
    * **Guest Users (Khách dùng thử):** Lưu trữ trong thư mục phiên tạm thời (`outputs/ephemeral/<session_id>/`), tự động dọn dẹp sau 30 phút hoặc khi vượt quá định ngạch dung lượng.
    * **Rate-Limiting:** Thuật toán giới hạn tốc độ yêu cầu chống quá tải server.
    * Script quản lý khóa tự động qua [`manage_keys.sh`](file:///e:/Tools/TSS-main/manage_keys.sh).

### 3.7. Tối Ưu Hóa Bộ Suy Luận & Quản Lý Giọng Nói
* **Bản gốc:** Mặc định chạy CPU. Việc kích hoạt GPU qua ONNX Runtime đòi hỏi cấu hình môi trường CUDA/cuDNN thủ công rất dễ lỗi.
* **Sau khi phát triển:**
  * **Tự động cấu hình CUDA ([`src/zerotts/synthesizer.py`](file:///e:/Tools/TSS-main/src/zerotts/synthesizer.py)):**
    * Hàm `_setup_cuda_environment()` tự động phát hiện đường dẫn và nạp trước (*preload*) các thư viện động liên quan của NVIDIA (`libcudart`, `libcublas`, `libcudnn`...).
    * Cơ chế **Graceful Fallback:** Tự động ưu tiên `CUDAExecutionProvider`, nếu môi trường thiếu driver sẽ chuyển đổi mượt mà sang `CPUExecutionProvider` mà không làm dừng ứng dụng.
  * **Nạp Voice đa định dạng ([`src/zerotts/voices.py`](file:///e:/Tools/TSS-main/src/zerotts/voices.py)):**
    * Hỗ trợ đồng thời cả `voice.npz` và file nhị phân raw `voice.bin`.
    * Tự động nhận diện Git LFS Pointer và tự thực thi `git lfs pull` khôi phục dữ liệu.
    * Chuẩn hóa danh mục gói giọng đọc tiếng Việt kèm thông tin vùng miền và giới tính tại [`Voice_ZeroTTS_model/voices/`](file:///e:/Tools/TSS-main/Voice_ZeroTTS_model/voices/).

### 3.8. Bộ Công Cụ Triển Khai Tự Động Hóa (DevOps & Cloud Notebooks)
* **Bản gốc:** Thiếu các công cụ triển khai tự động hóa.
* **Sau khi phát triển:**
  * **Windows 1-Click:** [`run_webui.bat`](file:///e:/Tools/TSS-main/run_webui.bat) tự động khởi tạo môi trường Python `.venv`, tải `ffmpeg.exe`, nạp trọng số mô hình và khởi chạy Studio.
  * **Linux/Ubuntu Daemon:** [`install.sh`](file:///e:/Tools/TSS-main/install.sh) và [`zerotts.sh`](file:///e:/Tools/TSS-main/zerotts.sh) (>1.000 dòng bash script) hỗ trợ triển khai dịch vụ ngầm, tự khởi động cùng máy chủ và cron job dọn dẹp bộ nhớ tạm.
  * **Môi trường Cloud Miễn phí:**
    * [`ZeroTTS_Colab_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Colab_FreeTier.ipynb): Khởi chạy WebUI Studio qua Cloudflare Tunnel trên GPU T4 miễn phí.
    * [`ZeroTTS_Colab_Headless.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Colab_Headless.ipynb): Chạy batch ngầm xuất âm thanh trực tiếp vào Google Drive.
    * [`ZeroTTS_Kaggle_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Kaggle_FreeTier.ipynb): Tối ưu chạy song song trên môi trường Kaggle.
  * **Quản trị Cloud VM:** Thư mục [`VM/`](file:///e:/Tools/TSS-main/VM/) chứa các script SSH và giám sát tài nguyên cho máy chủ đám mây (Oracle Cloud VM).

---

## 4. ĐÁNH GIÁ QUY MÔ & TÍNH THỰC TIỄN ỨNG DỤNG

### 4.1. Quy mô kỹ thuật
* **Khối lượng mã nguồn:** Bổ sung hơn **15.500 dòng code mới**, can thiệp từ tầng thuật toán chia đoạn, cấu hình suy luận ONNX, tầng dịch vụ backend REST API, giao diện SPA đến các script DevOps.
* **Độ sâu công nghệ:** Kết hợp đa ngành:
  * *Trí tuệ nhân tạo (AI/ML):* Zero-shot TTS, ONNX Runtime, CUDA Acceleration.
  * *Kỹ thuật phần mềm (Software Engineering):* Kiến trúc RESTful, SSE Streaming, Idempotency, Resume Pattern.
  * *Bảo mật & Hệ thống (Systems & Security):* Rate-limiting, Multi-tier storage isolation, Ephemeral resource pruning.

### 4.2. Tính thực tiễn trong đời sống & sản xuất
1. **Xuất bản số & Sản xuất Sách nói (Audiobooks):** Cho phép biên tập viên nạp toàn bộ một cuốn sách dạng `.docx`, tự động phân tách theo từng chương, chèn ngắt nghỉ và xuất ra tệp âm thanh hoàn chỉnh chỉ trong vài phút.
2. **Sản xuất Video & Bài giảng điện tử (E-learning):** Nhờ tệp `_mapping.txt`, các phần mềm dựng video có thể tự động căn khớp âm thanh với phụ đề và từng slide bài giảng mà không cần kỹ thuật viên phải cắt ghép thủ công.
3. **Tiết kiệm chi phí vận hành:** Tận dụng linh hoạt CPU máy tính cá nhân hoặc các nền tảng GPU Cloud miễn phí, giúp cá nhân và doanh nghiệp nhỏ tiết kiệm hàng nghìn USD chi phí thuê dịch vụ đọc giọng nước ngoài.

---

## 5. KHUNG SƯỜN BÁO CÁO THỰC TẬP CHUẨN HỌC THUẬT (5 CHƯƠNG)

Dưới đây là dàn ý cấu trúc báo cáo thực tập chi tiết để bạn có thể áp dụng trực tiếp vào tài liệu Word:

### CHƯƠNG 1: TỔNG QUAN VỀ ĐỀ TÀI & CƠ SỞ LÝ THUYẾT
* 1.1. Bối cảnh ứng dụng công nghệ Text-to-Speech (TTS) trong kỷ nguyên số.
* 1.2. Thách thức trong việc chuyển đổi các mô hình AI nghiên cứu thành sản phẩm công nghiệp.
* 1.3. Khảo sát mô hình gốc ZeroTTS (Kiến trúc mô hình, ưu điểm và các hạn chế tồn tại).
* 1.4. Mục tiêu, đối tượng và phạm vi nghiên cứu của đề tài.

### CHƯƠNG 2: PHÂN TÍCH YÊU CẦU & THIẾT KẾ KIẾN TRÚC HỆ THỐNG
* 2.1. Phân tích yêu cầu nghiệp vụ (Xử lý kịch bản dài, chèn khoảng lặng, phục hồi tiến trình, ghép nối âm thanh).
* 2.2. Phân tích yêu cầu phi chức năng (Tính sẵn sàng cao, hiệu năng suy luận, bảo mật đa người dùng).
* 2.3. Thiết kế kiến trúc tổng thể của hệ thống TSS Studio (Mô hình 5 tầng: Presentation ➔ API Gateway ➔ NLP Processing ➔ AI Inference ➔ Media Storage).
* 2.4. Thiết kế cơ chế lưu trữ phân tầng (Permanent Key Storage vs Ephemeral Guest Storage).

### CHƯƠNG 3: HIỆN THỰC HÓA CÁC PHÂN HỆ NÂNG CAO
* 3.1. Hiện thực hóa thuật toán cắt văn bản thích ứng (`AdaptiveChunker`) và cơ chế retry tự động.
* 3.2. Hiện thực hóa bộ phân tích cú pháp kịch bản Regex đa phân đoạn (`[Tag]`, `[pause]`, `$[Folder]`).
* 3.3. Xây dựng cơ chế chống sập (Isolated Rendering) và khôi phục tiến trình (Skip Existing / Resume).
* 3.4. Tích hợp engine FFmpeg tự động ghép nối âm thanh đa định dạng và xuất mốc thời gian Timeline.
* 3.5. Xây dựng phân hệ xác thực API Key, kiểm soát tải (Rate-limiting) và dọn dẹp tài nguyên.
* 3.6. Xây dựng giao diện Studio SPA và cơ chế truyền dữ liệu thời gian thực qua Server-Sent Events (SSE).

### CHƯƠNG 4: TRIỂN KHAI THỬ NGHIỆM & ĐÁNH GIÁ HIỆU NĂNG
* 4.1. Môi trường thử nghiệm và cấu hình phần cứng (Windows Local, Google Colab T4, Kaggle Dual GPU, Oracle Cloud VM).
* 4.2. Đánh giá tốc độ suy luận (RTF - Real-Time Factor) trên CPU và GPU tăng tốc CUDA.
* 4.3. Kiểm thử tính toàn vẹn văn bản và độ chính xác của thuật toán cắt đoạn thích ứng.
* 4.4. Kiểm thử cơ chế phục hồi tiến trình khi xảy ra gián đoạn giả lập.
* 4.5. Đánh giá giao diện người dùng và độ trễ phản hồi qua Server-Sent Events.

### CHƯƠNG 5: KẾT LUẬN & HƯỚNG PHÁT TRIỂN
* 5.1. Các kết quả chính đã đạt được của đề tài.
* 5.2. Đánh giá những đóng góp mới so với dự án gốc ZeroTTS.
* 5.3. Các hạn chế còn tồn tại.
* 5.4. Đề xuất hướng phát triển tiếp theo (Hỗ trợ thêm giọng vùng miền mới, phát triển ứng dụng di động, tích hợp tự động đồng bộ phụ đề SRT).

---
*Tài liệu được biên soạn đồng bộ trực tiếp từ mã nguồn thực tế của dự án [TSS Studio](file:///e:/Tools/TSS-main/).*
