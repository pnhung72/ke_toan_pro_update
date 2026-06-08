# data_config.py
import os
import sys

def get_data_directory():
    """
    Xác định thư mục dữ liệu chính xác
    Ưu tiên: Dữ liệu thật > Dữ liệu trong dist > Tạo mới
    """
    
    # Nếu đang chạy từ source code (python main.py)
    if not getattr(sys, 'frozen', False):
        # Dùng dữ liệu trong thư mục hiện tại
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "ke_toan_data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    # Nếu đang chạy từ file EXE
    exe_dir = os.path.dirname(sys.executable)
    
    # Ưu tiên 1: Dữ liệu thật (cùng cấp với thư mục chứa EXE)
    real_data = os.path.join(exe_dir, "..", "ke_toan_data")
    if os.path.exists(real_data) and os.path.exists(os.path.join(real_data, "ke_toan.db")):
        print(f"📁 Đang dùng dữ liệu thật: {real_data}")
        return real_data
    
    # Ưu tiên 2: Dữ liệu trong thư mục dist
    dist_data = os.path.join(exe_dir, "ke_toan_data")
    if os.path.exists(dist_data) and os.path.exists(os.path.join(dist_data, "ke_toan.db")):
        print(f"📁 Đang dùng dữ liệu trong dist: {dist_data}")
        return dist_data
    
    # Ưu tiên 3: Tạo thư mục dữ liệu mới
    os.makedirs(dist_data, exist_ok=True)
    print(f"📁 Tạo thư mục dữ liệu mới: {dist_data}")
    return dist_data

def get_backup_directory():
    """Thư mục backup"""
    data_dir = get_data_directory()
    backup_dir = os.path.join(os.path.dirname(data_dir), "backup")
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_log_directory():
    """Thư mục log"""
    data_dir = get_data_directory()
    log_dir = os.path.join(os.path.dirname(data_dir), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

# Xuất các hằng số
DATA_DIR = get_data_directory()
BACKUP_DIR = get_backup_directory()
LOG_DIR = get_log_directory()
DB_PATH = os.path.join(DATA_DIR, "ke_toan.db")

print(f"✅ Cấu hình dữ liệu:")
print(f"   - Database: {DB_PATH}")
print(f"   - Backup: {BACKUP_DIR}")
print(f"   - Log: {LOG_DIR}")