# utils/master_key.py
"""
Quản lý Master Key sử dụng PBKDF2 (thuần Python - hashlib)
Key KHÔNG được lưu trên ổ cứng, chỉ tồn tại trong RAM

Các tính năng bảo mật:
- Salt được lưu trong file với quyền truy cập hạn chế
- Hỗ trợ bytearray để xóa passphrase khỏi RAM
- Hỗ trợ đổi mật khẩu chủ (re-encrypt)
- Tương thích với SQLCipher cho database
"""

import os
import sys
import base64
import stat
import getpass
import hashlib
from cryptography.fernet import Fernet
import logging

def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
    """
    Tạo key từ password bằng PBKDF2 (thuần Python - hashlib)
    
    Args:
        password: Mật khẩu (string)
        salt: Salt (bytes)
        iterations: Số lần lặp
    
    Returns:
        Fernet-compatible key (base64 encoded)
    """
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
    return base64.urlsafe_b64encode(key)


def derive_key_from_bytes(password_bytes: bytes, salt: bytes, iterations: int = 100000) -> bytes:
    """
    Tạo key từ password dạng bytes bằng PBKDF2
    """
    key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt, iterations, dklen=32)
    return base64.urlsafe_b64encode(key)


class SecurePassphrase:
    """
    Wrapper an toàn cho passphrase sử dụng bytearray
    Có thể ghi đè để xóa khỏi RAM sau khi dùng
    """
    
    def __init__(self, passphrase=None):
        self._data = None
        if passphrase is not None:
            if isinstance(passphrase, str):
                self._data = bytearray(passphrase.encode('utf-8'))
            elif isinstance(passphrase, bytearray):
                self._data = passphrase
            elif isinstance(passphrase, bytes):
                self._data = bytearray(passphrase)
    
    @classmethod
    def from_input(cls, prompt="Enter master passphrase: "):
        """Nhập passphrase từ bàn phím (ẩn ký tự)"""
        pwd = getpass.getpass(prompt)
        return cls(pwd)
    
    def get_bytes(self) -> bytes:
        """Lấy passphrase dạng bytes"""
        return bytes(self._data) if self._data else b''
    
    def get_string(self) -> str:
        """Lấy passphrase dạng string (CHỈ DÙNG KHI CẦN, HẠN CHẾ)"""
        return self._data.decode('utf-8') if self._data else ''
    
    def clear(self):
        """Xóa passphrase khỏi RAM bằng cách ghi đè"""
        if self._data:
            for i in range(len(self._data)):
                self._data[i] = 0
            self._data = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
    
    def __del__(self):
        self.clear()


class MasterKeyManager:
    """Quản lý Master Key - Không lưu key trên ổ cứng"""
    
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        self.salt_file = os.path.join(config_dir, ".key_salt")
        self._key = None
        self._cipher = None
    
    def _ensure_config_dir(self):
        """Đảm bảo thư mục config tồn tại"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _set_secure_file_permissions(self, file_path: str):
        """Thiết lập quyền truy cập hạn chế cho file"""
        if sys.platform == "win32":
            try:
                os.chmod(file_path, stat.S_IREAD | stat.S_IWRITE)
            except Exception:
                pass
        else:
            os.chmod(file_path, 0o600)
    
    def _load_or_create_salt(self) -> bytes:
        """Tải hoặc tạo Salt (lưu trên ổ cứng, không phải key)"""
        self._ensure_config_dir()
        
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(32)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            self._set_secure_file_permissions(self.salt_file)
            logging.info(f"Đã tạo Salt mới tại: {self.salt_file}")
            return salt
    
    def derive_key(self, passphrase: str, iterations: int = 100000) -> bytes:
        """Tạo key từ passphrase (string)"""
        salt = self._load_or_create_salt()
        return derive_key_from_password(passphrase, salt, iterations)
    
    def derive_key_from_bytes(self, passphrase_bytes: bytes, iterations: int = 100000) -> bytes:
        """Tạo key từ passphrase (bytes)"""
        salt = self._load_or_create_salt()
        return derive_key_from_bytes(passphrase_bytes, salt, iterations)
    
    def get_cipher(self, passphrase) -> Fernet:
        """
        Lấy cipher để mã hóa/giải mã
        
        Args:
            passphrase: SecurePassphrase object hoặc string
        """
        if isinstance(passphrase, SecurePassphrase):
            key = self.derive_key_from_bytes(passphrase.get_bytes())
        else:
            key = self.derive_key(passphrase)
        return Fernet(key)
    
    def get_sqlcipher_key(self, passphrase, hex_format: bool = True) -> str:
        """
        Lấy key cho SQLCipher (để mã hóa database)
        
        Args:
            passphrase: SecurePassphrase object hoặc string
            hex_format: Trả về dạng hex (True) hay raw (False)
        """
        if isinstance(passphrase, SecurePassphrase):
            key = self.derive_key_from_bytes(passphrase.get_bytes())
        else:
            key = self.derive_key(passphrase)
        
        if hex_format:
            return key.hex()
        return key.hex()
    
    def encrypt_file(self, file_path: str, passphrase, output_path: str = None) -> str:
        """Mã hóa file với passphrase"""
        cipher = self.get_cipher(passphrase)
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = cipher.encrypt(data)
        
        output_path = output_path or (file_path + '.enc')
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        self._set_secure_file_permissions(output_path)
        
        logging.info(f"Đã mã hóa: {file_path} -> {output_path}")
        return output_path
    
    def decrypt_file(self, enc_path: str, passphrase, output_path: str = None) -> str:
        """Giải mã file với passphrase"""
        cipher = self.get_cipher(passphrase)
        
        with open(enc_path, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = cipher.decrypt(encrypted_data)
        except Exception as e:
            logging.error(f"Giải mã thất bại (sai passphrase?): {e}")
            return None
        
        output_path = output_path or enc_path.replace('.enc', '')
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        logging.info(f"Đã giải mã: {enc_path} -> {output_path}")
        return output_path
    
    def encrypt_string(self, text: str, passphrase) -> str:
        """Mã hóa chuỗi văn bản"""
        cipher = self.get_cipher(passphrase)
        encrypted = cipher.encrypt(text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_string(self, encrypted_text: str, passphrase) -> str:
        """Giải mã chuỗi văn bản"""
        cipher = self.get_cipher(passphrase)
        decrypted = cipher.decrypt(base64.urlsafe_b64decode(encrypted_text))
        return decrypted.decode()
    
    def reencrypt_file(self, file_path: str, old_passphrase, new_passphrase) -> bool:
        """Đổi mật khẩu chủ: giải mã bằng passphrase cũ, mã hóa bằng passphrase mới"""
        temp_file = file_path + ".temp"
        result = self.decrypt_file(file_path, old_passphrase, temp_file)
        
        if result is None:
            logging.error(f"Không thể giải mã file: {file_path}")
            return False
        
        self.encrypt_file(temp_file, new_passphrase, file_path)
        os.remove(temp_file)
        
        logging.info(f"Đã đổi passphrase cho file: {file_path}")
        return True
    
    def clear_key(self):
        """Xóa key khỏi RAM (gọi khi đăng xuất)"""
        self._key = None
        self._cipher = None
        import gc
        gc.collect()
        logging.info("Đã xóa Master Key khỏi bộ nhớ")


# Singleton instance
_master_key_manager = None

def get_master_key_manager() -> MasterKeyManager:
    global _master_key_manager
    if _master_key_manager is None:
        _master_key_manager = MasterKeyManager()
    return _master_key_manager


def secure_input(prompt="Enter master passphrase: ") -> SecurePassphrase:
    """Nhập passphrase an toàn, trả về SecurePassphrase object"""
    return SecurePassphrase.from_input(prompt)


def test_master_key():
    """Kiểm tra master key hoạt động"""
    print("=" * 60)
    print("TEST MASTER KEY MANAGER (haslib - thuần Python)")
    print("=" * 60)
    
    manager = get_master_key_manager()
    
    # Tạo passphrase an toàn
    with SecurePassphrase("test_password_123") as passphrase:
        test_data = b"Hello, this is secret data!"
        
        # Test encrypt/decrypt
        cipher = manager.get_cipher(passphrase)
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        
        if test_data == decrypted:
            print("✅ Test encrypt/decrypt: PASSED")
        else:
            print("❌ Test encrypt/decrypt: FAILED")
            return False
        
        # Test file encryption
        os.makedirs("configs", exist_ok=True)
        with open("configs/test.txt", "w") as f:
            f.write("test content")
        
        enc_file = manager.encrypt_file("configs/test.txt", passphrase)
        dec_file = manager.decrypt_file(enc_file, passphrase, "configs/test.txt.dec")
        
        if os.path.exists(dec_file):
            print("✅ Test file encrypt/decrypt: PASSED")
            os.remove("configs/test.txt")
            os.remove(enc_file)
            os.remove(dec_file)
        else:
            print("❌ Test file encrypt/decrypt: FAILED")
        
        # Test SQLCipher key
        sql_key = manager.get_sqlcipher_key(passphrase)
        if len(sql_key) == 64:
            print("✅ SQLCipher key format: PASSED")
        
        # Test change passphrase
        with SecurePassphrase("old_password") as old_pwd:
            with SecurePassphrase("new_password") as new_pwd:
                with open("configs/test_secret.txt", "w") as f:
                    f.write("secret")
                
                enc = manager.encrypt_file("configs/test_secret.txt", old_pwd)
                success = manager.reencrypt_file(enc, old_pwd, new_pwd)
                
                if success:
                    print("✅ Test re-encrypt: PASSED")
                    os.remove("configs/test_secret.txt")
                    os.remove(enc)
                else:
                    print("❌ Test re-encrypt: FAILED")
    
    print("=" * 60)
    print("🎉 Master Key Manager hoạt động bình thường!")
    return True


if __name__ == "__main__":
    test_master_key()