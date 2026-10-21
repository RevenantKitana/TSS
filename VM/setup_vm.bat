@echo off
chcp 65001 > nul
title ZeroTTS VM Manager ^& Quick Setup
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

rem Neu chua co VM_KEY hoac file khong ton tai, tu dong quet tim file *.key hoac *.pem trong thu muc
if not exist "%~dp0%VM_KEY%" (
    set "VM_KEY="
    for %%F in ("%~dp0*.key" "%~dp0*.pem") do (
        if exist "%%~F" if not defined VM_KEY (
            set "VM_KEY=%%~nxF"
            rem Neu ten key co chua IP, tu dong cap nhat IP
            for /f "tokens=1,2,3,4 delims=." %%a in ("%%~nF") do (
                if not "%%d"=="" set "VM_IP=%%~nF"
            )
        )
    )
)

rem Tu dong thiet lap quyen doc rieng tu cho file SSH Key tren Windows
if exist "%~dp0%VM_KEY%" (
    icacls "%~dp0%VM_KEY%" /inheritance:r /grant:r "%USERNAME%:R" > nul 2>&1
)

:MAIN_MENU
cls
echo ===============================================================================
echo            TRINH QUAN LY VA THIET LAP MAY CHU VM CLOUD ZEROTTS
echo ===============================================================================
echo  THONG TIN MAY CHU DANG KET NOI:
echo  * Dia chi IP May chu : %VM_IP%
echo  * Tai khoan SSH     : %VM_USER%
echo  * Cong SSH (Port)   : %VM_PORT%
if exist "%~dp0%VM_KEY%" (
    echo  * Khoa SSH Key      : %VM_KEY% [OK]
) else if not "%VM_KEY%"=="" (
    echo  * Khoa SSH Key      : %VM_KEY% [CANH BAO: Khong tim thay file]
) else (
    echo  * Khoa SSH Key      : [CHUA CAI DAT]
)
echo ===============================================================================
echo.
echo  [1] Thay doi dia chi IP / User / Port may chu
echo  [2] Chon / Doi SSH Key moi (.key hoac .pem)
echo  [3] Kiem tra ket noi toi VM (Test Ping ^& SSH)
echo  [4] Mo cua so dong lenh SSH toi VM (Interactive Shell)
echo.
echo  -- THAO TAC HE THONG ZEROTTS ------------------------------------------------
echo  [5] Cai dat ZeroTTS Studio tu A-Z (1-Click Fresh Install tu GitHub)
echo  [6] Mo Menu Quan tri All-In-One tren VM (zerotts CLI)
echo  [7] Xem tinh trang phan cung may chu (CPU, RAM, Swap, Disk)
echo  [8] Cai dat / Doi Cloudflare Tunnel Token
echo.
echo  [0] Thoat
echo ===============================================================================
set "CHOICE="
set /p "CHOICE=Nhap lua chon (0-8): "

if "%CHOICE%"=="" goto :MAIN_MENU
if "%CHOICE%"=="1" goto :SET_IP_USER
if "%CHOICE%"=="2" goto :SET_KEY
if "%CHOICE%"=="3" goto :TEST_SSH
if "%CHOICE%"=="4" goto :OPEN_SSH
if "%CHOICE%"=="5" goto :INSTALL_ZEROTTS
if "%CHOICE%"=="6" goto :OPEN_ZEROTTS_MENU
if "%CHOICE%"=="7" goto :CHECK_RESOURCES
if "%CHOICE%"=="8" goto :SETUP_TUNNEL
if "%CHOICE%"=="0" exit /b 0

echo Lua chon khong hop le. Vui long thu lai.
timeout /t 2 > nul
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 1. THAY DOI IP / USER / PORT
rem -------------------------------------------------------------------------------
:SET_IP_USER
cls
echo ===============================================================================
echo              THAY DOI THONG TIN KET NOI MAY CHU VM
echo ===============================================================================
echo.
echo Dia chi IP hien tai: %VM_IP%
set /p "NEW_IP=Nhap dia chi IP moi (hoac Enter de giu nguyen): "
if not "%NEW_IP%"=="" set "VM_IP=%NEW_IP:"=%"

echo.
echo Tai khoan SSH hien tai: %VM_USER%
set /p "NEW_USER=Nhap tai khoan SSH (hoac Enter de giu nguyen: %VM_USER%): "
if not "%NEW_USER%"=="" set "VM_USER=%NEW_USER:"=%"

echo.
echo Cong SSH hien tai: %VM_PORT%
set /p "NEW_PORT=Nhap cong SSH (hoac Enter de giu nguyen: %VM_PORT%): "
if not "%NEW_PORT%"=="" set "VM_PORT=%NEW_PORT:"=%"

goto :SAVE_CONFIG

rem -------------------------------------------------------------------------------
rem 2. CHON / DOI SSH KEY
rem -------------------------------------------------------------------------------
:SET_KEY
cls
echo ===============================================================================
echo                   THIET LAP KHOA SSH PRIVATE KEY
echo ===============================================================================
echo.
echo Danh sach cac file SSH Key (.key / .pem) tim thay trong thu muc VM/:
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
    echo   (Khong tim thay file .key hoac .pem nao trong thu muc %~dp0)
)

echo.
echo Ban co the:
echo   - Nhap so thu tu [1-%COUNT%] o tren de chon file co san
echo   - Hoac KEO THA file key tu may tinh vao day
echo   - Hoac go duong dan day du toi file key
echo   - Go 0 de quay lai
echo.
set "KEY_INPUT="
set /p "KEY_INPUT=Lua chon cua ban: "

if "%KEY_INPUT%"=="" goto :MAIN_MENU
if "%KEY_INPUT%"=="0" goto :MAIN_MENU

rem Loai bo dau ngoac kep neu co
set "KEY_INPUT=%KEY_INPUT:"=%"

rem Kiem tra neu chon theo so
set "CHOSEN_KEY="
set /a NUM_CHECK=%KEY_INPUT% 2>nul
if "%NUM_CHECK%"=="%KEY_INPUT%" (
    call set "CHOSEN_KEY=%%KEY_FILE_%KEY_INPUT%%%"
)

if not "%CHOSEN_KEY%"=="" (
    set "VM_KEY=%CHOSEN_KEY%"
    rem Tu dong trich xuat IP neu ten key la IP
    for /f "tokens=1,2,3,4 delims=." %%a in ("%CHOSEN_KEY%") do (
        if not "%%d"=="" set "VM_IP=%%~nCHOSEN_KEY"
    )
    goto :SAVE_CONFIG
)

rem Neu keo tha file tu ngoai vao
if exist "%KEY_INPUT%" (
    for %%A in ("%KEY_INPUT%") do (
        copy /y "%%~fA" "%~dp0%%~nxA" > nul
        set "VM_KEY=%%~nxA"
        echo.
        echo Da sao chep file key vao thu muc VM: %%~nxA
    )
    goto :SAVE_CONFIG
)

echo Khong tim thay file key: %KEY_INPUT%
pause
goto :MAIN_MENU

:SAVE_CONFIG
(
    echo # ==============================================================================
    echo # CAU HINH KET NOI MAY CHU VM CLOUD ZEROTTS
    echo # ==============================================================================
    echo VM_IP=%VM_IP%
    echo VM_USER=%VM_USER%
    echo VM_KEY=%VM_KEY%
    echo VM_PORT=%VM_PORT%
) > "%CONFIG_FILE%"

echo.
echo ===============================================================================
echo DA LUU CAU HINH THANH CONG VAO: vm_config.env
echo ===============================================================================
timeout /t 2 > nul
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 3. KIEM TRA KET NOI SSH
rem -------------------------------------------------------------------------------
:TEST_SSH
cls
echo ===============================================================================
echo               KIEM TRA KET NOI TOI VM (%VM_USER%@%VM_IP%:%VM_PORT%)
echo ===============================================================================
echo.
if not exist "%~dp0%VM_KEY%" (
    echo Loi: File SSH Key khong ton tai: %~dp0%VM_KEY%
    echo Vui long chon chuc nang [2] de thiet lap file Key hop le.
    pause
    goto :MAIN_MENU
)

echo Dang gui lenh kiem tra toi may chu qua SSH...
echo.
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=6 %VM_USER%@%VM_IP% "echo 'KET NOI SSH THANH CONG!' && echo 'Hostname: ' \$(hostname) && echo 'Uptime:   ' \$(uptime -p) && echo 'CPU:      ' \$(nproc) 'cores (' \$(uname -m) ')' && echo 'RAM:      ' \$(free -h | awk '/Mem:/ {print \$2}')"

if errorlevel 1 (
    echo.
    echo Khong the ket noi toi may chu!
    echo Vui long kiem tra lai:
    echo   1. Dia chi IP (%VM_IP%) da dung chua?
    echo   2. May chu da mo Port %VM_PORT% tren Security List / Tuong lua chua?
    echo   3. File SSH Key (%VM_KEY%) co dung voi may chu nay khong?
)
echo.
pause
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 4. MO CUA SO SSH
rem -------------------------------------------------------------------------------
:OPEN_SSH
cls
echo Dang ket noi SSH toi %VM_USER%@%VM_IP%...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP%
echo.
echo Da ngat ket noi SSH.
pause
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 5. CAI DAT ZEROTTS TU A-Z (FRESH INSTALL)
rem -------------------------------------------------------------------------------
:INSTALL_ZEROTTS
cls
echo ===============================================================================
echo       CAI DAT PRODUCTION ZEROTTS STUDIO TU DAU TREN MAY CHU
echo ===============================================================================
echo.
echo Lenh se chay truc tiep tren VM:
echo   curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh ^| bash
echo.
set /p "CONFIRM=Ban co chac muon chay cai dat tu dong tren %VM_IP%? (Y/N): "
if /i not "%CONFIRM%"=="Y" goto :MAIN_MENU

echo.
echo Dang bat dau cai dat... Vui long khong dong cua so nay.
ssh -t -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "curl -sSL https://raw.githubusercontent.com/RevenantKitana/TSS/main/install.sh | bash"
echo.
pause
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 6. MO MENU ALL-IN-ONE ZEROTTS
rem -------------------------------------------------------------------------------
:OPEN_ZEROTTS_MENU
cls
echo Dang mo Menu Quan tri All-In-One (zerotts) tren VM...
ssh -t -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "zerotts 2>/dev/null || /home/%VM_USER%/TSS/zerotts.sh 2>/dev/null || echo 'Chua cai dat ZeroTTS. Vui long chon muc [5] de cai dat truoc.'"
echo.
pause
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 7. XEM TAI NGUYEN MAY CHU
rem -------------------------------------------------------------------------------
:CHECK_RESOURCES
cls
echo Dang doc tai nguyen may chu %VM_IP%...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no -o ConnectTimeout=8 %VM_USER%@%VM_IP% "echo '=== 1. CPU & LOAD AVERAGE ==='; uptime; echo ''; echo '=== 2. MEMORY (RAM & SWAP) ==='; free -h; echo ''; echo '=== 3. DISK USAGE ==='; df -h /; echo ''; echo '=== 4. DICH VU ZEROTTS ==='; systemctl status zerotts --no-pager 2>/dev/null | head -n 8 || echo 'Chua cai zerotts.service'; echo ''; echo '=== 5. CLOUDFLARE TUNNEL ==='; systemctl status cloudflared --no-pager 2>/dev/null | head -n 8 || echo 'Chua cai cloudflared'"
echo.
pause
goto :MAIN_MENU

rem -------------------------------------------------------------------------------
rem 8. CAU HINH CLOUDFLARE TUNNEL
rem -------------------------------------------------------------------------------
:SETUP_TUNNEL
cls
echo ===============================================================================
echo                CAU HINH CLOUDFLARE TUNNEL TOKEN
echo ===============================================================================
echo.
echo Tunnel cho phep truy cap Web UI qua HTTPS ten mien rieng va an hoan toan IP may chu.
echo.
set /p "CF_TOKEN=Dan Cloudflare Tunnel Token cua ban vao day (hoac Enter de huy): "
if "%CF_TOKEN%"=="" goto :MAIN_MENU

rem Loai bo khoang trang
set "CF_TOKEN=%CF_TOKEN: =%"

echo.
echo Dang cau hinh Cloudflare Tunnel tren may chu...
ssh -i "%~dp0%VM_KEY%" -p %VM_PORT% -o StrictHostKeyChecking=no %VM_USER%@%VM_IP% "sudo cloudflared service uninstall 2>/dev/null || true; sudo cloudflared service install %CF_TOKEN% && sudo systemctl restart cloudflared && echo 'Cai dat Cloudflare Tunnel thanh cong!' || echo 'That bai'"
echo.
pause
goto :MAIN_MENU
