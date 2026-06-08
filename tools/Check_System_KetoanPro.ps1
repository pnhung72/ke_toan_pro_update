# 1. Thiết lập thông tin dự án
$ProjectName = "Kế Toán Pro - Audit"
$ProjectDir = Get-Location

Write-Host "--- BẮT ĐẦU KIỂM TRA HỆ SINH THÁI: $ProjectName ---" -ForegroundColor Cyan
Write-Host "Vị trí dự án: $ProjectDir"

# 2. Kiểm tra môi trường Python và các thư viện quan trọng
Write-Host "`n[1] Kiểm tra các thư viện hỗ trợ Thuế & Hóa đơn:" -ForegroundColor Yellow
$libraries = @("requests", "lxml", "pandas", "cryptography", "pyopenssl")
foreach ($lib in $libraries) {
    $check = pip show $lib | Select-String "Name:"
    if ($check) {
        Write-Host "[ OK ] $lib đã được cài đặt." -ForegroundColor Green
    } else {
        Write-Host "[ !! ] Thiếu thư viện: $lib" -ForegroundColor Red
    }
}

# 3. Quét cấu trúc Module hiện tại
Write-Host "`n[2] Tìm kiếm các thành phần liên quan đến Thuế/Hóa đơn:" -ForegroundColor Yellow
$searchTerms = @("invoice", "hoa_don", "thue", "tax", "api", "connect", "xml")
foreach ($term in $searchTerms) {
    $files = Get-ChildItem -Recurse -Include *.py | Select-String -Pattern $term -List
    if ($files) {
        Write-Host "-> Tìm thấy từ khóa '$term' trong các file: $($files.Filename -join ', ')" -ForegroundColor Gray
    }
}

# 4. Kiểm tra lỗi Import 'setup_fonts' từng gặp
Write-Host "`n[3] Kiểm tra file theme/font để đảm bảo ổn định:" -ForegroundColor Yellow
$themePath = Join-Path $ProjectDir "theme.py"
if (Test-Path $themePath) {
    $fontCheck = Select-String -Path $themePath -Pattern "setup_fonts"
    if ($fontCheck) {
        Write-Host "[ OK ] Đã tìm thấy định nghĩa 'setup_fonts' trong theme.py." -ForegroundColor Green
    } else {
        Write-Host "[ !! ] Cảnh báo: Không tìm thấy 'setup_fonts' trong theme.py." -ForegroundColor Red
    }
} else {
    Write-Host "[ ?? ] Không tìm thấy file theme.py trong thư mục gốc." -ForegroundColor Gray
}

Write-Host "`n--- HOÀN TẤT KIỂM TRA ---" -ForegroundColor Cyan
Write-Host "Vui lòng chụp ảnh hoặc copy kết quả này gửi lại để tôi nắm bắt tình hình!"