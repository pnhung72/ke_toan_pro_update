# -*- coding: utf-8 -*-
from views.tabs.base_tab import BaseTab
from tkinter import ttk

class MarketingTab(BaseTab):
    """Tab Marketing - Kế thừa từ BaseTab (tự là 1 Frame)"""
    
    def __init__(self, parent, notebook, *args, **kwargs):
        # Gọi khởi tạo BaseTab với các tham số bắt buộc.
        # *args và **kwargs giúp hứng các tham số thừa từ add_tab_safe, tránh lỗi.
        super().__init__(parent, notebook)
        
    def setup_ui(self):
        """Thiết lập giao diện - Dùng 'self' làm cha trực tiếp"""
        print("✅ [UI] MarketingTab đã sẵn sàng.")
        
        # Ví dụ một label trong tab này:
        label = ttk.Label(self, text="Chào mừng đến với Tab Marketing", font=("Segoe UI", 12))
        label.pack(pady=20)
        
    def bind_events(self):
        """Thiết lập sự kiện"""
        pass
        
    def load_data(self):
        """Tải dữ liệu marketing"""
        pass