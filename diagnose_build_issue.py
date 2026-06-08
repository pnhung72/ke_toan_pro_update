import os
import shutil
import subprocess
import sys

PROJECT_PATH = r"D:\ke_toan_pro_v3"
BUILD_DIR = os.path.join(PROJECT_PATH, "build")
DIST_DIR = os.path.join(PROJECT_PATH, "dist")

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_dirs():
    """Kiểm tra trạng thái thư mục build/dist"""
    print_header("KIỂM TRA THƯ MỤC BUILD/DIST")
    
    build_exists = os.path.exists(BUILD_DIR)
    dist_exists = os.path.exists(DIST_DIR)
    
    print(f"📁 Thư mục build: {'TỒN TẠI' if build_exists else 'KHÔNG CÓ'}")
    print(f"📁 Thư mục dist:  {'TỒN TẠI' if dist_exists else 'KHÔNG CÓ'}")
    
    if build_exists:
        try:
            size = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, dirnames, filenames in os.walk(BUILD_DIR) for f in filenames) / (1024 * 1024)
            print(f"   - Kích thước build: {size:.2f} MB")
        except:
            pass
    
    if dist_exists and os.path.exists(os.path.join(DIST_DIR, "PhanMemKeToan.exe")):
        exe_size = os.path.getsize(os.path.join(DIST_DIR, "PhanMemKeToan.exe")) / (1024 * 1024)
        print(f"   - Kích thước EXE: {exe_size:.2f} MB")
    
    return build_exists, dist_exists

def clean_build_dist():
    """Xóa thư mục build và dist"""
    print_header("XÓA THƯ MỤC BUILD/DIST")
    
    for dir_path, name in [(BUILD_DIR, "build"), (DIST_DIR, "dist")]:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Đã xóa thư mục {name}/")
            except Exception as e:
                print(f"❌ Không thể xóa {name}/: {e}")
        else:
            print(f"⚠️ Thư mục {name}/ không tồn tại")

def run_python_main():
    """Chạy python main.py và kiểm tra kết quả"""
    print_header("CHẠY PYTHON MAIN.PY (SOURCE CODE)")
    
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_PATH,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        print("✅ python main.py CHẠY THÀNH CÔNG!")
        return True
    else:
        print(f"❌ python main.py THẤT BẠI! Mã lỗi: {result.returncode}")
        if result.stderr:
            print(f"\n📋 Lỗi chi tiết:\n{result.stderr[:500]}")
        return False

def run_build():
    """Chạy build_release.bat"""
    print_header("CHẠY BUILD_RELEASE.BAT")
    
    bat_path = os.path.join(PROJECT_PATH, "build_release.bat")
    if not os.path.exists(bat_path):
        print("❌ Không tìm thấy build_release.bat!")
        return False
    
    # Chạy build với lựa chọn 2 (chỉ build EXE)
    proc = subprocess.Popen(
        [bat_path],
        cwd=PROJECT_PATH,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = proc.communicate(input="2\n", timeout=180)
        if proc.returncode == 0:
            print("✅ BUILD THÀNH CÔNG!")
            return True
        else:
            print(f"❌ BUILD THẤT BẠI! Mã lỗi: {proc.returncode}")
            return False
    except subprocess.TimeoutExpired:
        proc.kill()
        print("❌ BUILD QUÁ THỜI GIAN!")
        return False

def compare_exe_versions():
    """So sánh EXE cũ và mới nếu có"""
    print_header("SO SÁNH EXE")
    
    old_exe = os.path.join(DIST_DIR, "PhanMemKeToan.exe")
    if os.path.exists(old_exe):
        mtime = os.path.getmtime(old_exe)
        from datetime import datetime
        print(f"📅 EXE hiện tại được tạo lúc: {datetime.fromtimestamp(mtime)}")
        
        # Kiểm tra file copy_easyocr_models.py có được gọi không
        copy_script = os.path.join(PROJECT_PATH, "copy_easyocr_models.py")
        if os.path.exists(copy_script):
            print(f"✅ File copy_easyocr_models.py tồn tại")
        else:
            print(f"❌ THIẾU file copy_easyocr_models.py - ĐÂY CÓ THỂ LÀ NGUYÊN NHÂN!")

def check_copy_script():
    """Kiểm tra file copy_easyocr_models.py"""
    print_header("KIỂM TRA COPY_EASYOCR_MODELS.PY")
    
    script_path = os.path.join(PROJECT_PATH, "copy_easyocr_models.py")
    if os.path.exists(script_path):
        print("✅ File tồn tại")
        with open(script_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "shutil.copytree" in content:
                print("✅ Nội dung hợp lệ")
        return True
    else:
        print("❌ FILE KHÔNG TỒN TẠI!")
        print("   Đây là nguyên nhân build thất bại!")
        return False

def main():
    print("=" * 70)
    print("  🔬 CHẨN ĐOÁN NGUYÊN NHÂN LỖI BUILD")
    print("=" * 70)
    
    # 1. Kiểm tra file copy script
    has_copy_script = check_copy_script()
    
    # 2. Kiểm tra trạng thái hiện tại
    build_exists, dist_exists = check_dirs()
    
    # 3. Nếu có build/dist, xóa và test source code
    if build_exists or dist_exists:
        print("\n⚠️ Phát hiện build/dist cũ!")
        choice = input("   Có muốn xóa để kiểm tra python main.py? (y/n): ")
        if choice.lower() == 'y':
            clean_build_dist()
            
            # 4. Chạy python main.py
            source_ok = run_python_main()
            if source_ok:
                print("\n🎉 KẾT LUẬN: SOURCE CODE HOÀN TOÀN TỐT!")
                print("   Vấn đề nằm trong QUÁ TRÌNH BUILD hoặc THIẾU FILE copy_easyocr_models.py")
    
    # 5. Kiểm tra file copy script
    if not has_copy_script:
        print("\n" + "=" * 70)
        print("  🚨 NGUYÊN NHÂN CHÍNH ĐÃ ĐƯỢC XÁC ĐỊNH!")
        print("=" * 70)
        print("""
        ❌ THIẾU FILE: copy_easyocr_models.py
        
        File này bị xóa trong quá trình dọn rác.
        Khi build, lệnh 'python copy_easyocr_models.py' được gọi
        nhưng không tìm thấy file → BUILD THẤT BẠI!
        
        GIẢI PHÁP: Tạo lại file copy_easyocr_models.py
        """)
    else:
        print("\n" + "=" * 70)
        print("  ✅ KẾT LUẬN")
        print("=" * 70)
        print("""
        File copy_easyocr_models.py đã tồn tại.
        Nếu build vẫn lỗi, nguyên nhân có thể là:
        1. Model EasyOCR chưa được tải (chạy python main.py trước)
        2. Lỗi PyInstaller khi đóng gói (thử cài lại pyinstaller)
        3. Thiếu thư viện trong quá trình build
        """)
    
    print("\n" + "=" * 70)
    print("  KIỂM TRA HOÀN TẤT")
    print("=" * 70)

if __name__ == "__main__":
    main()