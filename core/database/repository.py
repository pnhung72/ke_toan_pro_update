# -*- coding: utf-8 -*-
"""
Repository Pattern - Tách biệt logic truy vấn database
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseRepository:
    """Repository cơ sở"""
    
    def __init__(self, db_connection):
        self.conn = db_connection


class CustomerRepository(BaseRepository):
    """Repository cho khách hàng"""
    
    def get_all(self, limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM customers LIMIT ?', (limit,))
        return cursor.fetchall()
    
    def get_by_id(self, customer_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        return cursor.fetchone()
    
    def create(self, name: str, phone: str, address: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO customers (name, phone, address, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, phone, address, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid


class InvoiceRepository(BaseRepository):
    """Repository cho hóa đơn"""
    
    def get_by_customer(self, customer_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM invoices WHERE customer_id = ? ORDER BY date DESC
        ''', (customer_id,))
        return cursor.fetchall()
    
    def get_unpaid(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM invoices WHERE status = 'unpaid' ORDER BY due_date
        ''')
        return cursor.fetchall()
        
# --- THÊM VÀO CUỐI FILE repository.py ---

# --- ĐOẠN CHỈNH CHUẨN CHO repository.py ---

class BankRepository(BaseRepository):
    """Repository chuyên biệt xử lý dữ liệu ngân hàng cho 27 bảng hệ thống"""

    def import_bank_transactions(self, data_list: List[Dict]) -> Dict:
        """Đổ dữ liệu từ Parser vào Database, tự động loại trùng"""
        query = """
            INSERT OR IGNORE INTO journal_entries 
            (date, reference, amount_in, amount_out, description, bank_code)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        # Chuyển đổi List[Dict] sang List[Tuple] để nạp nhanh
        values = [
            (d['trans_date'], d['reference'], d['amount_in'], 
             d['amount_out'], d['description'], d['bank_code'])
            for d in data_list
        ]
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM journal_entries")
            before = cursor.fetchone()[0]
            cursor.executemany(query, values)
            self.conn.commit()
            
            # Ghi log kết quả để Thầy theo dõi trong Nhật ký hệ thống
            cursor.execute("SELECT COUNT(*) FROM journal_entries")
            after = cursor.fetchone()[0]
            inserted_count = after - before
            return {"success": True, "count": inserted_count}
        except Exception as e:
            logger.error(f"Lỗi nạp dữ liệu ngân hàng: {e}")
            return {"success": False, "message": str(e)}