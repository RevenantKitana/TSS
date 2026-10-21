#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tool benchmark và kiểm thử trực quan Adaptive TTS Text Chunker.

Chạy thử nghiệm trên các đoạn văn bản dài thực tế, đo đạc phân phối ranh giới
(Sentence / Clause / Word / Hard cut), kiểm tra độ dài chunk và tính toàn vẹn dữ liệu.

Cách dùng:
    python scripts/test_chunker_benchmark.py
    python scripts/test_chunker_benchmark.py --file Test_input.txt --preset small
    python scripts/test_chunker_benchmark.py --file your_book.txt --preset medium
"""

from __future__ import annotations

import argparse
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from zerotts.adaptive_chunker import (
    AdaptiveChunker,
    BatchPreset,
    BoundaryType,
    PRESET_LARGE,
    PRESET_MEDIUM,
    PRESET_SMALL,
    PRESET_XLARGE,
    PRESETS,
)

SAMPLE_VIETNAMESE_TEXT = """
An toàn lao động trong thi công xây dựng là một trong những yêu cầu nghiêm ngặt và tối quan trọng hàng đầu. Theo báo cáo của PGS.TS Nguyễn Văn A, có đến hơn 15.5% các vụ tai nạn đáng tiếc có thể phòng ngừa hoàn toàn nếu người lao động tuân thủ đúng quy trình kiểm tra bảo hộ trước ca làm việc. Trước khi vận hành bất kỳ máy móc cơ giới nào, kỹ sư phụ trách phải kiểm tra áp suất, hệ thống phanh và trang bị bảo hộ cá nhân bao gồm: mũ cứng, kính chắn bụi, găng tay cách điện và giày mũi thép.

Bên cạnh yếu tố kỹ thuật, kỹ năng giao tiếp và làm việc nhóm cũng đóng vai trò quyết định đến năng suất làm việc của toàn đội ngũ. Một người quản lý giỏi không chỉ biết ra lệnh mà phải biết lắng nghe, thấu hiểu khó khăn của từng thành viên tại công trường. Khi xảy ra sự cố ngoài ý muốn, thay vì đổ lỗi cho nhau, cả nhóm cần ngồi lại, phân tích nguyên nhân cốt lõi và đưa ra giải pháp khắc phục kịp thời. Sự đoàn kết và tinh thần trách nhiệm chính là chìa khóa tạo nên một môi trường làm việc an toàn, bền vững và hiệu quả.
"""


def benchmark_text(text: str, preset_name: str = "medium"):
    preset = PRESETS.get(preset_name.lower(), PRESET_MEDIUM)
    chunker = AdaptiveChunker(default_preset=preset)

    print("=" * 65)
    print(f"🔬 BÁO CÁO BENCHMARK ADAPTIVE TTS TEXT CHUNKER")
    print("=" * 65)
    print(f"• Preset thử nghiệm: [{preset.name}]")
    print(f"  - Target chars : {preset.target_chars}")
    print(f"  - Max chars    : {preset.max_chars}")
    print(f"  - Min chars    : {preset.min_chars}")
    print(f"• Tổng độ dài văn bản gốc: {len(text):,} ký tự (Unicode code points)")
    print(f"• Tổng số từ văn bản gốc : {len(text.split()):,} từ")
    print("-" * 65)

    start_time = time.perf_counter()
    chunks = chunker.chunk_text(text, preset=preset)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    if not chunks:
        print("⚠️ Không có chunk nào được sinh ra (văn bản rỗng).")
        return

    # Thống kê phân loại ranh giới
    boundary_counts = {bt: 0 for bt in BoundaryType}
    char_lengths = []
    reconstructed_words = []

    for c in chunks:
        boundary_counts[c.boundary_type] += 1
        char_lengths.append(c.char_count)
        reconstructed_words.extend(c.chunk.split())

    min_len = min(char_lengths)
    max_len = max(char_lengths)
    avg_len = sum(char_lengths) / len(char_lengths)

    # Kiểm tra toàn vẹn
    orig_words = text.split()
    is_lossless = reconstructed_words == orig_words
    is_safe = max_len <= preset.max_chars

    print(f"⚡ Thời gian xử lý   : {elapsed_ms:.2f} ms")
    print(f"📊 Tổng số chunks    : {len(chunks)}")
    print(f"📏 Độ dài chunk (Min/Avg/Max): {min_len} / {avg_len:.1f} / {max_len} ký tự")
    print()
    print("📌 Phân bổ ranh giới ngắt đoạn:")
    for bt, count in boundary_counts.items():
        if count > 0:
            pct = (count / len(chunks)) * 100
            tag_icon = "🟢" if bt == BoundaryType.SENTENCE else ("🟡" if bt == BoundaryType.CLAUSE else ("🟠" if bt == BoundaryType.WORD else "🔴"))
            print(f"   {tag_icon} {bt.value:<12} : {count:>3} ({pct:>5.1f}%)")

    print()
    print("🔒 Kiểm tra tiêu chuẩn an toàn:")
    print(f"   - Không vượt trần max_chars ({preset.max_chars} ký tự) : {'✅ ĐẠT' if is_safe else '❌ KHÔNG ĐẠT'}")
    print(f"   - Toàn vẹn nội dung (không mất/lặp từ)     : {'✅ ĐẠT (100% Khớp)' if is_lossless else '❌ CÓ SAI LỆCH'}")
    print("=" * 65)
    print()

    # Hiển thị trực quan từng chunk
    print("📋 CHI TIẾT TỪNG CHUNK ĐÃ PHÂN TÁCH:")
    print("-" * 65)
    for idx, c in enumerate(chunks, start=1):
        badge = f"[{c.boundary_type.value}]"
        print(f"Chunk #{idx:02d} ({c.char_count} chars, delta={c.distance_to_target}) {badge}:")
        print(f"\"{c.chunk}\"")
        print()


def main():
    parser = argparse.ArgumentParser(description="Benchmark & Test Adaptive TTS Text Chunker.")
    parser.add_argument(
        "--file", "-f",
        help="Đường dẫn file văn bản cần test (mặc định dùng đoạn văn mẫu)",
    )
    parser.add_argument(
        "--preset", "-p",
        default="small",
        choices=["small", "medium", "large", "xlarge"],
        help="Preset kiểm thử (mặc định: small)",
    )

    args = parser.parse_args()

    test_content = SAMPLE_VIETNAMESE_TEXT
    if args.file and os.path.isfile(args.file):
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            test_content = f.read()

    benchmark_text(test_content, preset_name=args.preset)


if __name__ == "__main__":
    main()
