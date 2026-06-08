# -*- coding: utf-8 -*-
"""
DBOptimizer - Toi uu hieu nang database
"""

import sqlite3
import time
from functools import lru_cache
from threading import Lock
import logging

class DBOptimizer:
    """Toi uu database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = Lock()
        self._cache = {}
    
    def create_indexes(self):
        """Tao cac index de tang toc truy van"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_debt_customer ON debt(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_debt_status ON debt(status)",
        ]
        
        for idx in indexes:
            try:
                cursor.execute(idx)
            except Exception as e:
                logging.error(f"Lỗi tạo index: {e}")
        
        conn.commit()
        conn.close()
        logging.info("Đã tạo các index cho database")
    
    def optimize_query(self, query, params=None):
        """Chay query da duoc toi uu voi cache"""
        with self._lock:
            cache_key = f"{query}_{params}"
            
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            start = time.time()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchall()
            elapsed = time.time() - start
            
            # Chi cache query chay cham (>0.5s)
            if elapsed > 0.5:
                self._cache[cache_key] = result
            
            conn.close()
            return result
    
    def vacuum(self):
        """Toi gian kich thuoc database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.close()
        logging.info("Đã tối ưu database")
    
    def analyze(self):
        """Phan tich va cap nhat thong ke"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("ANALYZE")
        conn.close()
        logging.info("Đã phân tích database")
    
    def get_db_size(self):
        """Lay kich thuoc database (bytes)"""
        import os
        if os.path.exists(self.db_path):
            return os.path.getsize(self.db_path)
        return 0
    
    def get_table_stats(self):
        """Lay thong ke cac bang"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tables = ["invoices", "transactions", "products", "debt", "customers"]
        stats = {}
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[table] = count
            except Exception:
                stats[table] = 0
        
        conn.close()
        return stats