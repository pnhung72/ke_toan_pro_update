# -*- coding: utf-8 -*-
"""
Encryption - Ma hoa du lieu nham cam
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class DataEncryption:
    """Ma hoa va giai ma du lieu"""
    
    def __init__(self, password=None):
        if password is None:
            password = "KeToanPro2026@Secure"
        self.key = self._generate_key(password)
        self.cipher = Fernet(self.key)
    
    def _generate_key(self, password):
        """Tao key tu password"""
        password_bytes = password.encode('utf-8')
        salt = b'ke_toan_pro_salt_2026'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt(self, data):
        """Ma hoa du lieu"""
        if data is None:
            return None
        data_bytes = str(data).encode('utf-8')
        encrypted = self.cipher.encrypt(data_bytes)
        return encrypted.decode('utf-8')
    
    def decrypt(self, encrypted_data):
        """Giai ma du lieu"""
        if encrypted_data is None:
            return None
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted.decode('utf-8')
        except Exception:
            return None
    
    def encrypt_dict(self, data_dict, fields):
        """Ma hoa cac truong trong dict"""
        result = data_dict.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(result[field])
        return result
    
    def decrypt_dict(self, data_dict, fields):
        """Giai ma cac truong trong dict"""
        result = data_dict.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(result[field])
        return result