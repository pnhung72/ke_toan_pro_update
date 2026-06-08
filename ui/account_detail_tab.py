import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models.journal_entry import JournalEntry
from models.account import Account
from utils.excel_export import export_to_excel

class AccountDetailTab:
    def __init__(self, parent, notebook):
        self.parent = parent
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Sổ chi tiết")
        self.create_widgets()
        self.load_accounts()
        self.load_detail()

    def create_widgets(self):
        # === Frame bộ lọc ===
        filter_frame = ttk.LabelFrame(self.frame, text="Bộ lọc")
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Dòng 0: Chọn tài khoản
        ttk.Label(filter_frame, text="Tài khoản:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.account_combo = ttk.Combobox(filter_frame, state="readonly", width=30)
        self.account_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self.load_detail())

        # Dòng 1: Từ ngày, đến ngày
        ttk.Label(filter_frame, text="Từ ngày:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.from_date = ttk.Entry(filter_frame, width=12)
        self.from_date.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.from_date.insert(0, "01/01/2025")

        ttk.Label(filter_frame, text="Đến ngày:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.to_date = ttk.Entry(filter_frame, width=12)
        self.to_date.grid(row=1, column=3, padx=5, pady=5, sticky="w")
        self.to_date.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Nút áp dụng
        ttk.Button(filter_frame, text="Áp dụng", command=self.load_detail).grid(row=1, column=4, padx=10, pady=5)

        # Nút làm mới (reset ngày về mặc định)
        ttk.Button(filter_frame, text="Làm mới", command=self.reset_filters).grid(row=1, column=5, padx=5, pady=5)

        # === Nút chức năng ===
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Xuất Excel", command=self.export_excel).pack(side="left", padx=5)

        # === Treeview hiển thị sổ chi tiết ===
        columns = ("Ngày", "Diễn giải", "TK đối ứng", "Nợ", "Có", "Số dư")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        vsb = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

    def load_accounts(self):
        accounts = Account.load_accounts()
        self.account_combo['values'] = [f"{acc['Ma TK']} - {acc['Ten TK']}" for acc in accounts]
        if self.account_combo['values']:
            self.account_combo.current(0)

    def reset_filters(self):
        self.from_date.delete(0, tk.END)
        self.from_date.insert(0, "01/01/2025")
        self.to_date.delete(0, tk.END)
        self.to_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.load_detail()

    def load_detail(self):
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected = self.account_combo.get()
        if not selected:
            return
        account_code = selected.split(" - ")[0]

        from_date = self.from_date.get().strip()
        to_date = self.to_date.get().strip()

        # Kiểm tra định dạng ngày
        try:
            datetime.strptime(from_date, "%d/%m/%Y")
            datetime.strptime(to_date, "%d/%m/%Y")
        except Exception:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ (dd/mm/yyyy)")
            return

        # Lấy bút toán trong khoảng thời gian
        entries = JournalEntry.get_by_account_period(account_code, from_date, to_date)
        # Tính số dư đầu kỳ
        opening_balance = JournalEntry.get_balance_up_to(account_code, from_date)

        balance = opening_balance
        # Nếu có số dư đầu kỳ, hiển thị dòng đầu
        if opening_balance != 0:
            self.tree.insert("", 0, values=(
                f"(Đầu kỳ đến {from_date})",
                "Số dư đầu kỳ",
                "",
                f"{opening_balance:,.0f}".replace(",", ".") if opening_balance > 0 else "",
                f"{-opening_balance:,.0f}".replace(",", ".") if opening_balance < 0 else "",
                f"{opening_balance:,.0f}".replace(",", ".")
            ), tags=("opening",))
            self.tree.tag_configure("opening", background="#e8f0fe")

        # Duyệt từng bút toán
        for e in entries:
            debit = e['debit']
            credit = e['credit']
            balance += debit - credit
            self.tree.insert("", "end", values=(
                e['date'],
                e['description'],
                e.get('account_code', ''),
                f"{debit:,.0f}".replace(",", "."),
                f"{credit:,.0f}".replace(",", "."),
                f"{balance:,.0f}".replace(",", ".")
            ))

    def export_excel(self):
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            data.append(values)
        columns = ["Ngày", "Diễn giải", "TK đối ứng", "Nợ", "Có", "Số dư"]
        export_to_excel(data, columns, "So_chi_tiet")