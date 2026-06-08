from .database import Database

class PurchaseOrder:
    @staticmethod
    def create(date, product_code, quantity, unit_price, supplier):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO purchase_orders (date, product_code, quantity, unit_price, supplier)
                VALUES (?, ?, ?, ?, ?)
            ''', (date, product_code, quantity, unit_price, supplier))
            return cursor.lastrowid
    
    @staticmethod
    def get_all():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM purchase_orders ORDER BY date DESC")
            return cursor.fetchall()