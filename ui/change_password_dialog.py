import tkinter as tk
from tkinter import ttk, messagebox
from theme import get_font

class ChangePasswordDialog:
    def __init__(self, parent, user_model, current_user):
        self.parent = parent
        self.user_model = user_model
        self.current_user = current_user
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Đổi mật khẩu")
        self.dialog.geometry("400x300")
        self.dialog.grab_set()
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="ĐỔI MẬT KHẨU", font=get_font("title"), foreground="#2196F3").pack(pady=10)
        
        # Mật khẩu cũ
        frame1 = ttk.Frame(main_frame)
        frame1.pack(fill="x", pady=5)
        ttk.Label(frame1, text="Mật khẩu cũ:", width=15, font=get_font("label")).pack(side="left")
        self.old_pw = ttk.Entry(frame1, show="*", width=25, font=get_font("label"))
        self.old_pw.pack(side="left", padx=5)
        
        # Mật khẩu mới
        frame2 = ttk.Frame(main_frame)
        frame2.pack(fill="x", pady=5)
        ttk.Label(frame2, text="Mật khẩu mới:", width=15, font=get_font("label")).pack(side="left")
        self.new_pw = ttk.Entry(frame2, show="*", width=25, font=get_font("label"))
        self.new_pw.pack(side="left", padx=5)
        
        # Xác nhận mật khẩu mới
        frame3 = ttk.Frame(main_frame)
        frame3.pack(fill="x", pady=5)
        ttk.Label(frame3, text="Xác nhận mới:", width=15, font=get_font("label")).pack(side="left")
        self.confirm_pw = ttk.Entry(frame3, show="*", width=25, font=get_font("label"))
        self.confirm_pw.pack(side="left", padx=5)
        
        # Nút bấm
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Cập nhật", command=self.change_password, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Hủy", command=self.dialog.destroy, width=10).pack(side="left", padx=10)
    
    def change_password(self):
        old = self.old_pw.get().strip()
        new = self.new_pw.get().strip()
        confirm = self.confirm_pw.get().strip()
        
        if not old or not new:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ mật khẩu")
            return
        if new != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu mới và xác nhận không khớp")
            return
        if len(new) < 4:
            messagebox.showerror("Lỗi", "Mật khẩu mới phải có ít nhất 4 ký tự")
            return
        
        # Gọi model để đổi mật khẩu
        from models.user_model import UserModel
        username = self.current_user['username']
        success, msg = self.user_model.change_password(username, old, new)
        if success:
            messagebox.showinfo("Thành công", "Đổi mật khẩu thành công! Vui lòng đăng nhập lại.")
            self.dialog.destroy()
            # Yêu cầu đăng nhập lại
            self.parent.after(500, self.parent.show_login_dialog)
        else:
            messagebox.showerror("Lỗi", msg)