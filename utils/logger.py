import logging
import os
from datetime import datetime
from config import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT

os.makedirs(LOG_DIR, exist_ok=True)

# Tạo tên file log theo ngày
log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# Cấu hình logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class EmailErrorHandler(logging.Handler):
    """
    Tự động gửi email về admin khi có lỗi nghiêm trọng (ERROR trở lên)
    Chạy ngầm, khách không biết
    """
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            try:
                import threading
                from services.email_service import send_error_log_to_admin
                error_msg = self.format(record)
                # Gửi ngầm trong thread riêng, không làm chậm app
                threading.Thread(
                    target=send_error_log_to_admin,
                    args=(error_msg, log_file),
                    daemon=True
                ).start()
            except Exception:
                pass  # Không làm crash app nếu gửi email thất bại


def get_logger(name):
    """Lấy logger cho module"""
    logger = logging.getLogger(name)
    # Thêm email handler nếu chưa có
    if not any(isinstance(h, EmailErrorHandler) for h in logger.handlers):
        logger.addHandler(EmailErrorHandler())
    return logger