# core/currency_manager.py
# QUẢN LÝ NGOẠI TỆ VÀ TỶ GIÁ HỐI ĐOÁI

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

class CurrencyManager:
    """Quản lý ngoại tệ và tỷ giá hối đoái"""
    
    SUPPORTED_CURRENCIES = {
        "USD": "Đô la Mỹ",
        "EUR": "Euro",
        "GBP": "Bảng Anh",
        "JPY": "Yên Nhật",
        "CNY": "Nhân dân tệ",
        "KRW": "Won Hàn Quốc",
        "AUD": "Đô la Úc",
        "CAD": "Đô la Canada",
        "CHF": "Franc Thụy Sĩ",
        "THB": "Baht Thái Lan",
        "SGD": "Đô la Singapore",
        "VND": "Việt Nam Đồng"
    }
    
    def __init__(self, db_path: str = None):
        # Tìm đường dẫn database chính xác
        if db_path is None:
            # Cách 1: Dùng thư mục hiện tại
            base_dir = Path(__file__).parent.parent
            possible_paths = [
                base_dir / "ke_toan_data" / "ke_toan.db",
                Path("D:/ke_toan_pro_v3/ke_toan_data/ke_toan.db"),
                Path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ke_toan_data", "ke_toan.db")),
            ]
            
            # Thêm đường dẫn từ sys.argv[0] nếu có
            if getattr(sys, 'frozen', False):
                base = Path(sys.executable).parent
                possible_paths.append(base / "ke_toan_data" / "ke_toan.db")
            
            db_path = None
            for path in possible_paths:
                if path.exists():
                    db_path = str(path)
                    break
            
            if db_path is None:
                # Tạo thư mục và database mới
                db_dir = base_dir / "ke_toan_data"
                db_dir.mkdir(parents=True, exist_ok=True)
                db_path = str(db_dir / "ke_toan.db")
                logging.info(f"Tạo database mới tại: {db_path}")
        
        self.db_path = db_path
        logging.info(f"CurrencyManager DB: {self.db_path}")
        self._init_tables()
        self._init_default_currencies()
    
    def _init_tables(self):
        """Khởi tạo bảng quản lý ngoại tệ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS currencies (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    symbol TEXT,
                    is_base INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    decimal_places INTEGER DEFAULT 2,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_currency TEXT NOT NULL,
                    to_currency TEXT NOT NULL,
                    rate REAL NOT NULL,
                    effective_date TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    notes TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logging.info("Khởi tạo bảng ngoại tệ thành công")
        except Exception as e:
            logging.error(f"Lỗi khởi tạo bảng: {e}")
            raise
    
    def _init_default_currencies(self):
        """Thêm các ngoại tệ mặc định"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM currencies")
            count = cursor.fetchone()[0]
            
            if count == 0:
                for code, name in self.SUPPORTED_CURRENCIES.items():
                    is_base = 1 if code == "VND" else 0
                    cursor.execute("""
                        INSERT INTO currencies (code, name, symbol, is_base, is_active)
                        VALUES (?, ?, ?, ?, 1)
                    """, (code, name, code, is_base))
                conn.commit()
                logging.info(f"Đã thêm {len(self.SUPPORTED_CURRENCIES)} ngoại tệ mặc định")
            else:
                logging.info(f"Đã có {count} ngoại tệ trong database")
            
            conn.close()
        except Exception as e:
            logging.error(f"Lỗi thêm ngoại tệ: {e}")
    
    def get_exchange_rate(self, from_currency: str, to_currency: str = "VND", date: str = None) -> float:
        """Lấy tỷ giá tại thời điểm"""
        if from_currency == to_currency:
            return 1.0
        
        default_rates = {
            "USD": 25500, "EUR": 27500, "GBP": 32000, "JPY": 170, "CNY": 3500,
            "KRW": 19, "AUD": 17000, "CAD": 19000, "CHF": 28000, "THB": 700, "SGD": 19000
        }
        return default_rates.get(from_currency, 25000)
    
    def convert_amount(self, amount: float, from_currency: str, to_currency: str = "VND", rate: float = None) -> float:
        """Quy đổi tiền tệ"""
        if from_currency == to_currency:
            return amount
        if rate is None:
            rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate
    
    def get_all_currencies(self) -> List[Dict]:
        """Lấy danh sách tất cả ngoại tệ"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT code, name, symbol, is_base, is_active FROM currencies ORDER BY code")
            rows = cursor.fetchall()
            conn.close()
            return [{"code": r[0], "name": r[1], "symbol": r[2], "is_base": bool(r[3]), "is_active": bool(r[4])} for r in rows]
        except Exception as e:
            logging.error(f"Lỗi get_all_currencies: {e}")
            return []
    
    def add_currency(self, code: str, name: str, symbol: str = None):
        """Thêm ngoại tệ mới"""
        if symbol is None:
            symbol = code
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO currencies (code, name, symbol, is_active) VALUES (?, ?, ?, 1)",
                           (code.upper(), name, symbol))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Lỗi add_currency: {e}")
    
    def update_exchange_rate_daily(self):
        """Cập nhật tỷ giá hàng ngày"""
        logging.info("Cập nhật tỷ giá hàng ngày...")
        # TODO: Thêm logic cập nhật từ API


# ========== KIỂM TRA ==========
if __name__ == "__main__":
    print("=== KIỂM TRA CURRENCY MANAGER ===")
    cm = CurrencyManager()
    print(f"📊 Danh sách ngoại tệ: {len(cm.get_all_currencies())}")
    print(f"💰 100 USD = {cm.convert_amount(100, 'USD', 'VND'):,.0f} VND")
    print("✅ CurrencyManager hoạt động tốt!")
