# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from theme import get_font
from services.bank_engine.factory import BankEngineFactory
from core.database.repository import BankRepository

class BankConnectTab(tk.Frame):
    def __init__(self, parent, db_path):
        super().__init__(parent, bg="#f8f9fa")
        self.db_path = db_path
        self.temp_data = [] # Nơi chứa dữ liệu tạm từ Excel
        
        # Thiết lập Font từ hệ thống của Thầy
        self.h_font = get_font('header')
        self.n_font = get_font('normal')
        
        self.setup_ui()

    def setup_ui(self):
        # 1. Tiêu đề
        lbl_title = tk.Label(self, text="🏦 KẾT NỐI NGÂN HÀNG TỰ ĐỘNG", 
                             font=self.h_font, bg="#f8f9fa", fg="#2c3e50")
        lbl_title.pack(pady=15)

        # 2. Khung cấu hình
        frame_top = tk.LabelFrame(self, text=" Cấu hình nạp sao kê ", font=get_font('small'), bg="#f8f9fa")
        frame_top.pack(padx=20, fill="x", pady=5)

        tk.Label(frame_top, text="Chọn Ngân hàng:", font=self.n_font, bg="#f8f9fa").grid(row=0, column=0, padx=10, pady=10)
        self.cb_bank = ttk.Combobox(frame_top, values=("ACB", "VCB", "AGRI"), state="readonly", font=self.n_font)
        self.cb_bank.set("ACB")
        self.cb_bank.grid(row=0, column=1, padx=10)

        btn_browse = tk.Button(frame_top, text="📁 Chọn file Excel", font=self.n_font, 
                               bg="#3498db", fg="white", command=self.load_file)
        btn_browse.grid(row=0, column=2, padx=10)

        # 3. Bảng xem trước dữ liệu
        frame_table = tk.Frame(self)
        frame_table.pack(padx=20, fill="both", expand=True, pady=10)

        columns = ("date", "ref", "in", "out", "desc")
        self.tree = ttk.Treeview(frame_table, columns=columns, show='headings')
        
        headings = {"date": "Ngày GD", "ref": "Số chứng từ", "in": "Tiền vào", "out": "Tiền ra", "desc": "Nội dung"}
        for col, text in headings.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120 if col != "desc" else 300)
        
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 4. Nút xác nhận
        self.btn_import = tk.Button(self, text="🚀 XÁC NHẬN NẠP VÀO SỔ CÁI", font=self.n_font, 
                                    bg="#27ae60", fg="white", state="disabled",
                                    command=self.execute_import, padx=20, pady=10)
        self.btn_import.pack(pady=15)

    def load_file(self):
        bank_code = self.cb_bank.get()
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        
        if file_path:
            try:
                parser = BankEngineFactory.get_parser(bank_code)
                self.temp_data = parser.parse(file_path)
                
                # Xóa dữ liệu cũ trên bảng
                for item in self.tree.get_children(): self.tree.delete(item)
                
                # Nạp dữ liệu mới
                for r in self.temp_data:
                    self.tree.insert("", "end", values=(r['trans_date'], r['reference'], 
                                     f"{r['amount_in']:,.0f}", f"{r['amount_out']:,.0f}", r['description']))
                
                self.btn_import.config(state="normal", bg="#27ae60")
                messagebox.showinfo("Thông báo", f"Đã đọc được {len(self.temp_data)} giao dịch.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi xử lý file: {e}")

    def execute_import(self):
        if not self.temp_data: return
        try:
            conn = sqlite3.connect(self.db_path)
            try:
                repo = BankRepository(conn)
                res = repo.import_bank_transactions(self.temp_data)
            finally:
                conn.close()
            
            if res["success"]:
                messagebox.showinfo("Thành công", f"Đã nạp {res['count']} giao dịch mới vào Database!")
                self.btn_import.config(state="disabled", bg="#bdc3c7")
                self.temp_data = []
            else:
                messagebox.showerror("Lỗi", res["message"])
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e))