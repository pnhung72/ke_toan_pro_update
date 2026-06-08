# -*- coding: utf-8 -*-
"""
Unit tests for SecurityService
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from services.security_service import SecurityService


class TestSecurityService(unittest.TestCase):
    """Test cases for SecurityService"""
    
    def setUp(self):
        self.service = SecurityService()
    
    def test_sanitize_input(self):
        """Test làm sạch input"""
        test_cases = [
            ("normal text", "normal text"),
            ("text with 'quote'", "text with quote"),
            ('text with "double"', 'text with double'),
            ("DROP TABLE users;", "DROP TABLE users;"),
            ("'; DROP TABLE users; --", "; DROP TABLE users; --"),
        ]
        
        for input_text, expected in test_cases:
            result = self.service.sanitize_input(input_text)
            self.assertEqual(result, expected)
    
    def test_validate_password_weak(self):
        """Test mật khẩu yếu"""
        password = "123"
        result = self.service.validate_password(password)
        
        self.assertEqual(result["strength"], "Yeu")
        self.assertLess(result["score"], 3)
        self.assertTrue(len(result["feedback"]) > 0)
    
    def test_validate_password_strong(self):
        """Test mật khẩu mạnh"""
        password = "P@ssw0rd123!"
        result = self.service.validate_password(password)
        
        self.assertEqual(result["strength"], "Manh")
        self.assertEqual(result["score"], 5)
    
    def test_mask_sensitive_data(self):
        """Test che dữ liệu nhạy cảm"""
        phone = "0987654321"
        masked = self.service.mask_sensitive_data(phone, show_last=4)
        
        self.assertEqual(masked, "******4321")
        self.assertEqual(len(masked), len(phone))
    
    def test_mask_short_data(self):
        """Test che dữ liệu ngắn"""
        short = "123"
        masked = self.service.mask_sensitive_data(short, show_last=4)
        
        self.assertEqual(masked, "***")
    
    def test_hash_data(self):
        """Test hash dữ liệu"""
        data1 = "test_data"
        data2 = "test_data"
        data3 = "different"
        
        hash1 = self.service.hash_data(data1)
        hash2 = self.service.hash_data(data2)
        hash3 = self.service.hash_data(data3)
        
        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)
        self.assertEqual(len(hash1), 64)  # SHA256 = 64 chars


if __name__ == "__main__":
    unittest.main()