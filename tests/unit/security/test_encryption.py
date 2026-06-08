# -*- coding: utf-8 -*-
"""
Unit tests for Encryption module
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from core.security.encryption import DataEncryption


class TestEncryption(unittest.TestCase):
    """Test cases for DataEncryption"""
    
    def setUp(self):
        self.encryption = DataEncryption("test_password")
    
    def test_encrypt_decrypt_string(self):
        """Test mã hóa và giải mã chuỗi"""
        original = "Hello World 123!@#"
        encrypted = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(encrypted)
        
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, original)
        self.assertEqual(decrypted, original)
    
    def test_encrypt_decrypt_empty(self):
        """Test mã hóa chuỗi rỗng"""
        original = ""
        encrypted = self.encryption.encrypt(original)
        decrypted = self.encryption.decrypt(encrypted)
        
        self.assertEqual(decrypted, original)
    
    def test_encrypt_decrypt_none(self):
        """Test mã hóa None"""
        encrypted = self.encryption.encrypt(None)
        self.assertIsNone(encrypted)
        
        decrypted = self.encryption.decrypt(None)
        self.assertIsNone(decrypted)
    
    def test_encrypt_dict(self):
        """Test mã hóa dictionary"""
        data = {
            "name": "Nguyen Van A",
            "phone": "0987654321",
            "email": "test@example.com"
        }
        
        encrypted = self.encryption.encrypt_dict(data, ["phone", "email"])
        
        self.assertNotEqual(encrypted["phone"], data["phone"])
        self.assertNotEqual(encrypted["email"], data["email"])
        self.assertEqual(encrypted["name"], data["name"])
        
        decrypted = self.encryption.decrypt_dict(encrypted, ["phone", "email"])
        self.assertEqual(decrypted["phone"], data["phone"])
        self.assertEqual(decrypted["email"], data["email"])
    
    def test_different_keys_produce_different_results(self):
        """Test khóa khác nhau cho kết quả khác nhau"""
        enc1 = DataEncryption("password1")
        enc2 = DataEncryption("password2")
        
        original = "Secret data"
        encrypted1 = enc1.encrypt(original)
        encrypted2 = enc2.encrypt(original)
        
        self.assertNotEqual(encrypted1, encrypted2)


if __name__ == "__main__":
    unittest.main()