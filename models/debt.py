# -*- coding: utf-8 -*-
from .database import Database
from datetime import datetime
import logging

class Debt:
    """Model quản lý công nợ khách hàng - Bản sửa lỗi tham số"""

    # === Các phương thức quản lý nợ theo tên & số điện thoại ===
    @staticmethod
    def create(name, phone, total_debt=0, paid=0, last_debt_date=None, notes=""):
        if last_debt_date is None:
            last_debt_date = datetime.now().strftime("%d/%m/%Y")
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Cập nhật hoặc tạo mới công nợ (Đã sửa để không cộng dồn)
            cursor.execute("SELECT id FROM debts WHERE notes = ?", (notes,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE debts SET total_debt = ?, paid = ?, last_debt_date = ?
                    WHERE notes = ?
                ''', (total_debt, paid, last_debt_date, notes))
            else:
                cursor.execute('''
                    INSERT INTO debts (name, phone, total_debt, paid, last_debt_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, phone, total_debt, paid, last_debt_date, notes))
            
            # 2. HOÀN THIỆN NGHIỆP VỤ KẾ TOÁN: Ghi nhận dòng tiền vào sổ Nhật ký
            # Đây là bước giúp "dòng tiền chảy" vào sổ sách của bạn
            cursor.execute('''
                INSERT INTO journal_entries (date, description, debit, credit, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (last_debt_date, f"Ghi nhận nợ KH: {name}", total_debt, paid, notes))
            
            return True

    @staticmethod
    def add_debt(name, phone, amount, date=None, notes=""):
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM debts WHERE name=? AND phone=?", (name, phone))
            existing = cursor.fetchone()
            if existing:
                # SỬA: Dùng ghi đè thay vì cộng dồn (bỏ dấu +)
                cursor.execute('''
                    UPDATE debts SET total_debt = ?, last_debt_date = ?, notes = ?
                    WHERE name=? AND phone=?
                ''', (amount, date, notes, name, phone))
            else:
                # Thêm mới nếu chưa có
                cursor.execute('''
                    INSERT INTO debts (name, phone, total_debt, paid, last_debt_date, notes)
                    VALUES (?, ?, ?, 0, ?, ?)
                ''', (name, phone, amount, date, notes))
            return True

    @staticmethod
    def record_payment(name, phone, amount, date=None, notes=""):
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE debts SET paid = paid + ?, last_debt_date = ?, notes = ?
                WHERE name=? AND phone=?
            ''', (amount, date, notes, name, phone))
            return cursor.rowcount > 0

    # File: models/debt.py

    @staticmethod
    def get_all(db_connection=None):
        """
        Lấy danh sách công nợ. 
        Đã đồng bộ tuyệt đối: Lấy tất cả cột gốc và tạo thêm các cột định danh (alias) cho UI.
        """
        import sqlite3
        from data_config import DB_PATH
        should_close = False
        if db_connection is None:
            db_connection = sqlite3.connect(DB_PATH)
            should_close = True
            
        try:
            cursor = db_connection.cursor()
            # Sử dụng SELECT * để lấy mọi cột (bao gồm cả notes, phone, total_debt, paid...)
            # Đồng thời giữ lại các cột alias (as) để Dashboard không bị lỗi.
            query = (
                "SELECT *, name as customer_name, (total_debt - paid) as amount, "
                "last_debt_date as due_date "
                "FROM debts"
            )
            
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Lỗi Debt.get_all: {e}")
            return []
        finally:
            if should_close:
                db_connection.close()
                
    @staticmethod
    def get_by_name_phone(name, phone):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM debts WHERE name=? AND phone=?", (name, phone))
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            return None

    @staticmethod
    def delete(name, phone):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM debts WHERE name=? AND phone=?", (name, phone))
            return cursor.rowcount > 0

    # === Các phương thức hỗ trợ đồng bộ hóa với Hóa đơn (Invoice)[cite: 6] ===
    @staticmethod
    def update_or_create_debt(invoice_id, customer_name, customer_phone, remaining, date):
        """Đồng bộ nợ: Cộng dồn theo tên nhưng không làm mất lịch sử hóa đơn."""
        if date is None:
            date = datetime.now().strftime("%d/%m/%Y")
            
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Tìm theo tên khách hàng
            cursor.execute("SELECT id, total_debt FROM debts WHERE name = ? LIMIT 1", (customer_name,))
            record = cursor.fetchone()
            
            if remaining > 0:
                if record:
                    # ĐÃ CÓ: Cộng dồn nợ, giữ nguyên các thông tin cũ, chỉ cập nhật mới nhất
                    cursor.execute('''
                        UPDATE debts 
                        SET total_debt = total_debt + ?, 
                            last_debt_date = ?, 
                            notes = ?
                        WHERE id = ?
                    ''', (remaining, date, f"Cập nhật hóa đơn {invoice_id}", record[0]))
                else:
                    # CHƯA CÓ: Tạo mới
                    cursor.execute('''
                        INSERT INTO debts (invoice_id, name, phone, total_debt, paid, last_debt_date, notes)
                        VALUES (?, ?, ?, ?, 0, ?, ?)
                    ''', (invoice_id, customer_name, customer_phone, remaining, date, 
                          f"Hóa đơn {invoice_id}"))
            else:
                # NẾU TRẢ HẾT: Không nên xóa cả dòng, mà chỉ trừ đi số nợ của hóa đơn đó
                # Nếu bạn muốn đơn giản nhất là cập nhật lại nợ (trừ đi phần đã trả), 
                # thì dùng lệnh này để an toàn hơn:
                cursor.execute('''
                    UPDATE debts 
                    SET total_debt = MAX(0, total_debt - ?),
                        notes = ?
                    WHERE name = ?
                ''', (abs(remaining), f"Đã thanh toán hóa đơn {invoice_id}", customer_name))
                
            return True
            
    @staticmethod
    def delete_by_invoice(invoice_id):
        """Xóa nợ khi hủy hóa đơn[cite: 6]"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM debts WHERE invoice_id = ?", (invoice_id,))
            return cursor.rowcount > 0