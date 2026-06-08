# -*- coding: utf-8 -*-
"""
DBSecurity - Bao ve database
"""

import os
import sqlite3
import hashlib
from datetime import datetime
import logging
from utils.logger import get_logger
logger = get_logger(__name__)

class DatabaseSecurity:
    """Bao mat database"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_security_table()
    
    def _init_security_table(self):
        """Tao bang luu log bao mat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                table_name TEXT,
                record_id INTEGER,
                user TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                details TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_action(self, action, table_name, record_id, user="system", details=""):
        """Ghi log hanh dong"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO security_log (action, table_name, record_id, user, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (action, table_name, record_id, user, details))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Lỗi ghi log: {e}")
            return False
    
    def get_audit_trail(self, table_name=None, limit=100):
        """Lay lich su thao tac"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if table_name:
                cursor.execute('''
                    SELECT * FROM security_log 
                    WHERE table_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (table_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM security_log 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            logger.error(f"Lỗi lấy audit trail: {e}")
            return []
        finally:
            conn.close()
    
    def backup_database(self, backup_path=None):
        """Sao luu database"""
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.dirname(self.db_path)
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        self.log_action("BACKUP", "database", 0, "system", f"Backup to {backup_path}")
        return backup_path