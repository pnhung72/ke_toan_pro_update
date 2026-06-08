from .database import Database

class Product:
    @staticmethod
    def create(code, name, unit, price_sell, price_buy, stock=0, min_stock=0):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO products (code, name, unit, price_sell, price_buy, stock, min_stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, unit, price_sell, price_buy, stock, min_stock))
            return cursor.lastrowid

    @staticmethod
    def get_all():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY name")
            return cursor.fetchall()

    @staticmethod
    def get_by_code(code):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE code=?", (code,))
            return cursor.fetchone()

    @staticmethod
    def update(code, **kwargs):
        allowed_fields = ['name', 'unit', 'price_sell', 'price_buy', 'stock', 'min_stock']
        updates = []
        values = []
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field}=?")
                values.append(kwargs[field])
        if updates:
            values.append(code)
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE products SET {','.join(updates)} WHERE code=?", values)
                return cursor.rowcount > 0
        return False

    @staticmethod
    def delete(code):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE code=?", (code,))
            return cursor.rowcount > 0

    @staticmethod
    def update_stock(code, quantity, add=True, conn=None):
        """
        Cập nhật tồn kho.
        - add=True: nhập kho (tăng), add=False: xuất kho (giảm).
        - Nếu conn được truyền vào, sử dụng kết nối đó (dùng chung transaction).
        - Nếu conn=None, tự mở kết nối mới.
        """
        #print(f"DEBUG: update_stock called - code={code}, quantity={quantity}, add={add}")  # <-- Thêm dòng này

        if conn is None:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                if add:
                    cursor.execute("UPDATE products SET stock = stock + ? WHERE code=?", (quantity, code))
                else:
                    cursor.execute("UPDATE products SET stock = stock - ? WHERE code=?", (quantity, code))
                return cursor.rowcount > 0
        else:
            cursor = conn.cursor()
            if add:
                cursor.execute("UPDATE products SET stock = stock + ? WHERE code=?", (quantity, code))
            else:
                cursor.execute("UPDATE products SET stock = stock - ? WHERE code=?", (quantity, code))
            return cursor.rowcount > 0

    @staticmethod
    def get_low_stock(min_threshold=10):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE stock <= min_stock AND min_stock > 0")
            return cursor.fetchall()
            
    @staticmethod
    def update_stock(product_code, quantity, add=True, conn=None):
        """Cập nhật tồn kho: add=True cộng, add=False trừ"""
        if conn is None:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET stock = stock + ? WHERE code = ?", 
                               (quantity if add else -quantity, product_code))
                return cursor.rowcount > 0
        else:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = stock + ? WHERE code = ?", 
                           (quantity if add else -quantity, product_code))
            return cursor.rowcount > 0