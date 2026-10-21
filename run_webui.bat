@echo off
chcp 65001 > nul
title ZeroTTS Web UI
cd /d "%~dp0"

echo ===================================================
echo           Khoi chay ZeroTTS Web UI
echo ===================================================
echo.

rem 1. Kiem tra neu .venv san co va hoat dong tot
set "PY_CMD="
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import zerotts, fastapi, uvicorn, onnxruntime" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=.venv\Scripts\python.exe"
        goto :RUN_APP
    )
)

rem 2. Neu chua co .venv hoac thieu thu vien, su dung uv de khoi tao tu dong
echo * Dang kiem tra cong cu uv va moi truong Python...

set "UV_CMD=uv"
where uv >nul 2>&1
if errorlevel 1 (
    if exist "%~dp0uv.exe" (
        set "UV_CMD=%~dp0uv.exe"
    ) else (
        echo * Chua co uv trong PATH. Dang tu dong tai uv standalone tu Astral GitHub (~12MB)...
        curl.exe -fL -o "%~dp0uv.zip" "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
        if errorlevel 1 (
            echo [LOI] Khong the tai uv.exe qua curl! Vui long kiem tra ket noi mang.
            pause
            exit /b 1
        )
        tar.exe -xf "%~dp0uv.zip" -C "%~dp0" uv.exe
        del "%~dp0uv.zip" 2>nul
        set "UV_CMD=%~dp0uv.exe"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo * Dang tu dong tai Python 3.11 Portable va khoi tao moi truong .venv qua uv...
    "%UV_CMD%" venv "%~dp0.venv" --python 3.11
    if errorlevel 1 (
        echo [LOI] Khong the tao .venv qua uv!
        pause
        exit /b 1
    )
)

echo * Dang dong bo dependencies cho ZeroTTS Web UI qua uv...
"%UV_CMD%" pip install --python "%~dp0.venv\Scripts\python.exe" -e ".[webui]"
if errorlevel 1 (
    echo [CANH BAO] Co loi khi cai dat -e .[webui]. Dang thu cai dat truc tiep...
    "%UV_CMD%" pip install --python "%~dp0.venv\Scripts\python.exe" onnxruntime fastapi uvicorn requests soundfile scipy numpy python-docx aiofiles psutil huggingface_hub
)

set "PY_CMD=.venv\Scripts\python.exe"

:RUN_APP
rem 3. Kiem tra va tai mo hinh neu chua co hoac khong hop le
set "NEED_DOWNLOAD=0"
if not exist "ZeroTTS_model" set "NEED_DOWNLOAD=1"
if not exist "ZeroTTS_model\config.json" set "NEED_DOWNLOAD=1"

if "%NEED_DOWNLOAD%"=="1" (
    echo * Khong tim thay mo hinh hoac mo hinh khong hop le trong ZeroTTS_model!
    echo * Dang tai mo hinh zeroweight-ai/ZeroTTS tu Hugging Face ve thu muc tai cho...
    echo.
    "%PY_CMD%" -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='zeroweight-ai/ZeroTTS', local_dir='./ZeroTTS_model')"
    if exist "ZeroTTS_model\.cache" rmdir /s /q "ZeroTTS_model\.cache" >nul 2>&1
    echo.
)

rem 4. Kiem tra va tai ffmpeg.exe neu chua co trong local
if not exist "ffmpeg\bin\ffmpeg.exe" (
    echo * Khong tim thay ffmpeg.exe trong ffmpeg\bin!
    echo * Dang tu dong tai ffmpeg.exe tu https://cdn.mio.io.vn/ffmpeg.exe...
    echo.
    "%PY_CMD%" -c "import os, urllib.request, shutil; os.makedirs('ffmpeg/bin', exist_ok=True); req = urllib.request.Request('https://cdn.mio.io.vn/ffmpeg.exe', headers={'User-Agent': 'Mozilla/5.0'}); print('Dang tai ffmpeg.exe (141 MB)...'); [shutil.copyfileobj(resp, f) for resp, f in [(urllib.request.urlopen(req), open('ffmpeg/bin/ffmpeg.exe.tmp', 'wb'))]]; os.replace('ffmpeg/bin/ffmpeg.exe.tmp', 'ffmpeg/bin/ffmpeg.exe'); print('Da tai thanh cong ffmpeg.exe!')"
    echo.
)

rem 5. Khoi chay Web UI hoan toan bang mo hinh local tai cho
echo * Dang mo Web UI che do Offline bang mo hinh local trong ZeroTTS_model...
echo * Dia chi truy cap: http://localhost:7860  hoac  http://127.0.0.1:7860
echo.
set "VOICE_ARG="
if exist "Voice_ZeroTTS_model\voices" (
    set "VOICE_ARG=--voices ./Voice_ZeroTTS_model/voices"
    echo * Su dung cac mau giong tu thu muc: Voice_ZeroTTS_model\voices
) else if exist "Voice_ZeroTTS_model" (
    set "VOICE_ARG=--voices ./Voice_ZeroTTS_model"
    echo * Su dung cac mau giong tu thu muc: Voice_ZeroTTS_model
)
"%PY_CMD%" webui/server.py --model ./ZeroTTS_model %VOICE_ARG%

pause
