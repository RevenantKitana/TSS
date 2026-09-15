"""Backend for the Gradio demo: voice packs, long-form chunking, and streamed
generation. Kept UI-framework-agnostic so app.py just calls into here.

Speaker conditioning is a precomputed voice pack's latents, or the model's
learned unconditional prefix. There is no cloning — see zerotts.voices.
"""

from __future__ import annotations

import json
import os
import re
import time

import numpy as np
import soundfile as sf

from zerotts import ZeroTTS
from zerotts.chunking import (
    chunk_text,
    clean_segment_punctuation,
    load_text_samples,
    normalize_punctuation,
)
from zerotts.text_norm import normalize_vi_text

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

DEFAULT_MODEL = os.environ.get("ZEROTTS_MODEL", "zeroweight-ai/ZeroTTS")
GENERATED_DIR = os.path.join(_ROOT, "outputs", "generated")
SAMPLE_TEXTS_PATH = os.path.join(_HERE, "test_samples.txt")
MAX_TEXT_CHARS = 5000

# Frames of canonical silence appended after every text segment during streaming
# generation, so the codec's causal decoder (and the listener) gets a clean
# breath between segments instead of one butting against the next.
SILENCE_FRAMES_PER_CHUNK = 4

os.makedirs(GENERATED_DIR, exist_ok=True)

_tts: ZeroTTS | None = None
_silence_frame: np.ndarray | None = None
_model_id = DEFAULT_MODEL


def set_model(model_id: str) -> None:
    global _model_id
    _model_id = model_id


def get_tts() -> ZeroTTS:
    global _tts
    if _tts is None:
        print(f"Loading ZeroTTS from {_model_id} ...")
        _tts = ZeroTTS.from_pretrained(_model_id)
    return _tts


def get_sample_rate() -> int:
    """Output sample rate. Loads the model on first call (which generation would
    do a moment later anyway) — the streaming player needs it to write its WAV
    header before the first chunk exists."""
    return int(get_tts().sample_rate)


def _get_silence_frame(tts: ZeroTTS) -> np.ndarray:
    """The codec's canonical silence RVQ frame, (1, num_codebooks) int64.

    Shipped as silence_frame.npy rather than derived here: deriving it means
    encoding digital silence and taking the per-codebook mode, which needs the
    codec ENCODER — deliberately not part of this release. It is precomputed at
    build time from the same codec weights.

    Older model directories may predate the file; falling back to zeros is wrong
    (code 0 is a real code, not silence) and would inject a burst of noise
    between segments, so we skip the padding entirely instead.
    """
    global _silence_frame
    if _silence_frame is None:
        path = tts.model_dir / "silence_frame.npy"
        if not path.exists():
            return None  # caller skips inter-segment padding
        _silence_frame = np.load(path).astype(np.int64).reshape(1, -1)
    return _silence_frame


# ── voices ───────────────────────────────────────────────────────────────────

def list_voices() -> list:
    try:
        return get_tts().list_voices()
    except Exception:
        return []


def _load_voices() -> list:
    """Every voice pack, loaded once, silently dropping ones that fail — a
    single bad pack must not take the whole picker down."""
    tts = get_tts()
    out = []
    for name in list_voices():
        try:
            out.append(tts.load_voice(name))
        except Exception:
            continue
    return out


def voice_choices(selected_tags=None) -> list:
    """(label, name) pairs for the dropdown, optionally filtered to voices that
    carry at least one of ``selected_tags``. Label leads with the human name
    and lists the tags, so the picker itself doubles as the tag legend —
    `docs/VOICES.md#built-in-voices` has the same table for reference."""
    selected = set(selected_tags or [])
    choices = []
    for v in _load_voices():
        if selected and not (selected & set(v.tags)):
            continue
        label = v.display_name or v.name
        if v.tags:
            label = f"{label} — {', '.join(v.tags)}"
        choices.append((label, v.name))
    return choices


def voice_preview_path(name: str) -> str | None:
    """Path to a voice's preview wav, or None. Never raises — the UI calls this
    on every dropdown change, and a missing preview is not an error."""
    if not name:
        return None
    try:
        voice = get_tts().load_voice(name)
    except Exception:
        return None
    path = voice.preview_path
    return path if path and os.path.isfile(path) else None


def voice_display_name(name: str) -> str:
    """Human label for a voice id, falling back to the id itself. Used by the
    history list, whose rows carry the id from the sidecar json."""
    if not name:
        return ""
    try:
        v = get_tts().load_voice(name)
    except Exception:
        return name
    return v.display_name or v.name


def voice_info(name: str) -> str:
    if not name:
        return ""
    try:
        v = get_tts().load_voice(name)
    except Exception as exc:
        return f"Could not load voice: {exc}"
    # description is just ", ".join(tags) for the shipped presets (see
    # scripts/build_voice_packs.py), so showing it AND the tag chips below
    # would repeat the same words twice — the chips are the tag display here.
    bits = [f"**{v.display_name or v.name}**", f"`{v.name}`", v.language]
    if v.description and v.description != ", ".join(v.tags):
        bits.append(v.description)
    line = " · ".join(bits)
    if v.tags:
        line += "\n\n" + " ".join(f"`{t}`" for t in v.tags)
    return line


# ── history ──────────────────────────────────────────────────────────────────

def list_generated() -> list:
    """Newest-first list of saved generated-audio paths."""
    if not os.path.isdir(GENERATED_DIR):
        return []
    files = [os.path.join(GENERATED_DIR, f)
             for f in os.listdir(GENERATED_DIR) if f.endswith(".wav")]
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def generated_meta(path: str) -> dict:
    """What the history list shows for one saved file: voice, spoken text and
    duration, from the sidecar .json generate_stream writes next to the wav.

    Every field degrades to something displayable — a history entry whose
    sidecar is missing, truncated or hand-deleted must still render as a row,
    not take the whole panel down.
    """
    meta = {}
    try:
        with open(path + ".json", encoding="utf-8") as f:
            meta = json.load(f)
    except Exception:
        pass

    when = str(meta.get("created_at") or "")
    if len(when) == 15 and when[8] == "_":  # 20260817_143002
        when = f"{when[9:11]}:{when[11:13]}:{when[13:15]} · {when[6:8]}/{when[4:6]}"
    else:
        when = time.strftime("%H:%M:%S · %d/%m", time.localtime(os.path.getmtime(path)))

    try:
        info = sf.info(path)
        seconds = info.frames / float(info.samplerate or 1)
    except Exception:
        seconds = 0.0

    return {
        "path": path,
        "voice": meta.get("voice") or "không giọng",
        "text": (meta.get("text") or os.path.basename(path)).strip(),
        "when": when,
        "seconds": seconds,
    }


# ── text ─────────────────────────────────────────────────────────────────────

def get_sample_texts() -> dict:
    """{name: text} from webui/test_samples.txt — hand-edited, so re-read every
    call rather than cached."""
    return load_text_samples(SAMPLE_TEXTS_PATH)


def get_text_segments(text: str, max_chunk_sec: float = 15.0,
                      normalize_numbers: bool = True) -> list:
    """Exactly the segments generate_stream will synthesize, after Vietnamese
    text normalization, chunking and per-segment punctuation cleanup — exposed
    so the UI can show what will actually be spoken before generation starts.

    ``normalize_numbers`` runs zerotts.text_norm.normalize_vi_text first,
    turning dates, clock times, versions, fractions, acronyms and numbers into
    spoken Vietnamese. It runs BEFORE chunking because an expansion is several
    times longer than what it replaces, and the chunk budget has to size the
    text the model actually receives.

    Turn it off for non-Vietnamese text: the expansions are Vietnamese words, so
    "3/4" in an English sentence would come out "ba trên bốn".
    """
    if normalize_numbers:
        text = normalize_vi_text(text)
    raw = chunk_text(normalize_punctuation(text), max_chunk_sec=max_chunk_sec)
    return [c for c in (clean_segment_punctuation(x) for x in raw) if c]


# ── generation ───────────────────────────────────────────────────────────────

def generate_stream(
    text: str,
    voice_name: str | None,
    max_chunk_sec: float = 15.0,
    cfg_scale: float = 1.0,
    audio_temperature: float = 0.8,
    audio_topk: int = 25,
    audio_topp: float = 0.95,
    audio_repetition_penalty: float = 1.2,
    min_frames: int = 4,
    max_frames: int = 1500,
    max_chunk_frames: int = 16,
    eoa_extra_frames: int = 1,
    use_voice: bool = True,
    normalize_numbers: bool = True,
    result: dict | None = None,
):
    """Generator yielding (sample_rate, int16 ndarray) chunks for streaming.

    The text is punctuation-normalized and sentence-chunked into segments, and
    each segment is its own generate call — the architecture re-primes the
    global transformer's [voice | soa] prefix fresh per call.

    But the CODEC is a single continuous streaming session shared across ALL
    segments: one streaming decoder is opened up front and every segment's frames
    go through it, so the causal audio decoder's KV cache never resets and there
    is no cold-start discontinuity at a segment boundary. Getting this wrong —
    one decoder per segment — is audible as a click between segments.

    The chunk-size ramp (1, 2, 4 … frames per decode call) only buys
    time-to-first-audio, which only matters once, so it applies to the first
    segment only; later segments decode straight at ``max_chunk_frames``.

    On completion (including when the caller stops iterating early) the full
    audio is saved under GENERATED_DIR; pass a ``result`` dict to read back
    "path" and "n_samples" afterwards, since a generator cannot return a value
    through a plain for-loop.
    """
    if not text or not text.strip():
        raise ValueError("Please enter some text to synthesize.")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"Text is too long ({len(text)} chars) — max {MAX_TEXT_CHARS}.")

    tts = get_tts()
    voice_emb = None
    if use_voice:
        if not voice_name:
            raise ValueError("Please select a voice first.")
        voice_emb = tts.resolve_voice(voice_name)
    else:
        # Guiding away from the unconditional branch when the conditional branch
        # IS the unconditional branch is a no-op that costs twice as much.
        cfg_scale = 1.0

    segments = get_text_segments(text, max_chunk_sec=max_chunk_sec,
                                 normalize_numbers=normalize_numbers)
    silence_frame = _get_silence_frame(tts)

    stream = tts.codec.streaming_decoder()
    all_chunks: list = []

    def _emit(frames: list):
        codes = np.stack(frames, axis=-1)          # (1, num_codebooks, n)
        arr = np.asarray(stream.decode_chunk(codes)).squeeze(0)
        all_chunks.append(arr)
        return np.clip(arr * 32767.0, -32768, 32767).astype(np.int16)

    try:
        for seg_idx, segment in enumerate(segments):
            target = 1 if seg_idx == 0 else max_chunk_frames  # ramp on the first only
            buf: list = []
            for frame_codes in tts._generate_frames(
                segment, min_frames, max_frames,
                voice_emb=voice_emb, cfg_scale=cfg_scale,
                audio_temperature=audio_temperature, audio_topk=audio_topk,
                audio_topp=audio_topp,
                audio_repetition_penalty=audio_repetition_penalty,
                eoa_extra_frames=eoa_extra_frames,
            ):
                buf.append(frame_codes)
                if len(buf) >= target:
                    chunk = _emit(buf)
                    buf = []
                    if seg_idx == 0:
                        target = min(max_chunk_frames, target * 2)
                    yield tts.sample_rate, chunk
            if buf:
                yield tts.sample_rate, _emit(buf)
            if silence_frame is not None:
                yield tts.sample_rate, _emit([silence_frame] * SILENCE_FRAMES_PER_CHUNK)
    finally:
        stream.close()
        full = np.concatenate(all_chunks) if all_chunks else np.zeros(0, dtype=np.float32)
        ts = time.strftime("%Y%m%d_%H%M%S")
        tag = voice_name if use_voice else "uncond"
        out_path = os.path.join(GENERATED_DIR, f"{ts}_{tag or 'uncond'}.wav")
        sf.write(out_path, full, tts.sample_rate, subtype="PCM_16")
        with open(out_path + ".json", "w") as f:
            json.dump({"voice": voice_name if use_voice else None,
                       "cfg_scale": cfg_scale,
                       "text": text.strip().replace("\n", " ")[:200],
                       "created_at": ts}, f, indent=2, ensure_ascii=False)
        if result is not None:
            result["path"] = out_path
            result["n_samples"] = int(full.shape[0])


def sanitize_filename(name: str) -> str:
    if not name:
        return ""
    s = re.sub(r'[\\/:*?"<>|]', '_', name.strip())
    s = re.sub(r'\s+', '_', s)
    return s.strip('_')


def parse_text_blocks(text: str) -> list[dict]:
    """Parse input text into blocks delimited by `[Tag]`.
    
    Supports:
    - Multi-line body text per block
    - Text before the first `[...]` tag gets prepended to the first block (not split into a separate block)
    - Manual skip prefixes: `#`, `!`, `skip:`, `ignore:` before or inside `[...]`
    """
    if not text or not text.strip():
        return []

    first_tag_match = re.search(r'(?:^|\n)\s*[#!]?\s*\[', text)
    prefix_text = ""
    if first_tag_match:
        start_pos = first_tag_match.start()
        if start_pos > 0:
            prefix_text = text[:start_pos].strip()
            text = text[start_pos:]
    else:
        prefix_text = text.strip()
        text = ""

    pattern = r"(?:^|\n)\s*([#!]?)\s*\[(.*?)\]\s*(.*?)(?=(?:^|\n)\s*[#!]?\s*\[|$)"
    matches = re.findall(pattern, text, flags=re.DOTALL)

    blocks = []
    if not matches:
        if prefix_text:
            blocks.append({
                "index": 1,
                "tag": "Text 1",
                "raw_tag": "[Text 1]",
                "text": prefix_text,
                "is_skipped": False
            })
        return blocks

    for i, (prefix_sym, tag_content, body_text) in enumerate(matches, start=1):
        clean_tag = tag_content.strip()
        clean_body = body_text.strip()
        
        if i == 1 and prefix_text:
            clean_body = f"{prefix_text}\n{clean_body}".strip() if clean_body else prefix_text

        is_skipped = bool(prefix_sym)
        if (clean_tag.startswith("#") or clean_tag.startswith("!") or 
            clean_tag.lower().startswith("skip:") or clean_tag.lower().startswith("ignore:")):
            is_skipped = True
            if clean_tag.startswith("#") or clean_tag.startswith("!"):
                clean_tag = clean_tag[1:].strip()
            elif clean_tag.lower().startswith("skip:"):
                clean_tag = clean_tag[5:].strip()
            elif clean_tag.lower().startswith("ignore:"):
                clean_tag = clean_tag[7:].strip()
        
        if not clean_tag:
            clean_tag = f"Text {i}"

        if clean_body or clean_tag:
            blocks.append({
                "index": i,
                "tag": clean_tag,
                "raw_tag": f"[{tag_content.strip()}]",
                "text": clean_body,
                "is_skipped": is_skipped
            })

    return blocks


def list_generated_folders() -> list[dict]:
    """Scan GENERATED_DIR for batch folders and legacy root wav files."""
    if not os.path.isdir(GENERATED_DIR):
        return []
    
    folders = []
    
    # 1. Check for subdirectories (batch runs)
    subdirs = [os.path.join(GENERATED_DIR, d) for d in os.listdir(GENERATED_DIR)
               if os.path.isdir(os.path.join(GENERATED_DIR, d))]
    
    for sdir in subdirs:
        folder_name = os.path.basename(sdir)
        info_file = os.path.join(sdir, "info.json")
        info = {}
        if os.path.isfile(info_file):
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info = json.load(f)
            except Exception:
                pass
        
        wav_files = [f for f in os.listdir(sdir) if f.endswith(".wav")]
        if not wav_files and not info:
            continue
            
        created_at = info.get("created_at") or time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(sdir)))
        voice = info.get("voice") or "không giọng"
        total_items = info.get("total_items") or len(wav_files)
        
        label = f"📁 {folder_name} ({total_items} câu) · {voice} · {created_at}"
        folders.append({
            "folder_name": folder_name,
            "folder_path": sdir,
            "label": label,
            "created_at": created_at,
            "voice": voice,
            "total_items": total_items,
            "mtime": os.path.getmtime(sdir)
        })
        
    # 2. Check for legacy single wav files at root
    root_wavs = [os.path.join(GENERATED_DIR, f) for f in os.listdir(GENERATED_DIR) if f.endswith(".wav")]
    if root_wavs:
        folders.append({
            "folder_name": "__legacy__",
            "folder_path": GENERATED_DIR,
            "label": f"📁 Mặc định (File lẻ) ({len(root_wavs)} file)",
            "created_at": "",
            "voice": "-",
            "total_items": len(root_wavs),
            "mtime": max((os.path.getmtime(f) for f in root_wavs), default=0)
        })
        
    folders.sort(key=lambda x: x["mtime"], reverse=True)
    return folders


def get_folder_files(folder_name_or_path: str) -> list[dict]:
    """Return file list items inside a batch folder."""
    if not folder_name_or_path:
        return []
    
    if folder_name_or_path == "__legacy__":
        target_dir = GENERATED_DIR
        wav_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".wav")]
        wav_files.sort(key=os.path.getmtime, reverse=True)
        items = []
        for w in wav_files:
            meta = generated_meta(w)
            items.append({
                "path": w,
                "label": f"🔊 {os.path.basename(w)} — {meta['text'][:50]}",
                "text": meta['text'],
                "voice": meta['voice']
            })
        return items
    
def get_ffmpeg_path() -> str | None:
    """Find FFmpeg binary path (prefers local ffmpeg/bin/ffmpeg.exe, then system PATH)."""
    local_ffmpeg = os.path.join(_ROOT, "ffmpeg", "bin", "ffmpeg.exe")
    if os.path.isfile(local_ffmpeg):
        return local_ffmpeg
    
    import shutil
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    return None


def get_folder_files(folder_name_or_path: str) -> list[dict]:
    """Return file list items inside a batch folder, featuring _FULL_MERGED.* at the top if present."""
    if not folder_name_or_path:
        return []
    
    if folder_name_or_path == "__legacy__":
        target_dir = GENERATED_DIR
        wav_files = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.endswith(".wav")]
        wav_files.sort(key=os.path.getmtime, reverse=True)
        items = []
        for w in wav_files:
            meta = generated_meta(w)
            items.append({
                "path": w,
                "label": f"🔊 {os.path.basename(w)} — {meta['text'][:50]}",
                "text": meta['text'],
                "voice": meta['voice']
            })
        return items
    
    target_dir = folder_name_or_path
    if not os.path.isabs(target_dir):
        target_dir = os.path.join(GENERATED_DIR, folder_name_or_path)
        
    if not os.path.isdir(target_dir):
        return []
        
    info_file = os.path.join(target_dir, "info.json")
    info = {}
    if os.path.isfile(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                info = json.load(f)
        except Exception:
            pass
            
    items_info = {it.get("file"): it for it in info.get("items", [])} if info else {}
    
    all_files = os.listdir(target_dir)
    folder_name = os.path.basename(target_dir)
    
    merged_file = None
    for f in all_files:
        if f.startswith(f"{folder_name}_FULL_MERGED."):
            merged_file = f
            break

    results = []
    if merged_file:
        w_path = os.path.join(target_dir, merged_file)
        results.append({
            "path": w_path,
            "label": f"⭐ [TỆP GỘP HOÀN CHỈNH] {merged_file}",
            "text": "Tệp nối gộp toàn bộ các câu trong thư mục",
            "tag": "FULL_MERGED",
            "status": "MERGED"
        })

    segment_files = [f for f in all_files if f.endswith(".wav") and not "_FULL_MERGED" in f]
    segment_files.sort()
    
    for w in segment_files:
        w_path = os.path.join(target_dir, w)
        item_meta = items_info.get(w, {})
        tag = item_meta.get("tag") or os.path.splitext(w)[0]
        text_preview = item_meta.get("text") or ""
        status = item_meta.get("status") or "SUCCESS"
        
        status_symbol = "🔊" if status == "SUCCESS" else "⚠️"
        label = f"{status_symbol} [{tag}] {w} — {text_preview[:40]}"
        results.append({
            "path": w_path,
            "label": label,
            "text": text_preview,
            "tag": tag,
            "status": status
        })
        
    return results


def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 0
        secs += 1
        if secs >= 60:
            secs = 0
            mins += 1
            if mins >= 60:
                mins = 0
                hrs += 1
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{millis:03d}"


def concat_folder_audio(folder_name_or_path: str, output_format: str = "WAV (PCM)") -> str | None:
    """Concatenate segment WAV files inside a batch folder into `<folder_name>_FULL_MERGED.<ext>`.

    Supports: WAV (PCM), MP3 (320/192/128 kbps), FLAC, M4A (256 kbps), OGG (192 kbps).
    Filters out any existing `_FULL_MERGED.*` files to prevent recursion.
    """
    import subprocess
    if not folder_name_or_path or folder_name_or_path == "__legacy__":
        return None

    target_dir = folder_name_or_path
    if not os.path.isabs(target_dir):
        target_dir = os.path.join(GENERATED_DIR, folder_name_or_path)

    if not os.path.isdir(target_dir):
        return None

    folder_name = os.path.basename(target_dir)
    all_files = os.listdir(target_dir)

    segment_wavs = []
    for f in all_files:
        if not f.endswith(".wav"):
            continue
        if "_FULL_MERGED" in f or "_merged" in f.lower():
            continue
        name_without_ext = os.path.splitext(f)[0]
        match = re.search(r'_(\d+)$', name_without_ext)
        if match:
            idx = int(match.group(1))
            segment_wavs.append((idx, f))

    if len(segment_wavs) <= 1:
        return None

    segment_wavs.sort(key=lambda x: x[0])

    audio_data_list = []
    sr = None
    for idx, fname in segment_wavs:
        fpath = os.path.join(target_dir, fname)
        try:
            data, sample_rate = sf.read(fpath, dtype="float32")
            if sr is None:
                sr = sample_rate
            audio_data_list.append(data)
        except Exception as exc:
            print(f"Lỗi đọc file {fname} khi nối audio: {exc}")

    if not audio_data_list or sr is None:
        return None

    merged_arr = np.concatenate(audio_data_list)
    dur_sec = merged_arr.shape[0] / float(sr)

    # Determine extension and encoding flags
    ext = ".wav"
    ffmpeg_args = []
    fmt_lower = (output_format or "").lower()
    if "mp3" in fmt_lower:
        ext = ".mp3"
        bitrate = "320k" if "320" in fmt_lower else ("128k" if "128" in fmt_lower else "192k")
        ffmpeg_args = ["-c:a", "libmp3lame", "-b:a", bitrate]
    elif "flac" in fmt_lower:
        ext = ".flac"
        ffmpeg_args = ["-c:a", "flac"]
    elif "m4a" in fmt_lower or "aac" in fmt_lower:
        ext = ".m4a"
        ffmpeg_args = ["-c:a", "aac", "-b:a", "256k"]
    elif "ogg" in fmt_lower:
        ext = ".ogg"
        ffmpeg_args = ["-c:a", "libvorbis", "-b:a", "192k"]

    merged_filename = f"{folder_name}_FULL_MERGED{ext}"
    merged_filepath = os.path.join(target_dir, merged_filename)

    ffmpeg_exe = get_ffmpeg_path()
    if ext == ".wav" or not ffmpeg_exe or not ffmpeg_args:
        sf.write(merged_filepath, merged_arr, sr, subtype="PCM_16")
    else:
        temp_wav = os.path.join(target_dir, f"_temp_concat_{int(time.time())}.wav")
        sf.write(temp_wav, merged_arr, sr, subtype="PCM_16")
        
        cmd = [ffmpeg_exe, "-y", "-i", temp_wav] + ffmpeg_args + [merged_filepath]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except Exception as exc:
            print(f"Lỗi mã hóa FFmpeg sang {ext}: {exc}. Fallback lưu file WAV.")
            merged_filename = f"{folder_name}_FULL_MERGED.wav"
            merged_filepath = os.path.join(target_dir, merged_filename)
            sf.write(merged_filepath, merged_arr, sr, subtype="PCM_16")
        finally:
            if os.path.isfile(temp_wav):
                try:
                    os.remove(temp_wav)
                except Exception:
                    pass

    info_file = os.path.join(target_dir, "info.json")
    info = {}
    if os.path.isfile(info_file):
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                info = json.load(f)
        except Exception:
            pass

    info["merged_file"] = merged_filename
    info["merged_format"] = output_format
    info["merged_duration_sec"] = round(dur_sec, 3)
    info["merged_timestamp"] = format_timestamp(dur_sec)

    with open(info_file, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    return merged_filepath



def generate_batch_stream(
    text: str,
    voice_name: str | None,
    custom_name: str = "",
    overwrite_mode: str = "Ghi đè tất cả (Overwrite All)",
    auto_concat: bool = True,
    merged_format: str = "WAV (PCM)",
    max_chunk_sec: float = 15.0,
    cfg_scale: float = 1.0,
    audio_temperature: float = 0.8,
    audio_topk: int = 25,
    audio_topp: float = 0.95,
    audio_repetition_penalty: float = 1.2,
    eoa_extra_frames: int = 1,
    use_voice: bool = True,
    result: dict | None = None,
):
    """Batch generator processing blocks `[Tag]` into separate WAV files in a custom folder.

    Yields: (status_text, last_completed_file, segments_box_text)
    """
    blocks = parse_text_blocks(text)
    if not blocks:
        raise ValueError("Vui lòng nhập văn bản để tổng hợp.")

    is_single = len(blocks) <= 1
    custom_tag = sanitize_filename(custom_name)
    ts_now = time.strftime("%Y%m%d_%H%M%S")

    if is_single:
        out_dir = GENERATED_DIR
        tag_name_clean = sanitize_filename(voice_name or "uncond")
        folder_tag = custom_tag if custom_tag else f"{ts_now}_{tag_name_clean}"
    else:
        folder_tag = custom_tag if custom_tag else f"batch_{ts_now}"
        out_dir = os.path.join(GENERATED_DIR, folder_tag)
        os.makedirs(out_dir, exist_ok=True)

    tts = get_tts()
    voice_emb = None
    if use_voice:
        if not voice_name:
            raise ValueError("Hãy chọn một giọng đọc trước.")
        voice_emb = tts.resolve_voice(voice_name)
    else:
        cfg_scale = 1.0

    silence_frame = _get_silence_frame(tts)
    skip_existing = "Skip Existing" in overwrite_mode or "Bỏ qua file" in overwrite_mode

    items_meta = []
    mapping_lines = []

    last_saved_path = None
    total_samples_all = 0
    current_timeline_sec = 0.0

    for idx, b in enumerate(blocks, start=1):
        tag_name = b["tag"]
        block_text = b["text"]
        raw_tag = b["raw_tag"]
        if is_single:
            file_name = f"{folder_tag}.wav"
        else:
            file_name = f"{folder_tag}_{idx:02d}.wav"
        file_path = os.path.join(out_dir, file_name)

        if b["is_skipped"]:
            start_ts = format_timestamp(current_timeline_sec)
            items_meta.append({
                "index": idx, "file": file_name, "tag": tag_name,
                "start_sec": round(current_timeline_sec, 3),
                "end_sec": round(current_timeline_sec, 3),
                "duration_sec": 0.0,
                "start_timestamp": start_ts,
                "end_timestamp": start_ts,
                "text": block_text[:100], "status": "SKIPPED"
            })
            mapping_lines.append(f"[{file_name}] [{start_ts} -> {start_ts}] {raw_tag} [SKIPPED]")
            yield f"Đang xử lý [{idx}/{len(blocks)}]: Bỏ qua {raw_tag} (Manual Skip)...", None, "\n".join(f"[{b['tag']}] (Skipped)" for b in blocks)
            continue

        if skip_existing and os.path.isfile(file_path):
            dur_sec = 0.0
            try:
                f_info = sf.info(file_path)
                dur_sec = f_info.frames / float(f_info.samplerate or 1)
            except Exception:
                dur_sec = 0.0
            
            start_ts = format_timestamp(current_timeline_sec)
            end_ts = format_timestamp(current_timeline_sec + dur_sec)

            items_meta.append({
                "index": idx, "file": file_name, "tag": tag_name,
                "start_sec": round(current_timeline_sec, 3),
                "end_sec": round(current_timeline_sec + dur_sec, 3),
                "duration_sec": round(dur_sec, 3),
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "text": block_text[:100], "status": "EXISTS"
            })
            mapping_lines.append(f"[{file_name}] [{start_ts} -> {end_ts}] {raw_tag}")
            last_saved_path = file_path
            current_timeline_sec += dur_sec
            yield f"Đang xử lý [{idx}/{len(blocks)}]: Bỏ qua {raw_tag} (Tệp đã tồn tại)...", file_path, "\n".join(f"[{b['tag']}] (Exists)" for b in blocks)
            continue

        if not block_text.strip():
            items_meta.append({
                "index": idx, "file": file_name, "tag": tag_name,
                "text": "", "status": "EMPTY"
            })
            continue

        segments = get_text_segments(block_text, max_chunk_sec=max_chunk_sec)
        segments_text = "\n".join(f"[{i + 1}] {s}" for i, s in enumerate(segments))

        yield f"Đang tạo [{idx}/{len(blocks)}] ({raw_tag})...", None, segments_text

        stream = tts.codec.streaming_decoder()
        all_chunks = []
        try:
            for seg_idx, segment in enumerate(segments):
                target = 1 if seg_idx == 0 else 16
                buf = []
                for frame_codes in tts._generate_frames(
                    segment, min_frames=4, max_frames=1500,
                    voice_emb=voice_emb, cfg_scale=cfg_scale,
                    audio_temperature=audio_temperature, audio_topk=int(audio_topk),
                    audio_topp=audio_topp, audio_repetition_penalty=audio_repetition_penalty,
                    eoa_extra_frames=int(eoa_extra_frames),
                ):
                    buf.append(frame_codes)
                    if len(buf) >= target:
                        codes = np.stack(buf, axis=-1)
                        arr = np.asarray(stream.decode_chunk(codes)).squeeze(0)
                        all_chunks.append(arr)
                        buf = []
                        if seg_idx == 0:
                            target = min(16, target * 2)
                        yield f"Đang tạo [{idx}/{len(blocks)}] ({raw_tag})...", None, segments_text
                if buf:
                    codes = np.stack(buf, axis=-1)
                    arr = np.asarray(stream.decode_chunk(codes)).squeeze(0)
                    all_chunks.append(arr)
                if silence_frame is not None:
                    codes = np.stack([silence_frame] * SILENCE_FRAMES_PER_CHUNK, axis=-1)
                    arr = np.asarray(stream.decode_chunk(codes)).squeeze(0)
                    all_chunks.append(arr)

            full = np.concatenate(all_chunks) if all_chunks else np.zeros(0, dtype=np.float32)
            sf.write(file_path, full, tts.sample_rate, subtype="PCM_16")

            dur_sec = full.shape[0] / float(tts.sample_rate or 1)
            start_ts = format_timestamp(current_timeline_sec)
            end_ts = format_timestamp(current_timeline_sec + dur_sec)

            with open(file_path + ".json", "w", encoding="utf-8") as f:
                json.dump({"voice": voice_name if use_voice else None,
                           "cfg_scale": cfg_scale,
                           "text": block_text.strip().replace("\n", " ")[:200],
                           "created_at": ts_now,
                           "duration_sec": dur_sec,
                           "start_timestamp": start_ts,
                           "end_timestamp": end_ts}, f, indent=2, ensure_ascii=False)

            items_meta.append({
                "index": idx, "file": file_name, "tag": tag_name,
                "start_sec": round(current_timeline_sec, 3),
                "end_sec": round(current_timeline_sec + dur_sec, 3),
                "duration_sec": round(dur_sec, 3),
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "text": block_text.strip().replace("\n", " ")[:100],
                "status": "SUCCESS"
            })
            mapping_lines.append(f"[{file_name}] [{start_ts} -> {end_ts}] {raw_tag}")
            last_saved_path = file_path
            total_samples_all += int(full.shape[0])
            current_timeline_sec += dur_sec

        except Exception as exc:
            start_ts = format_timestamp(current_timeline_sec)
            items_meta.append({
                "index": idx, "file": file_name, "tag": tag_name,
                "start_sec": round(current_timeline_sec, 3),
                "end_sec": round(current_timeline_sec, 3),
                "duration_sec": 0.0,
                "start_timestamp": start_ts,
                "end_timestamp": start_ts,
                "text": block_text[:100], "status": f"FAILED: {exc}"
            })
            mapping_lines.append(f"[{file_name}] [{start_ts} -> {start_ts}] {raw_tag} [FAILED]")
            yield f"Lỗi ở [{idx}/{len(blocks)}] ({raw_tag}): {exc}", last_saved_path, segments_text
        finally:
            stream.close()

    if not is_single:
        mapping_path = os.path.join(out_dir, f"{folder_tag}_mapping.txt")
        with open(mapping_path, "w", encoding="utf-8") as f:
            f.write("\n".join(mapping_lines))

        info_path = os.path.join(out_dir, "info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump({
                "folder_name": folder_tag,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "voice": voice_name if use_voice else "không giọng",
                "total_items": len(blocks),
                "total_duration_sec": round(current_timeline_sec, 3),
                "total_duration_timestamp": format_timestamp(current_timeline_sec),
                "items": items_meta
            }, f, indent=2, ensure_ascii=False)

    merged_path = None
    if auto_concat and not is_single:
        valid_wavs = [f for f in os.listdir(out_dir) if f.endswith(".wav") and not "_FULL_MERGED" in f and not "_merged" in f.lower()]
        if len(valid_wavs) > 1:
            yield f"Đang tiến hành nối tất cả các tệp audio trong batch thành {merged_format}...", last_saved_path, "Đang nối..."
            merged_path = concat_folder_audio(out_dir, output_format=merged_format)
            if merged_path:
                last_saved_path = merged_path

    if result is not None:
        result["folder_path"] = out_dir
        result["last_saved"] = last_saved_path
        if merged_path:
            result["merged_path"] = merged_path

    folder_disp = "Thư mục gốc (Mặc định)" if is_single else out_dir
    status_msg = f"Xong toàn bộ batch — Tổng thời lượng: {format_timestamp(current_timeline_sec)} — đã lưu vào {folder_disp}"
    if merged_path:
        status_msg += f"\n⭐ Đã tự động tạo tệp gộp ({merged_format}): {os.path.basename(merged_path)}"

    yield status_msg, last_saved_path, "Đã hoàn thành."




