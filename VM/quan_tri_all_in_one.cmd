@echo off
chcp 65001 > nul
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

title ZeroTTS All-In-One Toolkit (%VM_USER%@%VM_IP%)

echo ===============================================================================
echo        KET NOI TOI ZEROTTS ALL-IN-ONE TOOLKIT (BASH SSH)
echo ===============================================================================
echo  * Host: %VM_USER%@%VM_IP%:%VM_PORT%
echo  * Key : %~dp0%VM_KEY%
echo ===============================================================================
echo.

ssh -t -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "zerotts 2>/dev/null || /home/%VM_USER%/TSS/zerotts.sh 2>/dev/null || echo 'Chua cai dat ZeroTTS tren VM! Chon setup_vm.bat muc [5] de cai dat.'"

echo.
echo Da dong phien lam viec.
pause
