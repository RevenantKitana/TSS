@echo off
setlocal
cd /d "%~dp0"
title Theo Doi Tai Nguyen VM Oracle (Auto-refresh 5s)

:LOOP
cls
ssh -i "%~dp0168.107.86.20.key" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@168.107.86.20 "echo '=== 1. CPU & LOAD AVERAGE ==='; lscpu | grep 'Model name'; uptime; echo ''; echo '=== 2. RAM & SWAP ==='; free -h; echo ''; echo '=== 3. DISK STORAGE ==='; df -h /; echo ''; echo '=== 4. ZEROTTS SERVICE STATUS ==='; systemctl status zerotts --no-pager 2>/dev/null | head -n 8 || echo 'Dich vu ZeroTTS chua cai dat (Hay chay install.sh de khoi tao)'"

echo.
echo ===============================================================================
echo  [Nhan phim Ctrl+C de thoat] - Dang tu dong cap nhat moi 5 giay...
echo ===============================================================================
ping 127.0.0.1 -n 6 >nul
goto :LOOP
