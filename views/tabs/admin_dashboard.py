# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab
from theme import get_font
from core.mail_detector import AdminMailScanner

class AdminDashboardTab(BaseTab):
    """Tab Trung Tâm Điều Hành Admin - Kế thừa từ BaseTab"""
    
    def __init__(self, parent, notebook, *args, **kwargs):
        super().__init__(parent, notebook)
        
        # Khởi tạo bộ quét mail
        self.scanner = AdminMailScanner(
            email_user="thayhung.ketoanpro@gmail.com", 
            email_pass="your_app_password_here" 
        )
        
        # Kích hoạt quét tự động
        self.scanner.start_scanning()
        self.listen_to_queue()

    def setup_ui(self):
        """Thiết lập giao diện - Dùng 'self' làm cha trực tiếp"""
        # Tiêu đề bảng điều khiển
        title_lbl = ttk.Label(self, text="🔔 DANH SÁCH YÊU CẦU KHÁCH HÀNG CHỜ XỬ LÝ", 
                              font=get_font("title"))
        title_lbl.pack(pady=15)

        # Khung chứa Bảng dữ liệu Grid
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill="both", expand=True)

        # Cấu hình các cột
        columns = ("customer", "phone", "content", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        
        self.tree.heading("customer", text="Tên Khách Hàng / Doanh Nghiệp")
        self.tree.heading("phone", text="Số Điện Thoại")
        self.tree.heading("content", text="Nội Dung Gửi Yêu Cầu")
        self.tree.heading("status", text="Trạng Thái Hệ Thống")

        self.tree.column("customer", width=200, anchor="w")
        self.tree.column("phone", width=120, anchor="center")
        self.tree.column("content", width=400, anchor="w")
        self.tree.column("status", width=120, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)

        # Thanh cuộn
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Khung điều hướng
        action_frame = ttk.Frame(self, padding=15)
        action_frame.pack()

        btn_refresh = ttk.Button(action_frame, text="🔄 Kiểm tra hòm thư ngay", command=self.refresh_mails)
        btn_refresh.pack(side="left", padx=10)

        btn_reply = ttk.Button(action_frame, text="✉️ Xem chi tiết & Phản hồi nhanh", command=self.quick_reply)
        btn_reply.pack(side="left", padx=10)

    def bind_events(self):
        """Thiết lập sự kiện nếu cần"""
        pass

    def load_data(self):
        """Tải dữ liệu ban đầu"""
        pass

    def listen_to_queue(self):
        """Bốc dỡ dữ liệu từ luồng chạy ngầm đẩy lên UI real-time"""
        while not self.scanner.update_queue.empty():
            try:
                data = self.scanner.update_queue.get_nowait()
                self.tree.insert("", 0, values=(data["customer"], data["phone"], data["content"], data["status"]))
            except:
                pass
        self.after(1000, self.listen_to_queue)

    def refresh_mails(self):
        if self.scanner.is_running:
            messagebox.showinfo("Thông báo", "Hệ thống đang quét ngầm dữ liệu, Thầy vui lòng đợi chút nhé!")
        else:
            self.scanner.start_scanning()
            messagebox.showinfo("Thành công", "Đang kết nối cổng IMAP quét các yêu cầu chưa xử lý...")

    def quick_reply(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Thầy chưa chọn yêu cầu của khách hàng nào để xử lý ạ!")
            return
            
        item_values = self.tree.item(selected_item, "values")
        customer_name = item_values[0]
        
        self.tree.item(selected_item, values=(item_values[0], item_values[1], item_values[2], "🟢 Đã xử lý"))
        messagebox.showinfo("Phản hồi nhanh", f"Đã mở kết nối gửi Mail Template phản hồi tự động tới: {customer_name}")