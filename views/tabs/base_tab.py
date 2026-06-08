# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from tkinter import ttk

class BaseTab(ttk.Frame, ABC):
    """
    BaseTab kế thừa trực tiếp từ ttk.Frame.
    Khi nạp vào notebook, chính đối tượng này là 1 Frame hợp lệ.
    """
    def __init__(self, parent, notebook, controller=None):
        # Khởi tạo Frame chính gắn thẳng vào notebook
        super().__init__(notebook)
        
        self.parent = parent
        self.notebook = notebook
        self.controller = controller
        self.is_loaded = False
        self.frame = self          # ← Thêm dòng này
        # Gọi các hàm thiết lập giao diện và sự kiện
        self.setup_ui()
        self.bind_events()

    @abstractmethod
    def setup_ui(self):
        """Thiết lập giao diện - Các lớp con cần override hàm này"""
        pass

    @abstractmethod
    def bind_events(self):
        """Thiết lập sự kiện - Các lớp con cần override hàm này"""
        pass

    @abstractmethod
    def load_data(self):
        """Load dữ liệu - Các lớp con cần override hàm này"""
        pass

    def on_tab_selected(self):
        """Hàm này nên được gọi khi Tab được chọn"""
        if not self.is_loaded:
            self.load_data()
            self.is_loaded = True

    def refresh(self):
        """Làm mới dữ liệu"""
        self.load_data()

    def get_frame(self):
        """Trả về chính nó vì bản thân class này là 1 Frame"""
        return self