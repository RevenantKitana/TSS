#!/usr/bin/env bash
# ==============================================================================
# ZeroTTS Automated Production Deployment Script for Oracle Cloud (ARM64 Ubuntu)
# ==============================================================================

set -e

echo "============================================================"
echo "🚀 BẮT ĐẦU CÀI ĐẶT PRODUCTION ZEROTTS TRÊN VM ARM64"
echo "============================================================"

APP_DIR="/home/ubuntu/TSS"
VENV_DIR="$APP_DIR/.venv"

# 1. Cập nhật hệ thống & Cài đặt gói cần thiết
echo "📦 [1/6] Đang cập nhật gói hệ điều hành & FFmpeg..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv ffmpeg git curl iptables-persistent netfilter-persistent

# 2. Tạo Swapfile 4GB (Nếu chưa có)
echo "💾 [2/6] Kiểm tra và cấu hình Swapfile 4GB..."
if [ $(swapon --show | wc -l) -eq 0 ]; then
    echo "   -> Đang tạo 4GB Swapfile..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    echo "   -> Đã bật Swap 4GB thành công!"
else
    echo "   -> Swapfile đã tồn tại, bỏ qua."
fi

# 3. Tạo môi trường ảo Python & Cài đặt Dependencies
echo "🐍 [3/6] Thiết lập Python Virtualenv (.venv) & ONNX Runtime ARM64..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
"$VENV_DIR/bin/pip" install numpy soundfile scipy tokenizers huggingface_hub fastapi uvicorn requests
"$VENV_DIR/bin/pip" install onnxruntime
"$VENV_DIR/bin/pip" install -e .

# 4. Mở Port tường lửa (Iptables)
echo "🛡️ [4/6] Mở port tường lửa nội bộ (7860, 80, 443, 14444)..."
for port in 7860 80 443 14444; do
    if ! sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null; then
        sudo iptables -I INPUT 5 -p tcp --dport "$port" -j ACCEPT
    fi
done
sudo netfilter-persistent save 2>/dev/null || true

# 5. Tải Model Weights nếu chưa có
echo "🤖 [5/6] Kiểm tra weights mô hình ZeroTTS..."
if [ ! -d "$APP_DIR/ZeroTTS_model" ] || [ ! -f "$APP_DIR/ZeroTTS_model/onnx/text_encoder.onnx" ]; then
    echo "   -> Đang tải mô hình ZeroTTS từ HuggingFace..."
    "$VENV_DIR/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('zeroweight-ai/ZeroTTS', local_dir='$APP_DIR/ZeroTTS_model')"
fi

# 6. Cấu hình Systemd Service chạy 24/7
echo "⚙️ [6/6] Cấu hình và kích hoạt Systemd Service (zerotts.service)..."
sudo tee /etc/systemd/system/zerotts.service > /dev/null <<EOF
[Unit]
Description=ZeroTTS Studio Production Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="OMP_NUM_THREADS=1"
ExecStart=$VENV_DIR/bin/python webui/server.py --host 0.0.0.0 --port 7860 --model $APP_DIR/ZeroTTS_model
Restart=always
RestartSec=5s
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable zerotts.service
sudo systemctl restart zerotts.service

echo ""
echo "============================================================"
echo "🎉 HOÀN TẤT TRIỂN KHAI PRODUCTION ZEROTTS!"
echo "============================================================"
echo "• Trạng thái Service: sudo systemctl status zerotts"
echo "• Xem Logs trực tiếp: sudo journalctl -u zerotts -f"
echo "• Quản lý API Key:    python auth_cli.py list"
echo "• Truy cập WebUI:     http://140.245.124.221:7860"
echo "============================================================"
