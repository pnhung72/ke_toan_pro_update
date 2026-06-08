import tkinter as tk
from tkinter import ttk, messagebox
from models.debt import Debt
from datetime import datetime
from theme import get_font
import sqlite3
from models.transaction import Transaction
from models.invoice import Invoice
from utils.printer import show_print_preview
from models.invoice import Invoice
from utils.printer import print_text
from utils.excel_export import export_to_excel
from models.utils import smart_backup
class DebtTab(ttk.Frame):
    def __init__(self, parent, notebook):
        # Kích hoạt lớp Frame gốc - Thay thế cho dòng tạo self.frame cũ
        super().__init__(notebook)

        self.parent = parent
        self.notebook = notebook

        self.create_widgets()
        self.load_debts()
    
    def create_widgets(self):
        # Style cho font
        style = ttk.Style()
        style.configure("Debt.TLabel", font=get_font("label"))
        style.configure("Debt.TEntry", font=get_font("label"))
        style.configure("Debt.TButton", font=get_font("label"))
        style.configure("Debt.Treeview", font=get_font("small"), rowheight=30)
        style.configure("Debt.Treeview.Heading", font=get_font("bold"))
        
        # === Frame tìm kiếm và thống kê ===
        search_frame = ttk.LabelFrame(self, text="TÌM KIẾM", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="Tên khách hàng:", style="Debt.TLabel").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.entry_search_name = ttk.Entry(search_frame, width=25, font=get_font("label"))
        self.entry_search_name.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        
        ttk.Label(search_frame, text="SĐT:", style="Debt.TLabel").grid(row=0, column=2, padx=10, pady=8, sticky="w")
        self.entry_search_phone = ttk.Entry(search_frame, width=18, font=get_font("label"))
        self.entry_search_phone.grid(row=0, column=3, padx=10, pady=8, sticky="w")
        
        btn_frame = ttk.Frame(search_frame)
        btn_frame.grid(row=0, column=4, padx=15, pady=8)
        ttk.Button(btn_frame, text="🔍 Tìm", command=self.search_debt, style="Debt.TButton", width=10).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Làm mới", command=self.load_debts, style="Debt.TButton", width=12).pack(side="left", padx=5)
        
        # === Frame danh sách nợ ===
        list_frame = ttk.LabelFrame(self, text="DANH SÁCH CÔNG NỢ", padding=5)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("STT", "Tên khách hàng", "SĐT", "Tổng nợ", "Đã trả", "Còn nợ", "Ngày nợ cuối", "Ghi chú")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10, style="Debt.Treeview")
        
        col_widths = [50, 200, 110, 140, 140, 140, 120, 250]
        for idx, col in enumerate(columns):
            self.tree.heading(col, text=col)
            if idx == 1 or idx == 7:
                self.tree.column(col, width=col_widths[idx], anchor="w")
            else:
                self.tree.column(col, width=col_widths[idx], anchor="center")
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # === Frame nút chức năng ===
        btn_bottom = ttk.Frame(list_frame)
        btn_bottom.grid(row=2, column=0, columnspan=2, pady=10, sticky="e")
        
        ttk.Button(btn_bottom, text="📄 In bảng kê", command=self.print_debt_statement, style="Debt.TButton", width=14).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="🖨️ In", command=self.print_debt_statement_direct, style="Debt.TButton", width=10).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="💰 Ghi nhận trả nợ", command=self.record_payment, style="Debt.TButton", width=18).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="🗑️ Xóa nợ", command=self.delete_debt, style="Debt.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="🔄 Làm mới", command=self.load_debts, style="Debt.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="📊 Xuất Excel", command=self.export_excel, style="Debt.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(btn_bottom, text="✏️ Sửa", command=self.edit_debt, style="Debt.TButton", width=10).pack(side="left", padx=5)
        
        # Hiển thị tổng nợ
        self.total_label = ttk.Label(self, text="Tổng nợ còn lại: 0 VNĐ", font=get_font("bold"), foreground="red")
        self.total_label.pack(side="bottom", padx=10, pady=10, anchor="e")
    
    def load_debts(self):
        """Tải danh sách nợ"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        debts = Debt.get_all()
        total_remaining = 0
        
        for idx, debt in enumerate(debts, 1):
            total = debt['total_debt']
            paid = debt['paid']
            remaining = total - paid
            total_remaining += remaining
            
            total_str = f"{int(total):,}".replace(",", ".")
            paid_str = f"{int(paid):,}".replace(",", ".")
            remaining_str = f"{int(remaining):,}".replace(",", ".")
            
            last_date = debt['last_debt_date'] if debt['last_debt_date'] else ''
            notes = debt['notes'] if debt['notes'] else ''
            phone = debt['phone'] if debt['phone'] else ''
            
            self.tree.insert("", "end", values=(
                idx, debt['name'], phone, total_str, paid_str, remaining_str, last_date, notes
            ))
        
        self.total_label.config(text=f"Tổng nợ còn lại: {int(total_remaining):,}".replace(",", ".") + " VNĐ")
    
    def search_debt(self):
        name = self.entry_search_name.get().strip()
        phone = self.entry_search_phone.get().strip()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        debts = Debt.get_all()
        total_remaining = 0
        idx = 1
        for d in debts:
            match = True
            if name and name.lower() not in d['name'].lower():
                match = False
            if phone and phone not in (d['phone'] if d['phone'] else ''):
                match = False
            if match:
                remaining = d['total_debt'] - d['paid']
                total_remaining += remaining
                self.tree.insert("", "end", values=(
                    idx, d['name'], d['phone'] if d['phone'] else '',
                    f"{int(d['total_debt']):,}".replace(",", "."),
                    f"{int(d['paid']):,}".replace(",", "."),
                    f"{int(remaining):,}".replace(",", "."),
                    d['last_debt_date'] if d['last_debt_date'] else '',
                    d['notes'] if d['notes'] else ''
                ))
                idx += 1
        
        if name or phone:
            self.total_label.config(text=f"Kết quả tìm kiếm: {int(total_remaining):,}".replace(",", ".") + " VNĐ")
        else:
            self.total_label.config(text=f"Tổng nợ còn lại: {int(total_remaining):,}".replace(",", ".") + " VNĐ")
    
    def record_payment(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn khoản nợ cần ghi nhận trả nợ")
            return
        values = self.tree.item(selected[0], "values")
        name = values[1]
        phone = values[2] if values[2] else ""
        remaining_str = values[5].replace(".", "")
        try:
            remaining = float(remaining_str)
        except Exception:
            remaining = 0
        
        pay_win = tk.Toplevel(self.parent)
        pay_win.title("Ghi nhận trả nợ")
        pay_win.grab_set()
        
        main_frame = ttk.Frame(pay_win, padding=20)
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(1, weight=1) 
        
        # --- THÔNG TIN & NHẬP LIỆU ---
        ttk.Label(main_frame, text=f"Khách hàng: {name}", font=get_font("bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(main_frame, text=f"SĐT: {phone if phone else 'Không có'}", font=get_font("label")).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        ttk.Label(main_frame, text=f"Còn nợ: {int(remaining):,}".replace(",", ".") + " VNĐ", font=get_font("bold"), foreground="red").grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        ttk.Label(main_frame, text="Số tiền trả (VNĐ):", font=get_font("label")).grid(row=3, column=0, sticky="w", pady=4)
        entry_amount = ttk.Entry(main_frame, font=get_font("label"))
        entry_amount.grid(row=3, column=1, sticky="ew", pady=4, padx=(10, 0))
        entry_amount.focus_set()
        
        ttk.Label(main_frame, text="Ngày trả:", font=get_font("label")).grid(row=4, column=0, sticky="w", pady=4)
        entry_date = ttk.Entry(main_frame, font=get_font("label"), width=15)
        entry_date.grid(row=4, column=1, sticky="w", pady=4, padx=(10, 0))
        entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ttk.Label(main_frame, text="Ghi chú:", font=get_font("label")).grid(row=5, column=0, sticky="w", pady=4)
        entry_note = ttk.Entry(main_frame, font=get_font("label"))
        entry_note.grid(row=5, column=1, sticky="ew", pady=4, padx=(10, 0))

        # --- HÀM XỬ LÝ (LOGIC) ---
        def do_payment():
            try:
                date = entry_date.get().strip()
                # Định dạng ngày cho DB
                formatted_date = datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d")
                
                raw_amount = entry_amount.get().replace(".", "").replace(",", "")
                amount = float(raw_amount)
                
                if amount <= 0: raise ValueError("Số tiền phải lớn hơn 0")
                if amount > (remaining + 0.01): raise ValueError("Số tiền trả vượt quá nợ còn lại")
                
                db_path = get_db_path()
                with sqlite3.connect(db_path) as conn:
                    trans_manager = Transaction(conn)
                    trans_manager.create_journal_entry(
                        date=formatted_date,
                        description=f"Thu nợ từ {name} - {phone}",
                        entries=[{'account': '111', 'debit': amount, 'credit': 0}, {'account': '131', 'debit': 0, 'credit': amount}],
                        reference_no=f"TN{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        created_by="Admin"
                    )
                    conn.execute("UPDATE debts SET paid = paid + ?, last_debt_date = ?, notes = ? WHERE name = ? AND phone = ?", 
                                 (amount, date, entry_note.get().strip(), name, phone))
                    conn.commit()
                    
                # --- THÊM DÒNG NÀY VÀO ---
                smart_backup(get_db_path())
                
                self.load_debts()
                pay_win.destroy()
                messagebox.showinfo("Thành công", "Đã ghi nhận trả nợ")
                
                self.load_debts()
                pay_win.destroy()
                messagebox.showinfo("Thành công", "Đã ghi nhận trả nợ")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        # --- NÚT BẤM ---
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Xác nhận", command=do_payment, width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Hủy", command=pay_win.destroy, width=10).pack(side="left", padx=10)
        
        # Tự co giãn cửa sổ
        pay_win.update_idletasks()
        pay_win.geometry(f"{pay_win.winfo_reqwidth() + 40}x{pay_win.winfo_reqheight() + 40}")
    
    def delete_debt(self):
        """Xóa công nợ (có xác nhận) - Phiên bản tối ưu và an toàn"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn công nợ cần xóa trong danh sách")
            return
        
        # Lấy thông tin từ dòng đã chọn
        values = self.tree.item(selected[0], "values")
        # Giả định: values[1] là tên khách hàng, values[2] là số điện thoại
        # Nếu cột của bạn khác, hãy điều chỉnh số index ở đây (bắt đầu từ 0)
        debt_id_display = values[0]
        debt_customer = values[1] if len(values) > 1 else "Khách hàng"
        debt_phone = values[2] if len(values) > 2 else ""
        debt_amount = values[4] if len(values) > 4 else "0"
        
        confirm = messagebox.askyesno(
            "Xác nhận xóa công nợ",
            f"Bạn có chắc chắn muốn xóa công nợ?\n\n"
            f"📋 Mã hiển thị: #{debt_id_display}\n"
            f"👤 Khách hàng: {debt_customer}\n"
            f"📞 SĐT: {debt_phone}\n"
            f"💰 Số tiền: {debt_amount}đ\n\n"
            f"⚠️ Hành động này KHÔNG THỂ hoàn tác!",
            icon='warning'
        )
        
        if not confirm:
            return
        
        try:
            import sqlite3
            # Sử dụng đúng đường dẫn Database thực tế của hệ thống
            from data_config import DB_PATH
            db_path = DB_PATH
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # Xóa dựa trên Tên và SĐT để đảm bảo chính xác tuyệt đối
                cursor.execute("DELETE FROM debts WHERE name = ? AND phone = ?", (debt_customer, debt_phone))
                conn.commit()
            
            # Làm mới giao diện sau khi xóa
            self.load_debts() 
            messagebox.showinfo("Thành công", f"Đã xóa công nợ của {debt_customer}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa công nợ:\n{str(e)}")
    
    def print_debt_statement(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn khách hàng cần in bảng kê")
            return

        values = self.tree.item(selected[0], "values")
        customer_name = values[1]
        phone = values[2]
        invoices = Invoice.get_unpaid_invoices_by_customer(customer_name)

        if not invoices:
            messagebox.showinfo("Thông báo", f"Khách hàng {customer_name} không có hóa đơn còn nợ")
            return

        content = f"""
{'='*60}
{'BẢNG KÊ CÔNG NỢ':^60}
{'='*60}
Khách hàng: {customer_name}
Số điện thoại: {phone}
Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'-'*60}
{'STT':<4} {'Số HĐ':<8} {'Ngày tạo':<12} {'Số tiền':<15} {'Đã TT':<15} {'Còn nợ':<15}
{'-'*60}
"""
        total_debt = 0
        for idx, inv in enumerate(invoices, 1):
            remaining = inv['total_payment'] - inv['paid']
            total_debt += remaining
            content += f"{idx:<4} {inv['id']:<8} {inv['created_date']:<12} {inv['total_payment']:,.0f} VND   {inv['paid']:,.0f} VND   {remaining:,.0f} VND\n"

        content += f"""
{'-'*60}
Tổng cộng còn nợ: {total_debt:,.0f} VND
{'='*60}
Cảm ơn quý khách!
"""

        
        show_print_preview(content, f"Bảng kê công nợ - {customer_name}", self.frame)
    
    def print_debt_statement_direct(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn khách hàng cần in bảng kê")
            return

        values = self.tree.item(selected[0], "values")
        customer_name = values[1]
        phone = values[2]

        
        invoices = Invoice.get_unpaid_invoices_by_customer(customer_name)

        if not invoices:
            messagebox.showinfo("Thông báo", f"Khách hàng {customer_name} không có hóa đơn còn nợ")
            return

        content = f"""
{'='*60}
{'BẢNG KÊ CÔNG NỢ':^60}
{'='*60}
Khách hàng: {customer_name}
Số điện thoại: {phone}
Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'-'*60}
{'STT':<4} {'Số HĐ':<8} {'Ngày tạo':<12} {'Số tiền':<15} {'Đã TT':<15} {'Còn nợ':<15}
{'-'*60}
"""
        total_debt = 0
        for idx, inv in enumerate(invoices, 1):
            remaining = inv['total_payment'] - inv['paid']
            total_debt += remaining
            content += f"{idx:<4} {inv['id']:<8} {inv['created_date']:<12} {inv['total_payment']:,.0f} VND   {inv['paid']:,.0f} VND   {remaining:,.0f} VND\n"

        content += f"""
{'-'*60}
Tổng cộng còn nợ: {total_debt:,.0f} VND
{'='*60}
Cảm ơn quý khách!
"""

        
        print_text(content, f"Bảng kê công nợ - {customer_name}")
    
    def export_excel(self):
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            total_debt = float(values[3].replace(".", "")) if values[3] else 0
            paid = float(values[4].replace(".", "")) if values[4] else 0
            remaining = float(values[5].replace(".", "")) if values[5] else 0
            data.append({
                "STT": values[0],
                "Tên khách hàng": values[1],
                "SĐT": values[2] if values[2] else '',
                "Tổng nợ": total_debt,
                "Đã trả": paid,
                "Còn nợ": remaining,
                "Ngày nợ cuối": values[6],
                "Ghi chú": values[7]
            })
        columns = ["STT", "Tên khách hàng", "SĐT", "Tổng nợ", "Đã trả", "Còn nợ", "Ngày nợ cuối", "Ghi chú"]
        export_to_excel(data, columns, "Danh_sach_cong_no")
    
    def edit_debt(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn khoản nợ cần sửa")
            return
        
        values = self.tree.item(selected[0], "values")
        if len(values) < 3:
            messagebox.showerror("Lỗi", "Dữ liệu không hợp lệ")
            return
        
        name = values[1]
        phone = values[2] if values[2] else ""
        
        debt = Debt.get_by_name_phone(name, phone)
        if not debt:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin nợ")
            return
        
        edit_win = tk.Toplevel(self.frame)
        edit_win.title("Sửa khoản nợ")
        edit_win.geometry("550x650")
        edit_win.resizable(False, False)
        edit_win.grab_set()

        # 1. TẠO KHUNG CHỨA NÚT CỐ ĐỊNH Ở ĐÁY CỬA SỔ (Nằm ngoài Canvas)
        btn_container = ttk.Frame(edit_win, padding=10)
        btn_container.pack(side="bottom", fill="x")
        
        # 2. TẠO KHUNG CÓ CUỘN CHO DỮ LIỆU
        canvas = tk.Canvas(edit_win)
        scrollbar = ttk.Scrollbar(edit_win, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # [CÁC DÒNG TẠO GIAO DIỆN NHẬP LIỆU GIỮ NGUYÊN...]
        ttk.Label(scrollable_frame, text="THÔNG TIN KHÁCH HÀNG", font=get_font("bold")).pack(anchor="w", pady=(10, 5), padx=10)
        info_frame = ttk.Frame(scrollable_frame)
        info_frame.pack(fill="x", pady=5, padx=10)
        ttk.Label(info_frame, text="Khách hàng:", font=get_font("label"), width=12).grid(row=0, column=0, sticky="w")
        ttk.Label(info_frame, text=name, font=get_font("label")).grid(row=0, column=1, sticky="w")
        ttk.Label(info_frame, text="SĐT:", font=get_font("label"), width=12).grid(row=1, column=0, sticky="w")
        ttk.Label(info_frame, text=phone if phone else "(Không có)", font=get_font("label")).grid(row=1, column=1, sticky="w")
        
        ttk.Label(scrollable_frame, text="THÔNG TIN NỢ", font=get_font("bold")).pack(anchor="w", pady=(15, 5), padx=10)
        input_frame = ttk.Frame(scrollable_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        ttk.Label(input_frame, text="Tổng nợ (VNĐ):", font=get_font("label"), width=15).grid(row=0, column=0, sticky="w", pady=8)
        entry_total = ttk.Entry(input_frame, width=25, font=get_font("label"))
        entry_total.grid(row=0, column=1, sticky="w", pady=8)
        entry_total.insert(0, f"{int(debt['total_debt']):,}".replace(",", "."))
        
        ttk.Label(input_frame, text="Đã trả (VNĐ):", font=get_font("label"), width=15).grid(row=1, column=0, sticky="w", pady=8)
        entry_paid = ttk.Entry(input_frame, width=25, font=get_font("label"))
        entry_paid.grid(row=1, column=1, sticky="w", pady=8)
        entry_paid.insert(0, f"{int(debt['paid']):,}".replace(",", "."))
        
        ttk.Label(input_frame, text="Ngày nợ cuối:", font=get_font("label"), width=15).grid(row=2, column=0, sticky="w", pady=8)
        entry_date = ttk.Entry(input_frame, width=25, font=get_font("label"))
        entry_date.grid(row=2, column=1, sticky="w", pady=8)
        entry_date.insert(0, debt['last_debt_date'] if debt['last_debt_date'] else datetime.now().strftime("%d/%m/%Y"))
        
        ttk.Label(input_frame, text="Ghi chú:", font=get_font("label"), width=15).grid(row=3, column=0, sticky="w", pady=8)
        entry_notes = tk.Text(input_frame, height=8, width=35, font=get_font("small"))
        entry_notes.grid(row=3, column=1, sticky="w", pady=8)
        entry_notes.insert("1.0", debt['notes'] if debt['notes'] else '')
        
        remaining = debt['total_debt'] - debt['paid']
        remaining_frame = ttk.Frame(scrollable_frame)
        remaining_frame.pack(fill="x", pady=10, padx=10)
        ttk.Label(remaining_frame, text="Còn nợ hiện tại:", font=get_font("bold")).pack(side="left")
        ttk.Label(remaining_frame, text=f"{int(remaining):,}".replace(",", ".") + " VNĐ", font=get_font("bold"), foreground="red").pack(side="left", padx=10)

        # 3. HÀM LƯU DỮ LIỆU
        def save_changes():
            try:
                total_str = entry_total.get().replace(".", "").replace(",", "")
                paid_str = entry_paid.get().replace(".", "").replace(",", "")
                
                new_total = float(total_str) if total_str else 0
                new_paid = float(paid_str) if paid_str else 0
                new_date = entry_date.get().strip()
                new_notes = entry_notes.get("1.0", "end").strip()
                
                if new_paid > new_total:
                    messagebox.showerror("Lỗi", "Số tiền đã trả không thể lớn hơn tổng nợ")
                    return
                
                success = Debt.create(name, phone, total_debt=new_total, paid=new_paid, last_debt_date=new_date, notes=new_notes)
                
                if success:
                    self.load_debts()
                    edit_win.destroy()
                    messagebox.showinfo("Thành công", "Đã cập nhật công nợ")
                else:
                    messagebox.showerror("Lỗi", "Không thể cập nhật khoản nợ")
                    
            except ValueError as e:
                messagebox.showerror("Lỗi", f"Số tiền không hợp lệ: {e}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {e}")

        # === KHU VỰC GIAO DIỆN NÚT BẤM (ĐỂ THẲNG HÀNG VỚI def save_changes) ===
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=20, fill="x", padx=10)
        
        ttk.Button(btn_frame, text="Cập nhật", command=save_changes, style="Debt.TButton", width=12).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Hủy", command=edit_win.destroy, style="Debt.TButton", width=10).pack(side="left", padx=10)
        
        # Cập nhật lại khung cuộn để hiển thị nút
        scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))