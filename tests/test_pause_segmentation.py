"""Unit tests for pause markdown syntax parser and generation planning."""

from __future__ import annotations

import sys
import os

# Add src and webui to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "webui"))

from zerotts.chunking import extract_pause_segments
from engine import get_generation_plan, get_text_segments


def test_extract_pause_segments_basic():
    text = "Xin chào các bạn. [pause: 2s] Hôm nay trời rất đẹp."
    res = extract_pause_segments(text)
    assert len(res) == 3
    assert res[0] == {"type": "speech", "text": "Xin chào các bạn."}
    assert res[1] == {"type": "pause", "duration_sec": 2.0, "raw_tag": "[pause: 2s]"}
    assert res[2] == {"type": "speech", "text": "Hôm nay trời rất đẹp."}


def test_extract_pause_segments_various_formats():
    # Milliseconds, decimal seconds, case variations, <2s>, [wait: 1s], <break time="500ms"/>
    text = "Đoạn 1 [PAUSE: 500ms] Đoạn 2 <1.5s> Đoạn 3 [wait: 3s] Đoạn 4 <break time='200ms'/> Đoạn 5"
    res = extract_pause_segments(text)
    assert len(res) == 9

    assert res[0]["text"] == "Đoạn 1"
    assert res[1] == {"type": "pause", "duration_sec": 0.5, "raw_tag": "[PAUSE: 500ms]"}

    assert res[2]["text"] == "Đoạn 2"
    assert res[3] == {"type": "pause", "duration_sec": 1.5, "raw_tag": "<1.5s>"}

    assert res[4]["text"] == "Đoạn 3"
    assert res[5] == {"type": "pause", "duration_sec": 3.0, "raw_tag": "[wait: 3s]"}

    assert res[6]["text"] == "Đoạn 4"
    assert res[7] == {"type": "pause", "duration_sec": 0.2, "raw_tag": "<break time='200ms'/>"}

    assert res[8]["text"] == "Đoạn 5"


def test_extract_pause_segments_empty_or_no_pause():
    assert extract_pause_segments("") == []
    assert extract_pause_segments("   ") == []

    plain = "Văn bản không có thẻ pause nào."
    res = extract_pause_segments(plain)
    assert len(res) == 1
    assert res[0] == {"type": "speech", "text": plain}


def test_get_generation_plan():
    text = "Chào bạn! [pause: 2s] Chúng ta bắt đầu nhé."
    plan = get_generation_plan(text, max_chunk_sec=15.0, normalize_numbers=True)

    assert len(plan) == 3
    assert plan[0]["type"] == "speech"
    assert "Chào bạn" in plan[0]["text"]
    assert plan[1] == {"type": "pause", "duration_sec": 2.0, "raw_tag": "[pause: 2s]"}
    assert plan[2]["type"] == "speech"
    assert "bắt đầu" in plan[2]["text"]


def test_get_text_segments_preview():
    text = "Câu một. [pause: 1.5s] Câu hai."
    preview = get_text_segments(text, max_chunk_sec=15.0)
    assert len(preview) == 3
    assert "Câu một" in preview[0]
    assert "⏸️ [Tạm dừng 1.5s]" in preview[1]
    assert "Câu hai" in preview[2]


if __name__ == "__main__":
    test_extract_pause_segments_basic()
    test_extract_pause_segments_various_formats()
    test_extract_pause_segments_empty_or_no_pause()
    test_get_generation_plan()
    test_get_text_segments_preview()
    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")
