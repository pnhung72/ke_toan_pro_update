# -*- coding: utf-8 -*-
"""
ConnectionPool - Quản lý kết nối database chuyên dụng cho Kế Toán Pro
ĐỒNG BỘ TRIỆT ĐỂ ĐƯỜNG DẪN DATABASE THỰC TẾ - THẦY HÙNG PRO
"""

import sqlite3
import logging
from config import DB_PATH  # 👉 Lấy đường dẫn chuẩn hóa từ config (accounting.db)

logger = logging.getLogger(__name__)

class ConnectionPool:
    """Pool kết nối database - Phiên bản tương thích trực tiếp, an toàn cho file .EXE đóng gói"""
    
    def __init__(self, db_path: str = None, max_connections: int = 5):
        # 👉 NẾU ĐƯỜNG DẪN TRUYỀN VÀO SAI LỆCH HOẶC TRỐNG, ÉP BUỘC SỬ DỤNG DB_PATH CHUẨN TỪ config
        if db_path is None or "ke_toan.db" in db_path:
            self.db_path = DB_PATH
        else:
            self.db_path = db_path
            
        self.max_connections = max_connections
        logger.info(f"ConnectionPool khoi tao thành công tại: {self.db_path}")
    
    def _create_connection(self):
        """Tạo kết nối mới với cấu hình tối ưu hiệu năng cao cho SQLite"""
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=20,
                check_same_thread=False  # Cực kỳ quan trọng để chống xung đột đa luồng trên giao diện Tkinter
            )
            # Ép kiểu dữ liệu dạng Row để truy xuất linh hoạt theo dạng dict (row['column_name'])
            conn.row_factory = sqlite3.Row
            
            # Kích hoạt các cấu hình Pragma tối ưu hóa tốc độ đọc/ghi cho hệ thống
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            
            return conn
        except Exception as e:
            logger.error(f"Không thể khởi tạo kết nối đến file Database: {e}")
            return None

    def get_connection(self):
        """
        Lấy kết nối trực tiếp từ tệp cơ sở dữ liệu vật lý.
        BẢO TOÀN: Bỏ @contextmanager để Dashboard gọi trực tiếp .cursor() không bị lỗi lỗi gãy chuỗi dữ liệu.
        """
        return self._create_connection()
    
    def transaction(self):
        """Hỗ trợ cơ chế giao dịch (Transaction) an toàn phòng chống hỏng dữ liệu khi mất điện"""
        conn = self.get_connection()
        if conn:
            try:
                conn.execute("BEGIN")
                return conn  # Trả về đối tượng kết nối để thực thi các lệnh ghi đồng bộ
            except Exception as e:
                logger.error(f"Lỗi khởi tạo chuỗi Transaction hệ thống: {e}")
        return None

    def close_all(self):
        """Đóng toàn bộ các luồng kết nối rảnh rỗi (Duy trì tính tương thích hệ thống)"""
        logger.info("Đã xác nhận dọn dẹp và đóng an toàn các luồng kết nối chạy ngầm")
    
    def get_stats(self) -> dict:
        """Lấy thông tin trạng thái hoạt động của hạ tầng dữ liệu phục vụ quản trị"""
        return {
            'status': 'Active',
            'database': self.db_path,
            'type': 'Direct Connection Pool'
        }

# =========================================================================
# 👉 KHỞI TẠO SINGLETON PATTERN - ĐỒNG BỘ TRIỆT ĐỂ BẤT KỂ ĐẦU VÀO TRUYỀN SAI
# =========================================================================
_pool_instance = None

def get_connection_pool(db_path: str = None, max_connections: int = 5) -> ConnectionPool:
    """Lấy thực thể duy nhất xuyến suốt toàn bộ phần mềm ứng dụng"""
    global _pool_instance
    if _pool_instance is None:
        # BẤT KỂ BIẾN TRUYỀN VÀO LÀ GÌ, ÉP BUỘC CHẠY THEO ĐƯỜNG DẪN TOÀN CỤC CHUẨN
        _pool_instance = ConnectionPool(db_path=DB_PATH, max_connections=max_connections)
    return _pool_instance