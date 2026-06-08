# -*- coding: utf-8 -*-
"""
DebtController - Xu ly logic cho cong no
"""

from controllers.base_controller import BaseController

class DebtController(BaseController):
    """Quan ly cong no khach hang"""
    
    def __init__(self, debt_service=None):
        super().__init__()
        self.debt_service = debt_service
    
    def get_all_debts(self):
        """Lay danh sach cong no"""
        try:
            if self.debt_service:
                return self.debt_service.get_all()
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai danh sach cong no")
            return []
    
    def get_summary(self):
        """Lay tong ket cong no"""
        try:
            if self.debt_service:
                return self.debt_service.get_summary()
            return {"total_debt": 0, "overdue": 0}
        except Exception as e:
            self.handle_error(e, "Khong the tinh tong ket")
            return {"total_debt": 0, "overdue": 0}
    
    def make_payment(self, customer, amount):
        """Thanh toan cong no"""
        try:
            if self.debt_service:
                result = self.debt_service.pay(customer, amount)
                self.handle_success(f"Da thanh toan {amount:,.0f} VND")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the thanh toan")
            return None