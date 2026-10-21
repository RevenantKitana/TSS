@echo off
chcp 65001 > nul
title SSH Oracle VM (168.107.86.20)
cd /d "%~dp0"

echo ===================================================
echo     Ket noi SSH toi Oracle VM (168.107.86.20)
echo ===================================================
echo.

ssh -i "%~dp0168.107.86.20.key" -o StrictHostKeyChecking=no ubuntu@168.107.86.20

echo.
echo Da ngat ket noi SSH.
pause
