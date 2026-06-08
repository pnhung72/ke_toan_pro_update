# utils/license_manager.py
import os
import json
import hashlib
import hmac
import subprocess
import uuid
from datetime import datetime, timedelta
from models.database import Database
# Import VERSION từ file cấu hình chung để tự động đồng bộ khi chạy build_release.bat
try:
    from config import VERSION
except ImportError:
    VERSION = "8.0.0"  # Dự phòng nếu file cấu hình chưa khởi tạo

SECRET_KEY = b'KeToanPro_2026_Secret_Key_DoNotShare'

def get_machine_id():
    """Lấy mã máy duy nhất (dựa trên UUID của máy tính)"""
    try:
        # Thử lấy UUID từ wmic
        result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            machine_id = lines[1].strip()
            if machine_id:
                return machine_id
    except Exception:
        pass
    # Fallback: dùng MAC address hoặc random
    return str(uuid.getnode())

def generate_license_key(machine_id, package, expiry_date=None):
    """Tạo license key dạng mã hóa"""
    data = f"{machine_id}|{package}|{expiry_date or 'forever'}"
    signature = hmac.new(SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{machine_id[:8]}-{package[:3]}-{signature[:16]}"

def verify_license(license_key):
    """Kiểm tra license key có hợp lệ không (dùng khi chạy phần mềm)"""
    try:
        with open('license.key', 'r') as f:
            data = json.load(f)
        sig = data.pop('signature')
        data_str = json.dumps(data, sort_keys=True)
        expected = hmac.new(SECRET_KEY, data_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return False, "Chữ ký không hợp lệ"
        if data.get('expiry_date'):
            expiry = datetime.strptime(data['expiry_date'], '%Y-%m-%d')
            if datetime.now() > expiry:
                return False, "License đã hết hạn"
        # Thay vì trả về 'basic' cố định, ưu tiên gói trong cấu hình hoặc ghi nhận từ tệp tin dữ liệu
        return True, data.get('package', 'enterprise')
    except Exception:
        return False, "Không tìm thấy hoặc lỗi license"

def save_customer(machine_id, full_name, email, phone, package, expiry_date):
    """Lưu thông tin khách hàng vào database"""
    license_key = generate_license_key(machine_id, package, expiry_date)
    with Database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO customers 
            (machine_id, full_name, email, phone, package, license_key, issued_date, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (machine_id, full_name, email, phone, package, license_key, 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'), expiry_date))
        conn.commit()
    return license_key

def export_license_file(machine_id, package, expiry_date, features="", output_path='license.key'):
    """
    Xuất file license.key để gửi cho khách (Đồng bộ động v{VERSION})
    features: chuỗi các tính năng cách nhau bởi dấu phẩy (vd: 'marketing,distribution')
    """
    license_data = {
        'machine_id': machine_id,
        'package': package,
        'expiry_date': expiry_date,
        'features': features,  # Bảo toàn tính năng đóng gói features của anh
        'issued_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'app_version': VERSION  # Gắn kèm thông tin phiên bản động vào cấu trúc file
    }
    
    # Chuyển thành chuỗi JSON để tạo chữ ký bảo mật
    # sort_keys=True rất quan trọng để đảm bảo thứ tự dữ liệu luôn đồng nhất
    data_str = json.dumps(license_data, sort_keys=True)
    
    # Tạo chữ ký HMAC (Nếu khách hàng tự ý sửa 'features' trong file, chữ ký sẽ sai ngay)
    signature = hmac.new(SECRET_KEY, data_str.encode(), hashlib.sha256).hexdigest()
    license_data['signature'] = signature
    
    # Ghi ra file gửi cho khách
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(license_data, f, indent=4, ensure_ascii=False)
        
    return output_path

def get_all_customers():
    """Lấy danh sách tất cả khách hàng"""
    with Database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY id DESC")
        return cursor.fetchall()
        
def verify_license_info():
    """
    Đọc file license.key và trả về toàn bộ thông tin để MainWindow 
    kiểm tra chuỗi 'features' phù hợp với phiên bản đang chạy.
    """
    try:
        with open('license.key', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data 
    except Exception as e:
        logging.error(f"Không đọc được License cho phiên bản {VERSION}: {e}")
        return {} # Trả về rỗng nếu không có license
        
# Thêm hàm này vào cuối file license_manager.py để tính tiền cho giao diện mới
def calculate_package_price(package_type, add_ons):
    """
    package_type: 'cơ bản', 'chuyên nghiệp', 'vĩnh viễn'
    add_ons: list các tính năng mua thêm
    """
    prices = {
        'cơ bản': 1000000, 
        'chuyên nghiệp': 2000000,
        'vĩnh viễn': 5000000
    }
    addon_prices = {
        'xuất_khẩu_excel': 200000,
        'quản_lý_trạm': 500000
    }
    
    total = prices.get(package_type, 0)
    for item in add_ons:
        total += addon_prices.get(item, 0)
    return total
    
def activate_license_key(key):
    """
    Kích hoạt license từ mã key nhập tay (thay vì copy file)
    key: chuỗi mã kích hoạt (có thể là nội dung của file license.key)
    Trả về: (success, message)
    """
    import json
    from pathlib import Path
    
    license_file = Path("license.key")
    try:
        # Ghi nội dung key vào file license.key
        license_file.write_text(key.strip(), encoding='utf-8')
        # Xác thực license bằng hàm có sẵn (kiểm tra chữ ký, hạn dùng)
        from utils.license_manager import verify_license
        is_valid, package_or_error = verify_license(None)  # verify_license không cần tham số, nó tự đọc file
        if is_valid:
            return True, f"Kích hoạt thành công! (Gói: {package_or_error}) Vui lòng khởi động lại phần mềm."
        else:
            license_file.unlink(missing_ok=True)
            return False, f"Mã kích hoạt không hợp lệ: {package_or_error}"
    except Exception as e:
        return False, f"Lỗi khi kích hoạt: {e}"