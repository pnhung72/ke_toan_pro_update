# -*- coding: utf-8 -*-
import sys
import os
import io # <--- THẦY PHẢI THÊM DÒNG NÀY VÀO ĐÂY
import traceback
import tkinter as tk
from tkinter import messagebox

# 1. Các module chức năng cũ (Bảo toàn)
from utils.error_logger import send_error_report
from utils.logger import get_logger
from configs import ensure_directories, DB_PATH, VERSION, ADMIN_HARDWARE_ID
from models.database import Database
from ui.main_window import MainWindow
from ui.font_config import setup_fonts
from core.security.KiemTraLicense import kiem_tra_ban_quyen_he_thong, get_real_hardware_id
from datetime import datetime, timedelta
import threading
import time
logger = get_logger(__name__)
from services.auto_updater import AutoUpdater   # ★ Cập nhật tự động


# Kiểm tra nếu sys.stdout tồn tại mới ép kiểu, nếu không thì bỏ qua để tránh lỗi NoneType
if sys.stdout is not None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr is not None:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 2. TÍNH NĂNG MỚI: Cơ chế kiểm tra quyền truy cập (Admin Mode)
def check_access_mode():
    current_id = get_real_hardware_id()
    # Kiểm tra admin.key tại thư mục gốc
    base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    admin_key_exists = os.path.exists(os.path.join(base_dir, "admin.key"))
    
    if current_id == ADMIN_HARDWARE_ID:
        return "ADMIN_MODE" if admin_key_exists else "ADMIN_TEST_MODE"
    else:
        if admin_key_exists: return "FRAUD"
        return "TRIAL"

def start_background_services():
    """Khởi động các dịch vụ nền: trình quét email, v.v."""
    try:
        logger.info("Dịch vụ nền đã khởi động.")
        
        # === ĐỒNG BỘ CLOUD CHỈ BẰNG THỦ CÔNG (QUA NÚT BẤM TRÊN GIAO DIỆN) ===
        # Tự động đã bị vô hiệu hóa để tránh xung đột với OCR
        # Người dùng bấm nút "Đồng bộ" khi muốn backup dữ liệu lên Google Drive
        
        # === KHỞI ĐỘNG TRÌNH QUÉT EMAIL ===
        from core.mail_detector import AdminMailScanner
        from services.email_service import EmailService
        
        email_service = EmailService()
        configs = email_service.get_all_configs()
        if configs:
            email_user = configs[0]['email']
            email_pass = configs[0]['app_password']
            scanner = AdminMailScanner(email_user, email_pass)
            thread = threading.Thread(target=scanner.start_scanning, daemon=True)
            thread.start()
            print("✅ [BACKGROUND] Đã khởi động trình quét email (chạy ngầm)")
            logger.info("Đã khởi động trình quét email")
        else:
            print("⚠️ [BACKGROUND] Chưa có cấu hình email, bỏ qua khởi động scanner")
            logger.warning("Chưa có cấu hình email, không khởi động scanner")
    except Exception as e:
        print(f"⚠️ [BACKGROUND] Lỗi khởi động dịch vụ nền: {e}")
        logger.error(f"Lỗi khởi động dịch vụ nền: {e}")
        


def check_trial_period():
    """Kiểm tra dùng thử 30 ngày lưu tại file trial.dat trong REAL_DATA_DIR."""
    from configs import REAL_DATA_DIR
    trial_file = os.path.join(REAL_DATA_DIR, "trial.dat")
    
    today = datetime.now()
    
    if not os.path.exists(trial_file):
        # Lần đầu chạy: tạo file với ngày hiện tại
        with open(trial_file, "w") as f:
            f.write(today.strftime('%Y-%m-%d'))
        return True
    else:
        # Đọc ngày bắt đầu
        with open(trial_file, "r") as f:
            start_date_str = f.read().strip()
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        # Kiểm tra nếu chưa quá 30 ngày
        if (today - start_date).days <= 30:
            return True
        return False

def main():
    root = tk.Tk()
    root.withdraw()
    
    try:
        ensure_directories()
        Database.init_db()
        
# 3. Logic phân quyền (Tích hợp mới)
        mode = check_access_mode()
        
        if mode == "FRAUD":
            messagebox.showerror("Cảnh báo", "Phát hiện can thiệp hệ thống trái phép!")
            sys.exit()

        # Xác định trạng thái bản quyền
        if mode == "ADMIN_MODE":
            trang_thai, ket_qua = "VALID", {"loai": "ADMIN TOÀN QUYỀN"}
        elif mode == "ADMIN_TEST_MODE":
            trang_thai, ket_qua = "VALID", {"loai": "TEST (CHẾ ĐỘ KHÁCH)"}
        elif mode == "TRIAL":
            if check_trial_period():
                trang_thai, ket_qua = "VALID", {"loai": "DÙNG THỬ (30 NGÀY)"}
            else:
                trang_thai, ket_qua = "EXPIRED", "Hết hạn dùng thử 30 ngày. Vui lòng mua bản quyền!"
        else:
            trang_thai, ket_qua = kiem_tra_ban_quyen_he_thong()
        
        # 4. Chạy giao diện chính
        if trang_thai == "VALID":
            if hasattr(Database, 'cleanup_duplicate_business_info'):
                Database.cleanup_duplicate_business_info()
            
            # Khởi động dịch vụ nền (không chặn giao diện nếu mất thời gian)
            try:
                start_background_services()
            except Exception as e:
                logger.warning(f"Dịch vụ nền không thể khởi động: {e}")
                    
            app = MainWindow(root) 
            root.title(f"Kế Toán Pro - v{VERSION} [{ket_qua.get('loai', 'User')}]")
            root.protocol("WM_DELETE_WINDOW", lambda: root.destroy())
            root.deiconify()
            # ★ Kích hoạt cập nhật tự động (kiểm tra ngầm mỗi 6 giờ)
            updater = AutoUpdater(root)
            updater.kich_hoat()
            # ★ Kiểm tra ngay sau 5 giây khi UI đã ổn định
            root.after(5000, updater.kiem_tra_ngay)
            root.mainloop()
        else:
            # Thông báo và thoát nếu bản quyền không hợp lệ
            thong_bao = ket_qua if isinstance(ket_qua, str) else "Bản quyền không hợp lệ."
            messagebox.showerror("Lỗi bản quyền", thong_bao)
            root.destroy()  # Đảm bảo giải phóng tài nguyên
            
    except Exception as e:
        logger.exception(f"Lỗi khởi động: {e}")
        send_error_report(traceback.format_exc())
        # Gửi log lỗi về admin ngầm
        try:
            from services.email_service import send_error_log_to_admin
            send_error_log_to_admin(traceback.format_exc())
        except Exception:
            pass
        # Thông báo thân thiện cho người dùng
        messagebox.showinfo(
            "Thông báo hệ thống",
            "⚠️ Hệ thống gặp sự cố nhỏ!\n\n"
            "✅ Đội kỹ thuật đã được thông báo tự động.\n"
            "🔄 Vui lòng khởi động lại phần mềm.\n\n"
            "Xin lỗi vì sự bất tiện này!"
        )

if __name__ == "__main__":
    main()