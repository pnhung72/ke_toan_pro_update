# -*- coding: utf-8 -*-
"""
TransactionController - Xu ly logic cho giao dich thu chi
"""

from controllers.base_controller import BaseController

class TransactionController(BaseController):
    """Quan ly giao dich thu chi"""
    
    def __init__(self, transaction_service=None):
        super().__init__()
        self.transaction_service = transaction_service
    
    def get_all_transactions(self):
        """Lay danh sach giao dich"""
        try:
            if self.transaction_service:
                return self.transaction_service.get_all()
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai danh sach giao dich")
            return []
    
    def get_transactions_by_date(self, start_date, end_date):
        """Lay giao dich theo khoang thoi gian"""
        try:
            if self.transaction_service:
                return self.transaction_service.get_by_date_range(start_date, end_date)
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai giao dich theo ngay")
            return []
    
    def add_transaction(self, transaction_data):
        """Them giao dich moi"""
        try:
            if self.transaction_service:
                result = self.transaction_service.add(transaction_data)
                self.handle_success("Da them giao dich")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the them giao dich")
            return None
    
    def get_summary(self):
        """Lay tong ket thu chi"""
        try:
            if self.transaction_service:
                return self.transaction_service.get_summary()
            return {"income": 0, "expense": 0, "balance": 0}
        except Exception as e:
            self.handle_error(e, "Khong the tinh tong ket")
            return {"income": 0, "expense": 0, "balance": 0}