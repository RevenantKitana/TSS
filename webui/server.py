"""FastAPI Server for ZeroTTS Pure HTML/CSS/JS Web UI.
Runs without Node.js — fully self-contained with Python.

Usage:
    python webui/server.py --model ./ZeroTTS_model --port 7860
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in [_ROOT, os.path.join(_ROOT, "src"), _HERE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import audio_stream  # noqa: E402
import auth  # noqa: E402
import engine  # noqa: E402

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


def _get_client_ip(request: Request) -> str:
    """Extract real client IP even behind Cloudflare or Reverse Proxy."""
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def _get_session_id(request: Request) -> str:
    """Extract session ID from X-Session-ID header or query parameter."""
    return request.headers.get("X-Session-ID") or request.query_params.get("session_id") or ""


def get_auth_context(request: Request, token_param: str | None = None) -> auth.AuthContext:
    """Extract and verify token from Authorization header or param."""
    token = token_param
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            token = request.headers.get("X-API-Key") or request.query_params.get("token")
    client_ip = _get_client_ip(request)
    return auth.auth_manager.verify_token(token, client_ip=client_ip)


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
    num_workers: int = Field(1, ge=1, le=16)
    token: str | None = None
    session_id: str | None = None


class VerifyTokenRequest(BaseModel):
    token: str = ""


class ConcatRequest(BaseModel):
    folder_name: str
    merged_format: str = "WAV (PCM)"
    token: str | None = None
    session_id: str | None = None


class ParseRequest(BaseModel):
    text: str = ""

    default_name: str = ""


class UploadFileRequest(BaseModel):
    filename: str = ""
    content_base64: str = ""


class OpenFolderRequest(BaseModel):
    folder_name_or_path: str | None = None


# ── Static & Frontend Routes ─────────────────────────────────────────────────

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    return Response(
        content='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🎙️</text></svg>',
        media_type="image/svg+xml",
    )


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(_STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=404, detail="index.html not found.")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ── REST API Endpoints ───────────────────────────────────────────────────────

@app.get("/api/auth/status")
async def get_auth_status(request: Request, token: str | None = None):
    """Return user tier, limits, remaining quota, and storage space."""
    ctx = get_auth_context(request, token)
    return {
        "tier": ctx.tier,
        "name": ctx.name,
        "has_key": ctx.has_key,
        "storage_slug": ctx.storage_slug,
        "max_chars": ctx.max_chars,
        "hourly_limit": ctx.hourly_limit,
        "remaining_quota": ctx.remaining_quota,
        "is_master": ctx.has_key,
        "is_vip": ctx.has_key,
    }


@app.post("/api/auth/verify")
async def verify_auth_token(req: VerifyTokenRequest, request: Request):
    """Verify submitted Access Key."""
    token = req.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Vui lòng nhập mã Key.")
    ctx = auth.auth_manager.verify_token(token, client_ip=_get_client_ip(request))
    if not ctx.has_key:
        raise HTTPException(status_code=401, detail="Mã Key không hợp lệ hoặc đã bị khóa.")
    return {
        "success": True,
        "tier": ctx.tier,
        "name": ctx.name,
        "has_key": ctx.has_key,
        "storage_slug": ctx.storage_slug,
        "max_chars": ctx.max_chars,
        "hourly_limit": ctx.hourly_limit,
        "remaining_quota": ctx.remaining_quota,
        "is_master": True,
        "is_vip": True,
        "message": f"Xác thực thành công: {ctx.name} (Không gian riêng: outputs/keys/{ctx.storage_slug}/)."
    }


@app.get("/api/voices")
async def get_voices():
    """Return all available voice packs with metadata and sample audio links."""
    tts = engine.get_tts()
    voices = []
    for name in engine.list_voices():
        try:
            v = tts.load_voice(name)
            preview_p = engine.voice_preview_path(name)
            has_preview = bool(preview_p and os.path.isfile(preview_p))
            voices.append({
                "id": v.name,
                "name": v.display_name or v.name,
                "tags": v.tags or [],
                "has_preview": has_preview,
                "preview_url": f"/api/voice-sample?name={urllib.parse.quote(v.name)}" if has_preview else None,
                "preview_source": preview_p,
            })
        except Exception as e:
            print(f"[API] ⚠️ Error loading voice '{name}': {e}")
            continue
    default_voice = "maichi" if any(v["id"] == "maichi" for v in voices) else (voices[0]["id"] if voices else None)
    return {"voices": voices, "default": default_voice, "voices_root": str(tts.voices_root)}


@app.get("/api/voice-sample")
async def get_voice_sample(name: str = Query(...)):
    """Serve the voice sample audio file."""
    preview_path = engine.voice_preview_path(name)
    if not preview_path or not os.path.isfile(preview_path):
        raise HTTPException(status_code=404, detail="Voice sample not found.")
    print(f"[API] 🔊 Serving preview for '{name}' from: {preview_path}")
    return FileResponse(
        preview_path,
        media_type="audio/wav",
        headers={"X-Voice-Source": os.path.abspath(preview_path)}
    )


@app.get("/api/history/folders")
async def get_history_folders(request: Request, token: str | None = None, session_id: str | None = None):
    """List project folders scoped to current user session."""
    ctx = get_auth_context(request, token)
    sid = session_id or _get_session_id(request)
    user_dir = auth.resolve_output_dir(ctx, sid)
    folders = engine.list_generated_folders(base_dir=str(user_dir))
    return {"folders": folders, "tier": ctx.tier, "scoped_dir": str(user_dir)}


@app.get("/api/history/files")
async def get_history_files(request: Request, folder: str = Query(...), token: str | None = None, session_id: str | None = None):
    """List audio files in a specific project folder scoped to user."""
    ctx = get_auth_context(request, token)
    sid = session_id or _get_session_id(request)
    user_dir = auth.resolve_output_dir(ctx, sid)
    files = engine.get_folder_files(folder, base_dir=str(user_dir))
    return {"files": files}


@app.get("/api/history/details")
async def get_history_details(request: Request, folder: str = Query(None), file: str = Query(None), token: str | None = None, session_id: str | None = None):
    """Parse segment and timeline info for folder / active file scoped to user."""
    ctx = get_auth_context(request, token)
    sid = session_id or _get_session_id(request)
    user_dir = auth.resolve_output_dir(ctx, sid)
    details = engine.parse_segment_details(folder, file, base_dir=str(user_dir))
    return {"details": details}


@app.get("/api/audio-file")
async def get_audio_file(request: Request, path: str = Query(...)):
    """Serve any generated audio file from the outputs directory with path traversal protection."""
    clean_path = os.path.abspath(path)
    if not os.path.isfile(clean_path):
        raise HTTPException(status_code=404, detail="Audio file not found.")

    base_outputs = os.path.abspath(os.environ.get("ZEROTTS_OUTPUT_DIR", os.path.join(_ROOT, "outputs")))
    gen_dir = os.path.abspath(engine.GENERATED_DIR)
    voices_dir = os.path.abspath(engine._voices_dir) if engine._voices_dir else ""

    is_allowed = (
        clean_path.startswith(base_outputs)
        or clean_path.startswith(gen_dir)
        or (voices_dir and clean_path.startswith(voices_dir))
    )
    if not is_allowed:
        raise HTTPException(status_code=403, detail="Truy cập tệp âm thanh bị từ chối.")

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
async def api_open_folder(req: OpenFolderRequest, request: Request):
    """Open a folder in Windows Explorer."""
    ctx = get_auth_context(request)
    sid = _get_session_id(request)
    user_dir = auth.resolve_output_dir(ctx, sid)
    target = req.folder_name_or_path
    if not target:
        target = str(user_dir)
    msg = engine.open_folder(target)
    return {"status": msg}


@app.post("/api/concat")
async def api_concat(req: ConcatRequest, request: Request):
    """Concatenate segment files in a folder into a single merged audio."""
    ctx = get_auth_context(request, req.token)
    sid = req.session_id or _get_session_id(request)
    user_dir = auth.resolve_output_dir(ctx, sid)
    merged_path = engine.concat_folder_audio(req.folder_name, output_format=req.merged_format, base_dir=str(user_dir))
    if not merged_path:
        raise HTTPException(status_code=400, detail="Không thể nối audio (không đủ tệp hoặc lỗi ffmpeg).")
    
    files = engine.get_folder_files(req.folder_name, base_dir=str(user_dir))
    details = engine.parse_segment_details(req.folder_name, merged_path, base_dir=str(user_dir))
    return {
        "success": True,
        "merged_path": merged_path,
        "file_name": os.path.basename(merged_path),
        "file_url": f"/api/audio-file?path={urllib.parse.quote(merged_path)}",
        "files": files,
        "details": details,
        "message": f"Đã nối thành công: {os.path.basename(merged_path)}",
    }



@app.post("/api/upload-file")
async def api_upload_file(req: UploadFileRequest):
    """Read uploaded .txt or .docx file (sent as base64 in JSON) and return extracted text and project hierarchy."""
    try:
        content_bytes = base64.b64decode(req.content_base64) if req.content_base64 else b""
        extracted_text, default_name = engine.read_input_file(content_bytes, filename=req.filename or "")
        projects = engine.parse_multi_project_blocks(extracted_text, default_name=default_name)
        total_blocks = sum(len(p.get("blocks", [])) for p in projects)
        return {
            "success": True,
            "filename": req.filename,
            "default_name": default_name,
            "text": extracted_text,
            "projects": projects,
            "total_projects": len(projects),
            "total_blocks": total_blocks,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Lỗi đọc tệp: {exc}")


@app.post("/api/parse-script")
async def api_parse_script(req: ParseRequest):
    """Parse raw text script into project blocks preview."""
    projects = engine.parse_multi_project_blocks(req.text, default_name=req.default_name)
    total_blocks = sum(len(p.get("blocks", [])) for p in projects)
    return {
        "projects": projects,
        "total_projects": len(projects),
        "total_blocks": total_blocks,
    }


# ── Safe Generator Helper for ThreadPoolExecutor ────────────────────────────
_GEN_FINISHED = object()


def _safe_generator_next(gen):
    """Safely fetch next item from a generator in a ThreadPoolExecutor.
    
    Prevents StopIteration from bubbling up into asyncio.Future, which triggers:
    TypeError: StopIteration interacts badly with generators and cannot be raised into a Future
    """
    try:
        return next(gen)
    except StopIteration:
        return _GEN_FINISHED


# Fix Windows Proactor ConnectionResetError (WinError 10054) on abrupt client disconnect
if sys.platform == "win32":
    def _win32_exception_handler(loop, context):
        exc = context.get("exception")
        if isinstance(exc, ConnectionResetError) and getattr(exc, "winerror", None) == 10054:
            return  # Suppress harmless client disconnect error on Windows
        loop.default_exception_handler(context)

    @app.on_event("startup")
    async def _setup_win32_exception_handler():
        try:
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(_win32_exception_handler)
        except Exception:
            pass


@app.on_event("startup")
async def _start_background_storage_cleaner():
    async def _cleanup_loop():
        cleaner = auth.StorageCleaner()
        while True:
            try:
                cleaner.cleanup_expired()
            except Exception as exc:
                print(f"[StorageCleaner] ⚠️ Lỗi dọn dẹp bộ nhớ: {exc}")
            await asyncio.sleep(300)  # Check every 5 minutes

    asyncio.create_task(_cleanup_loop())


# ── Server-Sent Events (SSE) Generation Endpoint ─────────────────────────────

@app.post("/api/generate")
async def generate_tts(req: GenerateRequest, request: Request):
    """Stream synthesis progress & live audio stream via Server-Sent Events (SSE)."""
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Vui lòng nhập văn bản cần chuyển đổi.")

    client_ip = _get_client_ip(request)
    auth_ctx = get_auth_context(request, req.token)
    session_id = req.session_id or _get_session_id(request)
    user_output_root = auth.resolve_output_dir(auth_ctx, session_id)

    # 1. Enforce Tier Character Limits
    if len(text) > auth_ctx.max_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Văn bản ({len(text):,} ký tự) vượt quá giới hạn tài nguyên của phiên ({auth_ctx.max_chars:,} ký tự) nhằm bảo vệ CPU máy chủ khỏi quá tải. Vui lòng rút ngắn nội dung."
        )

    # 2. Enforce Hourly Rate Limits
    if auth_ctx.remaining_quota <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Hệ thống tạm khóa yêu cầu ({auth_ctx.hourly_limit} lượt/giờ) nhằm chống spam và giữ ổn định tài nguyên máy chủ. Vui lòng thử lại sau."
        )

    use_voice = req.mode == "voice"
    if use_voice and not req.voice_name:
        raise HTTPException(status_code=400, detail="Vui lòng chọn một giọng đọc trước.")

    async def event_generator() -> AsyncGenerator[str, None]:
        result_container: dict = {}
        last_file = None
        
        # Start SSE stream
        yield f"event: start\ndata: {json.dumps({'message': 'Đang kết nối tới động cơ ZeroTTS...', 'tier': auth_ctx.tier})}\n\n"

        def _sync_generator():
            return engine.generate_projects_queue_stream(
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
                num_workers=int(req.num_workers),
                result=result_container,
                output_root=str(user_output_root),
            )

        loop = asyncio.get_running_loop() if hasattr(asyncio, "get_running_loop") else asyncio.get_event_loop()

        # Guard inference with Concurrency Semaphore (1 worker on single core)
        try:
            if auth.auth_manager.inference_semaphore.locked():
                yield f"event: progress\ndata: {json.dumps({'status': '⏳ Đang trong hàng đợi xử lý CPU... Vui lòng đợi trong giây lát.', 'segments': '', 'file_path': None, 'file_url': None, 'file_name': None, 'queue': {}}, ensure_ascii=False)}\n\n"

            async with auth.auth_manager.inference_semaphore:
                gen = _sync_generator()
                while True:
                    # Run generator step safely in threadpool
                    item = await loop.run_in_executor(None, _safe_generator_next, gen)
                    if item is _GEN_FINISHED:
                        break

                    status_msg, completed_file, segs_text, queue_meta = item
                    if completed_file:
                        last_file = completed_file

                    payload = {
                        "status": status_msg,
                        "segments": segs_text,
                        "file_path": last_file,
                        "file_url": f"/api/audio-file?path={urllib.parse.quote(last_file)}" if last_file else None,
                        "file_name": os.path.basename(last_file) if last_file else None,
                        "queue": queue_meta or {},
                    }
                    yield f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)

                # Record usage upon success
                auth.auth_manager.record_usage(auth_ctx, len(text), client_ip=client_ip)

            # Build completion payload safely
            all_folders = result_container.get("folders", [])
            out_folder = result_container.get("folder_path", "")
            if not out_folder or out_folder == str(user_output_root) or out_folder == engine.GENERATED_DIR:
                default_folder = "__legacy__"
            else:
                default_folder = os.path.basename(out_folder)

            folders = engine.list_generated_folders(base_dir=str(user_output_root))
            files = engine.get_folder_files(default_folder, base_dir=str(user_output_root)) if default_folder else []
            default_file = last_file or (files[0]["path"] if files else "")
            details = engine.parse_segment_details(out_folder, default_file, base_dir=str(user_output_root))

            final_payload = {
                "status": "✅ Đã hoàn thành toàn bộ dự án!",
                "folder_path": out_folder,
                "folder_name": default_folder,
                "all_folders": [os.path.basename(f) for f in all_folders],
                "folders": folders,
                "files": files,
                "file_path": default_file,
                "file_url": f"/api/audio-file?path={urllib.parse.quote(default_file)}" if default_file else None,
                "file_name": os.path.basename(default_file) if default_file else "",
                "details": details,
            }
            yield f"event: complete\ndata: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

        except asyncio.CancelledError:
            return
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
            return

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
    parser.add_argument("--voices", default=engine.DEFAULT_VOICES, help="Voices directory (default: ./Voice_ZeroTTS_model/voices)")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7860, help="Port number (default: 7860)")
    parser.add_argument("--reload", action="store_true", help="Auto reload on code change")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    engine.set_model(args.model, voices_dir=args.voices)
    print("=" * 60)
    print("      Khởi chạy ZeroTTS Studio Web Server")
    print(f"      Địa chỉ truy cập: http://{args.host}:{args.port}")
    print("=" * 60)
    uvicorn.run(app, host=args.host, port=args.port)
