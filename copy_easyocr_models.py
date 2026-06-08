import os
import shutil
from pathlib import Path

def copy_easyocr_models():
    # Đường dẫn thư mục model của easyocr (trên máy bạn)
    source_dir = Path.home() / ".EasyOCR"
    if not source_dir.exists():
        print(f"⚠️ Không tìm thấy thư mục model easyocr tại: {source_dir}")
        print("   Vui lòng chạy chương trình bằng python main.py một lần để easyocr tự động tải model.")
        return False

    # Đường dẫn đích trong thư mục dist
    dist_dir = Path("dist") / ".EasyOCR"
    
    if dist_dir.exists():
        print(f"   Đang xóa thư mục cũ: {dist_dir}")
        shutil.rmtree(dist_dir)
    
    print(f"   Đang sao chép từ {source_dir} -> {dist_dir}")
    shutil.copytree(source_dir, dist_dir)
    print("✅ Đã sao chép thành công model easyocr vào thư mục dist.")
    return True

if __name__ == "__main__":
    print("📁 Đang sao chép model EasyOCR...")
    copy_easyocr_models()