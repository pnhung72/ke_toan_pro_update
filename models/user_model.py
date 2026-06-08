# -*- coding: utf-8 -*-
"""
UserModel - Quan ly nguoi dung va phan quyen
"""

import sqlite3
import hashlib
from datetime import datetime
from utils.license_helper import get_machine_id # Import module định danh máy
import json # Để xử lý danh sách tính năng

class UserModel:
    """Model quan ly nguoi dung"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Tao bang nguoi dung va phan quyen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Bang users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        ''')
        
        # Bang roles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')
        
        # Bang permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                module TEXT NOT NULL,
                can_view INTEGER DEFAULT 0,
                can_edit INTEGER DEFAULT 0,
                can_delete INTEGER DEFAULT 0,
                UNIQUE(role, module)
            )
        ''')
        
        # Tao role mac dinh
        default_roles = [
            ("admin", "Quan tri vien - Toan quyen"),
            ("ke_toan", "Ke toan - Xem va sua du lieu"),
            ("thu_ngan", "Thu ngan - Chi nhap giao dich"),
            ("viewer", "Nguoi xem - Chi xem bao cao")
        ]
        
        for role, desc in default_roles:
            cursor.execute('INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)', (role, desc))
        
        # Tao permission mac dinh
        self._init_default_permissions(cursor)
        
        # Tao admin mac dinh (neu chua co)
        admin_password = self._hash_password("admin123")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', ("admin", admin_password, "Administrator", "admin", 1))
        
        conn.commit()
        # --- [BẮT ĐẦU CẢI TIẾN CHIẾN LƯỢC QUẢN LÝ GIÁ] ---
        # 1. Tạo bảng feature_tiers: Định nghĩa các gói sản phẩm
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_tiers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier_name TEXT UNIQUE NOT NULL,      -- Ví dụ: 'BASIC', 'PRO', 'PREMIUM'
                allowed_features TEXT,               -- Danh sách mã tính năng (csv)
                description TEXT
            )
        ''')

        # 2. Tạo bảng software_licenses: Quản lý bản quyền máy khách
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS software_licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT UNIQUE NOT NULL,     -- ID phần cứng duy nhất
                tier_id INTEGER,                     -- Liên kết với gói cước
                license_key TEXT,                    -- Mã kích hoạt đã mã hóa
                expiry_date DATETIME,                -- Ngày hết hạn
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (tier_id) REFERENCES feature_tiers(id)
            )
        ''')

        # 3. Khởi tạo dữ liệu gói mẫu nếu bảng đang trống
        cursor.execute("SELECT COUNT(*) FROM feature_tiers")
        if cursor.fetchone()[0] == 0:
            # Gói Basic: Các nghiệp vụ kế toán cơ bản
            cursor.execute("INSERT INTO feature_tiers (tier_name, allowed_features, description) VALUES (?, ?, ?)", 
                          ('BASIC', 'product,invoice,transaction,debt', 'Gói kế toán nội bộ cơ bản'))
            # Gói Pro: Đầy đủ tính năng cao cấp (Thuế, Excel, Báo cáo chuyên sâu)
            cursor.execute("INSERT INTO feature_tiers (tier_name, allowed_features, description) VALUES (?, ?, ?)", 
                          ('PRO', 'product,invoice,transaction,debt,tax_report,excel_export', 'Gói chuyên nghiệp đầy đủ tính năng'))
        
        conn.commit()
        # --- [KẾT THÚC CẢI TIẾN CHIẾN LƯỢC QUẢN LÝ GIÁ] ---
        conn.close()
    
    def _init_default_permissions(self, cursor):
        """Tao phan quyen mac dinh"""
        modules = ["product", "invoice", "transaction", "debt", "report", "user"]
        
        # Admin: full quyen
        for module in modules:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (role, module, can_view, can_edit, can_delete)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", module, 1, 1, 1))
        
        # Ke toan: xem va sua
        for module in modules:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (role, module, can_view, can_edit, can_delete)
                VALUES (?, ?, ?, ?, ?)
            ''', ("ke_toan", module, 1, 1, 0))
        
        # Thu ngan: chi nhap giao dich
        cursor.execute('''
            INSERT OR IGNORE INTO permissions (role, module, can_view, can_edit, can_delete)
            VALUES (?, ?, ?, ?, ?)
        ''', ("thu_ngan", "transaction", 1, 1, 0))
        
        # Viewer: chi xem bao cao
        cursor.execute('''
            INSERT OR IGNORE INTO permissions (role, module, can_view, can_edit, can_delete)
            VALUES (?, ?, ?, ?, ?)
        ''', ("viewer", "report", 1, 0, 0))
    
    def _hash_password(self, password):
        """Ma hoa mat khau"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """Xac thuc nguoi dung"""
        password_hash = self._hash_password(password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, role, is_active
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Cap nhat thoi gian dang nhap
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user[0]))
            conn.commit()
        
        conn.close()
        
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "full_name": user[2],
                "role": user[3],
                "is_active": user[4]
            }
        return None
    
    def get_user_permissions(self, role):
        """Lay quyen cua nguoi dung"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT module, can_view, can_edit, can_delete
            FROM permissions
            WHERE role = ?
        ''', (role,))
        
        permissions = {}
        for row in cursor.fetchall():
            permissions[row[0]] = {
                "can_view": bool(row[1]),
                "can_edit": bool(row[2]),
                "can_delete": bool(row[3])
            }
        
        conn.close()
        return permissions
    
    def has_permission(self, role, module, action):
        """Kiem tra quyen"""
        permissions = self.get_user_permissions(role)
        
        if module not in permissions:
            return False
        
        if action == "view":
            return permissions[module].get("can_view", False)
        elif action == "edit":
            return permissions[module].get("can_edit", False)
        elif action == "delete":
            return permissions[module].get("can_delete", False)
        
        return False
    
    def add_user(self, username, password, full_name, email, role):
        """Them nguoi dung moi"""
        password_hash = self._hash_password(password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, role))
            conn.commit()
            result = {"success": True, "message": "Them nguoi dung thanh cong"}
        except sqlite3.IntegrityError:
            result = {"success": False, "message": "Ten dang nhap da ton tai"}
        finally:
            conn.close()
        
        return result
    
    def get_all_users(self):
        """Lay danh sach nguoi dung"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, email, role, is_active, last_login
            FROM users
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "full_name": row[2],
                "email": row[3],
                "role": row[4],
                "is_active": bool(row[5]),
                "last_login": row[6]
            })
        
        conn.close()
        return users
        
    def change_password(self, username, old_password, new_password):
        """Đổi mật khẩu cho user, kiểm tra mật khẩu cũ"""
        import hashlib
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if not row:
                return False, "Người dùng không tồn tại"
            if row['password'] != old_hash:
                return False, "Mật khẩu cũ không đúng"
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_hash, username))
            conn.commit()
            return True, "Đổi mật khẩu thành công"
            
    def check_feature_access(self, feature_name):
        """
        Kiểm tra xem gói cước hiện tại của máy này có được phép dùng tính năng này không.
        Đây là lớp bảo mật thứ 2 sau phân quyền Role.
        """
        machine_id = get_machine_id()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Truy vấn gói cước dựa trên Machine ID
            cursor.execute('''
                SELECT ft.allowed_features 
                FROM software_licenses sl
                JOIN feature_tiers ft ON sl.tier_id = ft.id
                WHERE sl.machine_id = ? AND sl.is_active = 1
                AND (sl.expiry_date > DATETIME('now') OR sl.expiry_date IS NULL)
            ''', (machine_id,))
            
            row = cursor.fetchone()
            if not row:
                # Nếu chưa có License hoặc hết hạn, mặc định chỉ cho dùng các tính năng rất cơ bản
                # Hoặc anh có thể cho dùng thử gói BASIC
                return feature_name in ['product', 'transaction']
            
            allowed_features = row[0].split(',') # Chuyển chuỗi 'invoice,tax' thành list
            return feature_name in allowed_features
            
        except Exception as e:
            logging.error(f"Lỗi kiểm tra gói cước: {e}")
            return False
        finally:
            conn.close()