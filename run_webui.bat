@echo off
chcp 65001 > nul
title ZeroTTS Web UI
cd /d "%~dp0"

echo ===================================================
echo           Khoi chay ZeroTTS Web UI
echo ===================================================
echo.

rem 1. Kiem tra neu co thu muc Python Embed local trong python-3.11.2-embed-amd64
if exist "python-3.11.2-embed-amd64\python.exe" (
    set "PY_CMD=python-3.11.2-embed-amd64\python.exe"
    echo * Phat hien thuc thi Python Embed local trong python-3.11.2-embed-amd64!
    
    if exist "python-3.11.2-embed-amd64\python311._pth" (
        "python-3.11.2-embed-amd64\python.exe" -c "with open('python-3.11.2-embed-amd64/python311._pth', 'r+') as f: txt = f.read(); txt = txt.replace('#import site', 'import site'); txt = txt + '\nLib/site-packages\n' if 'Lib/site-packages' not in txt else txt; f.seek(0); f.write(txt); f.truncate()" >nul 2>&1
    )
    
    "python-3.11.2-embed-amd64\python.exe" -c "import zerotts, gradio" >nul 2>&1
    if errorlevel 1 (
        echo * Dang cai dat dependencies cho Python Embed local...
        where uv >nul 2>&1
        if not errorlevel 1 (
            uv pip install --python "python-3.11.2-embed-amd64\python.exe" -e ".[webui]"
        ) else if exist "uv.exe" (
            .\uv.exe pip install --python "python-3.11.2-embed-amd64\python.exe" -e ".[webui]"
        ) else (
            "python-3.11.2-embed-amd64\python.exe" -m pip install -e ".[webui]"
        )
    )
    goto :RUN_APP
)

rem 2. Neu khong dung Python Embed local, dung moi truong ao .venv
set "VENV_OK=0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import zerotts, gradio" >nul 2>&1
    if not errorlevel 1 set "VENV_OK=1"
)

if "%VENV_OK%"=="0" (
    if exist ".venv" (
        echo * Phat hien moi truong .venv bi loi hoac thieu thu vien. Dang tao lai...
        rmdir /s /q ".venv" >nul 2>&1
    ) else (
        echo * Chua tim thay moi truong ao .venv. Dang tien hanh cai dat tu dong...
    )

    where uv >nul 2>&1
    if not errorlevel 1 (
        echo * Phat hien cong cu uv! Dang tao .venv va cai dat dependencies...
        uv venv --python 3.11
        uv pip install -e ".[webui]"
    ) else if exist "uv.exe" (
        echo * Phat hien uv.exe local! Dang tao .venv va cai dat dependencies...
        .\uv.exe venv --python 3.11
        .\uv.exe pip install -e ".[webui]"
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            echo * Dang tao .venv bang Python he thong...
            python -m venv .venv
            call .venv\Scripts\activate.bat
            pip install -e ".[webui]"
        ) else (
            echo [LOI] May tinh cua ban chua cai dat Python hoac uv!
            echo Vui long cai dat Python phien ban >= 3.9 de su dung ZeroTTS.
            echo.
            pause
            exit /b 1
        )
    )
)

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

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
"%PY_CMD%" webui/app.py --model ./ZeroTTS_model

pause
