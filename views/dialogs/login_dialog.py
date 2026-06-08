# -*- coding: utf-8 -*-
"""
LoginDialog - Cửa sổ đăng nhập đã tối ưu cho font chữ lớn
"""

import tkinter as tk
from ui.theme import get_font  # Đảm bảo đường dẫn import đúng theo cấu trúc của Thầy
from tkinter import ttk, messagebox

class LoginDialog:
    """Dialog đăng nhập hệ thống"""
    
    def __init__(self, parent, user_model):
        self.parent = parent
        self.user_model = user_model
        self.result = None
        self._create_dialog()
    
    def _create_dialog(self):
        """Tạo dialog đăng nhập"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Đăng nhập hệ thống")
        
        # CHỈNH SỬA: Không cố định chiều cao (350) để cửa sổ tự nở theo font chữ
        # Chiều rộng giữ 420 để không bị hẹp ngang
        self.dialog.geometry("420x400") 
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title - Sử dụng font subtitle và giảm pady để cứu diện tích
        ttk.Label(main_frame, text="PHẦN MỀM KẾ TOÁN PRO", 
                  font=get_font("subtitle")).pack(pady=5)
        ttk.Label(main_frame, text="Đăng nhập để tiếp tục", 
                  font=get_font("label")).pack(pady=2)
        
        # Form nhập liệu - Giảm pady từ 20 xuống 10
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Tên đăng nhập:", font=get_font("label")).grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form_frame, width=22, font=get_font("label"))
        self.username_entry.grid(row=0, column=1, pady=5, padx=10)
        self.username_entry.focus()
        
        ttk.Label(form_frame, text="Mật khẩu:", font=get_font("label")).grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form_frame, width=22, show="*", font=get_font("label"))
        self.password_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        
        # Buttons - Giảm pady để kéo nút lên trên
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Đăng nhập", command=self.login, width=14).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Thoát", command=self.dialog.destroy, width=10).pack(side="left", padx=8)
        
        # Info - Gợi ý nhỏ phía dưới
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(pady=5)
        ttk.Label(info_frame, text="Mặc định: admin / admin123", 
                  font=get_font("status"), foreground="gray").pack()

        # Center window sau khi đã dàn trang xong
        self.dialog.update_idletasks()
        width = self.dialog.winfo_reqwidth()
        height = self.dialog.winfo_reqheight()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def login(self):
        """Xử lý đăng nhập"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
            return
        
        user = self.user_model.authenticate(username, password)
        
        if user:
            self.result = user
            self.dialog.destroy()
        else:
            messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def get_user(self):
        """Lấy thông tin người dùng đã đăng nhập"""
        self.dialog.wait_window()
        return self.result