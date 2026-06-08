# -*- coding: utf-8 -*-
"""
Transaction Model - Ghi sổ kép đúng chuẩn kế toán
"""

import sqlite3
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Transaction:
    """Model giao dịch kế toán - Chuẩn double-entry"""
    
    # Hệ thống tài khoản kế toán Việt Nam (QĐ 48/2006/QĐ-BTC)
    ACCOUNTS = {
        # Tài sản (1xx)
        '111': 'Tiền mặt',
        '112': 'Tiền gửi ngân hàng',
        '131': 'Phải thu khách hàng',
        '141': 'Tạm ứng',
        '151': 'Hàng mua đang đi đường',
        '152': 'Nguyên liệu, vật liệu',
        '153': 'Công cụ, dụng cụ',
        '156': 'Hàng hóa',
        '211': 'TSCĐ hữu hình',
        '214': 'Hao mòn TSCĐ',
        
        # Nguồn vốn (3xx)
        '311': 'Vay ngắn hạn',
        '331': 'Phải trả người bán',
        '333': 'Thuế phải nộp',
        '334': 'Phải trả người lao động',
        '338': 'Phải trả khác',
        '411': 'Vốn đầu tư chủ sở hữu',
        '421': 'Lợi nhuận chưa phân phối',
        
        # Doanh thu (5xx)
        '511': 'Doanh thu bán hàng',
        '515': 'Doanh thu hoạt động tài chính',
        '521': 'Chiết khấu thương mại',
        
        # Chi phí (6xx)
        '611': 'Mua hàng',
        '621': 'Chi phí nguyên liệu trực tiếp',
        '627': 'Chi phí sản xuất chung',
        '632': 'Giá vốn hàng bán',
        '635': 'Chi phí tài chính',
        '641': 'Chi phí bán hàng',
        '642': 'Chi phí quản lý doanh nghiệp',
        
        # Thu nhập khác (7xx)
        '711': 'Thu nhập khác',
        '811': 'Chi phí khác',
        
        # Xác định KQKD (9xx)
        '911': 'Xác định kết quả kinh doanh',
    }
    
    def __init__(self, db_connection) -> None:
        """Khởi tạo với connection pool"""
        self.conn = db_connection
        # ⭐ Thêm dòng này để có thể truy cập dữ liệu theo tên cột (ví dụ: row['date'])
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()
    
    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Kiểm tra định dạng ngày"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _to_decimal(amount) -> Decimal:
        """Chuyển đổi sang Decimal để tránh sai số float"""
        try:
            return Decimal(str(amount))
        except Exception:
            return Decimal('0')
            
    # File: models/transaction.py

    @staticmethod
    def get_all(db_connection=None, from_date: str = None, to_date: str = None) -> list:
        """
        Lấy danh sách giao dịch: Bảo toàn lọc ngày tháng và bổ sung sắp xếp theo ID.
        Đã sửa lỗi kiểm tra kiểu dữ liệu db_connection để tránh lỗi 'int' object.
        """
        import sqlite3
        # Kiểm tra nếu db_connection không phải là đối tượng kết nối hợp lệ
        if db_connection is None or isinstance(db_connection, int):
            from data_config import DB_PATH
            db_connection = sqlite3.connect(DB_PATH)
            should_close = True
        else:
            should_close = False
            
        try:
            cursor = db_connection.cursor()
            # Cải tiến: Liệt kê rõ các cột bao gồm id và thêm ORDER BY để số dư chuẩn xác
            query = "SELECT id, date, description, amount, type, category FROM transactions WHERE 1=1"
            params = []
            
            if from_date:
                query += " AND date >= ?"
                params.append(from_date)
            if to_date:
                query += " AND date <= ?"
                params.append(to_date)
                
            # Sắp xếp theo ngày tăng dần, nếu trùng ngày thì ưu tiên ID nhỏ (nhập trước) đứng trước
            query += " ORDER BY date ASC, id ASC"
                
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Lỗi Transaction.get_all: {e}")
            return []
        finally:
            if should_close:
                db_connection.close()
    
    def create_journal_entry(
        self,
        date: str,
        description: str,
        entries: List[Dict[str, Any]],
        reference_no: str = None,
        created_by: str = None,
        fiscal_year: int = None,
        period: int = None
    ) -> int:
        """
        Tạo bút toán kế toán (có thể có nhiều dòng Nợ/Có)
        
        Args:
            date: Ngày hạch toán (YYYY-MM-DD)
            description: Diễn giải
            entries: Danh sách các dòng, mỗi dòng có:
                {
                    'account': '111',
                    'debit': 1000000,
                    'credit': 0
                }
            reference_no: Số chứng từ gốc
            created_by: Người nhập
            fiscal_year: Năm tài chính
            period: Kỳ kế toán (1-12)
        
        Returns:
            journal_entry_id
        """
        if not self._validate_date(date):
            raise ValueError(f"Ngày không hợp lệ: {date}. Định dạng YYYY-MM-DD")
        
        # Kiểm tra tổng Nợ = tổng Có
        total_debit = sum(self._to_decimal(e.get('debit', 0)) for e in entries)
        total_credit = sum(self._to_decimal(e.get('credit', 0)) for e in entries)
        
        if total_debit != total_credit:
            raise ValueError(
                f"Bút toán không cân đối! Tổng Nợ={total_debit}, Tổng Có={total_credit}"
            )
        
        if total_debit == 0:
            raise ValueError("Bút toán phải có giá trị > 0")
        
        cursor = self.conn.cursor()
        
        try:
            # Bắt đầu transaction
            cursor.execute("BEGIN")
            
            # Tạo journal entry header
            fiscal_year = fiscal_year or datetime.now().year
            period = period or datetime.strptime(date, '%Y-%m-%d').month
            
            cursor.execute('''
                INSERT INTO journal_entries (
                    date, description, reference_no, created_by,
                    fiscal_year, period, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date, description, reference_no, created_by,
                fiscal_year, period, datetime.now().isoformat()
            ))
            
            journal_id = cursor.lastrowid
            
            # Tạo các dòng chi tiết (Nợ/Có)
            for entry in entries:
                debit = self._to_decimal(entry.get('debit', 0))
                credit = self._to_decimal(entry.get('credit', 0))
                account = entry.get('account')
                
                if account not in self.ACCOUNTS:
                    raise ValueError(f"Tài khoản không hợp lệ: {account}")
                
                cursor.execute('''
                    INSERT INTO journal_details (
                        journal_entry_id, account_code, account_name,
                        debit_amount, credit_amount
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    journal_id, account, self.ACCOUNTS[account],
                    float(debit), float(credit)
                ))
            
            # Cập nhật số dư tài khoản
            self._update_account_balances(journal_id)
            
            cursor.execute("COMMIT")
            logger.info(f"Đã tạo bút toán #{journal_id}: {description}")
            return journal_id
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Lỗi tạo bút toán: {e}")
            raise
    
    def _update_account_balances(self, journal_id: int):
        """Cập nhật số dư các tài khoản sau khi ghi sổ"""
        cursor = self.conn.cursor()
        
        # Lấy tất cả tài khoản trong bút toán
        cursor.execute('''
            SELECT account_code, debit_amount, credit_amount
            FROM journal_details
            WHERE journal_entry_id = ?
        ''', (journal_id,))
        
        for account_code, debit, credit in cursor.fetchall():
            # Cập nhật hoặc chèn số dư mới
            cursor.execute('''
                INSERT INTO account_balances (account_code, balance, last_updated)
                VALUES (?, 
                    COALESCE((SELECT balance FROM account_balances WHERE account_code = ?), 0) + ? - ?,
                    ?
                )
                ON CONFLICT(account_code) DO UPDATE SET
                    balance = balance + ? - ?,
                    last_updated = ?
            ''', (account_code, account_code, debit, credit, datetime.now().isoformat(),
                  debit, credit, datetime.now().isoformat()))
    
    def get_trial_balance(self, as_of_date: str = None) -> List[Dict]:
        """
        Lấy bảng cân đối thử
        Tổng dư Nợ = Tổng dư Có
        """
        cursor = self.conn.cursor()
        
        query = '''
            SELECT 
                account_code,
                account_name,
                SUM(debit_amount) as total_debit,
                SUM(credit_amount) as total_credit,
                SUM(debit_amount - credit_amount) as balance
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
        '''
        
        if as_of_date:
            query += f" WHERE je.date <= '{as_of_date}'"
        
        query += " GROUP BY account_code ORDER BY account_code"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        total_debit = sum(r['total_debit'] for r in results)
        total_credit = sum(r['total_credit'] for r in results)
        
        logger.info(f"Cân đối thử: Nợ={total_debit}, Có={total_credit}")
        
        if abs(total_debit - total_credit) > 0.01:
            logger.error(f"CÂN ĐỐI KHÔNG KHỚP! Chênh lệch: {total_debit - total_credit}")
        
        return results
        
    @staticmethod  # ⭐ Giữ nguyên dòng này
    def get_income_statement(db_conn, from_date: str, to_date: str) -> Dict: # ⭐ Đổi 'self' thành 'db_conn'
        """
        Báo cáo kết quả hoạt động kinh doanh
        Doanh thu - Chi phí = Lợi nhuận
        """
        cursor = db_conn.cursor() # ⭐ Đổi 'self.conn' thành 'db_conn'
        
        # Doanh thu (tài khoản 5xx, 7xx có số dư Có)
        cursor.execute('''
            SELECT account_code, SUM(credit_amount - debit_amount) as revenue
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
            WHERE je.date BETWEEN ? AND ?
                AND account_code LIKE '5%'
            GROUP BY account_code
        ''', (from_date, to_date))
        
        revenues = cursor.fetchall()
        # Chuyển đổi sang Decimal hoặc float để tính toán an toàn
        total_revenue = sum(float(r['revenue'] or 0) for r in revenues)
        
        # Chi phí (tài khoản 6xx, 8xx có số dư Nợ)
        cursor.execute('''
            SELECT account_code, SUM(debit_amount - credit_amount) as expense
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
            WHERE je.date BETWEEN ? AND ?
                AND account_code LIKE '6%'
            GROUP BY account_code
        ''', (from_date, to_date))
        
        expenses = cursor.fetchall()
        total_expense = sum(float(e['expense'] or 0) for e in expenses)
        
        net_profit = total_revenue - total_expense
        
        return {
            'from_date': from_date,
            'to_date': to_date,
            'revenues': revenues,
            'total_revenue': total_revenue,
            'expenses': expenses,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'net_profit_text': f"{'Lãi' if net_profit > 0 else 'Lỗ'}: {abs(net_profit):,.0f}đ"
        }
    
    def get_voucher_entry(self, voucher_type: str, voucher_no: str) -> Dict:
        """Lấy chứng từ ghi sổ theo số và loại"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT je.*, jd.account_code, jd.account_name, 
                   jd.debit_amount, jd.credit_amount
            FROM journal_entries je
            JOIN journal_details jd ON je.id = jd.journal_entry_id
            WHERE je.reference_no = ?
        ''', (f"{voucher_type}{voucher_no}",))
        
        rows = cursor.fetchall()
        if not rows:
            return None
        
        return {
            'header': rows[0],
            'details': rows
        }
    
    def reverse_entry(self, journal_id: int, reason: str, reversed_by: str) -> int:
        """Đảo bút toán (sửa lỗi)"""
        # Lấy bút toán gốc
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM journal_entries WHERE id = ?
        ''', (journal_id,))
        
        original = cursor.fetchone()
        if not original:
            raise ValueError(f"Không tìm thấy bút toán #{journal_id}")
        
        # Tạo bút toán đảo (đổi Nợ thành Có và ngược lại)
        cursor.execute('''
            SELECT account_code, debit_amount, credit_amount
            FROM journal_details
            WHERE journal_entry_id = ?
        ''', (journal_id,))
        
        reversed_entries = []
        for row in cursor.fetchall():
            reversed_entries.append({
                'account': row['account_code'],
                'debit': row['credit_amount'],
                'credit': row['debit_amount']
            })
        
        # Tạo bút toán đảo
        reverse_id = self.create_journal_entry(
            date=datetime.now().strftime('%Y-%m-%d'),
            description=f"ĐẢO BÚT TOÁN #{journal_id} - {reason}",
            entries=reversed_entries,
            reference_no=f"REV{journal_id}",
            created_by=reversed_by
        )
        
        # Đánh dấu bút toán gốc đã bị đảo
        cursor.execute('''
            UPDATE journal_entries 
            SET reversed_by_id = ?, reversed_reason = ?, is_reversed = 1
            WHERE id = ?
        ''', (reverse_id, reason, journal_id))
        
        logger.warning(f"Đã đảo bút toán #{journal_id} -> #{reverse_id}: {reason}")
        return reverse_id
        
    @staticmethod
    def get_total_income(db_connection=None):
        """
        Tính tổng doanh thu (Doanh thu bán hàng - tk 511)
        Bổ sung để sửa lỗi báo cáo tổng hợp.
        """
        import sqlite3
        if db_connection is None or isinstance(db_connection, int):
            db_connection = sqlite3.connect(get_db_path())
            should_close = True
        else:
            should_close = False
            
        try:
            cursor = db_connection.cursor()
            # Tính tổng số dư Có của tài khoản doanh thu 511
            query = """
                SELECT SUM(credit_amount - debit_amount) 
                FROM journal_details 
                WHERE account_code LIKE '511%'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0
        except Exception as e:
            logging.error(f"Lỗi Transaction.get_total_income: {e}")
            return 0.0
        finally:
            if should_close:
                db_connection.close()
        
    def _ensure_tables(self) -> None:
        """Tạo các bảng cần thiết nếu chưa có"""
        cursor = self.conn.cursor()
        
        # Bảng journal_entries
        cursor.execute('''
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
            )
        ''')
        
        # Bảng journal_details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER NOT NULL,
                account_code TEXT NOT NULL,
                account_name TEXT NOT NULL,
                debit_amount REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id)
            )
        ''')
        
        # Bảng account_balances
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account_balances (
                account_code TEXT PRIMARY KEY,
                balance REAL DEFAULT 0,
                last_updated TEXT
            )
        ''')
        
        # ⭐ THÊM BẢNG NÀY (quan trọng cho giao diện)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_metadata (
                journal_id INTEGER PRIMARY KEY,
                type TEXT,
                category TEXT,
                description TEXT,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
        logger.info("Đã khởi tạo các bảng database")
        
    @staticmethod
    def update(transaction_id: int, **kwargs) -> bool:
        import sqlite3
        allowed_fields = ['date', 'description', 'amount', 'type', 'category']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                val = kwargs[field]
                # Nếu là ngày, chuẩn hóa từ dd/mm/yyyy sang yyyy-mm-dd để database hiểu
                if field == 'date' and '/' in str(val):
                    try:
                        day, month, year = val.split('/')
                        val = f"{year}-{month}-{day}"
                    except Exception: pass
                updates.append(f"{field}=?")
                values.append(val)
        
        if not updates: return False
        values.append(transaction_id)
        
        db_path = get_db_path()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                query = f"UPDATE transactions SET {','.join(updates)} WHERE id=?"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Lỗi SQL: {e}")
            return False


# Helper functions for common transactions
def create_sales_entry(conn, date: str, customer_account: str, amount: float, description: str, created_by: str) -> int:
    """Tạo bút toán bán hàng"""
    return Transaction(conn).create_journal_entry(
        date=date,
        description=description,
        entries=[
            {'account': '111', 'debit': amount, 'credit': 0},  # Tiền mặt
            {'account': '511', 'debit': 0, 'credit': amount},  # Doanh thu
        ],
        reference_no=f"HD{date.replace('-', '')}",
        created_by=created_by
    )


def create_purchase_entry(conn, date: str, amount: float, description: str, created_by: str) -> int:
    """Tạo bút toán mua hàng"""
    return Transaction(conn).create_journal_entry(
        date=date,
        description=description,
        entries=[
            {'account': '156', 'debit': amount, 'credit': 0},  # Hàng hóa
            {'account': '331', 'debit': 0, 'credit': amount},  # Phải trả NB
        ],
        reference_no=f"PN{date.replace('-', '')}",
        created_by=created_by
    )
        

