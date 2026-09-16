"""FastAPI Server for ZeroTTS Pure HTML/CSS/JS Web UI.
Runs without Node.js — fully self-contained with Python.

Usage:
    python webui/server.py --model ./ZeroTTS_model --port 7860
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio_stream  # noqa: E402
import engine  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_HERE, "static")
os.makedirs(_STATIC_DIR, exist_ok=True)

app = FastAPI(title="ZeroTTS Studio Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount gapless live audio streaming route (/zerotts/stream/{sid}.wav)
audio_stream.mount(app)


# ── Request / Response Models ────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    text: str = Field(..., max_length=engine.MAX_TEXT_CHARS)
    voice_name: str | None = None
    mode: str = "voice"  # "voice" or "uncond"
    custom_name: str = ""
    overwrite_mode: str = "Ghi đè tất cả (Overwrite All)"
    auto_concat: bool = True
    merged_format: str = "WAV (PCM)"
    max_chunk_sec: float = 15.0
    cfg_scale: float = 1.0
    temperature: float = 0.8
    topk: int = 25
    topp: float = 0.95
    repetition_penalty: float = 1.2
    eoa_extra_frames: int = 1


class ConcatRequest(BaseModel):
    folder_name: str
    merged_format: str = "WAV (PCM)"


class OpenFolderRequest(BaseModel):
    folder_name_or_path: str | None = None


# ── Static & Frontend Routes ─────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(_STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="index.html not found.")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── REST API Endpoints ───────────────────────────────────────────────────────

@app.get("/api/voices")
async def get_voices():
    """Return all available voice packs with metadata and sample audio links."""
    tts = engine.get_tts()
    voices = []
    for name in engine.list_voices():
        try:
            v = tts.load_voice(name)
            has_preview = bool(v.preview_path and os.path.isfile(v.preview_path))
            voices.append({
                "id": v.name,
                "name": v.display_name or v.name,
                "tags": v.tags or [],
                "has_preview": has_preview,
                "preview_url": f"/api/voice-sample?name={urllib.parse.quote(v.name)}" if has_preview else None,
            })
        except Exception:
            continue
    return {"voices": voices, "default": voices[0]["id"] if voices else None}


@app.get("/api/voice-sample")
async def get_voice_sample(name: str = Query(...)):
    """Serve the voice sample audio file."""
    preview_path = engine.voice_preview_path(name)
    if not preview_path or not os.path.isfile(preview_path):
        raise HTTPException(status_code=404, detail="Voice sample not found.")
    return FileResponse(preview_path, media_type="audio/wav")


@app.get("/api/history/folders")
async def get_history_folders():
    """List all generated batch project folders."""
    folders = engine.list_generated_folders()
    return {"folders": folders}


@app.get("/api/history/files")
async def get_history_files(folder: str = Query(...)):
    """List audio files in a specific project folder."""
    files = engine.get_folder_files(folder)
    return {"files": files}


@app.get("/api/history/details")
async def get_history_details(folder: str = Query(None), file: str = Query(None)):
    """Parse segment and timeline info for folder / active file."""
    details = engine.parse_segment_details(folder, file)
    return {"details": details}


@app.get("/api/audio-file")
async def get_audio_file(path: str = Query(...)):
    """Serve any generated audio file from the outputs directory."""
    clean_path = os.path.abspath(path)
    # Safety check: ensure file exists
    if not os.path.isfile(clean_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")
    ext = os.path.splitext(clean_path)[1].lower()
    media_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
    }
    media_type = media_map.get(ext, "application/octet-stream")
    return FileResponse(clean_path, media_type=media_type, filename=os.path.basename(clean_path))


@app.post("/api/open-folder")
async def api_open_folder(req: OpenFolderRequest):
    """Open a folder in Windows Explorer."""
    msg = engine.open_folder(req.folder_name_or_path)
    return {"status": msg}


@app.post("/api/concat")
async def api_concat(req: ConcatRequest):
    """Concatenate segment files in a folder into a single merged audio."""
    merged_path = engine.concat_folder_audio(req.folder_name, output_format=req.merged_format)
    if not merged_path:
        raise HTTPException(status_code=400, detail="Không thể nối audio (không đủ tệp hoặc lỗi ffmpeg).")
    
    files = engine.get_folder_files(req.folder_name)
    details = engine.parse_segment_details(req.folder_name, merged_path)
    return {
        "success": True,
        "merged_path": merged_path,
        "file_name": os.path.basename(merged_path),
        "file_url": f"/api/audio-file?path={urllib.parse.quote(merged_path)}",
        "files": files,
        "details": details,
        "message": f"Đã nối thành công: {os.path.basename(merged_path)}",
    }


# ── Server-Sent Events (SSE) Generation Endpoint ─────────────────────────────

@app.post("/api/generate")
async def generate_tts(req: GenerateRequest):
    """Stream synthesis progress & live audio stream via Server-Sent Events (SSE)."""
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Vui lòng nhập văn bản cần chuyển đổi.")
    if len(text) > engine.MAX_TEXT_CHARS:
        raise HTTPException(status_code=400, detail=f"Văn bản quá dài ({len(text)} ký tự, tối đa {engine.MAX_TEXT_CHARS}).")

    use_voice = req.mode == "voice"
    if use_voice and not req.voice_name:
        raise HTTPException(status_code=400, detail="Vui lòng chọn một giọng đọc trước.")

    async def event_generator() -> AsyncGenerator[str, None]:
        result_container: dict = {}
        last_file = None
        
        # Start SSE stream
        yield f"event: start\ndata: {json.dumps({'message': 'Bắt đầu quá trình tạo giọng...'})}\n\n"

        def _sync_generator():
            return engine.generate_batch_stream(
                text=text,
                voice_name=req.voice_name,
                custom_name=req.custom_name,
                overwrite_mode=req.overwrite_mode,
                auto_concat=req.auto_concat,
                merged_format=req.merged_format,
                max_chunk_sec=req.max_chunk_sec,
                cfg_scale=float(req.cfg_scale),
                audio_temperature=float(req.temperature),
                audio_topk=int(req.topk),
                audio_topp=float(req.topp),
                audio_repetition_penalty=float(req.repetition_penalty),
                eoa_extra_frames=int(req.eoa_extra_frames),
                use_voice=use_voice,
                result=result_container,
            )

        loop = asyncio.get_event_loop()
        gen = _sync_generator()

        try:
            while True:
                # Run generator step in threadpool so we don't block the async event loop
                try:
                    item = await loop.run_in_executor(None, lambda: next(gen))
                except StopIteration:
                    break

                status_msg, completed_file, segs_text = item
                if completed_file:
                    last_file = completed_file

                payload = {
                    "status": status_msg,
                    "segments": segs_text,
                    "file_path": last_file,
                    "file_url": f"/api/audio-file?path={urllib.parse.quote(last_file)}" if last_file else None,
                    "file_name": os.path.basename(last_file) if last_file else None,
                }
                yield f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.01)

        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
            return

        out_folder = result_container.get("folder_path", "")
        folders = engine.list_generated_folders()
        default_folder = "__legacy__" if out_folder == engine.GENERATED_DIR else (folders[0]["folder_name"] if folders else "")
        files = engine.get_folder_files(default_folder) if default_folder else []
        default_file = last_file or (files[0]["path"] if files else "")
        details = engine.parse_segment_details(out_folder, default_file)

        final_payload = {
            "status": "✅ Đã hoàn thành!",
            "folder_path": out_folder,
            "folder_name": default_folder,
            "folders": folders,
            "files": files,
            "file_path": default_file,
            "file_url": f"/api/audio-file?path={urllib.parse.quote(default_file)}" if default_file else None,
            "file_name": os.path.basename(default_file) if default_file else "",
            "details": details,
        }
        yield f"event: complete\ndata: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Mount static assets directory
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


# ── Server Launch ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ZeroTTS Studio Web Server (HTML/Vanilla JS)")
    parser.add_argument("--model", default=engine.DEFAULT_MODEL, help="Model directory or repo ID")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7860, help="Port number (default: 7860)")
    parser.add_argument("--reload", action="store_true", help="Auto reload on code change")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    engine.set_model(args.model)
    print("=" * 60)
    print("      Khởi chạy ZeroTTS Studio Web Server")
    print(f"      Địa chỉ truy cập: http://{args.host}:{args.port}")
    print("=" * 60)
    uvicorn.run(app, host=args.host, port=args.port)
