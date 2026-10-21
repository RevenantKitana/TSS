#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script phân tách đoạn văn bản tự động không dùng AI (Rule-based / Regex),
chuẩn hóa định dạng đầu vào cho TSS (ZeroTTS):
    $[Ten_Du_An]
    [Text 1] Noi dung 1...
    [Text 2] Noi dung 2...

Hỗ trợ:
- Đọc file .txt, .docx, .md hoặc nhập trực tiếp văn bản.
- Tự động phát hiện chương/tiêu đề để tách thành các project ($[Folder]).
- Tách câu tiếng Việt thông minh (bảo vệ số thực 1.5, từ viết tắt PGS., TS., v.v.).
- Gom câu thành các đoạn có độ dài tối ưu (mặc định 150 - 250 ký tự, rất hợp TTS).
- Hoàn toàn dùng thư viện có sẵn (chuẩn Python), không cần cài đặt thêm.
"""

from __future__ import annotations

import argparse
import io
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

# Thêm đường dẫn src/ để nạp AdaptiveChunker
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

try:
    from zerotts.adaptive_chunker import AdaptiveChunker, BatchPreset, PRESETS
    HAS_ADAPTIVE = True
except ImportError:
    HAS_ADAPTIVE = False

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Danh sách từ viết tắt phổ biến để tránh ngắt câu sai ở dấu chấm
ABBREVIATIONS = {
    "tp", "tp.", "q", "q.", "h", "h.", "tx", "tx.", "p", "p.",
    "pgs", "pgs.", "ts", "ts.", "ths", "ths.", "bs", "bs.", "gs", "gs.",
    "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "dr", "dr.", "prof", "prof.",
    "v.v", "v.v.", "etc", "etc.", "e.g", "e.g.", "i.e", "i.e.",
    "đ/c", "đ/c.", "k/g", "đt", "đt.", "đd", "tr", "tr.", "đ", "đ.",
}

# Regex nhận diện tiêu đề chương/mục: Chương 1, Bài 2, Phần 3, Hồi 4, Mục 5, # Tiêu đề, v.v.
CHAPTER_PATTERN = re.compile(
    r"^(?:#{1,3}\s+|(?:\$|#|)\s*(?:Chương|Chuong|Bài|Bai|Phần|Phan|Hồi|Hoi|Mục|Muc|Tiết|Tiet|Chapter|Part|Section)\s+[\dIVXLCDMivxlcdm]+[\s:.\-_]).*",
    re.IGNORECASE | re.MULTILINE,
)


def sanitize_folder_name(name: str) -> str:
    """Chuẩn hóa tên folder hợp lệ cho TSS: chữ, số và dấu gạch dưới."""
    name = re.sub(r"[#\$\[\]\(\)\{\}\<\>:\\/\*\?\"\'\|]", "", name).strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name or "Du_an"


def read_file_content(file_path: str) -> tuple[str, str]:
    """Đọc nội dung văn bản từ file (.txt, .md, .docx). Không cần cài python-docx."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    clean_default_name = sanitize_folder_name(base_name)

    with open(file_path, "rb") as f:
        raw_bytes = f.read()

    # Kiểm tra nếu là file docx (file ZIP chứa word/document.xml)
    is_docx = file_path.lower().endswith(".docx") or (
        raw_bytes.startswith(b"PK\x03\x04") and b"word/document.xml" in raw_bytes[:8192]
    )

    if is_docx:
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                if "word/document.xml" in z.namelist():
                    xml_content = z.read("word/document.xml")
                    root = ET.fromstring(xml_content)
                    paragraphs = []
                    for p in root.iter():
                        tag = p.tag.split("}")[-1] if "}" in p.tag else p.tag
                        if tag == "p":
                            texts = []
                            for node in p.iter():
                                sub_tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
                                if sub_tag == "t" and node.text:
                                    texts.append(node.text)
                                elif sub_tag in ("br", "cr"):
                                    texts.append("\n")
                            line = "".join(texts).strip()
                            if line:
                                paragraphs.append(line)
                    return "\n\n".join(paragraphs), clean_default_name
        except Exception as e:
            print(f"[Cảnh báo] Lỗi đọc docx ({e}), thử đọc dạng văn bản...")

    # Đọc plain text với nhiều bảng mã phổ biến
    for enc in ["utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"]:
        try:
            return raw_bytes.decode(enc), clean_default_name
        except Exception:
            continue

    return raw_bytes.decode("utf-8", errors="ignore"), clean_default_name


def split_into_raw_sentences(text: str) -> list[str]:
    """Tách văn bản thành các câu mà không dùng AI, xử lý tốt tiếng Việt."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Chuẩn hóa khoảng trắng thừa
    text = re.sub(r"[ \t]+", " ", text)

    # Thay thế tạm các dấu chấm của số thực và từ viết tắt
    # 1. Số thập phân: 3.5 -> 3<DOT>5
    text = re.sub(r"(\d)\.(\d)", r"\1<NUMDOT>\2", text)
    text = re.sub(r"(\d),(\d)", r"\1<NUMCOMMA>\2", text)

    # 2. Xử lý từ viết tắt
    def _protect_abbr(match: re.Match) -> str:
        word = match.group(0)
        return word.replace(".", "<ABBRDOT>")

    for abbr in ABBREVIATIONS:
        pattern = r"\b" + re.escape(abbr.rstrip(".")) + r"\."
        text = re.sub(pattern, _protect_abbr, text, flags=re.IGNORECASE)

    # Tách theo đoạn văn (\n+) trước
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    raw_sentences = []

    # Regex ngắt câu: sau . ! ? hoặc … theo sau là khoảng trắng hoặc cuối đoạn
    sent_split_re = re.compile(r"(?<=[.!?…])\s+")

    for para in paragraphs:
        parts = sent_split_re.split(para)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # Khôi phục lại các dấu chấm đã bảo vệ
            part = part.replace("<NUMDOT>", ".")
            part = part.replace("<NUMCOMMA>", ",")
            part = part.replace("<ABBRDOT>", ".")
            raw_sentences.append(part)

    return raw_sentences


def break_long_sentence(sentence: str, max_chars: int) -> list[str]:
    """Nếu 1 câu dài vượt quá max_chars, phân tách tiếp theo dấu phẩy / từ."""
    if len(sentence) <= max_chars:
        return [sentence]

    # Ưu tiên tách theo dấu phẩy, chấm phẩy, gạch nối
    parts = re.split(r"(?<=[,;:–—-])\s+", sentence)
    if len(parts) > 1:
        chunks = []
        cur = ""
        for p in parts:
            p = p.strip()
            if not p:
                continue
            cand = f"{cur} {p}".strip() if cur else p
            if len(cand) <= max_chars:
                cur = cand
            else:
                if cur:
                    chunks.append(cur)
                if len(p) <= max_chars:
                    cur = p
                else:
                    # Nếu 1 vế vẫn quá dài, cắt theo từ
                    sub_words = p.split()
                    sub_cur = ""
                    for w in sub_words:
                        sub_cand = f"{sub_cur} {w}".strip() if sub_cur else w
                        if len(sub_cand) <= max_chars:
                            sub_cur = sub_cand
                        else:
                            if sub_cur:
                                chunks.append(sub_cur)
                            sub_cur = w
                    cur = sub_cur
        if cur:
            chunks.append(cur)
        return chunks

    # Trường hợp câu không có dấu ngắt phụ: cắt theo từ
    words = sentence.split()
    chunks = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip() if cur else w
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                chunks.append(cur)
            cur = w
    if cur:
        chunks.append(cur)
    return chunks


def pack_sentences_into_blocks(sentences: list[str], max_chars: int = 220, min_chars: int = 50) -> list[str]:
    """Gộp các câu nhỏ thành các block có độ dài vừa vặn (chuẩn input cho TTS)."""
    # 1. Bẻ nhỏ các câu quá dài trước
    refined_sentences = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) > max_chars:
            refined_sentences.extend(break_long_sentence(sent, max_chars))
        else:
            refined_sentences.append(sent)

    # 2. Gom nhóm câu
    blocks = []
    current_block = ""

    for sent in refined_sentences:
        if not current_block:
            current_block = sent
            continue

        cand = f"{current_block} {sent}"
        if len(cand) <= max_chars:
            current_block = cand
        else:
            # Block hiện tại đã đủ lớn
            blocks.append(current_block)
            current_block = sent

    if current_block:
        # Nếu block cuối cùng quá ngắn và có thể gộp vào block trước mà không vượt quá 1.3*max_chars
        if blocks and len(current_block) < min_chars and len(blocks[-1]) + len(current_block) + 1 <= int(max_chars * 1.3):
            blocks[-1] = f"{blocks[-1]} {current_block}"
        else:
            blocks.append(current_block)

    # 3. Chuẩn hóa dấu câu cuối: đảm bảo mỗi block kết thúc bằng ., !, ? hoặc …
    final_blocks = []
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b[-1] not in ".!?…":
            b = b.rstrip(" ,;:-–—") + "."
        final_blocks.append(b)

    return final_blocks


def parse_and_format_text(
    text: str,
    default_project_name: str = "Du_an_01",
    max_chars: int = 220,
    min_chars: int = 50,
    auto_detect_chapters: bool = True,
    preset: Optional[str] = None,
) -> str:
    """Tự động phân tách toàn bộ văn bản và sinh chuỗi chuẩn định dạng input TSS."""
    lines = text.strip().splitlines()
    sections: list[tuple[str, list[str]]] = []  # (tên project, danh sách dòng nội dung)

    current_title = default_project_name
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 1. Kiểm tra nếu là thẻ project $[Tên_Folder]
        proj_m = re.match(r"^\s*\$\s*\[(.*?)\]", stripped)
        if proj_m:
            if current_lines:
                sections.append((current_title, current_lines))
                current_lines = []
            clean_proj = sanitize_folder_name(proj_m.group(1))
            current_title = clean_proj or f"Du_an_{len(sections) + 1:02d}"
            continue

        # 2. Kiểm tra nếu là tiêu đề chương (Chương 1, Bài 2, # Tiêu đề...)
        if auto_detect_chapters and CHAPTER_PATTERN.match(stripped):
            if current_lines:
                sections.append((current_title, current_lines))
                current_lines = []
            clean_title = sanitize_folder_name(stripped)
            current_title = clean_title or f"Chuong_{len(sections) + 1:02d}"
            continue

        # 3. Lọc bỏ các tag cũ nếu có (ví dụ: [Text 1], [Text 2], [1]...)
        cleaned_line = re.sub(r"\[Text\s*\d+\]", "", stripped, flags=re.IGNORECASE)
        cleaned_line = re.sub(r"\s+", " ", cleaned_line).strip()
        if cleaned_line:
            current_lines.append(cleaned_line)

    if current_lines:
        sections.append((current_title, current_lines))

    if not sections:
        sections.append((default_project_name, [text]))

    # Sinh kết quả định dạng $[Folder] và [Text 1], [Text 2]...
    output_lines = []
    for sec_name, sec_lines in sections:
        sec_text = "\n".join(sec_lines)

        if preset and HAS_ADAPTIVE:
            active_p = PRESETS.get(preset.lower())
            if active_p:
                adaptive_chunker = AdaptiveChunker(default_preset=active_p)
                chunks_res = adaptive_chunker.chunk_text(sec_text, preset=active_p)
                blocks = [c.chunk for c in chunks_res if c.chunk]
            else:
                raw_sentences = split_into_raw_sentences(sec_text)
                blocks = pack_sentences_into_blocks(raw_sentences, max_chars=max_chars, min_chars=min_chars)
        else:
            raw_sentences = split_into_raw_sentences(sec_text)
            blocks = pack_sentences_into_blocks(raw_sentences, max_chars=max_chars, min_chars=min_chars)

        if not blocks:
            continue

        output_lines.append(f"$[{sec_name}]")
        output_lines.append("")
        for idx, block in enumerate(blocks, start=1):
            output_lines.append(f"[Text {idx}] {block}")
            output_lines.append("")
        output_lines.append("")

    return "\n".join(output_lines).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Script phân tách đoạn văn bản tự động không dùng AI cho TSS / ZeroTTS.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Đường dẫn file đầu vào (.txt, .docx, .md) hoặc để trống nếu dùng -t / STDIN",
    )
    parser.add_argument(
        "-t", "--text",
        help="Văn bản truyền trực tiếp từ dòng lệnh",
    )
    parser.add_argument(
        "-o", "--output",
        help="File đầu ra lưu kết quả (nếu không cung cấp, in trực tiếp ra màn hình)",
    )
    parser.add_argument(
        "-p", "--project",
        default="Du_an_01",
        help="Tên dự án / thư mục ($[Tên]) nếu file không có tiêu đề chương (mặc định: Du_an_01)",
    )
    parser.add_argument(
        "--preset",
        choices=["small", "medium", "large", "xlarge"],
        default=None,
        help="Preset Adaptive Chunker (small: 256/384, medium: 512/768, large: 1024/1536)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=220,
        help="Số ký tự tối đa cho mỗi đoạn [Text N] (khuyên dùng 150 - 250, mặc định: 220)",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=50,
        help="Số ký tự tối thiểu cho mỗi đoạn (mặc định: 50)",
    )
    parser.add_argument(
        "--no-chapters",
        action="store_true",
        help="Không tự động chia theo chương/tiêu đề, gom toàn bộ vào 1 dự án duy nhất",
    )

    args = parser.parse_args()

    # Xác định nguồn đầu vào
    raw_text = ""
    proj_name = args.project

    if args.text:
        raw_text = args.text
    elif args.input:
        try:
            raw_text, detected_name = read_file_content(args.input)
            if args.project == "Du_an_01" and detected_name:
                proj_name = detected_name
        except Exception as e:
            print(f"❌ Lỗi: {e}", file=sys.stderr)
            sys.exit(1)
    elif not sys.stdin.isatty():
        raw_text = sys.stdin.read()
    else:
        parser.print_help()
        print("\n👉 Ví dụ sử dụng:")
        print("  python scripts/split_text.py input.txt -o formatted_input.txt")
        print("  python scripts/split_text.py input.docx --max-chars 200 -o output.txt")
        print('  python scripts/split_text.py -t "Đoạn văn dài cần chia..." -o output.txt')
        sys.exit(0)

    if not raw_text.strip():
        print("⚠️ Văn bản đầu vào rỗng!", file=sys.stderr)
        sys.exit(1)

    result = parse_and_format_text(
        raw_text,
        default_project_name=proj_name,
        max_chars=args.max_chars,
        min_chars=args.min_chars,
        auto_detect_chapters=not args.no_chapters,
        preset=args.preset,
    )

    if args.output:
        out_dir = os.path.dirname(args.output)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Đã phân tách xong và lưu vào: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
