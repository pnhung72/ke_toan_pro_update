# models/customer_history.py
from .database import Database
from datetime import datetime

class CustomerHistory:
    @staticmethod
    def update(name, phone, address, tax_code):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO customer_history (name, phone, address, purchase_count, last_updated)
                VALUES (?, ?, ?, COALESCE((SELECT purchase_count FROM customer_history WHERE name=?), 0) + 1, ?)
            ''', (name, phone, address, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))