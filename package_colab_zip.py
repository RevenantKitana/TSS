"""Tạo file zip gọn nhẹ (chỉ chứa mã nguồn, bỏ qua các thư mục nặng như venv, model, ffmpeg)
để tải lên Google Colab hoặc lưu vào Google Drive.
"""

import os
import sys
import zipfile
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXCLUDE_DIRS = {
    ".venv",
    ".git",
    "__pycache__",
    "python-3.11.2-embed-amd64",
    "ZeroTTS_model",
    "outputs",
    "ffmpeg",
    ".idea",
    ".vscode",
}

EXCLUDE_EXTS = {".pyc", ".pyd", ".tmp", ".log"}


def create_colab_package(output_zip: str = "TSS_Code.zip"):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(root_dir, output_zip)
    
    if os.path.exists(zip_path):
        os.remove(zip_path)

    print(f"📦 Đang đóng gói mã nguồn từ {root_dir}...")
    file_count = 0
    total_size = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for dp, dn, fn in os.walk(root_dir):
            # Lọc bỏ thư mục loại trừ
            dn[:] = [d for d in dn if d not in EXCLUDE_DIRS and not d.startswith(".")]

            rel_dp = os.path.relpath(dp, root_dir)
            if rel_dp == ".":
                rel_dp = ""

            for f in fn:
                if f == output_zip or any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue

                abs_f = os.path.join(dp, f)
                arcname = os.path.join(rel_dp, f) if rel_dp else f
                zf.write(abs_f, arcname)
                file_count += 1
                total_size += os.path.getsize(abs_f)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✅ Đã tạo thành công file: {output_zip}")
    print(f"   - Số lượng file: {file_count}")
    print(f"   - Dung lượng: {zip_size_mb:.2f} MB")
    print(f"👉 Bạn có thể tải file '{output_zip}' này lên Google Colab hoặc Google Drive để chạy!")


if __name__ == "__main__":
    create_colab_package()
