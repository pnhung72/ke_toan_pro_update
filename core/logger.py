"""
Logger - Hệ thống logging chuyên nghiệp.

Module này cung cấp:
- Ghi log ra file và console
- Tự động xoay file khi quá lớn (10MB)
- Phân cấp log: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Decorator tự động ghi log hàm

Example:
    >>> from core.logger import get_logger, ModuleLogger
    >>> logger = get_logger(__name__)
    >>> logger.info("Thông báo")
"""

# core/logger.py
# HỆ THỐNG LOGGING CHUYÊN NGHIỆP
# Thay thế print trong toàn bộ ứng dụng

import os

"""
Logger - Hệ thống logging chuyên nghiệp.

Module này cung cấp:
- Ghi log ra file và console
- Tự động xoay file khi quá lớn (10MB)
- Phân cấp log: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Decorator tự động ghi log hàm

Example:
    >>> from core.logger import get_logger, ModuleLogger
    >>> logger = get_logger(__name__)
    >>> logger.info("Thông báo")
"""
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

class LoggerSetup:
    """
    Cấu hình logging toàn cục cho phần mềm
    - Ghi log ra file và console
    - Tự động xoay file khi quá lớn
    - Phân cấp log: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Xác định thư mục log
        base_dir = Path(__file__).parent.parent
        self.log_dir = base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Cấu hình logger
        self.setup_logging()
    
    def setup_logging(self):
        """Cấu hình logging system"""
        
        # Tên file log theo ngày
        log_file = self.log_dir / f"ke_toan_pro_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Định dạng log
        log_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler (ghi log ra file)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_format)
        
        # Console handler (hiển thị ra màn hình)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        
        # Cấu hình root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Xóa handlers cũ nếu có
        root_logger.handlers.clear()
        
        # Thêm handlers mới
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log khởi động
        logging.info("=" * 60)
        logging.info("KHOI DONG HE THONG LOGGING")
        logging.info(f"File log: {log_file}")
        logging.info("=" * 60)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Lấy logger cho module cụ thể"""
        return logging.getLogger(name)


# ========== LOGGER FACTORY ==========

_logger_setup = None

def get_logger(name: str = None) -> logging.Logger:
    """
    Lấy logger cho module hiện tại
    Sử dụng: logger = get_logger(__name__)
    """
    global _logger_setup
    if _logger_setup is None:
        _logger_setup = LoggerSetup()
    
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return _logger_setup.get_logger(name)


# ========== DECORATOR GHI LOG TỰ ĐỘNG ==========

def log_function(log_level=logging.INFO):
    """Decorator tự động ghi log khi gọi hàm"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            logger.log(log_level, f"--- GOI: {func.__name__} ---")
            
            try:
                result = func(*args, **kwargs)
                logger.log(log_level, f"--- KET THUC: {func.__name__} ---")
                return result
            except Exception as e:
                logger.error(f"LOI TRONG {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# ========== CLASS QUẢN LÝ LOG THEO MODULE ==========

class ModuleLogger:
    """Logging theo module riêng biệt"""
    
    def __init__(self, module_name: str):
        self.logger = get_logger(module_name)
        self.module_name = module_name
    
    def debug(self, message: str):
        self.logger.debug(f"[{self.module_name}] {message}")
    
    def info(self, message: str):
        self.logger.info(f"[{self.module_name}] {message}")
    
    def warning(self, message: str):
        self.logger.warning(f"[{self.module_name}] {message}")
    
    def error(self, message: str):
        self.logger.error(f"[{self.module_name}] {message}")
    
    def critical(self, message: str):
        self.logger.critical(f"[{self.module_name}] {message}")
    
    def exception(self, message: str):
        self.logger.exception(f"[{self.module_name}] {message}")


# ========== KIỂM TRA ==========
if __name__ == "__main__":
    print("=== KIỂM TRA LOGGING ===")
    
    # Cách 1: Dùng logger cơ bản
    logger = get_logger("test")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    
    # Cách 2: Dùng ModuleLogger
    mod_log = ModuleLogger("test_module")
    mod_log.info("Module test")
    
    # Cách 3: Dùng decorator
    @log_function()
    def test_function():
        mod_log.info("Trong test_function")
        return "OK"
    
    test_function()
    
    print("\n✅ Logging hoạt động tốt!")
    print(f"📁 Xem log tại: {Path(__file__).parent.parent / 'logs'}")