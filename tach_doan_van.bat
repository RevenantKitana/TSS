@echo off
chcp 65001 > nul
title Phan Tach Doan Van Cho TSS
cd /d "%~dp0"

echo ===================================================
echo     Cong Cu Phan Tach Doan Van Tu Dong (Khong AI)
echo ===================================================
echo.

rem 1. Tim Python thuc thi
set "PY_CMD=python"
if exist "python-3.11.2-embed-amd64\python.exe" (
    set "PY_CMD=python-3.11.2-embed-amd64\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
)

rem 2. Neu nguoi dung keo tha file vao hoac truyen tham so
if not "%~1"=="" (
    echo * Dang xu ly file: %~1
    set "OUT_FILE=%~dpn1_formatted.txt"
    "%PY_CMD%" scripts\split_text.py "%~1" -o "%OUT_FILE%"
    echo.
    echo * File ket qua da duoc luu tai:
    echo   %OUT_FILE%
    echo.
    pause
    exit /b 0
)

rem 3. Neu chay truc tiep khong truyen file, hoi nguoi dung nhap duong dan file
echo Ban co the:
echo 1. Keo tha truc tiep file .txt hoac .docx vao file bat nay.
echo 2. Hoac nhap duong dan file ben duoi:
echo.
set /p "USER_INPUT_FILE=Nhap duong dan file can tach (hoac an Enter de thoat): "

if "%USER_INPUT_FILE%"=="" (
    echo Da huy.
    exit /b 0
)

rem Loai bo dau ngoac kep neu co
set "USER_INPUT_FILE=%USER_INPUT_FILE:"=%"

if not exist "%USER_INPUT_FILE%" (
    echo [Loi] Khong tim thay file: %USER_INPUT_FILE%
    pause
    exit /b 1
)

for %%F in ("%USER_INPUT_FILE%") do set "OUT_FILE=%%~dpnF_formatted.txt"
"%PY_CMD%" scripts\split_text.py "%USER_INPUT_FILE%" -o "%OUT_FILE%"

echo.
echo ===================================================
echo Da hoan thanh! File dau ra: %OUT_FILE%
echo ===================================================
echo.
pause
