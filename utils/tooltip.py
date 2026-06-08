# -*- coding: utf-8 -*-
"""
Tooltip - Hiển thị hướng dẫn khi di chuột
"""

import tkinter as tk
from tkinter import ttk


class ToolTip:
    """Tạo tooltip cho widget"""
    
    def __init__(self, widget, text, delay=500):
        """
        Args:
            widget: Widget cần gắn tooltip
            text: Nội dung hướng dẫn
            delay: Thời gian delay trước khi hiện (ms)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tip_window = None
        self.after_id = None
        
        # Gắn sự kiện
        widget.bind('<Enter>', self._on_enter)
        widget.bind('<Leave>', self._on_leave)
        widget.bind('<ButtonPress>', self._on_click)
    
    def _on_enter(self, event=None):
        """Khi chuột vào widget"""
        self.after_id = self.widget.after(self.delay, self._show_tip)
    
    def _on_leave(self, event=None):
        """Khi chuột rời widget"""
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        self._hide_tip()
    
    def _on_click(self, event=None):
        """Khi click vào widget - ẩn tooltip"""
        self._hide_tip()
    
    def _show_tip(self):
        """Hiển thị tooltip"""
        if self.tip_window or not self.text:
            return
        
        # Tạo cửa sổ tooltip
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Không có khung viền
        tw.wm_geometry(f'+{self._get_x()+10}+{self._get_y()+20}')
        
        # Tạo label chứa text
        label = tk.Label(
            tw, 
            text=self.text, 
            justify=tk.LEFT,
            background="#FFFFE0",  # Màu vàng nhạt
            foreground="#333333",
            relief=tk.SOLID, 
            borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(padx=4, pady=2)
    
    def _hide_tip(self):
        """Ẩn tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
    
    def _get_x(self):
        """Lấy tọa độ X của widget"""
        x = self.widget.winfo_rootx()
        return x
    
    def _get_y(self):
        """Lấy tọa độ Y của widget"""
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        return y


def add_tooltip(widget, text, delay=500):
    """Hàm tiện ích để thêm tooltip nhanh"""
    return ToolTip(widget, text, delay)