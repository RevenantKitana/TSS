@echo off
title ZeroTTS All-In-One Toolkit (168.107.86.20)
cd /d "%~dp0"

echo ===============================================================================
echo        KET NOI TOI ZEROTTS ALL-IN-ONE TOOLKIT (BASH SSH)
echo ===============================================================================
echo  * Host: ubuntu@168.107.86.20
echo  * Key : %~dp0168.107.86.20.key
echo ===============================================================================
echo.

ssh -t -i "%~dp0168.107.86.20.key" -o StrictHostKeyChecking=no ubuntu@168.107.86.20 "/home/ubuntu/TSS/zerotts.sh"

echo.
echo Da dong phien lam viec.
pause
