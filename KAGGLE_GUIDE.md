# 📖 Hướng Dẫn Chạy Toàn Bộ Mã Nguồn TSS Trên Kaggle (GPU Free Tier)

Kaggle cung cấp **GPU miễn phí lên tới 30 giờ/tuần** (sử dụng GPU NVIDIA **T4 x2** 16GB hoặc **P100** 16GB VRAM, thời gian mỗi session tối đa lên tới 12 giờ liên tục).

Notebook [`ZeroTTS_Kaggle_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Kaggle_FreeTier.ipynb) đã được thiết lập để **tự động nạp trực tiếp mã nguồn từ GitHub [RevenantKitana/TSS](https://github.com/RevenantKitana/TSS)** mà không cần phải nén hay tải file zip thủ công.

---

## ⚡ 2 Thiết Lập Bắt Buộc Trước Khi Chạy Trên Kaggle

Trước khi bấm chạy notebook, bạn nhìn sang cột **Notebook settings** (ở cạnh bên phải màn hình Kaggle):

1. **Accelerator**: Chọn **GPU T4 x2** (hoặc **GPU P100**).
2. **Internet**: Chuyển công tắc **Internet** sang **ON** *(Bắt buộc bật để notebook tải mã nguồn từ GitHub, tải mô hình weights từ Hugging Face và tạo đường hầm Cloudflare Tunnel)*.

> 🔴 **Nếu bạn gặp lỗi: `Error: Permission 'kernelSessions.enableInternet' was denied`**  
> 👉 **Nguyên nhân**: Tài khoản Kaggle cần **Xác minh số điện thoại (Phone Verification)** 1 lần duy nhất để Kaggle mở quyền truy cập Internet và cấp 30h GPU/tuần miễn phí (chống bot).  
> 👉 **Cách sửa cực nhanh (1 phút)**:
> 1. Mở trang cài đặt: [https://www.kaggle.com/settings](https://www.kaggle.com/settings)
> 2. Cuộn xuống mục **Phone Verification** -> Nhập số điện thoại của bạn (chọn cờ Việt Nam `+84`, bỏ số 0 ở đầu).
> 3. Nhập mã OTP 6 số gửi về SMS để xác nhận.
> 4. Quay lại Notebook, F5 tải lại trang và gạt **Internet sang ON** là thành công ngay!

---

## 🚀 Khởi Chạy 2 Bước Trên Kaggle (Tối Ưu Cho Non-Tech)

1. **Tải Notebook lên Kaggle**:
   - Truy cập [Kaggle Notebooks](https://www.kaggle.com/code) -> Bấm nút **New Notebook**.
   - Trên menu trên cùng, chọn **File** -> **Upload Notebook** -> Chọn file [`ZeroTTS_Kaggle_FreeTier.ipynb`](file:///e:/Tools/TSS-main/ZeroTTS_Kaggle_FreeTier.ipynb).
2. **Bật GPU & Internet**:
   - Ở cột bên phải (**Settings**): Chọn **Accelerator: GPU T4 x2** và bật **Internet: ON**.
3. **Quy trình chỉ đúng 2 bước:**
   - **Bước 1 (Cài Đặt Trọn Gói A-Z):** Bấm nút Play (▶️) để tự động tải mã nguồn, cài đặt thư viện và nạp mô hình AI (~2 phút).
   - **Bước 2 (Khởi Chạy WebUI):** Bấm nút Play (▶️) -> Nhấp vào nút màu tím hiển thị trên màn hình để mở WebUI Studio!
