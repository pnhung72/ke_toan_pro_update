# -*- coding: utf-8 -*-
"""
Dich vu Kế toán - Xu ly nghiep vu ke toan thuc te
Tu dong định khoan, kiem tra so du, sinh bao cao
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple
import logging
import calendar

logger = logging.getLogger(__name__)


class AccountingService:
    """Xu ly cac nghiep vu ke toan chinh"""
    
    def __init__(self, db_connection, transaction_model):
        """
        Args:
            db_connection: Connection tu pool
            transaction_model: Transaction model (da viet o tren)
        """
        self.conn = db_connection
        self.transaction = transaction_model
        
        # Cau hinh nam tai chinh
        self.fiscal_year_start_month = 1  # Thang bat dau nam tai chinh (1=Thang 1)
        self.current_fiscal_year = datetime.now().year
        
        # Danh sach tai khoan can theo doi dac biet
        self.cash_accounts = ['111', '112']  # Tien mat, Tien gui NH
        self.inventory_accounts = ['151', '152', '153', '156']  # Hang ton kho
        self.revenue_accounts = ['511', '515', '711']
        self.expense_accounts = ['611', '621', '627', '632', '635', '641', '642', '811']
    
    # ==================== NGHIEP VU BAN HANG ====================
    
    def record_sales(
        self,
        date: str,
        customer_name: str,
        amount: Decimal,
        vat_rate: float = 0.0,
        payment_method: str = 'cash',
        description: str = None,
        created_by: str = None
    ) -> int:
        """
        Ghi nhan doanh thu ban hang
        
        Dinh khoan:
            Nợ 111/112/131: Tong thanh toan
            Có 511: Doanh thu chua VAT
            Có 3331: VAT phai nop (neu co)
        
        Args:
            date: Ngay ban hang (YYYY-MM-DD)
            customer_name: Ten khach hang
            amount: Tong tien thanh toan (da bao gom VAT)
            vat_rate: Thue suat VAT (0, 5, 8, 10%)
            payment_method: 'cash' (tien mat), 'bank' (chuyen khoan), 'credit' (cong no)
            description: Dien giai
            created_by: Nguoi nhap lieu
        
        Returns:
            journal_entry_id
        """
        revenue = amount / (1 + vat_rate / 100)
        vat_amount = amount - revenue
        
        # Xac dinh tai khoan thu
        if payment_method == 'cash':
            debit_account = '111'  # Tien mat
        elif payment_method == 'bank':
            debit_account = '112'  # Tien gui NH
        else:  # credit
            debit_account = '131'  # Phai thu khach hang
        
        entries = [
            {'account': debit_account, 'debit': float(amount), 'credit': 0},
            {'account': '511', 'debit': 0, 'credit': float(revenue)},
        ]
        
        if vat_amount > 0:
            entries.append({'account': '3331', 'debit': 0, 'credit': float(vat_amount)})
        
        description = description or f"Ban hang cho {customer_name} - {amount:,.0f}đ"
        
        # Cap nhat cong no khach hang (neu co)
        if payment_method == 'credit':
            self._update_customer_debt(customer_name, amount, date, 'sales')
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"HD{date.replace('-', '')}_{customer_name[:10]}",
            created_by=created_by,
            fiscal_year=self.current_fiscal_year
        )
    
    # ==================== NGHIEP VU MUA HANG ====================
    
    def record_purchase(
        self,
        date: str,
        supplier_name: str,
        amount: Decimal,
        vat_rate: float = 0.0,
        payment_method: str = 'cash',
        description: str = None,
        created_by: str = None
    ) -> int:
        """
        Ghi nhan mua hang
        
        Dinh khoan:
            Nợ 156/152: Gia tri hang mua (chua VAT)
            Nợ 1331: VAT duoc khau tru (neu co)
            Có 111/112/331: Tong thanh toan
        
        Args:
            date: Ngay mua hang
            supplier_name: Ten nha cung cap
            amount: Tong tien thanh toan
            vat_rate: Thue suat VAT
            payment_method: 'cash', 'bank', 'credit'
            description: Dien giai
            created_by: Nguoi nhap
        
        Returns:
            journal_entry_id
        """
        purchase_value = amount / (1 + vat_rate / 100)
        vat_amount = amount - purchase_value
        
        # Xac dinh tai khoan chi tra
        if payment_method == 'cash':
            credit_account = '111'
        elif payment_method == 'bank':
            credit_account = '112'
        else:  # credit
            credit_account = '331'  # Phai tra nguoi ban
        
        entries = [
            {'account': '156', 'debit': float(purchase_value), 'credit': 0},
        ]
        
        if vat_amount > 0:
            entries.append({'account': '1331', 'debit': float(vat_amount), 'credit': 0})
        
        entries.append({'account': credit_account, 'debit': 0, 'credit': float(amount)})
        
        description = description or f"Mua hang tu {supplier_name} - {amount:,.0f}đ"
        
        # Cap nhat cong no nha cung cap (neu co)
        if payment_method == 'credit':
            self._update_supplier_debt(supplier_name, amount, date, 'purchase')
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"PN{date.replace('-', '')}_{supplier_name[:10]}",
            created_by=created_by
        )
    
    # ==================== NGHIEP VU CHI PHI ====================
    
    def record_expense(
        self,
        date: str,
        expense_type: str,
        amount: Decimal,
        payment_method: str = 'cash',
        description: str = None,
        created_by: str = None
    ) -> int:
        """
        Ghi nhan chi phi (ban hang, quan ly)
        
        Dinh khoan:
            Nợ 641/642: Chi phi
            Có 111/112: Tien chi
        
        Args:
            date: Ngay phat sinh
            expense_type: 'selling' (ban hang) hoac 'admin' (quan ly)
            amount: So tien
            payment_method: 'cash', 'bank'
            description: Dien giai
            created_by: Nguoi nhap
        """
        # Xac dinh tai khoan chi phi
        if expense_type == 'selling':
            expense_account = '641'  # Chi phi ban hang
        else:  # admin
            expense_account = '642'  # Chi phi QLDN
        
        # Xac dinh tai khoan chi tra
        credit_account = '111' if payment_method == 'cash' else '112'
        
        entries = [
            {'account': expense_account, 'debit': float(amount), 'credit': 0},
            {'account': credit_account, 'debit': 0, 'credit': float(amount)}
        ]
        
        description = description or f"Chi phi {expense_type} - {amount:,.0f}đ"
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"CP{date.replace('-', '')}",
            created_by=created_by
        )
    
    # ==================== NGHIEP VU LUONG ====================
    
    def record_salary(
        self,
        date: str,
        employee_name: str,
        gross_salary: Decimal,
        deductions: Dict[str, Decimal] = None,
        created_by: str = None
    ) -> int:
        """
        Ghi nhan tien luong
        
        Dinh khoan:
            Nợ 642: Tong luong gross
            Có 334: Luong phai tra
            Có 3335: Cac khoan tru vao luong (thue TNCN, BHXH...)
        
        Args:
            date: Ngay tinh luong
            employee_name: Ten nhan vien
            gross_salary: Tong luong gross
            deductions: Cac khoan tru {'tax': 50000, 'insurance': 100000}
            created_by: Nguoi nhap
        """
        deductions = deductions or {'tax': 0, 'insurance': 0}
        total_deductions = sum(deductions.values())
        net_salary = gross_salary - total_deductions
        
        entries = [
            {'account': '642', 'debit': float(gross_salary), 'credit': 0},
            {'account': '334', 'debit': 0, 'credit': float(net_salary)},
        ]
        
        if deductions.get('tax', 0) > 0:
            entries.append({'account': '3335', 'debit': 0, 'credit': float(deductions['tax'])})
        
        if deductions.get('insurance', 0) > 0:
            entries.append({'account': '338', 'debit': 0, 'credit': float(deductions['insurance'])})
        
        description = f"Luong thang {date[:7]} - {employee_name} (Net: {net_salary:,.0f}đ)"
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"L{date.replace('-', '')}_{employee_name[:10]}",
            created_by=created_by
        )
    
    # ==================== NGHIEP VU KHẤU HAO TSCĐ ====================
    
    def record_depreciation(
        self,
        date: str,
        asset_name: str,
        asset_account: str,
        depreciation_amount: Decimal,
        created_by: str = None
    ) -> int:
        """
        Ghi nhan khau hao TSCĐ
        
        Dinh khoan:
            Nợ 627/641/642: Chi phi khau hao
            Có 214: Hao mon TSCĐ
        
        Args:
            date: Ngay trich khau hao
            asset_name: Ten tai san
            asset_account: Tai khoan TSCĐ (211, 212, 213)
            depreciation_amount: So tien khau hao
            created_by: Nguoi nhap
        """
        # Xac dinh tai khoan chi phi khau hao dua tren loai TSCĐ
        if asset_account in ['211', '213']:  # TSCĐ hinh thanh, vo hinh
            expense_account = '627'  # Chi phi san xuat chung
        else:
            expense_account = '642'  # Chi phi QLDN
        
        entries = [
            {'account': expense_account, 'debit': float(depreciation_amount), 'credit': 0},
            {'account': '214', 'debit': 0, 'credit': float(depreciation_amount)}
        ]
        
        description = f"Khau hao TSCĐ {asset_name} - {depreciation_amount:,.0f}đ"
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"KH{date.replace('-', '')}_{asset_name[:10]}",
            created_by=created_by
        )
    
    # ==================== NGHIEP VU THUẾ ====================
    
    def record_tax_payment(
        self,
        date: str,
        tax_type: str,
        amount: Decimal,
        payment_method: str = 'bank',
        created_by: str = None
    ) -> int:
        """
        Ghi nhan nop thue
        
        Dinh khoan:
            Nợ 333: Thue phai nop
            Có 112: Tien gui ngan hang
        
        Args:
            date: Ngay nop thue
            tax_type: 'vat', 'income_tax', 'other'
            amount: So tien
            payment_method: 'bank' hoac 'cash'
            created_by: Nguoi nhap
        """
        # Xac dinh tai khoan chi tiet
        tax_accounts = {
            'vat': '3331',      # Thue GTGT
            'income_tax': '3334', # Thue TNDN
            'other': '3338'      # Thue khac
        }
        
        tax_account = tax_accounts.get(tax_type, '3338')
        
        # Xac dinh tai khoan chi tra
        credit_account = '112' if payment_method == 'bank' else '111'
        
        entries = [
            {'account': tax_account, 'debit': float(amount), 'credit': 0},
            {'account': credit_account, 'debit': 0, 'credit': float(amount)}
        ]
        
        description = f"Nop thue {tax_type} - {amount:,.0f}đ"
        
        return self.transaction.create_journal_entry(
            date=date,
            description=description,
            entries=entries,
            reference_no=f"THUE{date.replace('-', '')}",
            created_by=created_by
        )
    
    # ==================== KET CHUYEN CUOI KY ====================
    
    def closing_entries(self, from_date: str, to_date: str, created_by: str = None) -> List[int]:
        """
        Thuc hien ket chuyen cuoi ky
        
        Bao gom:
        1. Ket chuyen doanh thu -> Xac dinh KQKD
        2. Ket chuyen chi phi -> Xac dinh KQKD
        3. Ket chuyen loi nhuan -> Loi nhuan chua phan phoi
        
        Returns:
            Danh sach journal_entry_id da tao
        """
        journal_ids = []
        
        # 1. Ket chuyen doanh thu
        revenue_ids = ['511', '515', '711']
        for revenue_acc in revenue_ids:
            balance = self._get_account_balance(revenue_acc, from_date, to_date)
            if balance > 0:
                entry_id = self.transaction.create_journal_entry(
                    date=to_date,
                    description=f"Ket chuyen doanh thu TK {revenue_acc}",
                    entries=[
                        {'account': revenue_acc, 'debit': balance, 'credit': 0},
                        {'account': '911', 'debit': 0, 'credit': balance}
                    ],
                    created_by=created_by
                )
                journal_ids.append(entry_id)
        
        # 2. Ket chuyen chi phi
        expense_ids = ['611', '621', '627', '632', '635', '641', '642', '811']
        for expense_acc in expense_ids:
            balance = self._get_account_balance(expense_acc, from_date, to_date)
            if balance > 0:
                entry_id = self.transaction.create_journal_entry(
                    date=to_date,
                    description=f"Ket chuyen chi phi TK {expense_acc}",
                    entries=[
                        {'account': '911', 'debit': balance, 'credit': 0},
                        {'account': expense_acc, 'debit': 0, 'credit': balance}
                    ],
                    created_by=created_by
                )
                journal_ids.append(entry_id)
        
        # 3. Xac dinh loi nhuan
        profit_balance = self._get_account_balance('911', from_date, to_date)
        if profit_balance != 0:
            if profit_balance > 0:  # Lai
                entry_id = self.transaction.create_journal_entry(
                    date=to_date,
                    description="Ket chuyen loi nhuan",
                    entries=[
                        {'account': '911', 'debit': profit_balance, 'credit': 0},
                        {'account': '421', 'debit': 0, 'credit': profit_balance}
                    ],
                    created_by=created_by
                )
            else:  # Lo
                entry_id = self.transaction.create_journal_entry(
                    date=to_date,
                    description="Ket chuyen lo",
                    entries=[
                        {'account': '421', 'debit': abs(profit_balance), 'credit': 0},
                        {'account': '911', 'debit': 0, 'credit': abs(profit_balance)}
                    ],
                    created_by=created_by
                )
            journal_ids.append(entry_id)
        
        logger.info(f"Da thuc hien ket chuyen tu {from_date} den {to_date}")
        return journal_ids
    
    # ==================== PHUONG THUC HO TRO ====================
    
    def _get_account_balance(self, account_code: str, from_date: str, to_date: str) -> float:
        """Lay so du tai khoan trong ky"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT SUM(debit_amount - credit_amount) as balance
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
            WHERE jd.account_code = ? AND je.date BETWEEN ? AND ?
        ''', (account_code, from_date, to_date))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0.0
    
    def _update_customer_debt(self, customer_name: str, amount: Decimal, date: str, trans_type: str):
        """Cap nhat cong no khach hang"""
        cursor = self.conn.cursor()
        
        if trans_type == 'sales':
            # Tang cong no
            cursor.execute('''
                INSERT INTO debts (customer_name, amount, remaining, due_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (customer_name, float(amount), float(amount), date, datetime.now().isoformat()))
            self.conn.commit()
        else:  # payment
            # Giam cong no
            cursor.execute('''
                UPDATE debts 
                SET remaining = remaining - ?,
                    paid_date = ?
                WHERE customer_name = ? AND remaining > 0
                ORDER BY due_date
                LIMIT 1
            ''', (float(amount), date, customer_name))
    
    def _update_supplier_debt(self, supplier_name: str, amount: Decimal, date: str, trans_type: str):
        """Cap nhat cong no nha cung cap"""
        cursor = self.conn.cursor()
        
        if trans_type == 'purchase':
            cursor.execute('''
                INSERT INTO supplier_debts (supplier_name, amount, remaining, due_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (supplier_name, float(amount), float(amount), date, datetime.now().isoformat()))
    
    # ==================== BAO CAO TONG HOP ====================
    
    def get_monthly_report(self, year: int, month: int) -> Dict:
        """
        Bao cao tai chinh thang
        
        Returns:
            {
                'revenue': Tong doanh thu,
                'expense': Tong chi phi,
                'profit': Loi nhuan,
                'top_customers': Top khach hang,
                'top_expenses': Top chi phi
            }
        """
        from_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        to_date = f"{year}-{month:02d}-{last_day:02d}"
        
        # Doanh thu
        total_revenue = sum(
            self._get_account_balance(acc, from_date, to_date)
            for acc in self.revenue_accounts
        )
        
        # Chi phi
        total_expense = sum(
            self._get_account_balance(acc, from_date, to_date)
            for acc in self.expense_accounts
        )
        
        return {
            'year': year,
            'month': month,
            'revenue': total_revenue,
            'expense': total_expense,
            'profit': total_revenue - total_expense,
            'profit_text': f"{'Lãi' if total_revenue > total_expense else 'Lỗ'}: {abs(total_revenue - total_expense):,.0f}đ"
        }
    
    def check_accounting_balance(self, as_of_date: str = None) -> bool:
        """
        Kiem tra tong quat so lieu ke toan
        
        Returns:
            True neu du lieu hop le, False neu co van de
        """
        trial_balance = self.transaction.get_trial_balance(as_of_date)
        
        total_debit = sum(item['total_debit'] for item in trial_balance)
        total_credit = sum(item['total_credit'] for item in trial_balance)
        
        is_balanced = abs(total_debit - total_credit) < 0.01
        
        if not is_balanced:
            logger.error(f"SO LIEU KHONG CAN DOI! Chenh lech: {total_debit - total_credit}")
        
        return is_balanced


# ==================== FACTORY FUNCTION ====================

def create_accounting_service(db_connection, transaction_model) -> AccountingService:
    """
    Tao instance cua AccountingService
    """
    return AccountingService(db_connection, transaction_model)