# 📖 Hướng Dẫn Chạy Toàn Bộ Mã Nguồn TSS Trên Google Colab (Free Tier)

Hệ thống đã được thiết lập để **tự động nạp trực tiếp toàn bộ mã nguồn mới nhất từ GitHub [RevenantKitana/TSS](https://github.com/RevenantKitana/TSS)** lên **Google Colab Free Tier**, tận dụng GPU T4 15GB VRAM.

---

## 🚀 Khởi Chạy 1-Click Trên Google Colab

1. Mở [Google Colab](https://colab.research.google.com) và tải lên file [`ZeroTTS_Colab_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Colab_FreeTier.ipynb).
2. Bật GPU T4: Vào **Runtime** -> **Change runtime type** -> Chọn **T4 GPU** -> Nhấn **Save**.
3. Chọn **Runtime** -> **Run all (Chạy tất cả)**:
   - Colab sẽ tự động kết nối Google Drive, clone mã nguồn mới nhất từ GitHub `https://github.com/RevenantKitana/TSS`, cài đặt môi trường và tải trọng số mô hình.
   - Khi chạy đến **Bước 5**, bạn chỉ cần bấm vào đường link **Public URL** (`https://xxxx.trycloudflare.com`) để mở WebUI!

---

## 🎯 Toàn Bộ Tính Năng Đã Tích Hợp Đầy Đủ:
- ✅ **Trình biên soạn & Phân tích Tag**: Hỗ trợ đầy đủ cú pháp theo [HD.md](file:///e:/Tools/TSS-main/HD.md) (`[Câu 1]`, `#[Bỏ qua]`, `[pause: 1.5s]`, `[Kết Thúc]`).
- ✅ **Tăng tốc GPU T4**: Tự động dùng `CUDAExecutionProvider` giúp sinh giọng nói siêu tốc.
- ✅ **Lưu trữ Google Drive**: Tự động đồng bộ các file `outputs/` về `MyDrive/ZeroTTS_Outputs` trên Google Drive.
- ✅ **Cloudflare Tunnel**: Đường truyền HTTPS an toàn, nghe stream mượt mà không lo đứt đoạn.
