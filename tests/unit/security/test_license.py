import pytest
from datetime import datetime, timedelta
# Giả sử bạn import hàm check_license từ module service bảo mật của bạn
from core.security.license_manager import check_license_status 

def test_license_expired():
    """Kiểm tra trường hợp license đã hết hạn."""
    # Giả lập database hoặc mock dữ liệu
    license_data = {"expiry_date": "2025-01-01", "is_active": True}
    status = check_license_status(license_data)
    assert status is False, "Hệ thống phải chặn truy cập khi license đã hết hạn."

def test_license_inactive():
    """Kiểm tra trường hợp license bị vô hiệu hóa bởi quản trị viên."""
    license_data = {"expiry_date": "2026-12-31", "is_active": False}
    status = check_license_status(license_data)
    assert status is False, "Hệ thống phải chặn truy cập khi license bị vô hiệu hóa."

def test_license_valid():
    """Kiểm tra trường hợp license còn hạn và đang kích hoạt."""
    future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    license_data = {"expiry_date": future_date, "is_active": True}
    status = check_license_status(license_data)
    assert status is True, "Hệ thống phải cho phép truy cập khi license hợp lệ."

def test_missing_license():
    """Kiểm tra trường hợp không tìm thấy license trong hệ thống."""
    license_data = None
    status = check_license_status(license_data)
    assert status is False, "Hệ thống phải chặn truy cập nếu không có dữ liệu license."