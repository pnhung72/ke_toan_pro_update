# -*- coding: utf-8 -*-
"""
ProductController - Xu ly logic cho san pham
"""

from controllers.base_controller import BaseController

class ProductController(BaseController):
    """Quan ly san pham"""
    
    def __init__(self, product_service=None):
        super().__init__()
        self.product_service = product_service
    
    def get_all_products(self):
        """Lay danh sach san pham"""
        try:
            if self.product_service:
                return self.product_service.get_all()
            return []
        except Exception as e:
            self.handle_error(e, "Khong the tai danh sach san pham")
            return []
    
    def add_product(self, product_data):
        """Them san pham moi"""
        try:
            if self.product_service:
                result = self.product_service.add(product_data)
                self.handle_success("Da them san pham")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the them san pham")
            return None
    
    def update_product(self, product_id, product_data):
        """Cap nhat san pham"""
        try:
            if self.product_service:
                result = self.product_service.update(product_id, product_data)
                self.handle_success("Da cap nhat san pham")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the cap nhat san pham")
            return None
    
    def delete_product(self, product_id):
        """Xoa san pham"""
        try:
            if self.product_service:
                result = self.product_service.delete(product_id)
                self.handle_success("Da xoa san pham")
                return result
            return None
        except Exception as e:
            self.handle_error(e, "Khong the xoa san pham")
            return None