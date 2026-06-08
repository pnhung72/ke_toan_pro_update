# -*- coding: utf-8 -*-
import os
import sys

# === 1. XÁC ĐỊNH THƯ MỤC GỐC ===
if getattr(sys, 'frozen', False):
    EXE_DIR = os.path.dirname(sys.executable)
    BASE_DIR = EXE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === 2. THƯ MỤC DỮ LIỆU THẬT ===
def get_real_data_dir():
    if getattr(sys, 'frozen', False):
        current_run_dir = os.path.dirname(sys.executable)
    else:
        current_run_dir = BASE_DIR

    # 1. Kiểm tra file data_path.txt ngay cạnh file thực thi
    config_file = os.path.join(current_run_dir, "data_path.txt")
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            custom_path = f.read().strip()
            if custom_path and not os.path.isabs(custom_path):
                custom_path = os.path.abspath(os.path.join(current_run_dir, custom_path))
            
            if custom_path and os.path.exists(custom_path):
                return custom_path
    
    # 2. Ưu tiên tìm thư mục ke_toan_data nằm cùng cấp với file chạy
    local_data = os.path.join(current_run_dir, "ke_toan_data")
    if os.path.exists(local_data):
        return local_data
    
    # 3. Nếu không thấy, tự động tạo thư mục dữ liệu mặc định
    os.makedirs(local_data, exist_ok=True)
    return local_data

# === 3. ĐƯỜNG DẪN HỆ THỐNG TOÀN CỤC (ĐÃ KHỬ TRÙNG LẶP & ĐỒNG BỘ) ===
REAL_DATA_DIR = get_real_data_dir()

# 👉 FIX DỨT ĐIỂM: Sử dụng đúng file ke_toan.db chứa toàn bộ dữ liệu lịch sử của Thầy
DB_PATH = os.path.join(REAL_DATA_DIR, "ke_toan.db")

BACKUP_DIR = os.path.join(REAL_DATA_DIR, "backups")
LOG_DIR = os.path.join(os.path.dirname(REAL_DATA_DIR), "logs")
config_DIR = os.path.join(os.path.dirname(REAL_DATA_DIR), "configs")
EXPORT_DIR = os.path.join(os.path.dirname(REAL_DATA_DIR), "exports")
APP_STATE_PATH = os.path.join(config_DIR, "app_state.json")

# --- KHỞI TẠO CÁC THƯ MỤC VẬT LÝ ---
os.makedirs(REAL_DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(config_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

# Hàm bổ trợ cho các module bên ngoài gọi khi cần thiết
def ensure_directories():
    os.makedirs(REAL_DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(config_DIR, exist_ok=True)
    os.makedirs(EXPORT_DIR, exist_ok=True)

# === 4. CẤU HÌNH LOG ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# === 5. THÔNG TIN PHẦN MỀM (Bảo toàn nguyên bản) ===
VERSION = "17.1.3"
# Sửa dòng cũ thành dòng này:
ADMIN_HARDWARE_ID = "/6C69Y24/CNCMC0043R0D3A/"
SOFTWARE_OWNER = "Phan Ngoc Hung, Khanh Hoa"
EMAIL = "pnhungc3nvt@gmail.com"
WEBSITE = "https://phanmemhubvn.blogspot.com/"
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw3E88Akb8jNJ0vXWQ8iazmw_m4UiZHqbvWy6eXtHlK1EHDdkBtORZhBMHF8KGujas5/exec"

# === 6. CẤU HÌNH THUẾ (CẬP NHẬT THEO NGHỊ ĐỊNH 141/2026/NĐ-CP) ===
THU_NHAP_MIE_THUE_NGUONG = 1000000000 
NGAY_AP_DUNG_LUAT_THUE_MOI = "2026-01-01"

def get_tax_threshold():
    try:
        return THU_NHAP_MIE_THUE_NGUONG 
    except NameError:
        return 1000000000 

# === 7. CÁC HÀM TIỆN ÍCH ===
def get_db_path():
    return DB_PATH

def get_backup_dir():
    return BACKUP_DIR

def get_log_dir():
    return LOG_DIR

def get_export_dir():
    return EXPORT_DIR

# === 8. HIỂN THỊ THÔNG TIN KHI KHỞI ĐỘNG ===
print("=" * 50)
print("PHAN MEM KE TOAN PRO - CAU HINH")
print("=" * 50)
print(f"Thu muc goc: {BASE_DIR}")
print(f"Du lieu that: {REAL_DATA_DIR}")
print(f"Database: {DB_PATH}")
print(f"Backup: {BACKUP_DIR}")
print(f"Log: {LOG_DIR}")
print(f"Export: {EXPORT_DIR}")
print(f"Nguong mien thue: {THU_NHAP_MIE_THUE_NGUONG:,} VND")
print("=" * 50)
