# Cấu hình nguồn dữ liệu mặc định cho toàn bộ phần mềm
# Người dùng có thể thay đổi tại đây hoặc qua giao diện

DEFAULT_DATA_SOURCE = "invoices"  # 'invoices', 'transactions', 'both', 'deduplicated'

# Giải thích các chế độ:
# - 'invoices': Chỉ tính từ hóa đơn (chính xác nhất cho kê khai thuế)
# - 'transactions': Chỉ tính từ giao dịch thu (dùng nếu không có hóa đơn)
# - 'both': Cộng dồn cả hai (có thể trùng lặp)
# - 'deduplicated': Loại bỏ trùng lặp tự động (tốt nhất khi có cả hai)

def get_data_source():
    """Lấy nguồn dữ liệu hiện tại"""
    return DEFAULT_DATA_SOURCE

def set_data_source(source):
    """Thay đổi nguồn dữ liệu"""
    global DEFAULT_DATA_SOURCE
    if source in ['invoices', 'transactions', 'both', 'deduplicated']:
        DEFAULT_DATA_SOURCE = source
        return True
    return False