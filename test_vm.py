import time
from zerotts import ZeroTTS

print("=" * 50)
print("🎙️ Đang nạp mô hình ZeroTTS vào RAM...")
t0 = time.time()
tts = ZeroTTS.from_pretrained("/home/ubuntu/TSS/ZeroTTS_model")
t_load = time.time() - t0
print(f"✅ Mô hình nạp xong trong {t_load:.2f}s")

text = "Xin chào! Đây là bản thử nghiệm giọng đọc chạy trực tiếp trên vi xử lý ARM64 Ampere Altra của Oracle Cloud."
print(f"\n📝 Văn bản: {text}")
print("⚡ Đang tổng hợp giọng nói (Inference)...")

t1 = time.time()
audio = tts.synthesize(text, voice="maichi")
t_synth = time.time() - t1

duration_sec = audio.shape[-1] / tts.sample_rate
rtf = t_synth / duration_sec

print("\n" + "=" * 50)
print(f"🎉 KẾT QUẢ HIỆU NĂNG SUY LUẬN (BENCHMARK):")
print(f"  • Độ dài âm thanh sinh ra: {duration_sec:.2f} giây")
print(f"  • Thời gian xử lý (CPU):   {t_synth:.2f} giây")
print(f"  • Real-Time Factor (RTF):  {rtf:.2f}x ({'Nhanh hơn thời gian thực' if rtf <= 1.0 else 'Gần thời gian thực'})")
print("=" * 50)

tts.save_audio(audio, "/home/ubuntu/TSS/test_arm.wav")
print("💾 Đã lưu file audio mẫu tại: /home/ubuntu/TSS/test_arm.wav\n")
