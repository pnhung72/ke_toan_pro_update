import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from services.report_service import get_report_service
from core.database.connection_pool import get_connection_pool
from pathlib import Path
from models.transaction import Transaction
from models.invoice import Invoice
from models.database import Database   # thêm để truy vấn trực tiếp nếu cần
from datetime import datetime
import os
import pandas as pd
from utils.license import is_full_version
from theme import get_font

class ReportTab(ttk.Frame):

    def __init__(self, parent, notebook):
        # Kích hoạt lớp Frame gốc - Thay thế cho dòng tạo self.frame cũ
        super().__init__(notebook)

        self.parent = parent
        self.notebook = notebook

        # Khởi tạo connection pool và report service - BẢO TOÀN NGUYÊN TRẠNG LOGIC
        data_dir = Path(__file__).parent.parent / "ke_toan_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / "ke_toan.db")
        self.pool = get_connection_pool(db_path)
        self.report_service = get_report_service()

        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Khởi tạo giao diện Tab Báo cáo - Bảo toàn Style và Font toàn cục"""
        # === 1. STYLE CHO FONT (Giữ nguyên thiết lập của Thầy) ===
        style = ttk.Style()
        style.configure("Report.TNotebook.Tab", font=get_font("title"), padding=[15, 8])
        style.configure("Report.TLabelframe.Label", font=get_font("bold"))
        style.configure("Report.TButton", font=get_font("label"), padding=8)
        style.configure("Report.TLabel", font=get_font("label"))
        style.configure("Report.Treeview", font=get_font("small"), rowheight=28)
        style.configure("Report.Treeview.Heading", font=get_font("bold"))
        
        # === 2. FRAME NÚT CHỨC NĂNG (Đưa lên trước để không bị đè) === - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        # Khai báo borderwidth và relief đúng quy tắc để tránh TclError
        btn_frame = ttk.Frame(self, padding=5, borderwidth=1, relief="ridge")
        btn_frame.pack(side="bottom", fill="x", padx=5, pady=2) # Đặt ở đáy
        
        left_btn_frame = ttk.Frame(btn_frame)
        left_btn_frame.pack(side="left")
        
        ttk.Button(left_btn_frame, text="🔄 Làm mới dữ liệu", command=self.load_data,
                   style="Report.TButton").pack(side="left", padx=5)
        ttk.Button(left_btn_frame, text="📥 Xuất Excel tổng hợp", command=self.export_all_reports,
                   style="Report.TButton").pack(side="left", padx=5)
        ttk.Button(left_btn_frame, text="🖨️ In báo cáo", command=self.print_all_reports,
                   style="Report.TButton").pack(side="left", padx=5)
        
        right_btn_frame = ttk.Frame(btn_frame)
        right_btn_frame.pack(side="right")
        
        self.update_time_label = ttk.Label(
            right_btn_frame,
            text=f"Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}",
            foreground="gray",
            font=get_font("small")
        )
        self.update_time_label.pack(side="right", padx=5)

        # === 3. NỘI DUNG CHÍNH (Notebook) === - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        # Đặt sau để nó tự co giãn trong phần diện tích còn lại
        self.notebook = ttk.Notebook(self, style="Report.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=10, pady=3)
        
        # === CÁC TAB CHÍNH ===
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="📊 Tổng quan")
        
        self.category_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text="📁 Theo danh mục")
        
        self.quarterly_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.quarterly_frame, text="📅 Theo quý")
        
        self.yearly_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.yearly_frame, text="📆 Theo năm")
        
        self.tax_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tax_frame, text="💰 Thuế")
        
        # === TẠO TAX_TREE TRONG TAB THUẾ ===
        result_frame = ttk.LabelFrame(self.tax_frame, text="Kết quả tính thuế", style="Report.TLabelframe")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("Loại thuế", "Số tiền", "Ghi chú")
        self.tax_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=12, style="Report.Treeview")
        self.tax_tree.heading("Loại thuế", text="Loại thuế")
        self.tax_tree.heading("Số tiền", text="Số tiền (VNĐ)")
        self.tax_tree.heading("Ghi chú", text="Ghi chú")
        self.tax_tree.column("Loại thuế", width=180, anchor="w")
        self.tax_tree.column("Số tiền", width=180, anchor="e")
        self.tax_tree.column("Ghi chú", width=450, anchor="w")
        
        vsb = ttk.Scrollbar(result_frame, orient="vertical", command=self.tax_tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient="horizontal", command=self.tax_tree.xview)
        self.tax_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tax_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
    def _get_transaction_count(self) -> int:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM journal_entries")
            return cursor.fetchone()[0]

    def _get_invoice_count(self) -> int:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM invoices")
            return cursor.fetchone()[0]

    def _get_transactions_from_metadata(self, limit: int = 1000):
        transactions = []
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    je.id,
                    je.date,
                    COALESCE(tm.description, je.description) as description,
                    COALESCE(tm.type, 'Thu') as type,
                    COALESCE(tm.category, 'Khác') as category,
                    jd.debit_amount,
                    jd.credit_amount
                FROM journal_entries je
                LEFT JOIN transaction_metadata tm ON je.id = tm.journal_id
                JOIN journal_details jd ON je.id = jd.journal_entry_id
                WHERE jd.account_code IN ('111', '511', '642')
                GROUP BY je.id
                ORDER BY je.date DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            for row in rows:
                amount = row['debit_amount'] if row['debit_amount'] > 0 else row['credit_amount']
                transactions.append({
                    'id': row['id'],
                    'date': row['date'],
                    'description': row['description'],
                    'amount': amount,
                    'type': row['type'],
                    'category': row['category']
                })
        return transactions
    
    def export_all_reports(self):
        """Xuất báo cáo tổng hợp - Đã xử lý triệt để lỗi invalid command name"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        
        from services.invoice_service import InvoiceService
        import pandas as pd
        import os
        from tkinter import filedialog, messagebox
        from datetime import datetime
        
        try:
            # 1. Lấy số liệu tổng quát từ Service (Dữ liệu gốc, không phụ thuộc giao diện)
            total_income = self.report_service.get_total_income() + InvoiceService.get_total_revenue()
            total_expense = self.report_service.get_total_expense()
            profit = total_income - total_expense
            
            categories = self.report_service.get_categories_summary()
            quarterly = self.report_service.get_quarterly_report()
            yearly = self.report_service.get_yearly_report()
            
            # 2. Xử lý dữ liệu Thuế AN TOÀN
            # Thay vì lấy từ self.tax_tree (dễ lỗi), ta gọi hàm tính toán thuế của chính nó
            # Giả sử Thầy có hàm get_tax_calculation_logic() trong service hoặc gọi trực tiếp tại đây
            tax_data = []
            try:
                # Nếu bảng Thuế đang hiển thị và có dữ liệu thì lấy, nếu lỗi thì bỏ qua hoặc tính tay
                if hasattr(self, 'tax_tree') and self.tax_tree.winfo_exists():
                    for item in self.tax_tree.get_children():
                        val = self.tax_tree.item(item, "values")
                        if val: tax_data.append(val)
            except Exception:
                # Nếu bảng chưa khởi tạo (lỗi invalid command), ta có thể để trống hoặc 
                # gọi hàm xử lý logic thuế từ report_service để lấy dữ liệu thô
                tax_data = [["Thông tin", "Dữ liệu chưa được nạp", "Vui lòng xem trong tab Thuế"]]

            # 3. Lưu File
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"Bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            if not file_path: return

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: Tổng quan
                pd.DataFrame([
                    ["Tổng thu", total_income],
                    ["Tổng chi", total_expense],
                    ["Lợi nhuận", profit],
                    ["Số giao dịch", self._get_transaction_count()]
                ], columns=["Chỉ tiêu", "Số tiền"]).to_excel(writer, sheet_name="Tổng quan", index=False)
                
                # Sheet 2: Danh mục
                if categories:
                    pd.DataFrame(list(categories.items()), columns=["Danh mục", "Số tiền"]).to_excel(writer, sheet_name="Theo danh mục", index=False)
                
                # Sheet 3: Theo Quý
                if quarterly:
                    q_list = [[y, q, vals['income'], vals['expense'], vals['income']-vals['expense']] 
                             for y, qs in quarterly.items() for q, vals in qs.items()]
                    pd.DataFrame(q_list, columns=["Năm", "Quý", "Thu", "Chi", "Lợi nhuận"]).to_excel(writer, sheet_name="Theo quý", index=False)
                
                # Sheet 4: Theo Năm
                if yearly:
                    y_list = [[y, v['income'], v['expense'], v['income']-v['expense']] for y, v in yearly.items()]
                    pd.DataFrame(y_list, columns=["Năm", "Thu", "Chi", "Lợi nhuận"]).to_excel(writer, sheet_name="Theo năm", index=False)
                
                # Sheet 5: Thuế
                if tax_data:
                    pd.DataFrame(tax_data, columns=["Loại thuế", "Số tiền", "Ghi chú"]).to_excel(writer, sheet_name="Thuế", index=False)
            
            messagebox.showinfo("Thành công", f"Đã xuất file tại:\n{file_path}")
            if messagebox.askyesno("Mở file", "Thầy có muốn xem file ngay không?"):
                os.startfile(file_path)
                
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể xuất báo cáo: {str(e)}")

    def print_all_reports(self):
        """In báo cáo tổng hợp"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from services.transaction_service import TransactionService
        from services.invoice_service import InvoiceService
        from utils.printer import show_print_preview
        
        total_income = TransactionService.get_total_income() + InvoiceService.get_total_revenue()
        total_expense = TransactionService.get_total_expense()
        profit = total_income - total_expense
        
        transactions = TransactionService.get_all_transactions()
        categories = {}
        for t in transactions:
            cat = t['category']
            if cat not in categories:
                categories[cat] = {'Thu': 0, 'Chi': 0}
            if t['type'] == 'Thu':
                categories[cat]['Thu'] += t['amount']
            else:
                categories[cat]['Chi'] += t['amount']
        
        quarterly = {}
        for t in transactions:
            try:
                d, m, y = t['date'].split('/')
                y = int(y)
                m = int(m)
                q = (m-1)//3 + 1
                key = (y, q)
                if key not in quarterly:
                    quarterly[key] = {'Thu': 0, 'Chi': 0}
                if t['type'] == 'Thu':
                    quarterly[key]['Thu'] += t['amount']
                else:
                    quarterly[key]['Chi'] += t['amount']
            except Exception:
                continue
        
        content = f"""
    {'='*60}
    {'BÁO CÁO TÀI CHÍNH':^60}
    {'='*60}

    Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M')}

    {'TỔNG QUAN':^60}
    {'-'*60}
    Tổng thu:  {self.format_money(total_income)} VNĐ
    Tổng chi:  {self.format_money(total_expense)} VNĐ
    Lợi nhuận: {self.format_money(profit)} VNĐ
    Số giao dịch: {len(transactions)}

    {'THEO DANH MỤC (TOP 10)':^60}
    {'-'*60}
    """
        sorted_cats = sorted(categories.items(), key=lambda x: abs(x[1]['Thu'] - x[1]['Chi']), reverse=True)[:10]
        for cat, vals in sorted_cats:
            chenh = vals['Thu'] - vals['Chi']
            content += f"{cat[:30]:<30}: {self.format_money(chenh):>15} VNĐ\n"
        
        content += f"""
    {'THEO QUÝ':^60}
    {'-'*60}
    """
        for (y, q), vals in sorted(quarterly.items()):
            thu = vals['Thu']
            chi = vals['Chi']
            lnhuan = thu - chi
            content += f"Năm {y} - Quý {q}:\n"
            content += f"  Thu: {self.format_money(thu)} VNĐ\n"
            content += f"  Chi: {self.format_money(chi)} VNĐ\n"
            content += f"  Lợi nhuận: {self.format_money(lnhuan)} VNĐ\n\n"
        
        content += f"{'='*60}\n"
        
        show_print_preview(content, "Báo cáo tài chính", self.frame)
    
    def load_data(self):
        """Hàm nạp dữ liệu tổng thể - Bảo toàn cấu trúc gọi hàm gốc"""
        self.load_overview()   # Hàm này đã được nâng cấp chạy động theo JSON
        self.load_category()   # Bảo toàn nguyên trạng tính năng cũ
        self.load_quarterly()  # Bảo toàn nguyên trạng tính năng cũ
        self.load_yearly()     # Bảo toàn nguyên trạng tính năng cũ
        self.load_tax()        # Bảo toàn nguyên trạng tính năng cũ
        
        # Cập nhật nhãn thời gian đúng theo định dạng gốc của thầy
        self.update_time_label.config(text=f"Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")

    def load_overview(self):
        """Nâng cấp tính năng load_overview chạy động theo cấu hình Thông tư JSON"""
        # 1. Xóa sạch dữ liệu cũ trên bảng hiển thị tổng quan chính xác của thầy
        for item in self.overview_tree.get_children():
            self.overview_tree.delete(item)

        try:
            # 2. Khởi tạo kết nối Database an toàn từ Pool sẵn có của thầy
            db_conn = self.pool.get_connection() 
            
            # 3. Gọi Engine tính toán báo cáo động
            from services.reports.report_engine import ReportEngine
            engine = ReportEngine(db_conn)
            
            # Quét file JSON và trả về mảng kết quả tính toán số dư tài khoản
            danh_sach_bao_cao = engine.xuat_bao_cao_tai_chinh()
            
            # 4. Đổ dữ liệu động lên giao diện Treeview (Bảo toàn cấu trúc 4 cột)
            for bctc in danh_sach_bao_cao:
                # Nếu chỉ tiêu yêu cầu in đậm (co_in_dam: true trong JSON), gán tag 'indam'
                tags = ("indam",) if bctc["co_in_dam"] else ()
                
                # Định dạng tiền tệ Kỳ này (Ví dụ: 125,400,000.00)
                ky_nay = f"{bctc['so_tien']:,.2f}" if isinstance(bctc['so_tien'], (int, float)) else "0.00"
                
                # Kỳ trước (Hiện tại mặc định 0.00, thầy có thể mở rộng lấy số dư đầu kỳ trong JSON sau)
                ky_truoc = "0.00"
                
                # Chèn đúng vào 4 cột: Mã số, Chỉ tiêu, Kỳ này, Kỳ trước
                self.overview_tree.insert(
                    "", 
                    "end", 
                    values=(bctc["ma_so"], bctc["ten_chi_tieu"], ky_nay, ky_truoc),
                    tags=tags
                )
                
            # 5. Áp dụng biến font toàn cục get_font('bold') chuẩn xác cho dòng in đậm
            self.overview_tree.tag_configure("indam", font=get_font('bold'))
            
            # Trả lại kết nối vào Pool sau khi hoàn thành để tối ưu hệ thống
            self.pool.release_connection(db_conn)
            
        except Exception as e:
            messagebox.showerror("Lỗi nạp dữ liệu", f"Không thể tải dữ liệu tổng quan động: {str(e)}")
    
    def format_money(self, amount):
        return f"{amount:,.0f}".replace(",", ".")
    
    def load_overview(self):
        for widget in self.overview_frame.winfo_children():
            widget.destroy()
        
        total_income = self.report_service.get_total_income()
        total_expense = self.report_service.get_total_expense()
        profit = total_income - total_expense
        
        # Tạo frame chính với padding
        main_frame = ttk.Frame(self.overview_frame, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(title_frame, text="📊 BÁO CÁO TỔNG QUAN", font=get_font("bold"), foreground="#2196F3").pack()
        
        # Khung hiển thị số liệu - chia làm 2 cột
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="both", expand=True)
        
        # Cột trái
        left_frame = ttk.LabelFrame(stats_frame, text="Số liệu chính", padding=15, style="Report.TLabelframe")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        label_font = get_font("label")
        value_font = get_font("title")   # title đã được định nghĩa là bold size 18
        
        # Định dạng số liệu
        def format_color(amount):
            if amount >= 0:
                return f"🟢 {self.format_money(amount)}"
            return f"🔴 {self.format_money(amount)}"
        
        stats = [
            ("💰 Tổng thu", self.format_money(total_income), "#4CAF50"),
            ("📉 Tổng chi", self.format_money(total_expense), "#f44336"),
            ("📈 Lợi nhuận", format_color(profit), "#2196F3" if profit >= 0 else "#f44336"),
        ]
        
        for i, (label_text, value, color) in enumerate(stats):
            frame = ttk.Frame(left_frame)
            frame.pack(fill="x", pady=8)
            ttk.Label(frame, text=label_text, font=label_font, width=15).pack(side="left")
            ttk.Label(frame, text=value, font=value_font, foreground=color).pack(side="left", padx=10)
        
        ttk.Separator(left_frame, orient='horizontal').pack(fill="x", pady=10)
        
        # Thông tin phụ
        small_font = get_font("small")
        sub_frame = ttk.Frame(left_frame)
        sub_frame.pack(fill="x", pady=5)
        ttk.Label(sub_frame, text="📋 Số giao dịch:", font=small_font).pack(side="left")
        ttk.Label(sub_frame, text=str(self._get_transaction_count()), font=get_font("bold"), foreground="#666").pack(side="left", padx=10)
        
        sub_frame2 = ttk.Frame(left_frame)
        sub_frame2.pack(fill="x", pady=5)
        ttk.Label(sub_frame2, text="🧾 Số hóa đơn:", font=small_font).pack(side="left")
        ttk.Label(sub_frame2, text=str(self._get_invoice_count()), font=get_font("bold"), foreground="#666").pack(side="left", padx=10)
        
        # Cột phải - Thông tin bổ sung
        right_frame = ttk.LabelFrame(stats_frame, text="Thông tin bổ sung", padding=15, style="Report.TLabelframe")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ttk.Label(right_frame, text="📌 Tỷ lệ lợi nhuận:", font=label_font).pack(anchor="w", pady=(0, 5))
        if total_income > 0:
            profit_ratio = (profit / total_income) * 100
            ratio_text = f"{profit_ratio:,.1f}%"
            color = "#4CAF50" if profit_ratio >= 0 else "#f44336"
            ttk.Label(right_frame, text=ratio_text, font=get_font("bold"), foreground=color).pack(anchor="w", pady=(0, 15))
        else:
            ttk.Label(right_frame, text="0%", font=get_font("bold")).pack(anchor="w", pady=(0, 15))
        
        ttk.Label(right_frame, text="📊 Kỳ báo cáo:", font=label_font).pack(anchor="w", pady=(0, 5))
        ttk.Label(right_frame, text=datetime.now().strftime("%d/%m/%Y"), font=get_font("label")).pack(anchor="w")
        
        # Nút bấm
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="📥 Xuất Excel", command=self.export_overview, 
                   style="Report.TButton", width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🖨️ In", command=self.print_overview, 
                   style="Report.TButton", width=15).pack(side="left", padx=5)
                   
        if total_income == 0 and total_expense == 0:
                ttk.Label(main_frame, text="⚠️ Chưa có dữ liệu giao dịch. Hãy vào tab 'Giao dịch' để thêm mới.", 
                          font=get_font("label"), foreground="orange").pack(pady=20)
    
    def load_category(self):
        for widget in self.category_frame.winfo_children():
            widget.destroy()
        
        categories = self.report_service.get_categories_summary()
        
        # Tạo frame chính với padding
        main_frame = ttk.Frame(self.category_frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(title_frame, text="📁 BÁO CÁO THEO DANH MỤC", font=get_font("bold"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Thống kê thu/chi theo từng danh mục", font=get_font("label"), foreground="gray").pack()
        
        # Khung chứa treeview và scrollbar
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        # Tạo treeview với độ rộng cột cân đối
        tree = ttk.Treeview(tree_frame, columns=("Danh mục", "Số tiền"), show="headings", height=12, style="Report.Treeview")
        tree.heading("Danh mục", text="Danh mục")
        tree.heading("Số tiền", text="Số tiền (VNĐ)")
        tree.column("Danh mục", width=400, anchor="w")
        tree.column("Số tiền", width=250, anchor="e")
        
        # Thêm dữ liệu
        total_amount = 0
        for cat, amount in sorted(categories.items(), key=lambda x: abs(x[1]), reverse=True):
            amount_str = self.format_money(amount)
            # Màu sắc cho số tiền
            if amount > 0:
                tag = "income"
            elif amount < 0:
                tag = "expense"
            else:
                tag = "zero"
            tree.insert("", "end", values=(cat, amount_str), tags=(tag,))
            total_amount += amount
        
        # Cấu hình màu sắc
        tree.tag_configure("income", foreground="#4CAF50")
        tree.tag_configure("expense", foreground="#f44336")
        tree.tag_configure("zero", foreground="#666")
        
        # Thanh cuộn
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Khung thống kê nhanh
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 5))
        
        # Tổng hợp thu/chi
        total_income = sum(a for a in categories.values() if a > 0)
        total_expense = sum(abs(a) for a in categories.values() if a < 0)
        
        stats_left = ttk.Frame(stats_frame)
        stats_left.pack(side="left", expand=True, fill="x")
        
        ttk.Label(stats_left, text=f"💰 Tổng thu: {self.format_money(total_income)}", 
                 font=get_font("label"), foreground="#4CAF50").pack(side="left", padx=10)
        ttk.Label(stats_left, text=f"📉 Tổng chi: {self.format_money(total_expense)}", 
                 font=get_font("label"), foreground="#f44336").pack(side="left", padx=10)
        ttk.Label(stats_left, text=f"📊 Chênh lệch: {self.format_money(total_income - total_expense)}", 
                 font=get_font("bold")).pack(side="left", padx=10)
        
    def load_quarterly(self):
        """Tải dữ liệu theo quý - Đã dọn dẹp nút lỗi hiển thị và bảo toàn Double-click"""
        for widget in self.quarterly_frame.winfo_children():
            widget.destroy()
        
        quarterly = self.report_service.get_quarterly_report()
        
        # Tạo frame chính với padding
        main_frame = ttk.Frame(self.quarterly_frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Tiêu đề (Bảo toàn Font chữ hệ thống)
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(title_frame, text="📅 BÁO CÁO THEO QUÝ", font=get_font("bold"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Thống kê doanh thu, chi phí và lợi nhuận theo từng quý", 
                  font=get_font("label"), foreground="gray").pack()
        
        # Khung chứa treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        # Khởi tạo Treeview (Giữ nguyên để Double-click hoạt động)
        self.quarter_tree = ttk.Treeview(tree_frame, columns=("Năm", "Quý", "Thu", "Chi", "Lợi nhuận"), 
                                         show="headings", height=12, style="Report.Treeview")
        
        columns_config = {
            "Năm": {"width": 100, "anchor": "center"},
            "Quý": {"width": 80, "anchor": "center"},
            "Thu": {"width": 180, "anchor": "e"},
            "Chi": {"width": 180, "anchor": "e"},
            "Lợi nhuận": {"width": 180, "anchor": "e"}
        }
        
        for col in self.quarter_tree["columns"]:
            self.quarter_tree.heading(col, text=col)
            cfg = columns_config.get(col, {"width": 120, "anchor": "e"})
            self.quarter_tree.column(col, width=cfg["width"], anchor=cfg["anchor"])
        
        # Thêm dữ liệu và tính tổng
        total_income = 0
        total_expense = 0
        
        for year in sorted(quarterly.keys()):
            # Duyệt qua các quý hiện có trong dữ liệu của năm đó
            for q_key in sorted(quarterly[year].keys()): 
                inc = quarterly[year][q_key]['income']
                exp = quarterly[year][q_key]['expense']
                profit = inc - exp
                total_income += inc
                total_expense += exp
                
                tag = "profit_positive" if profit >= 0 else "profit_negative"
                
                self.quarter_tree.insert("", "end", values=(
                    year, 
                    q_key,  # Bỏ chữ f"Q{...}" đi vì q_key của Thầy đã có sẵn chữ Q rồi
                    self.format_money(inc),
                    self.format_money(exp),
                    self.format_money(profit)
                ), tags=(tag,))
        
        # Màu sắc lợi nhuận
        self.quarter_tree.tag_configure("profit_positive", foreground="#4CAF50")
        self.quarter_tree.tag_configure("profit_negative", foreground="#f44336")
        
        # Thanh cuộn
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.quarter_tree.yview)
        self.quarter_tree.configure(yscrollcommand=vsb.set)
        self.quarter_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # === QUAN TRỌNG: Giữ lại sự kiện Double-click để xem chi tiết ===
        self.quarter_tree.bind("<Double-1>", self.show_quarter_details)
        
        # Khung thống kê tổng hợp (Dưới bảng)
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 5))
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack()
        
        ttk.Label(stats_container, text=f"💰 Tổng thu: {self.format_money(total_income)}", 
                 font=get_font("label"), foreground="#4CAF50").pack(side="left", padx=15)
        ttk.Label(stats_container, text=f"📉 Tổng chi: {self.format_money(total_expense)}", 
                 font=get_font("label"), foreground="#f44336").pack(side="left", padx=15)
        ttk.Label(stats_container, text=f"📊 Tổng lợi nhuận: {self.format_money(total_income - total_expense)}", 
                 font=get_font("bold"), foreground="#2196F3").pack(side="left", padx=15)

        # Ghi chú nhỏ hướng dẫn Thầy
        ttk.Label(main_frame, text="💡 Nháy đúp chuột (Double-click) vào một hàng để xem chi tiết giao dịch của quý đó.", 
                  font=get_font("small"), foreground="#888").pack(pady=5)
        
        # ĐÃ XÓA PHẦN NÚT BẤM GÂY LỖI Ở ĐÂY
    
    def load_yearly(self):
        """Tải dữ liệu theo năm - Đã xóa nút thừa, đồng bộ giao diện Pro"""
        for widget in self.yearly_frame.winfo_children():
            widget.destroy()
        
        yearly = self.report_service.get_yearly_report()
        
        # Tạo frame chính với padding
        main_frame = ttk.Frame(self.yearly_frame, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Tiêu đề (Sử dụng font bold hệ thống)
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(title_frame, text="📆 BÁO CÁO THEO NĂM", font=get_font("bold"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Thống kê doanh thu, chi phí và lợi nhuận theo từng năm", 
                  font=get_font("label"), foreground="gray").pack()
        
        # Khung chứa treeview
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill="both", expand=True, pady=5)
        
        # Tạo treeview
        tree = ttk.Treeview(tree_frame, columns=("Năm", "Thu", "Chi", "Lợi nhuận"), 
                            show="headings", height=12, style="Report.Treeview")
        
        # Cấu hình cột
        columns_config = {
            "Năm": {"width": 120, "anchor": "center"},
            "Thu": {"width": 200, "anchor": "e"},
            "Chi": {"width": 200, "anchor": "e"},
            "Lợi nhuận": {"width": 200, "anchor": "e"}
        }
        
        for col in tree["columns"]:
            tree.heading(col, text=col)
            cfg = columns_config.get(col, {"width": 140, "anchor": "e"})
            tree.column(col, width=cfg["width"], anchor=cfg["anchor"])
        
        # Thêm dữ liệu và tính tổng
        total_income = 0
        total_expense = 0
        
        for year in sorted(yearly.keys()):
            inc = yearly[year]['income']
            exp = yearly[year]['expense']
            profit = inc - exp
            total_income += inc
            total_expense += exp
            
            tag = "profit_positive" if profit >= 0 else "profit_negative"
            
            tree.insert("", "end", values=(
                year,
                self.format_money(inc),
                self.format_money(exp),
                self.format_money(profit)
            ), tags=(tag,))
        
        # Cấu hình màu sắc
        tree.tag_configure("profit_positive", foreground="#4CAF50")
        tree.tag_configure("profit_negative", foreground="#f44336")
        
        # Thanh cuộn
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Khung thống kê tổng hợp (Dưới bảng)
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 5))
        
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack()
        
        ttk.Label(stats_container, text=f"💰 Tổng thu: {self.format_money(total_income)}", 
                 font=get_font("label"), foreground="#4CAF50").pack(side="left", padx=15)
        ttk.Label(stats_container, text=f"📉 Tổng chi: {self.format_money(total_expense)}", 
                 font=get_font("label"), foreground="#f44336").pack(side="left", padx=15)
        ttk.Label(stats_container, text=f"📊 Tổng lợi nhuận: {self.format_money(total_income - total_expense)}", 
                 font=get_font("bold"), foreground="#2196F3").pack(side="left", padx=15)

        # ĐÃ XÓA PHẦN NÚT BẤM GÂY LỖI Ở ĐÂY ĐỂ ĐỒNG BỘ VỚI THANH CÔNG CỤ CHÍNH
    
    def load_tax(self):
        for widget in self.tax_frame.winfo_children():
            widget.destroy()
        
        revenue = self.report_service.get_total_income()
        
        input_frame = ttk.LabelFrame(self.tax_frame, text="Thông tin tính thuế", style="Report.TLabelframe")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        label_font = get_font("label")
        entry_font = get_font("label")
        
        ttk.Label(input_frame, text="Doanh thu (VNĐ):", font=label_font).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.revenue_var = tk.StringVar(value=self.format_money(revenue))
        self.revenue_entry = ttk.Entry(input_frame, textvariable=self.revenue_var, width=18, font=entry_font)
        self.revenue_entry.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        
        ttk.Label(input_frame, text="Năm tính thuế:", font=label_font).grid(row=0, column=2, padx=10, pady=8, sticky="w")
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.year_entry = ttk.Entry(input_frame, textvariable=self.year_var, width=8, font=entry_font)
        self.year_entry.grid(row=0, column=3, padx=10, pady=8, sticky="w")
        
        ttk.Label(input_frame, text="Loại hình:", font=label_font).grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.business_type = ttk.Combobox(input_frame, values=["Hộ kinh doanh cá thể", "Doanh nghiệp (Công ty TNHH, Cổ phần)"], width=32, font=entry_font)
        self.business_type.grid(row=1, column=1, padx=10, pady=8, sticky="w")
        self.business_type.current(0)
        
        ttk.Label(input_frame, text="Ngành nghề:", font=label_font).grid(row=1, column=2, padx=10, pady=8, sticky="w")
        self.industry = ttk.Combobox(input_frame, values=["Phân phối, cung cấp hàng hóa", "Dịch vụ, xây dựng không bao thầu", "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa", "Hoạt động kinh doanh khác"], width=38, font=entry_font)
        self.industry.grid(row=1, column=3, padx=10, pady=8, sticky="w")
        self.industry.current(0)
        
        def calculate():
            try:
                rev = float(self.revenue_var.get().replace(".", "").replace(",", ""))
                year = int(self.year_var.get())
                tax = self.report_service.calculate_tax(rev, self.business_type.get(), self.industry.get(), year)
                result_text = f"""
                Thuế GTGT: {self.format_money(tax['vat'])} VNĐ
                Thuế TNCN (hộ KD): {self.format_money(tax['pit'])} VNĐ
                Thuế TNDN (doanh nghiệp): {self.format_money(tax['tndn'])} VNĐ
                Lệ phí môn bài: {self.format_money(tax['mon_bai'])} VNĐ
                Tổng thuế phải nộp: {self.format_money(tax['vat']+tax['pit']+tax['tndn']+tax['mon_bai'])} VNĐ
                """
                result_label.config(text=result_text)
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))
        
        ttk.Button(input_frame, text="Tính thuế", command=calculate, style="Report.TButton").grid(row=2, column=0, columnspan=4, pady=10)
        
        result_frame = ttk.LabelFrame(self.tax_frame, text="Kết quả tính thuế", style="Report.TLabelframe")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        result_label = ttk.Label(result_frame, text="", justify=tk.LEFT, font=get_font("label"))
        result_label.pack(padx=15, pady=10, anchor="w")
        
        btn_export_tax = ttk.Button(self.tax_frame, text="📥 Xuất Excel", command=self.export_tax, style="Report.TButton")
        btn_export_tax.pack(pady=10)
    
    def export_overview(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        total_income = self.report_service.get_total_income()
        total_expense = self.report_service.get_total_expense()
        profit = total_income - total_expense
        data = [
            ["Tổng thu", total_income],
            ["Tổng chi", total_expense],
            ["Lợi nhuận", profit],
            ["Số giao dịch", self._get_transaction_count()],
            ["Số hóa đơn", self._get_invoice_count()]
        ]
        columns = ["Chỉ tiêu", "Giá trị"]
        export_to_excel(data, columns, "Bao_cao_tong_quan")

    def export_category(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        categories = self.report_service.get_categories_summary()
        data = [(cat, amount) for cat, amount in categories.items()]
        columns = ["Danh mục", "Số tiền"]
        export_to_excel(data, columns, "Bao_cao_theo_danh_muc")

    def export_quarterly(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        quarterly = self.report_service.get_quarterly_report()
        data = []
        for year in sorted(quarterly.keys()):
            for q in ["Q1", "Q2", "Q3", "Q4"]:
                if q in quarterly[year]:
                    inc = quarterly[year][q]['income']
                    exp = quarterly[year][q]['expense']
                    profit = inc - exp
                    data.append([year, q, inc, exp, profit])
        columns = ["Năm", "Quý", "Thu", "Chi", "Lợi nhuận"]
        export_to_excel(data, columns, "Bao_cao_theo_quy")

    def export_yearly(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        yearly = self.report_service.get_yearly_report()
        data = []
        for year in sorted(yearly.keys()):
            inc = yearly[year]['income']
            exp = yearly[year]['expense']
            profit = inc - exp
            data.append([year, inc, exp, profit])
        columns = ["Năm", "Thu", "Chi", "Lợi nhuận"]
        export_to_excel(data, columns, "Bao_cao_theo_nam")

    def export_tax(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        revenue_str = self.revenue_var.get() if hasattr(self, 'revenue_var') else "0"
        revenue = float(revenue_str.replace(".", "").replace(",", ""))
        business = self.business_type.get() if hasattr(self, 'business_type') else "Hộ kinh doanh cá thể"
        industry = self.industry.get() if hasattr(self, 'industry') else "Phân phối, cung cấp hàng hóa"
        year = int(self.year_var.get()) if hasattr(self, 'year_var') else datetime.now().year
        tax = self.report_service.calculate_tax(revenue, business, industry, year)
        data = [
            ["Doanh thu", revenue],
            ["Thuế GTGT", tax['vat']],
            ["Thuế TNCN", tax['pit']],
            ["Thuế TNDN", tax['tndn']],
            ["Lệ phí môn bài", tax['mon_bai']],
            ["Tổng thuế phải nộp", tax['vat']+tax['pit']+tax['tndn']+tax['mon_bai']]
        ]
        columns = ["Chỉ tiêu", "Số tiền"]
        export_to_excel(data, columns, "Bao_cao_thue")
        
    def export_excel(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        from services.report_service import ReportService
        import pandas as pd
        from datetime import datetime
        
        try:
            total_income = self.report_service.get_total_income()
            total_expense = self.report_service.get_total_expense()
            profit = total_income - total_expense
            overview_data = [
                ["Tổng thu", total_income],
                ["Tổng chi", total_expense],
                ["Lợi nhuận", profit],
                ["Số giao dịch", self._get_transaction_count()],
                ["Số hóa đơn", self._get_invoice_count()]
            ]
            
            categories = self.report_service.get_categories_summary()
            cat_data = [[cat, amount] for cat, amount in categories.items()]
            
            quarterly = self.report_service.get_quarterly_report()
            quarter_data = []
            for year in sorted(quarterly.keys()):
                for q in ["Q1", "Q2", "Q3", "Q4"]:
                    if q in quarterly[year]:
                        inc = quarterly[year][q]['income']
                        exp = quarterly[year][q]['expense']
                        profit_q = inc - exp
                        quarter_data.append([year, q, inc, exp, profit_q])
            
            yearly = self.report_service.get_yearly_report()
            year_data = []
            for year in sorted(yearly.keys()):
                inc = yearly[year]['income']
                exp = yearly[year]['expense']
                profit_y = inc - exp
                year_data.append([year, inc, exp, profit_y])
            
            revenue_str = self.revenue_var.get() if hasattr(self, 'revenue_var') else "0"
            revenue = float(revenue_str.replace(".", "").replace(",", "")) if revenue_str else 0
            tax_year = self.year_var.get() if hasattr(self, 'year_var') else str(datetime.now().year)
            business = self.business_type.get() if hasattr(self, 'business_type') else "Hộ kinh doanh cá thể"
            industry = self.industry.get() if hasattr(self, 'industry') else "Phân phối, cung cấp hàng hóa"
            tax = ReportService.calculate_tax(revenue, business, industry, int(tax_year))
            tax_data = [
                ["Thuế GTGT", tax['vat']],
                ["Thuế TNCN (hộ KD)", tax['pit']],
                ["Thuế TNDN (doanh nghiệp)", tax['tndn']],
                ["Lệ phí môn bài", tax['mon_bai']],
                ["Tổng thuế phải nộp", tax['vat'] + tax['pit'] + tax['tndn'] + tax['mon_bai']]
            ]
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"Bao_cao_tong_hop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            if not file_path:
                return
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                pd.DataFrame(overview_data, columns=["Chỉ tiêu", "Số tiền"]).to_excel(writer, sheet_name="Tổng quan", index=False)
                pd.DataFrame(cat_data, columns=["Danh mục", "Số tiền"]).to_excel(writer, sheet_name="Theo danh mục", index=False)
                pd.DataFrame(quarter_data, columns=["Năm", "Quý", "Thu", "Chi", "Lợi nhuận"]).to_excel(writer, sheet_name="Theo quý", index=False)
                pd.DataFrame(year_data, columns=["Năm", "Thu", "Chi", "Lợi nhuận"]).to_excel(writer, sheet_name="Theo năm", index=False)
                pd.DataFrame(tax_data, columns=["Loại thuế", "Số tiền"]).to_excel(writer, sheet_name="Thuế", index=False)
            
            messagebox.showinfo("Thành công", f"Đã xuất báo cáo tổng hợp:\n{file_path}")
            if messagebox.askyesno("Mở file", "Bạn có muốn mở file vừa xuất không?"):
                os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo:\n{str(e)}")
            
    def print_overview(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        total_income = self.report_service.get_total_income()
        total_expense = self.report_service.get_total_expense()
        profit = total_income - total_expense
        content = f"""
        {'='*50}
        {'BÁO CÁO TÀI CHÍNH - TỔNG QUAN':^50}
        {'='*50}
        
        Ngày in: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        Tổng thu:     {self.format_money(total_income)} VNĐ
        Tổng chi:     {self.format_money(total_expense)} VNĐ
        Lợi nhuận:    {self.format_money(profit)} VNĐ
        Số giao dịch: {self._get_transaction_count()}
        Số hóa đơn:   {self._get_invoice_count()}
        {'='*50}
        """
        from utils.printer import show_print_preview
        show_print_preview(content, "Báo cáo tổng quan", self.parent)
        
    def update_revenue_from_system(self):
        from services.transaction_service import TransactionService
        from services.invoice_service import InvoiceService
        
        total_revenue = TransactionService.get_total_income() + InvoiceService.get_total_revenue()
        total_expense = TransactionService.get_total_expense()
        
        self.revenue_var.set(self.format_money(total_revenue))
        self.expense_var.set(self.format_money(total_expense))
        self.profit_var.set(self.format_money(total_revenue - total_expense))
        
        self.calculate_tax_display()
        
    def calculate_tax_display(self):
        from services.tax_service import TaxService
        
        try:
            revenue_str = self.revenue_var.get().replace(".", "").replace(",", "")
            revenue = float(revenue_str) if revenue_str else 0
            
            profit_str = self.profit_var.get().replace(".", "").replace(",", "")
            profit = float(profit_str) if profit_str else 0
            
            business_type = self.business_type.get()
            industry = self.industry.get()
            tax_year = int(self.tax_year.get())
            
            tax = TaxService.calculate_tax(revenue, business_type, industry, tax_year)
            
            for item in self.tax_tree.get_children():
                self.tax_tree.delete(item)
            
            def fmt(amt):
                return f"{amt:,.0f}".replace(",", ".")
            
            self.tax_tree.insert("", "end", values=("Thuế GTGT", fmt(tax['vat']), "Tính trên doanh thu"))
            self.tax_tree.insert("", "end", values=("Thuế TNCN (hộ KD)", fmt(tax['pit']), "Tính trên doanh thu"))
            
            if "Doanh nghiệp" in business_type:
                tndn = profit * 0.20
                self.tax_tree.insert("", "end", values=("Thuế TNDN", fmt(tndn), "20% trên lợi nhuận thực tế"))
            else:
                self.tax_tree.insert("", "end", values=("Thuế TNDN", "0", "Không áp dụng"))
            
            if tax_year < 2026:
                self.tax_tree.insert("", "end", values=("Lệ phí môn bài", fmt(tax['mon_bai']), "Theo NĐ 139/2016"))
            else:
                self.tax_tree.insert("", "end", values=("Lệ phí môn bài", "0", "Đã bãi bỏ từ 2026"))
            
            total = tax['vat'] + tax['pit']
            if "Doanh nghiệp" in business_type:
                total += profit * 0.20
            if tax_year < 2026:
                total += tax['mon_bai']
            
            self.tax_tree.insert("", "end", values=("TỔNG CỘNG", fmt(total), ""), tags=("total",))
            self.tax_tree.tag_configure("total", background="#E3F2FD")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tính thuế: {str(e)}")
            
    def export_tax_report(self):
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        from utils.excel_export import export_to_excel
        
        data = []
        for item in self.tax_tree.get_children():
            values = self.tax_tree.item(item, "values")
            data.append(values)
        
        columns = ["Loại thuế", "Số tiền", "Ghi chú"]
        export_to_excel(data, columns, "Bao_cao_thue")

    # =============== PHẦN MỚI THÊM: CHI TIẾT THEO QUÝ ===============
    def show_quarter_details(self, event):
        """Hiển thị chi tiết hóa đơn và chi phí trong quý được double-click"""
        selected = self.quarter_tree.selection()
        if not selected:
            return
        values = self.quarter_tree.item(selected[0], "values")
        if len(values) < 2:
            return
        
        # values[0] = Năm, values[1] = Quý (dạng "Q1")
        year = values[0]
        quarter_str = values[1]   # ví dụ "Q1"
        # Chuyển quý thành số 1-4
        quarter_num = int(quarter_str[1])
        
        # Xác định khoảng thời gian của quý
        if quarter_num == 1:
            start_month, end_month = 1, 3
        elif quarter_num == 2:
            start_month, end_month = 4, 6
        elif quarter_num == 3:
            start_month, end_month = 7, 9
        else:
            start_month, end_month = 10, 12
        
        # Lấy danh sách hóa đơn trong quý
        invoices = self.get_invoices_by_quarter(year, start_month, end_month)
        # Lấy danh sách chi phí (nếu có bảng expenses)
        expenses = self.get_expenses_by_quarter(year, start_month, end_month)
        
        # Mở cửa sổ chi tiết
        self.show_detail_window(year, quarter_num, invoices, expenses)
    
    def get_invoices_by_quarter(self, year, start_month, end_month):
        """Lấy danh sách hóa đơn trong quý (định dạng ngày dd/mm/yyyy)"""
        invoices = []
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                # Do ngày lưu dạng dd/mm/yyyy, phải dùng SUBSTR để trích năm và tháng
                query = """
                    SELECT id, created_date, buyer_name, product_name, quantity, total_payment
                    FROM invoices
                    WHERE SUBSTR(created_date, 7, 4) = ?
                      AND CAST(SUBSTR(created_date, 4, 2) AS INTEGER) BETWEEN ? AND ?
                    ORDER BY created_date DESC
                """
                cursor.execute(query, (str(year), start_month, end_month))
                rows = cursor.fetchall()
                for row in rows:
                    invoices.append((
                        row['id'],
                        row['created_date'],
                        row['buyer_name'],
                        row['product_name'],
                        f"{row['quantity']:,.0f}".replace(",", "."),
                        f"{row['total_payment']:,.0f}".replace(",", ".")
                    ))
        except Exception as e:
            logging.error(f"Lỗi khi lấy hóa đơn theo quý: {e}")
        return invoices

    def get_expenses_by_quarter(self, year, start_month, end_month):
        expenses = []
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        je.id,
                        je.date,
                        COALESCE(tm.description, je.description) as description,
                        jd.debit_amount
                    FROM journal_entries je
                    LEFT JOIN transaction_metadata tm ON je.id = tm.journal_id
                    JOIN journal_details jd ON je.id = jd.journal_entry_id
                    WHERE COALESCE(tm.type, '') = 'Chi'
                      AND substr(je.date, 1, 4) = ?
                      AND CAST(substr(je.date, 6, 2) AS INTEGER) BETWEEN ? AND ?
                    ORDER BY je.date DESC
                ''', (str(year), start_month, end_month))
                rows = cursor.fetchall()
                for row in rows:
                    expenses.append((
                        row['id'],
                        row['date'],
                        row['description'][:50] if row['description'] else '',
                        f"{row['debit_amount']:,.0f}".replace(",", ".")
                    ))
        except Exception as e:
            pass
        return expenses
    
    def show_detail_window(self, year, quarter_num, invoices, expenses):
        """Tạo cửa sổ hiển thị chi tiết hóa đơn và chi phí"""
        detail_win = tk.Toplevel(self.parent)
        detail_win.title(f"Chi tiết Quý {quarter_num}/{year}")
        detail_win.geometry("1000x550")
        
        notebook = ttk.Notebook(detail_win)
        notebook.pack(fill="both", expand=True, padx=5, pady=3)
        
        # Tab Doanh thu (hóa đơn)
        frame_income = ttk.Frame(notebook)
        notebook.add(frame_income, text="📄 Doanh thu (hóa đơn)")
        self.create_detail_treeview(
            frame_income,
            invoices,
            columns=("Mã HĐ", "Ngày", "Khách hàng", "Sản phẩm", "Số lượng", "Thành tiền")
        )
        
        # Tab Chi phí (nếu có dữ liệu)
        frame_expense = ttk.Frame(notebook)
        notebook.add(frame_expense, text="💰 Chi phí")
        if expenses:
            self.create_detail_treeview(
                frame_expense,
                expenses,
                columns=("ID", "Ngày", "Nội dung", "Số tiền")
            )
        else:
            ttk.Label(frame_expense, text="Không có dữ liệu chi phí trong quý này.", font=get_font("label")).pack(pady=20)
    
    def create_detail_treeview(self, parent, data, columns):
        """Tạo Treeview hiển thị danh sách với font lớn"""
        style = ttk.Style()
        style.configure("Detail.Treeview", font=get_font("label"), rowheight=25)
        style.configure("Detail.Treeview.Heading", font=get_font("bold"))
        
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12, style="Detail.Treeview")
        for col in columns:
            tree.heading(col, text=col)
            if col in ["Mã HĐ", "Khách hàng", "Sản phẩm", "Nội dung"]:
                tree.column(col, width=120, anchor="w")
            elif col in ["Thành tiền", "Số tiền"]:
                tree.column(col, width=150, anchor="e")
            else:
                tree.column(col, width=100, anchor="center")
        
        for item in data:
            tree.insert("", "end", values=item)
        
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
    def xuat_excel(self):
        from utils.license import is_full_version
        from utils.trial import get_remaining_days
        from tkinter import messagebox
        
        if not is_full_version():
            remaining = get_remaining_days()
            if remaining <= 0:
                messagebox.showerror(
                    "Hết hạn dùng thử",
                    "Bạn đã hết thời gian dùng thử.\nVui lòng mua bản quyền để tiếp tục sử dụng.\nLiên hệ: 0982493474"
                )
                return
        
        # Gọi hàm xuất Excel tổng hợp đã có sẵn
        self.export_excel()
        
    def confirm_delete_report(self, report_name):
        """Xác nhận trước khi xóa báo cáo"""
        result = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa báo cáo '{report_name}'?\n\n⚠️ Hành động này không thể hoàn tác!",
            icon='warning'
        )
        return result