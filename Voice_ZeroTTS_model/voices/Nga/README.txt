ZeroTTS voice pack — Nga

You do not need to unzip this. Every ZeroTTS surface takes the .zip as it
is, copies what it needs out of it, and keeps the voice — so this is a
one-time step, not something to repeat each time you run it.

Gradio demo (webui/app.py)
  Voice picker → the "Nhập giọng của bạn" tab → drop this .zip on it.
      python webui/app.py --voice /path/to/Nga-QY9oBcDlg6j3ux0aQvaT.zip

Browser demo (js/)
  Same tab, same gesture. The file is read in the page — nothing is
  uploaded — and the voice is still there on your next visit.

Python
  from zerotts import ZeroTTS
  tts = ZeroTTS.from_pretrained('zeroweight-ai/ZeroTTS')
  tts.add_voices('/path/to/Nga-QY9oBcDlg6j3ux0aQvaT.zip')   # once, ever
  tts.synthesize('Xin chào.', voice='QY9oBcDlg6j3ux0aQvaT')

If you do unzip it, the folder inside is the voice pack and works the same
way — point any of the above at the folder instead:

  voice.npz    the latents, for the Python package and the Gradio demo
  voice.bin    the same latents as raw float32, for the browser demo
  preview.wav  a sample of this voice
  meta.json    the name and tags shown in a voice picker

https://github.com/zeroweight-ai/ZeroTTS
