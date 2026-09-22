"""ZeroTTS Colab Launcher with Automated Cloudflare Tunneling.
Provides 1-command startup for Google Colab / Kaggle / remote Linux environments.

Usage:
    python colab_runner.py
    python colab_runner.py --port 7860 --model ./ZeroTTS_model
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request


def setup_cloudflared() -> str:
    """Ensure cloudflared executable is available on Linux system."""
    cf_path = shutil.which("cloudflared") or "/usr/local/bin/cloudflared"
    if not os.path.exists(cf_path):
        print("📥 Đang tải Cloudflare Tunnel binary (cloudflared)...")
        os.makedirs(os.path.dirname(cf_path), exist_ok=True)
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        try:
            urllib.request.urlretrieve(url, cf_path)
            subprocess.run(["chmod", "+x", cf_path], check=True)
            print("✅ Đã cài đặt cloudflared thành công!")
        except Exception as e:
            print(f"⚠️ Không thể tải cloudflared tự động: {e}")
            return "cloudflared"
    return cf_path


def main():
    parser = argparse.ArgumentParser(description="ZeroTTS Colab Launcher")
    parser.add_argument("--model", default=os.environ.get("ZEROTTS_MODEL", "./ZeroTTS_model"), help="Model dir or HF ID")
    parser.add_argument("--port", type=int, default=7860, help="Local server port")
    parser.add_argument("--host", default="0.0.0.0", help="Host binding (default: 0.0.0.0)")
    parser.add_argument("--drive-dir", default=os.environ.get("ZEROTTS_OUTPUT_DIR", ""), help="Output directory on Drive/local")
    args = parser.parse_args()

    if args.drive_dir:
        os.environ["ZEROTTS_OUTPUT_DIR"] = args.drive_dir
        os.makedirs(args.drive_dir, exist_ok=True)
        print(f"📁 Thư mục lưu kết quả: {args.drive_dir}")

    # 1. Start Server
    print("🚀 Đang khởi chạy ZeroTTS FastAPI WebUI Server...")
    server_cmd = [sys.executable, "webui/server.py", "--model", args.model, "--host", args.host, "--port", str(args.port)]
    server_proc = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    time.sleep(3)

    # 2. Start Cloudflare Tunnel
    cf_bin = setup_cloudflared()
    print("🌐 Đang thiết lập đường hầm bảo mật Cloudflare Tunnel...")
    tunnel_cmd = [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{args.port}"]
    tunnel_proc = subprocess.Popen(tunnel_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    public_url = None
    for _ in range(50):
        line = tunnel_proc.stdout.readline()
        if not line:
            time.sleep(0.3)
            continue
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\\.com", line)
        if match:
            public_url = match.group(0)
            break

    print("\n" + "=" * 65)
    if public_url:
        print("🎉 ZERO TTS WEBUI ĐÃ SẴN SÀNG TRUY CẬP!")
        print(f"👉 Link WebUI (HTTPS):  {public_url}")
    else:
        print("⚠️ Đang khởi động đường hầm, vui lòng đợi thêm giây lát...")
    print("=" * 65 + "\n")

    # 3. Stream server output
    try:
        while True:
            line = server_proc.stdout.readline()
            if line:
                print(line, end="", flush=True)
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Đang dừng server và đóng tunnel...")
        server_proc.terminate()
        tunnel_proc.terminate()
        print("✅ Đã dừng hoàn toàn.")


if __name__ == "__main__":
    main()
