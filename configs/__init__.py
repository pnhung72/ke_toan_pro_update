# -*- coding: utf-8 -*-
import os

# 1. THIẾT LẬP ĐƯỜNG DẪN CỐ ĐỊNH (Không cần dynamic phức tạp)
# BASE_DIR là thư mục gốc D:\ke_toan_pro_v3
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 2. CẤU HÌNH CỐ ĐỊNH (Đã kiểm chứng)
VERSION = "14.0.10"
ADMIN_HARDWARE_ID = "/6C69Y24/CNCMC0043R0D3A/"

REAL_DATA_DIR = os.path.join(BASE_DIR, "ke_toan_data")
DB_PATH = os.path.join(REAL_DATA_DIR, "ke_toan.db")
BACKUP_DIR = os.path.join(REAL_DATA_DIR, "backups")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 3. HÀM CHỨC NĂNG BẢO TOÀN
def ensure_directories():
    """Tạo các thư mục cần thiết nếu chưa tồn tại"""
    for d in [LOG_DIR, BACKUP_DIR, REAL_DATA_DIR]:
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

def get_tax_threshold():
    """Ngưỡng miễn thuế mặc định"""
    return 1000000000

def print_config_info():
    print("==================================================")
    print("PHẦN MỀM KẾ TOÁN PRO - CẤU HÌNH ĐÃ NẠP TỪ configS")
    print(f"Phiên bản: {VERSION}")
    print(f"DB Path: {DB_PATH}")
    print("==================================================")

# Khởi tạo tự động
ensure_directories()