# -*- coding: utf-8 -*-
"""
BaseController - Xử lý logic nghiệp vụ
"""
import logging

class BaseController:
    """Base controller cho tất cả các module"""
    
    def __init__(self, model=None):
        self.model = model
    
    def handle_error(self, error, user_message="Có lỗi xảy ra"):
        """Xử lý lỗi tập trung"""
        logging.error(f"Lỗi: {error}")
        return user_message
    
    def handle_success(self, message="Thành công"):
        """Xử lý thành công"""
        logging.info(f"{message}")
        return message