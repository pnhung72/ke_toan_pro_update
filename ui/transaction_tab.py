import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from models.transaction import Transaction
from models.category import Category
from theme import get_font
from core.database.connection_pool import get_connection_pool
from utils.tooltip import add_tooltip
from ai.services.ai_service import AIService
from utils.license import has_ai_feature
import logging

class TransactionTab(ttk.Frame):
    def __init__(self, main_window, notebook):
            import sys
            # Kích hoạt lớp Frame gốc để đăng ký trực tiếp đối tượng với Notebook
            super().__init__(notebook)
            
            self.main_window = main_window
            self.notebook = notebook
            
            # --- CẬP NHẬT ĐƯỜNG DẪN THÔNG MINH BẢO TOÀN NGUYÊN TRẠNG ---
            # Kiểm tra xem đang chạy file .py hay file .exe (frozen)
            if getattr(sys, 'frozen', False):
                # Nếu là EXE, lấy đường dẫn thư mục chứa file EXE
                base_dir = Path(sys.executable).parent
            else:
                # Nếu là .py, lấy đường dẫn từ mã nguồn như cũ
                base_dir = Path(__file__).parent.parent

            # Khởi tạo connection pool với đường dẫn đã chuẩn hóa
            data_dir = base_dir / "ke_toan_data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "ke_toan.db")
            self.pool = get_connection_pool(db_path)
            # --- AI Service và gợi ý thông minh ---
            # --- AI Service và gợi ý thông minh (chỉ bật khi có license) ---
            self.ai_enabled = has_ai_feature()
            if self.ai_enabled:
                from ai.services.ai_service import AIService
                self.ai_service = AIService()
                self.selected_ai_suggestion = None
                self._suggestions = []
                # Không bind ở đây vì entry_desc chưa có, sẽ bind sau khi tạo widget
            else:
                self.ai_service = None
                self.suggestion_timer = None
                self._suggestions = []
                self.selected_ai_suggestion = None
            # -----------------------------------------------------------
            
            self.create_widgets()
            
            # --- BẢO TOÀN TOÀN BỘ BIẾN TRẠNG THÁI HỆ THỐNG PHÍA DƯỚI CỦA THẦY ---
            self.current_page = 1
            self.total_pages = 1
            self.page_size = 50
            self.all_transactions = []
            
            # Khởi tạo dữ liệu danh mục ban đầu cho hệ thống bộ lọc
            self.categories = []
            try:
                # Không cần truyền conn vào đây vì bản thân Category.get_all đã tự lấy kết nối
                self.categories = Category.get_all() 
            except Exception as e:
                logging.error(f"Lỗi nạp danh mục: {e}")
                
            # === CẬP NHẬT TRẬT TỰ KHỞI TẠO CHUẨN V9.0.0 ===
            # 1. Khởi tạo khung và các nhãn tổng kết trước để hệ thống có biến cấu hình
            self.create_summary_frame()
            
            # 2. Tải danh mục từ cơ sở dữ liệu
            self.load_categories()
            
            # 3. Cuối cùng mới nạp dữ liệu lên bảng hiển thị (Hàm này sẽ gọi update_summary an toàn)
            self.refresh_table()

    def load_categories(self):
        """Tải danh sách danh mục từ database"""
        self.categories = Category.get_all()
        self.update_category_combobox()

    def update_category_combobox(self):
        """Cập nhật combobox danh mục dựa trên loại giao dịch đã chọn"""
        trans_type = self.cbo_type.get()
        filtered = [cat['name'] for cat in self.categories if cat['type'] == trans_type]
        self.cbo_category['values'] = filtered
        if filtered:
            self.cbo_category.current(0)
        else:
            self.cbo_category.set('')
            
    def on_description_changed(self, event=None):
        """Gọi sau khi người dùng ngừng gõ 300ms"""
        if self.suggestion_timer:
            self.after(300, self.do_suggest)  # dùng tkinter after thay vì QTimer
        else:
            self.do_suggest()

    def do_suggest(self):
        """Gọi AI service để gợi ý danh mục"""
        desc = self.entry_desc.get().strip()
        if len(desc) < 3:
            return
        try:
            suggestions = self.ai_service.suggest_account(desc)
            if not suggestions:
                return
            self._suggestions = suggestions
            # Hiển thị popup menu ngay dưới ô mô tả
            self.show_suggestion_menu(suggestions)
        except Exception as e:
            logging.error(f"AI suggest error: {e}")

    def show_suggestion_menu(self, suggestions):
        """Hiển thị menu popup gợi ý danh mục"""
        menu = tk.Menu(self, tearoff=0)
        for cat, prob in suggestions:
            # Hiển thị danh mục và độ tin cậy (dạng phần trăm)
            text = f"{cat} ({prob:.0%})"
            menu.add_command(label=text, command=lambda c=cat: self.select_suggestion(c))
        # Hiển thị tại vị trí con trỏ (hoặc dưới ô mô tả)
        x = self.entry_desc.winfo_rootx()
        y = self.entry_desc.winfo_rooty() + self.entry_desc.winfo_height()
        menu.post(x, y)

    def select_suggestion(self, category_name):
        """Chọn danh mục từ gợi ý AI và ghi nhận feedback"""
        # Ghi nhận rằng người dùng đã chọn gợi ý này
        self.selected_ai_suggestion = category_name
        
        # Tìm và chọn trong combobox
        values = self.cbo_category['values']
        if category_name in values:
            self.cbo_category.set(category_name)
        else:
            messagebox.showinfo("Gợi ý AI", f"Danh mục '{category_name}' chưa có trong danh sách. Bạn có thể thêm qua 'Quản lý danh mục'.")
            
    def create_widgets(self):
        # Style cho font
        style = ttk.Style()
        style.configure("Transaction.TLabel", font=get_font("label"))
        style.configure("Transaction.TEntry", font=get_font("label"))
        style.configure("Transaction.TButton", font=get_font("label"))
        style.configure("Transaction.Treeview", font=get_font("small"), rowheight=30)
        style.configure("Transaction.Treeview.Heading", font=get_font("bold"))

        # Frame nhập liệu - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        input_frame = ttk.LabelFrame(self, text="Thêm giao dịch")
        input_frame.pack(fill="x", padx=10, pady=2)

        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(3, weight=1)
        input_frame.columnconfigure(5, weight=1)
        
        # === THÊM BỘ LỌC NGÀY === - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        filter_frame = ttk.LabelFrame(self, text="LỌC THEO NGÀY", padding=5)
        filter_frame.pack(fill="x", padx=10, pady=3)
        
        ttk.Label(filter_frame, text="Từ ngày:", font=get_font("label")).pack(side="left", padx=5)
        self.filter_start_date = ttk.Entry(filter_frame, width=12, font=get_font("label"))
        self.filter_start_date.pack(side="left", padx=5)
        # Mặc định ngày đầu tháng
        self.filter_start_date.insert(0, datetime.now().strftime("01/%m/%Y"))
        
        ttk.Label(filter_frame, text="Đến ngày:", font=get_font("label")).pack(side="left", padx=5)
        self.filter_end_date = ttk.Entry(filter_frame, width=12, font=get_font("label"))
        self.filter_end_date.pack(side="left", padx=5)
        self.filter_end_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ttk.Button(filter_frame, text="🔍 Lọc", command=self.filter_by_date, style="Transaction.TButton", width=8).pack(side="left", padx=10)
        ttk.Button(filter_frame, text="🔄 Xem tất cả", command=self.clear_filter, style="Transaction.TButton", width=10).pack(side="left", padx=5)

        # Ngày
        ttk.Label(input_frame, text="Ngày:", style="Transaction.TLabel").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.entry_date = ttk.Entry(input_frame, width=12, style="Transaction.TEntry")
        self.entry_date.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Mô tả
        ttk.Label(input_frame, text="Mô tả:", style="Transaction.TLabel").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        self.entry_desc = ttk.Entry(input_frame, width=35, style="Transaction.TEntry")
        self.entry_desc.grid(row=0, column=3, padx=5, pady=3, sticky="we")
        
        if self.ai_enabled:
            self.entry_desc.bind('<KeyRelease>', self.on_description_changed)

        # Số tiền
        ttk.Label(input_frame, text="Số tiền:", style="Transaction.TLabel").grid(row=1, column=0, padx=5, pady=3, sticky="w")
        self.entry_amount = ttk.Entry(input_frame, width=15, style="Transaction.TEntry")
        self.entry_amount.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        # Loại
        ttk.Label(input_frame, text="Loại:", style="Transaction.TLabel").grid(row=1, column=2, padx=5, pady=3, sticky="w")
        self.cbo_type = ttk.Combobox(input_frame, values=["Thu", "Chi"], width=10, state="readonly", font=get_font("label"))
        self.cbo_type.grid(row=1, column=3, padx=5, pady=3, sticky="w")
        self.cbo_type.current(0)
        self.cbo_type.bind("<<ComboboxSelected>>", lambda e: self.update_category_combobox())

        # Danh mục
        ttk.Label(input_frame, text="Danh mục:", style="Transaction.TLabel").grid(row=1, column=4, padx=5, pady=3, sticky="w")
        self.cbo_category = ttk.Combobox(input_frame, width=35, state="readonly", font=get_font("label"))
        self.cbo_category.grid(row=1, column=5, padx=5, pady=3, sticky="w")

        # Nút thêm
        btn_add = ttk.Button(input_frame, text="Thêm giao dịch", command=self.add_transaction, style="Transaction.TButton")
        btn_add.grid(row=2, column=5, padx=5, pady=3, sticky="e")
        from utils.tooltip import add_tooltip
        add_tooltip(btn_add, "Thêm giao dịch thu/chi mới vào sổ")

        # Frame danh sách - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        list_frame = ttk.LabelFrame(self, text="DANH SÁCH GIAO DỊCH", padding=5)
        list_frame.pack(fill="both", expand=True, padx=10, pady=2)

        columns = ("ID", "Ngày", "Mô tả", "Số tiền", "Loại", "Danh mục")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=7, style="Transaction.Treeview")

        col_widths = [60, 110, 400, 150, 100, 250]
        for idx, col in enumerate(columns):
            self.tree.heading(col, text=col)
            if col in ("Mô tả", "Danh mục"):
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

        # Frame nút chức năng - CHUYỂN DÁN TRỰC TIẾP LÊN TẦNG LÕI self
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=(2, 5), padx=10)

        # Cấu hình để các cột tự giãn rộng bằng nhau nếu cần
        for i in range(5):
            btn_frame.columnconfigure(i, weight=0)

        # Nút lệnh chức năng
        btn_edit = ttk.Button(btn_frame, text="✏️ Sửa", command=self.edit_transaction, style="Transaction.TButton")
        btn_edit.grid(row=0, column=0, padx=2)
        add_tooltip(btn_edit, "Sửa thông tin giao dịch đã chọn")

        btn_delete = ttk.Button(btn_frame, text="🗑️ Xóa", command=self.delete_transaction, style="Transaction.TButton")
        btn_delete.grid(row=0, column=1, padx=2)
        add_tooltip(btn_delete, "Xóa giao dịch đã chọn (không thể hoàn tác)")

        btn_refresh = ttk.Button(btn_frame, text="🔄 Làm mới", command=self.refresh_table, style="Transaction.TButton")
        btn_refresh.grid(row=0, column=2, padx=2)
        add_tooltip(btn_refresh, "Tải lại danh sách giao dịch mới nhất")

        btn_export = ttk.Button(btn_frame, text="📊 Xuất Excel", command=self.export_excel, style="Transaction.TButton")
        btn_export.grid(row=0, column=3, padx=2)
        add_tooltip(btn_export, "Xuất danh sách giao dịch ra file Excel")

        btn_category = ttk.Button(btn_frame, text="📂 Quản lý danh mục", command=self.manage_categories, style="Transaction.TButton")
        btn_category.grid(row=0, column=4, padx=2)
        add_tooltip(btn_category, "Thêm, sửa, xóa danh mục thu/chi")
        
    def create_summary_frame(self):
        """Tạo khung tổng kết thu/chi"""
        summary_frame = ttk.LabelFrame(self, text="TỔNG KẾT", padding=5)
        summary_frame.pack(fill="x", padx=10, pady=2)
        
        # Phải tạo các label này trước khi update_summary gọi
        self.total_income_label = ttk.Label(summary_frame, text="Thu: 0 VND", foreground="green", font=get_font("bold"))
        self.total_income_label.pack(side="left", padx=15)
        
        self.total_expense_label = ttk.Label(summary_frame, text="Chi: 0 VND", foreground="red", font=get_font("bold"))
        self.total_expense_label.pack(side="left", padx=15)
        
        self.balance_label = ttk.Label(summary_frame, text="Còn lại: 0 VND", foreground="blue", font=get_font("bold"))
        self.balance_label.pack(side="left", padx=15)

    def _convert_date_to_ymd(self, date_str: str) -> str:
        """Chuyển đổi dd/mm/yyyy sang yyyy-mm-dd"""
        try:
            day, month, year = date_str.split('/')
            return f"{year}-{month}-{day}"
        except Exception:
            return datetime.now().strftime("%Y-%m-%d")

    def _convert_date_to_dmy(self, date_str: str) -> str:
        """Chuyển đổi yyyy-mm-dd sang dd/mm/yyyy"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return date_str

    def _get_account_for_category(self, trans_type: str, category_name: str) -> tuple:
        """
        Lấy tài khoản Nợ và Có dựa trên loại giao dịch và danh mục
        Trả về: (debit_account, credit_account, description)
        """
        # Mặc định: Thu -> Nợ 111 (tiền mặt), Có 511 (doanh thu)
        #            Chi -> Nợ 642 (chi phí), Có 111 (tiền mặt)
        
        if trans_type == "Thu":
            # Doanh thu: Nợ tiền mặt, Có doanh thu bán hàng
            return ("111", "511", f"Doanh thu {category_name}")
        else:
            # Chi phí: Nợ chi phí, Có tiền mặt
            expense_accounts = {
                "Lương": "642",
                "Điện nước": "642",
                "Văn phòng phẩm": "642",
                "Mua hàng": "632",
                "Khấu hao": "627",
                "Thuế": "635",
            }
            account = expense_accounts.get(category_name, "642")
            return (account, "111", f"Chi phí {category_name}")

    def add_transaction(self):
        try:
            date_dmy = self.entry_date.get().strip()
            date_ymd = self._convert_date_to_ymd(date_dmy)
            desc = self.entry_desc.get().strip()
            amount_str = self.entry_amount.get().strip().replace('.', '').replace(',', '')
            amount = float(amount_str)
            trans_type = self.cbo_type.get()
            category = self.cbo_category.get()

            if not date_dmy or not desc or amount <= 0:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin")
                return

            try:
                datetime.strptime(date_dmy, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Lỗi", "Ngày không hợp lệ (dd/mm/yyyy)")
                return

            # Lấy tài khoản Nợ/Có dựa trên loại và danh mục
            debit_account, credit_account, entry_desc = self._get_account_for_category(trans_type, category)

            # Tạo bút toán kế toán
            with self.pool.get_connection() as conn:
                transaction = Transaction(conn)
                
                if trans_type == "Thu":
                    # Doanh thu: Nợ tiền mặt / Có doanh thu
                    entries = [
                        {'account': debit_account, 'debit': amount, 'credit': 0},
                        {'account': credit_account, 'debit': 0, 'credit': amount}
                    ]
                else:
                    # Chi phí: Nợ chi phí / Có tiền mặt
                    entries = [
                        {'account': debit_account, 'debit': amount, 'credit': 0},
                        {'account': credit_account, 'debit': 0, 'credit': amount}
                    ]
                
                journal_id = transaction.create_journal_entry(
                    date=date_ymd,
                    description=f"{entry_desc}: {desc}",
                    entries=entries,
                    reference_no=f"GD{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    created_by="user"
                )
                
                # Lưu thông tin category và feedback AI vào bảng metadata
                feedback = None
                if hasattr(self, 'selected_ai_suggestion') and self.selected_ai_suggestion:
                    feedback = 'correct' if self.selected_ai_suggestion == category else 'wrong_correction'
                elif hasattr(self, '_suggestions') and self._suggestions and self._suggestions[0][0] != category:
                    feedback = 'wrong_correction'

                self._save_transaction_metadata(journal_id, trans_type, category, desc, feedback)

                # Reset biến sau khi đã dùng
                self.selected_ai_suggestion = None
                
            self.clear_inputs()
            self.refresh_table()
            messagebox.showinfo("Thành công", f"Đã thêm giao dịch (bút toán #{journal_id})")
            
        except ValueError:
            messagebox.showerror("Lỗi", "Số tiền không hợp lệ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm giao dịch:\n{str(e)}")

    def _save_transaction_metadata(self, journal_id: int, trans_type: str, category: str, description: str, ai_feedback: str = None):
        """
        Lưu metadata giao dịch (loại, danh mục) vào bảng phụ để hiển thị.
        Tham số ai_feedback: 'correct', 'wrong_correction', hoặc None (mặc định).
        """
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            
            # --- Tự động thêm cột ai_feedback nếu chưa có (bảo toàn dữ liệu cũ) ---
            cursor.execute("PRAGMA table_info(transaction_metadata)")
            existing_columns = [col[1] for col in cursor.fetchall()]
            if 'ai_feedback' not in existing_columns:
                cursor.execute("ALTER TABLE transaction_metadata ADD COLUMN ai_feedback TEXT")
            
            # --- Tạo bảng nếu chưa tồn tại (đã có cột mới) ---
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaction_metadata (
                    journal_id INTEGER PRIMARY KEY,
                    type TEXT,
                    category TEXT,
                    description TEXT,
                    created_at TEXT,
                    ai_feedback TEXT
                )
            ''')
            
            # --- Chèn hoặc cập nhật, hỗ trợ tham số mới ---
            cursor.execute('''
                INSERT OR REPLACE INTO transaction_metadata 
                (journal_id, type, category, description, created_at, ai_feedback)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (journal_id, trans_type, category, description, datetime.now().isoformat(), ai_feedback))
            
            conn.commit()

    def _get_transactions_for_display(self, limit: int = 100):
            """Lấy danh sách giao dịch - Bản bảo tồn tính năng gốc và mở rộng tài khoản"""
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Thử lấy dữ liệu kèm Metadata (Ưu tiên hiển thị chi tiết)
                cursor.execute('''
                    SELECT 
                        je.id, je.date, 
                        tm.description as trans_description,
                        (SELECT SUM(debit_amount) FROM journal_details WHERE journal_entry_id = je.id) as total_amount,
                        tm.type, tm.category
                    FROM journal_entries je
                    JOIN transaction_metadata tm ON je.id = tm.journal_id
                    ORDER BY je.date DESC, je.id DESC LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                
                # 2. Nếu chưa có metadata (Dữ liệu cũ hoặc nhập trực tiếp vào DB)
                if not rows:
                    cursor.execute('''
                        SELECT 
                            je.id, je.date, 
                            je.description as trans_description,
                            (SELECT SUM(debit_amount) FROM journal_details WHERE journal_entry_id = je.id) as total_amount,
                            '' as type, '' as category
                        FROM journal_entries je
                        ORDER BY je.date DESC, je.id DESC LIMIT ?
                    ''', (limit,))
                    rows = cursor.fetchall()
                
                # 3. Chuyển đổi định dạng để hiển thị lên bảng (Bảo toàn logic cũ)
                result = []
                for row in rows:
                    # Logic xác định loại Thu/Chi dựa trên dữ liệu có sẵn
                    trans_type = row['type']
                    if not trans_type:
                        # Nếu là dữ liệu cũ, kiểm tra xem có tài khoản doanh thu (5xx) không
                        cursor.execute("SELECT 1 FROM journal_details WHERE journal_entry_id = ? AND account_code LIKE '5%' LIMIT 1", (row['id'],))
                        trans_type = "Thu" if cursor.fetchone() else "Chi"

                    result.append({
                        'id': row['id'],
                        'date': self._convert_date_to_dmy(row['date']),
                        'description': row['trans_description'],
                        'amount': row['total_amount'] if row['total_amount'] else 0,
                        'type': trans_type,
                        'category': row['category'] if row['category'] else "Khác"
                    })
                
                return result

    def edit_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn giao dịch cần sửa")
            return
        values = self.tree.item(selected[0], "values")
        tid = values[0]

        edit_win = tk.Toplevel(self)
        edit_win.title("Sửa giao dịch")
        edit_win.geometry("500x400")
        edit_win.grab_set()

        main_frame = ttk.Frame(edit_win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=3)

        # --- CÁC Ô NHẬP LIỆU ---
        ttk.Label(main_frame, text="Ngày:", font=get_font("label")).grid(row=0, column=0, padx=5, pady=3, sticky="w")
        entry_date = ttk.Entry(main_frame, width=12, font=get_font("label"))
        entry_date.grid(row=0, column=1, padx=5, pady=3)
        entry_date.insert(0, values[1])

        ttk.Label(main_frame, text="Mô tả:", font=get_font("label")).grid(row=1, column=0, padx=5, pady=3, sticky="w")
        entry_desc = ttk.Entry(main_frame, width=40, font=get_font("label"))
        entry_desc.grid(row=1, column=1, padx=5, pady=3)
        entry_desc.insert(0, values[2])

        ttk.Label(main_frame, text="Số tiền:", font=get_font("label")).grid(row=2, column=0, padx=5, pady=3, sticky="w")
        entry_amount = ttk.Entry(main_frame, width=15, font=get_font("label"))
        entry_amount.grid(row=2, column=1, padx=5, pady=3)
        amount_clean = values[3].replace(".", "")
        entry_amount.insert(0, amount_clean)

        ttk.Label(main_frame, text="Loại:", font=get_font("label")).grid(row=3, column=0, padx=5, pady=3, sticky="w")
        cbo_type = ttk.Combobox(main_frame, values=["Thu", "Chi"], width=10, state="readonly", font=get_font("label"))
        cbo_type.grid(row=3, column=1, padx=5, pady=3)
        cbo_type.set(values[4])

        ttk.Label(main_frame, text="Danh mục:", font=get_font("label")).grid(row=4, column=0, padx=5, pady=3, sticky="w")
        cbo_category = ttk.Combobox(main_frame, width=35, state="readonly", font=get_font("label"))
        cbo_category.grid(row=4, column=1, padx=5, pady=3)

        def update_cat():
            cat_type = cbo_type.get()
            cats = [cat['name'] for cat in Category.get_all() if cat['type'] == cat_type]
            cbo_category['values'] = cats
            if values[5] in cats:
                cbo_category.set(values[5])
            elif cats:
                cbo_category.current(0)
        update_cat()
        cbo_type.bind("<<ComboboxSelected>>", lambda e: update_cat())

        # --- HÀM XỬ LÝ LƯU (LOGIC CỦA THẦY) ---
        def save():
            try:
                # 1. Lấy dữ liệu
                new_date_dmy = entry_date.get().strip()
                new_date_ymd = self._convert_date_to_ymd(new_date_dmy)
                new_desc = entry_desc.get().strip()
                
                # Chuyển đổi số tiền
                raw_amount = entry_amount.get().strip().replace('.', '').replace(',', '')
                val = float(raw_amount)
                
                new_type = cbo_type.get() # 'Thu' hoặc 'Chi'
                new_cat = cbo_category.get()

                # 2. Logic Kế toán: Phân bổ số tiền vào Debit (Nợ) hoặc Credit (Có)
                # Giả định: Thu là ghi Nợ (Debit), Chi là ghi Có (Credit) 
                # Thầy có thể đảo lại tùy theo nghiệp vụ của Thầy
                if new_type == "Thu":
                    new_debit, new_credit = val, 0
                else:
                    new_debit, new_credit = 0, val

                import sqlite3
                from data_config import DB_PATH
                db_path = DB_PATH
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 3. Cập nhật bảng journal_entries (Sổ cái)
                    # Cập nhật đúng các cột: date, description, debit, credit
                    cursor.execute('''
                        UPDATE journal_entries 
                        SET date = ?, description = ?, debit = ?, credit = ?
                        WHERE id = ?
                    ''', (new_date_ymd, new_desc, new_debit, new_credit, int(tid)))
                    
                    # 4. Cập nhật bảng transaction_metadata
                    # Bảng này của Thầy không có 'amount', nên ta chỉ cập nhật type và category
                    cursor.execute('''
                        UPDATE transaction_metadata 
                        SET type = ?, category = ?, description = ?, created_at = ?
                        WHERE journal_id = ?
                    ''', (new_type, new_cat, new_desc, new_date_ymd, int(tid)))
                    
                    conn.commit()

                # 5. Hoàn tất
                edit_win.destroy()
                try:
                    self.refresh_table()
                except Exception:
                    pass
                messagebox.showinfo("Thành công", f"Đã cập nhật giao dịch #{tid}")
                
            except Exception as e:
                messagebox.showerror("Lỗi hệ thống", f"Không thể lưu: {str(e)}")

        # --- KHÔI PHỤC NÚT BẤM (PHẦN BỊ THIẾU) ---
        btn_frame = ttk.Frame(edit_win)
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        btn_save = ttk.Button(btn_frame, text="Cập nhật", command=save)
        btn_save.pack(side='right', padx=5)
        
        btn_cancel = ttk.Button(btn_frame, text="Hủy", command=edit_win.destroy)
        btn_cancel.pack(side='right', padx=5)
        
        # Căn giữa cửa sổ sửa để Thầy dễ nhìn
        edit_win.update_idletasks()
        x = (edit_win.winfo_screenwidth() // 2) - (edit_win.winfo_width() // 2)
        y = (edit_win.winfo_screenheight() // 2) - (edit_win.winfo_height() // 2)
        edit_win.geometry(f'+{x}+{y}')

    def delete_transaction(self):
        """Xóa giao dịch (có xác nhận)"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Chọn giao dịch cần xóa")
            return
        
        # Lấy thông tin giao dịch để hiển thị xác nhận
        values = self.tree.item(selected[0], "values")
        trans_id = values[0]
        trans_desc = values[2] if len(values) > 2 else "Không có mô tả"
        trans_amount = values[3] if len(values) > 3 else "0"
        trans_type = values[4] if len(values) > 4 else "Thu"
        
        # Hộp thoại xác nhận chi tiết
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa giao dịch sau?\n\n"
            f"📋 Mã: #{trans_id}\n"
            f"📝 Mô tả: {trans_desc}\n"
            f"💰 Số tiền: {trans_amount}đ\n"
            f"📊 Loại: {trans_type}\n\n"
            f"⚠️ Hành động này KHÔNG THỂ hoàn tác!",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Xác nhận lần 2 (an toàn hơn)
        confirm2 = messagebox.askyesno(
            "Xác nhận lần cuối",
            f"❌ Bạn có chắc chắn muốn XÓA VĨNH VIỄN giao dịch #{trans_id}?\n\nHành động này không thể phục hồi!",
            icon='warning'
        )
        
        if not confirm2:
            return
        
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("BEGIN")
                
                # Xóa metadata trước
                cursor.execute("DELETE FROM transaction_metadata WHERE journal_id = ?", (int(trans_id),))
                # Xóa chi tiết bút toán
                cursor.execute("DELETE FROM journal_details WHERE journal_entry_id = ?", (int(trans_id),))
                # Xóa header bút toán
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (int(trans_id),))
                
                conn.commit()
            
            self.refresh_table()
            messagebox.showinfo("Thành công", f"Đã xóa giao dịch #{trans_id}")
            
            # Cập nhật thanh trạng thái
            self._update_main_status_bar(f"Đã xóa giao dịch #{trans_id}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa giao dịch:\n{str(e)}")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        try:
            transactions = self._get_transactions_for_display(limit=100)
            for t in transactions:
                amount_str = f"{t['amount']:,.0f}".replace(",", ".")
                self.tree.insert("", "end", values=(
                    t["id"],
                    t["date"],
                    t["description"][:50] + ("..." if len(t["description"]) > 50 else ""),
                    amount_str,
                    t["type"],
                    t["category"]
                ))
            
            # === THÊM DÒNG NÀY ===
            self.update_summary()
            
        except Exception as e:
            if "no such table" in str(e):
                messagebox.showinfo("Thông báo", "Hãy thêm giao dịch đầu tiên để khởi tạo dữ liệu")
            else:
                messagebox.showerror("Lỗi", f"Lỗi tải dữ liệu: {str(e)}")
                
                

    def clear_inputs(self):
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.entry_desc.delete(0, tk.END)
        self.entry_amount.delete(0, tk.END)
        self.cbo_type.current(0)
        self.update_category_combobox()

    def export_excel(self):
        from utils.excel_export import export_to_excel
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            amount_str = values[3].replace(".", "")
            try:
                amount = float(amount_str) if amount_str else 0
            except Exception:
                amount = 0
            data.append({
                "ID": values[0],
                "Ngày": values[1],
                "Mô tả": values[2],
                "Số tiền": amount,
                "Loại": values[4],
                "Danh mục": values[5]
            })
        columns = ["ID", "Ngày", "Mô tả", "Số tiền", "Loại", "Danh mục"]
        export_to_excel(data, columns, "Danh_sach_giao_dich")

    def manage_categories(self):
        """Mở cửa sổ quản lý danh mục"""
        from ui.category_manager import CategoryManager
        # Thay vì self.frame (không tồn tại), sử dụng self để làm frame cha
        CategoryManager(self, self.load_categories)
        
    def update_summary(self):
        """Cập nhật tổng kết thu/chi"""
        try:
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                # --- THÊM DÒNG NÀY ĐỂ BẮT LỖI CHÍNH XÁC ---
                #print("DEBUG: Đang chạy truy vấn tổng kết...")
                
                # Tổng thu
                cursor.execute('''
                    SELECT COALESCE(SUM(credit_amount), 0) as total
                    FROM journal_details jd
                    JOIN journal_entries je ON jd.journal_entry_id = je.id
                    WHERE jd.account_code = '511'
                ''')
                total_income = cursor.fetchone()[0]
                
                # Tổng chi
                cursor.execute('''
                    SELECT COALESCE(SUM(debit_amount), 0) as total
                    FROM journal_details jd
                    JOIN journal_entries je ON jd.journal_entry_id = je.id
                    WHERE jd.account_code = '642'
                ''')
                total_expense = cursor.fetchone()[0]
                
                balance = total_income - total_expense
                
                self.total_income_label.config(text=f"Thu: {total_income:,.0f} VND")
                self.total_expense_label.config(text=f"Chi: {total_expense:,.0f} VND")
                
                balance_color = "green" if balance >= 0 else "red"
                self.balance_label.config(text=f"Còn lại: {balance:,.0f} VND", foreground=balance_color)
        except Exception as e:
            logging.error(f"Lỗi cập nhật tổng kết: {e}")
            import traceback
            traceback.print_exc() # Dòng này sẽ in ra chính xác file và dòng gây lỗi
    
    def filter_by_date(self):
        """Lọc giao dịch theo khoảng ngày"""
        start_dmy = self.filter_start_date.get().strip()
        end_dmy = self.filter_end_date.get().strip()
        
        try:
            start_ymd = self._convert_date_to_ymd(start_dmy)
            end_ymd = self._convert_date_to_ymd(end_dmy)
        except Exception:
            messagebox.showerror("Lỗi", "Ngày không hợp lệ (dd/mm/yyyy)")
            return
        
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    je.id,
                    je.date,
                    tm.description as trans_description,
                    jd.debit_amount,
                    jd.credit_amount,
                    tm.type,
                    tm.category
                FROM journal_entries je
                JOIN transaction_metadata tm ON je.id = tm.journal_id
                JOIN journal_details jd ON je.id = jd.journal_entry_id
                WHERE je.date BETWEEN ? AND ?
                GROUP BY je.id
                ORDER BY je.date DESC, je.id DESC
            ''', (start_ymd, end_ymd))
            
            rows = cursor.fetchall()
            
            # Xóa dữ liệu cũ trên tree
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            for row in rows:
                amount = row['debit_amount'] if row['debit_amount'] > 0 else row['credit_amount']
                trans_type = row['type'] if row['type'] else ("Thu" if row['credit_amount'] > 0 else "Chi")
                category = row['category'] if row['category'] else "Khác"
                description = row['trans_description']
                date_dmy = self._convert_date_to_dmy(row['date'])
                
                amount_str = f"{amount:,.0f}".replace(",", ".")
                self.tree.insert("", "end", values=(
                    row['id'], date_dmy, 
                    description[:50] + ("..." if len(description) > 50 else ""),
                    amount_str, trans_type, category
                ))
            
            self.update_summary()
            self.show_message(f"Đã lọc {len(rows)} giao dịch từ {start_dmy} đến {end_dmy}")
    
    def clear_filter(self):
        """Xóa bộ lọc, hiển thị tất cả giao dịch"""
        self.refresh_table()
        self.show_message("Đã xóa bộ lọc, hiển thị tất cả giao dịch")
    
    def show_message(self, message):
        """Hiển thị thông báo tạm thời trên status bar nếu có"""
        try:
            main_window = self.parent.winfo_toplevel()
            if hasattr(main_window, 'update_status'):
                main_window.update_status(message)
        except Exception:
            pass
            
    def _update_main_status_bar(self, message):
        """Cập nhật thanh trạng thái của cửa sổ chính"""
        try:
            main_window = self.parent.winfo_toplevel()
            if hasattr(main_window, 'update_status'):
                main_window.update_status(message)
        except Exception:
            pass