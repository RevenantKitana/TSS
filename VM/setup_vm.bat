@echo off
chcp 65001 > nul
title ZeroTTS VM Manager & Quick Setup
cd /d "%~dp0"

:LOAD_CONFIG
set "CONFIG_FILE=%~dp0vm_config.env"
set "VM_IP=127.0.0.1"
set "VM_USER=ubuntu"
set "VM_KEY="
set "VM_PORT=22"

if exist "%CONFIG_FILE%" (
    for /f "usebackq eol=# tokens=1* delims==" %%A in ("%CONFIG_FILE%") do (
        if /i "%%A"=="VM_IP" set "VM_IP=%%B"
        if /i "%%A"=="VM_USER" set "VM_USER=%%B"
        if /i "%%A"=="VM_KEY" set "VM_KEY=%%B"
        if /i "%%A"=="VM_PORT" set "VM_PORT=%%B"
    )
)

rem Neu chua co VM_KEY, thu quet tim file *.key hoac *.pem trong thu muc
if "%VM_KEY%"=="" (
    for %%F in ("%~dp0*.key" "%~dp0*.pem") do (
        if exist "%%~F" (
            set "VM_KEY=%%~nxF"
            goto :AFTER_KEY_SCAN
        )
    )
)
:AFTER_KEY_SCAN

:MAIN_MENU
cls
echo ===============================================================================
echo            🚀 TRÌNH QUẢN LÝ VÀ THIẾT LẬP MÁY CHỦ VM CLOUD ZEROTTS
echo ===============================================================================
echo  📍 THÔNG TIN MÁY CHỦ ĐANG KẾT NỐI:
echo  • Địa chỉ IP Máy chủ : %VM_IP%
echo  • Tài khoản SSH     : %VM_USER%
echo  • Cổng SSH (Port)   : %VM_PORT%
if exist "%~dp0%VM_KEY%" (
    echo  • Khóa SSH Key      : %VM_KEY% [OK]
) else if not "%VM_KEY%"=="" (
    echo  • Khóa SSH Key      : %VM_KEY% [CANH BAO: Khong tim thay file]
) else (
    echo  • Khóa SSH Key      : [CHUA CAI DAT]
)
echo ===============================================================================
echo.
echo  [1] ⚙️  Thay đổi địa chỉ IP / User / Port máy chủ
echo  [2] 🔑  Chọn / Đổi SSH Key mới (Tự động quét file .key / .pem hoặc kéo thả)
echo  [3] 🔌  Kiểm tra kết nối tới VM (Test Ping ^& SSH)
echo  [4] 💻  Mở cửa sổ dòng lệnh SSH tới VM (Interactive Shell)
echo.
echo  ── THAO TÁC HỆ THỐNG ZEROTTS ───────────────────────────────────────────
echo  [5] 🚀  Cài đặt ZeroTTS Studio từ A-Z (1-Click Fresh Install từ GitHub)
echo  [6] 🛠️   Mở Menu Quản trị All-In-One trên VM (zerotts CLI)
echo  [7] 📊  Xem tình trạng phần cứng máy chủ (CPU, RAM, Swap, Disk)
echo  [8] 🌐  Cài đặt / Đổi Cloudflare Tunnel Token
echo.
echo  [0] 🚪  Thoát
echo ===============================================================================
set /p "CHOICE=👉 Nhập lựa chọn (0-8): "

if "%CHOICE%"=="1" goto :SET_IP_USER
if "%CHOICE%"=="2" goto :SET_KEY
if "%CHOICE%"=="3" goto :TEST_SSH
if "%CHOICE%"=="4" goto :OPEN_SSH
if "%CHOICE%"=="5" goto :INSTALL_ZEROTTS
if "%CHOICE%"=="6" goto :OPEN_ZEROTTS_MENU
if "%CHOICE%"=="7" goto :CHECK_RESOURCES
if "%CHOICE%"=="8" goto :SETUP_TUNNEL
if "%CHOICE%"=="0" exit /b 0

echo Lựa chọn không hợp lệ. Vui lòng thử lại.
timeout /t 2 > nul
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 1. THAY ĐỔI IP / USER / PORT
rem ───────────────────────────────────────────────────────────────────────────
:SET_IP_USER
cls
echo ===============================================================================
echo              ⚙️ THAY ĐỔI THÔNG TIN KẾT NỐI MÁY CHỦ VM
echo ===============================================================================
echo.
echo Địa chỉ IP hiện tại: %VM_IP%
set /p "NEW_IP=Nhập địa chỉ IP mới (hoặc Enter để giữ nguyên): "
if not "%NEW_IP%"=="" set "VM_IP=%NEW_IP:"=%"

echo.
echo Tài khoản SSH hiện tại: %VM_USER%
set /p "NEW_USER=Nhập tài khoản SSH (hoặc Enter để giữ nguyên: %VM_USER%): "
if not "%NEW_USER%"=="" set "VM_USER=%NEW_USER:"=%"

echo.
echo Cổng SSH hiện tại: %VM_PORT%
set /p "NEW_PORT=Nhập cổng SSH (hoặc Enter để giữ nguyên: %VM_PORT%): "
if not "%NEW_PORT%"=="" set "VM_PORT=%NEW_PORT:"=%"

goto :SAVE_CONFIG

rem ───────────────────────────────────────────────────────────────────────────
rem 2. CHỌN / ĐỔI SSH KEY
rem ───────────────────────────────────────────────────────────────────────────
:SET_KEY
cls
echo ===============================================================================
echo                   🔑 THIẾT LẬP KHÓA SSH PRIVATE KEY
echo ===============================================================================
echo.
echo Danh sách các file SSH Key (.key / .pem) tìm thấy trong thư mục VM/:
echo.

set "COUNT=0"
for %%F in ("%~dp0*.key" "%~dp0*.pem") do (
    if exist "%%~F" (
        set /a COUNT+=1
        call set "KEY_FILE_%%COUNT%%=%%~nxF"
        call echo   [%%COUNT%%] %%~nxF
    )
)

if %COUNT%==0 (
    echo   (Không tìm thấy file .key hoặc .pem nào trong thư mục %~dp0)
)

echo.
echo Bạn có thể:
echo   - Nhập số thứ tự [1-%COUNT%] ở trên để chọn file có sẵn
echo   - Hoặc KÉO THẢ file key từ máy tính vào đây
echo   - Hoặc gõ đường dẫn đầy đủ tới file key
echo   - Gõ 0 để quay lại
echo.
set /p "KEY_INPUT=👉 Lựa chọn của bạn: "

if "%KEY_INPUT%"=="" goto :MAIN_MENU
if "%KEY_INPUT%"=="0" goto :MAIN_MENU

rem Loại bỏ dấu ngoặc kép nếu người dùng kéo thả file
set "KEY_INPUT=%KEY_INPUT:"=%"

rem Kiểm tra nếu người dùng chọn theo số
set "CHOSEN_KEY="
set /a NUM_CHECK=%KEY_INPUT% 2>nul
if "%NUM_CHECK%"=="%KEY_INPUT%" (
    call set "CHOSEN_KEY=%%KEY_FILE_%KEY_INPUT%%%"
)

if not "%CHOSEN_KEY%"=="" (
    set "VM_KEY=%CHOSEN_KEY%"
    goto :SAVE_CONFIG
)

rem Nếu người dùng nhập đường dẫn file hoặc kéo thả file từ ngoài vào
if exist "%KEY_INPUT%" (
    for %%A in ("%KEY_INPUT%") do (
        copy /y "%%~fA" "%~dp0%%~nxA" > nul
        set "VM_KEY=%%~nxA"
        echo.
        echo ✅ Đã sao chép file key vào thư mục VM: %%~nxA
    )
    goto :SAVE_CONFIG
)

echo ❌ Không tìm thấy file key: %KEY_INPUT%
pause
goto :MAIN_MENU

:SAVE_CONFIG
(
    echo # ==============================================================================
    echo # CẤU HÌNH KẾT NỐI MÁY CHỦ VM CLOUD ZEROTTS
    echo # ==============================================================================
    echo VM_IP=%VM_IP%
    echo VM_USER=%VM_USER%
    echo VM_KEY=%VM_KEY%
    echo VM_PORT=%VM_PORT%
) > "%CONFIG_FILE%"

echo.
echo ===============================================================================
echo ✅ ĐÃ LƯU CẤU HÌNH THÀNH CÔNG VÀO: vm_config.env
echo ===============================================================================
timeout /t 2 > nul
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 3. KIỂM TRA KẾT NỐI SSH
rem ───────────────────────────────────────────────────────────────────────────
:TEST_SSH
cls
echo ===============================================================================
echo               🔌 KIỂM TRA KẾT NỐI TỚI VM (%VM_USER%@%VM_IP%:%VM_PORT%)
echo ===============================================================================
echo.
if not exist "%~dp0%VM_KEY%" (
    echo ❌ Lỗi: File SSH Key không tồn tại: %~dp0%VM_KEY%
    echo Vui lòng chọn chức năng [2] để thiết lập file Key hợp lệ.
    pause
    goto :MAIN_MENU
)

echo Đang gửi lệnh kiểm tra tới máy chủ qua SSH...
echo.
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=6 %VM_USER%@%VM_IP% "echo '✅ KẾT NỐI SSH THÀNH CÔNG!' && echo '• Hostname: ' \$(hostname) && echo '• Uptime:   ' \$(uptime -p) && echo '• CPU:      ' \$(nproc) 'cores (' \$(uname -m) ')' && echo '• RAM:      ' \$(free -h | awk '/Mem:/ {print \$2}')"

if errorlevel 1 (
    echo.
    echo ❌ Không thể kết nối tới máy chủ!
    echo Vui lòng kiểm tra lại:
    echo   1. Địa chỉ IP (%VM_IP%) đã đúng chưa?
    echo   2. Máy chủ đã mở Port %VM_PORT% trên Security List / Tường lửa chưa?
    echo   3. File SSH Key (%VM_KEY%) có đúng với máy chủ này không?
)
echo.
pause
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 4. MỞ CỬA SỔ SSH
rem ───────────────────────────────────────────────────────────────────────────
:OPEN_SSH
cls
echo Đang kết nối SSH tới %VM_USER%@%VM_IP%...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP%
echo.
echo Đã ngắt kết nối SSH.
pause
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 5. CÀI ĐẶT ZEROTTS TỪ A-Z (FRESH INSTALL)
rem ───────────────────────────────────────────────────────────────────────────
:INSTALL_ZEROTTS
cls
echo ===============================================================================
echo       🚀 CÀI ĐẶT PRODUCTION ZEROTTS STUDIO TỪ ĐẦU TRÊN MÁY CHỦ
echo ===============================================================================
echo.
echo Lệnh sẽ chạy trực tiếp trên VM:
echo   curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh ^| bash
echo.
set /p "CONFIRM=Bạn có chắc muốn chạy cài đặt tự động trên %VM_IP%? (Y/N): "
if /i not "%CONFIRM%"=="Y" goto :MAIN_MENU

echo.
echo ⏳ Đang bắt đầu cài đặt... Vui lòng không đóng cửa sổ này.
ssh -t -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh | bash"
echo.
pause
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 6. MỞ MENU ALL-IN-ONE ZEROTTS
rem ───────────────────────────────────────────────────────────────────────────
:OPEN_ZEROTTS_MENU
cls
echo Đang mở Menu Quản trị All-In-One (zerotts) trên VM...
ssh -t -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "zerotts 2>/dev/null || /home/%VM_USER%/TSS/zerotts.sh 2>/dev/null || echo 'Chưa cài đặt ZeroTTS. Vui lòng chọn mục [5] để cài đặt trước.'"
echo.
pause
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 7. XEM TÀI NGUYÊN MÁY CHỦ
rem ───────────────────────────────────────────────────────────────────────────
:CHECK_RESOURCES
cls
echo Đang đọc tài nguyên máy chủ %VM_IP%...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no -o ConnectTimeout=8 %VM_USER%@%VM_IP% "echo '=== 1. CPU & LOAD AVERAGE ==='; uptime; echo ''; echo '=== 2. MEMORY (RAM & SWAP) ==='; free -h; echo ''; echo '=== 3. DISK USAGE ==='; df -h /; echo ''; echo '=== 4. DỊCH VỤ ZEROTTS ==='; systemctl status zerotts --no-pager 2>/dev/null | head -n 8 || echo 'Chưa cài zerotts.service'; echo ''; echo '=== 5. CLOUDFLARE TUNNEL ==='; systemctl status cloudflared --no-pager 2>/dev/null | head -n 8 || echo 'Chưa cài cloudflared'"
echo.
pause
goto :MAIN_MENU

rem ───────────────────────────────────────────────────────────────────────────
rem 8. CẤU HÌNH CLOUDFLARE TUNNEL
rem ───────────────────────────────────────────────────────────────────────────
:SETUP_TUNNEL
cls
echo ===============================================================================
echo                🌐 CẤU HÌNH CLOUDFLARE TUNNEL TOKEN
echo ===============================================================================
echo.
echo Tunnel cho phép truy cập Web UI qua HTTPS tên miền riêng và ẩn hoàn toàn IP máy chủ.
echo.
set /p "CF_TOKEN=👉 Dán Cloudflare Tunnel Token của bạn vào đây (hoặc Enter để hủy): "
if "%CF_TOKEN%"=="" goto :MAIN_MENU

rem Loại bỏ khoảng trắng
set "CF_TOKEN=%CF_TOKEN: =%"

echo.
echo Đang cấu hình Cloudflare Tunnel trên máy chủ...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "sudo cloudflared service uninstall 2>/dev/null || true; sudo cloudflared service install %CF_TOKEN% && sudo systemctl restart cloudflared && echo '✅ Cài đặt Cloudflare Tunnel thành công!' || echo '❌ Thất bại'"
echo.
pause
goto :MAIN_MENU
