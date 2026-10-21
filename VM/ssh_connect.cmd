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

title SSH Oracle VM (%VM_USER%@%VM_IP%:%VM_PORT%)

echo ===================================================
echo     Ket noi SSH toi VM (%VM_USER%@%VM_IP%:%VM_PORT%)
echo ===================================================
echo.

ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP%

echo.
echo Da ngat ket noi SSH.
pause
