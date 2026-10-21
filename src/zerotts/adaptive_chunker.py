"""Adaptive TTS Text Chunker.

Chia van ban thanh cac batch toi uu cho TTS dua tren moc muc tieu (target_chars),
gioi han toi da (max_chars) va tim kiem ranh gioi 2 chieu (bidirectional boundary search)
gan moc nhat.

Ho tro:
- 4 Preset tieu chuan (Small, Medium, Large, X-Large) va tuy chinh.
- Ranh gioi uu tien: Sentence (. ! ? ...) -> Clause (, ; : —) -> Word -> Hard Cut.
- Khong bo sot, khong lap noi dung (No-gap, no-overlap guarantee).
- Render Orchestrator voi co che tu dong chia nho rieng chunk loi (Adaptive Sub-chunking & Retry).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class BoundaryType(str, Enum):
    """Phan loai ranh gioi cat doan."""
    SENTENCE = "SENTENCE"        # Dau ket cau: . ! ? … \n\n
    CLAUSE = "CLAUSE"            # Dau ngat phu: , ; : — – \n
    WORD = "WORD"                # Ranh gioi tu (khoang trang)
    HARD_CUT = "HARD_CUT"        # Cat cung theo gioi han ky tu
    END_OF_TEXT = "END_OF_TEXT"  # Ket thuc van ban tu nhien


@dataclass(frozen=True)
class BatchPreset:
    """Cau hinh gioi han do dai theo Unicode code point."""
    name: str
    target_chars: int
    max_chars: int
    min_chars: int = 40
    description: str = ""

    def __post_init__(self):
        if self.target_chars <= 0:
            raise ValueError(f"target_chars phai > 0, nhan duoc: {self.target_chars}")
        if self.max_chars < self.target_chars:
            raise ValueError(
                f"max_chars ({self.max_chars}) phai >= target_chars ({self.target_chars})"
            )
        if self.min_chars < 0 or self.min_chars > self.target_chars:
            raise ValueError(
                f"min_chars ({self.min_chars}) phai >= 0 va <= target_chars ({self.target_chars})"
            )


# 4 Preset tieu chuan de xuat
PRESET_SMALL = BatchPreset(
    name="Small",
    target_chars=256,
    max_chars=384,
    min_chars=40,
    description="Doan ngan, hoi thoai, an toan cao, tranh hallucination",
)
PRESET_MEDIUM = BatchPreset(
    name="Medium",
    target_chars=512,
    max_chars=768,
    min_chars=80,
    description="Can bang tu nhien, phu hop doc sach, bao chi, truyen",
)
PRESET_LARGE = BatchPreset(
    name="Large",
    target_chars=1024,
    max_chars=1536,
    min_chars=120,
    description="Doan dai, phu hop tai lieu, tiet kiem so lan goi model",
)
PRESET_XLARGE = BatchPreset(
    name="X-Large",
    target_chars=2048,
    max_chars=3072,
    min_chars=200,
    description="Rat dai, danh cho model co context window lon",
)

PRESETS: Dict[str, BatchPreset] = {
    "small": PRESET_SMALL,
    "medium": PRESET_MEDIUM,
    "large": PRESET_LARGE,
    "xlarge": PRESET_XLARGE,
    "x-large": PRESET_XLARGE,
}


@dataclass
class ChunkResult:
    """Ket qua cua tung chunk sau khi phan doan."""
    chunk: str
    start_index: int
    end_index: int
    next_start_index: int
    boundary_type: BoundaryType
    char_count: int
    distance_to_target: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# Tu viet tat pho bien (tieng Viet & tieng Anh) de tranh cat nham cau
_COMMON_ABBREVIATIONS = {
    "tp", "tp.", "q", "q.", "h", "h.", "tx", "tx.", "p", "p.",
    "pgs", "pgs.", "ts", "ts.", "ths", "ths.", "bs", "bs.", "gs", "gs.",
    "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "dr", "dr.", "prof", "prof.",
    "v.v", "v.v.", "etc", "etc.", "e.g", "e.g.", "i.e", "i.e.",
    "đ/c", "đ/c.", "k/g", "đt", "đt.", "đd", "tr", "tr.",
}


class AdaptiveChunker:
    """Bo phan tach van ban thich ung danh rieng cho TTS (Khong dung AI)."""

    def __init__(self, default_preset: BatchPreset = PRESET_MEDIUM):
        self.default_preset = default_preset

    @classmethod
    def get_preset(cls, name_or_preset: str | BatchPreset) -> BatchPreset:
        if isinstance(name_or_preset, BatchPreset):
            return name_or_preset
        key = str(name_or_preset).lower().strip()
        if key in PRESETS:
            return PRESETS[key]
        raise KeyError(
            f"Preset '{name_or_preset}' khong ton tai. Lua chon hop le: {list(PRESETS.keys())}"
        )

    def is_sentence_boundary(self, text: str, pos: int) -> bool:
        """Kiem tra xem vi tri pos (ket thuc tai pos) co phai la ket cau hop le khong.
        
        pos la vi tri ngay sau dau ngat cau (VD: sau '.', '!', '?', '…').
        Bao ve: khong ngat o so thap phan (15.5) hoac tu viet tat (PGS.TS, Mr.).
        """
        if pos <= 0 or pos > len(text):
            return False

        char_before = text[pos - 1]
        if char_before not in ".!?…":
            return False

        # 1. Khong phai ket cau neu theo sau ngay lap tuc boi chu so (so thap phan nhu 3.14)
        if pos < len(text) and text[pos].isdigit():
            return False

        # 2. Khong phai ket cau neu phia truoc la chu so va phia sau la chu so (VD: 1.5)
        if pos >= 2 and text[pos - 2].isdigit() and pos < len(text) and text[pos].isdigit():
            return False

        # 3. Kiem tra tu viet tat phia truoc
        # Quet nguoc tim tu ngay truoc dau cham
        left_sub = text[:pos]
        m = re.search(r"([A-Za-zÀ-ỹ0-9_./-]+)\.$", left_sub)
        if m:
            token = m.group(1).lower()
            if token in _COMMON_ABBREVIATIONS or f"{token}." in _COMMON_ABBREVIATIONS:
                return False
            # Tu viet tat 1 chu cai in hoa nhu A., B.
            if len(m.group(1)) == 1 and m.group(1).isupper():
                return False

        # 4. Hop le neu o cuoi chuoi hoac theo sau boi khoang trang / dau ngoac / xuong dong
        if pos == len(text):
            return True
        next_char = text[pos]
        return next_char.isspace() or next_char in "\"'”)»]\n"

    def is_clause_boundary(self, text: str, pos: int) -> bool:
        """Kiem tra xem vi tri pos co phai la dau ngat phu (, ; : — – \n) hop le khong."""
        if pos <= 0 or pos > len(text):
            return False
        char_before = text[pos - 1]
        if char_before in ",;:—–":
            # Khong phai ngat neu la so co dau phay hang nghin nhu 10,000
            if char_before == "," and pos >= 2 and text[pos - 2].isdigit():
                if pos < len(text) and text[pos].isdigit():
                    return False
            return True
        if char_before == "\n":
            return True
        return False

    def is_word_boundary(self, text: str, pos: int) -> bool:
        """Kiem tra xem vi tri pos co phai la ranh gioi tu (truoc khoang trang) khong."""
        if pos <= 0 or pos >= len(text):
            return False
        # Ranh gioi tu: ky tu tai pos la khoang trang hoac ky tu truoc pos khong phai khoang trang va tai pos la khoang trang
        return text[pos].isspace() and not text[pos - 1].isspace()

    def find_next_chunk(
        self,
        text: str,
        start_index: int,
        preset: BatchPreset,
    ) -> Optional[ChunkResult]:
        """Tim va tra ve 1 chunk tiep theo bat dau tu start_index.
        
        Quy trinh:
        1. Xac dinh cua so: target_index va max_index.
        2. Tim kiem 2 chieu quanh target_index trong [min_index, max_index].
        3. Uu tien: SENTENCE -> CLAUSE -> WORD -> HARD_CUT.
        """
        text_len = len(text)
        if start_index >= text_len:
            return None

        # Bo qua khoang trang o dau chunk neu co
        while start_index < text_len and text[start_index].isspace():
            start_index += 1
        if start_index >= text_len:
            return None

        remaining = text_len - start_index

        # Neu toan bo phan con lai nho hon hoac bang target_chars -> lay het (END_OF_TEXT)
        if remaining <= preset.target_chars:
            raw_chunk = text[start_index:text_len]
            return ChunkResult(
                chunk=raw_chunk.strip(),
                start_index=start_index,
                end_index=text_len,
                next_start_index=text_len,
                boundary_type=BoundaryType.END_OF_TEXT,
                char_count=len(raw_chunk.strip()),
                distance_to_target=abs(len(raw_chunk) - preset.target_chars),
            )

        target_index = start_index + preset.target_chars
        max_index = min(text_len, start_index + preset.max_chars)
        min_index = start_index + preset.min_chars

        # Thu thap cac ung vien ranh gioi
        # Danh sach: (distance_to_target, is_after_target, cut_pos, boundary_type)
        sentence_candidates: List[Tuple[int, bool, int, BoundaryType]] = []
        clause_candidates: List[Tuple[int, bool, int, BoundaryType]] = []
        word_candidates: List[Tuple[int, bool, int, BoundaryType]] = []

        # Quet toan bo khoang [min_index, max_index]
        for pos in range(min_index, max_index + 1):
            dist = abs(pos - target_index)
            is_forward = pos >= target_index

            if self.is_sentence_boundary(text, pos):
                sentence_candidates.append((dist, is_forward, pos, BoundaryType.SENTENCE))
            elif self.is_clause_boundary(text, pos):
                clause_candidates.append((dist, is_forward, pos, BoundaryType.CLAUSE))
            elif self.is_word_boundary(text, pos):
                word_candidates.append((dist, is_forward, pos, BoundaryType.WORD))

        chosen_cut: Optional[int] = None
        chosen_type: BoundaryType = BoundaryType.HARD_CUT

        # Ham chon ung vien gan target_index nhat; neu bang nhau uu tien huong forward de bao toan cau
        def _pick_best(candidates):
            if not candidates:
                return None
            # Sort theo distance tang dan, neu distance bang nhau thi is_forward=True (1) truoc
            candidates.sort(key=lambda x: (x[0], not x[1]))
            return candidates[0]

        best_sentence = _pick_best(sentence_candidates)
        if best_sentence:
            chosen_cut = best_sentence[2]
            chosen_type = best_sentence[3]
        else:
            best_clause = _pick_best(clause_candidates)
            if best_clause:
                chosen_cut = best_clause[2]
                chosen_type = best_clause[3]
            else:
                best_word = _pick_best(word_candidates)
                if best_word:
                    chosen_cut = best_word[2]
                    chosen_type = best_word[3]
                else:
                    # Khong tim thay ranh gioi tu nhien -> Cung tai max_index
                    chosen_cut = max_index
                    chosen_type = BoundaryType.HARD_CUT

        # Cat chuoi
        end_index = chosen_cut
        raw_chunk = text[start_index:end_index]

        # Xac dinh vi tri bat dau cua chunk tiep theo (bo qua khoang trang phan cach)
        next_start = end_index
        while next_start < text_len and text[next_start].isspace():
            next_start += 1

        clean_chunk = raw_chunk.strip()
        dist_final = abs(len(clean_chunk) - preset.target_chars)

        return ChunkResult(
            chunk=clean_chunk,
            start_index=start_index,
            end_index=end_index,
            next_start_index=next_start,
            boundary_type=chosen_type,
            char_count=len(clean_chunk),
            distance_to_target=dist_final,
        )

    def chunk_text(
        self,
        text: str,
        preset: Optional[BatchPreset | str] = None,
    ) -> List[ChunkResult]:
        """Phan tach toan bo van ban thanh danh sach cac chunk theo preset."""
        if not text or not text.strip():
            return []

        active_preset = self.get_preset(preset) if preset else self.default_preset
        chunks: List[ChunkResult] = []
        curr_index = 0
        text_len = len(text)

        while curr_index < text_len:
            result = self.find_next_chunk(text, curr_index, active_preset)
            if result is None:
                break
            if not result.chunk:
                # Tranh vong lap vo tan neu gap khoang trang lien tiep o cuoi chuoi
                curr_index = result.next_start_index
                continue
            chunks.append(result)
            # Dam bao luon tien ve phia truoc
            if result.next_start_index <= curr_index:
                curr_index += 1
            else:
                curr_index = result.next_start_index

        return chunks


# ── Render Orchestrator & Adaptive Retry (Buoc 7) ─────────────────────────────

@dataclass
class RenderResult:
    """Ket qua render cua tung chunk kem lich su retry."""
    chunk_index: int
    text: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    preset_used: str = ""
    retry_count: int = 0
    sub_chunks: List[RenderResult] = field(default_factory=list)


class RenderOrchestrator:
    """Bo dieu phoi goi TTS va tu dong chia nho chunk khi render bi loi."""

    def __init__(
        self,
        renderer: Callable[[str], Any],
        chunker: Optional[AdaptiveChunker] = None,
        max_subchunk_retries: int = 2,
    ):
        """
        renderer: Ham thuc thi nhan vao (text: str) -> output (Audio tensor / Path / v.v.)
                  Nem Exception neu render that bai (OOM, timeout, hallucination...).
        """
        self.renderer = renderer
        self.chunker = chunker or AdaptiveChunker()
        self.max_retries = max_subchunk_retries

    def _get_smaller_preset(self, current_preset: BatchPreset, text_len: int = 0) -> BatchPreset:
        """Ha bac preset de chia nho hon khi retry."""
        base_target = current_preset.target_chars
        # Neu doan van thuc te ngan hon target_chars cua preset hien tai,
        # ta can lay moc do dai thuc te cua doan van de chia doi.
        if text_len > 0 and text_len < base_target:
            base_target = text_len

        # Chon bac thang tiep theo
        if base_target > PRESET_LARGE.target_chars:
            cand = PRESET_LARGE
        elif base_target > PRESET_MEDIUM.target_chars:
            cand = PRESET_MEDIUM
        elif base_target > PRESET_SMALL.target_chars:
            cand = PRESET_SMALL
        else:
            cand = None

        if cand is not None and (text_len == 0 or cand.target_chars < text_len):
            return cand

        # Neu da o Small hoac can chia nho hon nua: chia doi do dai
        new_target = max(30, int(base_target * 0.5))
        new_max = max(new_target + 15, int(new_target * 1.4))
        new_min = max(10, new_target // 3)

        return BatchPreset(
            name=f"Sub_{new_target}",
            target_chars=new_target,
            max_chars=new_max,
            min_chars=new_min,
        )

    def render_chunk_with_retry(
        self,
        text: str,
        current_preset: BatchPreset,
        current_retry_level: int = 0,
    ) -> RenderResult:
        """Goi render cho 1 doan van ban; neu that bai, tu dong chia nho va thu lai."""
        try:
            output = self.renderer(text)
            return RenderResult(
                chunk_index=0,
                text=text,
                success=True,
                output=output,
                preset_used=current_preset.name,
                retry_count=current_retry_level,
            )
        except Exception as exc:
            error_msg = str(exc)

            # Neu con luot retry va doan van con du dai de chia
            if (
                current_retry_level < self.max_retries
                and len(text) > 30
            ):
                smaller_preset = self._get_smaller_preset(current_preset, text_len=len(text))
                sub_chunks = self.chunker.chunk_text(text, preset=smaller_preset)

                # Neu tach duoc thanh it nhat 2 manh nho hon
                if len(sub_chunks) > 1:
                    sub_results: List[RenderResult] = []
                    all_sub_success = True
                    for sc in sub_chunks:
                        sub_res = self.render_chunk_with_retry(
                            sc.chunk,
                            smaller_preset,
                            current_retry_level=current_retry_level + 1,
                        )
                        sub_results.append(sub_res)
                        if not sub_res.success:
                            all_sub_success = False

                    return RenderResult(
                        chunk_index=0,
                        text=text,
                        success=all_sub_success,
                        output=[r.output for r in sub_results if r.success],
                        error=None if all_sub_success else "Mot so sub-chunk that bai",
                        preset_used=current_preset.name,
                        retry_count=current_retry_level + 1,
                        sub_chunks=sub_results,
                    )

            # Khong the retry nua
            return RenderResult(
                chunk_index=0,
                text=text,
                success=False,
                error=error_msg,
                preset_used=current_preset.name,
                retry_count=current_retry_level,
            )

    def orchestrate(
        self,
        text: str,
        preset: Optional[BatchPreset | str] = None,
    ) -> List[RenderResult]:
        """Dieu phoi toan bo quy trinh: Chunking -> Render tung chunk -> Tu retry neu loi."""
        active_preset = self.chunker.get_preset(preset) if preset else self.chunker.default_preset
        chunks = self.chunker.chunk_text(text, preset=active_preset)

        final_results: List[RenderResult] = []
        for idx, item in enumerate(chunks, start=1):
            res = self.render_chunk_with_retry(item.chunk, active_preset)
            res.chunk_index = idx
            final_results.append(res)

        return final_results
