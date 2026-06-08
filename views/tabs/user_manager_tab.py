# -*- coding: utf-8 -*-
"""
UserManagerTab - Quan ly nguoi dung (chi admin)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab

class UserManagerTab(BaseTab):
    """Tab quan ly nguoi dung"""
    
    def __init__(self, parent, notebook, user_model, current_user):
        self.user_model = user_model
        self.current_user = current_user
        super().__init__(parent, notebook, None)
    
    def setup_ui(self):
        """Tao giao dien"""
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="Thêm người dùng", command=self.add_user).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Sửa", command=self.edit_user).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Xóa", command=self.delete_user).pack(side="left", padx=2)
        ttk.Button(toolbar, text="Làm mới", command=self.refresh).pack(side="left", padx=2)
        
        # Treeview
        columns = ("id", "username", "full_name", "email", "role", "status", "last_login")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="Tên đăng nhập")
        self.tree.heading("full_name", text="Họ tên")
        self.tree.heading("email", text="Email")
        self.tree.heading("role", text="Vai trò")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("last_login", text="Lần cuối")
        
        self.tree.column("id", width=50)
        self.tree.column("username", width=120)
        self.tree.column("full_name", width=150)
        self.tree.column("email", width=150)
        self.tree.column("role", width=100)
        self.tree.column("status", width=80)
        self.tree.column("last_login", width=150)
        
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def bind_events(self):
        pass
    
    def load_data(self):
        """Tai danh sach nguoi dung"""
        users = self.user_model.get_all_users()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for user in users:
            status = "Hoạt động" if user["is_active"] else "Khóa"
            self.tree.insert("", "end", values=(
                user["id"],
                user["username"],
                user["full_name"],
                user["email"],
                user["role"],
                status,
                user["last_login"]
            ))
        
        self.show_message(f"Đã tải {len(users)} người dùng")
    
    def add_user(self):
        """Them nguoi dung moi"""
        dialog = tk.Toplevel(self.frame)
        dialog.title("Thêm người dùng")
        dialog.geometry("400x400")
        dialog.grab_set()
        
        form = ttk.Frame(dialog, padding=20)
        form.pack(fill="both", expand=True)
        
        ttk.Label(form, text="Tên đăng nhập:").grid(row=0, column=0, sticky="w", pady=5)
        username_entry = ttk.Entry(form, width=30)
        username_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(form, text="Mật khẩu:").grid(row=1, column=0, sticky="w", pady=5)
        password_entry = ttk.Entry(form, width=30, show="*")
        password_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(form, text="Họ tên:").grid(row=2, column=0, sticky="w", pady=5)
        fullname_entry = ttk.Entry(form, width=30)
        fullname_entry.grid(row=2, column=1, pady=5)
        
        ttk.Label(form, text="Email:").grid(row=3, column=0, sticky="w", pady=5)
        email_entry = ttk.Entry(form, width=30)
        email_entry.grid(row=3, column=1, pady=5)
        
        ttk.Label(form, text="Vai trò:").grid(row=4, column=0, sticky="w", pady=5)
        role_combo = ttk.Combobox(form, values=["ke_toan", "thu_ngan", "viewer"], width=27)
        role_combo.grid(row=4, column=1, pady=5)
        role_combo.current(0)
        
        def save():
            result = self.user_model.add_user(
                username_entry.get(),
                password_entry.get(),
                fullname_entry.get(),
                email_entry.get(),
                role_combo.get()
            )
            
            if result["success"]:
                messagebox.showinfo("Thành công", result["message"])
                dialog.destroy()
                self.refresh()
            else:
                messagebox.showerror("Lỗi", result["message"])
        
        ttk.Button(form, text="Lưu", command=save).grid(row=5, column=0, columnspan=2, pady=20)
    
    def edit_user(self):
        """Sua nguoi dung"""
        selected = self.tree.selection()
        if not selected:
            self.show_message("Vui lòng chọn người dùng cần sửa", True)
            return
        
        item = self.tree.item(selected[0])
        user_id = item["values"][0]
        
        self.show_message(f"Đang phát triển - Sửa user ID: {user_id}")
    
    def delete_user(self):
        """Xoa nguoi dung"""
        selected = self.tree.selection()
        if not selected:
            self.show_message("Vui lòng chọn người dùng cần xóa", True)
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa người dùng này?"):
            self.show_message("Tính năng đang phát triển")
    
    def refresh(self):
        self.load_data()