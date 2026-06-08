@echo off
title CHAY KE TOAN PRO SAU KHI BUILD
cd /d D:\ke_toan_pro_v3

echo Xoa cache lan cuoi...
python clean_cache.py

echo Copy model lan cuoi...
python copy_easyocr_models.py

echo Chay chuong trinh...
cd dist
start PhanMemKeToan.exe

echo Hoan tat!