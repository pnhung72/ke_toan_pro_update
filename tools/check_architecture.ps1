# ============================================================================
# KIỂM TRA KIẾN TRÚC DỰ ÁN - PHẦN MỀM KẾ TOÁN PRO V3
# Chạy tại: D:\ke_toan_pro_v3
# ============================================================================

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "         KIỂM TRA KIẾN TRÚC DỰ ÁN - PHẦN MỀM KẾ TOÁN PRO V3" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan

# Đặt đường dẫn gốc
$projectRoot = "D:\ke_toan_pro_v3"
Set-Location $projectRoot

# ============================================================================
# 1. CẤU TRÚC THƯ MỤC HIỆN TẠI
# ============================================================================
Write-Host "1. CẤU TRÚC THƯ MỤC HIỆN TẠI" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# Hiển thị cây thư mục (cấp độ 3)
if (Get-Command tree -ErrorAction SilentlyContinue) {
    tree /F /A | Select-Object -First 100
} else {
    Get-ChildItem -Directory | ForEach-Object {
        Write-Host "+---$($_.Name)" -ForegroundColor Green
        Get-ChildItem $_.FullName -Directory | ForEach-Object {
            Write-Host "|   +---$($_.Name)" -ForegroundColor DarkGreen
        }
    }
}

# ============================================================================
# 2. KIỂM TRA THƯ MỤC THEO KIẾN TRÚC MỤC TIÊU
# ============================================================================
Write-Host "`n2. KIỂM TRA THƯ MỤC THEO KIẾN TRÚC MỤC TIÊU" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$requiredFolders = @(
    "config",
    "core",
    "core\database",
    "core\security", 
    "core\utils",
    "models",
    "views",
    "views\tabs",
    "views\dialogs",
    "controllers",
    "tests",
    "tests\unit",
    "tests\integration",
    "resources",
    "resources\icons",
    "resources\templates",
    "resources\locale"
)

$missingFolders = @()
foreach ($folder in $requiredFolders) {
    if (Test-Path $folder) {
        Write-Host "  ✅ $folder" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $folder (thiếu)" -ForegroundColor Red
        $missingFolders += $folder
    }
}

# ============================================================================
# 3. THỐNG KÊ FILE THEO LOẠI
# ============================================================================
Write-Host "`n3. THỐNG KÊ FILE THEO LOẠI" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$extensions = @{
    ".py" = "Python";
    ".ui" = "Qt Designer";
    ".json" = "JSON";
    ".txt" = "Text";
    ".md" = "Markdown";
    ".sql" = "SQL";
    ".html" = "HTML";
    ".css" = "CSS";
    ".js" = "JavaScript";
}

foreach ($ext in $extensions.Keys) {
    $count = (Get-ChildItem -Recurse -Filter "*$ext" -ErrorAction SilentlyContinue).Count
    if ($count -gt 0) {
        Write-Host "  $ext : $count file ($($extensions[$ext]))" -ForegroundColor Cyan
    }
}

# Tổng số file
$totalFiles = (Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue).Count
Write-Host "`n  📦 Tổng số file: $totalFiles" -ForegroundColor Magenta

# ============================================================================
# 4. TOP 10 FILE LỚN NHẤT (DÒNG CODE)
# ============================================================================
Write-Host "`n4. TOP 10 FILE LỚN NHẤT (DÒNG CODE)" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$pythonFiles = Get-ChildItem -Recurse -Filter "*.py" -ErrorAction SilentlyContinue
$fileLines = @()

foreach ($file in $pythonFiles) {
    try {
        $lines = (Get-Content $file.FullName -ErrorAction SilentlyContinue).Count
        $fileLines += [PSCustomObject]@{
            Path = $file.FullName.Replace($projectRoot, "").TrimStart("\")
            Lines = $lines
        }
    } catch {}
}

$fileLines | Sort-Object Lines -Descending | Select-Object -First 10 | ForEach-Object {
    Write-Host "  $($_.Lines) dòng : $($_.Path)" -ForegroundColor DarkYellow
}

# ============================================================================
# 5. KIỂM TRA LỖI CẤU TRÚC
# ============================================================================
Write-Host "`n5. KIỂM TRA LỖI CẤU TRÚC" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

# 5a. Kiểm tra file quá lớn (>1000 dòng)
Write-Host "  📏 File quá lớn (>1000 dòng):" -ForegroundColor Cyan
$largeFiles = $fileLines | Where-Object { $_.Lines -gt 1000 }
if ($largeFiles) {
    $largeFiles | ForEach-Object {
        Write-Host "     ⚠️ $($_.Lines) dòng - $($_.Path)" -ForegroundColor Red
    }
} else {
    Write-Host "     ✅ Không có file nào >1000 dòng" -ForegroundColor Green
}

# 5b. Kiểm tra trùng lặp code (so sánh file cùng tên)
Write-Host "`n  🔄 Kiểm tra trùng lặp file:" -ForegroundColor Cyan
$duplicateNames = Get-ChildItem -Recurse -Filter "*.py" | Group-Object Name | Where-Object { $_.Count -gt 1 }
if ($duplicateNames) {
    $duplicateNames | ForEach-Object {
        Write-Host "     ⚠️ File '$($_.Name)' xuất hiện $($_.Count) lần" -ForegroundColor Red
        $_.Group | ForEach-Object {
            Write-Host "        - $($_.Directory)" -ForegroundColor DarkRed
        }
    }
} else {
    Write-Host "     ✅ Không phát hiện file trùng tên" -ForegroundColor Green
}

# 5c. Kiểm tra import vòng tròn (cơ bản)
Write-Host "`n  🔗 Kiểm tra import:" -ForegroundColor Cyan
$importIssues = 0
foreach ($file in $pythonFiles | Select-Object -First 50) {
    $content = Get-Content $file.FullName -ErrorAction SilentlyContinue
    if ($content -match "from \.\.|import \.\\.") {
        Write-Host "     ⚠️ Relative import sâu: $($file.Name)" -ForegroundColor Yellow
        $importIssues++
    }
}
if ($importIssues -eq 0) {
    Write-Host "     ✅ Không phát hiện vấn đề import đặc biệt" -ForegroundColor Green
}

# ============================================================================
# 6. KIỂM TRA MODULE CORE
# ============================================================================
Write-Host "`n6. KIỂM TRA MODULE CORE" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$coreChecks = @{
    "database" = "Có file nào chứa 'database', 'sql', 'connection' không?";
    "security" = "Có file nào chứa 'encrypt', 'hash', 'password', 'auth' không?";
    "utils" = "Có file nào chứa 'helper', 'utils', 'common' không?";
}

foreach ($check in $coreChecks.Keys) {
    $found = Get-ChildItem -Recurse -Filter "*.py" | Select-String -Pattern $check -CaseSensitive:$false | Select-Object -First 3
    if ($found) {
        Write-Host "  ✅ $check : Tìm thấy module liên quan" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $check : Chưa tìm thấy module" -ForegroundColor Red
    }
}

# ============================================================================
# 7. KIỂM TRA TEST
# ============================================================================
Write-Host "`n7. KIỂM TRA TEST" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$testFiles = Get-ChildItem -Recurse -Filter "test_*.py" -ErrorAction SilentlyContinue
$testCount = $testFiles.Count
if ($testCount -gt 0) {
    Write-Host "  ✅ Có $testCount file test" -ForegroundColor Green
} else {
    Write-Host "  ❌ Không có file test nào" -ForegroundColor Red
}

# ============================================================================
# 8. KIỂM TRA TÀI NGUYÊN (RESOURCES)
# ============================================================================
Write-Host "`n8. KIỂM TRA TÀI NGUYÊN" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$resourceTypes = @{
    "icons" = "*.png", "*.ico", "*.svg";
    "templates" = "*.html", "*.template";
    "locale" = "*.po", "*.mo", "*.qm";
}

foreach ($resType in $resourceTypes.Keys) {
    $found = Get-ChildItem -Recurse -Include ($resourceTypes[$resType] -split ", ") -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "  ✅ $resType : $($found.Count) file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $resType : Không tìm thấy" -ForegroundColor Red
    }
}

# ============================================================================
# 9. ĐÁNH GIÁ TỔNG THỂ
# ============================================================================
Write-Host "`n9. ĐÁNH GIÁ TỔNG THỂ" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

$score = 0
$maxScore = 10

# Chấm điểm
if ($missingFolders.Count -eq 0) { $score += 3 }
elseif ($missingFolders.Count -le 5) { $score += 1 }

if ($largeFiles.Count -eq 0) { $score += 2 }
elseif ($largeFiles.Count -le 2) { $score += 1 }

if ($testCount -gt 0) { $score += 2 }
if (Test-Path "core") { $score += 2 }
if (Test-Path "controllers") { $score += 1 }

$percentage = ($score / $maxScore) * 100

if ($percentage -ge 80) {
    $rating = "🟢 TỐT"
    $color = "Green"
} elseif ($percentage -ge 50) {
    $rating = "🟡 TRUNG BÌNH - Cần cải thiện"
    $color = "Yellow"
} else {
    $rating = "🔴 KÉM - Cần tái cấu trúc ngay"
    $color = "Red"
}

Write-Host "  Điểm kiến trúc: $score / $maxScore ($([math]::Round($percentage,1))%)" -ForegroundColor $color
Write-Host "  Đánh giá: $rating" -ForegroundColor $color

# ============================================================================
# 10. KHUYẾN NGHỊ
# ============================================================================
Write-Host "`n10. KHUYẾN NGHỊ" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Gray

if ($missingFolders.Count -gt 0) {
    Write-Host "  🔧 Tạo các thư mục còn thiếu:" -ForegroundColor Cyan
    foreach ($folder in $missingFolders | Select-Object -First 5) {
        Write-Host "     mkdir `"$folder`" 2>nul" -ForegroundColor White
    }
}

if ($largeFiles.Count -gt 0) {
    Write-Host "`n  📦 Tách các file lớn thành module nhỏ hơn" -ForegroundColor Cyan
    Write-Host "     - Sử dụng nguyên tắc Single Responsibility" -ForegroundColor White
    Write-Host "     - Mỗi class/file chỉ làm một việc" -ForegroundColor White
}

if ($testCount -eq 0) {
    Write-Host "`n  🧪 Thiết lập pytest và viết unit test" -ForegroundColor Cyan
    Write-Host "     pip install pytest pytest-qt" -ForegroundColor White
}

Write-Host "`n============================================================================" -ForegroundColor Cyan
Write-Host "                    HOÀN THÀNH KIỂM TRA" -ForegroundColor Cyan
Write-Host "============================================================================`n" -ForegroundColor Cyan