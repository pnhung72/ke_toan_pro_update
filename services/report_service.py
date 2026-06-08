# -*- coding: utf-8 -*-
"""
Report Service - Dịch vụ báo cáo thống kê (Đã cập nhật cho hệ thống kế toán kép)
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
import logging
import config
from core.database.connection_pool import get_connection_pool

logger = logging.getLogger(__name__)


class ReportService:
    """Dịch vụ báo cáo thống kê"""
    
    def __init__(self) -> None:
        # Khởi tạo connection pool
        data_dir = Path(__file__).parent.parent / "ke_toan_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / "ke_toan.db")
        self.pool = get_connection_pool(db_path)
        self._ensure_tables()
        
    def _ensure_tables(self) -> None:
        """Đảm bảo các bảng cần thiết tồn tại"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tạo bảng journal_entries
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
                
                # Tạo bảng journal_details
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
                
                # Tạo bảng account_balances
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS account_balances (
                        account_code TEXT PRIMARY KEY,
                        balance REAL DEFAULT 0,
                        last_updated TEXT
                    )
                ''')
                
                # Tạo bảng transaction_metadata
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transaction_metadata (
                        journal_id INTEGER PRIMARY KEY,
                        type TEXT,
                        category TEXT,
                        description TEXT,
                        created_at TEXT
                    )
                ''')
                
                # ⭐ Tạo bảng invoices (hóa đơn bán hàng)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        created_date TEXT NOT NULL,
                        buyer_name TEXT,
                        product_name TEXT,
                        quantity REAL DEFAULT 1,
                        unit_price REAL DEFAULT 0,
                        total_payment REAL DEFAULT 0,
                        status TEXT DEFAULT 'unpaid',
                        due_date TEXT,
                        created_at TEXT
                    )
                ''')
                
                # ⭐ Tạo bảng transactions (bảng cũ - để tương thích ngược)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL DEFAULT 0,
                        type TEXT,
                        category TEXT,
                        journal_entry_id INTEGER
                    )
                ''')
                
                # ⭐ Tạo bảng customers (khách hàng)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS customers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        phone TEXT,
                        address TEXT,
                        email TEXT,
                        created_at TEXT
                    )
                ''')
                
                # ⭐ Tạo bảng categories (danh mục thu/chi)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        parent_id INTEGER DEFAULT 0,
                        created_at TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Đã kiểm tra và tạo các bảng cần thiết")
        except Exception as e:
            logger.error(f"Lỗi khi tạo bảng: {e}")
            
    @staticmethod
    def get_total_income() -> float:
        """Tổng thu nhập (doanh thu từ Transaction + Invoice)"""
        # Vì là staticmethod nên ta khởi tạo một instance tạm thời để gọi các hàm con
        service = ReportService()
        total = service._get_transaction_income() + service._get_invoice_revenue()
        return total
    
    def _get_transaction_income(self) -> float:
        """Tổng thu nhập từ giao dịch (tài khoản 5xx, 7xx)"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COALESCE(SUM(credit_amount - debit_amount), 0) as total
                    FROM journal_details jd
                    JOIN journal_entries je ON jd.journal_entry_id = je.id
                    WHERE (jd.account_code LIKE '5%' OR jd.account_code LIKE '7%')
                ''')
                result = cursor.fetchone()
                return float(result['total']) if result else 0
        except Exception as e:
            logger.error(f"Lỗi _get_transaction_income: {e}")
            return 0
    
    def _get_invoice_revenue(self) -> float:
        """Tổng doanh thu từ hóa đơn"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(total_payment) as total FROM invoices
            ''')
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0
    
    @staticmethod
    def get_total_expense() -> float:
        """Tổng chi phí (Truy vấn từ các tài khoản đầu 6 và 8)"""
        # Khởi tạo instance tạm thời để sử dụng pool kết nối database
        service = ReportService()
        with service.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(debit_amount - credit_amount) as total
                FROM journal_details jd
                JOIN journal_entries je ON jd.journal_entry_id = je.id
                WHERE (jd.account_code LIKE '6%' OR jd.account_code LIKE '8%')
            ''')
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0.0
    
    def get_categories_summary(self) -> dict:
        """Tổng hợp theo danh mục thu/chi"""
        categories = defaultdict(float)
        
        # Lấy từ bảng transaction_metadata
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    tm.category,
                    tm.type,
                    CASE 
                        WHEN tm.type = 'Thu' THEN jd.credit_amount 
                        ELSE jd.debit_amount 
                    END as amount
                FROM transaction_metadata tm
                JOIN journal_details jd ON tm.journal_id = jd.journal_entry_id
                WHERE (tm.type = 'Thu' AND jd.account_code = '511')
                   OR (tm.type = 'Chi' AND jd.account_code = '642')
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                cat = row['category']
                amount = float(row['amount'])
                if row['type'] == 'Thu':
                    categories[cat] += amount
                else:
                    categories[cat] -= amount
        
        # Thêm thu từ hóa đơn vào danh mục "Thu hóa đơn"
        invoice_revenue = self._get_invoice_revenue()
        if invoice_revenue > 0:
            categories['Thu hóa đơn'] += invoice_revenue
        
        # Nếu không có dữ liệu từ metadata, thử lấy từ transaction_metadata cũ
        if not categories:
            categories = self._get_categories_from_old_table()
        
        return dict(categories)
    
    def _get_categories_from_old_table(self) -> dict:
        """Lấy từ bảng cũ (nếu có)"""
        categories = defaultdict(float)
        with self.pool.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT category, type, amount FROM transactions
                ''')
                rows = cursor.fetchall()
                for row in rows:
                    if row['type'] == 'Thu':
                        categories[row['category']] += row['amount']
                    else:
                        categories[row['category']] -= row['amount']
            except Exception:
                pass
        return dict(categories)
    
    def get_quarterly_report(self) -> dict:
        """Báo cáo theo quý"""
        quarterly = defaultdict(lambda: defaultdict(lambda: {'income': 0, 'expense': 0}))
        
        # Lấy từ journal_entries và transaction_metadata
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    je.date,
                    tm.type,
                    CASE 
                        WHEN tm.type = 'Thu' THEN jd.credit_amount 
                        ELSE jd.debit_amount 
                    END as amount
                FROM journal_entries je
                LEFT JOIN transaction_metadata tm ON je.id = tm.journal_id
                JOIN journal_details jd ON je.id = jd.journal_entry_id
                WHERE (tm.type = 'Thu' AND jd.account_code = '511')
                   OR (tm.type = 'Chi' AND jd.account_code = '642')
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                try:
                    date_str = row['date']
                    year, month, day = map(int, date_str.split('-'))
                    q = (month - 1) // 3 + 1
                    amount = float(row['amount'])
                    
                    if row['type'] == 'Thu':
                        quarterly[year][f'Q{q}']['income'] += amount
                    else:
                        quarterly[year][f'Q{q}']['expense'] += amount
                except Exception:
                    pass
        
        # Thêm doanh thu từ hóa đơn
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_date, total_payment FROM invoices
            ''')
            rows = cursor.fetchall()
            for row in rows:
                try:
                    date_str = row['created_date']
                    day, month, year = map(int, date_str.split('/'))
                    q = (month - 1) // 3 + 1
                    amount = float(row['total_payment'])
                    quarterly[year][f'Q{q}']['income'] += amount
                except Exception:
                    pass
        
        return dict(quarterly)
    
    def get_yearly_report(self) -> dict:
        """Báo cáo theo năm"""
        yearly = defaultdict(lambda: {'income': 0, 'expense': 0})
        
        # Lấy từ journal_entries và transaction_metadata
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    je.date,
                    tm.type,
                    CASE 
                        WHEN tm.type = 'Thu' THEN jd.credit_amount 
                        ELSE jd.debit_amount 
                    END as amount
                FROM journal_entries je
                LEFT JOIN transaction_metadata tm ON je.id = tm.journal_id
                JOIN journal_details jd ON je.id = jd.journal_entry_id
                WHERE (tm.type = 'Thu' AND jd.account_code = '511')
                   OR (tm.type = 'Chi' AND jd.account_code = '642')
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                try:
                    date_str = row['date']
                    year = int(date_str.split('-')[0])
                    amount = float(row['amount'])
                    
                    if row['type'] == 'Thu':
                        yearly[year]['income'] += amount
                    else:
                        yearly[year]['expense'] += amount
                except Exception:
                    pass
        
        # Thêm doanh thu từ hóa đơn
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT created_date, total_payment FROM invoices
            ''')
            rows = cursor.fetchall()
            for row in rows:
                try:
                    date_str = row['created_date']
                    day, month, year = map(int, date_str.split('/'))
                    amount = float(row['total_payment'])
                    yearly[year]['income'] += amount
                except Exception:
                    pass
        
        return dict(yearly)
    
    def calculate_tax(self, revenue: float, business_type: str, industry: str, year: int) -> dict:
        """Tính thuế theo Thông tư 99/2025"""
        tax_rates = {
            "Phân phối, cung cấp hàng hóa": {"vat": 0.01, "pit": 0.005},
            "Dịch vụ, xây dựng không bao thầu": {"vat": 0.05, "pit": 0.02},
            "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa": {"vat": 0.03, "pit": 0.015},
            "Hoạt động kinh doanh khác": {"vat": 0.02, "pit": 0.01}
        }
        rate = tax_rates.get(industry, tax_rates["Phân phối, cung cấp hàng hóa"])
        result = {"vat": 0, "pit": 0, "tndn": 0, "mon_bai": 0}
        
        if "Hộ kinh doanh" in business_type:
            if year >= 2026:
                if revenue <= config.get_tax_threshold():
                    # Miễn thuế theo Thông tư 99/2025
                    pass
                else:
                    result['vat'] = revenue * rate['vat']
                    result['pit'] = revenue * rate['pit']
            else:
                if revenue <= 100_000_000:
                    pass
                else:
                    result['vat'] = revenue * rate['vat']
                    result['pit'] = revenue * rate['pit']
                    if revenue <= 300_000_000:
                        result['mon_bai'] = 300_000
                    elif revenue <= 500_000_000:
                        result['mon_bai'] = 500_000
                    else:
                        result['mon_bai'] = 1_000_000
        else:
            # Doanh nghiệp
            profit = revenue * 0.1  # giả định 10% lợi nhuận
            result['tndn'] = profit * 0.20
            result['vat'] = revenue * 0.10
            if year < 2026:
                if revenue <= 1_000_000_000:
                    result['mon_bai'] = 1_000_000
                elif revenue <= 3_000_000_000:
                    result['mon_bai'] = 1_500_000
                else:
                    result['mon_bai'] = 2_000_000
            else:
                result['mon_bai'] = 0
        
        return result
    
    def get_period_income(self, start_date: str, end_date: str) -> float:
        """Thu nhập trong khoảng thời gian"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(credit_amount - debit_amount) as total
                FROM journal_details jd
                JOIN journal_entries je ON jd.journal_entry_id = je.id
                WHERE (jd.account_code LIKE '5%' OR jd.account_code LIKE '7%')
                    AND je.date BETWEEN ? AND ?
            ''', (start_date, end_date))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0
    
    def get_period_expense(self, start_date: str, end_date: str) -> float:
        """Chi phí trong khoảng thời gian"""
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(debit_amount - credit_amount) as total
                FROM journal_details jd
                JOIN journal_entries je ON jd.journal_entry_id = je.id
                WHERE (jd.account_code LIKE '6%' OR jd.account_code LIKE '8%')
                    AND je.date BETWEEN ? AND ?
            ''', (start_date, end_date))
            result = cursor.fetchone()
            return float(result['total']) if result and result['total'] else 0
    
    def get_total_income_by_year(self, year: int) -> float:
        """Tổng doanh thu theo năm (từ giao dịch + hóa đơn)"""
        total = 0
        
        # Từ giao dịch (bút toán kế toán)
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(credit_amount - debit_amount) as total
                FROM journal_details jd
                JOIN journal_entries je ON jd.journal_entry_id = je.id
                WHERE (jd.account_code LIKE '5%' OR jd.account_code LIKE '7%')
                    AND strftime('%Y', je.date) = ?
            ''', (str(year),))
            result = cursor.fetchone()
            total += float(result['total']) if result and result['total'] else 0
        
        # Từ hóa đơn
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(total_payment) as total
                FROM invoices
                WHERE substr(created_date, 7, 4) = ?
            ''', (str(year),))
            result = cursor.fetchone()
            total += float(result['total']) if result and result['total'] else 0
        
        return total
    
    def get_balance(self) -> float:
        """Số dư hiện tại (Thu - Chi)"""
        return self.get_total_income() - self.get_total_expense()
    
    def get_monthly_summary(self, year: int) -> list:
        """Tổng hợp thu chi 12 tháng trong năm"""
        summary = []
        for month in range(1, 13):
            from_date = f"{year}-{month:02d}-01"
            
            if month == 12:
                to_date = f"{year + 1}-01-01"
            else:
                to_date = f"{year}-{month + 1:02d}-01"
            
            income = self.get_period_income(from_date, to_date)
            expense = self.get_period_expense(from_date, to_date)
            
            summary.append({
                'month': month,
                'month_name': f"Tháng {month}",
                'income': income,
                'expense': expense,
                'balance': income - expense
            })
        return summary


# Singleton instance
_report_service_instance = None


def get_report_service() -> ReportService:
    """Lấy singleton instance của ReportService"""
    global _report_service_instance
    if _report_service_instance is None:
        _report_service_instance = ReportService()
    return _report_service_instance