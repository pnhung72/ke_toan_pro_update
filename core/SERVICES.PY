# core/services.py
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


"""
def start_background_services():
    """Khởi động dịch vụ nền - KHÔNG CRASH nếu lỗi"""
    services = [
        ('email_scanner', _start_email_scanner),
        ('backup_scheduler', _start_backup_scheduler),
    ]
    
    for service_name, start_func in services:
        try:
            start_func()
            logger.info(f"✅ Dịch vụ {service_name} khởi động thành công")
        except Exception as e:
            logger.error(f"❌ Dịch vụ {service_name} khởi động thất bại: {e}")

"""
def _start_email_scanner():
    """Khởi động trình quét email"""
    try:
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
            logger.info(f"Đã khởi động trình quét email cho {email_user}")
        else:
            logger.warning("Chưa có cấu hình email, bỏ qua trình quét email")
    except ImportError as e:
        logger.warning(f"Thiếu module email: {e}")
    except Exception as e:
        logger.error(f"Lỗi khởi động email scanner: {e}")


def _start_backup_scheduler():
    """Khởi động lịch backup tự động (hàng ngày lúc 2h sáng)"""
    from utils.backup import auto_backup
    
    def backup_loop():
        last_backup_date = None
        while True:
            now = datetime.now()
            # Backup lúc 2h sáng
            if now.hour == 2 and last_backup_date != now.date():
                try:
                    auto_backup()
                    last_backup_date = now.date()
                    logger.info("Backup tự động thành công")
                except Exception as e:
                    logger.error(f"Lỗi trong quá trình backup: {e}")
            # Kiểm tra mỗi 1 tiếng
            time.sleep(3600)
    
    thread = threading.Thread(target=backup_loop, daemon=True)
    thread.start()
    logger.info("Đã khởi động backup scheduler (hàng ngày lúc 2h sáng)")


if __name__ == "__main__":
    start_background_services()