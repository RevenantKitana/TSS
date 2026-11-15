@echo off
chcp 65001 > nul
title ZeroTTS Studio Portable
cd /d "%~dp0"

echo ===================================================
echo          Khoi chay ZeroTTS Studio (Portable)
echo ===================================================
echo.

rem 1. Uu tien tuyet doi: Python Portable noi bo ngay trong thu muc du an
set "PY_CMD="
if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" -c "import zerotts, fastapi, uvicorn, onnxruntime" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=%~dp0python\python.exe"
        echo * Phat hien moi truong Python Portable doc lap trong thu muc python\
        goto :RUN_APP
    )
)

rem 2. Kiem tra moi truong .venv (neu co)
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import zerotts, fastapi, uvicorn, onnxruntime" >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=%~dp0.venv\Scripts\python.exe"
        echo * Phat hien moi truong .venv san co va hop le
        goto :RUN_APP
    )
)

rem 3. Neu chua co moi truong nao, su dung uv de khoi tao Python Portable tai cho
echo * Chua tim thay moi truong Portable. Dang kiem tra cong cu uv...

set "UV_CMD=uv"
where uv >nul 2>&1
if not errorlevel 1 goto :SETUP_PORTABLE

if exist "%~dp0uv.exe" (
    set "UV_CMD=%~dp0uv.exe"
    goto :SETUP_PORTABLE
)

echo * Dang tu dong tai uv standalone tu Astral GitHub...
curl.exe -fL -o "%~dp0uv.zip" "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
if errorlevel 1 (
    echo [LOI] Khong the tai uv.exe qua curl! Vui long kiem tra ket noi mang.
    goto :ON_ERROR
)
tar.exe -xf "%~dp0uv.zip" -C "%~dp0" uv.exe
del "%~dp0uv.zip" 2>nul
set "UV_CMD=%~dp0uv.exe"

:SETUP_PORTABLE
echo * Dang tu dong khoi tao moi truong Python 3.11 Portable qua uv...
"%UV_CMD%" venv "%~dp0.venv" --python 3.11 --clear
if errorlevel 1 (
    echo [LOI] Khong the tao moi truong Python qua uv!
    goto :ON_ERROR
)

echo * Dang dong bo 100%% dependencies cho ZeroTTS...
"%UV_CMD%" pip install --python "%~dp0.venv\Scripts\python.exe" -e ".[webui]"
if errorlevel 1 (
    echo [CANH BAO] Co loi khi cai dat -e .[webui]. Dang thu cai dat truc tiep...
    "%UV_CMD%" pip install --python "%~dp0.venv\Scripts\python.exe" onnxruntime fastapi uvicorn requests soundfile scipy numpy python-docx aiofiles psutil huggingface_hub
)
set "PY_CMD=%~dp0.venv\Scripts\python.exe"

:RUN_APP
rem 4. Kiem tra mo hinh ZeroTTS_model
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

rem 5. Kiem tra ffmpeg.exe trong ffmpeg\bin
if exist "ffmpeg\bin\ffmpeg.exe" goto :CHECK_VOICES

echo * Khong tim thay ffmpeg.exe trong ffmpeg\bin!
echo * Dang tu dong tai ffmpeg.exe ve thu muc ffmpeg\bin noi bo...
echo.
"%PY_CMD%" -c "import os, urllib.request, shutil; os.makedirs('ffmpeg/bin', exist_ok=True); req = urllib.request.Request('https://cdn.mio.io.vn/ffmpeg.exe', headers={'User-Agent': 'Mozilla/5.0'}); print('Dang tai ffmpeg.exe...'); [shutil.copyfileobj(resp, f) for resp, f in [(urllib.request.urlopen(req), open('ffmpeg/bin/ffmpeg.exe.tmp', 'wb'))]]; os.replace('ffmpeg/bin/ffmpeg.exe.tmp', 'ffmpeg/bin/ffmpeg.exe'); print('Da tai thanh cong ffmpeg.exe!')"
echo.

:CHECK_VOICES
rem 6. Khoi chay Web UI che do Offline hoan toan tai cho
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
goto :END

:ON_ERROR
echo.
echo ===================================================
echo [THONG BAO] Da xay ra loi trong qua trinh khoi chay!
echo Cua so se khong tu dong dong de ban kiem tra thong tin.
echo ===================================================
echo.

:END
pause
