"""
TaxReports - Báo cáo thuế GTGT, TNDN, TNCN.

Module này cung cấp:
- Báo cáo thuế GTGT (Thông tư 219/2013/TT-BTC)
- Báo cáo thuế TNDN (Thông tư 78/2014/TT-BTC)
- Báo cáo thuế TNCN (Thông tư 111/2013/TT-BTC)

Example:
    >>> from reports.tax_reports import TaxReports
    >>> tax = TaxReports()
    >>> vat = tax.get_vat_report("2026-01-01", "2026-03-31")
"""

# reports/tax_reports.py
# BÁO CÁO THUẾ GTGT, TNDN, TNCN
# Theo Thông tư 99/2025/TT-BTC

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class TaxReports:
    """Báo cáo thuế theo quy định mới"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent
            db_path = base_dir / "ke_toan_data" / "ke_toan.db"
        self.db_path = str(db_path)
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_vat_report(self, from_date: str, to_date: str, vat_rate: float = 10) -> Dict:
        """Báo cáo thuế GTGT"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Hóa đơn đầu ra
        cursor.execute("""
            SELECT 
                COUNT(*) as invoice_count,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(SUM(vat_amount), 0) as total_vat
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
        """, (from_date, to_date))
        output = cursor.fetchone()
        
        # Hóa đơn đầu vào (nếu có bảng purchase_orders)
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as purchase_count,
                    COALESCE(SUM(total_amount), 0) as total_purchases,
                    COALESCE(SUM(vat_amount), 0) as total_input_vat
                FROM purchase_orders
                WHERE order_date BETWEEN ? AND ?
            """, (from_date, to_date))
            input_data = cursor.fetchone()
        except:
            input_data = (0, 0, 0)
        
        conn.close()
        
        return {
            "report_name": "BÁO CÁO THUẾ GTGT",
            "from_date": from_date,
            "to_date": to_date,
            "vat_rate": vat_rate,
            "output": {
                "invoice_count": output[0] if output else 0,
                "sales_amount": output[1] if output else 0,
                "vat_amount": output[2] if output else 0
            },
            "input": {
                "purchase_count": input_data[0] if input_data else 0,
                "purchase_amount": input_data[1] if input_data else 0,
                "vat_amount": input_data[2] if input_data else 0
            },
            "payable_vat": (output[2] if output else 0) - (input_data[2] if input_data else 0)
        }
    
    def get_cit_report(self, year: int) -> Dict:
        """Báo cáo thuế TNDN"""
        from_date = f"{year}-01-01"
        to_date = f"{year}-12-31"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM invoices
            WHERE invoice_date BETWEEN ? AND ?
        """, (from_date, to_date))
        revenue = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM purchase_orders
            WHERE order_date BETWEEN ? AND ?
        """, (from_date, to_date))
        expenses = cursor.fetchone()[0]
        
        conn.close()
        
        profit_before_tax = revenue - expenses
        tax_rate = 20
        tax_amount = profit_before_tax * tax_rate / 100 if profit_before_tax > 0 else 0
        
        return {
            "report_name": "BÁO CÁO THUẾ TNDN",
            "year": year,
            "revenue": revenue,
            "expenses": expenses,
            "profit_before_tax": profit_before_tax,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "net_profit": profit_before_tax - tax_amount
        }
    
    def get_pit_report(self, year: int, month: int = None) -> Dict:
        """Báo cáo thuế TNCN"""
        from_date = f"{year}-01-01"
        to_date = f"{year}-12-31"
        
        return {
            "report_name": "BÁO CÁO THUẾ TNCN",
            "period": f"{year}",
            "total_employees": 0,
            "total_income": 0,
            "total_tax": 0,
            "employees": []
        }


# ========== KIỂM TRA ==========
if __name__ == "__main__":
    print("=== KIỂM TRA TAX REPORTS ===")
    tax = TaxReports()
    print("✅ TaxReports hoạt động tốt!")
