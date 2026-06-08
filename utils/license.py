import os
import json
import hashlib
import uuid
import socket
import sys
from datetime import datetime

SECRET_KEY = "KeToanPro_2026_Secret"

def get_machine_id():
    mac = uuid.getnode()
    hostname = socket.gethostname()
    username = os.getlogin()
    combined = f"{mac}{hostname}{username}"
    return hashlib.sha256(combined.encode()).hexdigest()

def is_admin():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        admin_file = os.path.join(base_dir, 'admin.key')
        result = os.path.exists(admin_file)
        #print(f"[DEBUG is_admin] base_dir={base_dir}, admin_file={admin_file}, exists={result}")
        return result
    except Exception as e:
        #print(f"[DEBUG is_admin] ERROR: {e}")
        return False

def _get_license_data():
    """Đọc và giải mã file license.key, trả về dict hoặc None"""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        license_path = os.path.join(base_dir, 'license.key')
        if not os.path.exists(license_path):
            return None
        with open(license_path, 'r') as f:
            data = json.load(f)
        # Kiểm tra chữ ký
        machine_id = get_machine_id()
        if data.get("machine_id") != machine_id:
            return None
        signing_data = f"{data['machine_id']}|{data['expiry']}|{SECRET_KEY}"
        expected = hashlib.sha256(signing_data.encode()).hexdigest()
        if expected != data.get("signature"):
            return None
        # Kiểm tra hết hạn
        expiry = datetime.strptime(data["expiry"], "%Y-%m-%d")
        if datetime.now() > expiry:
            return None
        return data
    except Exception:
        return None

def verify_license():
    """Kiểm tra license hợp lệ (có hiệu lực)"""
    return _get_license_data() is not None

def get_license_features():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        license_path = os.path.join(base_dir, 'license.key')
        #print(f"[DEBUG get_license_features] license_path={license_path}, exists={os.path.exists(license_path)}")
        if not os.path.exists(license_path):
            return []
        with open(license_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        features_str = data.get('features', '')
        #print(f"[DEBUG get_license_features] features_str={features_str}")
        return [f.strip() for f in features_str.split(',') if f.strip()]
    except Exception as e:
        #print(f"[DEBUG get_license_features] ERROR: {e}")
        return []

def has_feature(feature_name):
    """Kiểm tra xem license có chứa feature cụ thể không"""
    return feature_name in get_license_features()

def is_full_version():
    """Admin hoặc có license hợp lệ (không cần feature)"""
    return is_admin() or verify_license()

# Hàm tiện ích cho AI
def has_ai_feature():
    # Admin luôn được dùng AI (không cần license)
    if is_admin():
        return True
    # Ngược lại, kiểm tra license có feature 'ai_analytics' không
    return has_feature('ai_analytics')