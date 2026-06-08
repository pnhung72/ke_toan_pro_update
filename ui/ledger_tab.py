import tkinter as tk
from tkinter import ttk, messagebox
from models.database import Database
from services.transaction_service import TransactionService
from services.invoice_service import InvoiceService
from datetime import datetime
from utils.license import is_full_version
from theme import get_font

class LedgerTab:
    def __init__(self, parent, notebook):
        self.parent = parent
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Sổ cái")
        self.create_widgets()
        self.load_accounts()
        self.load_ledger()
    
    def create_widgets(self):
        # === STYLE CHO FONT LỚN (Giữ nguyên các thiết lập tốt của Thầy) ===
        style = ttk.Style()
        style.configure("Ledger.TLabelframe.Label", font=get_font("bold"))
        style.configure("Ledger.TButton", font=get_font("label"), padding=8)
        style.configure("Ledger.TLabel", font=get_font("label"))
        style.configure("Ledger.Treeview", font=get_font("small"), rowheight=28)
        style.configure("Ledger.Treeview.Heading", font=get_font("bold"))
        style.configure("Ledger.TCombobox", font=get_font("label"))
        
        # === KHUNG BỘ LỌC (Nâng cấp thêm chọn ngày) ===
        filter_frame = ttk.LabelFrame(self.frame, text="Bộ lọc dữ liệu", style="Ledger.TLabelframe")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Dòng 1: Chọn tài khoản và thời gian
        row1_frame = ttk.Frame(filter_frame)
        row1_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(row1_frame, text="Tài khoản:").pack(side="left", padx=5)
        self.account_combo = ttk.Combobox(row1_frame, width=35, style="Ledger.TCombobox")
        self.account_combo.pack(side="left", padx=5)
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self.load_ledger())

        ttk.Label(row1_frame, text="Từ ngày:").pack(side="left", padx=(20, 5))
        self.start_date_entry = ttk.Entry(row1_frame, width=12, font=get_font("label"))
        self.start_date_entry.insert(0, f"01/{datetime.now().strftime('%m/%Y')}") # Mặc định đầu tháng
        self.start_date_entry.pack(side="left", padx=5)

        ttk.Label(row1_frame, text="Đến ngày:").pack(side="left", padx=(10, 5))
        self.end_date_entry = ttk.Entry(row1_frame, width=12, font=get_font("label"))
        self.end_date_entry.insert(0, datetime.now().strftime("%d/%m/%Y")) # Mặc định ngày hiện tại
        self.end_date_entry.pack(side="left", padx=5)
        
        # Dòng 2: Nút chức năng
        row2_frame = ttk.Frame(filter_frame)
        row2_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(row2_frame, text="🔄 Truy vấn", command=self.load_ledger,
                   style="Ledger.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="📥 Xuất Excel", command=self.export_excel,
                   style="Ledger.TButton", width=12).pack(side="left", padx=5)
        
        # === KHUNG HIỂN THỊ SỔ CÁI (Nâng cấp 8 cột chuẩn) ===
        ledger_frame = ttk.LabelFrame(self.frame, text="SỔ CÁI CHI TIẾT", style="Ledger.TLabelframe")
        ledger_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 1. Định nghĩa 8 cột chuẩn kế toán
        columns = ("post_date", "vouch_no", "vouch_date", "desc", "opp_acc", "debit", "credit", "balance")
        self.tree = ttk.Treeview(ledger_frame, columns=columns, show="headings", 
                                  height=15, style="Ledger.Treeview")
        
        # 2. Tiêu đề hiển thị (Tiếng Việt chuẩn)
        headings = {
            "post_date": "Ngày ghi sổ",
            "vouch_no": "Số hiệu CT",
            "vouch_date": "Ngày CT",
            "desc": "Diễn giải",
            "opp_acc": "TK Đối ứng",
            "debit": "Nợ",
            "credit": "Có",
            "balance": "Số dư"
        }
        
        # 3. Cấu hình độ rộng và căn lề từng cột
        col_configs = {
            "post_date": (100, "center"),
            "vouch_no": (100, "center"),
            "vouch_date": (100, "center"),
            "desc": (350, "w"),
            "opp_acc": (100, "center"),
            "debit": (130, "e"),
            "credit": (130, "e"),
            "balance": (150, "e")
        }
        
        for col in columns:
            self.tree.heading(col, text=headings[col])
            width, anchor = col_configs[col]
            self.tree.column(col, width=width, anchor=anchor)
        
        # Thanh cuộn (Giữ nguyên logic Grid của Thầy)
        vsb = ttk.Scrollbar(ledger_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(ledger_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        ledger_frame.columnconfigure(0, weight=1)
        ledger_frame.rowconfigure(0, weight=1)
        
        # === KHUNG TỔNG HỢP (Giữ nguyên logic của Thầy) ===
        summary_frame = ttk.LabelFrame(self.frame, text="Tổng hợp kỳ hạch toán", style="Ledger.TLabelframe")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        summary_inner = ttk.Frame(summary_frame)
        summary_inner.pack(fill="x", padx=10, pady=8)
        
        self.total_debit_label = ttk.Label(summary_inner, text="Tổng Nợ: 0", 
                                           font=get_font("bold"), foreground="#2196F3")
        self.total_debit_label.pack(side="left", padx=20)
        
        self.total_credit_label = ttk.Label(summary_inner, text="Tổng Có: 0", 
                                            font=get_font("bold"), foreground="#F44336")
        self.total_credit_label.pack(side="left", padx=20)
        
        self.balance_label = ttk.Label(summary_inner, text="Số dư cuối: 0", 
                                       font=get_font("bold"), foreground="#4CAF50")
        self.balance_label.pack(side="left", padx=20)
    
    def load_accounts(self):
        """Tải danh sách tài khoản từ database"""
        accounts = []
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT account_code, account_name 
                    FROM accounts 
                    ORDER BY account_code
                """)
                rows = cursor.fetchall()
                for row in rows:
                    accounts.append(f"{row['account_code']} - {row['account_name']}")
        except Exception as e:
            # Nếu chưa có bảng accounts, tạo dữ liệu mặc định
            accounts = [
                "111 - Tiền mặt",
                "112 - Tiền gửi ngân hàng",
                "131 - Phải thu khách hàng",
                "156 - Hàng hóa",
                "331 - Phải trả nhà cung cấp",
                "511 - Doanh thu bán hàng",
                "632 - Giá vốn hàng bán",
                "641 - Chi phí bán hàng",
                "642 - Chi phí quản lý",
                "911 - Xác định kết quả kinh doanh"
            ]
        
        self.account_combo['values'] = accounts
        if accounts:
            self.account_combo.current(0)
    
    def load_ledger(self):
        """Tải dữ liệu sổ cái: Đã sửa lỗi UnboundLocalError và chuẩn hóa 8 cột"""
        # 1. Dọn dẹp bảng cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        selected = self.account_combo.get()
        if not selected:
            return
            
        # Lấy mã tài khoản
        account_code = selected.split(" - ")[0].strip()
        is_asset = account_code.startswith(('1', '2'))
        is_expense = account_code.startswith(('6', '7', '8'))

        # --- ĐƯA HÀM NÀY LÊN ĐẦU ĐỂ TRÁNH LỖI UnboundLocalError ---
        def parse_date(d_str):
            try:
                if not d_str: return datetime.min
                clean_date = d_str.split(' ')[0] if ' ' in d_str else d_str
                return datetime.strptime(clean_date, "%d/%m/%Y")
            except Exception:
                return datetime.min
        
        # 2. LẤY KHOẢNG NGÀY TỪ GIAO DIỆN
        try:
            start_date = datetime.strptime(self.start_date_entry.get(), "%d/%m/%Y")
            end_date = datetime.strptime(self.end_date_entry.get(), "%d/%m/%Y")
        except Exception:
            messagebox.showerror("Lỗi", "Định dạng ngày không đúng (DD/MM/YYYY)")
            return
            
        # 3. Thu thập dữ liệu
        transactions = TransactionService.get_all_transactions()
        invoices = InvoiceService.get_all_invoices()
        all_entries = []
        
        # --- LỌC VÀ XỬ LÝ GIAO DỊCH (TRANSACTION) ---
        for t in transactions:
            try:
                date_str = t.get('date', '')
                curr_date = parse_date(date_str)
                # BỘ LỌC CẢI TIẾN
                if not (start_date <= curr_date <= end_date): 
                    continue
                
                amount = t.get('amount', 0)
                trans_type = t.get('type', '')
                
                if account_code == '111':
                    debit = amount if trans_type == 'Thu' else 0
                    credit = amount if trans_type != 'Thu' else 0
                    opposite_account = '511' if trans_type == 'Thu' else '642'
                elif account_code == '511':
                    debit = amount if trans_type != 'Thu' else 0
                    credit = amount if trans_type == 'Thu' else 0
                    opposite_account = '111'
                else:
                    debit = amount if trans_type == 'Thu' else 0
                    credit = amount if trans_type != 'Thu' else 0
                    opposite_account = '511' if trans_type == 'Thu' else '642'
                
                all_entries.append({
                    'date': date_str,
                    'vouch_no': 'PK',
                    'vouch_date': date_str,
                    'description': f"{t.get('description', '')} ({t.get('category', '')})" if t.get('category') else t.get('description', ''),
                    'opposite_account': opposite_account,
                    'debit': debit,
                    'credit': credit,
                    'id': t.get('id', 0)
                })
            except Exception: continue

        # --- LỌC VÀ XỬ LÝ HÓA ĐƠN (INVOICE) ---
        for inv in invoices:
            try:
                date_str = inv.get('created_date', '')
                curr_date = parse_date(date_str)
                if not (start_date <= curr_date <= end_date): 
                    continue
                if account_code not in ['111', '511']: 
                    continue
                
                amount = inv.get('total_payment', 0)
                inv_no = inv.get('invoice_number', '')
                
                if account_code == '111':
                    debit, credit, opposite_account = amount, 0, '511'
                else: 
                    debit, credit, opposite_account = 0, amount, '111'
                    
                all_entries.append({
                    'date': date_str,
                    'vouch_no': f"HĐ{inv_no}",
                    'vouch_date': date_str,
                    'description': f"Bán hàng: {inv.get('buyer_name', '')}",
                    'opposite_account': opposite_account,
                    'debit': debit,
                    'credit': credit,
                    'id': inv.get('id', 0)
                })
            except Exception: continue

        # SẮP XẾP THEO NGÀY
        all_entries.sort(key=lambda x: (parse_date(x['date']), x.get('id', 0)))

        # 4. LẤY SỐ DƯ ĐẦU KỲ
        opening_balance = 0
        try:
            with Database.get_connection() as conn:
                import sqlite3
                conn.row_factory = sqlite3.Row 
                cursor = conn.cursor()
                current_year = datetime.now().strftime("%Y")
                cursor.execute("SELECT opening_balance FROM account_balances WHERE account_code = ? AND period = ?", (account_code, current_year))
                row = cursor.fetchone()
                if row: opening_balance = row['opening_balance']
        except Exception: opening_balance = 0

        # Hiển thị hàng SỐ DƯ ĐẦU KỲ
        self.tree.insert("", "end", values=("---", "---", "---", "SỐ DƯ ĐẦU KỲ", "---", "", "", self.format_money(opening_balance)), tags=("blue",))

        # 5. TÍNH TOÁN LŨY KẾ VÀ ĐỔ DỮ LIỆU (CHỈ DÙNG 1 VÒNG LẶP DUY NHẤT)
        running_balance = opening_balance
        total_debit = 0
        total_credit = 0
        
        for entry in all_entries:
            if is_asset or is_expense:
                running_balance += entry['debit'] - entry['credit']
            else:
                running_balance += entry['credit'] - entry['debit']
            
            total_debit += entry['debit']
            total_credit += entry['credit']
            
            tag = "green" if running_balance >= 0 else "red"
            self.tree.insert("", "end", values=(
                entry['date'],
                entry['vouch_no'],
                entry['vouch_date'],
                entry['description'],
                entry['opposite_account'],
                self.format_money(entry['debit']) if entry['debit'] > 0 else "",
                self.format_money(entry['credit']) if entry['credit'] > 0 else "",
                self.format_money(running_balance)
            ), tags=(tag,))

        # 6. CẬP NHẬT NHÃN TỔNG HỢP
        self.total_debit_label.config(text=f"💰 Tổng Nợ: {self.format_money(total_debit)}")
        self.total_credit_label.config(text=f"💸 Tổng Có: {self.format_money(total_credit)}")
        balance_color = "#4CAF50" if running_balance >= 0 else "#F44336"
        self.balance_label.config(text=f"📊 Số dư cuối: {self.format_money(running_balance)}", foreground=balance_color)
        
        self.tree.tag_configure("green", foreground="#4CAF50")
        self.tree.tag_configure("red", foreground="#F44336")
        self.tree.tag_configure("blue", foreground="#2196F3", font=get_font("bold"))
    
    def format_money(self, amount):
        """Định dạng số tiền"""
        if amount == 0:
            return "0"
        return f"{amount:,.0f}".replace(",", ".")
    
    def export_excel(self):
        """Xuất sổ cái ra Excel"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        
        from utils.excel_export import export_to_excel
        import os
        from tkinter import filedialog
        
        selected = self.account_combo.get()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản")
            return
        
        # Lấy dữ liệu từ Treeview
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            data.append(values)
        
        if not data:
            messagebox.showinfo("Thông báo", "Không có dữ liệu để xuất")
            return
        
        columns = [
            "Ngày ghi sổ", "Số hiệu CT", "Ngày CT", "Diễn giải", 
            "TK đối ứng", "Nợ", "Có", "Số dư"
        ]
        file_name = f"So_cai_{selected.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=file_name
        )
        
        if file_path:
            export_to_excel(data, columns, file_name, file_path)
            messagebox.showinfo("Thành công", f"Đã xuất sổ cái:\n{file_path}")