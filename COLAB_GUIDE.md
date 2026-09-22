# 📖 Hướng Dẫn Chạy Toàn Bộ Mã Nguồn TSS Trên Google Colab (Free Tier)

Hệ thống đã được thiết lập để bạn có thể mang **chính xác toàn bộ mã nguồn của bạn** (bao gồm WebUI tùy chỉnh, tính năng đọc tag `[Câu 1]`, `#[Bỏ qua]`, chèn `[pause: 1.5s]`, gộp `_FULL_MERGED.mp3`, streaming audio) lên **Google Colab Free Tier**, tận dụng GPU T4 15GB VRAM.

---

## 📦 Bước 1: Đóng Gói Mã Nguồn Tùy Chỉnh (Chỉ 1 Click)

1. Tại thư mục dự án trên máy tính, bạn chỉ cần nhấp đúp vào file:
   👉 [`tao_file_zip_colab.bat`](file:///c:/Users/ADMIN/Downloads/TSS-VIE/tao_file_zip_colab.bat) (hoặc chạy lệnh `python package_colab_zip.py`).
2. Script sẽ tự động gom toàn bộ mã nguồn `src/`, `webui/`, `HD.md`, cùng toàn bộ các gói giọng (`Voice_ZeroTTS_model/voices/`) trên máy thành 1 file duy nhất:
   👉 **`TSS_Code.zip`** (Dung lượng siêu nhẹ ~4.9 MB).

---

## 🚀 Bước 2: Chạy Trên Google Colab

### Cách 1 (Khuyên dùng - Nhanh nhất): Nạp Trực Tiếp Từ GitHub hoặc Google Drive
1. Mở [Google Colab](https://colab.research.google.com) và mở file [`ZeroTTS_Colab_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Colab_FreeTier.ipynb) (hoặc nạp link GitHub `https://github.com/RevenantKitana/TSS`).
2. Bật GPU T4: Vào **Runtime** -> **Change runtime type** -> Chọn **T4 GPU** -> Nhấn **Save**.
3. Chọn **Runtime** -> **Run all (Chạy tất cả)**:
   - Colab sẽ tự đồng bộ mã nguồn và thư mục `Voice_ZeroTTS_model/voices`, tải model weights và khởi động server.
   - Khi chạy đến **Bước 5**, bạn chỉ cần bấm vào đường link **Public URL** (`https://xxxx.trycloudflare.com`) để mở WebUI Studio!

### Cách 2: Tải lên trực tiếp từ máy tính trong Colab
- Nếu chưa tải file zip lên Google Drive, khi chạy đến **Bước 2** trong Notebook, một nút **Choose Files (Chọn tệp)** sẽ xuất hiện. Bạn chỉ cần bấm vào và chọn file `TSS_Code.zip` từ máy tính.

---

## 🎯 Toàn Bộ Tính Năng Đã Tích Hợp Đầy Đủ:
- ✅ **Đồng nhất giọng đọc 100%**: Toàn bộ file embedding của từng giọng (`voice.npz`, `meta.json`, `voice.bin`) được nạp trực tiếp từ máy local lên Colab, không bị ghi đè bởi model gốc Hugging Face.
- ✅ **Trình biên soạn & Phân tích Tag**: Hỗ trợ đầy đủ cú pháp theo [HD.md](file:///c:/Users/ADMIN/Downloads/TSS-VIE/HD.md) (`[Câu 1]`, `#[Bỏ qua]`, `[pause: 1.5s]`, `[Kết Thúc]`).
- ✅ **Tăng tốc GPU T4**: Tự động dùng `CUDAExecutionProvider` giúp sinh giọng nói siêu tốc.
- ✅ **Lưu trữ Google Drive**: Tự động đồng bộ các file `outputs/` về `MyDrive/ZeroTTS_Outputs` trên Google Drive.
- ✅ **Cloudflare Tunnel**: Đường truyền HTTPS an toàn, nghe stream mượt mà không lo đứt đoạn.

---

## 💻 Cách 2: Chạy Bằng Lệnh Nhanh (Terminal / Python Script)

Nếu bạn muốn khởi chạy trực tiếp qua dòng lệnh trên Colab / máy chủ Linux từ xa:

```bash
# 1. Cài đặt hệ thống & thư viện
apt-get update -qq && apt-get install -y ffmpeg libportaudio2
pip install onnxruntime-gpu soundfile sounddevice fastapi uvicorn tokenizers huggingface_hub scipy requests
pip install -e .

# 2. Khởi chạy WebUI kèm Cloudflare Tunnel tự động
python colab_runner.py
```

Khi chạy xong, terminal sẽ in ra đường link Public HTTPS để bạn truy cập.

---

## ⚡ Ưu Điểm Khi Chạy Trên Colab Free Tier

| Tính năng | Lợi ích |
| :--- | :--- |
| **GPU T4 15GB VRAM** | Tốc độ sinh giọng cực nhanh (Real-Time Factor < 0.1s, 10s audio chỉ mất ~1s render). |
| **Không tốn RAM/CPU máy thật** | Phù hợp cho máy yếu, laptop văn phòng hoặc điện thoại. |
| **Cloudflare Tunnel** | Truy cập từ bất kỳ trình duyệt nào mà không cần cài đặt phần mềm phụ trợ, không cần token. |
| **Tự động lưu Google Drive** | Không lo mất dữ liệu khi ngắt kết nối session Colab. |
