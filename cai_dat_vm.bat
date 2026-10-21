@echo off
cd /d "%~dp0VM"
if not exist "setup_vm.bat" (
    echo [LOI] Khong tim thay file VM\setup_vm.bat
    pause
    exit /b 1
)
call setup_vm.bat
if errorlevel 1 (
    echo.
    echo Script da dung lai voi ma loi %errorlevel%.
    pause
)
