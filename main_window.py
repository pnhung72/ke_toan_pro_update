import tkinter as tk
from tkinter import ttk, messagebox
from ui.product_tab import ProductTab
from ui.transaction_tab import TransactionTab
from ui.invoice_tab import InvoiceTab
from ui.debt_tab import DebtTab
from ui.report_tab import ReportTab
from utils.backup import manual_backup, start_auto_backup_loop, on_exit_backup
from config import VERSION
from ui.ledger_tab import LedgerTab
from ui.period_closing_tab import PeriodClosingTab
from ui.tax_declaration_tab import TaxDeclarationTab
from ui.about_tab import AboutTab
from utils.license import is_full_version, get_machine_id
from ui.business_info_tab import BusinessInfoTab   # <--- THÊM DÒNG NÀY

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Phần Mềm Kế Toán Pro - Phiên bản {VERSION}")
        self.geometry("1200x800")
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Thanh trạng thái
        self.status_bar = ttk.Label(self, text="Sẵn sàng", relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Các tab
        self.product_tab = ProductTab(self, self.notebook)
        self.transaction_tab = TransactionTab(self, self.notebook)
        self.invoice_tab = InvoiceTab(self, self.notebook)
        self.debt_tab = DebtTab(self, self.notebook)
        self.report_tab = ReportTab(self, self.notebook)
        self.ledger_tab = LedgerTab(self, self.notebook)
        self.closing_tab = PeriodClosingTab(self, self.notebook)
        self.tax_decl_tab = TaxDeclarationTab(self, self.notebook)
        # Đưa Thông tin thuế lên trước
        self.business_info_tab = BusinessInfoTab(self.notebook)
        self.notebook.add(self.business_info_tab.get_frame(), text="🏠 Thông tin thuế")

        # Giới thiệu xuống cuối
        self.about_tab = AboutTab(self, self.notebook)
        
        # Tạo menu
        self.create_menu()
        
        # Khởi động sao lưu tự động (mỗi 24h)
        start_auto_backup_loop(interval_hours=24)
        
        # Xử lý đóng cửa sổ
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
               
        # 👇 THÊM DÒNG NÀY VÀO ĐÂY
        # Kiểm tra license mỗi 5 phút (300,000 milliseconds)
        self.after(300000, self.check_license_periodically)

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menu Hệ thống
        sys_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hệ thống", menu=sys_menu)
        sys_menu.add_command(label="Sao lưu dữ liệu", command=self.backup_data)
        sys_menu.add_separator()
        sys_menu.add_command(label="Thoát", command=self.on_closing)
        
        # ===== MENU CÀI ĐẶT (THÊM MỚI) =====
        setting_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Cài đặt", menu=setting_menu)
        
        # Tạo biến lưu nguồn dữ liệu
        self.data_source_var = tk.StringVar(value="invoices")
        
        setting_menu.add_radiobutton(
            label="📄 Chỉ từ hóa đơn (khuyến nghị)", 
            variable=self.data_source_var, 
            value="invoices",
            command=self.change_data_source
        )
        setting_menu.add_radiobutton(
            label="💰 Chỉ từ giao dịch thu", 
            variable=self.data_source_var, 
            value="transactions",
            command=self.change_data_source
        )
        setting_menu.add_radiobutton(
            label="🔧 Đã loại bỏ trùng lặp (thông minh)", 
            variable=self.data_source_var, 
            value="deduplicated",
            command=self.change_data_source
        )
        setting_menu.add_radiobutton(
            label="⚠️ Cả hai nguồn (có thể trùng)", 
            variable=self.data_source_var, 
            value="both",
            command=self.change_data_source
        )
        setting_menu.add_separator()
        setting_menu.add_command(label="Thông tin nguồn dữ liệu", command=self.show_data_source_info)
        
        # Menu Công cụ (giữ nguyên)
        tool_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Công cụ", menu=tool_menu)
        tool_menu.add_command(label="Báo cáo tài chính", command=self.show_report_tab)
        tool_menu.add_command(label="In nhãn đơn hàng", command=self.print_label)
        tool_menu.add_separator()
        tool_menu.add_command(label="Quản lý danh mục", command=self.open_category_manager)
        
        # ===== MENU TRỢ GIÚP (THÊM MỚI) =====
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="Thông tin phiên bản", command=self.show_about)
    
    def backup_data(self):
        manual_backup()
    
    def show_report_tab(self):
        self.notebook.select(self.report_tab.frame)
    
    def print_label(self):
        if hasattr(self.invoice_tab, 'print_invoice'):
            self.invoice_tab.print_invoice()
        else:
            messagebox.showinfo("Thông báo", "Vui lòng chọn hóa đơn trong tab Hóa đơn để in")
    
    def open_category_manager(self):
        """Mở cửa sổ quản lý danh mục giao dịch"""
        from ui.category_manager import CategoryManager
        # Truyền callback để refresh danh mục trong transaction_tab sau khi thay đổi
        CategoryManager(self, refresh_callback=self.transaction_tab.load_categories)
    
    def show_license_dialog(self):
        """Hiển thị dialog yêu cầu kích hoạt bản quyền"""
        
        # 👇 THÊM: Đánh dấu dialog đang mở (để kiểm tra định kỳ không mở thêm)
        self._license_dialog_open = True
        
        dialog = tk.Toplevel(self)
        dialog.title("Kích hoạt bản quyền")
        dialog.geometry("550x400")
        dialog.grab_set()
        dialog.transient(self)
        
        ttk.Label(dialog, text="Bạn đang dùng bản dùng thử có giới hạn tính năng.", 
                  font=("Arial", 10, "bold")).pack(pady=10)
        
        machine_id = get_machine_id()
        ttk.Label(dialog, text="Mã máy của bạn:").pack()
        entry_machine = ttk.Entry(dialog, width=70)
        entry_machine.insert(0, machine_id)
        entry_machine.pack(pady=2)
        entry_machine.config(state="readonly")
        
        def copy_machine():
            self.clipboard_clear()
            self.clipboard_append(machine_id)
            messagebox.showinfo("Đã sao chép", "Mã máy đã được sao chép.")
        ttk.Button(dialog, text="Sao chép mã máy", command=copy_machine).pack(pady=5)
        
        ttk.Label(dialog, text="Vui lòng gửi mã máy này cho nhà phát triển qua:\nEmail: pnhungc3nv@gmail.com\nZalo: 0982493474", 
                  justify="left").pack(pady=10)
        
        ttk.Label(dialog, text="Sau khi nhận được file license.key, hãy đặt vào thư mục phần mềm và nhấn nút bên dưới.").pack()
        
        def check_license():
            if is_full_version():
                messagebox.showinfo("Thành công", "Kích hoạt thành công! Phần mềm sẽ khởi động lại.")
                self._license_dialog_open = False  # 👈 THÊM: Xóa trạng thái mở
                dialog.destroy()
                self.restart_app()
            else:
                messagebox.showerror("Chưa có license", "Không tìm thấy file license.key hợp lệ.\nHãy đặt file license.key vào thư mục chứa phần mềm và thử lại.")
        
        # 👇 THÊM: Hàm xử lý khi đóng dialog (bấm X hoặc nút "Tiếp tục dùng thử")
        def on_dialog_close():
            self._license_dialog_open = False
            dialog.destroy()
        
        # 👇 THÊM: Bắt sự kiện đóng cửa sổ bằng nút X
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        
        ttk.Button(dialog, text="Kiểm tra license", command=check_license).pack(pady=5)
        
        # 👇 SỬA: Thay command=dialog.destroy bằng on_dialog_close
        ttk.Button(dialog, text="Tiếp tục dùng thử", command=on_dialog_close).pack(pady=5)
        
        self.wait_window(dialog)
        
    def restart_app(self):
        """Khởi động lại ứng dụng"""
        import sys, os
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def on_closing(self):
        """Xử lý khi đóng cửa sổ - tự động backup trước khi thoát"""
        try:
            print("🔄 Đang sao lưu dữ liệu...")
            result = on_exit_backup()
            if result:
                print("✅ Đã sao lưu dữ liệu thành công")
            else:
                print("⚠️ Sao lưu dữ liệu thất bại, vẫn thoát bình thường")
        except Exception as e:
            print(f"❌ Lỗi khi sao lưu: {e}")
        
        # Đóng tất cả kết nối database
        try:
            from models.database import Database
            Database.close_all_connections()
        except:
            pass
        
        # Hỏi xác nhận thoát
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn thoát?"):
            self.destroy()
            
    def update_status(self, message, is_error=False):
        """Cập nhật thanh trạng thái"""
        if is_error:
            self.status_bar.config(text=f"❌ {message}", foreground="red")
        else:
            self.status_bar.config(text=f"✅ {message}", foreground="green")
        self.after(3000, lambda: self.status_bar.config(text="Sẵn sàng", foreground="black"))
        
    def change_data_source(self):
        """Thay đổi nguồn dữ liệu toàn cục"""
        try:
            from config_data_source import set_data_source
            source = self.data_source_var.get()
            set_data_source(source)
            
            # Tên hiển thị của từng chế độ
            source_names = {
                'invoices': 'Chỉ từ hóa đơn',
                'transactions': 'Chỉ từ giao dịch thu',
                'deduplicated': 'Đã loại bỏ trùng lặp (thông minh)',
                'both': 'Cả hai nguồn (có thể trùng)'
            }
            
            # Mô tả chi tiết
            source_descriptions = {
                'invoices': '✅ Chính xác nhất cho kê khai thuế\n✅ Chỉ tính doanh thu từ hóa đơn đã xuất',
                'transactions': '⚠️ Chỉ dùng khi không có hóa đơn\n⚠️ Dựa trên giao dịch thu nhập',
                'deduplicated': '🌟 Khuyến nghị khi có cả hai nguồn\n🌟 Tự động phát hiện và loại bỏ trùng lặp',
                'both': '❌ Không khuyến nghị\n❌ Có thể bị trùng lặp doanh thu'
            }
            
            messagebox.showinfo(
                "Cài đặt", 
                f"Đã chuyển sang chế độ: {source_names.get(source, source)}\n\n"
                f"{source_descriptions.get(source, '')}\n\n"
                f"Dữ liệu sẽ được cập nhật khi chuyển tab hoặc làm mới."
            )
            
            # Refresh các tab để áp dụng thay đổi
            self.refresh_tabs_after_source_change()
            
        except ImportError:
            # Nếu chưa có file config, tạo mặc định
            self.create_default_config()
            self.change_data_source()

    def create_default_config(self):
        """Tạo file config mặc định nếu chưa có"""
        config_content = '''
    # Cấu hình nguồn dữ liệu mặc định cho toàn bộ phần mềm
    DEFAULT_DATA_SOURCE = "invoices"  # 'invoices', 'transactions', 'both', 'deduplicated'

    def get_data_source():
        """Lấy nguồn dữ liệu hiện tại"""
        return DEFAULT_DATA_SOURCE

    def set_data_source(source):
        """Thay đổi nguồn dữ liệu"""
        global DEFAULT_DATA_SOURCE
        if source in ['invoices', 'transactions', 'both', 'deduplicated']:
            DEFAULT_DATA_SOURCE = source
            return True
        return False
    '''
        try:
            with open("config_data_source.py", "w", encoding="utf-8") as f:
                f.write(config_content)
        except:
            pass

    def refresh_tabs_after_source_change(self):
        """Làm mới các tab sau khi thay đổi nguồn dữ liệu"""
        try:
            # Làm mới tab Thông tin thuế
            if hasattr(self, 'business_info_tab'):
                if hasattr(self.business_info_tab, 'refresh_other_tabs'):
                    self.business_info_tab.refresh_other_tabs()
                if hasattr(self.business_info_tab, 'load_data'):
                    self.business_info_tab.load_data()
            
            # Làm mới tab Báo cáo
            if hasattr(self, 'report_tab'):
                if hasattr(self.report_tab, 'refresh_data'):
                    self.report_tab.refresh_data()
            
            # Cập nhật thanh trạng thái
            if hasattr(self, 'update_status'):
                source_names = {
                    'invoices': 'hóa đơn',
                    'transactions': 'giao dịch thu',
                    'deduplicated': 'đã loại trùng',
                    'both': 'cả hai nguồn'
                }
                source = self.data_source_var.get()
                self.update_status(f"Đã chuyển sang nguồn: {source_names.get(source, source)}")
        except Exception as e:
            print(f"Lỗi refresh tabs: {e}")

    def show_data_source_info(self):
        """Hiển thị thông tin về các nguồn dữ liệu"""
        info = """
        📊 CÁC NGUỒN DỮ LIỆU DOANH THU
        
        1. 📄 Chỉ từ hóa đơn (khuyến nghị)
           - Chỉ tính doanh thu từ hóa đơn đã xuất
           - Chính xác nhất cho kê khai thuế
           - Phù hợp khi đã xuất hóa đơn cho khách hàng
        
        2. 💰 Chỉ từ giao dịch thu
           - Chỉ tính doanh thu từ giao dịch thu nhập
           - Phù hợp khi không xuất hóa đơn
           - Dùng cho hộ kinh doanh nhỏ lẻ
        
        3. 🔧 Đã loại bỏ trùng lặp (thông minh)
           - Tự động phát hiện giao dịch và hóa đơn trùng
           - Loại bỏ trùng lặp để tránh sai số
           - Khuyến nghị khi có cả hai nguồn
        
        4. ⚠️ Cả hai nguồn (có thể trùng)
           - Cộng dồn cả giao dịch và hóa đơn
           - CÓ THỂ BỊ TRÙNG LẶP DOANH THU
           - Không khuyến nghị cho kê khai chính thức
        
        💡 Khuyến nghị: Chọn chế độ "Đã loại bỏ trùng lặp" 
           nếu bạn vừa nhập giao dịch vừa tạo hóa đơn.
        """
        messagebox.showinfo("Thông tin nguồn dữ liệu", info)

    def show_help(self):
        """Hiển thị hướng dẫn sử dụng"""
        help_text = """
        📘 HƯỚNG DẪN SỬ DỤNG NHANH
        
        1. CÀI ĐẶT NGUỒN DỮ LIỆU
           - Vào menu "Cài đặt" → chọn nguồn dữ liệu phù hợp
           - Khuyến nghị: "Đã loại bỏ trùng lặp (thông minh)"
        
        2. NHẬP DỮ LIỆU
           - Hàng hóa: Thêm sản phẩm/dịch vụ
           - Giao dịch: Nhập thu/chi tiền mặt
           - Hóa đơn: Xuất hóa đơn bán hàng
        
        3. XUẤT BÁO CÁO THUẾ
           - Vào tab "Thông tin thuế"
           - Chọn kỳ báo cáo
           - Xuất XML nộp lên Cổng DVC
           - Hoặc in trực tiếp
        
        4. HẠN NỘP QUAN TRỌNG
           - Mẫu 01/BK-STK: 20/04/2026
           - Mẫu 01/TKN-CNKD: 31/07 (6 tháng đầu) hoặc 31/01 (cả năm)
        
        Mọi thắc mắc vui lòng liên hệ nhà phát triển.
        """
        messagebox.showinfo("Hướng dẫn sử dụng", help_text)

    def show_about(self):
        """Hiển thị thông tin phiên bản"""
        from config import VERSION
        about_text = f"""
        PHẦN MỀM KẾ TOÁN PRO
        Phiên bản {VERSION}
        
        📅 Ngày phát hành: 17/04/2026
        
        📋 Hỗ trợ các mẫu biểu:
        - 01/BK-STK: Thông báo tài khoản ngân hàng
        - S1a-HKD: Sổ doanh thu bán hàng
        - 01/TKN-CNKD: Thông báo doanh thu
        - 01/CNKD: Tờ khai thuế (doanh thu >500tr)
        
        📚 Căn cứ pháp lý:
        - Thông tư 18/2026/TT-BTC
        - Thông tư 152/2025/TT-BTC
        - Nghị định 68/2026/NĐ-CP
        
        © 2026 - Phần mềm quản lý thuế cho hộ kinh doanh
        """
        messagebox.showinfo("Thông tin phiên bản", about_text)
        
    def check_license_periodically(self):
        """Kiểm tra license định kỳ, nếu mất license thì hiện dialog"""
        from utils.license import is_full_version
        
        if not is_full_version():
            # Kiểm tra xem dialog license đã mở chưa (tránh mở nhiều cửa sổ)
            if not hasattr(self, '_license_dialog_open') or not self._license_dialog_open:
                self.show_license_dialog()
        
        # Lập lịch kiểm tra lại sau 5 phút
        self.after(300000, self.check_license_periodically)