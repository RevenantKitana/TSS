#!/usr/bin/env bash
# ==============================================================================
#  🎙️ ZEROTTS STUDIO — BASH SSH ALL-IN-ONE VM & SYSTEM TOOLKIT
#  Tác giả: Nguyễn Quốc Khánh (RevenantKitana) | https://k.mio.io.vn
# ==============================================================================
#  Tính năng:
#    1. Khởi tạo dự án từ 0 (Zero-to-Hero Auto Setup)
#    2. Tối ưu hóa OS & Tài nguyên VM (Kernel, BBR, Swap, IOPS, ONNX Threading)
#    3. Quản lý Access Key & Lưu trữ (CRUD Keys & Storage Isolation)
#    4. Giám sát tài nguyên thời gian thực (CPU, RAM, Swap, Disk, Port)
#    5. Quản lý dịch vụ ZeroTTS (Start, Stop, Restart, Status, Auto-boot)
#    6. Xem nhật ký hoạt động trực tiếp (Live Logs)
#    7. Dọn dẹp rác & Giải phóng dung lượng ổ cứng
#    8. Cấu hình Tường lửa & Mạng (UFW / Oracle iptables)
#    9. Cập nhật mã nguồn từ GitHub (Git Checkout Stable Commit)
# ==============================================================================

set -e

# ANSI Color Definitions
C_RESET="\033[0m"
C_BOLD="\033[1m"
C_DIM="\033[2m"
C_RED="\033[31m"
C_GREEN="\033[32m"
C_YELLOW="\033[33m"
C_BLUE="\033[34m"
C_MAGENTA="\033[35m"
C_CYAN="\033[36m"
C_WHITE="\033[37m"
C_BG_BLUE="\033[44m"

# Project Constants
REPO_URL="https://github.com/RevenantKitana/TSS.git"
STABLE_COMMIT="main"
MODEL_HF_REPO="zeroweight-ai/ZeroTTS"
MODEL_HF_URL="https://huggingface.co/zeroweight-ai/ZeroTTS"
DEFAULT_INSTALL_DIR="/home/ubuntu/TSS"

# Resolve working directory
if [ -d "$DEFAULT_INSTALL_DIR" ]; then
    APP_DIR="$DEFAULT_INSTALL_DIR"
else
    APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
cd "$APP_DIR"

# Detect Python interpreter
get_python() {
    if [ -f "$APP_DIR/.venv/bin/python" ]; then
        echo "$APP_DIR/.venv/bin/python"
    elif [ -f "/home/ubuntu/TSS/.venv/bin/python" ]; then
        echo "/home/ubuntu/TSS/.venv/bin/python"
    elif command -v python3 &>/dev/null; then
        echo "python3"
    else
        echo "python"
    fi
}

PY=$(get_python)

# ── Helper: Header Banner ────────────────────────────────────────────────────
print_banner() {
    [ -t 1 ] && clear 2>/dev/null || true
    echo -e "${C_CYAN}${C_BOLD}"
    echo "================================================================================"
    echo "       🎙️ ZEROTTS STUDIO — BASH SSH ALL-IN-ONE VM & SYSTEM TOOLKIT"
    echo "         Hệ thống quản trị máy chủ, tối ưu tài nguyên & triển khai"
    echo "================================================================================"
    echo -e "${C_RESET}"
}

pause_key() {
    if [ -t 0 ]; then
        echo ""
        read -rp "👉 Nhấn Enter để tiếp tục..." _dummy
    fi
}

# ── [1] Khởi tạo Dự án từ 0 (Zero-to-Hero Setup) ─────────────────────────────
setup_from_scratch() {
    print_banner
    echo -e "${C_BOLD}${C_GREEN}🚀 [1/6] BẮT ĐẦU KHỞI TẠO DỰ ÁN ZEROTTS TỪ 0...${C_RESET}\n"

    # 1. Cập nhật và cài đặt Package Hệ thống
    echo -e "${C_YELLOW}📦 1. Đang cài đặt các thư viện hệ thống cần thiết...${C_RESET}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        git git-lfs python3 python3-venv python3-pip python3-dev \
        ffmpeg libsndfile1 curl wget htop cron ufw libgomp1 build-essential
    git lfs install --skip-repo 2>/dev/null || true
    echo -e "${C_GREEN}   ✅ Đã cài đặt xong gói hệ thống.${C_RESET}\n"

    # 2. Khởi tạo / Đồng bộ Repo TSS
    echo -e "${C_YELLOW}📥 2. Kiểm tra mã nguồn ZeroTTS TSS...${C_RESET}"
    if [ ! -f "$APP_DIR/webui/server.py" ]; then
        echo "   Đang tải repo từ GitHub ($REPO_URL)..."
        git clone "$REPO_URL" "$APP_DIR"
        cd "$APP_DIR"
    fi
    git fetch origin 2>/dev/null || true
    git checkout "$STABLE_COMMIT" 2>/dev/null || true
    echo -e "${C_GREEN}   ✅ Đang ở commit ổn định: $(git rev-parse --short HEAD 2>/dev/null || echo $STABLE_COMMIT)${C_RESET}\n"

    # 3. Tạo môi trường ảo Python (.venv)
    echo -e "${C_YELLOW}🐍 3. Thiết lập môi trường ảo Python (.venv)...${C_RESET}"
    if [ ! -d "$APP_DIR/.venv" ]; then
        python3 -m venv "$APP_DIR/.venv"
    fi
    "$APP_DIR/.venv/bin/pip" install --upgrade pip setuptools wheel -q
    
    if [ -f "$APP_DIR/requirements.txt" ]; then
        echo "   Đang cài đặt dependencies từ requirements.txt..."
        "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
    else
        "$APP_DIR/.venv/bin/pip" install fastapi uvicorn onnxruntime soundfile scipy numpy python-docx requests aiofiles psutil -q
    fi
    echo -e "${C_GREEN}   ✅ Đã cấu hình xong môi trường Python.${C_RESET}\n"

    # 4. Tải Model AI ZeroTTS
    echo -e "${C_YELLOW}🧠 4. Kiểm tra mô hình AI ZeroTTS ($MODEL_HF_REPO)...${C_RESET}"
    if [ ! -d "$APP_DIR/ZeroTTS_model" ] || [ ! -f "$APP_DIR/ZeroTTS_model/config.json" ]; then
        echo "   Đang tải trọng số mô hình từ HuggingFace (zeroweight-ai/ZeroTTS)..."
        "$APP_DIR/.venv/bin/python" -c "
from huggingface_hub import snapshot_download
import sys
try:
    snapshot_download(repo_id='$MODEL_HF_REPO', local_dir='$APP_DIR/ZeroTTS_model')
    print('   ✅ Tải hoàn tất qua HuggingFace Hub!')
except Exception as e:
    print('   ⚠️ Fallback to git clone:', e)
    sys.exit(1)
" 2>/dev/null || git clone "$MODEL_HF_URL" "$APP_DIR/ZeroTTS_model"
    else
        echo "   ZeroTTS_model đã tồn tại và sẵn sàng."
    fi
    echo -e "${C_GREEN}   ✅ Mô hình AI đã sẵn sàng.${C_RESET}\n"

    # 5. Tạo cấu trúc thư mục & phân quyền
    echo -e "${C_YELLOW}📁 5. Khởi tạo cấu trúc thư mục lưu trữ & phân quyền...${C_RESET}"
    mkdir -p "$APP_DIR/data" "$APP_DIR/outputs/keys" "$APP_DIR/outputs/ephemeral" "$APP_DIR/scripts"
    chmod +x "$APP_DIR/manage_keys.sh" "$APP_DIR/scripts/cron_cleanup.sh" "$APP_DIR/zerotts.sh" 2>/dev/null || true
    
    # Khởi tạo Key đầu tiên nếu chưa có
    PY=$(get_python)
    "$PY" "$APP_DIR/webui/manage_keys.py" clean >/dev/null 2>&1 || true
    echo -e "${C_GREEN}   ✅ Cấu trúc thư mục dữ liệu đã sẵn sàng.${C_RESET}\n"

    # 6. Cấu hình Systemd Service & Cronjob
    echo -e "${C_YELLOW}⚙️ 6. Thiết lập Systemd Service & Cronjob tự động...${C_RESET}"
    sudo bash -c "cat > /etc/systemd/system/zerotts.service << 'EOF'
[Unit]
Description=ZeroTTS Studio Production Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment=\"PATH=$APP_DIR/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
Environment=\"PYTHONUNBUFFERED=1\"
Environment=\"OMP_NUM_THREADS=1\"
Environment=\"ONNX_NUM_THREADS=1\"
ExecStart=$APP_DIR/.venv/bin/python webui/server.py --host 0.0.0.0 --port 7860 --model $APP_DIR/ZeroTTS_model
Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable --now zerotts
    sudo systemctl restart zerotts

    # Cài đặt Crontab dọn dẹp mỗi 15 phút
    (crontab -l 2>/dev/null | grep -v "cron_cleanup.sh" || true; echo "*/15 * * * * $APP_DIR/scripts/cron_cleanup.sh >> $APP_DIR/data/cron_cleanup.log 2>&1") | crontab -

    echo -e "${C_BOLD}${C_GREEN}\n🎉 HOÀN TẤT KHỞI TẠO HỆ THỐNG ZEROTTS STUDIO!${C_RESET}"
    echo -e "   • Dịch vụ Web:  ${C_CYAN}http://0.0.0.0:7860${C_RESET}"
    echo -e "   • Systemd:      ${C_GREEN}zerotts.service (Đang chạy ngầm)${C_RESET}"
    echo -e "   • Cron Cleanup: ${C_GREEN}Tự dọn dẹp mỗi 15 phút${C_RESET}\n"
    pause_key
}

# ── [2] Tối ưu hóa OS & Tài nguyên VM ─────────────────────────────────────────
optimize_vm() {
    print_banner
    echo -e "${C_BOLD}${C_GREEN}⚡ TỐI ƯU HÓA HỆ ĐIỀU HÀNH & TÀI NGUYÊN VM (ORACLE FREE TIER)${C_RESET}\n"
    
    # 0. Tinh gọn OS & Chống tự động cập nhật ngầm 100% (Anti Auto-Update Lock)
    echo -e "${C_YELLOW}🧹 0. Tinh gọn OS & Khóa chặn Auto-Update (Block background updates)...${C_RESET}"
    
    # Khóa cấu hình APT
    sudo mkdir -p /etc/apt/apt.conf.d/
    sudo bash -c "cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists \"0\";
APT::Periodic::Download-Upgradeable-Packages \"0\";
APT::Periodic::AutocleanInterval \"0\";
APT::Periodic::Unattended-Upgrade \"0\";
EOF"
    sudo cp /etc/apt/apt.conf.d/20auto-upgrades /etc/apt/apt.conf.d/10periodic 2>/dev/null || true

    # Tắt nhắc nhở nâng cấp OS
    if [ -f /etc/update-manager/release-upgrades ]; then
        sudo sed -i 's/^Prompt=.*/Prompt=never/' /etc/update-manager/release-upgrades 2>/dev/null || true
    fi

    # Mask cứng toàn bộ services và timers cập nhật ngầm
    sudo systemctl stop apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true
    sudo systemctl disable apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true
    sudo systemctl mask apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true

    # Vô hiệu hóa snapd, multipathd, crash reporting
    sudo systemctl stop snapd snapd.socket snapd.seeded multipathd apport whoopsie 2>/dev/null || true
    sudo systemctl disable snapd snapd.socket snapd.seeded multipathd apport whoopsie 2>/dev/null || true
    sudo systemctl mask snapd snapd.socket multipathd apport whoopsie 2>/dev/null || true
    sudo apt-get install -y libjemalloc2 -qq 2>/dev/null || true
    echo "   ✅ Đã khóa chặn 100% tự động update ngầm và tinh gọn OS (Tiết kiệm ~300MB - 400MB RAM)."

    # 1. Tối ưu Swap & RAM
    echo -e "\n${C_YELLOW}🧠 1. Kiểm tra & Tối ưu Swapfile / Virtual Memory...${C_RESET}"
    SWAP_TOTAL=$(free -m | awk '/Swap:/ {print $2}')
    if [ "$SWAP_TOTAL" -lt 2000 ]; then
        echo "   Swap hiện tại < 2GB. Đang tạo 4GB Swapfile..."
        sudo swapoff -a 2>/dev/null || true
        sudo rm -f /swapfile
        sudo fallocate -l 4G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        if ! grep -q '/swapfile' /etc/fstab; then
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        fi
        echo "   ✅ Đã tạo 4GB Swapfile thành công."
    else
        echo "   ✅ Swapfile hiện có: ${SWAP_TOTAL} MB (Đạt chuẩn)."
    fi

    # 2. Cấu hình Sysctl Kernel (Swappiness, BBR, Cache, File Limits)
    echo -e "\n${C_YELLOW}🚀 2. Tối ưu Kernel Sysctl (TCP BBR, Swappiness, IO Buffers)...${C_RESET}"
    sudo bash -c "cat > /etc/sysctl.d/99-zerotts-optimizations.conf << 'EOF'
# Giảm tần suất đẩy RAM sang Swap để bảo vệ IOPS trên Oracle Free Tier
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10

# Tăng giới hạn File Descriptors
fs.file-max = 2097152

# Bật thuật toán nghẽn mạng TCP BBR (Tăng tốc stream audio & WebUI)
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Mở rộng Network Socket Buffers
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
EOF"
    sudo sysctl --system >/dev/null 2>&1 || true
    echo "   ✅ Đã kích hoạt TCP BBR và tối ưu hóa bộ nhớ ảo."

    # 3. Giới hạn Journald Logs (Tránh tràn ổ đĩa 45GB)
    echo -e "\n${C_YELLOW}📜 3. Giới hạn dung lượng Log của Systemd (Max 50MB)...${C_RESET}"
    sudo mkdir -p /etc/systemd/journald.conf.d/
    sudo bash -c "cat > /etc/systemd/journald.conf.d/size-limit.conf << 'EOF'
[Journal]
SystemMaxUse=50M
RuntimeMaxUse=30M
MaxRetentionSec=7day
EOF"
    sudo systemctl restart systemd-journald 2>/dev/null || true
    echo "   ✅ Đã giới hạn log systemd tối đa 50MB."

    # 4. Tối ưu OpenMP / ONNX Threading & Jemalloc trong Service
    echo -e "\n${C_YELLOW}⚙️ 4. Tối ưu hóa Threading CPU đơn nhân & Giảm phân mảnh RAM...${C_RESET}"
    if [ -f /etc/systemd/system/zerotts.service ]; then
        sudo sed -i '/OMP_NUM_THREADS/d' /etc/systemd/system/zerotts.service
        sudo sed -i '/ONNX_NUM_THREADS/d' /etc/systemd/system/zerotts.service
        sudo sed -i '/OPENBLAS_NUM_THREADS/d' /etc/systemd/system/zerotts.service
        sudo sed -i '/MKL_NUM_THREADS/d' /etc/systemd/system/zerotts.service
        sudo sed -i '/MALLOC_ARENA_MAX/d' /etc/systemd/system/zerotts.service
        sudo sed -i '/LD_PRELOAD/d' /etc/systemd/system/zerotts.service
        
        JEMALLOC_PATH=""
        for p in /usr/lib/aarch64-linux-gnu/libjemalloc.so.2 /usr/lib/x86_64-linux-gnu/libjemalloc.so.2 /usr/lib/libjemalloc.so.2; do
            if [ -f "$p" ]; then
                JEMALLOC_PATH="$p"
                break
            fi
        done
        ENV_JEM=""
        if [ -n "$JEMALLOC_PATH" ]; then
            ENV_JEM="Environment=\"LD_PRELOAD=$JEMALLOC_PATH\""
        fi

        sudo sed -i "/\[Service\]/a Environment=\"ONNX_NUM_THREADS=1\"\nEnvironment=\"OMP_NUM_THREADS=1\"\nEnvironment=\"OPENBLAS_NUM_THREADS=1\"\nEnvironment=\"MKL_NUM_THREADS=1\"\nEnvironment=\"MALLOC_ARENA_MAX=2\"\n$ENV_JEM" /etc/systemd/system/zerotts.service
        sudo systemctl daemon-reload
        sudo systemctl restart zerotts
    fi
    echo "   ✅ Đã tối ưu hóa CPU inference và bộ nhớ cho nhân ARM."

    echo -e "${C_BOLD}${C_GREEN}\n🎉 ĐÃ HOÀN TẤT TỐI ƯU HÓA HỆ THỐNG VM!${C_RESET}\n"
    pause_key
}

# ── [3] Quản lý Access Key & Lưu trữ ─────────────────────────────────────────
manage_keys_sub() {
    PY=$(get_python)
    "$PY" "$APP_DIR/webui/manage_keys.py"
}

# ── [4] Giám sát Tài nguyên Thời gian thực ───────────────────────────────────
monitor_system() {
    while true; do
        [ -t 1 ] && clear 2>/dev/null || true
        echo -e "${C_CYAN}${C_BOLD}"
        echo "================================================================================"
        echo "       📊 THEO DÕI TÀI NGUYÊN VM ORACLE CLOUD (TỰ LÀM MỚI MỖI 3 GIÂY)"
        echo "                 Nhấn Ctrl+C hoặc phím 'q' để quay lại Menu"
        echo "================================================================================"
        echo -e "${C_RESET}"

        echo -e "${C_BOLD}${C_YELLOW}=== 1. CPU & LOAD AVERAGE ===${C_RESET}"
        lscpu 2>/dev/null | grep -E "Model name|CPU\(s\):" || true
        uptime
        echo ""

        echo -e "${C_BOLD}${C_YELLOW}=== 2. RAM & SWAP MEMORY ===${C_RESET}"
        free -h
        echo ""

        echo -e "${C_BOLD}${C_YELLOW}=== 3. Ổ CỨNG LƯU TRỮ (DISK STORAGE) ===${C_RESET}"
        df -h /
        echo ""

        echo -e "${C_BOLD}${C_YELLOW}=== 4. DỊCH VỤ ZEROTTS STUDIO ===${C_RESET}"
        systemctl status zerotts --no-pager 2>/dev/null | grep -E "Active:|Main PID|Memory:|CPU:" || echo "Dịch vụ zerotts chưa được cài đặt."
        echo ""

        echo -e "${C_BOLD}${C_YELLOW}=== 5. THƯ MỤC LƯU TRỮ (STORAGE PARTITIONS) ===${C_RESET}"
        KEY_DIRS=$(find "$APP_DIR/outputs/keys" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
        EPH_DIRS=$(find "$APP_DIR/outputs/ephemeral" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
        echo -e " • Thư mục Key vĩnh viễn (outputs/keys/)     : ${C_GREEN}${KEY_DIRS}${C_RESET} không gian riêng"
        echo -e " • Thư mục Khách phiên ngắn (outputs/ephemeral/): ${C_CYAN}${EPH_DIRS}${C_RESET} phiên tạm"
        echo ""

        echo -e "${C_DIM}Đang làm mới sau 3 giây... (Nhấn q để thoát)${C_RESET}"
        read -t 3 -n 1 input_key || true
        if [ "$input_key" = "q" ] || [ "$input_key" = "Q" ]; then
            break
        fi
    done
}

# ── [5] Quản lý Dịch vụ ZeroTTS ──────────────────────────────────────────────
manage_service() {
    print_banner
    echo -e "${C_BOLD}${C_CYAN}🔄 QUẢN LÝ DỊCH VỤ ZEROTTS (SYSTEMD SERVICE)${C_RESET}\n"
    echo "  [1] 🔄 Khởi động lại dịch vụ (Restart)"
    echo "  [2] ⏸️ Tạm dừng dịch vụ (Stop)"
    echo "  [3] ▶️ Khởi chạy dịch vụ (Start)"
    echo "  [4] 📋 Xem trạng thái chi tiết (Status)"
    echo "  [5] ⚡ Bật tự khởi động cùng OS (Enable Auto-start)"
    echo "  [0] ↩️ Quay lại"
    echo ""
    read -rp "👉 Chọn thao tác (0-5): " s_choice

    case "$s_choice" in
        1)
            echo "Đang khởi động lại zerotts.service..."
            sudo systemctl restart zerotts
            echo -e "${C_GREEN}✅ Đã restart thành công.${C_RESET}"
            pause_key
            ;;
        2)
            echo "Đang tạm dừng zerotts.service..."
            sudo systemctl stop zerotts
            echo -e "${C_YELLOW}⏸️ Đã dừng dịch vụ.${C_RESET}"
            pause_key
            ;;
        3)
            echo "Đang khởi chạy zerotts.service..."
            sudo systemctl start zerotts
            echo -e "${C_GREEN}▶️ Đã khởi chạy dịch vụ.${C_RESET}"
            pause_key
            ;;
        4)
            echo ""
            sudo systemctl status zerotts --no-pager
            pause_key
            ;;
        5)
            sudo systemctl enable zerotts
            echo -e "${C_GREEN}✅ Đã bật tự khởi động cùng máy chủ.${C_RESET}"
            pause_key
            ;;
        *)
            ;;
    esac
}

# ── [6] Xem Nhật ký Hoạt động Trực tiếp (Live Logs) ───────────────────────────
view_live_logs() {
    [ -t 1 ] && clear 2>/dev/null || true
    echo -e "${C_CYAN}${C_BOLD}"
    echo "================================================================================"
    echo "         📜 NHẬT KÝ HOẠT ĐỘNG TRỰC TIẾP ZEROTTS (LIVE JOURNALCTL)"
    echo "                     Nhấn Ctrl+C để dừng xem log"
    echo "================================================================================"
    echo -e "${C_RESET}"
    journalctl -u zerotts -f -n 50 --no-pager
}

# ── [7] Dọn dẹp Rác & Giải phóng Bộ nhớ ──────────────────────────────────────
clean_system() {
    print_banner
    echo -e "${C_BOLD}${C_YELLOW}🧹 DỌN DẸP TOÀN DIỆN & GIẢI PHÓNG BỘ NHỚ${C_RESET}\n"

    # 1. Dọn dẹp Storage ZeroTTS
    echo "1. Đang dọn dẹp các phiên khách hết hạn và thư mục key không còn hợp lệ..."
    PY=$(get_python)
    "$PY" "$APP_DIR/webui/manage_keys.py" clean

    # 2. Dọn dẹp Apt cache
    echo -e "\n2. Dọn dẹp cache cài đặt apt..."
    sudo apt-get autoremove -y -qq
    sudo apt-get clean -qq

    # 3. Dọn dẹp Log cũ
    echo -e "\n3. Dọn dẹp log cũ hơn 3 ngày..."
    sudo journalctl --vacuum-time=3d >/dev/null 2>&1 || true

    # 4. Xóa file tạm
    echo -e "\n4. Dọn dẹp thư mục tạm /tmp..."
    sudo rm -rf /tmp/pip-* /tmp/*.tmp 2>/dev/null || true

    echo -e "${C_BOLD}${C_GREEN}\n✅ ĐÃ HOÀN TẤT DỌN DẸP TOÀN BỘ HỆ THỐNG!${C_RESET}\n"
    df -h /
    pause_key
}

# ── [8] Cấu hình Tường lửa & Mạng ───────────────────────────────────────────
configure_firewall() {
    print_banner
    echo -e "${C_BOLD}${C_CYAN}🛡️ CẤU HÌNH TƯỜNG LỬA & MỞ CỔNG MẠNG (FIREWALL & PORTS)${C_RESET}\n"

    echo "Đang mở các cổng mạng cần thiết trên UFW (22 SSH, 80 HTTP, 443 HTTPS, 7860 WebUI)..."
    sudo ufw allow 22/tcp comment 'SSH' 2>/dev/null || true
    sudo ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
    sudo ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
    sudo ufw allow 7860/tcp comment 'ZeroTTS WebUI' 2>/dev/null || true
    sudo ufw --force enable 2>/dev/null || true

    # Fix Oracle Cloud default iptables drop rules
    echo "Đang tối ưu iptables Oracle Cloud..."
    sudo iptables -I INPUT -p tcp --dport 7860 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

    echo -e "${C_BOLD}${C_GREEN}\n✅ ĐÃ MỞ CỔNG VÀ BẬO MẬT MẠNG THÀNH CÔNG!${C_RESET}"
    sudo ufw status verbose
    pause_key
}

# ── [9] Cập nhật Mã nguồn từ GitHub ─────────────────────────────────────────
update_source_code() {
    print_banner
    echo -e "${C_BOLD}${C_MAGENTA}📦 CẬP NHẬT MÃ NGUỒN TỪ GITHUB${C_RESET}\n"

    echo "Đang kéo mã nguồn mới nhất từ GitHub..."
    git fetch origin
    git checkout "$STABLE_COMMIT"
    
    echo -e "\nĐang khởi động lại zerotts.service..."
    sudo systemctl restart zerotts

    echo -e "${C_BOLD}${C_GREEN}\n✅ ĐÃ ĐỒNG BỘ VÀ KHỞI ĐỘNG LẠI DỊCH VỤ THÀNH CÔNG!${C_RESET}\n"
    git log -n 1 --oneline
    pause_key
}

# ── Main Menu Loop ───────────────────────────────────────────────────────────
main_menu() {
    while true; do
        print_banner
        echo -e "  ${C_BOLD}${C_GREEN}[1] ⚡ Khởi tạo Dự án từ 0${C_RESET} ${C_DIM}(Zero-to-Hero Auto Setup)${C_RESET}"
        echo -e "  ${C_BOLD}${C_CYAN}[2] 🚀 Tối ưu hóa OS & Tài nguyên VM${C_RESET} ${C_DIM}(BBR, Swap, IOPS, Threads)${C_RESET}"
        echo -e "  ${C_BOLD}${C_YELLOW}[3] 🔑 Quản lý Access Key & Lưu trữ${C_RESET} ${C_DIM}(CRUD Keys & Dedicated Storage)${C_RESET}"
        echo -e "  ${C_BOLD}${C_WHITE}[4] 📊 Giám sát Tài nguyên Thời gian thực${C_RESET} ${C_DIM}(CPU, RAM, Disk, Port)${C_RESET}"
        echo -e "  ${C_BOLD}${C_BLUE}[5] 🔄 Quản lý Dịch vụ ZeroTTS${C_RESET} ${C_DIM}(Start, Stop, Restart, Status)${C_RESET}"
        echo -e "  ${C_BOLD}${C_MAGENTA}[6] 📜 Xem Nhật ký Hoạt động Trực tiếp${C_RESET} ${C_DIM}(Live Logs journalctl)${C_RESET}"
        echo -e "  ${C_BOLD}${C_YELLOW}[7] 🧹 Dọn dẹp Rác & Giải phóng Dung lượng${C_RESET} ${C_DIM}(Purge Expired & Clean Cache)${C_RESET}"
        echo -e "  ${C_BOLD}${C_GREEN}[8] 🛡️ Cấu hình Tường lửa & Mạng${C_RESET} ${C_DIM}(UFW, Oracle Ports 80/443/7860)${C_RESET}"
        echo -e "  ${C_BOLD}${C_CYAN}[9] 📦 Cập nhật Mã nguồn từ GitHub${C_RESET} ${C_DIM}(Git Checkout Stable)${C_RESET}"
        echo -e "  ${C_BOLD}${C_RED}[0] 🚪 Thoát${C_RESET}"
        echo -e "${C_CYAN}================================================================================${C_RESET}"

        read -rp "👉 Chọn chức năng (0-9): " choice

        case "$choice" in
            1) setup_from_scratch ;;
            2) optimize_vm ;;
            3) manage_keys_sub ;;
            4) monitor_system ;;
            5) manage_service ;;
            6) view_live_logs ;;
            7) clean_system ;;
            8) configure_firewall ;;
            9) update_source_code ;;
            0|q|Q|exit)
                echo -e "\n${C_CYAN}Cảm ơn bạn đã sử dụng ZeroTTS Toolkit. Tạm biệt!${C_RESET}\n"
                exit 0
                ;;
            *)
                echo -e "\n${C_RED}Lựa chọn không hợp lệ, vui lòng thử lại.${C_RESET}"
                sleep 1
                ;;
        esac
    done
}

# ── Non-interactive CLI Subcommands Support ─────────────────────────────────
case "$1" in
    setup) setup_from_scratch ;;
    optimize) optimize_vm ;;
    keys) manage_keys_sub ;;
    monitor) monitor_system ;;
    restart) sudo systemctl restart zerotts && echo "Restarted zerotts.service" ;;
    status) sudo systemctl status zerotts --no-pager ;;
    logs) view_live_logs ;;
    clean) clean_system ;;
    firewall) configure_firewall ;;
    update) update_source_code ;;
    *) main_menu ;;
esac
