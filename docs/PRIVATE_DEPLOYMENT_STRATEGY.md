# 📘 CHIẾN LƯỢC TRIỂN KHAI PRIVATE REPOSITORY VỚI GITHUB TOKEN (PAT READ-ONLY)
> **Dự án:** ZeroTTS Studio (TSS)  
> **Tác giả ý tưởng:** Nguyễn Quốc Khánh  
> **Trạng thái:** Kiến trúc chuẩn hóa (Standard Architecture)

---

## 1. Đặt Vấn Đề & Bối Cảnh (Problem Statement)

Khi đưa mã nguồn dự án **ZeroTTS Studio** về chế độ **Private (Riêng tư)** nhằm bảo vệ tài sản trí tuệ và chống sao chép trái phép, bài toán đặt ra là: **Làm sao để triển khai tự động, mượt mà trên cả 2 môi trường mà không cần can thiệp thủ công lằng nhằng?**

1. **Production Cloud VM (Oracle Cloud ARM 3 OCPU / 18GB RAM):**
   * Triển khai từ xa qua mạng từ máy tính cá nhân (Windows).
   * Không muốn phải SSH vào máy ảo gõ lệnh tạo key thủ công hay cấu hình quyền file phức tạp.
   * Dễ dàng cập nhật code mới thường ngày (`git pull`) mà không bị chặn xác thực.
2. **Google Colab (Môi trường GPU Free-Tier / Headless):**
   * Máy ảo Colab mang tính chất tạm thời (ephemeral), tự hủy và xóa trắng sau mỗi phiên làm việc.
   * Không thể lưu file khóa SSH lâu dài.
   * Không được để lộ thông tin xác thực trong notebook (khi quay video màn hình, chia sẻ tài liệu hoặc xuất file `.ipynb`).

---

## 2. So Sánh Kiến Trúc: Deploy Key SSH vs. GitHub Token (PAT)

| Tiêu chí so sánh | Cách truyền thống: Deploy Key (SSH) | Giải pháp của bạn: GitHub Token (PAT Read-Only) |
| :--- | :--- | :--- |
| **Định dạng khóa** | Cặp file `id_ed25519` (Private) & `.pub` (Public) | 1 chuỗi ký tự text ngắn (`github_pat_...`) |
| **Thao tác trên VM** | Phải copy file `.key` sang `~/.ssh/`, gán `chmod 600`, cấu hình `~/.ssh/config` | **Zero-setup:** Nạp thẳng qua biến môi trường 1 dòng lệnh |
| **Tải file bootstrap (`install.sh`)** | Phải cấu hình API hoặc dùng token phụ | **Tải trực tiếp bằng `curl`** với header Authorization |
| **Thao tác trên Colab** | Cồng kềnh (mỗi lần bật Colab phải nạp lại file key) | **Native 1-Click:** Lưu vào **Colab Secrets (🔑)**, nạp ngầm tự động |
| **Rủi ro lộ bí mật** | Dễ vô tình commit file key hoặc paste vào cell | **An toàn tuyệt đối** qua cơ chế keyring của Google Colab |
| **Khả năng thu hồi (Revoke)** | Xóa deploy key trong Settings của repo | **Hủy tức thì** trong Developer Settings của GitHub |

> [!NOTE]
> **Kết luận:** GitHub Token (Fine-grained PAT Read-Only) giải quyết triệt để sự bất tiện của Deploy Key, tạo ra một trải nghiệm triển khai đồng nhất, liền mạch từ Local -> Cloud VM -> Google Colab.

---

## 3. Kiến Trúc Hoạt Động (Architecture & Workflows)

```mermaid
graph TD
    subgraph GITHUB [GitHub - Private Repository]
        Repo[Repo: RevenantKitana/TSS]
        Token[Fine-Grained PAT<br/>Scope: Contents Read-Only]
    end

    subgraph LOCAL [Máy Tính Cá Nhân - Windows]
        CodeLocal[Mã nguồn Local TSS]
        ConfigEnv[VM/vm_config.env<br/>GH_TOKEN=github_pat_...]
        BatScript[cai_dat_vm.bat<br/>Menu Quản trị từ xa]
    end

    subgraph VM [Production Cloud VM - Oracle Cloud]
        SSHAuth[Xác thực SSH Key]
        InstallScript[install.sh Bootstrap]
        GitConfig[TSS/.git/config<br/>Lưu URL xác thực ngầm]
        SystemdService[zerotts.service<br/>WebUI Port 7860]
    end

    subgraph COLAB [Google Colab - GPU / Headless]
        ColabSecret[Colab Secrets 🔑<br/>GH_TOKEN]
        ColabCell[Notebook Cell<br/>userdata.get('GH_TOKEN')]
        ColabApp[/content/TSS]
    end

    %% Local to GitHub & VM
    CodeLocal -->|git push origin main| Repo
    ConfigEnv -.->|Đọc token an toàn| BatScript
    BatScript -->|1. SSH truyền GH_TOKEN| SSHAuth
    SSHAuth -->|2. curl install.sh| InstallScript
    InstallScript -->|3. git clone với Token| Repo
    Repo -->|4. Kéo mã nguồn| GitConfig
    GitConfig --> SystemdService

    %% Colab
    Token -.->|Lưu vào Secrets| ColabSecret
    ColabSecret --> ColabCell
    ColabCell -->|git clone với Token| Repo
    Repo -->|Kéo mã nguồn| ColabApp
```

---

## 4. Chi Tiết Vận Hành Trên Từng Môi Trường

### 4.1. Môi trường Production Cloud VM (Oracle Cloud)

#### Bước 1: Bảo vệ Token tại máy trạm Windows
* Chuỗi Token được khai báo trong file `VM/vm_config.env`:
  ```env
  VM_IP=129.221.241.47
  VM_USER=ubuntu
  VM_KEY=129.221.241.47.key
  VM_PORT=22
  GH_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxx
  ```
* **Lớp bảo vệ:** File `vm_config.env` đã được cấu hình trong `.gitignore`, đảm bảo token không bao giờ bị lộ ra ngoài kho lưu trữ.

#### Bước 2: Cài đặt mới 1-Chạm (Fresh 1-Click Install)
* Người dùng mở `cai_dat_vm.bat` -> Bấm phím `[5]`.
* Lệnh SSH được tự động sinh ra và đẩy sang máy chủ:
  ```bash
  ssh -t -i "%VM_KEY%" %VM_USER%@%VM_IP% \
    "GH_TOKEN='$GH_TOKEN' curl -sSL -H 'Authorization: token $GH_TOKEN' https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh | GH_TOKEN='$GH_TOKEN' bash"
  ```
* Bên trong máy chủ, lệnh `git clone` sử dụng URL nhúng xác thực:
  ```bash
  git clone https://${GH_TOKEN}@github.com/RevenantKitana/TSS.git /home/ubuntu/TSS
  ```

#### Bước 3: Cơ chế tự động ghi nhớ để Cập nhật mã nguồn (Day-to-day Updates)
* Khi clone bằng cú pháp trên, Git sẽ tự động lưu URL vào file cấu hình `/home/ubuntu/TSS/.git/config`.
* Về sau, khi người dùng muốn cập nhật tính năng mới:
  1. Ở máy tính: `git push origin main`.
  2. Mở `cai_dat_vm.bat` -> Chọn `[6]` -> Chọn `[9] Cập nhật Mã nguồn từ GitHub`.
  3. Lệnh `git fetch origin` & `git checkout main` tự động xác thực thành công mà **không bao giờ hỏi mật khẩu hay token**.

---

### 4.2. Môi trường Google Colab (Free-Tier & Headless)

#### Bước 1: Lưu trữ qua Colab Secrets (Native Keyring)
* Trên giao diện Google Colab, mở thanh công cụ bên trái -> Nhấp biểu tượng chiếc chìa khóa **Secrets (🔑)**.
* Thêm Secret mới:
  * **Name:** `GH_TOKEN`
  * **Value:** `github_pat_xxxxxxxxxxxxxxxxxxxx`
  * Bật công tắc: **Notebook access** (Cho phép notebook đọc giá trị).

#### Bước 2: Đọc biến ngầm trong Notebook
* Cell nạp mã nguồn trong `ZeroTTS_Colab_FreeTier.ipynb` và `ZeroTTS_Colab_Headless.ipynb` sẽ sử dụng thư viện chuẩn của Google Colab:
  ```python
  import os
  import subprocess
  from google.colab import userdata

  try:
      gh_token = userdata.get('GH_TOKEN')
      repo_url = f"https://{gh_token}@github.com/RevenantKitana/TSS.git"
  except Exception:
      repo_url = "https://github.com/RevenantKitana/TSS.git"

  subprocess.run(["git", "clone", repo_url, "/content/TSS"], check=True)
  ```
* **Lợi thế:** Mã token được Google che giấu hoàn toàn trong bộ nhớ kernel, không xuất hiện ở text cell, không xuất hiện ở console log.

---

## 5. Phân Tích Mô Hình An Toàn & Bảo Mật (Threat & Security Model)

```
                       CƠ CHẾ BẢO VỆ 3 LỚP (DEFENSE IN DEPTH)
  ┌────────────────────────────────────────────────────────────────────────┐
  │ 1. NGUYÊN TẮC ĐẶC QUYỀN TỐI THIỂU (LEAST PRIVILEGE)                    │
  │    • Phạm vi giới hạn: Đúng 1 repository `RevenantKitana/TSS`.         │
  │    • Quyền hạn: Duy nhất `Contents: Read`.                             │
  │    • Nguy cơ: Kẻ xấu không thể sửa code, không thể xóa code, không thể │
  │      đụng tới các repository khác trong tài khoản GitHub.              │
  ├────────────────────────────────────────────────────────────────────────┤
  │ 2. CÔ LẬP KHÔNG GIAN LƯU TRỮ (STORAGE ISOLATION)                       │
  │    • Local: Nằm trong file ignored `.env`, không bao giờ commit.       │
  │    • Colab: Mã hóa trong Google Cloud IAM Secrets của người dùng.      │
  │    • VM: Thuộc sở hữu user `ubuntu`, phân quyền file hệ thống tiêu chuẩn.│
  ├────────────────────────────────────────────────────────────────────────┤
  │ 3. NÚT DỪNG KHẨN CẤP (INSTANT KILL-SWITCH)                             │
  │    • Nếu nghi ngờ lộ token: Vào GitHub Settings bấm 1 nút Revoke.      │
  │    • Ngay lập tức mọi quyền tải mã nguồn trên VM và Colab bị vô hiệu.  │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Hướng Dẫn Thiết Lập Nhanh (Quick Setup Checklist)

- [ ] **Bước 1 (GitHub):** Vào `GitHub Settings` -> `Developer Settings` -> `Personal access tokens` -> `Fine-grained tokens` -> Chọn repo `TSS` -> Cấp quyền `Contents: Read-only` -> Copy token `github_pat_...`.
- [ ] **Bước 2 (Chuyển Repo sang Private):** Vào repo `TSS` -> `Settings` -> `Danger Zone` -> `Change visibility` -> Đổi thành **Private**.
- [ ] **Bước 3 (Cấu hình Local VM Tool):** Mở [VM/vm_config.env](file:///e:/Tools/TSS-main/VM/vm_config.env) và thêm dòng: `GH_TOKEN=github_pat_...`.
- [ ] **Bước 4 (Cấu hình Google Colab):** Mở Colab -> Biểu tượng 🔑 Secrets -> Thêm `GH_TOKEN`.
- [ ] **Bước 5 (Kích hoạt Triển khai):** Chạy [cai_dat_vm.bat](file:///e:/Tools/TSS-main/cai_dat_vm.bat) -> Chọn `[5]` để kiểm tra toàn bộ luồng tự động.
