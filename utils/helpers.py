import re
from datetime import datetime

def format_currency(amount):
    """Định dạng số tiền"""
    try:
        return f"{amount:,.0f} VNĐ"
    except Exception:
        return "0 VNĐ"

def format_date(date_str):
    """Định dạng ngày tháng"""
    try:
        if '/' in date_str:
            d, m, y = date_str.split('/')
            return f"{int(d):02d}/{int(m):02d}/{y}"
    except Exception:
        pass
    return date_str

def validate_mst(ma_so_thue):
    """Kiểm tra mã số thuế (10 hoặc 13 số)"""
    pattern = r'^\d{10}(-\d{3})?$'
    return re.match(pattern, str(ma_so_thue)) is not None

def get_current_quarter():
    """Lấy quý hiện tại"""
    month = datetime.now().month
    if month <= 3:
        return 1
    elif month <= 6:
        return 2
    elif month <= 9:
        return 3
    else:
        return 4

def get_current_year():
    """Lấy năm hiện tại"""
    return datetime.now().year

def get_quarter_months(quarter):
    """Lấy các tháng trong quý"""
    if quarter == 1:
        return [1, 2, 3]
    elif quarter == 2:
        return [4, 5, 6]
    elif quarter == 3:
        return [7, 8, 9]
    else:
        return [10, 11, 12]