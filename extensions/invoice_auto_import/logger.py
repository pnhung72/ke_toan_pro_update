import logging
import os
from datetime import datetime

_LOG_FILE = None

def setup_logger(base_log_dir="logs"):
    """Tạo logger riêng cho invoice_auto_import"""
    global _LOG_FILE
    
    # Đảm bảo thư mục logs tồn tại
    os.makedirs(base_log_dir, exist_ok=True)
    
    log_filename = os.path.join(base_log_dir, "invoice_auto_import.log")
    _LOG_FILE = log_filename
    
    logger = logging.getLogger("invoice_import")
    logger.setLevel(logging.INFO)
    
    # Tránh thêm handler nhiều lần
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s – %(message)s', 
                                      datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger():
    """Lấy logger đã được setup (hoặc setup mặc định)"""
    logger = logging.getLogger("invoice_import")
    if not logger.handlers:
        setup_logger()
    return logger