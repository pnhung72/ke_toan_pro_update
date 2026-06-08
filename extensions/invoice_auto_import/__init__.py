"""
Extension: Tự động nhận hóa đơn XML từ email
Phiên bản 1.0 - dành cho Kế toán Pro v14.0.15

Cách sử dụng:
    from extensions.invoice_auto_import import init_extension
    init_extension(main_window=None, db_connection=None)
"""

from .logger import setup_logger as init_logger
from .queue_db import init_queue_table
from . import hook_email

def init_extension(main_window=None, db_connection=None):
    """
    Khởi tạo extension:
        - Tạo bảng queue nếu chưa có
        - Thiết lập logger
        - (Tùy chọn) Kết nối signal để mở dialog duyệt từ menu
    """
    init_logger()
    init_queue_table()
    # Nếu có main_window, có thể thêm menu item ở đây (tùy chọn)
    if main_window:
        # Ví dụ: thêm menu item "Duyệt hóa đơn XML" vào menu Công cụ
        try:
            from PyQt5.QtWidgets import QAction
            action = QAction("Duyệt hóa đơn XML", main_window)
            action.triggered.connect(lambda: show_approval_dialog(main_window))
            # Giả sử main_window có menu "Công cụ" - bạn cần điều chỉnh theo cấu trúc menu thực tế
            if hasattr(main_window, 'menu_tools'):
                main_window.menu_tools.addAction(action)
            else:
                # Nếu không tìm thấy menu, thêm vào menu bar
                menubar = main_window.menuBar()
                tools_menu = menubar.addMenu("Công cụ mở rộng")
                tools_menu.addAction(action)
        except Exception as e:
            from .logger import get_logger
            get_logger().error(f"Không thể thêm menu item: {e}")

def show_approval_dialog(parent):
    """Hiển thị cửa sổ duyệt hóa đơn"""
    from .approval_dialog import ApprovalDialog
    # Lấy global_font từ main window nếu có
    global_font = getattr(parent, 'global_font', None)
    dialog = ApprovalDialog(parent, global_font=global_font)
    dialog.exec_()