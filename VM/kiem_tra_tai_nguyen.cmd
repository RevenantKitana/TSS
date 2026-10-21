@echo off
setlocal
cd /d "%~dp0"

set "VM_IP=168.107.86.20"
set "VM_USER=ubuntu"
set "VM_KEY=168.107.86.20.key"
set "VM_PORT=22"

if exist "%~dp0vm_config.env" (
    for /f "usebackq tokens=1,* delims==" %%A in ("%~dp0vm_config.env") do (
        if /i "%%A"=="VM_IP" set "VM_IP=%%B"
        if /i "%%A"=="VM_USER" set "VM_USER=%%B"
        if /i "%%A"=="VM_KEY" set "VM_KEY=%%B"
        if /i "%%A"=="VM_PORT" set "VM_PORT=%%B"
    )
)

title Theo Doi Tai Nguyen VM (%VM_USER%@%VM_IP% - Auto-refresh 5s)

:LOOP
cls
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no -o ConnectTimeout=5 %VM_USER%@%VM_IP% "echo '=== 1. CPU & LOAD AVERAGE ==='; lscpu | grep 'Model name'; uptime; echo ''; echo '=== 2. RAM & SWAP ==='; free -h; echo ''; echo '=== 3. DISK STORAGE ==='; df -h /; echo ''; echo '=== 4. ZEROTTS SERVICE STATUS ==='; systemctl status zerotts --no-pager 2>/dev/null | head -n 8 || echo 'Dich vu ZeroTTS chua cai dat (Hay chay install.sh de khoi tao)'"

echo.
echo ===============================================================================
echo  [Nhan phim Ctrl+C de thoat] - Dang tu dong cap nhat moi 5 giay...
echo ===============================================================================
ping 127.0.0.1 -n 6 >nul
goto :LOOP
