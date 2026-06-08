# -*- coding: utf-8 -*-
"""
Integration tests for database flow
"""

import unittest
import sys
import os
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.database.db_optimizer import DBOptimizer
from core.database.connection_pool import ConnectionPool


class TestDatabaseFlow(unittest.TestCase):
    """Integration tests for database operations"""
    
    def setUp(self):
        """Tạo database tạm cho test"""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Tạo bảng test
        self._create_test_tables()
        
        self.pool = ConnectionPool(self.db_path, max_connections=3)
        self.optimizer = DBOptimizer(self.db_path)
    
    def _create_test_tables(self):
        """Tạo bảng test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        """)
        
        # Insert test data
        cursor.executemany(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            [("User 1", "user1@test.com"), ("User 2", "user2@test.com")]
        )
        
        conn.commit()
        conn.close()
    
    def test_connection_pool(self):
        """Test connection pool"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_users")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2)
    
    def test_multiple_connections(self):
        """Test nhiều kết nối cùng lúc"""
        connections = []
        
        for i in range(5):
            conn = self.pool._create_connection()
            connections.append(conn)
        
        for conn in connections:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            conn.close()
    
    def test_create_indexes(self):
        """Test tạo indexes"""
        self.optimizer.create_indexes()
        
        # Kiểm tra index đã được tạo
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchall()
        conn.close()
        
        self.assertGreater(len(indexes), 0)
    
    def test_vacuum(self):
        """Test VACUUM"""
        # Insert nhiều dữ liệu
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for i in range(100):
            cursor.execute("INSERT INTO test_users (name, email) VALUES (?, ?)", 
                          (f"User {i}", f"user{i}@test.com"))
        conn.commit()
        conn.close()
        
        # Chạy VACUUM
        self.optimizer.vacuum()
        
        # Kiểm tra database vẫn hoạt động
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM test_users")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 100)
    
    def tearDown(self):
        """Dọn dẹp sau test"""
        self.pool.close_all()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)


if __name__ == "__main__":
    unittest.main()