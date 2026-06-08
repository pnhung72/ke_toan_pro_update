# Định nghĩa đường dẫn
$sourceExe = "D:\ke_toan_pro_v3\dist\PhanMemKeToan.exe"
$sourceData = "D:\ke_toan_pro_v3\dist\ke_toan_data"
$destFolder = "D:\PhanMemKeToan_Pro_v3.0"
$batchFile = "D:\ke_toan_pro_v3\dist\ChayPhanMem.bat"
$iconFile = "D:\ke_toan_pro_v3\icon.ico"
$readmeFile = "D:\ke_toan_pro_v3\README.txt"

# Xóa thư mục đích nếu tồn tại
if (Test-Path $destFolder) {
    Remove-Item -Path $destFolder -Recurse -Force
}

# Tạo thư mục đích
New-Item -ItemType Directory -Path $destFolder -Force | Out-Null

# 1. Copy exe
if (Test-Path $sourceExe) {
    Copy-Item -Path $sourceExe -Destination $destFolder -Force
    Write-Host "Da copy PhanMemKeToan.exe"
} else {
    Write-Host "Khong tim thay file exe!" -ForegroundColor Red
    exit 1
}

# 2. Copy file batch
if (Test-Path $batchFile) {
    Copy-Item -Path $batchFile -Destination $destFolder -Force
    Write-Host "Da copy ChayPhanMem.bat"
} else {
    Write-Host "Khong tim thay ChayPhanMem.bat, bo qua" -ForegroundColor Yellow
}

# 3. Tạo thư mục dữ liệu MỚI (không copy dữ liệu cũ)
$newDataFolder = Join-Path $destFolder "ke_toan_data"
New-Item -ItemType Directory -Path $newDataFolder -Force | Out-Null
Write-Host "Da tao thu muc ke_toan_data MOI (khong chua du lieu cu)" -ForegroundColor Green

# 4. Tạo file database rỗng (không có dữ liệu cũ)
$emptyDbPath = Join-Path $newDataFolder "ke_toan.db"
if (Test-Path $emptyDbPath) {
    Remove-Item -Path $emptyDbPath -Force
}

# Kết nối tạo database rỗng với cấu trúc bảng
$connectionString = "Data Source=$emptyDbPath"
Add-Type -Path "C:\Program Files\System.Data.SQLite\2010\GAC\System.Data.SQLite.dll" -ErrorAction SilentlyContinue
if (-not (Get-Module -ListAvailable -Name System.Data.SQLite)) {
    # Nếu không có SQLite, tạo file rỗng và sẽ được khởi tạo khi chạy lần đầu
    New-Item -Path $emptyDbPath -ItemType File -Force | Out-Null
    Write-Host "Da tao file database rong (se duoc khoi tao khi chay lan dau)" -ForegroundColor Yellow
}

# 5. Tạo file cấu hình mặc định
$configFile = Join-Path $newDataFolder "app_config.json"
$defaultconfig = @{
    data_source = "invoices"
    auto_backup = $true
    backup_interval_hours = 24
} | ConvertTo-Json
Set-Content -Path $configFile -Value $defaultconfig -Encoding UTF8
Write-Host "Da tao file cau hinh mac dinh"

# 6. Tạo thư mục backup
$backupFolder = Join-Path $destFolder "backup"
New-Item -ItemType Directory -Path $backupFolder -Force | Out-Null
Write-Host "Da tao thu muc backup"

# 7. Copy icon
if (Test-Path $iconFile) {
    Copy-Item -Path $iconFile -Destination $destFolder -Force
    Write-Host "Da copy icon.ico"
}

# 8. Copy README
if (Test-Path $readmeFile) {
    Copy-Item -Path $readmeFile -Destination $destFolder -Force
    Write-Host "Da copy README.txt"
}

# 9. Xóa admin.key nếu có
$adminKeyFile = Join-Path $destFolder "admin.key"
if (Test-Path $adminKeyFile) {
    Remove-Item -Path $adminKeyFile -Force
    Write-Host "Da xoa admin.key (khong gui cho khach)" -ForegroundColor Yellow
}

# 10. Xóa license.key cũ nếu có
$oldLicenseKey = Join-Path $destFolder "license.key"
if (Test-Path $oldLicenseKey) {
    Remove-Item -Path $oldLicenseKey -Force
    Write-Host "Da xoa license.key cu (khach se kich hoat bang ma may moi)" -ForegroundColor Yellow
}

# 11. Xóa file trial.json cũ nếu có (reset thời gian dùng thử)
$trialFile = Join-Path $destFolder "trial.json"
if (Test-Path $trialFile) {
    Remove-Item -Path $trialFile -Force
    Write-Host "Da xoa file trial.json cu (reset thoi gian dung thu)" -ForegroundColor Yellow
}

# 12. Tạo file hướng dẫn kích hoạt bản quyền
$licenseGuide = Join-Path $destFolder "LICENSE_GUIDE.txt"
$guideContent = @"
========== HUONG DAN KICH HOAT BAN QUYEN ==========

1. Chay file PhanMemKeToan.exe
2. Man hinh se hien thi MA MAY (gom 64 ky tu)
3. Sao chep ma may va gui cho nha phat trien:
   - Email: pnhungc3nv@gmail.com
   - Zalo: 0982493474
4. Sau khi thanh toan, ban se nhan duoc file license.key
5. Dat file license.key vao CUNG THU MUC voi file PhanMemKeToan.exe
6. Khoi dong lai phan mem de kich hoat

========== THONG TIN LIEN HE ==========
Email: pnhungc3nv@gmail.com
Zalo: 0982493474

========== LUU Y ==========
- Lan dau chay, phan mem se tu dong tao database moi
- Ban duoc dung thu 30 ngay voi day du tinh nang
- Mua ban quyen de su dung vinh vien
"@
Set-Content -Path $licenseGuide -Value $guideContent -Encoding UTF8
Write-Host "Da tao file LICENSE_GUIDE.txt"

# 13. Tạo file thông báo reset dữ liệu
$resetNotice = Join-Path $destFolder "THONG_BAO_RESET_DU_LIEU.txt"
$resetContent = @"
========== THONG BAO ==========

Phan mem nay da duoc dong goi VOI DU LIEU MOI, KHONG CHUA DU LIEU CU.

- Tat ca du lieu giao dich, hoa don, khach hang da duoc xoa
- Database duoc tao moi hoan toan
- Thoi gian dung thu duoc reset ve 30 ngay

Khi chay lan dau, phan mem se tu dong khoi tao database rong.

Luu y: Day la phien ban danh cho khach hang moi.
"@
Set-Content -Path $resetNotice -Value $resetContent -Encoding UTF8
Write-Host "Da tao file THONG_BAO_RESET_DU_LIEU.txt"

Write-Host "`n=== THANH CONG ===" -ForegroundColor Green
Write-Host "Thu muc phan phoi da duoc tao tai: $destFolder"
Write-Host "DA XOA TOAN BO DU LIEU CU!" -ForegroundColor Green
Write-Host "Database duoc tao moi, khong chua thong tin cu" -ForegroundColor Green
Write-Host "`nBan co the nen thu muc nay va gui cho khach hang."