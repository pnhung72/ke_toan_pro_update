import tkinter as tk
from tkinter import ttk, messagebox
from services.email_service import EmailService

class EmailConnectionTab(ttk.Frame):
    """
    TAB 1: CẤU HÌNH KẾT NỐI EMAIL (LẤY HÓA ĐƠN)
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.service = EmailService()
        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        top_frame = tk.LabelFrame(self, text=" Cấu hình Email Kết nối ", padx=10, pady=10)
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(top_frame, text="Email:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_email = tk.Entry(top_frame, width=30)
        self.entry_email.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(top_frame, text="Mật khẩu ứng dụng:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.entry_password = tk.Entry(top_frame, width=20, show="*")
        self.entry_password.grid(row=0, column=3, padx=5, pady=5)

        btn_add = tk.Button(top_frame, text="Thêm kết nối", command=self.on_click_add_connection, bg="#e1e1e1")
        btn_add.grid(row=0, column=4, padx=10, pady=5)

        action_frame = tk.Frame(self)
        action_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(action_frame, text="📝 Chỉnh sửa", command=self.on_edit_email).pack(side="left", padx=5)
        tk.Button(action_frame, text="🗑️ Xóa Email", command=self.on_delete_email).pack(side="left", padx=5)
        tk.Button(action_frame, text="🔍 Tìm Hóa Đơn", command=self.on_scan_invoices, bg="#d1e7dd").pack(side="left", padx=5)
        
        self.tree_email = ttk.Treeview(self, columns=("ID", "Email", "Ngày tạo"), show='headings')
        self.tree_email.heading("ID", text="ID"); self.tree_email.heading("Email", text="Email Kết Nối"); self.tree_email.heading("Ngày tạo", text="Ngày Cấu Hình")
        self.tree_email.column("ID", width=50, anchor="center"); self.tree_email.column("Email", width=400); self.tree_email.column("Ngày tạo", width=200, anchor="center")
        self.tree_email.pack(fill="both", expand=True, padx=10, pady=5)

    def load_data(self):
        for item in self.tree_email.get_children(): self.tree_email.delete(item)
        configs = self.service.get_all_configs() 
        if configs:
            for row in configs: self.tree_email.insert("", "end", values=(row['id'], row['email'], row['created_at']))

    def on_click_add_connection(self):
        email, pwd = self.entry_email.get().strip(), self.entry_password.get().strip()
        if not email or not pwd:
            messagebox.showwarning("Thông báo", "Vui lòng nhập đầy đủ!")
            return
        success, msg = self.service.verify_and_save(email, pwd)
        if success:
            messagebox.showinfo("Kế Toán Pro", msg)
            self.load_data()
        else:
            messagebox.showerror("Lỗi", msg)

    def on_edit_email(self): pass
    def on_delete_email(self): pass
    def on_scan_invoices(self): messagebox.showinfo("Kế Toán Pro", "Đang quét hóa đơn...")


class CustomerRequestTab(ttk.Frame):
    """
    TAB 2: PHIÊN BẢN TỐI ƯU THẨM MĨ - TIẾP NHẬN YÊU CẦU PHẢN HỒI GỬI ADMIN
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()

    def _setup_ui(self):
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = tk.LabelFrame(self, text=" ✉️ HỆ THỐNG TIẾP NHẬN PHẢN HỒI & ĐỀ XUẤT NÂNG CẤP ", font=("Arial", 11, "bold"), fg="#0d6efd", padx=25, pady=25)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.columnconfigure(1, weight=1)

        # Loại yêu cầu
        tk.Label(main_frame, text="Phân loại yêu cầu:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=15, pady=12, sticky="w")
        self.combo_type = ttk.Combobox(main_frame, values=["⚠️ Báo lỗi", "💡 Đề xuất", "🔒 Bảo mật", "🎨 Giao diện"], width=40, state="readonly")
        self.combo_type.current(0); self.combo_type.grid(row=0, column=1, pady=12, sticky="we")

        # Tiêu đề
        tk.Label(main_frame, text="Tiêu đề phản hồi:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=15, pady=12, sticky="w")
        self.entry_subject = tk.Entry(main_frame, font=("Arial", 10)); self.entry_subject.grid(row=1, column=1, pady=12, sticky="we")

        # Nội dung
        tk.Label(main_frame, text="Nội dung chi tiết:", font=("Arial", 10, "bold")).grid(row=2, column=0, padx=15, pady=12, sticky="nw")
        text_frame = tk.Frame(main_frame); text_frame.grid(row=2, column=1, pady=12, sticky="nsew")
        self.txt_content = tk.Text(text_frame, height=5, font=("Arial", 10)); self.txt_content.pack(side="left", fill="both", expand=True)

        # Nút gửi
        self.btn_send = tk.Button(main_frame, text="🚀 Gửi Yêu Cầu Đến Tác Giả ", command=self.on_submit_feedback, bg="#0d6efd", fg="white", cursor="hand2")
        self.btn_send.grid(row=3, column=1, pady=10, sticky="e")

    def on_submit_feedback(self):
        if not self.entry_subject.get().strip() or not self.txt_content.get("1.0", tk.END).strip():
            messagebox.showwarning("Thông báo", "Vui lòng nhập đủ thông tin!")
            return
        messagebox.showinfo("Kế Toán Pro", "Đã gửi thành công!")
        self.entry_subject.delete(0, tk.END); self.txt_content.delete("1.0", tk.END)