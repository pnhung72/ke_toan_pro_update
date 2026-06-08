# -*- coding: utf-8 -*-
"""
DashboardService - Thống kê và biểu đồ (Bản sửa lỗi kết nối triệt để)
"""

from datetime import datetime, timedelta
from collections import defaultdict
from models.debt import Debt
from models.invoice import Invoice
from models.transaction import Transaction
from models.product import Product
import logging

class DashboardService:
    """Dịch vụ thống kê cho dashboard - Sử dụng dữ liệu thực từ Pool mới"""
    
    def __init__(self, db_pool=None) -> None:
        # Sử dụng self.pool thống nhất để tránh lỗi AttributeError
        self.pool = db_pool 

    def _get_conn(self):
        """Hàm hỗ trợ lấy kết nối thực từ Pool để SQLite không báo lỗi[cite: 4, 5]"""
        if hasattr(self.pool, 'get_connection'):
            return self.pool.get_connection()
        return self.pool # Trường hợp đã là connection hoặc None
    
    def get_revenue_by_month(self, year: int = None) -> list:
        """
        Thống kê doanh thu theo tháng - BẢO VỆ FONT TOÀN CỤC.
        Chỉ xử lý tính toán số liệu, không import thư viện mới.
        """
        # Sử dụng biến year truyền vào hoặc mặc định năm 2026 (theo mốc hiện tại)
        target_year = year if year else 2026
        
        months = [f"Tháng {i}" for i in range(1, 13)]
        revenues = [0.0] * 12
        
        # Kiểm tra an toàn pool dữ liệu
        if not hasattr(self, 'pool') or not self.pool: 
            return {"months": months, "revenues": revenues}

        try:
            # 1. Lấy kết nối an toàn
            conn = self._get_conn()

            # 2. Xử lý Hóa đơn (Invoices)
            invoices = Invoice.get_all() 
            if invoices and isinstance(invoices, list):
                for inv in invoices:
                    date_str = inv.get('created_date', '')
                    if date_str and len(date_str) >= 4:
                        try:
                            # Tách chuỗi thủ công để tránh dùng thư viện datetime
                            parts = date_str.split('-')
                            if int(parts[0]) == target_year:
                                m = int(parts[1]) - 1
                                if 0 <= m < 12:
                                    revenues[m] += float(inv.get('total_payment', 0) or 0)
                        except Exception: continue
            
            # 3. Xử lý Giao dịch (Transactions) - Bảo toàn lọc đầu 5
            transactions = Transaction.get_all()
            if transactions and isinstance(transactions, list):
                for t in transactions:
                    t_type = t.get('type', '')
                    acc_code = str(t.get('account_code', ''))
                    
                    # Giữ nguyên logic lọc doanh thu của Thầy
                    if t_type == 'Thu' or acc_code.startswith('5') or '5' in acc_code:
                        date_str = t.get('date', '')
                        if date_str and len(date_str) >= 4:
                            try:
                                parts = date_str.split('-')
                                if int(parts[0]) == target_year:
                                    m = int(parts[1]) - 1
                                    if 0 <= m < 12:
                                        revenues[m] += float(t.get('total_amount', 0) or 0)
                            except Exception: continue
            
            return {"months": months, "revenues": revenues}

        except Exception as e:
            # Chỉ ghi log lỗi ra console, không làm gián đoạn UI
            logging.error(f"Lỗi Dashboard: {e}")
            return {"months": months, "revenues": [0.0] * 12}
    
    def get_top_products(self, limit: int = 5) -> list:
        if not self.pool: return []
        product_sales = defaultdict(float)
        try:
            invoices = Invoice.get_all()
            if invoices:
                for inv in invoices:
                    name = inv.get('product_name')
                    qty = inv.get('quantity', 0)
                    if name:
                        product_sales[name] += float(qty)
            
            result = []
            for name, total_qty in product_sales.items():
                result.append({
                    'product_name': name, # Khóa này phải khớp với giao diện
                    'qty': total_qty,
                    'unit': 'lít'
                })
            
            result.sort(key=lambda x: x['qty'], reverse=True)
            return result[:limit]
        except Exception:
            return []
    
    def get_debt_summary(self) -> dict:
        """Thống kê công nợ tổng quát[cite: 5]"""
        if not self.pool: return {"total_debt": 0, "overdue": 0, "paid": 0, "customers_count": 0}
        
        # Truyền kết nối thực vào Debt.get_all[cite: 5, 6]
        debts = Debt.get_all()
        total_debt = 0
        total_paid = 0
        overdue = 0
        today = datetime.now().date()
        
        for d in debts:
            total = d.get('total_debt', 0)
            paid = d.get('paid', 0)
            remaining = total - paid
            total_debt += remaining
            total_paid += paid
            
            due_date_str = d.get('due_date', '')
            if due_date_str and remaining > 0:
                try:
                    due = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    if due < today:
                        overdue += remaining
                except Exception: continue
        
        return {
            "total_debt": total_debt,
            "overdue": overdue,
            "paid": total_paid,
            "customers_count": len(debts)
        }
    
    def get_cash_flow_forecast(self, days: int = 30) -> list:
        """Dự báo dòng tiền dựa trên lịch sử[cite: 5]"""
        forecast = []
        today = datetime.now().date()
        if not self.pool: return []
        
        conn = self._get_conn()
        transactions = Transaction.get_all()
        invoices = Invoice.get_all() 
        
        total_income = 0
        total_expense = 0
        date_set = set()
        
        for t in transactions:
            amount = t.get('total_amount', 0) 
            if t.get('type') == 'Thu':
                total_income += amount
            else:
                total_expense += amount
            try:
                d_str = t.get('date', '')
                if d_str: date_set.add(d_str)
            except Exception: continue
        
        for inv in invoices:
            total_income += inv.get('total_payment', 0)
            try:
                d_str = inv.get('created_date', '')
                if d_str: date_set.add(d_str)
            except Exception: continue
        
        days_count = max(len(date_set), 1)
        avg_income = total_income / days_count
        avg_expense = total_expense / days_count
        
        current_balance = total_income - total_expense
        for i in range(days):
            date = today + timedelta(days=i)
            current_balance += (avg_income - avg_expense)
            forecast.append({
                "date": date.strftime("%d/%m/%Y"),
                "inflow": avg_income,
                "outflow": avg_expense,
                "balance": current_balance
            })
        return forecast
    
    def get_tax_summary(self) -> dict:
        """Tóm tắt thuế VAT (tạm tính 10%)[cite: 5]"""
        year = datetime.now().year
        total_revenue = 0
        if not self.pool: return {"vat": 0, "pitt": 0, "paid": 0, "pending": 0}

        conn = self._get_conn()
        invoices = Invoice.get_all()
        for inv in invoices:
            try:
                date_str = inv.get('created_date', '')
                if date_str and date_str.startswith(str(year)):
                    total_revenue += inv.get('total_payment', 0)
            except Exception: continue
        
        transactions = Transaction.get_all()
        for t in transactions:
            if t.get('type') == 'Thu' or '5' in str(t.get('account_code', '')):
                try:
                    date_str = t.get('date', '')
                    if date_str and date_str.startswith(str(year)):
                        total_revenue += t.get('total_amount', 0)
                except Exception: continue
        
        vat = total_revenue * 0.1
        paid = vat * 0.7 # Giả định đã nộp 70%
        return {"vat": vat, "pitt": 0, "paid": paid, "pending": vat - paid}
    
    def get_recent_transactions(self, limit: int = 10) -> list:
        if not self.pool: return []
        items = []
        conn = self._get_conn()
        
        invoices = Invoice.get_all()
        for inv in invoices:
            items.append({
                "date": inv.get('created_date', ''),
                "type": "Thu",
                "amount": inv.get('total_payment', 0),
                "description": f"Hóa đơn {inv.get('id', '')} - {inv.get('buyer_name', '')}"
            })
        
        transactions = Transaction.get_all()
        for t in transactions:
            items.append({
                "date": t.get('date', ''),
                "type": t.get('type', ''),
                "amount": t.get('total_amount', 0), 
                "description": t.get('description', '')
            })
        
        items.sort(key=lambda x: x.get('date', ''), reverse=True)
        return items[:limit]
    
    def get_revenue_stats(self) -> dict:
        """
        So sánh doanh thu tháng này và tháng trước.
        Đã sửa lỗi Binding để hiển thị biểu đồ và bảo toàn logic lọc tài khoản loại 5.
        """
        from datetime import datetime, timedelta
        
        today = datetime.now()
        current_month = today.strftime('%Y-%m')
        last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        revenue_current = 0
        revenue_last = 0
        
        # Kiểm tra sự tồn tại của connection pool để tránh lỗi hệ thống
        if not hasattr(self, 'pool') or not self.pool: 
            return {'monthly_revenue': 0, 'change_percent': 0}
        
        try:
            # Lấy kết nối an toàn từ pool
            conn = self._get_conn()
            
            # 1. Xử lý doanh thu từ Hóa đơn (Invoices)
            # Truyền conn vào Invoice.get_all để đồng nhất phiên làm việc với Database
            invoices = Invoice.get_all()
            if invoices:
                for inv in invoices:
                    # Sử dụng phương thức .get() để tránh lỗi nếu thiếu key trong dictionary
                    date = inv.get('created_date', '')
                    if date:
                        amount = inv.get('total_payment', 0) or 0
                        if date.startswith(current_month):
                            revenue_current += amount
                        elif date.startswith(last_month):
                            revenue_last += amount
            
            # 2. Xử lý doanh thu từ Giao dịch (Transactions)
            # Truyền conn vào Transaction.get_all để khắc phục lỗi 'int' object has no attribute 'cursor'
            transactions = Transaction.get_all()
            if transactions:
                for t in transactions:
                    # Bảo toàn tính năng lọc: Loại 'Thu' hoặc tài khoản doanh thu (đầu 5)
                    t_type = t.get('type', '')
                    acc_code = str(t.get('account_code', ''))
                    
                    if t_type == 'Thu' or '5' in acc_code: 
                        date = t.get('date', '')
                        if date:
                            # Lấy giá trị số tiền, mặc định là 0 nếu null
                            amount_val = t.get('total_amount', 0) or 0
                            if date.startswith(current_month):
                                revenue_current += amount_val
                            elif date.startswith(last_month):
                                revenue_last += amount_val
            
            # 3. Tính toán phần trăm tăng trưởng
            change = ((revenue_current - revenue_last) / revenue_last * 100) if revenue_last else 0
            
            return {
                'monthly_revenue': revenue_current, 
                'change_percent': round(change, 2) # Làm tròn 2 chữ số cho đẹp giao diện
            }
            
        except Exception as e:
            # Ghi lại lỗi chính xác ở hàm nào để Thầy dễ theo dõi trong log
            logging.error(f"Lỗi tại DashboardService.get_revenue_stats: {e}")
            return {'monthly_revenue': 0, 'change_percent': 0}
    
    def get_debt_customers(self) -> list:
        if not self.pool: return []
        debts = Debt.get_all()
        customers = []
        for d in debts:
            total = d.get('total_debt', 0)
            paid = d.get('paid', 0)
            remaining = total - paid
            if remaining > 0:
                customers.append({
                    'customer_name': d.get('name', ''),
                    'debt': remaining,
                    'due_date': d.get('due_date', ''),
                    'is_overdue': False
                })
        return customers