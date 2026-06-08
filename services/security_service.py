# -*- coding: utf-8 -*-
"""
SecurityService - Dich vu bao mat
"""

import re
import hashlib
from core.security.encryption import DataEncryption

class SecurityService:
    """Dich vu bao mat tong hop"""
    
    def __init__(self):
        self.encryption = DataEncryption()
    
    def sanitize_input(self, text):
        """Lam sach dau vao tranh SQL injection"""
        if text is None:
            return ""
        # Xoa cac ky tu dac biet nguy hiem
        dangerous_chars = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
        result = text
        for char in dangerous_chars:
            result = result.replace(char, "")
        return result.strip()
    
    def validate_password(self, password):
        """Kiem tra do manh cua mat khau"""
        score = 0
        feedback = []
        
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Mat khau can it nhat 8 ky tu")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("Can co it nhat 1 ky tu in hoa")
        
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("Can co it nhat 1 ky tu thuong")
        
        if re.search(r'\d', password):
            score += 1
        else:
            feedback.append("Can co it nhat 1 so")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("Can co it nhat 1 ky tu dac biet")
        
        if score >= 4:
            strength = "Manh"
        elif score >= 3:
            strength = "Trung binh"
        else:
            strength = "Yeu"
        
        return {
            "score": score,
            "strength": strength,
            "feedback": feedback
        }
    
    def mask_sensitive_data(self, data, show_last=4):
        """An cac thong tin nham cam"""
        if not data:
            return ""
        data_str = str(data)
        if len(data_str) <= show_last:
            return "*" * len(data_str)
        return "*" * (len(data_str) - show_last) + data_str[-show_last:]
    
    def hash_data(self, data):
        """Tao hash cho du lieu"""
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()