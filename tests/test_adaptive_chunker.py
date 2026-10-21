#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive test suite for Adaptive TTS Text Chunker and Render Orchestrator."""

import os
import sys
import unittest

# Đảm bảo import được module trong src/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from zerotts.adaptive_chunker import (
    AdaptiveChunker,
    BatchPreset,
    BoundaryType,
    PRESET_SMALL,
    PRESET_MEDIUM,
    PRESET_LARGE,
    PRESET_XLARGE,
    PRESETS,
    RenderOrchestrator,
    RenderResult,
)


class TestBatchPreset(unittest.TestCase):
    """Kiểm tra tính hợp lệ của cấu hình BatchPreset."""

    def test_valid_presets(self):
        for name, preset in PRESETS.items():
            self.assertGreater(preset.target_chars, 0)
            self.assertGreaterEqual(preset.max_chars, preset.target_chars)
            self.assertLessEqual(preset.min_chars, preset.target_chars)

    def test_invalid_presets(self):
        # max_chars < target_chars
        with self.assertRaises(ValueError):
            BatchPreset(name="Invalid", target_chars=500, max_chars=400)

        # target_chars <= 0
        with self.assertRaises(ValueError):
            BatchPreset(name="Invalid", target_chars=0, max_chars=400)

        # min_chars > target_chars
        with self.assertRaises(ValueError):
            BatchPreset(name="Invalid", target_chars=200, max_chars=300, min_chars=250)


class TestAdaptiveChunkerBoundaryDetection(unittest.TestCase):
    """Kiểm tra tính chính xác của việc phát hiện ranh giới câu, dấu ngắt và từ."""

    def setUp(self):
        self.chunker = AdaptiveChunker()

    def test_sentence_boundary_valid(self):
        text = "Hôm nay trời đẹp. Ngày mai trời mưa!"
        # Vị trí ngay sau dấu chấm (index 17)
        self.assertTrue(self.chunker.is_sentence_boundary(text, 17))
        # Vị trí ngay sau dấu chấm than ở cuối chuỗi
        self.assertTrue(self.chunker.is_sentence_boundary(text, len(text)))

    def test_sentence_boundary_decimal_protection(self):
        text = "Tỷ lệ tăng trưởng đạt 15.5% trong quý này."
        dot_pos = text.find(".") + 1
        # Dấu chấm giữa 15 và 5 KHÔNG được coi là ranh giới kết câu
        self.assertFalse(self.chunker.is_sentence_boundary(text, dot_pos))

    def test_sentence_boundary_abbreviation_protection(self):
        text = "PGS.TS Nguyễn Văn A đã phát biểu."
        # Dấu chấm sau PGS
        pgs_dot = text.find("PGS.") + 4
        self.assertFalse(self.chunker.is_sentence_boundary(text, pgs_dot))
        # Dấu chấm sau TS
        ts_dot = text.find("TS.") + 3
        self.assertFalse(self.chunker.is_sentence_boundary(text, ts_dot))

    def test_clause_boundary(self):
        text = "Trước khi làm việc, người lao động cần kiểm tra thiết bị."
        comma_pos = text.find(",") + 1
        self.assertTrue(self.chunker.is_clause_boundary(text, comma_pos))

        # Số có dấu phẩy hàng nghìn (10,000) không phải là ngắt mệnh đề
        num_text = "Chi phí là 10,000 đồng."
        num_comma = num_text.find(",") + 1
        self.assertFalse(self.chunker.is_clause_boundary(num_text, num_comma))

    def test_word_boundary(self):
        text = "Xin chào các bạn"
        space_pos = text.find(" ")
        self.assertTrue(self.chunker.is_word_boundary(text, space_pos))


class TestAdaptiveChunkerWindowing(unittest.TestCase):
    """Kiểm tra thuật toán tìm kiếm 2 chiều và phân đoạn theo cửa sổ."""

    def setUp(self):
        self.chunker = AdaptiveChunker()

    def test_empty_or_whitespace_input(self):
        self.assertEqual(self.chunker.chunk_text(""), [])
        self.assertEqual(self.chunker.chunk_text("    \n\t  "), [])

    def test_text_shorter_than_target(self):
        text = "Một đoạn văn ngắn dưới mốc mục tiêu."
        chunks = self.chunker.chunk_text(text, preset=PRESET_SMALL)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk, text)
        self.assertEqual(chunks[0].boundary_type, BoundaryType.END_OF_TEXT)

    def test_bidirectional_search_forward_preference(self):
        """Kiểm tra tìm kiếm ranh giới phía SAU mốc mục tiêu (forward) trong giới hạn max_chars."""
        # Tạo câu có độ dài ~280 ký tự (vượt target 256 nhưng dưới max 384)
        c1 = "An toàn lao động là một trong những yêu cầu bắt buộc và tối quan trọng trong mọi công trình xây dựng hiện nay. "
        c2 = "Người lao động cần tuân thủ nghiêm ngặt các quy tắc an toàn bảo hộ cá nhân nhằm tránh các tai nạn đáng tiếc xảy ra."
        full_text = c1 + c2

        custom_preset = BatchPreset(name="TestBidirectional", target_chars=120, max_chars=200, min_chars=40)
        chunks = self.chunker.chunk_text(full_text, preset=custom_preset)

        # Chunk đầu tiên nên bắt trọn c1 (ngắt câu tự nhiên) thay vì cắt sớm
        self.assertEqual(chunks[0].boundary_type, BoundaryType.SENTENCE)
        self.assertTrue(chunks[0].chunk.endswith("."))

    def test_no_punctuation_fallback_to_word(self):
        """Văn bản không có dấu câu -> Phải fallback ngắt theo từ (WORD)."""
        words = ["tu"] * 80  # ~240 ký tự gồm khoảng trắng
        text = " ".join(words)
        preset = BatchPreset(name="TestWord", target_chars=50, max_chars=80, min_chars=20)
        chunks = self.chunker.chunk_text(text, preset=preset)

        self.assertGreater(len(chunks), 1)
        for c in chunks[:-1]:
            self.assertEqual(c.boundary_type, BoundaryType.WORD)
            self.assertLessEqual(c.char_count, preset.max_chars)

    def test_continuous_string_hard_cut(self):
        """Chuỗi ký tự dài liên tục không có khoảng trắng -> Buộc phải HARD_CUT an toàn."""
        giant_string = "a" * 300
        preset = BatchPreset(name="TestHardCut", target_chars=50, max_chars=80, min_chars=20)
        chunks = self.chunker.chunk_text(giant_string, preset=preset)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].boundary_type, BoundaryType.HARD_CUT)
        self.assertEqual(chunks[0].char_count, preset.max_chars)

    def test_invariants_no_data_loss_and_no_duplication(self):
        """Bảo đảm nguyên tắc: Không bỏ sót từ và không lặp lại nội dung."""
        text = (
            "Giao tiếp hiệu quả bắt đầu từ những điều rất đơn giản, chẳng hạn như một lời chào đúng lúc. "
            "Khi gặp người khác, hãy chủ động chào hỏi với thái độ lịch sự và thân thiện. "
            "Khi trò chuyện, hãy tập trung lắng nghe người đối diện. "
            "Không ngắt lời khi người khác đang nói và nên đặt câu hỏi khi cần làm rõ thông tin. "
            "Cách lựa chọn từ ngữ cũng rất quan trọng. "
            "Hãy sử dụng những lời nói rõ ràng, phù hợp với hoàn cảnh và tôn trọng người nghe."
        )

        for preset_name in ["small", "medium"]:
            preset = PRESETS[preset_name]
            chunks = self.chunker.chunk_text(text, preset=preset)

            # 1. Kiểm tra giới hạn max_chars
            for c in chunks:
                self.assertLessEqual(
                    c.char_count,
                    preset.max_chars,
                    f"Chunk '{c.chunk[:30]}...' vượt max_chars ({c.char_count} > {preset.max_chars})",
                )

            # 2. Ghép lại toàn bộ các từ từ các chunk
            reconstructed_words = []
            for c in chunks:
                reconstructed_words.extend(c.chunk.split())

            original_words = text.split()
            self.assertEqual(
                reconstructed_words,
                original_words,
                f"Lệch từ giữa bản gốc và bản tái lập ở preset {preset_name}!",
            )


class TestRenderOrchestrator(unittest.TestCase):
    """Kiểm tra bộ điều phối Render và cơ chế tự động chia nhỏ khi lỗi (Bước 7)."""

    def setUp(self):
        self.chunker = AdaptiveChunker()

    def test_successful_render(self):
        """Tất cả chunk đều render thành công."""
        def mock_tts(text: str) -> str:
            return f"audio_of({len(text)}_chars)"

        orchestrator = RenderOrchestrator(renderer=mock_tts, chunker=self.chunker)
        text = "Câu thứ nhất rất ngắn. Câu thứ hai cũng rất ngắn."
        results = orchestrator.orchestrate(text, preset=PRESET_SMALL)

        self.assertGreater(len(results), 0)
        for r in results:
            self.assertTrue(r.success)
            self.assertEqual(r.retry_count, 0)
            self.assertIsNotNone(r.output)

    def test_adaptive_retry_on_failure(self):
        """Giả lập: Chunk dài trên 100 ký tự sẽ bị OOM/Lỗi; Chunker phải tự chia nhỏ và thành công."""
        def mock_tts_with_limit(text: str) -> str:
            if len(text) > 100:
                raise RuntimeError(f"OOM: Đoạn văn quá dài ({len(text)} ký tự > 100)!")
            return f"audio_success_{len(text)}"

        orchestrator = RenderOrchestrator(
            renderer=mock_tts_with_limit,
            chunker=self.chunker,
            max_subchunk_retries=2,
        )

        # Đoạn văn ~160 ký tự, khi chạy preset Small (target 256) sẽ tạo ra 1 chunk ~160 ký tự
        # Chunk này sẽ bị mock_tts báo lỗi -> Orchestrator tự hạ preset để chia nhỏ thành 2 sub-chunk < 100 ký tự
        text = (
            "An toàn lao động là một trong những yêu cầu bắt buộc. "
            "Người lao động cần tuân thủ nghiêm ngặt các quy tắc bảo hộ."
        )

        results = orchestrator.orchestrate(text, preset=PRESET_SMALL)
        self.assertEqual(len(results), 1)

        parent_result = results[0]
        # Kết quả tổng quát phải thành công nhờ cơ chế sub-chunking
        self.assertTrue(parent_result.success)
        self.assertGreater(parent_result.retry_count, 0)
        self.assertGreater(len(parent_result.sub_chunks), 1)

        # Tất cả các sub-chunks đều phải render thành công
        for sc in parent_result.sub_chunks:
            self.assertTrue(sc.success)
            self.assertLessEqual(len(sc.text), 100)

    def test_unrecoverable_failure(self):
        """Giả lập: Hàm render luôn luôn lỗi (VD hỏng phần cứng) -> Báo lỗi sạch sẽ, không crash."""
        def broken_tts(text: str):
            raise ConnectionError("Không thể kết nối đến TTS Engine")

        orchestrator = RenderOrchestrator(
            renderer=broken_tts,
            chunker=self.chunker,
            max_subchunk_retries=2,
        )

        text = "Văn bản thử nghiệm lỗi."
        results = orchestrator.orchestrate(text, preset=PRESET_SMALL)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn("Không thể kết nối", results[0].error)


if __name__ == "__main__":
    unittest.main(verbosity=2)
