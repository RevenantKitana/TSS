@echo off
chcp 65001 > nul
title Dong Goi Ma Nguon TSS Cho Google Colab va Kaggle
cd /d "%~dp0"

echo ==========================================================
echo   Dong Goi Ma Nguon TSS De Chay Tren Google Colab va Kaggle
echo ==========================================================
echo.

if exist "python-3.11.2-embed-amd64\python.exe" (
    "python-3.11.2-embed-amd64\python.exe" package_colab_zip.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" package_colab_zip.py
) else (
    python package_colab_zip.py
)

echo.
pause
