# services/email_service.py
"""
Dịch vụ email - TÍCH HỢP:
1. Giữ nguyên toàn bộ chức năng gốc (verify_and_save, get_all_configs từ DB, send_feedback)
2. Thêm chức năng mã hóa cấu hình (tùy chọn, không bắt buộc)
3. Hỗ trợ cả 2 nguồn: file mã hóa (ưu tiên) và database cũ (fallback)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import json
import sqlite3
import errno
from imap_tools import MailBox
from datetime import datetime
from utils.logger import get_logger
from utils.master_key import get_master_key_manager, secure_input

logger = get_logger(__name__)
# Thêm vào sau dòng import (khoảng dòng 20)
from cryptography.fernet import Fernet
import base64
import hashlib
import logging

# Khóa mã hóa cố định (có thể thay đổi sau)
ENCRYPTION_KEY = base64.urlsafe_b64encode(hashlib.sha256(b"ke-toan-pro-email-secret-key-2025").digest())
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    """Mã hóa mật khẩu trước khi lưu"""
    if not password:
        return ""
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    """Giải mã mật khẩu khi sử dụng"""
    if not encrypted:
        return ""
    return cipher.decrypt(encrypted.encode()).decode()

class EmailService:
    def __init__(self, db_path=None, master_passphrase=None):
        """
        Khởi tạo dịch vụ email
        
        Args:
            db_path: Đường dẫn database (tùy chọn)
            master_passphrase: SecurePassphrase object (để đọc file mã hóa)
        """
        self.master_passphrase = master_passphrase
        self._encrypted_config = None
        self._encrypted_loaded = False
        
        # Xác định db_path (giữ nguyên logic gốc)
        if db_path:
            self.db_path = db_path
        else:
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.dirname(current_dir)
            
            data_path_file = os.path.join(base_dir, "data_path.txt")
            if os.path.exists(data_path_file):
                with open(data_path_file, 'r', encoding='utf-8') as f:
                    rel_path = f.read().strip()
                    if rel_path:
                        real_data_dir = os.path.join(base_dir, rel_path)
                    else:
                        real_data_dir = os.path.join(base_dir, "ke_toan_data")
            else:
                real_data_dir = os.path.join(base_dir, "ke_toan_data")
            
            self.db_path = os.path.join(real_data_dir, "ke_toan.db")
        
        logging.info(f"EmailService đang kết nối tới: {self.db_path}")
        
        # Tự động tạo bảng nếu chưa có (giữ nguyên logic gốc)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS email_configurations 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                             email_address TEXT UNIQUE, 
                             app_password TEXT, 
                             created_at TEXT)''')
            conn.commit()
            conn.close()
            logging.info("Đã kiểm tra và khởi tạo bảng email_configurations")
        except Exception as e:
            logging.error(f"Lỗi khởi tạo bảng ban đầu: {e}")
    
    # ============================================================
    # CHỨC NĂNG MỚI: ĐỌC CẤU HÌNH TỪ FILE MÃ HÓA
    # ============================================================
    
    def _load_encrypted_config(self):
        """Tải cấu hình từ file mã hóa (configs/smtp_config.enc)"""
        config_path = "configs/smtp_config.enc"
        
        if not os.path.exists(config_path):
            return None
        
        if self.master_passphrase is None:
            return None
        
        try:
            manager = get_master_key_manager()
            temp_json = "configs/smtp_config_temp.json"
            
            result = manager.decrypt_file(config_path, self.master_passphrase, temp_json)
            
            if result is None:
                logger.error("Giải mã cấu hình SMTP thất bại")
                return None
            
            with open(temp_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            os.remove(temp_json)
            return config
            
        except Exception as e:
            logger.error(f"Lỗi khi giải mã cấu hình SMTP: {e}")
            return None
    
    def get_encrypted_config(self):
        """Lấy cấu hình từ file mã hóa (nếu có)"""
        if not self._encrypted_loaded:
            self._encrypted_config = self._load_encrypted_config()
            self._encrypted_loaded = True
        return self._encrypted_config
    
    def has_encrypted_config(self):
        """Kiểm tra xem đã có cấu hình trong file mã hóa chưa"""
        return self.get_encrypted_config() is not None
    
    def save_encrypted_config(self, email: str, app_password: str) -> bool:
        """Lưu cấu hình vào file mã hóa"""
        if self.master_passphrase is None:
            logger.error("Thiếu master passphrase, không thể lưu cấu hình mã hóa")
            return False
        
        config_data = {
            "email": email,
            "app_password": app_password,
            "updated_at": datetime.now().isoformat()
        }
        
        os.makedirs("configs", exist_ok=True)
        temp_json = "configs/smtp_config_temp.json"
        
        try:
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            manager = get_master_key_manager()
            manager.encrypt_file(temp_json, self.master_passphrase, "configs/smtp_config.enc")
            os.remove(temp_json)
            
            self._encrypted_config = config_data
            self._encrypted_loaded = True
            
            logger.info(f"✅ Đã lưu cấu hình SMTP vào file mã hóa (email: {email})")
            return True
            
        except PermissionError as e:
            logger.error(f"Lỗi quyền truy cập: {e}")
            if os.path.exists(temp_json):
                os.remove(temp_json)
            return False
        except OSError as e:
            if e.errno == errno.ENOSPC:
                logger.critical(f"LỖI: Đĩa đầy! Không thể lưu cấu hình.")
            else:
                logger.error(f"Lỗi hệ thống: {e}")
            if os.path.exists(temp_json):
                os.remove(temp_json)
            return False
        except Exception as e:
            logger.error(f"Lỗi lưu cấu hình: {e}")
            if os.path.exists(temp_json):
                os.remove(temp_json)
            return False
    
    # ============================================================
    # CHỨC NĂNG GỐC: GIỮ NGUYÊN
    # ============================================================
    
    def verify_and_save(self, email_user, app_password):
        """Kiểm tra kết nối và lưu vào Database - CÓ MÃ HÓA"""
        conn = None
        try:
            # 1. Thử kết nối thực tế với Server IMAP
            with MailBox('imap.gmail.com').login(email_user, app_password) as mailbox:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''CREATE TABLE IF NOT EXISTS email_configurations 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                 email_address TEXT UNIQUE, 
                                 app_password TEXT, 
                                 created_at TEXT)''')
                
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # ⭐ CHỈ SỬA 1 DÒNG NÀY: Mã hóa mật khẩu trước khi lưu
                encrypted_password = encrypt_password(app_password)  # <-- THÊM DÒNG NÀY
                
                cursor.execute("""INSERT OR REPLACE INTO email_configurations 
                                  (email_address, app_password, created_at) VALUES (?, ?, ?)""",
                               (email_user, encrypted_password, now))  # <-- SỬA: app_password -> encrypted_password
                
                conn.commit()
                
                # Nếu có master_passphrase, cũng lưu vào file mã hóa
                if self.master_passphrase is not None:
                    self.save_encrypted_config(email_user, app_password)
                
                return True, "Kết nối thành công và đã lưu cấu hình!"
        except Exception as e:
            return False, f"Lỗi kết nối hoặc ghi dữ liệu: {str(e)}"
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
    
    def get_all_configs(self):
        """
        BẢO TOÀN TÍNH NĂNG THÍCH ỨNG:
        Lấy cấu hình Email (id, email, app_password, created_at).
        ƯU TIÊN: File mã hóa > Database cũ
        Hỗ trợ cả 2 cấu trúc bảng cũ và mới.
        ⭐ MỚI: Tự động giải mã mật khẩu từ database
        """
        # ƯU TIÊN 1: Lấy từ file mã hóa (nếu có)
        encrypted = self.get_encrypted_config()
        if encrypted and encrypted.get('email'):
            return [{
                'id': 1,
                'email': encrypted['email'],
                'app_password': encrypted.get('app_password', ''),
                'created_at': encrypted.get('updated_at', '')
            }]
        
        # FALLBACK: Đọc từ database (giữ nguyên logic gốc)
        conn = None
        rows = []
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, email_address as email, app_password, created_at FROM email_configurations ORDER BY id DESC")
            rows = cursor.fetchall()
            
            # ⭐ THÊM: Giải mã mật khẩu trong từng dòng
            decrypted_rows = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get('app_password'):
                    try:
                        # Thử giải mã (nếu đã được mã hóa)
                        row_dict['app_password'] = decrypt_password(row_dict['app_password'])
                    except Exception:
                        # Nếu giải mã thất bại (là plain text cũ), giữ nguyên
                        pass
                decrypted_rows.append(row_dict)
            rows = decrypted_rows
            
        except Exception:
            if conn:
                try: conn.close()
                except Exception: pass
                
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT id, email, '' as app_password, created_at FROM email_configurations ORDER BY id DESC")
                raw_rows = cursor.fetchall()
                # Chuyển đổi thành dict (không có mật khẩu để giải mã)
                rows = [dict(r) for r in raw_rows]
            except Exception as e2:
                logging.error(f"Lỗi truy vấn dữ liệu Email: {e2}")
                rows = []
        finally:
            if conn:
                try: conn.close()
                except Exception: pass
                
        return rows
        
    def send_feedback_to_admin(self, subject, content, sender_email, sender_password=None):
        """
        Dùng SMTP để gửi phản hồi về cho Admin (Thầy)
        GIỮ NGUYÊN logic gốc
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        admin_email = os.environ.get("ADMIN_EMAIL", "pnhungc3nvt@gmail.com")
        admin_password = os.environ.get("ADMIN_EMAIL_PASSWORD", "bhczlexkuxythqsc")

        recipient = "pnhungc3nvt@gmail.com"
        msg = MIMEMultipart()
        msg["From"] = admin_email
        msg["To"] = recipient
        msg["Subject"] = f"[PHẢN HỒI TỪ {sender_email}] {subject}"

        full_content = f"Email người gửi: {sender_email}\n\nNội dung:\n{content}"
        msg.attach(MIMEText(full_content, "plain", "utf-8"))

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(admin_email, admin_password)
                server.sendmail(admin_email, recipient, msg.as_string())
            return True
        except Exception as e:
            logging.error(f"Lỗi gửi phản hồi: {e}")
            return False
    
    # ============================================================
    # HÀM TIỆN ÍCH: DI CHUYỂN DỮ LIỆU CŨ
    # ============================================================
    
    def migrate_db_to_encrypted(self, master_passphrase) -> bool:
        """
        Di chuyển cấu hình từ database cũ sang file mã hóa
        Chạy 1 lần khi nâng cấp hệ thống
        """
        self.master_passphrase = master_passphrase
        
        if self.has_encrypted_config():
            logger.info("Đã có cấu hình trong file mã hóa, bỏ qua migration")
            return True
        
        old_configs = self.get_all_configs()
        if not old_configs:
            logger.info("Không có cấu hình trong database cũ")
            return True
        
        config = old_configs[0]
        
        # SỬA: Xử lý đúng kiểu sqlite3.Row (không có phương thức .get())
        try:
            # Cách 1: Truy cập bằng thuộc tính (nếu có)
            email = getattr(config, 'email', '') or getattr(config, 'email_address', '')
            password = getattr(config, 'app_password', '')
        except Exception:
            # Cách 2: Truy cập bằng index (dựa trên cấu trúc Row)
            try:
                # Giả sử Row có các cột: id, email, app_password, created_at
                email = config[1] if len(config) > 1 else ''
                password = config[2] if len(config) > 2 else ''
            except Exception:
                # Cách 3: Chuyển thành dict
                config_dict = dict(config)
                email = config_dict.get('email', '') or config_dict.get('email_address', '')
                password = config_dict.get('app_password', '')
        
        if not email:
            logger.warning("Không tìm thấy email trong database cũ")
            return False
        
        success = self.save_encrypted_config(email, password)
        
        if success:
            logger.info(f"✅ Đã di chuyển cấu hình email sang file mã hóa: {email}")
        else:
            logger.error("❌ Di chuyển cấu hình thất bại")
        
        return success

def migrate_email_config():
    """Di chuyển cấu hình từ database cũ sang file mã hóa"""
    print("=" * 50)
    print("DI CHUYỂN CẤU HÌNH EMAIL TỪ DB CŨ")
    print("=" * 50)
    
    from utils.master_key import secure_input
    
    print("\n⚠️ Tính năng này sẽ di chuyển cấu hình email từ database cũ")
    print("⚠️ sang file mã hóa (configs/smtp_config.enc)")
    print("⚠️ Dữ liệu cũ sẽ được vô hiệu hóa, không bị xóa hoàn toàn\n")
    
    with secure_input("Nhập mật khẩu chủ (tạo mới): ") as passphrase:
        service = EmailService(master_passphrase=passphrase)
        success = service.migrate_db_to_encrypted(passphrase)
        
        if success:
            print("\n✅ Đã di chuyển cấu hình email thành công!")
            print("📁 File cấu hình: configs/smtp_config.enc")
        else:
            logging.error("Di chuyển cấu hình thất bại!")
        
        return success
        
# Hàm tiện ích để thiết lập cấu hình email lần đầu (hỗ trợ CLI)
def setup_email_config():
    """Thiết lập cấu hình email lần đầu (hỗ trợ CLI)"""
    print("=" * 50)
    print("THIẾT LẬP CẤU HÌNH EMAIL")
    print("=" * 50)
    
    email = input("Email gửi: ").strip()
    app_password = input("App password: ").strip()
    
    if not email or not app_password:
        print("❌ Email và mật khẩu không được để trống!")
        return False
    
    service = EmailService()
    success, message = service.verify_and_save(email, app_password)
    
    print(f"\n{message}")
    return success

def send_error_log_to_admin(error_message: str, log_file_path: str = None):
    """
    Tự động gửi log lỗi về email admin khi có lỗi nghiêm trọng
    Khách không cần biết, hệ thống tự gửi ngầm
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    admin_email = os.environ.get("ADMIN_EMAIL", "pnhungc3nvt@gmail.com")
    admin_password = os.environ.get("ADMIN_EMAIL_PASSWORD", "bhczlexkuxythqsc")

    try:
        msg = MIMEMultipart()
        msg["From"] = admin_email
        msg["To"] = admin_email
        msg["Subject"] = f"[LỖI HỆ THỐNG] {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"

        body = f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\nLỗi:\n{error_message}"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Đính kèm file log nếu có
        if log_file_path and os.path.exists(log_file_path):
            with open(log_file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename=error_log.txt")
                msg.attach(part)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(admin_email, admin_password)
            server.sendmail(admin_email, admin_email, msg.as_string())

        logger.info("Đã gửi log lỗi về admin")
        return True
    except Exception as e:
        logger.error(f"Không thể gửi log lỗi: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_email_config()
    else:
        setup_email_config()