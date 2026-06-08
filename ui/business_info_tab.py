import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models.business import Business, BankAccount
from services.bank_account_service import BankAccountService
from services.revenue_book_service import RevenueBookService
from services.revenue_notification_service import RevenueNotificationService
from services.business_tax_return_service import BusinessTaxReturnService
from utils.logger import get_logger
from utils.helpers import format_currency, validate_mst, get_current_year, get_current_quarter
from ui.styles import ICONS
import os
import webbrowser
from datetime import datetime
from theme import get_font
logger = get_logger(__name__)

class BusinessInfoTab:
    """Tab quản lý thông tin hộ kinh doanh và các mẫu biểu thuế"""
    
    def __init__(self, parent, ma_so_thue=None):
        self.frame = ttk.Frame(parent)
        self.master = parent  # Lưu tham chiếu đến master (Notebook hoặc Tk)
        self.ma_so_thue = ma_so_thue
        self.business_info = None
        self.current_account_id = None
        
        self.setup_ui()
        self.load_data()
        
    def create_scrollable_frame(self, parent):
        """Tạo một khung có thanh cuộn dọc"""
        
        # Khung chứa canvas và scrollbar
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)
        
        # Canvas để cuộn
        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame bên trong canvas (nơi chứa nội dung thực)
        inner_frame = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        
        # Cập nhật vùng cuộn khi frame thay đổi kích thước
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Cập nhật chiều rộng canvas khi thay đổi
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        inner_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Hỗ trợ cuộn bằng chuột
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
        inner_frame.bind("<MouseWheel>", on_mousewheel)
        
        return inner_frame
    
    def setup_ui(self):
        # Tạo notebook con (4 tab nhỏ)
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Thông tin hộ kinh doanh
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="🏠 Thông tin hộ kinh doanh")
        self.setup_info_tab()
        
        # Tab 2: Quản lý tài khoản ngân hàng
        self.bank_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bank_frame, text="🏦 Tài khoản ngân hàng")
        self.setup_bank_tab()
        
        # Tab 3: Xuất hồ sơ thuế (01/BK-STK)
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="📤 Xuất hồ sơ thuế")
        self.setup_export_tab()
        
        # Tab 4: Sổ doanh thu S1a-HKD (THÊM MỚI)
        self.revenue_book_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.revenue_book_frame, text="📒 Sổ doanh thu S1a-HKD")
        self.setup_revenue_book_tab()
        
        # Tab 5: Thông báo doanh thu 01/TKN-CNKD
        self.notification_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.notification_frame, text="📢 Thông báo doanh thu")
        self.setup_notification_tab()
        
        # Tab 6: Tờ khai thuế 01/CNKD (cho nhóm 2 và 3)
        self.tax_return_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tax_return_frame, text="📋 Tờ khai thuế 01/CNKD")
        self.setup_tax_return_tab()
    
    def setup_info_tab(self):
        """Tab thông tin hộ kinh doanh - BỐ CỤC CÂN ĐỐI 2 BÊN (cải tiến căn giữa, tăng độ rộng trường)"""
        
        # Tạo thanh cuộn
        canvas = tk.Canvas(self.info_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.info_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas, style='Card.TFrame')
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # ===== Frame chính với padding =====
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # CẤU HÌNH GRID: 2 CỘT (TRÁI - PHẢI) CÂN ĐỐI
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # ========== CỘT TRÁI: THÔNG TIN CƠ BẢN ==========
        info_container = ttk.LabelFrame(content_frame, text="Thông tin cơ bản", padding=15)
        info_container.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=12)
        
        # Cấu hình grid cho info_container: cột 0 (nhãn) cố định, cột 1 (nhập) co giãn
        info_container.columnconfigure(0, weight=0)
        info_container.columnconfigure(1, weight=1)
        
        # Tiêu đề (nằm trên cả 2 cột)
        title_frame = ttk.Frame(content_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 15))
        ttk.Label(title_frame, text=f"{ICONS['home']} THÔNG TIN HỘ KINH DOANH", font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Vui lòng nhập đầy đủ thông tin chính xác theo giấy phép kinh doanh", font=get_font("label"), foreground="gray").pack()
        
        labels = [
            ("Mã số thuế:", "ma_so_thue", "10 hoặc 13 số, ví dụ: 037072008655"),
            ("Tên hộ kinh doanh:", "ten_ho_kinh_doanh", "Tên theo giấy phép kinh doanh"),
            ("Địa chỉ:", "dia_chi", "Địa chỉ trụ sở chính"),
            ("Số điện thoại:", "so_dien_thoai", "Số điện thoại liên hệ"),
            ("Email:", "email", "Địa chỉ email nhận thông báo thuế"),
            ("Loại hình:", "loai_hinh", "Hộ kinh doanh / Cá nhân kinh doanh"),
            ("Nhóm đối tượng:", "nhom_doi_tuong", "Chọn nhóm dựa trên doanh thu dự kiến"),
            ("Ngày bắt đầu KD:", "ngay_bat_dau_kinh_doanh", "Định dạng: DD/MM/YYYY"),
            ("Ngành nghề KD:", "nganh_nghe_kinh_doanh", "Chọn ngành nghề chính"),
        ]
        
        self.entries = {}
        
        for i, (label_text, field_name, tooltip_text) in enumerate(labels):
            label = ttk.Label(info_container, text=label_text, anchor="e", font=get_font("label"))
            label.grid(row=i, column=0, padx=12, pady=8, sticky="e")
            
            if field_name == "nhom_doi_tuong":
                self.nhom_combobox = ttk.Combobox(info_container, state="readonly", font=get_font("label"))
                nhom_options = Business.get_all_nhom_doi_tuong()
                self.nhom_combobox['values'] = list(nhom_options.values())
                self.nhom_combobox.grid(row=i, column=1, padx=12, pady=8, sticky="ew")
                self.entries[field_name] = self.nhom_combobox
                self.create_tooltip(self.nhom_combobox, tooltip_text)
            elif field_name == "ma_so_thue":
                entry = ttk.Entry(info_container, font=get_font("label"), width=20)
                entry.grid(row=i, column=1, padx=12, pady=8, sticky="ew")
                entry.bind("<FocusOut>", lambda e, f=field_name: self.validate_mst_field())
                self.entries[field_name] = entry
                self.create_tooltip(entry, tooltip_text)
                self.mst_validation_label = ttk.Label(info_container, text="", foreground="red", font=get_font("label"))
                self.mst_validation_label.grid(row=i, column=2, padx=12, pady=8, sticky="w")
            elif field_name == "email":
                entry = ttk.Entry(info_container, font=get_font("label"), width=30)
                entry.grid(row=i, column=1, padx=12, pady=8, sticky="ew")
                entry.bind("<FocusOut>", lambda e: self.validate_email())
                self.entries[field_name] = entry
                self.create_tooltip(entry, tooltip_text)
                self.email_validation_label = ttk.Label(info_container, text="", foreground="red", font=get_font("label"))
                self.email_validation_label.grid(row=i, column=2, padx=12, pady=8, sticky="w")
            elif field_name == "ngay_bat_dau_kinh_doanh":
                entry = ttk.Entry(info_container, font=get_font("label"), width=15)
                entry.grid(row=i, column=1, padx=12, pady=8, sticky="w")
                entry.bind("<FocusOut>", lambda e: self.validate_date())
                self.entries[field_name] = entry
                self.create_tooltip(entry, tooltip_text)
                self.date_validation_label = ttk.Label(info_container, text="", foreground="red", font=get_font("label"))
                self.date_validation_label.grid(row=i, column=2, padx=12, pady=8, sticky="w")
            else:
                # Các trường thông thường: tăng width cho tên hộ, địa chỉ, ngành nghề
                if field_name == "ten_ho_kinh_doanh":
                    width = 50
                elif field_name == "dia_chi":
                    width = 60
                elif field_name == "nganh_nghe_kinh_doanh":
                    width = 50
                else:
                    width = 30
                entry = ttk.Entry(info_container, font=get_font("label"), width=width)
                entry.grid(row=i, column=1, padx=12, pady=8, sticky="ew")
                self.entries[field_name] = entry
                self.create_tooltip(entry, tooltip_text)
        
        # ========== CỘT PHẢI: THÔNG TIN BỔ SUNG & HƯỚNG DẪN ==========
        extra_container = ttk.LabelFrame(content_frame, text="Thông tin bổ sung", padding=15)
        extra_container.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=12)
        
        ttk.Label(extra_container, text="Gợi ý chọn nhóm đối tượng theo doanh thu năm:", font=get_font("label")).grid(row=0, column=0, columnspan=2, pady=12, sticky="w")
        
        group_suggestions = [
            ("📊 Dưới 1 tỷ", "→ Nhóm 1: Không chịu thuế GTGT, không nộp TNCN"),
            ("📈 1 tỷ - 3 tỷ", "→ Nhóm 2: Thuế theo % doanh thu"),
            ("📉 3 tỷ - 50 tỷ", "→ Nhóm 3: Thuế TNCN theo thu nhập tính thuế"),
            ("🏢 Trên 50 tỷ", "→ Nhóm 4: Kê khai theo tháng"),
        ]
        
        for i, (range_text, desc) in enumerate(group_suggestions):
            ttk.Label(extra_container, text=range_text, font=get_font("label")).grid(row=i+1, column=0, padx=10, pady=2, sticky="w")
            ttk.Label(extra_container, text=desc, foreground="blue", font=get_font("label")).grid(row=i+1, column=1, padx=10, pady=2, sticky="w")
        
        # Thêm hướng dẫn nhanh
        ttk.Separator(extra_container, orient='horizontal').grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(extra_container, text="📌 Lưu ý:", foreground="red", font=get_font("bold")).grid(row=6, column=0, columnspan=2, sticky="w", pady=(5,0))
        ttk.Label(extra_container, text="• Mã số thuế phải có 10 hoặc 13 chữ số\n• Email phải đúng định dạng\n• Ngày bắt đầu: DD/MM/YYYY", 
                 wraplength=300, justify="left", font=get_font("label")).grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=12)
        
        # ========== NÚT BẤM (NẰM NGANG DƯỚI CẢ 2 CỘT) ==========
        btn_frame = ttk.Frame(content_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        save_btn = ttk.Button(btn_frame, text=f"{ICONS['save']} Lưu thông tin", 
                             command=self.save_business_info,
                             style="Primary.TButton", width=15)
        save_btn.pack(side="left", padx=10)
        self.create_tooltip(save_btn, "Lưu thông tin hộ kinh doanh vào cơ sở dữ liệu")
        
        refresh_btn = ttk.Button(btn_frame, text=f"{ICONS['refresh']} Làm mới", 
                                command=self.load_data, width=15)
        refresh_btn.pack(side="left", padx=10)
        self.create_tooltip(refresh_btn, "Tải lại thông tin từ cơ sở dữ liệu")
        
        clear_btn = ttk.Button(btn_frame, text="🗑️ Xóa trắng", 
                              command=self.clear_form, width=15)
        clear_btn.pack(side="left", padx=10)
        self.create_tooltip(clear_btn, "Xóa tất cả dữ liệu đang nhập trên form")
        
        # Thanh trạng thái nhỏ trong tab
        self.info_status_label = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.info_status_label.grid(row=3, column=0, columnspan=2, pady=12)
    
    def setup_bank_tab(self):
        """Tab quản lý tài khoản ngân hàng - BỐ CỤC CÂN ĐỐI (cải tiến màu chữ đen)"""
        
        # Tạo thanh cuộn
        canvas = tk.Canvas(self.bank_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.bank_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas, style='Card.TFrame')
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Frame chính với padding
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Tạo frame chứa 2 cột (dùng pack)
        two_columns_frame = ttk.Frame(content_frame)
        two_columns_frame.pack(fill="both", expand=True)
        
        # Đảm bảo style cho LabelFrame có chữ đen
        style = ttk.Style()
        style.configure("Info.TLabelframe.Label", foreground="black", font=get_font("bold"))
        
        # ========== CỘT TRÁI: FORM NHẬP LIỆU ==========
        form_frame = ttk.LabelFrame(two_columns_frame, text=f"{ICONS['add']} Thêm tài khoản mới", 
                                    padding=15, style="Info.TLabelframe")
        form_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=12)
        
        # Cấu hình grid cho form_frame
        form_frame.columnconfigure(0, weight=0)
        form_frame.columnconfigure(1, weight=1)
        
        # Tên ngân hàng
        ttk.Label(form_frame, text="Tên ngân hàng:", anchor="e", font=get_font("label"), foreground="black").grid(row=0, column=0, padx=12, pady=8, sticky="e")
        self.bank_name_entry = ttk.Entry(form_frame, font=get_font("label"))
        self.bank_name_entry.grid(row=0, column=1, padx=12, pady=8, sticky="ew")
        self.create_tooltip(self.bank_name_entry, "Ví dụ: Vietcombank, Techcombank, BIDV, Agribank...")
        
        # Số tài khoản
        ttk.Label(form_frame, text="Số tài khoản:", anchor="e", font=get_font("label"), foreground="black").grid(row=1, column=0, padx=12, pady=8, sticky="e")
        self.account_number_entry = ttk.Entry(form_frame, font=get_font("label"))
        self.account_number_entry.grid(row=1, column=1, padx=12, pady=8, sticky="ew")
        self.create_tooltip(self.account_number_entry, "Số tài khoản ngân hàng (không dấu cách)")
        
        # Số hiệu ví điện tử
        ttk.Label(form_frame, text="Số hiệu ví điện tử:", anchor="e", font=get_font("label"), foreground="black").grid(row=2, column=0, padx=12, pady=8, sticky="e")
        self.vid_entry = ttk.Entry(form_frame, font=get_font("label"))
        self.vid_entry.grid(row=2, column=1, padx=12, pady=8, sticky="ew")
        self.create_tooltip(self.vid_entry, "Số điện thoại đăng ký ví MoMo, ZaloPay, ViettelPay... (nếu có)")
        
        # Tài khoản chính
        self.is_main_var = tk.BooleanVar()
        main_check = ttk.Checkbutton(form_frame, text="Đây là tài khoản chính", 
                                     variable=self.is_main_var)
        main_check.grid(row=3, column=1, padx=12, pady=8, sticky="w")
        self.create_tooltip(main_check, "Chọn nếu đây là tài khoản thanh toán chính của hộ kinh doanh")
        
        # Nút thêm
        add_btn = ttk.Button(form_frame, text=f"{ICONS['add']} Thêm tài khoản", 
                             command=self.add_bank_account, style="Success.TButton")
        add_btn.grid(row=4, column=0, columnspan=2, pady=10)
        self.create_tooltip(add_btn, "Thêm tài khoản ngân hàng vào danh sách đã đăng ký")
        
        # ========== CỘT PHẢI: HƯỚNG DẪN ==========
        guide_frame = ttk.LabelFrame(two_columns_frame, text=f"{ICONS['help']} Hướng dẫn", 
                                     padding=15, style="Info.TLabelframe")
        guide_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=12)
        
        ttk.Label(guide_frame, text="📌 Lưu ý khi đăng ký tài khoản:", font=get_font("bold"), foreground="black").pack(anchor="w", pady=(0, 10))
        
        guide_texts = [
            "• Tên ngân hàng phải viết đầy đủ, không viết tắt",
            "• Số tài khoản chính xác theo hợp đồng mở tại ngân hàng",
            "• Ví điện tử nhập số điện thoại đã đăng ký",
            "• Nên chọn 1 tài khoản chính để thanh toán thuế",
            "• Có thể đăng ký nhiều tài khoản ngân hàng khác nhau"
        ]
        
        for text in guide_texts:
            ttk.Label(guide_frame, text=text, wraplength=350, justify="left", font=get_font("label"), foreground="black").pack(anchor="w", pady=8)
        
        ttk.Separator(guide_frame, orient='horizontal').pack(fill="x", pady=10)
        
        ttk.Label(guide_frame, text="📞 Hỗ trợ:", font=get_font("bold"), foreground="black").pack(anchor="w", pady=(5, 0))
        ttk.Label(guide_frame, text="Nếu gặp lỗi, vui lòng liên hệ bộ phận kỹ thuật để được hỗ trợ.", 
                 wraplength=350, foreground="blue", font=get_font("label")).pack(anchor="w", pady=8)
        
        # ========== PHẦN DƯỚI (CHIẾM 2 CỘT): DANH SÁCH TÀI KHOẢN ==========
        list_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['bank']} Danh sách tài khoản đã đăng ký", 
                                    padding=10, style="Info.TLabelframe")
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview
        columns = ("id", "ten_ngan_hang", "so_tai_khoan", "so_hieu_vi_dien_tu", "la_tai_khoan_chinh")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=14)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("ten_ngan_hang", text="Tên ngân hàng")
        self.tree.heading("so_tai_khoan", text="Số tài khoản")
        self.tree.heading("so_hieu_vi_dien_tu", text="Ví điện tử")
        self.tree.heading("la_tai_khoan_chinh", text="TK chính")
        
        self.tree.column("id", anchor="center", width=60)
        self.tree.column("ten_ngan_hang", width=220, anchor="w")
        self.tree.column("so_tai_khoan", width=180, anchor="center")
        self.tree.column("so_hieu_vi_dien_tu", width=150, anchor="center")
        self.tree.column("la_tai_khoan_chinh", width=80, anchor="center")
        
        # Scrollbar cho treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Tạo frame chứa treeview và scrollbar
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill="both", expand=True)
        
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")
        
        # Nút xóa
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", pady=10)
        
        delete_btn = ttk.Button(btn_frame, text=f"{ICONS['delete']} Xóa tài khoản đã chọn", 
                               command=self.delete_bank_account, style="Warning.TButton")
        delete_btn.pack()
        self.create_tooltip(delete_btn, "Xóa tài khoản ngân hàng đã chọn khỏi danh sách")
        
        # Bind chọn item (GIỮ NGUYÊN)
        self.tree.bind("<<TreeviewSelect>>", self.on_bank_select)
        
        # Label thông báo (GIỮ NGUYÊN)
        self.bank_status_label = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.bank_status_label.pack(pady=12)
    
    def setup_export_tab(self):
        """Tab xuất hồ sơ thuế mẫu 01/BK-STK - BỐ CỤC CÂN ĐỐI (cải tiến màu chữ đen)"""
        # Tạo khung có thanh cuộn
        main_frame = self.create_scrollable_frame(self.export_frame)
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 20))
        ttk.Label(title_frame, text=f"{ICONS['upload']} XUẤT HỒ SƠ THUẾ", font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Mẫu 01/BK-STK - Thông báo số tài khoản/số hiệu ví điện tử", font=get_font("label"), foreground="gray").pack()
        
        # Hạn nộp
        han_frame = ttk.Frame(content_frame)
        han_frame.pack(pady=10)
        han_nop = BankAccountService.get_han_nop()
        han_color = "red" if "quá hạn" in han_nop else "green"
        ttk.Label(han_frame, text=f"⏰ {han_nop}", foreground=han_color, font=get_font("label")).pack()
        
        # Khung kiểm tra
        info_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['info']} Kiểm tra trước khi xuất", 
                                    padding=15, style="Info.TLabelframe")
        info_frame.pack(fill="x", pady=10)
        
        # Đảm bảo tiêu đề LabelFrame có chữ đen
        style = ttk.Style()
        style.configure("Info.TLabelframe.Label", foreground="black", font=get_font("bold"))
        
        self.check_items = {}
        checks = [
            ("business_info", "✓ Thông tin hộ kinh doanh", "Đã nhập mã số thuế, tên, địa chỉ"),
            ("bank_accounts", "✓ Tài khoản ngân hàng", "Có ít nhất 1 tài khoản"),
            ("mst_valid", "✓ Mã số thuế hợp lệ", "MST đúng định dạng 10 hoặc 13 số"),
        ]
        
        for i, (key, text, tooltip) in enumerate(checks):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(info_frame, text=text, variable=var, state="disabled")
            cb.grid(row=i, column=0, padx=10, pady=12, sticky="w")
            self.check_items[key] = {"var": var, "text": text, "tooltip": tooltip}
            self.create_tooltip(cb, tooltip)
        
        # Nút kiểm tra
        check_btn = ttk.Button(info_frame, text="🔍 Kiểm tra lại", 
                              command=self.check_before_export)
        check_btn.grid(row=len(checks), column=0, padx=10, pady=10, sticky="w")
        self.create_tooltip(check_btn, "Kiểm tra lại thông tin trước khi xuất")
        
        # Nút xuất
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=20)
        
        # Style cho nút có chữ đen
        style.configure("BlackPrimary.TButton", font=get_font("button"), foreground="black", background="#2196F3")
        style.configure("Black.TButton", font=get_font("button"), foreground="black")
        
        xml_btn = ttk.Button(btn_frame, text=f"{ICONS['export_xml']} Xuất XML (nộp lên Cổng DVC)", 
                            command=self.export_xml, style="BlackPrimary.TButton", width=35)
        xml_btn.pack(pady=12)
        self.create_tooltip(xml_btn, "Xuất file XML theo chuẩn Tổng cục Thuế để nộp trực tuyến")
        
        html_btn = ttk.Button(btn_frame, text=f"{ICONS['print']} Xem trước & In (HTML)", 
                             command=self.preview_html, style="Black.TButton", width=35)
        html_btn.pack(pady=12)
        self.create_tooltip(html_btn, "Xem trước và in mẫu 01/BK-STK")
        
        # Hướng dẫn
        guide_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['help']} Hướng dẫn nộp hồ sơ", 
                                     padding=15, style="Info.TLabelframe")
        guide_frame.pack(fill="x", pady=10)
        
        guide_steps = [
            "1. Xuất file XML từ nút bên trên",
            "2. Truy cập https://dichvucong.gdt.gov.vn",
            "3. Đăng nhập bằng tài khoản thuế điện tử",
            "4. Chọn 'Nộp hồ sơ' → 'Thông báo số tài khoản (01/BK-STK)'",
            "5. Upload file XML vừa xuất và gửi",
        ]
        
        for step in guide_steps:
            ttk.Label(guide_frame, text=step, foreground="blue", font=get_font("label")).pack(anchor="w", pady=4)
        
        # Status label
        self.export_status_label = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.export_status_label.pack(pady=12)
    
    def setup_revenue_book_tab(self):
        """Tab sổ doanh thu mẫu S1a-HKD - BỐ CỤC CÂN ĐỐI (bảo toàn mọi tính năng)"""
        
        # Tạo thanh cuộn
        canvas = tk.Canvas(self.revenue_book_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.revenue_book_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas, style='Card.TFrame')
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Frame chính với padding
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 15))
        ttk.Label(title_frame, text=f"{ICONS['book']} SỔ DOANH THU BÁN HÀNG HÓA, DỊCH VỤ", font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="(Mẫu số S1a-HKD ban hành kèm theo Thông tư 152/2025/TT-BTC)", font=get_font("label"), foreground="gray").pack()
        
        # Cấu hình grid: 2 cột
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # ========== CỘT TRÁI: CHỌN KỲ KÊ KHAI ==========
        period_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['settings']} Chọn kỳ kê khai", 
                                      padding=15, style="Info.TLabelframe")
        period_frame.pack(fill="both", expand=True, padx=(0, 10), pady=12)
        
        # Cấu hình grid cho period_frame
        period_frame.columnconfigure(0, weight=1)
        period_frame.columnconfigure(1, weight=1)
        period_frame.columnconfigure(2, weight=1)
        period_frame.columnconfigure(3, weight=1)
        
        # Năm
        ttk.Label(period_frame, text="Năm:", anchor="e", font=get_font("label"), foreground="black").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.year_combobox = ttk.Combobox(period_frame, values=[2024, 2025, 2026, 2027, 2028], 
                                          width=12, state="readonly", font=get_font("label"))
        self.year_combobox.set(datetime.now().year)
        self.year_combobox.grid(row=0, column=1, padx=10, pady=8, sticky="w")
        self.create_tooltip(self.year_combobox, "Chọn năm cần xuất sổ doanh thu")
        
        # Kỳ
        ttk.Label(period_frame, text="Kỳ:", anchor="e", font=get_font("label"), foreground="black").grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.period_combobox = ttk.Combobox(period_frame, 
            values=["Quý 1", "Quý 2", "Quý 3", "Quý 4", "Cả năm"], 
            width=12, state="readonly", font=get_font("label"))
        self.period_combobox.set("Quý 1")
        self.period_combobox.grid(row=0, column=3, padx=10, pady=8, sticky="w")
        self.create_tooltip(self.period_combobox, "Chọn quý hoặc cả năm")
        
        # Hiển thị thống kê nhanh
        self.stats_label = ttk.Label(period_frame, text="", foreground="blue", font=get_font("label"))
        self.stats_label.grid(row=1, column=0, columnspan=4, pady=10)
        
        # Nút xem thống kê
        stats_btn = ttk.Button(period_frame, text="📊 Xem thống kê nhanh", 
                              command=self.show_quick_stats)
        stats_btn.grid(row=2, column=0, columnspan=4, pady=12)
        self.create_tooltip(stats_btn, "Xem nhanh tổng doanh thu của kỳ đã chọn")
        
        # ========== CỘT PHẢI: HƯỚNG DẪN ==========
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=12)
        
        # Khung hướng dẫn
        guide_frame = ttk.LabelFrame(right_frame, text=f"{ICONS['help']} Hướng dẫn sử dụng", 
                                     padding=15, style="Info.TLabelframe")
        guide_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(guide_frame, text="📌 Hướng dẫn:", font=get_font("bold"), foreground="black").pack(anchor="w", pady=(0, 5))
        
        guide_texts = [
            "• Sổ doanh thu S1a-HKD dùng để ghi chép doanh thu",
            "• Dữ liệu được tổng hợp từ giao dịch thu và hóa đơn",
            "• Hộ kinh doanh có trách nhiệm lưu giữ sổ này",
            "• Xuất trình khi cơ quan thuế yêu cầu",
        ]
        
        for text in guide_texts:
            ttk.Label(guide_frame, text=text, wraplength=350, justify="left", font=get_font("label"), foreground="black").pack(anchor="w", pady=2)
        
        # Khung lưu ý quan trọng
        note_frame = ttk.LabelFrame(right_frame, text=f"{ICONS['warning']} Lưu ý quan trọng", 
                                    padding=15, style="Info.TLabelframe")
        note_frame.pack(fill="x")
        
        ttk.Label(note_frame, text="⚠️", font=get_font("large_icon"), foreground="black").pack(anchor="w")
        
        note_texts = [
            "Nếu doanh thu dưới 1 tỷ/năm:",
            "  • KHÔNG phải nộp tờ khai thuế theo quý",
            "  • Vẫn phải ghi chép đầy đủ sổ doanh thu (S1a-HKD)",
            "  • Lưu tại hộ kinh doanh, xuất trình khi cơ quan thuế yêu cầu",
        ]
        
        for text in note_texts:
            if "KHÔNG" in text:
                ttk.Label(note_frame, text=text, foreground="red", wraplength=350, font=get_font("label")).pack(anchor="w", pady=1)
            else:
                ttk.Label(note_frame, text=text, foreground="#333", wraplength=350, font=get_font("label")).pack(anchor="w", pady=1)
        
        # ========== PHẦN DƯỚI (CHIẾM 2 CỘT): NÚT XUẤT ==========
        btn_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['export']} Xuất báo cáo", 
                                   padding=15, style="Info.TLabelframe")
        btn_frame.pack(fill="x", pady=10)
        
        # Đảm bảo chữ trong LabelFrame và nút không bị trắng
        style = ttk.Style()
        style.theme_use('clam')  # Dòng này giúp style hoạt động tốt hơn
        style.configure("Info.TLabelframe.Label", foreground="black")
        style.configure("Primary.TButton", font=get_font("button"), foreground="black", background="#2196F3")
        style.configure("Success.TButton", font=get_font("button"), foreground="black", background="#4CAF50")
        
        btn_inner_frame = ttk.Frame(btn_frame)
        btn_inner_frame.pack()
        
        preview_btn = ttk.Button(btn_inner_frame, text=f"{ICONS['print']} Xem trước & In (HTML)", 
                                command=self.preview_revenue_book, 
                                style="Primary.TButton")
        preview_btn.pack(side="left", padx=10, pady=12)
        self.create_tooltip(preview_btn, "Xem trước và in sổ doanh thu")
        
        excel_btn = ttk.Button(btn_inner_frame, text=f"{ICONS['export']} Xuất Excel", 
                              command=self.export_revenue_book_excel, 
                              style="Success.TButton")
        excel_btn.pack(side="left", padx=10, pady=12)
        self.create_tooltip(excel_btn, "Xuất sổ doanh thu ra file Excel")
        
        # Status label
        self.revenue_book_status = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.revenue_book_status.pack(pady=12)
        
        # Cấu hình row weights
        content_frame.rowconfigure(0, weight=0)
        content_frame.rowconfigure(1, weight=0)
        content_frame.rowconfigure(2, weight=0)
    
    def load_data(self):
        """Tải thông tin hộ kinh doanh từ database"""
        try:
            # Reset trạng thái
            if hasattr(self, 'info_status_label'):
                self.info_status_label.config(text="Đang tải dữ liệu...", foreground="blue")
            
            # QUAN TRỌNG: Luôn tải lại từ database (không phụ thuộc vào self.ma_so_thue)
            self.business_info = Business.get_info(self.ma_so_thue) if self.ma_so_thue else Business.get_info()
            
            # Điền dữ liệu vào form
            if self.business_info:
                self.ma_so_thue = self.business_info.get('ma_so_thue')
                logger.info(f"Đã tải thông tin hộ kinh doanh: {self.ma_so_thue}")
                
                field_mapping = {
                    'ma_so_thue': 'ma_so_thue',
                    'ten_ho_kinh_doanh': 'ten_ho_kinh_doanh',
                    'dia_chi': 'dia_chi',
                    'so_dien_thoai': 'so_dien_thoai',
                    'email': 'email',
                    'loai_hinh': 'loai_hinh',
                    'ngay_bat_dau_kinh_doanh': 'ngay_bat_dau_kinh_doanh',
                    'nganh_nghe_kinh_doanh': 'nganh_nghe_kinh_doanh',
                }
                
                for db_field, entry_key in field_mapping.items():
                    if entry_key in self.entries:
                        value = self.business_info.get(db_field, '')
                        if value:
                            try:
                                # Xử lý đặc biệt cho ngày tháng (chuyển YYYY-MM-DD -> DD/MM/YYYY)
                                if db_field == 'ngay_bat_dau_kinh_doanh':
                                    if isinstance(value, str) and '-' in value:
                                        parts = value.split('-')
                                        if len(parts) == 3:
                                            y, m, d = parts
                                            value = f"{int(d):02d}/{int(m):02d}/{int(y)}"
                                
                                if entry_key == "nhom_doi_tuong":
                                    nhom_map = Business.get_all_nhom_doi_tuong()
                                    self.entries[entry_key].set(nhom_map.get(value, value))
                                else:
                                    self.entries[entry_key].delete(0, tk.END)
                                    self.entries[entry_key].insert(0, str(value))
                            except Exception as e:
                                logger.warning(f"Lỗi điền field {entry_key}: {e}")
                
                # Cập nhật thông tin nhóm hiện tại
                nhom = self.business_info.get('nhom_doi_tuong', 'group1')
                nhom_map = Business.get_all_nhom_doi_tuong()
                nhom_text = nhom_map.get(nhom, 'Chưa xác định')
                
                if hasattr(self, 'current_group_label'):
                    self.current_group_label.config(text=f"Nhóm hiện tại: {nhom_text}")
                    self.current_group_label.config(foreground="orange" if nhom == 'group1' else "blue")
                
                # Cập nhật validation
                if hasattr(self, 'validate_mst_field'):
                    self.validate_mst_field()
                if hasattr(self, 'validate_email'):
                    self.validate_email()
                if hasattr(self, 'validate_date'):
                    self.validate_date()
                
                if hasattr(self, 'info_status_label'):
                    self.info_status_label.config(text="✓ Đã tải dữ liệu thành công", foreground="green")
                    self.master.after(3000, lambda: self.info_status_label.config(text=""))
            else:
                if hasattr(self, 'info_status_label'):
                    self.info_status_label.config(text="Chưa có dữ liệu. Vui lòng nhập thông tin.", foreground="orange")
                
                # Reset form
                for entry_key in self.entries:
                    if entry_key != "nhom_doi_tuong":
                        try:
                            self.entries[entry_key].delete(0, tk.END)
                        except Exception:
                            pass
                    else:
                        try:
                            self.entries[entry_key].set('')
                        except Exception:
                            pass
            
            # Tải danh sách tài khoản
            self.load_bank_accounts()
            
            # Làm mới các tab khác
            self.refresh_other_tabs()
            
        except Exception as e:
            logger.error(f"Lỗi tải dữ liệu: {e}")
            if hasattr(self, 'info_status_label'):
                self.info_status_label.config(text=f"❌ Lỗi: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu:\n{str(e)}")
    
    def load_bank_accounts(self):
        """Tải danh sách tài khoản ngân hàng"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.ma_so_thue:
            return
        
        accounts = BankAccountService.get_all_accounts(self.ma_so_thue)
        for acc in accounts:
            self.tree.insert("", "end", values=(
                acc.get('id', ''),
                acc.get('ten_ngan_hang', ''),
                acc.get('so_tai_khoan', ''),
                acc.get('so_hieu_vi_dien_tu', ''),
                "✓" if acc.get('la_tai_khoan_chinh') else ""
            ))
    
    def save_business_info(self):
        """Lưu thông tin hộ kinh doanh (cập nhật có validation)"""
        try:
            # Validation trước khi lưu
            if not self.validate_mst_field():
                messagebox.showerror("Lỗi", "Mã số thuế không hợp lệ.\nVui lòng nhập 10 hoặc 13 số.")
                self.entries['ma_so_thue'].focus()
                return
            
            if not self.validate_email():
                if messagebox.askyesno("Cảnh báo", "Email có vẻ không hợp lệ. Bạn vẫn muốn lưu?"):
                    pass
                else:
                    self.entries['email'].focus()
                    return
            
            if not self.validate_date():
                messagebox.showerror("Lỗi", "Ngày bắt đầu kinh doanh không hợp lệ.\nĐịnh dạng: DD/MM/YYYY")
                self.entries['ngay_bat_dau_kinh_doanh'].focus()
                return
            
            ma_so_thue = self.entries['ma_so_thue'].get().strip()
            if not ma_so_thue:
                messagebox.showerror("Lỗi", "Mã số thuế không được để trống")
                self.entries['ma_so_thue'].focus()
                return
            
            # Lấy nhóm đối tượng
            nhom_text = self.nhom_combobox.get()
            nhom_map = Business.get_all_nhom_doi_tuong()
            nhom_value = None
            for key, val in nhom_map.items():
                if val == nhom_text:
                    nhom_value = key
                    break
            
            Business.save_or_update(
                ma_so_thue=ma_so_thue,
                ten_ho_kinh_doanh=self.entries['ten_ho_kinh_doanh'].get(),
                dia_chi=self.entries['dia_chi'].get(),
                so_dien_thoai=self.entries['so_dien_thoai'].get(),
                email=self.entries['email'].get(),
                loai_hinh=self.entries['loai_hinh'].get() or "Hộ kinh doanh",
                nhom_doi_tuong=nhom_value,
                ngay_bat_dau_kinh_doanh=self.entries['ngay_bat_dau_kinh_doanh'].get(),
                nganh_nghe_kinh_doanh=self.entries['nganh_nghe_kinh_doanh'].get()
            )
            
            self.ma_so_thue = ma_so_thue
            self.info_status_label.config(text="✓ Đã lưu thông tin thành công!", foreground="green")
            self.master.after(3000, lambda: self.info_status_label.config(text=""))
            messagebox.showinfo("Thành công", "Đã lưu thông tin hộ kinh doanh")
            logger.info(f"Đã lưu thông tin hộ kinh doanh: {ma_so_thue}")
            
            # Cập nhật status bar nếu có
            try:
                self.master.update_status("Đã lưu thông tin hộ kinh doanh")
            except Exception:
                pass
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu: {str(e)}")
            logger.error(f"Lỗi lưu thông tin: {e}")
            self.info_status_label.config(text=f"❌ Lỗi: {str(e)[:50]}", foreground="red")
    
    def add_bank_account(self):
        """Thêm tài khoản ngân hàng (cập nhật có validation)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        ten_ngan_hang = self.bank_name_entry.get().strip()
        so_tai_khoan = self.account_number_entry.get().strip()
        
        # Validation
        if not ten_ngan_hang:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên ngân hàng")
            self.bank_name_entry.focus()
            return
        
        if not so_tai_khoan:
            messagebox.showerror("Lỗi", "Vui lòng nhập số tài khoản")
            self.account_number_entry.focus()
            return
        
        success, msg = BankAccountService.add_account(
            ma_so_thue=self.ma_so_thue,
            ten_ngan_hang=ten_ngan_hang,
            so_tai_khoan=so_tai_khoan,
            so_hieu_vi_dien_tu=self.vid_entry.get().strip(),
            la_tai_khoan_chinh=1 if self.is_main_var.get() else 0
        )
        
        if success:
            self.bank_status_label.config(text=f"✓ {msg}", foreground="green")
            self.master.after(3000, lambda: self.bank_status_label.config(text=""))
            # Clear form
            self.bank_name_entry.delete(0, tk.END)
            self.account_number_entry.delete(0, tk.END)
            self.vid_entry.delete(0, tk.END)
            self.is_main_var.set(False)
            # Reload danh sách
            self.load_bank_accounts()
            # Cập nhật checklist ở tab xuất hồ sơ
            if hasattr(self, 'check_before_export'):
                self.check_before_export()
            messagebox.showinfo("Thành công", msg)
        else:
            self.bank_status_label.config(text=f"❌ {msg}", foreground="red")
            messagebox.showerror("Lỗi", msg)
    
    def on_bank_select(self, event):
        """Khi chọn một tài khoản trong treeview"""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0])['values']
            if values:
                self.current_account_id = values[0]
    
    def delete_bank_account(self):
        """Xóa tài khoản ngân hàng đã chọn"""
        if not self.current_account_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn tài khoản cần xóa")
            return
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa tài khoản này?"):
            success = BankAccountService.delete_account(self.current_account_id)
            if success:
                messagebox.showinfo("Thành công", "Đã xóa tài khoản")
                self.current_account_id = None
                self.load_bank_accounts()
            else:
                messagebox.showerror("Lỗi", "Không thể xóa tài khoản")
    
    def export_xml(self):
        """Xuất file XML để nộp lên Cổng DVC"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        accounts = BankAccountService.get_all_accounts(self.ma_so_thue)
        if not accounts:
            messagebox.showerror("Lỗi", "Chưa có tài khoản ngân hàng nào. Vui lòng thêm tài khoản.")
            return
        
        try:
            xml_content = BankAccountService.generate_xml(self.ma_so_thue)
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
                initialfile=f"ThongBaoTaiKhoan_{self.ma_so_thue}.xml"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                messagebox.showinfo("Thành công", f"Đã xuất XML tại:\n{file_path}\n\nHãy upload file này lên Cổng DVC quốc gia.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất XML: {str(e)}")
    
    def preview_html(self):
        """Xem trước và in mẫu 01/BK-STK"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        html_content = BankAccountService.generate_html_preview(self.ma_so_thue)
        if html_content:
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            webbrowser.open(temp_file.name)
            messagebox.showinfo("Hướng dẫn", "Đã mở file xem trước trong trình duyệt.\nBạn có thể in từ trình duyệt (Ctrl+P).")
        else:
            messagebox.showerror("Lỗi", "Không thể tạo HTML preview")
    
    def preview_revenue_book(self):
        """Xem trước và in sổ doanh thu S1a-HKD (THÊM MỚI)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        # Lấy thông tin hộ kinh doanh
        business_info = Business.get_info(self.ma_so_thue)
        if not business_info:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin hộ kinh doanh")
            return
        
        # Lấy năm và kỳ
        nam = int(self.year_combobox.get())
        ky_text = self.period_combobox.get()
        
        # Chuyển đổi kỳ
        ky_map = {
            "Quý 1": "quy1",
            "Quý 2": "quy2", 
            "Quý 3": "quy3",
            "Quý 4": "quy4",
            "Cả năm": "nam"
        }
        ky_value = ky_map.get(ky_text, "quy1")
        
        try:
            html_content = RevenueBookService.generate_html_s1a(
                self.ma_so_thue, ky_value, nam, business_info
            )
            
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            webbrowser.open(temp_file.name)
            messagebox.showinfo("Thành công", f"Đã tạo sổ doanh thu kỳ {ky_text}/{nam}\nĐã mở trong trình duyệt để xem trước và in.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo sổ doanh thu: {str(e)}")
    
    def export_revenue_book_excel(self):
        """Xuất sổ doanh thu S1a-HKD ra Excel (THÊM MỚI)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        business_info = Business.get_info(self.ma_so_thue)
        if not business_info:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin hộ kinh doanh")
            return
        
        nam = int(self.year_combobox.get())
        ky_text = self.period_combobox.get()
        
        ky_map = {
            "Quý 1": "quy1",
            "Quý 2": "quy2",
            "Quý 3": "quy3",
            "Quý 4": "quy4",
            "Cả năm": "nam"
        }
        ky_value = ky_map.get(ky_text, "quy1")
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"So_doanh_thu_S1a_{self.ma_so_thue}_{ky_text}_{nam}.xlsx"
        )
        
        if file_path:
            try:
                RevenueBookService.generate_excel_s1a(
                    self.ma_so_thue, ky_value, nam, business_info, file_path
                )
                messagebox.showinfo("Thành công", f"Đã xuất Excel tại:\n{file_path}")
                
                if messagebox.askyesno("Mở file", "Bạn có muốn mở file vừa xuất không?"):
                    os.startfile(file_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xuất Excel: {str(e)}")
    
    def get_frame(self):
        return self.frame
        
    def setup_notification_tab(self):
        """Tab thông báo doanh thu mẫu 01/TKN-CNKD - BỐ CỤC CÂN ĐỐI (cải tiến căn chỉnh)"""
        
        # Tạo thanh cuộn
        canvas = tk.Canvas(self.notification_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.notification_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas, style='Card.TFrame')
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Frame chính với padding
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 15))
        ttk.Label(title_frame, text=f"{ICONS['notification']} THÔNG BÁO DOANH THU THỰC TẾ PHÁT SINH", font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="(Mẫu số 01/TKN-CNKD ban hành kèm theo Thông tư 18/2026/TT-BTC)", font=get_font("label"), foreground="gray").pack()
        
        # Cấu hình 2 cột cân đối
        two_columns_frame = ttk.Frame(content_frame)
        two_columns_frame.pack(fill="both", expand=True)
        two_columns_frame.columnconfigure(0, weight=1)
        two_columns_frame.columnconfigure(1, weight=1)
        
        # ========== CỘT TRÁI: CHỌN KỲ THÔNG BÁO ==========
        period_frame = ttk.LabelFrame(two_columns_frame, text=f"{ICONS['settings']} Chọn kỳ thông báo", 
                                      padding=15, style="Info.TLabelframe")
        period_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=12)
        
        # Cấu hình grid cho period_frame
        period_frame.columnconfigure(0, weight=0)  # label năm
        period_frame.columnconfigure(1, weight=1)  # combobox năm
        period_frame.columnconfigure(2, weight=0)  # label kỳ
        period_frame.columnconfigure(3, weight=1)  # combobox kỳ
        
        # Dòng 1: Năm và Kỳ
        ttk.Label(period_frame, text="Năm:", anchor="e", font=get_font("label")).grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.notify_year_combobox = ttk.Combobox(period_frame, values=[2025, 2026, 2027, 2028], 
                                                 width=15, state="readonly", font=get_font("label"))
        self.notify_year_combobox.set(datetime.now().year)
        self.notify_year_combobox.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        self.create_tooltip(self.notify_year_combobox, "Chọn năm cần thông báo doanh thu")
        
        ttk.Label(period_frame, text="Kỳ:", anchor="e", font=get_font("label")).grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.notify_period_combobox = ttk.Combobox(period_frame, 
            values=["6 tháng đầu năm", "Cả năm"], 
            width=18, state="readonly", font=get_font("label"))
        self.notify_period_combobox.set("6 tháng đầu năm")
        self.notify_period_combobox.grid(row=0, column=3, padx=10, pady=8, sticky="ew")
        self.create_tooltip(self.notify_period_combobox, "Chọn kỳ thông báo (6 tháng đầu năm hoặc cả năm)")
        
        # Dòng 2: NGUỒN DỮ LIỆU
        ttk.Label(period_frame, text="Nguồn dữ liệu:", anchor="e", font=get_font("label")).grid(row=1, column=0, padx=10, pady=8, sticky="e")
        self.data_source_combo = ttk.Combobox(period_frame, 
            values=["🤖 Tự động (khuyến nghị)", "📄 Chỉ từ hóa đơn", "💰 Chỉ từ giao dịch thu", "🔧 Đã loại bỏ trùng lặp", "⚠️ Cả hai nguồn (có trùng)"], 
            state="readonly", font=get_font("label"))
        self.data_source_combo.set("📄 Từ hóa đơn (khuyến nghị)")
        self.data_source_combo.grid(row=1, column=1, columnspan=3, padx=10, pady=8, sticky="ew")
        self.create_tooltip(self.data_source_combo, 
            "Chọn chế độ tính doanh thu:\n"
            "• 🤖 Tự động: Hệ thống tự chọn nguồn tốt nhất\n"
            "• 📄 Chỉ từ hóa đơn: Chính xác cho kê khai thuế\n"
            "• 💰 Chỉ từ giao dịch thu: Dùng nếu không có hóa đơn\n"
            "• 🔧 Đã loại bỏ trùng lặp: Tốt nhất khi có cả hai nguồn\n"
            "• ⚠️ Cả hai nguồn: Sẽ bị trùng lặp, không khuyến nghị")
        
        # Dòng 3: Hạn nộp
        self.han_nop_label = ttk.Label(period_frame, text="", foreground="red", font=get_font("label"))
        self.han_nop_label.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Dòng 4: Thống kê nhanh
        self.notify_stats_label = ttk.Label(period_frame, text="", foreground="blue", wraplength=450, font=get_font("label"))
        self.notify_stats_label.grid(row=3, column=0, columnspan=4, pady=12)
        
        # Dòng 5: Nút xem thống kê
        stats_btn = ttk.Button(period_frame, text="📊 Xem thống kê doanh thu", 
                              command=self.show_notify_stats)
        stats_btn.grid(row=4, column=0, columnspan=4, pady=12)
        self.create_tooltip(stats_btn, "Xem nhanh tổng doanh thu của kỳ đã chọn theo nguồn dữ liệu")
        
        # Cập nhật hạn nộp khi thay đổi năm/kỳ
        def update_han_nop(*args):
            from services.revenue_notification_service import RevenueNotificationService
            nam = int(self.notify_year_combobox.get())
            ky = self.notify_period_combobox.get()
            ky_value = "6_thang_dau" if ky == "6 tháng đầu năm" else "ca_nam"
            han_nop = RevenueNotificationService.get_han_nop(ky_value, nam)
            try:
                d, m, y = han_nop.split('/')
                han_date = datetime(int(y), int(m), int(d))
                if datetime.now() > han_date:
                    self.han_nop_label.config(text=f"⚠️ ĐÃ QUÁ HẠN! Hạn nộp: {han_nop}", foreground="red")
                else:
                    self.han_nop_label.config(text=f"⏰ Hạn nộp: {han_nop}", foreground="orange")
            except Exception:
                self.han_nop_label.config(text=f"⏰ Hạn nộp: {han_nop}", foreground="orange")
        
        self.notify_year_combobox.bind("<<ComboboxSelected>>", update_han_nop)
        self.notify_period_combobox.bind("<<ComboboxSelected>>", update_han_nop)
        update_han_nop()
        
        # ========== CỘT PHẢI: HƯỚNG DẪN ==========
        right_container = ttk.Frame(two_columns_frame)
        right_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=12)
        right_container.columnconfigure(0, weight=1)
        
        # Khung hướng dẫn
        guide_frame = ttk.LabelFrame(right_container, text=f"{ICONS['help']} Hướng dẫn sử dụng", 
                                     padding=15, style="Info.TLabelframe")
        guide_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(guide_frame, text="📌 Hướng dẫn:", font=get_font("bold")).pack(anchor="w", pady=(0, 5))
        
        guide_texts = [
            "• Mẫu 01/TKN-CNKD dùng cho hộ kinh doanh",
            "• Doanh thu từ 1 tỷ đồng trở xuống",
            "• Thời hạn nộp: 31/01 năm sau (cả năm)",
            "• Hoặc 31/07 (6 tháng đầu năm)",
        ]
        
        for text in guide_texts:
            ttk.Label(guide_frame, text=text, wraplength=350, justify="left", font=get_font("label")).pack(anchor="w", pady=2)
        
        # Khung lưu ý quan trọng
        note_frame = ttk.LabelFrame(right_container, text=f"{ICONS['warning']} Lưu ý quan trọng", 
                                    padding=15, style="Info.TLabelframe")
        note_frame.pack(fill="x")
        
        ttk.Label(note_frame, text="⚠️", font=get_font("large_icon")).pack(anchor="w")
        
        note_texts = [
            "Nếu doanh thu thực tế vượt 1 tỷ:",
            "  • Quý tiếp theo phải chuyển sang mẫu 01/CNKD",
            "",
            "Khuyến nghị về nguồn dữ liệu:",
            "  • Nên chọn 'Từ hóa đơn' để tránh trùng lặp",
            "  • Chỉ dùng 'Cả hai nguồn' nếu không tạo hóa đơn",
        ]
        
        for text in note_texts:
            if "Khuyến nghị" in text:
                ttk.Label(note_frame, text=text, foreground="blue", font=get_font("label")).pack(anchor="w", pady=(5, 0))
            elif "vượt" in text or "phải chuyển" in text:
                ttk.Label(note_frame, text=text, foreground="red", wraplength=350, font=get_font("label")).pack(anchor="w", pady=1)
            elif text == "":
                continue
            else:
                ttk.Label(note_frame, text=text, foreground="#333", wraplength=350, font=get_font("label")).pack(anchor="w", pady=1)
        
        # ========== PHẦN DƯỚI (CHIẾM 2 CỘT): XUẤT BÁO CÁO ==========
        btn_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['print']} Xuất báo cáo", 
                                   padding=15, style="Info.TLabelframe")
        btn_frame.pack(fill="x", pady=10)
        
        # Tạo style riêng cho nút có chữ đen
        style = ttk.Style()
        style.configure("Notif.TButton", font=get_font("button"), foreground="black", background="#2196F3")
        
        preview_btn = ttk.Button(btn_frame, text=f"{ICONS['print']} Xem trước & In (HTML)", 
                                command=self.preview_notification, 
                                style="Notif.TButton")
        preview_btn.pack(pady=10)
        self.create_tooltip(preview_btn, "Xem trước và in thông báo doanh thu")
        
        # Status label
        self.notify_status_label = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.notify_status_label.pack(pady=12)
        
    def preview_notification(self):
        """Xem trước thông báo doanh thu 01/TKN-CNKD (có chọn nguồn dữ liệu)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        from services.revenue_notification_service import RevenueNotificationService
        
        business_info = Business.get_info(self.ma_so_thue)
        if not business_info:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin hộ kinh doanh")
            return
        
        nam = int(self.notify_year_combobox.get())
        ky_text = self.notify_period_combobox.get()
        ky_value = "6_thang_dau" if ky_text == "6 tháng đầu năm" else "ca_nam"
        
        # Lấy nguồn dữ liệu từ combobox
        source_text = self.data_source_combo.get()
        if "Từ hóa đơn" in source_text:
            source = "invoices"
            source_display = "hóa đơn"
        elif "Từ giao dịch thu" in source_text:
            source = "transactions"
            source_display = "giao dịch thu"
        else:
            source = "both"
            source_display = "cả hai nguồn"
        
        try:
            html_content = RevenueNotificationService.generate_html_tkn(
                self.ma_so_thue, ky_value, nam, business_info, source
            )
            
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            webbrowser.open(temp_file.name)
            self.notify_status_label.config(text="✓ Đã tạo thông báo thành công", foreground="green")
            self.master.after(3000, lambda: self.notify_status_label.config(text=""))
            messagebox.showinfo("Thành công", 
                f"Đã tạo thông báo doanh thu kỳ {ky_text}/{nam}\n"
                f"Nguồn dữ liệu: {source_display}\n"
                f"Đã mở trong trình duyệt để xem trước và in.")
        except Exception as e:
            self.notify_status_label.config(text=f"❌ Lỗi: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Lỗi", f"Không thể tạo thông báo: {str(e)}")
            
    def setup_tax_return_tab(self):
        """Tab tờ khai thuế mẫu 01/CNKD - BỐ CỤC CÂN ĐỐI (cải tiến căn giữa, tăng độ rộng)"""
        
        # Tạo thanh cuộn
        canvas = tk.Canvas(self.tax_return_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tax_return_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas, style='Card.TFrame')
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        
        main_frame.bind("<Configure>", on_configure)
        canvas.bind("<MouseWheel>", on_mousewheel)
        
        # Frame chính với padding
        content_frame = ttk.Frame(main_frame, padding=20)
        content_frame.pack(fill="both", expand=True)
        
        # Tiêu đề
        title_frame = ttk.Frame(content_frame)
        title_frame.pack(pady=(0, 15))
        ttk.Label(title_frame, text=f"{ICONS['tax_return']} TỜ KHAI THUẾ ĐỐI VỚI HỘ KINH DOANH", font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="(Mẫu số 01/CNKD ban hành kèm theo Thông tư 18/2026/TT-BTC)", font=get_font("label"), foreground="gray").pack()
        
        # Cấu hình 2 cột cân đối
        two_columns_frame = ttk.Frame(content_frame)
        two_columns_frame.pack(fill="both", expand=True)
        two_columns_frame.columnconfigure(0, weight=1)
        two_columns_frame.columnconfigure(1, weight=1)
        
        # ========== CỘT TRÁI: CẢNH BÁO + CHỌN KỲ ==========
        left_frame = ttk.Frame(two_columns_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=12)
        left_frame.columnconfigure(0, weight=1)
        
        # Cảnh báo đối tượng sử dụng
        warning_frame = ttk.LabelFrame(left_frame, text=f"{ICONS['warning']} LƯU Ý QUAN TRỌNG", 
                                       padding=15, style="Info.TLabelframe")
        warning_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(warning_frame, 
                 text="⚠️ Mẫu này chỉ dành cho hộ kinh doanh có doanh thu TRÊN 1 tỷ đồng/năm!\n"
                      "Nếu doanh thu dưới 1 tỷ đồng, vui lòng sử dụng tab '📢 Thông báo doanh thu'.",
                 foreground="red", justify="center", font=get_font("label")).pack()
        
        # Hiển thị nhóm hiện tại
        self.current_group_label = ttk.Label(warning_frame, text="", foreground="blue", font=get_font("label"))
        self.current_group_label.pack(pady=12)
        
        # Khung chọn kỳ
        period_frame = ttk.LabelFrame(left_frame, text=f"{ICONS['settings']} Chọn kỳ khai thuế", 
                                      padding=15, style="Info.TLabelframe")
        period_frame.pack(fill="x")
        
        # Cấu hình grid cho period_frame (4 cột)
        period_frame.columnconfigure(0, weight=0)
        period_frame.columnconfigure(1, weight=1)
        period_frame.columnconfigure(2, weight=0)
        period_frame.columnconfigure(3, weight=1)
        
        # Năm
        ttk.Label(period_frame, text="Năm:", anchor="e", font=get_font("label")).grid(row=0, column=0, padx=10, pady=8, sticky="e")
        self.tax_return_year = ttk.Combobox(period_frame, values=[2025, 2026, 2027, 2028], 
                                            width=15, state="readonly", font=get_font("label"))
        self.tax_return_year.set(datetime.now().year)
        self.tax_return_year.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        self.create_tooltip(self.tax_return_year, "Chọn năm khai thuế")
        
        # Quý
        ttk.Label(period_frame, text="Quý:", anchor="e", font=get_font("label")).grid(row=0, column=2, padx=10, pady=8, sticky="e")
        self.tax_return_quarter = ttk.Combobox(period_frame, values=[1, 2, 3, 4], 
                                               width=10, state="readonly", font=get_font("label"))
        self.tax_return_quarter.set(get_current_quarter())
        self.tax_return_quarter.grid(row=0, column=3, padx=10, pady=8, sticky="ew")
        self.create_tooltip(self.tax_return_quarter, "Chọn quý khai thuế")
        
        # Hiển thị hạn nộp
        self.tax_return_han_label = ttk.Label(period_frame, text="", foreground="orange", font=get_font("label"))
        self.tax_return_han_label.grid(row=1, column=0, columnspan=4, pady=10)
        
        # Hiển thị thống kê nhanh
        self.tax_return_stats_label = ttk.Label(period_frame, text="", foreground="blue", wraplength=400, font=get_font("label"))
        self.tax_return_stats_label.grid(row=2, column=0, columnspan=4, pady=12)
        
        # Nút xem thống kê
        stats_btn = ttk.Button(period_frame, text="📊 Xem thống kê doanh thu & chi phí", 
                              command=self.show_tax_return_stats)
        stats_btn.grid(row=3, column=0, columnspan=4, pady=12)
        self.create_tooltip(stats_btn, "Xem nhanh doanh thu và chi phí của quý đã chọn")
        
        # Cập nhật hạn nộp
        def update_tax_return_han(*args):
            from services.business_tax_return_service import BusinessTaxReturnService
            nam = int(self.tax_return_year.get())
            quy = int(self.tax_return_quarter.get())
            han_nop = BusinessTaxReturnService.get_han_nop(quy, nam)
            try:
                d, m, y = han_nop.split('/')
                han_date = datetime(int(y), int(m), int(d))
                if datetime.now() > han_date:
                    self.tax_return_han_label.config(text=f"⚠️ ĐÃ QUÁ HẠN! Hạn nộp: {han_nop}", foreground="red")
                else:
                    self.tax_return_han_label.config(text=f"⏰ Hạn nộp tờ khai: {han_nop}", foreground="orange")
            except Exception:
                self.tax_return_han_label.config(text=f"⏰ Hạn nộp tờ khai: {han_nop}", foreground="orange")
        
        self.tax_return_year.bind("<<ComboboxSelected>>", update_tax_return_han)
        self.tax_return_quarter.bind("<<ComboboxSelected>>", update_tax_return_han)
        update_tax_return_han()
        
        # ========== CỘT PHẢI: HƯỚNG DẪN + TÍNH THỬ THUẾ ==========
        right_frame = ttk.Frame(two_columns_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=12)
        right_frame.columnconfigure(0, weight=1)
        
        # Khung hướng dẫn
        guide_frame = ttk.LabelFrame(right_frame, text=f"{ICONS['help']} Hướng dẫn sử dụng", 
                                     padding=15, style="Info.TLabelframe")
        guide_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(guide_frame, text="📌 Hướng dẫn:", font=get_font("bold")).pack(anchor="w", pady=(0, 5))
        
        guide_texts = [
            "• Mẫu 01/CNKD dùng cho hộ kinh doanh",
            "• Doanh thu TRÊN 1 tỷ đồng/năm",
            "• Thời hạn nộp: Ngày cuối tháng đầu quý sau",
            "  - Q1: 30/04 | Q2: 31/07",
            "  - Q3: 30/10 | Q4: 31/01",
        ]
        
        for text in guide_texts:
            if text.startswith("  -"):
                ttk.Label(guide_frame, text=text, wraplength=350, justify="left", foreground="#555", font=get_font("label")).pack(anchor="w", padx=15)
            else:
                ttk.Label(guide_frame, text=text, wraplength=350, justify="left", font=get_font("label")).pack(anchor="w", pady=1)
        
        # Khung tính thuế thử
        calc_frame = ttk.LabelFrame(right_frame, text=f"{ICONS['info']} Tính thử thuế", 
                                    padding=15, style="Info.TLabelframe")
        calc_frame.pack(fill="x")
        calc_frame.columnconfigure(0, weight=0)
        calc_frame.columnconfigure(1, weight=1)
        
        ttk.Label(calc_frame, text="Nhập doanh thu thử nghiệm:", anchor="e", font=get_font("label"), foreground="black").grid(row=0, column=0, padx=12, pady=12, sticky="e")
        self.test_revenue_entry = ttk.Entry(calc_frame, font=get_font("label"), width=25)
        self.test_revenue_entry.grid(row=0, column=1, padx=12, pady=12, sticky="ew")
        self.create_tooltip(self.test_revenue_entry, "Nhập số tiền để tính thử thuế")
        
        ttk.Label(calc_frame, text="Chọn ngành nghề:", anchor="e", font=get_font("label"), foreground="black").grid(row=1, column=0, padx=12, pady=12, sticky="e")
        self.test_industry_combo = ttk.Combobox(calc_frame, 
            values=["Phân phối, cung cấp hàng hóa", "Dịch vụ, xây dựng không bao thầu",
                    "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa", "Hoạt động kinh doanh khác"],
            state="readonly", font=get_font("label"))
        self.test_industry_combo.set("Phân phối, cung cấp hàng hóa")
        self.test_industry_combo.grid(row=1, column=1, padx=12, pady=12, sticky="ew")
        
        # Tạo style cho nút có chữ đen
        style = ttk.Style()
        style.configure("Calc.TButton", font=get_font("button"), foreground="black", background="#4CAF50")
        style.configure("Preview.TButton", font=get_font("button"), foreground="black", background="#2196F3")
        
        calc_btn = ttk.Button(calc_frame, text="🧮 Tính thử thuế", 
                             command=self.calculate_test_tax, style="Calc.TButton")
        calc_btn.grid(row=2, column=0, columnspan=2, pady=10)
        self.create_tooltip(calc_btn, "Tính thử số thuế phải nộp dựa trên doanh thu nhập vào")
        
        self.test_result_label = ttk.Label(calc_frame, text="", foreground="green", wraplength=350, font=get_font("label"))
        self.test_result_label.grid(row=3, column=0, columnspan=2, pady=12)
        
        # Nút xuất báo cáo
        btn_frame = ttk.LabelFrame(content_frame, text=f"{ICONS['print']} Xuất báo cáo", 
                                   padding=15, style="Info.TLabelframe")
        btn_frame.pack(fill="x", pady=10)
        preview_btn = ttk.Button(btn_frame, text=f"{ICONS['print']} Xem trước & In (HTML)", 
                                command=self.preview_tax_return, style="Preview.TButton")
        preview_btn.pack(pady=10)
        self.create_tooltip(preview_btn, "Xem trước và in tờ khai thuế 01/CNKD")
        
        self.tax_return_status = ttk.Label(content_frame, text="", foreground="green", font=get_font("label"))
        self.tax_return_status.pack(pady=12)
        
    def preview_tax_return(self):
        """Xem trước tờ khai thuế 01/CNKD (cập nhật)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        from services.business_tax_return_service import BusinessTaxReturnService
        
        business_info = Business.get_info(self.ma_so_thue)
        if not business_info:
            messagebox.showerror("Lỗi", "Không tìm thấy thông tin hộ kinh doanh")
            return
        
        # Kiểm tra nhóm đối tượng
        nhom = business_info.get('nhom_doi_tuong', 'group1')
        if nhom == 'group1':
            messagebox.showwarning("Cảnh báo", 
                "Hộ kinh doanh của bạn đang ở nhóm 1 (doanh thu <1 tỷ).\n"
                "Mẫu 01/CNKD không áp dụng cho nhóm này.\n"
                "Vui lòng sử dụng tab '📢 Thông báo doanh thu'.")
            return
        
        nam = int(self.tax_return_year.get())
        quy = int(self.tax_return_quarter.get())
        
        try:
            html_content = BusinessTaxReturnService.generate_html_cnkd(
                self.ma_so_thue, quy, nam, business_info
            )
            
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
            temp_file.write(html_content)
            temp_file.close()
            
            webbrowser.open(temp_file.name)
            self.tax_return_status.config(text="✓ Đã tạo tờ khai thuế thành công", foreground="green")
            self.master.after(3000, lambda: self.tax_return_status.config(text=""))
            messagebox.showinfo("Thành công", f"Đã tạo tờ khai thuế Quý {quy}/{nam}\nĐã mở trong trình duyệt để xem trước và in.")
        except Exception as e:
            self.tax_return_status.config(text=f"❌ Lỗi: {str(e)[:50]}", foreground="red")
            messagebox.showerror("Lỗi", f"Không thể tạo tờ khai: {str(e)}")
            
    def create_tooltip(self, widget, text):
        """Tạo tooltip cho widget"""
        def show_tooltip(event):
            if hasattr(self, 'current_tooltip'):
                try:
                    self.current_tooltip.destroy()
                except Exception:
                    pass
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+25}")
            label = ttk.Label(tooltip, text=text, background="#FFFFCC", 
                             relief="solid", borderwidth=1, padding=5)
            label.pack()
            self.current_tooltip = tooltip
            widget.after(3000, lambda: self.hide_tooltip(tooltip))
        
        def hide_tooltip(event):
            if hasattr(self, 'current_tooltip'):
                try:
                    self.current_tooltip.destroy()
                except Exception:
                    pass
                self.current_tooltip = None
        
        def hide_tooltip_timeout(tooltip):
            try:
                tooltip.destroy()
            except Exception:
                pass
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def hide_tooltip(self, tooltip):
        """Ẩn tooltip"""
        try:
            tooltip.destroy()
        except Exception:
            pass

    def validate_mst_field(self):
        """Kiểm tra mã số thuế"""
        mst = self.entries['ma_so_thue'].get().strip()
        if mst and not validate_mst(mst):
            self.mst_validation_label.config(text="⚠️ MST không hợp lệ (10 hoặc 13 số)")
            return False
        else:
            self.mst_validation_label.config(text="✓ Hợp lệ" if mst else "")
            return True

    def validate_email(self):
        """Kiểm tra email"""
        email = self.entries['email'].get().strip()
        if email and '@' not in email:
            self.email_validation_label.config(text="⚠️ Email không hợp lệ (thiếu @)")
            return False
        elif email and '.' not in email.split('@')[-1]:
            self.email_validation_label.config(text="⚠️ Email không hợp lệ (thiếu tên miền)")
            return False
        else:
            self.email_validation_label.config(text="✓ Hợp lệ" if email else "")
            return True

    def validate_date(self):
        """Kiểm tra ngày tháng"""
        date_str = self.entries['ngay_bat_dau_kinh_doanh'].get().strip()
        if date_str:
            try:
                d, m, y = date_str.split('/')
                datetime(int(y), int(m), int(d))
                self.date_validation_label.config(text="✓ Hợp lệ")
                return True
            except Exception:
                self.date_validation_label.config(text="⚠️ Sai định dạng (DD/MM/YYYY)")
                return False
        else:
            self.date_validation_label.config(text="")
            return True

    def clear_form(self):
        """Xóa trắng form"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa trắng form?"):
            for field_name, entry in self.entries.items():
                if hasattr(entry, 'delete'):
                    entry.delete(0, tk.END)
                elif hasattr(entry, 'set'):
                    entry.set('')
            self.info_status_label.config(text="Đã xóa trắng form", foreground="blue")
            self.master.after(3000, lambda: self.info_status_label.config(text=""))
            
    def check_before_export(self):
        """Kiểm tra thông tin trước khi xuất"""
        from utils.helpers import validate_mst
        
        ok_count = 0
        total = len(self.check_items)
        
        # Kiểm tra thông tin hộ kinh doanh
        business = Business.get_info(self.ma_so_thue) if self.ma_so_thue else None
        if business and business.get('ten_ho_kinh_doanh'):
            self.check_items["business_info"]["var"].set(True)
            ok_count += 1
        else:
            self.check_items["business_info"]["var"].set(False)
        
        # Kiểm tra tài khoản ngân hàng
        accounts = BankAccountService.get_all_accounts(self.ma_so_thue) if self.ma_so_thue else []
        if accounts:
            self.check_items["bank_accounts"]["var"].set(True)
            ok_count += 1
        else:
            self.check_items["bank_accounts"]["var"].set(False)
        
        # Kiểm tra MST hợp lệ
        if self.ma_so_thue and validate_mst(self.ma_so_thue):
            self.check_items["mst_valid"]["var"].set(True)
            ok_count += 1
        else:
            self.check_items["mst_valid"]["var"].set(False)
        
        if ok_count == total:
            self.export_status_label.config(text="✓ Tất cả thông tin đã sẵn sàng! Bạn có thể xuất hồ sơ.", foreground="green")
            messagebox.showinfo("Kiểm tra thành công", "Tất cả thông tin đã sẵn sàng!\nBạn có thể xuất hồ sơ.")
        else:
            self.export_status_label.config(text=f"⚠️ Còn {total - ok_count} mục chưa sẵn sàng. Vui lòng kiểm tra lại.", foreground="red")
            messagebox.showwarning("Thiếu thông tin", f"Còn {total - ok_count} mục chưa sẵn sàng.\nVui lòng kiểm tra lại.")
            
    def show_quick_stats(self):
        """Hiển thị thống kê nhanh doanh thu"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        from services.revenue_book_service import RevenueBookService
        
        nam = int(self.year_combobox.get())
        ky_text = self.period_combobox.get()
        
        ky_map = {"Quý 1": "quy1", "Quý 2": "quy2", "Quý 3": "quy3", "Quý 4": "quy4", "Cả năm": "nam"}
        ky_value = ky_map.get(ky_text, "quy1")
        
        data = RevenueBookService.get_revenue_data(self.ma_so_thue, ky_value, nam)
        
        self.stats_label.config(
            text=f"📊 {data['ky_ke_khai']}: {data['record_count']} giao dịch | "
                 f"Tổng doanh thu: {data['total_revenue']:,.0f} VNĐ"
        )
        
        # Cảnh báo nếu doanh thu vượt 1 tỷ
        if data['total_revenue'] > 1000_000_000:
            messagebox.showwarning("Cảnh báo doanh thu", 
                f"Doanh thu kỳ {ky_text}/{nam} là {data['total_revenue']:,.0f} VNĐ\n"
                f"Đã vượt ngưỡng 1 tỷ đồng.\n"
                f"Quý tiếp theo bạn phải chuyển sang kê khai thuế theo mẫu 01/CNKD.")
                
    def show_notify_stats(self):
        """Hiển thị thống kê doanh thu (thông minh)"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        from services.revenue_notification_service import RevenueNotificationService
        
        nam = int(self.notify_year_combobox.get())
        ky_text = self.notify_period_combobox.get()
        ky_value = "6_thang_dau" if ky_text == "6 tháng đầu năm" else "ca_nam"
        
        # Lấy chế độ từ combobox
        source_text = self.data_source_combo.get()
        if "Tự động" in source_text:
            source = "auto"
        elif "Chỉ từ hóa đơn" in source_text:
            source = "invoices"
        elif "Chỉ từ giao dịch thu" in source_text:
            source = "transactions"
        elif "Đã loại bỏ trùng lặp" in source_text:
            source = "deduplicated"
        else:
            source = "both"
        
        data = RevenueNotificationService.get_revenue_by_period(self.ma_so_thue, ky_value, nam, source)
        
        # Xây dựng thông báo
        status_text = f"📊 {data['ky_thong_bao']}: {data['total_revenue']:,.0f} VNĐ"
        status_text += f"\n📌 Chế độ: {data['note']}"
        
        if data['has_duplicates']:
            status_text += f"\n⚠️ Phát hiện {data['duplicate_count']} giao dịch trùng lặp ({data['duplicate_amount']:,.0f} VNĐ)"
        
        self.notify_stats_label.config(text=status_text, foreground="blue")
        
        # Hiển thị hộp thoại chi tiết
        detail_msg = f"""
        === THỐNG KÊ DOANH THU ===
        
        Kỳ: {data['ky_thong_bao']}
        
        📊 Chi tiết:
        - Từ giao dịch thu: {data['transaction_revenue']:,.0f} VNĐ
        - Từ hóa đơn: {data['invoice_revenue']:,.0f} VNĐ
        {'- Trùng lặp: ' + f"{data['duplicate_amount']:,.0f} VNĐ" if data['has_duplicates'] else ''}
        {'-' * 30}
        - TỔNG DOANH THU: {data['total_revenue']:,.0f} VNĐ
        
        💡 Khuyến nghị: {data['recommendation']}
        """
        
        # Sửa lại đoạn code của Thầy:
        if data.get('vuot_1 tỷ', False):
            # Dùng .get() cho cả 'canh_bao' để chắc chắn không bao giờ bị sập app
            canh_bao_msg = data.get('canh_bao', 'Vui lòng kiểm tra lại ngưỡng doanh thu.')
            detail_msg += f"\n\n⚠️ CẢNH BÁO: Doanh thu vượt 1 tỷ đồng!\n{canh_bao_msg}"
            messagebox.showwarning("Cảnh báo doanh thu", detail_msg)
        else:
            messagebox.showinfo("Thống kê doanh thu", detail_msg)
                
    def show_tax_return_stats(self):
        """Hiển thị thống kê doanh thu và chi phí cho tờ khai thuế"""
        if not self.ma_so_thue:
            messagebox.showerror("Lỗi", "Vui lòng lưu thông tin hộ kinh doanh trước")
            return
        
        from services.business_tax_return_service import BusinessTaxReturnService
        
        nam = int(self.tax_return_year.get())
        quy = int(self.tax_return_quarter.get())
        
        revenue = BusinessTaxReturnService.get_quarter_revenue(self.ma_so_thue, quy, nam)
        expense = BusinessTaxReturnService.get_quarter_expense(self.ma_so_thue, quy, nam)
        profit = revenue - expense
        
        self.tax_return_stats_label.config(
            text=f"📊 Quý {quy}/{nam}: Doanh thu {revenue:,.0f} VNĐ | "
                 f"Chi phí {expense:,.0f} VNĐ | Lợi nhuận {profit:,.0f} VNĐ"
        )
        
        # Cập nhật thông tin nhóm hiện tại
        if self.business_info:
            nhom = self.business_info.get('nhom_doi_tuong', 'group1')
            nhom_map = Business.get_all_nhom_doi_tuong()
            nhom_text = nhom_map.get(nhom, 'Chưa xác định')
            self.current_group_label.config(text=f"Nhóm hiện tại: {nhom_text}")
            
    def calculate_test_tax(self):
        """Tính thử thuế dựa trên doanh thu nhập vào"""
        from services.business_tax_return_service import BusinessTaxReturnService
        from services.tax_service import TaxService
        
        try:
            test_revenue = float(self.test_revenue_entry.get().replace(',', ''))
        except Exception:
            messagebox.showerror("Lỗi", "Vui lòng nhập doanh thu hợp lệ (số)")
            return
        
        industry = self.test_industry_combo.get()
        nam = datetime.now().year
        
        if test_revenue <= 1000_000_000:
            # Nhóm 1: Miễn thuế
            self.test_result_label.config(
                text=f"💰 Doanh thu {test_revenue:,.0f} VNĐ < 1 tỷ → Được miễn thuế GTGT và TNCN",
                foreground="green"
            )
        elif test_revenue <= 3_000_000_000:
            # Nhóm 2
            tax = BusinessTaxReturnService.calculate_tax_for_group2(test_revenue, industry, nam)
            self.test_result_label.config(
                text=f"💰 Thuế GTGT: {tax['vat']:,.0f} VNĐ ({tax['vat_rate']:.1f}%) | "
                     f"Thuế TNCN: {tax['pit']:,.0f} VNĐ ({tax['pit_rate']:.1f}%) | "
                     f"Tổng: {tax['total']:,.0f} VNĐ",
                foreground="blue"
            )
        else:
            # Nhóm 3 (giả định chi phí = 70% doanh thu)
            estimated_expense = test_revenue * 0.7
            tax = BusinessTaxReturnService.calculate_tax_for_group3(test_revenue, estimated_expense, industry, nam)
            self.test_result_label.config(
                text=f"💰 Thuế GTGT: {tax['vat']:,.0f} VNĐ ({tax['vat_rate']:.1f}%) | "
                     f"Thuế TNCN: {tax['pit']:,.0f} VNĐ ({tax['pit_rate']:.1f}%) | "
                     f"Tổng: {tax['total']:,.0f} VNĐ\n"
                     f"(Giả định chi phí = 70% doanh thu, thu nhập tính thuế: {tax['taxable_income']:,.0f} VNĐ)",
                foreground="blue"
            )
    def refresh_other_tabs(self):
        """Làm mới dữ liệu trên các tab khác sau khi tải thông tin"""
        try:
            # Làm mới checklist ở tab xuất hồ sơ
            if hasattr(self, 'check_before_export'):
                self.master.after(100, self.check_before_export)
            
            # Làm mới thống kê ở tab sổ doanh thu
            if hasattr(self, 'year_combobox') and hasattr(self, 'period_combobox'):
                self.master.after(200, self.show_quick_stats)
            
            # Làm mới thống kê ở tab thông báo doanh thu
            if hasattr(self, 'notify_year_combobox') and hasattr(self, 'notify_period_combobox'):
                self.master.after(300, self.show_notify_stats)
            
            # Làm mới thống kê ở tab tờ khai thuế
            if hasattr(self, 'tax_return_year') and hasattr(self, 'tax_return_quarter'):
                self.master.after(400, self.show_tax_return_stats)
                
            logger.info("Đã làm mới các tab khác")
        except Exception as e:
            logger.warning(f"Lỗi khi làm mới tab khác: {e}")
            
    def load_bank_accounts(self):
        """Tải danh sách tài khoản ngân hàng (cập nhật có xử lý lỗi)"""
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not self.ma_so_thue:
            if hasattr(self, 'bank_status_label'):
                self.bank_status_label.config(text="Chưa có mã số thuế. Vui lòng lưu thông tin trước.", foreground="orange")
            return
        
        try:
            accounts = BankAccountService.get_all_accounts(self.ma_so_thue)
            
            if accounts:
                for acc in accounts:
                    self.tree.insert("", "end", values=(
                        acc.get('id', ''),
                        acc.get('ten_ngan_hang', ''),
                        acc.get('so_tai_khoan', ''),
                        acc.get('so_hieu_vi_dien_tu', '') or "",
                        "✓" if acc.get('la_tai_khoan_chinh') else ""
                    ))
                
                if hasattr(self, 'bank_status_label'):
                    self.bank_status_label.config(text=f"✓ Đã tải {len(accounts)} tài khoản", foreground="green")
                    self.master.after(3000, lambda: self.bank_status_label.config(text=""))
            else:
                if hasattr(self, 'bank_status_label'):
                    self.bank_status_label.config(text="Chưa có tài khoản ngân hàng nào. Hãy thêm mới.", foreground="orange")
                    
        except Exception as e:
            logger.error(f"Lỗi tải tài khoản ngân hàng: {e}")
            if hasattr(self, 'bank_status_label'):
                self.bank_status_label.config(text=f"❌ Lỗi: {str(e)[:50]}", foreground="red")
