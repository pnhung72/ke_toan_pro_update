# fix_version_ui.py
import os
import re

# Định nghĩa các thư mục cần quét sạch trong dự án của anh
TARGET_DIRS = ['ui', 'views', 'controllers', 'utils', '.']
OLD_TEXT = "Quản lý bản quyền - Hệ thống 6.0"

def scan_and_fix_version():
    print("========== BẮT ĐẦU QUÉT MỌI NGÓC NGÁCH GIAO DIỆN ==========")
    count_fixed = 0
    
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
            
        for root, dirs, files in os.walk(target_dir):
            # Bỏ qua các thư mục bộ nhớ đệm
            if '__pycache__' in root or 'build' in root or 'dist' in root:
                continue
                
            for file in files:
                if file.endswith('.py') and file != 'fix_version_ui.py':
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Kiểm tra xem file có chứa chuỗi viết cứng hệ thống 6.0 không
                        if OLD_TEXT in content:
                            print(f"[PHÁT HIỆN]: Tìm thấy chuỗi gán cứng trong file: {file_path}")
                            
                            # Xử lý thay thế: Tự động import VERSION từ config và đưa vào tiêu đề động
                            # Tìm vị trí import để chèn cho đúng chuẩn mã nguồn
                            replacement = (
                                "try:\n"
                                "    from config import VERSION\n"
                                "except ImportError:\n"
                                "    VERSION = '8.0.0'\n"
                            )
                            
                            # Thay đổi chuỗi hiển thị thành dạng f-string sử dụng biến VERSION động
                            new_content = content.replace(f'"{OLD_TEXT}"', f'f"Quản lý bản quyền - Hệ thống {{VERSION}}"')
                            new_content = new_content.replace(f"'{OLD_TEXT}'", f"f'Quản lý bản quyền - Hệ thống {{VERSION}}'")
                            
                            # Nếu trong file chưa có cụm từ import config, tự động chèn lên đầu file
                            if "from config import VERSION" not in new_content:
                                new_content = replacement + "\n" + new_content
                                
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            print(f" -> [THÀNH CÔNG]: Đã chuyển hóa tiêu đề sang phiên bản tự động bộ.")
                            count_fixed += 1
                    except Exception as e:
                        print(f" Không thể đọc/ghi file {file_path}: {e}")
                        
    print("===========================================================")
    print(f"Hoàn tất! Đã tìm và xử lý dứt điểm {count_fixed} vị trí viết cứng.")

if __name__ == '__main__':
    scan_and_fix_version()