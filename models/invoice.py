from .database import Database
from datetime import datetime
from models.product import Product
import logging

logger = logging.getLogger(__name__)

class Invoice:
    @staticmethod
    def create(buyer_name, phone, tax_code, address, product_code, product_name,
               quantity, unit_price, total_excluding_tax, tax_amount, total_payment,
               paid, payment_method, sale_source="Cửa hàng", created_date=None, conn=None):
        """
        Tạo hóa đơn mới - Phiên bản 5.0.5 Hoàn thiện
        - Bảo toàn tính năng trừ kho và log debug.
        - Cho phép tùy chỉnh ngày tạo (không bị ghi đè).
        """
        # 1. Ưu tiên ngày Thầy nhập từ giao diện
        if not created_date or created_date == "":
            created_date = datetime.now().strftime("%d/%m/%Y")

        # 2. Xử lý các trường có thể để trống
        phone = phone if phone else None
        tax_code = tax_code if tax_code else None
        address = address if address else None
        product_name = product_name if product_name else None
        sale_source = sale_source if sale_source else "Cửa hàng"

        # 3. Hàm thực thi logic (Ghi hóa đơn + Trừ kho)
        def _execute_full_logic(conn_obj):
            cursor = conn_obj.cursor()
            # Thực hiện INSERT đủ 15 cột
            cursor.execute('''
                INSERT INTO invoices (
                    buyer_name, phone, tax_code, address, product_code, product_name,
                    quantity, unit_price, total_excluding_tax, tax_amount, total_payment,
                    paid, payment_method, sale_source, created_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                buyer_name, phone, tax_code, address, product_code, product_name,
                quantity, unit_price, total_excluding_tax, tax_amount, total_payment,
                paid, payment_method, sale_source, created_date
            ))
            invoice_id = cursor.lastrowid
            
            # Tính năng trừ kho và in debug (Bảo toàn tính năng hữu ích)
            #print(f"DEBUG: Invoice.create called with product_code={product_code}, quantity={quantity}")
            if product_code:
                Product.update_stock(product_code, quantity, add=False, conn=conn_obj)
            
            return invoice_id

        # 4. Điều hướng kết nối Database (Phải thụt đầu dòng đúng mức này)
        if conn:
            return _execute_full_logic(conn)
        else:
            with Database.get_connection() as new_conn:
                res = _execute_full_logic(new_conn)
                new_conn.commit()
                return res

    @staticmethod
    def get_all(limit=None):
        """
        Lấy danh sách hóa đơn: Đã chuyển sang dạng Dict và hỗ trợ sắp xếp cho Sổ cái.
        Tự động nhận diện tên bảng thực tế (invoice hoặc invoices) một cách an toàn tuyệt đối.
        """
        from .database import Database
        with Database.get_connection() as conn:
            # Dòng này cực kỳ quan trọng để lấy dữ liệu dạng inv['total_payment'] thay vì số thứ tự
            conn.row_factory = lambda cursor, row: {col[0]: row[i] for i, col in enumerate(cursor.description)}
            cursor = conn.cursor()
            
            # --- ĐOẠN KIỂM TRA VÀ TỰ ĐỘNG KHỚP TÊN BẢNG THỰC TẾ (ĐÃ FIX LỖI KEYERROR) ---
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            rows = cursor.fetchall()
            
            # Trích xuất tên bảng an toàn bất kể dữ liệu trả về là Tuple hay Dictionary
            existing_tables = []
            for row in rows:
                if isinstance(row, dict):
                    existing_tables.append(row.get('name'))
                elif isinstance(row, (tuple, list)) and len(row) > 0:
                    existing_tables.append(row[0])
            
            # Mặc định dùng 'invoice' (số ít) theo database thực tế, nếu không có thì dùng 'invoices'
            table_name = 'invoice' if 'invoice' in existing_tables else 'invoices'
            
            # Xây dựng câu lệnh truy vấn chuẩn xác theo tên bảng được phát hiện
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" ORDER BY id DESC LIMIT {limit}"
            else:
                query += " ORDER BY id DESC"
                
            cursor.execute(query)
            return cursor.fetchall()

    @staticmethod
    def get_by_id(invoice_id):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,))
            return cursor.fetchone()

    @staticmethod
    def update(invoice_id, **kwargs):
        """Cập nhật hóa đơn - ĐÃ HỖ TRỢ created_date"""
        allowed_fields = ['buyer_name', 'phone', 'tax_code', 'address', 'product_code', 'product_name',
                          'quantity', 'unit_price', 'total_excluding_tax', 'tax_amount',
                          'total_payment', 'paid', 'payment_method', 'sale_source', 'created_date']
        updates = []
        values = []
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field}=?")
                val = kwargs[field]
                # Xử lý các trường có thể để trống
                if field in ['phone', 'tax_code', 'address', 'product_name'] and val == '':
                    val = None
                values.append(val)
        if updates:
            values.append(invoice_id)
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE invoices SET {','.join(updates)} WHERE id=?", values)
                return cursor.rowcount > 0
        return False

    @staticmethod
    def delete(invoice_id):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
            return cursor.rowcount > 0

    @staticmethod
    def get_total_revenue():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(total_payment) FROM invoices")
            result = cursor.fetchone()[0]
            return result if result else 0

    @staticmethod
    def get_unpaid_invoices():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM invoices WHERE total_payment > paid")
            return cursor.fetchall()

    @staticmethod
    def get_invoices_by_customer(name=None, phone=None):
        """Lấy hóa đơn theo tên hoặc số điện thoại"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            if name and phone:
                cursor.execute(
                    "SELECT * FROM invoices WHERE buyer_name LIKE ? OR phone LIKE ?",
                    (f"%{name}%", f"%{phone}%")
                )
            elif name:
                cursor.execute(
                    "SELECT * FROM invoices WHERE buyer_name LIKE ?",
                    (f"%{name}%",)
                )
            elif phone:
                cursor.execute(
                    "SELECT * FROM invoices WHERE phone LIKE ?",
                    (f"%{phone}%",)
                )
            else:
                cursor.execute("SELECT * FROM invoices ORDER BY id DESC")
            return cursor.fetchall()
            
    @staticmethod
    def get_unpaid_invoices_by_customer(customer_name):
        """Lấy tất cả hóa đơn còn nợ của khách hàng (theo tên)"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM invoices 
                WHERE buyer_name = ? AND total_payment > paid
                ORDER BY created_date
            ''', (customer_name,))
            return cursor.fetchall()
            
    @staticmethod
    def get_by_year(year):
        """Lấy tất cả hóa đơn trong một năm (định dạng ngày dd/mm/yyyy)"""
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM invoices WHERE SUBSTR(created_date, 7, 4) = ?"
                cursor.execute(query, (str(year),))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Lỗi lấy hóa đơn theo năm {year}: {e}")
            return []
    
    @staticmethod
    def get_by_date_range(start_date, end_date):
        """Lấy hóa đơn trong khoảng thời gian (định dạng dd/mm/yyyy)"""
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                # Chuyển đổi định dạng ngày để so sánh (dd/mm/yyyy -> yyyymmdd)
                query = """
                    SELECT * FROM invoices 
                    WHERE SUBSTR(created_date, 7, 4) || SUBSTR(created_date, 4, 2) || SUBSTR(created_date, 1, 2)
                    BETWEEN ? AND ?
                    ORDER BY created_date
                """
                start_compare = start_date[6:10] + start_date[3:5] + start_date[0:2]
                end_compare = end_date[6:10] + end_date[3:5] + end_date[0:2]
                cursor.execute(query, (start_compare, end_compare))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Lỗi lấy hóa đơn theo khoảng ngày: {e}")
            return []
    
    @staticmethod
    def get_total_by_year(year):
        """Tính tổng doanh thu theo năm"""
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT SUM(total_payment) FROM invoices WHERE SUBSTR(created_date, 7, 4) = ?"
                cursor.execute(query, (str(year),))
                result = cursor.fetchone()[0]
                return result if result else 0
        except Exception as e:
            logger.error(f"Lỗi tính tổng doanh thu năm {year}: {e}")
            return 0
    
    @staticmethod
    def get_total_by_month(year, month):
        """Tính tổng doanh thu theo tháng"""
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                # Tìm các hóa đơn có năm và tháng khớp
                query = """
                    SELECT SUM(total_payment) FROM invoices 
                    WHERE SUBSTR(created_date, 7, 4) = ? 
                    AND SUBSTR(created_date, 4, 2) = ?
                """
                month_str = f"{month:02d}"
                cursor.execute(query, (str(year), month_str))
                result = cursor.fetchone()[0]
                return result if result else 0
        except Exception as e:
            logger.error(f"Lỗi tính tổng doanh thu tháng {month}/{year}: {e}")
            return 0