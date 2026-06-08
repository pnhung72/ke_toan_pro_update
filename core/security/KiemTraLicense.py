import sqlite3
import os
import json
import sys
from datetime import datetime
from core.encryption import encryption
import tkinter as tk
from tkinter import messagebox
 

# 1. Tự động phân biệt môi trường chạy code và môi trường chạy file .EXE
if sys.platform == 'win32' and hasattr(sys, '_MEIPASS'):
    # Nếu đang chạy bên trong file .EXE đã đóng gói, lấy thư mục chứa file .EXE thực tế ngoài ổ đĩa
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Nếu đang chạy bằng lệnh python main.py thông thường
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH
config_STATE_PATH = os.path.join(BASE_DIR, "configs", "app_state.json")
ADMIN_KEY_PATH = os.path.join(BASE_DIR, "admin.key")  # Đường dẫn kiểm tra file key Admin

def kiem_tra_ban_quyen_he_thong():
    # -------------------------------------------------------------------------
    # LUỒNG ƯU TIÊN Cao nhất: KIỂM TRA ĐẶC QUYỀN ADMIN (FILE admin.key)
    # -------------------------------------------------------------------------
    if os.path.exists(ADMIN_KEY_PATH):
        # Nếu xuất hiện file admin.key tại thư mục gốc, cấp toàn quyền không giới hạn thời gian
        return "VALID", {
            "loai": "ADMIN_FULL",
            "ngay_het_han": "Vĩnh viễn",
            "so_ngay_con_lai": 9999
        }

    # -------------------------------------------------------------------------
    # LUỒNG THƯỜNG: KIỂM TRA BẢN DÙNG THỬ / LICENSE TRONG DATABASE
    # -------------------------------------------------------------------------
    if not os.path.exists(DB_PATH):
        return "ERROR", f"Không tìm thấy file cơ sở dữ liệu tại: {DB_PATH}"
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Đọc thông tin license đang hoạt động
        cursor.execute("""
            SELECT license_type, start_date, expire_date, status 
            FROM licenses 
            WHERE status = 'ACTIVE' 
            ORDER BY id DESC LIMIT 1;
        """)
        license_data = cursor.fetchone()
        
        if not license_data:
            # Hiển thị thông báo hướng dẫn cho khách hàng khi chưa có license
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw() # Ẩn cửa sổ chính
            messagebox.showinfo("Kế Toán Pro - Thông báo", 
                                "Chào mừng bạn đến với Kế Toán Pro!\n\n"
                                "Phần mềm hiện chưa có thông tin bản quyền.\n"
                                "Vui lòng liên hệ Thầy Hùng để nhận mã kích hoạt dùng thử.\n\n"
                                "Website: https://mamcotcacom.blogspot.com/\n"
                                "Cảm ơn bạn!")
            root.destroy()
            return "LOCKED", "Không tìm thấy thông tin bản quyền hợp lệ. Vui lòng liên hệ Thầy Hùng!"
            
        license_type, start_date_str, expire_date_str, status = license_data
        expire_date = datetime.strptime(expire_date_str, '%Y-%m-%d %H:%M:%S')
        thoi_gian_hien_tai = datetime.now()
        
        # 2. Kiểm tra cơ chế chống lùi ngày giờ hệ thống (Anti-cheat)
        if check_gian_lan_thoi_gian(thoi_gian_hien_tai):
            cursor.execute("UPDATE licenses SET status = 'LOCKED' WHERE status = 'ACTIVE';")
            conn.commit()
            return "LOCKED", "Phát hiện gian lận thời gian hệ thống! Phần mềm đã bị khóa tự động."
            
        # 3. Kiểm tra xem đã quá hạn dùng thử/bản quyền chưa
        if thoi_gian_hien_tai > expire_date:
            cursor.execute("UPDATE licenses SET status = 'EXPIRED' WHERE status = 'ACTIVE';")
            conn.commit()
            return "EXPIRED", f"Phiên bản [{license_type}] đã hết hạn vào ngày {expire_date_str}. Vui lòng nâng cấp!"
            
        # 4. Hợp lệ -> Cập nhật lại vết thời gian sử dụng gần nhất và tính số ngày còn lại
        update_vet_thoi_gian(thoi_gian_hien_tai)
        so_ngay_con_lai = (expire_date - thoi_gian_hien_tai).days
        
        return "VALID", {
            "loai": license_type,
            "ngay_het_han": expire_date_str,
            "so_ngay_con_lai": max(0, so_ngay_con_lai)
        }
        
    except sqlite3.Error as e:
        return "ERROR", f"Lỗi truy vấn Database: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()

def check_gian_lan_thoi_gian(thoi_gian_hien_tai):
    if not os.path.exists(config_STATE_PATH):
        return False
    try:
        with open(config_STATE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        last_run_str = data.get("last_run")
        if last_run_str:
            last_run = datetime.strptime(last_run_str, '%Y-%m-%d %H:%M:%S')
            if thoi_gian_hien_tai < last_run:
                return True
    except Exception:
        pass
    return False

def update_vet_thoi_gian(thoi_gian_hien_tai):
    os.makedirs(os.path.dirname(config_STATE_PATH), exist_ok=True)
    data = {"last_run": thoi_gian_hien_tai.strftime('%Y-%m-%d %H:%M:%S')}
    with open(config_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
def get_real_hardware_id():
    """Lấy Hardware ID đã được làm sạch hoàn toàn."""
    try:
        import subprocess
        # Lệnh lấy serial
        cmd = "wmic baseboard get serialnumber"
        output = subprocess.check_output(cmd, shell=True).decode()
        
        # Lấy dòng thứ 2 (dữ liệu) và dùng strip() để xóa sạch khoảng trắng/xuống dòng
        lines = [line.strip() for line in output.split('\n') if line.strip()]
        if len(lines) > 1:
            clean_id = lines[1].strip()
            # In ra Terminal để Thầy xem tận mắt nó là cái gì
            #print(f"DEBUG: ID Mainboard thực tế là: '{clean_id}'")
            return clean_id
        return "UNKNOWN_ID"
    except Exception:
        return "UNKNOWN_ID"
        
def hien_thi_thong_bao_kich_hoat():
    root = tk.Tk()
    root.withdraw()  # Ẩn cửa sổ chính của tkinter
    messagebox.showinfo("Kế Toán Pro - Kích hoạt bản quyền", 
                        "Chào mừng bạn đến với Kế Toán Pro!\n\n"
                        "Phần mềm chưa được kích hoạt bản quyền.\n"
                        "Vui lòng liên hệ Thầy Hùng để nhận mã kích hoạt dùng thử 30 ngày.\n\n"
                        "Website: https://mamcotcacom.blogspot.com/\n"
                        "Cảm ơn bạn đã tin dùng!")
    root.destroy()