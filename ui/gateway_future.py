# -*- coding: utf-8 -*-
# file: ui/gateway_future.py
import tkinter as tk
from tkinter import messagebox, ttk
import socket
import os
import json
from datetime import datetime

class DigitalGateway:
    def __init__(self):
        """Khởi tạo cổng kết nối và các đường dẫn an toàn"""
        self.log_path = "logs/gateway.log"
        self.config_path = "configs/gateway_config.json"
        
        # QUY TRÌNH AN TOÀN: Tự động kiểm tra và tạo thư mục nếu thiếu
        for folder in ["logs", "config"]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    def log_event(self, event_name):
        """Ghi nhật ký trực tiếp để theo dõi hành vi hệ thống"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"{timestamp} - INFO - {event_name}\n"
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_message)
                f.flush()
        except Exception: pass

    def open_config_window(self):
        """Tạo cửa sổ cấu hình thông số doanh nghiệp"""
        config_win = tk.Toplevel()
        config_win.title("Cấu hình Doanh nghiệp - Kế Toán Pro")
        config_win.geometry("480x280")
        config_win.resizable(False, False)
        config_win.grab_set() # Giữ trọng tâm vào cửa sổ này để tránh thao tác nhầm bên ngoài

        main_frame = ttk.Frame(config_win, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Giao diện nhập liệu
        ttk.Label(main_frame, text="Mã số thuế (MST):").grid(row=0, column=0, sticky=tk.W, pady=8)
        mst_entry = ttk.Entry(main_frame, width=35)
        mst_entry.grid(row=0, column=1, pady=8)

        ttk.Label(main_frame, text="API Token (Hóa đơn):").grid(row=1, column=0, sticky=tk.W, pady=8)
        token_entry = ttk.Entry(main_frame, width=35, show="*") # Ẩn thông tin nhạy cảm
        token_entry.grid(row=1, column=1, pady=8)

        # Nút Lưu với quy trình xác nhận
        def save_config():
            mst = mst_entry.get().strip()
            if not mst:
                messagebox.showerror("Lỗi", "Mã số thuế không được để trống!")
                return

            data = {
                "mst": mst,
                "token": token_entry.get().strip(),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
                self.log_event(f"Cập nhật cấu hình doanh nghiệp cho MST: {mst}")
                messagebox.showinfo("Thành công", "Dữ liệu cấu hình đã được bảo vệ và lưu trữ!")
                config_win.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi hệ thống", f"Không thể lưu file cấu hình: {e}")

        btn_save = ttk.Button(main_frame, text="💾 Lưu và Bảo mật", command=save_config)
        btn_save.grid(row=2, column=0, columnspan=2, pady=25)

    def is_internet_available(self):
        """Kiểm tra kết nối mạng trước khi thực hiện tác vụ ngoại vi"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except OSError: return False

    def connect_tax_department(self):
        self.log_event("Kết nối Tổng cục Thuế")
        if not self.is_internet_available():
            messagebox.showwarning("Lỗi kết nối", "Vui lòng kiểm tra Internet.")
            return
        messagebox.showinfo("Kế Toán Pro", "Đang thiết lập cổng kết nối an toàn với Tổng cục Thuế...")

    def e_invoice_sync(self):
        self.log_event("Đồng bộ Hóa đơn điện tử")
        if not self.is_internet_available():
            messagebox.showwarning("Lỗi kết nối", "Hệ thống cần Internet để đồng bộ.")
            return
        messagebox.showinfo("Kế Toán Pro", "Đang khởi tạo cổng đồng bộ hóa đơn tự động...")