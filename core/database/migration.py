# -*- coding: utf-8 -*-
"""
Database Migration - Quản lý version database & Tự động tạo bảng Xăng Dầu - Nhật Ký
Hệ thống nâng cấp chuyên dụng - Kế Toán Pro v5.2.0 - Thầy Hùng phát triển
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Quản lý migration database nâng cấp hệ thống"""
    
    # Nâng version lên 3 để kích hoạt luồng tạo bảng mới tự động
    VERSION = 3  
    
    MIGRATIONS = {
        1: """
            -- Version 1: Cấu trúc database cũ (giữ nguyên)
        """,
        2: """
            -- Version 2: Thêm bảng kế toán lõi
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                reference_no TEXT,
                created_by TEXT,
                fiscal_year INTEGER,
                period INTEGER,
                created_at TEXT,
                is_reversed INTEGER DEFAULT 0,
                reversed_by_id INTEGER,
                reversed_reason TEXT
            );
            
            CREATE TABLE IF NOT EXISTS journal_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER NOT NULL,
                account_code TEXT NOT NULL,
                account_name TEXT NOT NULL,
                debit_amount REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
            );
            
            CREATE TABLE IF NOT EXISTS account_balances (
                account_code TEXT PRIMARY KEY,
                balance REAL DEFAULT 0,
                last_updated TEXT
            );
            
            -- ALTER TABLE transactions ADD COLUMN journal_entry_id INTEGER;
        """,
        3: """
            -- =========================================================
            -- VERSION 3: TỰ ĐỘNG KHỞI TẠO PHÂN HỆ NHẬT KÝ BẢO MẬT & XĂNG DẦU
            -- =========================================================
            
            -- A. BẢNG NHẬT KÝ BẢO MẬT (AUDIT LOG SYSTEM)
            CREATE TABLE IF NOT EXISTS system_audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_time TEXT NOT NULL,
                user_name TEXT NOT NULL,
                action_type TEXT NOT NULL,   -- ĐĂNG NHẬP, KHÓA SỔ, XUẤT HÓA ĐƠN...
                description TEXT,
                ip_address TEXT
            );

            -- B. BẢNG QUẢN LÝ BỂ CHỨA XĂNG DẦU (GAS TANKS)
            CREATE TABLE IF NOT EXISTS gas_tanks (
                tank_id TEXT PRIMARY KEY,
                tank_name TEXT NOT NULL,
                fuel_type TEXT NOT NULL,         -- RON 95-V, E5 RON 92, DO...
                capacity REAL NOT NULL,           -- Dung tích tối đa (Lít)
                current_volume REAL DEFAULT 0,     -- Tồn kho hiện tại trong bồn
                temperature_standard REAL DEFAULT 15.0
            );
            
            -- C. BẢNG QUẢN LÝ VÒI BƠM TRỤ CƠ (GAS PUMPS)
            CREATE TABLE IF NOT EXISTS gas_pumps (
                pump_id TEXT PRIMARY KEY,
                pump_name TEXT NOT NULL,
                tank_id TEXT,
                last_index REAL DEFAULT 0,         -- Số công tơ vòi bơm gần nhất
                FOREIGN KEY (tank_id) REFERENCES gas_tanks(tank_id)
            );
            
            -- D. BẢNG NHẬT KÝ CHỐT CA TRỰC XĂNG DẦU (HAOHỤT QUY ĐỔI 15°C)
            CREATE TABLE IF NOT EXISTS gas_shift_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_date TEXT NOT NULL,
                shift_name TEXT NOT NULL,
                pump_id TEXT NOT NULL,
                staff_name TEXT,
                start_index REAL NOT NULL,
                end_index REAL NOT NULL,
                volume_sold REAL NOT NULL,          -- Thể tích lít cơ học bán ra
                price REAL NOT NULL,                -- Đơn giá
                total_money REAL NOT NULL,          -- Tổng thành tiền doanh thu ca
                density REAL DEFAULT 0.750,         -- Tỷ trọng dầu khí
                temp_actual REAL DEFAULT 30.0,      -- Nhiệt độ bồn khi đo
                volume_standard REAL,               -- Số lít quy chuẩn về 15°C để báo thuế
                created_at TEXT,
                FOREIGN KEY (pump_id) REFERENCES gas_pumps(pump_id)
            );
        """
    }
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_current_version(self) -> int:
        """Lấy version hiện tại của database từ bảng quản lý hệ thống"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT
                )
            ''')
            cursor.execute('SELECT version FROM schema_version ORDER BY version DESC LIMIT 1')
            row = cursor.fetchone()
            return row[0] if row else 1
        except Exception as e:
            logger.error(f"Lỗi kiểm tra schema version: {e}")
            return 1
        finally:
            conn.close()
    
    def migrate(self, target_version: int = None):
        """Chạy tự động quét nâng cấp cấu trúc database lên version cao nhất"""
        current = self.get_current_version()
        target = target_version or self.VERSION
        
        if current >= target:
            logger.info(f"Database đã ở version {current}, không cần migrate")
            return
        
        logger.info(f"⚡ Tiến hành nâng cấp cấu trúc Database từ version {current} lên {target}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for version in range(current + 1, target + 1):
            if version in self.MIGRATIONS:
                logger.info(f"Chạy tập lệnh nâng cấp Version {version}")
                try:
                    cursor.executescript(self.MIGRATIONS[version])
                    
                    # Chèn vết nạp dữ liệu mẫu cho Xăng dầu ở phiên bản 3 để có sẵn dữ liệu test
                    if version == 3:
                        cursor.execute("SELECT COUNT(*) FROM gas_tanks")
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("INSERT INTO gas_tanks VALUES ('BON_01', 'Bồn Xăng RON95', 'RON 95-V', 20000.0, 15000.0, 15.0)")
                            cursor.execute("INSERT INTO gas_tanks VALUES ('BON_02', 'Bồn Dầu DO', 'DO 0.05S', 15000.0, 9500.0, 15.0)")
                            cursor.execute("INSERT INTO gas_pumps VALUES ('VOI_01', 'Vòi Trụ 01 - RON95', 'BON_01', 102500.0)")
                            cursor.execute("INSERT INTO gas_pumps VALUES ('VOI_02', 'Vòi Trụ 02 - DO', 'BON_02', 45200.0)")
                    
                    cursor.execute('''
                        INSERT INTO schema_version (version, applied_at)
                        VALUES (?, ?)
                    ''', (version, datetime.now().isoformat()))
                    conn.commit()
                except Exception as e:
                    logger.error(f"❌ Thất bại khi chạy nâng cấp phiên bản {version}: {e}")
                    conn.rollback()
                    raise
        
        conn.close()
        logger.info(f"🎉 Nâng cấp Database thành công! Phiên bản hiện tại: {target}")


def run_migration_if_needed(db_path: str):
    """Chạy cấu trúc tự động (Được kích hoạt khi Thầy bật phần mềm Kế Toán Pro)"""
    migrator = DatabaseMigrator(db_path)
    migrator.migrate()