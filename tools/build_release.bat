@echo off
title KE TOAN PRO - BUILD & LICENSE TOOL
setlocal enabledelayedexpansion

:: ============================================================
::  CÔNG CỤ ĐÓNG GÓI VÀ TẠO LICENSE CHO KẾ TOÁN PRO
::  - dist: GIỮ NGUYÊN DỮ LIỆU THẬT (để admin làm việc)
::  - gói khách: XÓA SẠCH DỮ LIỆU, chỉ giữ cấu trúc
::  - tạo license key cho khách hàng
::  - XUẤT KIẾN TRÚC PHẦN MỀM
::  - TỰ ĐỘNG ĐỒNG BỘ PHIÊN BẢN TỪ version.txt (MỚI)
:: ============================================================

:: Kiểm tra quyền Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Ban can chay file nay voi quyen Administrator.
    pause
    exit /b 1
)

cd /d D:\ke_toan_pro_v3 2>nul || ( echo Khong tim thay thu muc! & pause & exit /b 1 )

:: ============================================================
:: TỰ ĐỘNG LẤY PHIÊN BẢN DUY NHẤT TỪ version.txt
:: ============================================================
setlocal enabledelayedexpansion

if exist version.json (
    for /f "delims=" %%v in ('powershell -NoProfile -Command "(Get-Content version.json -Raw | ConvertFrom-Json).phien_ban_moi_nhat"') do (
        set "VERSION=%%v"
    )
    echo [OK] Da tim thay phien ban !VERSION! trong version.json
    echo !VERSION!> version.txt
    echo [OK] Da dong bo version.txt = !VERSION!
) else (
    echo [CANH BAO] Khong tim thay version.json!
    set VERSION=Unknown
)

echo Dang dong goi phien ban !VERSION!...

:: === TỰ ĐỘNG ĐỒNG BỘ PHIÊN BẢN VÀO CONFIG.PY ===
echo.
echo Dang dong bo phien ban %VERSION% vao config.py...
powershell -Command "(Get-Content 'config.py') -replace 'VERSION = \".*?\"', 'VERSION = \"%VERSION%\"' | Set-Content 'config.py'"
if errorlevel 1 (
    echo LOI: Khong the dong bo config.py!
    pause
) else (
    echo Da dong bo thanh cong config.py
)

:: Tạo timestamp
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (set DD=%%a&set MM=%%b&set YYYY=%%c)
if "%DD:~0,1%"=="0" set DD=%DD:~1%
if "%MM:~0,1%"=="0" set MM=%MM:~1%
for /f "tokens=1-3 delims=: " %%a in ('time /t') do (set HH=%%a&set MN=%%b)
if "%HH:~0,1%"=="0" set HH=%HH:~1%
if "%MN:~0,1%"=="0" set MN=%MN:~1%
set TIMESTAMP=%YYYY%%MM%%DD%_%HH%%MN%
set ARCH_FILE=KienTrucPhanMem_%VERSION%_%TIMESTAMP%.txt
set ARCH_PATH=D:\%ARCH_FILE%

:menu
cls
echo ============================================================
echo     KE TOAN PRO - BUILD AND TOOL MENU
echo ============================================================
echo.
echo   Phien ban: %VERSION%
echo   Ngay: %date% - %time%
echo.
echo   [1] Build EXE + Tao dist + Dong goi cho khach (day du)
echo   [2] Chi build EXE
echo   [3] Tao license key cho khach hang
echo   [4] XUAT KIEN TRUC PHAN MEM
echo   [5] Thoat
echo.
choice /C 12345 /N /M "Lua chon cua ban: "
if errorlevel 5 exit /b 0
if errorlevel 4 goto :export_architecture
if errorlevel 3 goto :create_license
if errorlevel 2 goto :build_only
if errorlevel 1 goto :full_build

:: ============================================================
::  XUẤT KIẾN TRÚC PHẦN MỀM
:: ============================================================
:export_architecture
echo.
echo ============================================================
echo XUAT KIEN TRUC PHAN MEM KE TOAN PRO v%VERSION%
echo ============================================================
echo.

:: Tạo lại timestamp và đường dẫn cho lần xuất này
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (set DD=%%a&set MM=%%b&set YYYY=%%c)
if "%DD:~0,1%"=="0" set DD=%DD:~1%
if "%MM:~0,1%"=="0" set MM=%MM:~1%
for /f "tokens=1-3 delims=: " %%a in ('time /t') do (set HH=%%a&set MN=%%b)
if "%HH:~0,1%"=="0" set HH=%HH:~1%
if "%MN:~0,1%"=="0" set MN=%MN:~1%
set TIMESTAMP=%YYYY%%MM%%DD%_%HH%%MN%
set ARCH_FILE=KienTrucPhanMem_%VERSION%_%TIMESTAMP%.txt
set ARCH_PATH=D:\%ARCH_FILE%

echo Dang xuat cau truc thu muc...
echo. > "%ARCH_PATH%"
echo ============================================================ >> "%ARCH_PATH%"
echo KIEN TRUC PHAN MEM KE TOAN PRO v%VERSION% >> "%ARCH_PATH%"
echo Ngay xuat: %date% %time% >> "%ARCH_PATH%"
echo ============================================================ >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"

:: 1. CẤU TRÚC THƯ MỤC
echo [1. Cau truc thu muc] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
powershell -Command "& {
    $path = 'D:\ke_toan_pro_v3'
    $exclude = @('__pycache__', 'build', 'dist')
    Get-ChildItem -Path $path -Directory | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
        Add-Content -Path '%ARCH_PATH%' -Value ('  +---' + $_.Name)
        $subDirs = Get-ChildItem -Path $_.FullName -Directory -ErrorAction SilentlyContinue | Where-Object { $exclude -notcontains $_.Name }
        $subDirs | ForEach-Object {
            Add-Content -Path '%ARCH_PATH%' -Value ('  |   +---' + $_.Name)
        }
    }
}" 2>nul

:: 2. DANH SÁCH FILE PYTHON THEO THƯ MỤC
echo. >> "%ARCH_PATH%"
echo [2. Thong ke file Python theo thu muc] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
powershell -Command "& {
    $path = 'D:\ke_toan_pro_v3'
    $exclude = @('__pycache__', 'build', 'dist')
    Get-ChildItem -Path $path -Directory | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
        $count = (Get-ChildItem -Path $_.FullName -Recurse -Filter '*.py' -ErrorAction SilentlyContinue).Count
        Add-Content -Path '%ARCH_PATH%' -Value ('  ' + $_.Name + ': ' + $count + ' file')
    }
}" 2>nul

:: 3. CÁC MODULE QUAN TRỌNG
echo. >> "%ARCH_PATH%"
echo [3. Cac module quan trong] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"

echo --- Core / Security --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\core" (
    dir /b "D:\ke_toan_pro_v3\core\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Models --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\models" (
    dir /b "D:\ke_toan_pro_v3\models\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Views --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\views" (
    dir /b "D:\ke_toan_pro_v3\views\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Controllers --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\controllers" (
    dir /b "D:\ke_toan_pro_v3\controllers\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Services --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\services" (
    dir /b "D:\ke_toan_pro_v3\services\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Utils --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\utils" (
    dir /b "D:\ke_toan_pro_v3\utils\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- UI --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\ui" (
    dir /b "D:\ke_toan_pro_v3\ui\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

echo --- Reports (MOI) --- >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\reports" (
    dir /b "D:\ke_toan_pro_v3\reports\*.py" 2>nul >> "%ARCH_PATH%"
) else ( echo   (Khong co) >> "%ARCH_PATH%" )
echo. >> "%ARCH_PATH%"

:: 4. CẤU HÌNH VÀ DỮ LIỆU
echo. >> "%ARCH_PATH%"
echo [4. File cau hinh] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\*.json" dir /b "D:\ke_toan_pro_v3\*.json" 2>nul >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\*.config" dir /b "D:\ke_toan_pro_v3\*.config" 2>nul >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\*.md" dir /b "D:\ke_toan_pro_v3\*.md" 2>nul >> "%ARCH_PATH%"
echo    version.txt >> "%ARCH_PATH%"
echo    requirements.txt >> "%ARCH_PATH%"

:: 5. CẤU TRÚC DATABASE
echo. >> "%ARCH_PATH%"
echo [5. Cau truc Database] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\ke_toan_data\ke_toan.db" (
    sqlite3 "D:\ke_toan_pro_v3\ke_toan_data\ke_toan.db" ".tables" 2>nul >> "%ARCH_PATH%"
) else (
    echo Khong tim thay database >> "%ARCH_PATH%"
)

:: 6. THỐNG KÊ TỔNG HỢP
echo. >> "%ARCH_PATH%"
echo [6. Thong ke tong hop] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"

set COUNT=0
for /r "D:\ke_toan_pro_v3" %%f in (*.py) do (
    echo %%f | findstr /i "__pycache__" >nul
    if errorlevel 1 set /a COUNT+=1
)
echo So luong file .py: %COUNT% >> "%ARCH_PATH%"

powershell -Command "& {
    $size = (Get-ChildItem -Path 'D:\ke_toan_pro_v3' -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike '*__pycache__*' } | Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Add-Content -Path '%ARCH_PATH%' -Value ('Tong dung luong: ' + $sizeMB + ' MB')
}" 2>nul

:: 7. DEPENDENCIES
echo. >> "%ARCH_PATH%"
echo [7. Dependencies] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
if exist "D:\ke_toan_pro_v3\requirements.txt" (
    type "D:\ke_toan_pro_v3\requirements.txt" >> "%ARCH_PATH%" 2>nul
) else (
    echo Khong tim thay requirements.txt >> "%ARCH_PATH%"
)

:: 8. CÁC CLASS CHÍNH
echo. >> "%ARCH_PATH%"
echo [8. Cac class chinh phat hien] >> "%ARCH_PATH%"
echo. >> "%ARCH_PATH%"
powershell -Command "& {
    $path = 'D:\ke_toan_pro_v3'
    $classes = Get-ChildItem -Path $path -Recurse -Filter '*.py' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike '*__pycache__*' } | ForEach-Object {
        Select-String -Path $_.FullName -Pattern '^class\s+(\w+)' -AllMatches | ForEach-Object { $_.Matches.Groups[1].Value }
    }
    $classes | Select-Object -First 30 | Sort-Object | ForEach-Object {
        Add-Content -Path '%ARCH_PATH%' -Value ('  - ' + $_)
    }
}" 2>nul

echo. >> "%ARCH_PATH%"
echo ============================================================ >> "%ARCH_PATH%"
echo HOAN TAT XUAT KIEN TRUC >> "%ARCH_PATH%"
echo ============================================================ >> "%ARCH_PATH%"

echo.
echo ============================================================
echo XUAT FILE KIEN TRUC THANH CONG!
echo ============================================================
echo   File: %ARCH_PATH%
echo.
explorer /select,"%ARCH_PATH%"
if "%1"=="from_build" goto :eof
pause
goto :menu

:: ============================================================
::  FULL BUILD
:: ============================================================
:full_build
echo.
echo ============================================================
echo BUILD KE TOAN PRO v%VERSION% - %TIMESTAMP%
echo ============================================================
echo.

:: Xóa cache PyInstaller
echo Dang xoa cache PyInstaller...
if exist "%LOCALAPPDATA%\pyinstaller" rmdir /s /q "%LOCALAPPDATA%\pyinstaller"
if exist "%TEMP%\pyinstaller" rmdir /s /q "%TEMP%\pyinstaller"
if exist "%USERPROFILE%\.pyinstaller" rmdir /s /q "%USERPROFILE%\.pyinstaller"
echo Da xoa cache PyInstaller

:: 1. Dọn dẹp
tasklist /FI "IMAGENAME eq PhanMemKeToan.exe" 2>NUL | find /I "PhanMemKeToan.exe" >NUL
if not errorlevel 1 (
    echo Dang dong PhanMemKeToan.exe...
    taskkill /F /IM "PhanMemKeToan.exe" >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)
:: === BAO VE DU LIEU ADMIN TRUOC KHI XOA DIST ===
set ADMIN_DATA_BACKUP=%TEMP%\ke_toan_admin_data_backup
if exist "%ADMIN_DATA_BACKUP%" rmdir /s /q "%ADMIN_DATA_BACKUP%"

set IS_ADMIN_BUILD=0
if exist "dist\admin.key" set IS_ADMIN_BUILD=1
if exist "dist\ke_toan_data\ke_toan.db" (
    if %IS_ADMIN_BUILD%==0 (
        for /f %%c in ('sqlite3 "dist\ke_toan_data\ke_toan.db" "SELECT COUNT(*) FROM customers;" 2^>nul') do (
            if %%c GTR 0 set IS_ADMIN_BUILD=1
        )
    )
)

if %IS_ADMIN_BUILD%==1 (
    echo [BAO VE] Phat hien du lieu ADMIN. Dang sao luu...
    mkdir "%ADMIN_DATA_BACKUP%"
    xcopy "dist\ke_toan_data\*" "%ADMIN_DATA_BACKUP%\" /E /I /H /Y /Q >nul
    if exist "dist\admin.key" copy /Y "dist\admin.key" "%ADMIN_DATA_BACKUP%\_admin.key" >nul
    echo [OK] Da sao luu xong.
) else (
    echo [INFO] Khong phat hien admin, xoa dist binh thuong.
)
:: ================================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

:: 2. Build EXE
echo Dang build EXE (3-5 phut)...

:: ── Sinh changelog tự động từ git log ──────────────────────
echo Dang sinh changelog tu git log...
python generate_changelog.py version.json
if errorlevel 1 (
    echo    Giu nguyen changelog cu, tiep tuc build...
)
pyinstaller --onefile --windowed --name "PhanMemKeToan" --icon="icon.ico" ^
    --add-data "ui;ui" --add-data "models;models" --add-data "services;services" --add-data "utils;utils" --add-data "views;views" ^
    --add-data "reports;reports" --add-data "ai;ai" --add-data "config.py;." --add-data "data_config.py;." --add-data "data_path.txt;." --add-data "version.txt;." --add-data "icon.ico;." ^
    --add-data "ACB.jpeg;." --add-data "configs;configs" ^
    --add-data "client_secrets.json;." ^
    main.py

:: === SAO CHÉP MODEL EASYOCR VÀO DIST ===
echo Dang sao chep model easyocr vao dist...
if exist copy_easyocr_models.py (
    python copy_easyocr_models.py
    if errorlevel 1 (
        echo WARNING: Khong the copy model easyocr, tiep tuc build...
    )
) else (
    echo WARNING: Khong tim thay copy_easyocr_models.py, tiep tuc build...
)

:: 3. Tạo dist (CẢI TIẾN: BẢO VỆ DỮ LIỆU THỰC TẾ TRONG DIST)
set DIST_DIR=dist
echo Dang kiem tra va bao ve du lieu trong dist...

:: Tạo các thư mục chức năng nếu chưa có
mkdir "%DIST_DIR%\backup" 2>nul
mkdir "%DIST_DIR%\exports" 2>nul
mkdir "%DIST_DIR%\logs" 2>nul
mkdir "%DIST_DIR%\assets" 2>nul
mkdir "%DIST_DIR%\reports" 2>nul

:: LOGIC BẢO VE DU LIEU ADMIN (Restore sau khi dist moi duoc tao)
if %IS_ADMIN_BUILD%==1 (
    if exist "%ADMIN_DATA_BACKUP%" (
        echo [RESTORE] Dang phuc hoi du lieu ADMIN vao dist moi...
        mkdir "%DIST_DIR%\ke_toan_data" 2>nul
        xcopy "%ADMIN_DATA_BACKUP%\*" "%DIST_DIR%\ke_toan_data\" /E /I /H /Y /Q >nul
        if exist "%ADMIN_DATA_BACKUP%\_admin.key" (
            copy /Y "%ADMIN_DATA_BACKUP%\_admin.key" "%DIST_DIR%\admin.key" >nul
        )
        echo [OK] Du lieu Quan ly Ban quyen NGUYEN VEN.
        rmdir /s /q "%ADMIN_DATA_BACKUP%" 2>nul
    )
) else (
    if exist "%DIST_DIR%\ke_toan_data\ke_toan.db" (
        echo [XAC NHAN] Da thay du lieu trong dist. Bo qua de bao ve.
    ) else (
        echo [INFO] Chua co du lieu. Dang khoi tao tu nguon goc...
        mkdir "%DIST_DIR%\ke_toan_data" 2>nul
        if exist "ke_toan_data" (
            xcopy "ke_toan_data" "%DIST_DIR%\ke_toan_data\" /E /I /H /Y /Q >nul
            echo Da copy du lieu mau vao dist\ke_toan_data.
        ) else (
            echo WARN: Khong tim thay ke_toan_data goc.
        )
    )
)

:: Cập nhật các file thực thi và cấu hình (luôn cập nhật file mới nhất sau build)
copy /Y "dist\PhanMemKeToan.exe" "%DIST_DIR%\" >nul
copy /Y "icon.ico" "%DIST_DIR%\" >nul
copy /Y "ACB.jpeg" "%DIST_DIR%\" >nul
rem if exist "rclone.exe" copy /Y "rclone.exe" "%DIST_DIR%\" >nul
if exist "TERMS_OF_USE.md" copy /Y "TERMS_OF_USE.md" "%DIST_DIR%\" >nul
if exist "PRIVACY_POLICY.md" copy /Y "PRIVACY_POLICY.md" "%DIST_DIR%\" >nul
echo .\ke_toan_data > "%DIST_DIR%\data_path.txt"
echo %VERSION% > "%DIST_DIR%\version.txt"

:: Tạo file chạy nhanh và thông tin hỗ trợ
(
echo @echo off
echo title KE TOAN PRO v%VERSION%
echo cd /d "%%~dp0"
echo start "" "PhanMemKeToan.exe"
) > "%DIST_DIR%\ChayPhanMem.bat"

(
echo PHAN MEM KE TOAN PRO v%VERSION%
echo.
echo HUONG DAN: Chay "ChayPhanMem.bat"
echo HO TRO: Zalo 0982493474
) > "%DIST_DIR%\README.txt"

echo Da tao/cap nhat dist thanh cong (Du lieu an toan).
:: 4a. Tự động tạo ke_toan_empty.db nếu chưa có
if not exist "ke_toan_data\ke_toan_empty.db" (
    echo Dang tao ke_toan_empty.db...
    python tao_empty_db.py
    if errorlevel 1 (
        echo [CANH BAO] Khong tao duoc ke_toan_empty.db
    )
) else (
    echo [OK] Da co ke_toan_empty.db, bo qua.
)
:: 4. Tạo gói khách
set PACKAGE_NAME=PhanMemKeToan_Pro_v%VERSION%_%TIMESTAMP%
set PACKAGE_PATH=D:\%PACKAGE_NAME%
echo Dang tao thu muc dong goi cho khach: %PACKAGE_PATH%
if exist "%PACKAGE_PATH%" rmdir /s /q "%PACKAGE_PATH%"
mkdir "%PACKAGE_PATH%"
xcopy "%DIST_DIR%" "%PACKAGE_PATH%\" /E /I /H /Y /Q >nul

if exist "%PACKAGE_PATH%\ke_toan_data" (
    rmdir /s /q "%PACKAGE_PATH%\ke_toan_data"
    mkdir "%PACKAGE_PATH%\ke_toan_data"
    :: Tao DB rong (chi cau truc, khong co du lieu that) cho khach
    if exist "ke_toan_data\ke_toan_empty.db" (
        copy /Y "ke_toan_data\ke_toan_empty.db" "%PACKAGE_PATH%\ke_toan_data\ke_toan.db" >nul
        echo Da tao DB rong cho khach tu ke_toan_empty.db.
    ) else (
        echo [CANH BAO] Khong tim thay ke_toan_empty.db - App khach co the loi khi khoi dong!
        echo Hay tao file ke_toan_data\ke_toan_empty.db truoc khi dong goi.
    )
    echo Da xoa du lieu that trong goi khach.
)
if exist "%PACKAGE_PATH%\admin.key" del "%PACKAGE_PATH%\admin.key"

:: 5. Tạo ZIP
set ZIP_FILE=D:\%PACKAGE_NAME%.zip
if exist "%ZIP_FILE%" del "%ZIP_FILE%"
powershell -Command "Compress-Archive -Path '%PACKAGE_PATH%\*' -DestinationPath '%ZIP_FILE%' -Force"
if exist "%ZIP_FILE%" ( echo Da tao ZIP: %ZIP_FILE% ) else ( echo LOI: Khong tao duoc ZIP & pause )

:: 6. Backup (ĐÃ TỐI ƯU: ĐẢM BẢO COPY ĐỦ FILE MÃ NGUỒN VÀ DỮ LIỆU)
set BACKUP_DIR=D:\BACKUP_KE_TOAN_PRO_%TIMESTAMP%
if exist "%BACKUP_DIR%" rmdir /s /q "%BACKUP_DIR%"
mkdir "%BACKUP_DIR%\source_code"
mkdir "%BACKUP_DIR%\real_data_from_dist"

echo Dang backup ma nguon gốc...
:: Sử dụng robocopy để loại bỏ thư mục rác thông minh hơn xcopy
robocopy "D:\ke_toan_pro_v3" "%BACKUP_DIR%\source_code" /E /R:1 /W:1 /XD build dist __pycache__ .git /XF *.spec /MT:8

:: 2. Backup RIÊNG dữ liệu thực tế từ DIST (Bảo vệ con số 38.960.000đ)
if exist "%DIST_DIR%\ke_toan_data\ke_toan.db" (
    echo [QUAN TRONG] Dang sao luu du lieu thuc te tu thu muc DIST...
    :: Thêm dấu * sau đường dẫn nguồn để đảm bảo lấy hết file bên trong
    xcopy "%DIST_DIR%\ke_toan_data\*" "%BACKUP_DIR%\real_data_from_dist\" /E /I /H /Y /Q
    echo Da backup du lieu lam viec hien tai vao backup.
)

echo Hoan tat backup tai: %BACKUP_DIR%

:: 7. Xuất kiến trúc
call :export_architecture from_build

echo.
echo ============================================================
echo HOAN TAT!
echo ============================================================
echo   Dist: %CD%\dist
echo   Goi khach: %PACKAGE_PATH%
echo   File ZIP: %ZIP_FILE%
echo   Backup: %BACKUP_DIR%
echo   Kien truc: %ARCH_PATH%
echo.
explorer /select,"%ZIP_FILE%"
pause
goto :menu

:: ============================================================
::  CHI BUILD EXE
:: ============================================================
:build_only
echo.
echo ============================================================
echo CHI BUILD EXE (KHONG TAO DIST, KHONG DONG GOI)
echo ============================================================
tasklist /FI "IMAGENAME eq PhanMemKeToan.exe" 2>NUL | find /I "PhanMemKeToan.exe" >NUL
if not errorlevel 1 (
    taskkill /F /IM "PhanMemKeToan.exe" >NUL 2>&1
    timeout /t 2 /nobreak >NUL
)
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
echo Dang build EXE...
:: === CẬP NHẬT PHIÊN BẢN VÀO CONFIG TRƯỚC KHI BUILD ===
echo Cap nhat VERSION=%VERSION% vao config.py...
powershell -Command "(Get-Content config.py) -replace 'VERSION = \".*\"', 'VERSION = \"%VERSION%\"' | Set-Content config.py"
echo Dang build EXE...

:: ── Sinh changelog tự động từ git log ──────────────────────
echo Dang sinh changelog tu git log...
python generate_changelog.py version.json
if errorlevel 1 (
    echo    Giu nguyen changelog cu, tiep tuc build...
)

pyinstaller --onefile --windowed --name "PhanMemKeToan" --icon="icon.ico" ^
    --add-data "ui;ui" ^
    --add-data "models;models" ^
    --add-data "services;services" ^
    --add-data "utils;utils" ^
    --add-data "views;views" ^
    --add-data "reports;reports" ^
    --add-data "ai;ai" ^
    --add-data "ke_toan_data;ke_toan_data" ^
    --add-data "configs;configs" ^
    --add-data "config.py;." ^
    --add-data "data_config.py;." ^
    --add-data "data_path.txt;." ^
    --add-data "version.txt;." ^
    --add-data "icon.ico;." ^
    --add-data "ACB.jpeg;." ^
    --add-data "client_secrets.json;." ^
    main.py

:: === SAO CHÉP MODEL EASYOCR VÀO DIST ===
echo Dang sao chep model easyocr vao dist...
if exist copy_easyocr_models.py (
    python copy_easyocr_models.py
    if errorlevel 1 (
        echo WARNING: Khong the copy model easyocr
    )
) else (
    echo WARNING: Khong tim thay copy_easyocr_models.py
)
pause
goto :menu

:: ============================================================
::  TẠO LICENSE
:: ============================================================
:create_license
echo.
echo ============================================================
echo TAO LICENSE KEY CHO KHACH HANG
echo ============================================================
if not exist "create_license.py" (
    echo LOI: Khong tim thay file create_license.py
    pause
    goto :menu
)
python create_license.py
echo.
pause >nul
goto :menu