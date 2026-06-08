# services/metadata_service.py
import sqlite3
import logging

class MetadataService:
    """Lớp dịch vụ chuyên trách xử lý ghi và đọc thuộc tính động cho các module ngành nghề"""
    
    def __init__(self, db_path=None):
        from data_config import DB_PATH
        if db_path is None:
            db_path = DB_PATH
        self.db_path = db_path

    def save_transaction_metadata(self, transaction_id, metadata_dict):
        """
        Hàm lưu tất cả các thuộc tính đặc thù của một giao dịch dưới dạng Dictionary.
        Ví dụ: metadata_dict = {"do_dam": "40_Do_Dam", "so_luong_thung": "50_Thung"}
        """
        if not metadata_dict:
            return True
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # 1. Xóa các key cũ của giao dịch này trước để tránh trùng lặp khi ghi đè
            placeholders = ",".join(["?"] * len(metadata_dict))
            delete_query = f"DELETE FROM transaction_metadata WHERE transaction_id = ? AND meta_key IN ({placeholders});"
            
            # Tham số truyền vào gồm: transaction_id đứng đầu, theo sau là danh sách các meta_key
            delete_params = [transaction_id] + list(metadata_dict.keys())
            cursor.execute(delete_query, delete_params)
            
            # 2. Chuẩn bị dữ liệu mới để nạp hàng loạt vào bảng phụ
            insert_data = [(transaction_id, key, str(val)) for key, val in metadata_dict.items()]
            
            cursor.executemany("""
                INSERT INTO transaction_metadata (transaction_id, meta_key, meta_value) 
                VALUES (?, ?, ?);
            """, insert_data)
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Lỗi khi lưu Metadata: {e}")
            return False

    def get_transaction_metadata(self, transaction_id):
        """Hàm lấy ra toàn bộ thuộc tính đặc thù của một giao dịch dưới dạng Dictionary"""
        metadata = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT meta_key, meta_value 
                FROM transaction_metadata 
                WHERE transaction_id = ?;
            """, (transaction_id,))
            
            rows = cursor.fetchall()
            for row in rows:
                metadata[row[0]] = row[1]
                
            conn.close()
        except Exception as e:
            logging.error(f"Lỗi khi đọc Metadata: {e}")
        return metadata