@echo off
title PHAN MEM KE TOAN PRO V3 - FIXED FONT
echo ============================================================================
echo           DANG CHAY UNG DUNG VOI FONT CHUAN SEGOE UI
echo ============================================================================
echo.

REM Set bi?n m?i tr??ng cho font Windows
set QT_AUTO_SCREEN_SCALE_FACTOR=1
set QT_SCALE_FACTOR=1

REM Ch?y ?ng d?ng
python main.py

if errorlevel 1 (
    echo.
    echo LOI: Khong the chay ung dung!
    echo Thu thu: python run.py hoac python app.py
    pause
)
