#!/usr/bin/env bash
# ==============================================================================
#  🎙️ ZEROTTS STUDIO — 1-CLICK ALL-IN-ONE INSTALLER TỪ 0 (UBUNTU / DEBIAN)
#  Tác giả: Nguyễn Quốc Khánh (RevenantKitana) | https://k.mio.io.vn
# ==============================================================================
#  Lệnh chạy 1 dòng trực tiếp từ terminal máy chủ mới:
#    curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh | bash
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

echo -e "${C_CYAN}${C_BOLD}"
echo "================================================================================"
echo "    🎙️ BẮT ĐẦU CÀI ĐẶT PRODUCTION ZEROTTS STUDIO TỪ 0 (1-CLICK INSTALLER)"
echo "        Hỗ trợ Ubuntu / Debian | Tối ưu hóa cho ARM64 & x86_64 Cloud VM"
echo "================================================================================"
echo -e "${C_RESET}"

REPO_URL="https://github.com/RevenantKitana/TSS.git"
STABLE_COMMIT="main"
MODEL_HF_REPO="zeroweight-ai/ZeroTTS"
MODEL_HF_URL="https://huggingface.co/zeroweight-ai/ZeroTTS"
INSTALL_DIR="/home/ubuntu/TSS"

# Ensure user ubuntu or current user
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" != "root" ] && [ -d "/home/$CURRENT_USER" ]; then
    INSTALL_DIR="/home/$CURRENT_USER/TSS"
elif [ "$CURRENT_USER" = "root" ] && [ -d "/home/ubuntu" ]; then
    CURRENT_USER="ubuntu"
    INSTALL_DIR="/home/ubuntu/TSS"
fi

# ── 1. Cập nhật hệ điều hành & Cài đặt gói hệ thống ──────────────────────────
echo -e "${C_YELLOW}📦 [1/8] Đang cập nhật hệ thống & cài đặt thư viện phần mềm cần thiết...${C_RESET}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    git git-lfs python3 python3-venv python3-pip python3-dev \
    ffmpeg libsndfile1 curl wget htop cron ufw libgomp1 build-essential \
    libjemalloc2 iptables-persistent netfilter-persistent 2>/dev/null || sudo apt-get install -y git git-lfs python3 python3-venv python3-pip ffmpeg libsndfile1 curl wget htop cron ufw libgomp1 build-essential

git lfs install --skip-repo 2>/dev/null || true
echo -e "${C_GREEN}   ✅ Hoàn tất cài đặt các gói hệ thống.${C_RESET}\n"

# ── 2. Tinh gọn OS (Debloat) & Tối ưu hóa RAM, Swap & Kernel BBR ─────────────
echo -e "${C_YELLOW}⚡ [2/8] Tinh gọn hệ điều hành & Tối ưu hóa tài nguyên phần cứng VM...${C_RESET}"

# 2.1 Tinh gọn OS & Chống tự động cập nhật ngầm 100% (Anti Auto-Update Lock)
echo "   -> Chống tự động cập nhật (Block Auto-Update): Khóa cứng apt-daily, unattended-upgrades & timers..."

# Khóa cấu hình APT không cho quét / tải / nâng cấp gói ngầm
sudo mkdir -p /etc/apt/apt.conf.d/
sudo bash -c "cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists \"0\";
APT::Periodic::Download-Upgradeable-Packages \"0\";
APT::Periodic::AutocleanInterval \"0\";
APT::Periodic::Unattended-Upgrade \"0\";
EOF"
sudo cp /etc/apt/apt.conf.d/20auto-upgrades /etc/apt/apt.conf.d/10periodic 2>/dev/null || true

# Tắt nhắc nhở nâng cấp phiên bản OS
if [ -f /etc/update-manager/release-upgrades ]; then
    sudo sed -i 's/^Prompt=.*/Prompt=never/' /etc/update-manager/release-upgrades 2>/dev/null || true
fi

# Mask cứng toàn bộ services và timers cập nhật ngầm
sudo systemctl stop apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true
sudo systemctl disable apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true
sudo systemctl mask apt-daily.service apt-daily.timer apt-daily-upgrade.service apt-daily-upgrade.timer unattended-upgrades.service update-notifier-download.timer motd-news.timer 2>/dev/null || true

# Vô hiệu hóa các dịch vụ thừa (snapd, multipathd, crash reporting)
sudo systemctl stop snapd snapd.socket snapd.seeded multipathd apport whoopsie 2>/dev/null || true
sudo systemctl disable snapd snapd.socket snapd.seeded multipathd apport whoopsie 2>/dev/null || true
sudo systemctl mask snapd snapd.socket multipathd apport whoopsie 2>/dev/null || true
echo "   ✅ Đã khóa chặn 100% tự động update ngầm và tinh gọn OS (tiết kiệm ~300MB - 400MB RAM)."

# 2.2 Tạo 4GB Swap nếu chưa đủ
SWAP_TOTAL=$(free -m | awk '/Swap:/ {print $2}')
if [ "$SWAP_TOTAL" -lt 2000 ]; then
    echo "   -> Đang tạo 4GB Swapfile..."
    sudo swapoff -a 2>/dev/null || true
    sudo rm -f /swapfile
    sudo fallocate -l 4G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    echo "   -> Đã tạo và kích hoạt 4GB Swapfile."
else
    echo "   -> Swapfile hiện có: ${SWAP_TOTAL} MB (Đạt chuẩn)."
fi

# 2.3 Cấu hình Kernel Sysctl (TCP BBR, Swappiness 10, IO Buffers)
sudo bash -c "cat > /etc/sysctl.d/99-zerotts-optimizations.conf << 'EOF'
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
fs.file-max = 2097152
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
EOF"
sudo sysctl --system >/dev/null 2>&1 || true

# 2.4 Giới hạn Log Systemd 50MB
sudo mkdir -p /etc/systemd/journald.conf.d/
sudo bash -c "cat > /etc/systemd/journald.conf.d/size-limit.conf << 'EOF'
[Journal]
SystemMaxUse=50M
RuntimeMaxUse=30M
MaxRetentionSec=7day
EOF"
sudo systemctl restart systemd-journald 2>/dev/null || true
echo -e "${C_GREEN}   ✅ Đã tinh gọn OS (tiết kiệm ~300MB RAM), bật TCP BBR và Swappiness=10.${C_RESET}\n"

# ── 3. Tải mã nguồn TSS từ GitHub ────────────────────────────────────────────
echo -e "${C_YELLOW}📥 [3/8] Tải mã nguồn ZeroTTS TSS từ GitHub ($REPO_URL)...${C_RESET}"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"
git fetch origin 2>/dev/null || true
git checkout "$STABLE_COMMIT" 2>/dev/null || true
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR" 2>/dev/null || true
echo -e "${C_GREEN}   ✅ Đã tải mã nguồn TSS tại: $INSTALL_DIR (Commit: $(git rev-parse --short HEAD 2>/dev/null || echo $STABLE_COMMIT))${C_RESET}\n"

# ── 4. Tạo môi trường ảo Python & Cài đặt Dependencies AI ────────────────────
echo -e "${C_YELLOW}🐍 [4/8] Thiết lập Python Virtual Environment (.venv)...${C_RESET}"
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    python3 -m venv "$INSTALL_DIR/.venv"
fi
VENV_PY="$INSTALL_DIR/.venv/bin/python"
VENV_PIP="$INSTALL_DIR/.venv/bin/pip"

"$VENV_PIP" install --upgrade pip setuptools wheel -q
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    "$VENV_PIP" install -r "$INSTALL_DIR/requirements.txt" -q
else
    "$VENV_PIP" install fastapi uvicorn onnxruntime soundfile scipy numpy python-docx requests aiofiles psutil huggingface_hub -q
fi
"$VENV_PIP" install huggingface_hub -q 2>/dev/null || true
"$VENV_PIP" install -e "$INSTALL_DIR" -q 2>/dev/null || true
echo -e "${C_GREEN}   ✅ Đã cấu hình xong môi trường Python & ONNX Runtime.${C_RESET}\n"

# ── 5. Tải Mô hình AI ZeroTTS ────────────────────────────────────────────────
echo -e "${C_YELLOW}🧠 [5/8] Kiểm tra & Tải mô hình AI ZeroTTS ($MODEL_HF_REPO)...${C_RESET}"
if [ ! -d "$INSTALL_DIR/ZeroTTS_model" ] || [ ! -f "$INSTALL_DIR/ZeroTTS_model/config.json" ]; then
    echo "   -> Đang tải trọng số mô hình từ HuggingFace (zeroweight-ai/ZeroTTS)..."
    "$VENV_PY" -c "
from huggingface_hub import snapshot_download
import sys
try:
    snapshot_download(repo_id='$MODEL_HF_REPO', local_dir='$INSTALL_DIR/ZeroTTS_model')
    print('   ✅ Tải hoàn tất qua HuggingFace Hub!')
except Exception as e:
    print('   ⚠️ Fallback to git clone:', e)
    sys.exit(1)
" 2>/dev/null || git clone "$MODEL_HF_URL" "$INSTALL_DIR/ZeroTTS_model"
else
    echo "   -> Mô hình ZeroTTS_model đã tồn tại và sẵn sàng."
fi
sudo chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR/ZeroTTS_model" 2>/dev/null || true
echo -e "${C_GREEN}   ✅ Mô hình AI ZeroTTS đã sẵn sàng.${C_RESET}\n"

# ── 6. Thiết lập Thư mục dữ liệu & Quyền thực thi ────────────────────────────
echo -e "${C_YELLOW}📁 [6/8] Khởi tạo cấu trúc thư mục lưu trữ & phân quyền...${C_RESET}"
mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/outputs/keys" "$INSTALL_DIR/outputs/ephemeral" "$INSTALL_DIR/scripts"
chmod +x "$INSTALL_DIR/manage_keys.sh" "$INSTALL_DIR/scripts/cron_cleanup.sh" "$INSTALL_DIR/zerotts.sh" 2>/dev/null || true

# Tạo symlink toàn cục `zerotts`
sudo ln -sf "$INSTALL_DIR/zerotts.sh" /usr/local/bin/zerotts

# Khởi tạo auth keys
"$VENV_PY" "$INSTALL_DIR/webui/manage_keys.py" clean >/dev/null 2>&1 || true
echo -e "${C_GREEN}   ✅ Đã thiết lập cấu trúc lưu trữ và lệnh toàn cục 'zerotts'.${C_RESET}\n"

# ── 7. Cấu hình Systemd Service & Cronjob Tự động ────────────────────────────
echo -e "${C_YELLOW}⚙️ [7/8] Thiết lập Systemd Service (zerotts.service) & Cronjob...${C_RESET}"

# Tìm thư viện jemalloc để tối ưu cấp phát RAM cho Python
JEMALLOC_PATH=""
for p in /usr/lib/aarch64-linux-gnu/libjemalloc.so.2 /usr/lib/x86_64-linux-gnu/libjemalloc.so.2 /usr/lib/libjemalloc.so.2; do
    if [ -f "$p" ]; then
        JEMALLOC_PATH="$p"
        break
    fi
done

ENV_JEMALLOC=""
if [ -n "$JEMALLOC_PATH" ]; then
    ENV_JEMALLOC="Environment=\"LD_PRELOAD=$JEMALLOC_PATH\""
fi

sudo bash -c "cat > /etc/systemd/system/zerotts.service << EOF
[Unit]
Description=ZeroTTS Studio Production Server
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR
Environment=\"PATH=$INSTALL_DIR/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
Environment=\"PYTHONUNBUFFERED=1\"
Environment=\"OMP_NUM_THREADS=1\"
Environment=\"ONNX_NUM_THREADS=1\"
Environment=\"OPENBLAS_NUM_THREADS=1\"
Environment=\"MKL_NUM_THREADS=1\"
Environment=\"MALLOC_ARENA_MAX=2\"
$ENV_JEMALLOC
ExecStart=$INSTALL_DIR/.venv/bin/python webui/server.py --host 0.0.0.0 --port 7860 --model $INSTALL_DIR/ZeroTTS_model
Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable zerotts
sudo systemctl restart zerotts

# Cài đặt Cronjob dọn dẹp mỗi 15 phút
(crontab -l 2>/dev/null | grep -v "cron_cleanup.sh" || true; echo "*/15 * * * * $INSTALL_DIR/scripts/cron_cleanup.sh >> $INSTALL_DIR/data/cron_cleanup.log 2>&1") | crontab -
echo -e "${C_GREEN}   ✅ zerotts.service đang chạy và Crontab đã được kích hoạt.${C_RESET}\n"

# ── 8. Mở Tường lửa & Cài đặt Cloudflared sẵn sàng ───────────────────────────
echo -e "${C_YELLOW}🛡️ [8/8] Mở cổng tường lửa & Cài đặt Cloudflare Tunnel Client...${C_RESET}"
sudo ufw allow 22/tcp comment 'SSH' 2>/dev/null || true
sudo ufw allow 80/tcp comment 'HTTP' 2>/dev/null || true
sudo ufw allow 443/tcp comment 'HTTPS' 2>/dev/null || true
sudo ufw allow 7860/tcp comment 'ZeroTTS WebUI' 2>/dev/null || true
sudo ufw --force enable 2>/dev/null || true

# Oracle iptables bypass
sudo iptables -I INPUT -p tcp --dport 7860 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# Tải sẵn cloudflared client (để mask IP/Port khi cần)
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb"
else
    CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb"
fi
curl -sL "$CF_URL" -o /tmp/cloudflared.deb 2>/dev/null && sudo dpkg -i /tmp/cloudflared.deb >/dev/null 2>&1 && rm -f /tmp/cloudflared.deb || true
echo -e "${C_GREEN}   ✅ Đã cấu hình tường lửa và cài đặt sẵn cloudflared.${C_RESET}\n"

# ── Lấy IP Công khai & Master Key ────────────────────────────────────────────
PUBLIC_IP=$(curl -s -m 3 https://api.ipify.org || curl -s -m 3 https://ifconfig.me || echo "140.245.124.221")
MASTER_KEY=$(grep -o '"zk_[^"]*"' "$INSTALL_DIR/data/auth_keys.json" 2>/dev/null | head -n 1 | tr -d '"' || echo "zk_master_...")

echo -e "${C_BOLD}${C_GREEN}"
echo "================================================================================"
echo "          🎉 CHÚC MỪNG! HỆ THỐNG ZEROTTS STUDIO ĐÃ ĐƯỢC CÀI ĐẶT THÀNH CÔNG!"
echo "================================================================================"
echo -e "${C_RESET}"
echo -e "  🌐 ${C_BOLD}Địa chỉ truy cập WebUI:${C_RESET} ${C_CYAN}${C_BOLD}http://${PUBLIC_IP}:7860${C_RESET}"
echo -e "  🔑 ${C_BOLD}Master Key mặc định:  ${C_RESET} ${C_YELLOW}${C_BOLD}${MASTER_KEY}${C_RESET}"
echo -e "  📁 ${C_BOLD}Thư mục cài đặt:      ${C_RESET} ${INSTALL_DIR}"
echo ""
echo -e "  🛠️ ${C_BOLD}CÁC LỆNH QUẢN TRỊ TOÀN CỤC (Gõ trực tiếp ở bất kỳ đâu):${C_RESET}"
echo -e "     • ${C_BOLD}zerotts${C_RESET}          👉 Mở Menu Quản trị All-In-One"
echo -e "     • ${C_BOLD}zerotts monitor${C_RESET}  👉 Giám sát CPU, RAM, Disk thời gian thực"
echo -e "     • ${C_BOLD}zerotts keys${C_RESET}     👉 Quản lý Access Key (Tạo, Khóa, Xóa)"
echo -e "     • ${C_BOLD}zerotts restart${C_RESET}  👉 Khởi động lại Web Server"
echo -e "     • ${C_BOLD}zerotts logs${C_RESET}     👉 Xem nhật ký hoạt động trực tiếp"
echo -e "     • ${C_BOLD}zerotts clean${C_RESET}    👉 Dọn dẹp rác & giải phóng dung lượng"
echo ""
echo -e "  🛡️ ${C_BOLD}CÁCH MASK IP & PORT 7860 BẰNG CLOUDFLARE TUNNEL (TÙY CHỌN):${C_RESET}"
echo -e "     • Chạy Quick Tunnel ẩn IP ngay lập tức:"
echo -e "       ${C_DIM}cloudflared tunnel --url http://127.0.0.1:7860${C_RESET}"
echo -e "     • Hoặc cài đặt Cloudflare Zero Trust Tunnel với tên miền riêng:"
echo -e "       ${C_DIM}sudo cloudflared service install <TOKEN_CỦA_BẠN>${C_RESET}"
echo -e "${C_CYAN}================================================================================${C_RESET}\n"
