# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import imaplib
import email
from email.header import decode_header
import os

class AdminFeedbackTab(ttk.Frame):
    def __init__(self, parent, controller, is_admin=False):
        super().__init__(parent)
        self.controller = controller
        self.is_admin = is_admin
        
        # Log để kiểm tra trong Console
        print(f"[DEBUG] Khởi tạo AdminFeedbackTab. Quyền Admin: {self.is_admin}")
        
        self._setup_ui()
        
        # Chỉ quét email nếu là Admin
        if self.is_admin:
            self.fetch_emails()

    def _setup_ui(self):
        if self.is_admin:
            # GIAO DIỆN ADMIN: Hiển thị bảng phản hồi
            label = tk.Label(self, text="📥 DANH SÁCH PHẢN HỒI (ADMIN)", font=("Arial", 12, "bold"))
            label.pack(pady=10)
            
            self.tree = ttk.Treeview(self, columns=("sender", "subject", "date"), show='headings')
            self.tree.heading("sender", text="Người gửi")
            self.tree.heading("subject", text="Tiêu đề")
            self.tree.heading("date", text="Ngày gửi")
            self.tree.column("sender", width=200)
            self.tree.column("subject", width=300)
            self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        else:
            # GIAO DIỆN KHÁCH: Form gửi ý kiến
            label = tk.Label(self, text="📝 GỬI YÊU CẦU HỖ TRỢ KỸ THUẬT", font=("Arial", 12, "bold"))
            label.pack(pady=10)
            
            tk.Label(self, text="Tiêu đề yêu cầu:").pack(anchor="w", padx=10)
            self.subject_entry = tk.Entry(self)
            self.subject_entry.pack(fill="x", padx=10, pady=5)
            
            tk.Label(self, text="Nội dung cần hỗ trợ:").pack(anchor="w", padx=10)
            self.content_text = tk.Text(self, height=10)
            self.content_text.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Dòng chú thích minh bạch cho khách hàng
            tk.Label(self, text="*Yêu cầu sẽ được gửi đến bộ phận kỹ thuật (pnhungc3nvt@gmail.com)", 
                     fg="blue", font=("Arial", 8, "italic")).pack(anchor="w", padx=10)
            
            self.btn_send = ttk.Button(self, text="Gửi yêu cầu", command=self.submit_feedback)
            self.btn_send.pack(pady=10)

    def fetch_emails(self):
        """Logic quét hòm thư phản hồi với xử lý Font an toàn"""
        email_user = "pnhungc3nvt@gmail.com"
        email_pass = os.getenv("EMAIL_APP_PASSWORD", "mật_khẩu_ứng_dụng_của_thầy")

        try:
            print("[DEBUG] Đang kết nối IMAP...")
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            # Ép kiểu mật khẩu về dạng bytes chuẩn để thư viện IMAP không bị lỗi font
            mail.login(email_user, str(email_pass).encode('ascii', 'ignore').decode('ascii'))
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")
            mail_ids = messages[0].split()

            if hasattr(self, 'tree'):
                for item in self.tree.get_children():
                    self.tree.delete(item)

                # Duyệt 20 email gần nhất
                for i in mail_ids[-20:]:
                    res, msg_data = mail.fetch(i, "(RFC822)")
                    for response in msg_data:
                        if isinstance(response, tuple):
                            msg = email.message_from_bytes(response[1])
                            
                            # --- XỬ LÝ TIÊU ĐỀ AN TOÀN (KHÔNG BỊ LỖI ASCII) ---
                            raw_subject = msg.get("Subject", "")
                            subject = ""
                            if raw_subject:
                                decoded_parts = decode_header(raw_subject)
                                for part, encoding in decoded_parts:
                                    if isinstance(part, bytes):
                                        # Ép về utf-8, nếu lỗi thì thay bằng '?'
                                        subject += part.decode(encoding or 'utf-8', errors='replace')
                                    else:
                                        subject += part
                            else:
                                subject = "(Không tiêu đề)"
                            
                            self.tree.insert("", "end", values=(msg.get("From"), subject, msg.get("Date")))
            
            mail.logout()
            print("[DEBUG] Quét email thành công.")
        except Exception as e:
            print(f"[DEBUG] LỖI FETCH EMAIL: {e}")

    def submit_feedback(self):
        """Gửi phản hồi của khách hàng về Admin bằng chính cấu hình email của họ"""
        subject = self.subject_entry.get().strip()
        body = self.content_text.get("1.0", tk.END).strip()

        if not subject or not body:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ tiêu đề và nội dung!")
            return

        # 1. Lấy cấu hình email khách đang dùng từ DB thông qua email_service
        configs = self.email_service.get_all_configs()
        if not configs:
            messagebox.showerror("Lỗi", "Chưa cấu hình email nguồn. Vui lòng kiểm tra lại cấu hình!")
            return

        # Sử dụng email và mật khẩu khách đã cấu hình để gửi đi
        sender_email = configs[0]['email']
        sender_pass = configs[0]['app_password']
        
        # 2. Gọi hàm gửi phản hồi từ EmailService (đã được bảo toàn tính năng)
        success = self.email_service.send_feedback_to_admin(subject, body, sender_email, sender_pass)
        
        if success:
            messagebox.showinfo("Thông báo", "Đã gửi ý kiến đến Admin thành công!")
            # Xóa form sau khi gửi
            self.subject_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)
        else:
            messagebox.showerror("Lỗi", "Không thể gửi phản hồi. Vui lòng kiểm tra lại mật khẩu ứng dụng của email cấu hình.")