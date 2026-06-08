# -*- coding: utf-8 -*-
"""
InvoiceController - Xu ly logic cho hoa don
"""

from controllers.base_controller import BaseController

class InvoiceController(BaseController):
    """Quan ly hoa don"""
    
    def __init__(self, invoice_service=None, product_service=None):
        super().__init__()
        self.invoice_service = invoice_service
        self.product_service = product_service
    
    def get_all_invoices(self):
        """Lay danh sach hoa don"""
        try:
            if self.invoice_service:
                return self.invoice_service.get_all()
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai danh sach hoa don")
            return []
    
    def get_invoice_by_id(self, invoice_id):
        """Lay hoa don theo ID"""
        try:
            if self.invoice_service:
                return self.invoice_service.get_by_id(invoice_id)
            return None
        except Exception as e:
            self.handle_error(e, f"Khong the tai hoa don {invoice_id}")
            return None
    
    def create_invoice(self, invoice_data):
        """Tao hoa don moi"""
        try:
            if self.invoice_service:
                result = self.invoice_service.create(invoice_data)
                self.handle_success("Da tao hoa don")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the tao hoa don")
            return None
    
    def get_products(self):
        """Lay danh sach san pham de chon"""
        try:
            if self.product_service:
                return self.product_service.get_all()
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai san pham")
            return []
    
    def calculate_total(self, items):
        """Tinh tong tien hoa don"""
        total = 0
        for item in items:
            total += item.get('price', 0) * item.get('quantity', 1)
        return total