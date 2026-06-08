# -*- coding: utf-8 -*-
import subprocess
import hashlib
import platform

def get_machine_id():
    """
    Tạo mã định danh duy nhất (Machine ID) cho máy tính khách hàng.
    Kết hợp số Serial ổ cứng và tên máy để đảm bảo không trùng lặp.
    """
    try:
        # 1. Lấy số Serial của ổ cứng (Dùng lệnh WMIC trên Windows)
        cmd = "wmic diskdrive get serialnumber"
        serial = subprocess.check_output(cmd, shell=True).decode().split('\n')[1].strip()
        
        # 2. Kết hợp với tên node mạng (tên máy) để tăng độ chính xác
        raw_id = f"{serial}-{platform.node()}"
        
        # 3. Mã hóa SHA-256 để tạo một chuỗi ngắn gọn, chuyên nghiệp
        machine_hash = hashlib.sha256(raw_id.encode()).hexdigest().upper()
        
        # Trả về 16 ký tự đầu để dễ quản lý (Ví dụ: 4B8F-9A2C-11EE-55FF)
        return "-".join([machine_hash[i:i+4] for i in range(0, 16, 4)])
    except Exception:
        # Trường hợp lỗi (ví dụ máy ảo), dùng ID dự phòng từ tên máy và processor
        backup_id = f"{platform.node()}-{platform.processor()}"
        return hashlib.md5(backup_id.encode()).hexdigest()[:19].upper()

def verify_license(stored_key, machine_id):
    """
    Hàm kiểm tra xem mã Key có khớp với máy này không (Sẽ dùng ở Giai đoạn 3)
    """
    # Logic mã hóa Key của Thầy Hùng sẽ nằm ở đây
    pass