import json
import time
import urllib.request
import sys

print("=" * 60)
print("🔍 KIỂM TRA DANH SÁCH GIỌNG NÓI TỪ API WEB SERVICE...")
print("=" * 60)

try:
    res = urllib.request.urlopen("http://127.0.0.1:7860/api/voices")
    data = json.loads(res.read().decode("utf-8"))
    voices = data.get("voices", [])
    print(f"✅ Tổng số giọng nhận diện được: {len(voices)}")
    print(f"🎯 Giọng mặc định: {data.get('default')}")
    print(f"📂 Thư mục giọng: {data.get('voices_root')}")
    print("-" * 60)
    for v in voices:
        tags_str = ", ".join(v.get("tags", []))
        print(f"  • [{v['id']}] {v['name']} (Tags: {tags_str})")
except Exception as e:
    print(f"❌ Lỗi gọi API /api/voices: {e}")

print("\n" + "=" * 60)
print("🎙️ KIỂM TRA THỰC HIỆN TỔNG HỢP ÂM THANH VỚI GIỌNG MỚI (quynhanh)...")
print("=" * 60)

try:
    sys.path.insert(0, "/home/ubuntu/TSS/src")
    from zerotts import ZeroTTS
    
    tts = ZeroTTS.from_pretrained("/home/ubuntu/TSS/ZeroTTS_model", voices_dir="/home/ubuntu/TSS/Voice_ZeroTTS_model/voices")
    text = "Xin chào các bạn, giọng đọc Quỳnh Anh đã được tích hợp thành công vào hệ thống ZeroTTS trên máy chủ VM."
    
    t0 = time.time()
    audio = tts.synthesize(text, voice="quynhanh")
    t_synth = time.time() - t0
    dur = audio.shape[-1] / tts.sample_rate
    rtf = t_synth / dur
    
    print(f"✅ Sinh âm thanh thành công!")
    print(f"  • Độ dài audio: {dur:.2f}s")
    print(f"  • Thời gian xử lý: {t_synth:.2f}s (RTF: {rtf:.2f}x)")
    tts.save_audio(audio, "/home/ubuntu/TSS/test_quynhanh.wav")
    print("  • Đã lưu mẫu thử tại: /home/ubuntu/TSS/test_quynhanh.wav")
except Exception as e:
    print(f"❌ Lỗi tổng hợp giọng nói: {e}")

print("=" * 60)
