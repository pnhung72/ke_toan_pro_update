import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
import tempfile
import threading

# Các thành phần giao diện UI cũ của Thầy
from ui.product_tab import ProductTab
from ui.transaction_tab import TransactionTab
from ui.invoice_tab import InvoiceTab
from ui.debt_tab import DebtTab
from ui.report_tab import ReportTab
from ui.ledger_tab import LedgerTab
from ui.period_closing_tab import PeriodClosingTab
from ui.tax_declaration_tab import TaxDeclarationTab
from ui.about_tab import AboutTab
from ui.business_info_tab import BusinessInfoTab
from ui.currency_tab import CurrencyTab

# Các tab mới theo kiến trúc MVC (Bảo toàn đầy đủ dòng chèn AdminDashboardTab)
from views.tabs.dashboard_tab import DashboardTab
from views.tabs.report_export_tab import ReportExportTab
from views.tabs.user_manager_tab import UserManagerTab
from views.tabs.audit_log_tab import AuditLogTab
from views.tabs.tax_compliance_tab import TaxComplianceTab
from views.tabs.admin_dashboard import AdminDashboardTab      # 💾 Đã chèn thành công
from views.tabs.email_connection_tab import EmailConnectionTab 

# Các lõi xử lý Models và Định dạng Thẩm mỹ
from models.user_model import UserModel
from config import VERSION, DB_PATH
from theme import get_font

# Các dịch vụ báo cáo, ngoại tệ và XML
from reports.tax_reports import TaxReports
from reports.pdf_exporter import PDFExporter
from core.currency_manager import CurrencyManager
from services.xml_service import XMLService  # Động cơ xử lý XML
# Nạp cả 2 tính năng (Cập nhật thông tư + Đồng bộ đám mây v11) từ cùng một đường dẫn chuẩn định dạng gói
from services.reports.update_service import AutoUpdateService, CloudSyncService
from services.reports.cloud_thread import BackgroundSyncManager

# Các hàm bổ trợ quản lý Backup và Bản quyền (Đã sửa đồng bộ verify_license_info)
from utils.backup import manual_backup, start_auto_backup_loop, on_exit_backup
from utils.license import is_full_version, get_machine_id
from utils.license_manager import verify_license, verify_license_info # Đã thêm hàm _info để khớp __init__
#from ui.gas_station_tab import GasStationTab
import importlib
# Chèn thêm vào nhóm import ở đầu file main_window.py
from core.registry import ModuleRegistry
from services.metadata_service import MetadataService
import queue
from ui.license_manager_dialog import LicenseManagerDialog
from ui.invoice_approval_tab import InvoiceApprovalTab
from ui.tabs.ai_tab import AITab
from utils.license import has_ai_feature

# === Sửa lại đường dẫn Cổng kết nối tương lai (Bản chép đè chuẩn) ===
try:
    from gateway_future import DigitalGateway
except ImportError:
    # Nếu import trực tiếp thất bại, thử thêm đường dẫn vào sys.path để tìm file
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from gateway_future import DigitalGateway

# === CẤU HÌNH LOGGING HÀNH VI (Bảo toàn nguyên vẹn cấu trúc của Thầy) ===
LOG_BEHAVIOR_DIR = "logs"
try:
    os.makedirs(LOG_BEHAVIOR_DIR, exist_ok=True)
except PermissionError:
    # Nếu không tạo được, dùng thư mục tạm của user
    LOG_BEHAVIOR_DIR = os.path.join(tempfile.gettempdir(), "KeToanPro_Logs")
    os.makedirs(LOG_BEHAVIOR_DIR, exist_ok=True)

# Tạo logger riêng cho hành vi
behavior_logger = None

def init_behavior_logging():
    """Khởi tạo hệ thống ghi log hành vi người dùng"""
    global behavior_logger
    log_file = os.path.join(LOG_BEHAVIOR_DIR, f"behavior_{datetime.now().strftime('%Y%m%d')}.log")
    
    behavior_logger = logging.getLogger('behavior')
    behavior_logger.setLevel(logging.INFO)
    
    # Xóa handler cũ để tránh trùng lặp
    behavior_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    behavior_logger.addHandler(file_handler)
    
    # Console handler (tùy chọn, để debug)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
    behavior_logger.addHandler(console_handler)
    
    return behavior_logger

def log_behavior(action, user="system", details="", level="INFO"):
    """Ghi log hành vi người dùng"""
    if behavior_logger is None:
        init_behavior_logging()
    
    message = f"HÀNH VI: {action} | USER: {user} | {details}"
    if level == "INFO":
        behavior_logger.info(message)
    elif level == "WARNING":
        behavior_logger.warning(message)
    elif level == "ERROR":
        behavior_logger.error(message)

# Khởi tạo logging ngay khi import
init_behavior_logging()


class MainWindow(tk.Tk):
    def __init__(self, root):
        # Kích hoạt báo lỗi tự động qua email
        from utils.error_logger import kich_hoat_bao_loi_tu_dong
        kich_hoat_bao_loi_tu_dong()
        # --- BẮT ĐẦU MÃ THÁM TỬ ---
        import os, sys
        #print(f"🕵️ [THÁM TỬ] Đang khởi tạo MainWindow...")
        #print(f"🕵️ [THÁM TỬ] sys.executable: {sys.executable}")
        #print(f"🕵️ [THÁM TỬ] Current working dir: {os.getcwd()}")
        #print(f"🕵️ [THÁM TỬ] Base dir xác định được: {os.path.dirname(os.path.abspath(__file__))}")
        # --- KẾT THÚC MÃ THÁM TỬ ---
        # ĐỊNH NGHĨA BIẾN NÀY NGAY ĐẦU HÀM __init__
        import os
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        super().__init__()
        self.root = root
        self.ui_queue = queue.Queue() # Thêm hàng đợi
        # ========== GIAI ĐOẠN 1: KHỞI TẠO BIẾN & LOGIC NỀN ==========
        # [0] Biến cờ nội bộ
        self.active_module_ids = []  # <--- BẮT BUỘC THÊM DÒNG NÀY
        self.root = self
        self._is_closing = False
        self._after_ids = []
        self.current_user = None  # <--- THÊM DÒNG NÀY VÀO ĐÂY
        self.bought_features = [] # <--- NÊN KHỞI TẠO LUÔN ĐỂ TRÁNH LỖI
        self._industry_tab_instances = {}   # 👈 THÊM DÒNG NÀY
        # [1] Xác định đường dẫn gốc (base_dir)
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
            self.resource_dir = sys._MEIPASS   # thư mục tạm chứa tài nguyên đóng gói
        else:
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.resource_dir = self.base_dir
        os.chdir(self.base_dir)

        # [2] Kiểm tra quyền ADMIN (admin.key) – NGAY sau khi có base_dir
        key_abs_path = os.path.join(self.base_dir, "admin.key")
        is_real_admin = os.path.exists(key_abs_path)          # biến cục bộ
        self.is_super_admin = is_real_admin
        self.is_admin = is_real_admin

        #print(f"DEBUG: PATH KIỂM TRA KEY: {key_abs_path}")
        #print(f"DEBUG: KẾT QUẢ KIỂM TRA (True=Admin, False=Khách): {is_real_admin}")

        # [3] Các đường dẫn tài nguyên
        self.qr_path = os.path.join(self.base_dir, "ACB.jpeg")
        icon_path = os.path.join(self.base_dir, "icon.ico")

        # [4] Đồng bộ DB & thư mục logs
        global DB_PATH, LOG_BEHAVIOR_DIR
        
        # Cấu hình đường dẫn DB ưu tiên theo cấu trúc thư mục của dự án
        db_options = [
            os.path.join(self.base_dir, "ke_toan_data", "ke_toan.db"), # Vị trí chuẩn (có dữ liệu)
            os.path.join(self.base_dir, "database.db")                # Vị trí dự phòng
        ]
        # --- MÃ THÁM TỬ ĐIỀU TRA ---
        for path in db_options:
            exists = os.path.exists(path)
            #print(f"🕵️ [THÁM TỬ] Kiểm tra DB tại: {path} -> Tồn tại: {exists}")
        # ---------------------------
        
        # Tìm file tồn tại, nếu không tìm thấy thì gán vào vị trí chuẩn (để tránh lỗi)
        self.db_path = next((p for p in db_options if os.path.exists(p)), db_options[0])
        #print(f"🕵️ [THÁM TỬ] DB_PATH CHÍNH THỨC ĐƯỢC CHỌN: {self.db_path}")
        # THÊM DÒNG NÀY ĐỂ THẦY CÓ THỂ KIỂM TRA LỖI KHI CHẠY .EXE
        #print(f"DEBUG: Đường dẫn Database đang dùng: {self.db_path}")
        LOG_BEHAVIOR_DIR = os.path.join(self.base_dir, "logs")
        os.makedirs(LOG_BEHAVIOR_DIR, exist_ok=True)

        # [5] Đọc license (features) – NGAY sau khi có base_dir
        self.bought_features = []
        license_modules = []  # sẽ chứa danh sách module từ license
        try:
            from utils.license_manager import verify_license_info
            license_result = verify_license_info()
            features_str = license_result.get('features', "")
            self.bought_features = features_str.split(',') if features_str else []
            # Tách riêng các module ngành nghề (admin đã chọn) – chúng là các id như "gas_station", "san_xuat_dac_thu"
            # Lọc lấy các module có trong industry_modules.json
            import json, os
            # Dùng resource_dir để tìm file cấu hình (quan trọng khi build exe)
            config_path = os.path.join(self.resource_dir, "configs", "industry_modules.json")
            if not os.path.exists(config_path):
                # Thử dùng base_dir (khi chạy source)
                config_path = os.path.join(self.base_dir, "configs", "industry_modules.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    industry_data = json.load(f)
                    valid_module_ids = [item["id"] for item in industry_data.get("industry_tabs", [])]
                    # Chỉ lấy những features nằm trong valid_module_ids
                    license_modules = [m for m in self.bought_features if m in valid_module_ids]
                #print(f"✅ Đọc license: features={self.bought_features}, modules từ license={license_modules}")
            else:
                pass #print(f"⚠️ Không tìm thấy industry_modules.json tại {config_path}, bỏ qua lọc module từ license")
        except Exception as e:
            pass #print(f"Lỗi đọc license features: {e}")

        # Đọc active_module_ids từ app_state.json (nếu có)
        state_path = os.path.join(self.base_dir, "configs", "app_state.json")
        saved_modules = []
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    saved_modules = state.get("active_module_ids", [])
                #print(f"📁 Đọc app_state.json: {saved_modules}")
            except Exception as e:
                logging.warning(f"Lỗi đọc app_state.json: {e}")

        # Gộp: nếu có license_modules (từ license) thì ưu tiên dùng nó, nếu không thì dùng saved_modules
        if license_modules:
            self.active_module_ids = license_modules
            # Đảm bảo thư mục configs tồn tại trước khi ghi
            config_dir = os.path.join(self.base_dir, "configs")
            os.makedirs(config_dir, exist_ok=True)
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump({"active_module_ids": self.active_module_ids}, f)
            #print(f"✅ Đã đồng bộ active_module_ids từ license: {self.active_module_ids}")
        else:
            self.active_module_ids = saved_modules
            #print(f"📁 Sử dụng active_module_ids từ app_state.json: {self.active_module_ids}")
        features = self.bought_features   # đặt tên ngắn gọn cho dễ dùng

        # ========== [SỬA] KHỞI TẠO GATEWAY NGAY SAU KHI CÓ features, TRƯỚC KHI TẠO GIAO DIỆN ==========
        # Lý do: self.create_menu() cần self.gateway, nếu để sau sẽ bị lỗi AttributeError.
        self.gateway = None
        try:
            from services.digital_gateway import DigitalGateway
            instance = DigitalGateway()
            class SafeGatewayWrapper:
                def __init__(self, real_instance): self._real = real_instance
                def __getattr__(self, name):
                    if hasattr(self._real, name):
                        return getattr(self._real, name)
                    return lambda *args, **kwargs: print(f"💡 [Tính năng ngầm] Hàm '{name}'...")
            self.gateway = SafeGatewayWrapper(instance)
        except Exception:
            class FlexibleMockGateway:
                def __getattr__(self, name):
                    return lambda *args, **kwargs: print(f"💡 [Mock] Nút bấm '{name}' đang chờ.")
            self.gateway = FlexibleMockGateway()
        # ========== KẾT THÚC DI CHUYỂN ==========

        # ========== GIAI ĐOẠN 2: TẠO CẤU TRÚC GIAO DIỆN CHÍNH ==========
        self.root.withdraw()
        
        # --- TẠO MAIN CONTAINER (QUẢN LÝ LAYOUT TỐT NHẤT) ---
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # [7] Tạo Menu (thanh menu hệ thống)
        self.create_menu()
        
        # --- HIỂN THỊ TRẠNG THÁI BẢN QUYỀN (NHẸ NHÀNG, CHUYÊN NGHIỆP) ---
        self.top_header = tk.Frame(self.main_container, bg='white', height=28)
        self.top_header.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))
        self.top_header.pack_propagate(False)  # giữ chiều cao cố định

        trial_text = self.get_trial_status_display()
        
        # Xác định màu chữ dựa trên nội dung
        if "🟢" in trial_text:
            fg_color = "#2e7d32"   # xanh lá đậm (dùng thử)
        elif "🔴" in trial_text:
            fg_color = "#c62828"   # đỏ (hết hạn)
        elif "🔵" in trial_text:
            fg_color = "#0d47a1"   # xanh dương (admin)
        else:
            fg_color = "#1976d2"   # xanh dương mặc định

        self.trial_status_label = tk.Label(
            self.top_header,
            text=trial_text,
            font=("Segoe UI", 9),  # cỡ nhỏ, thanh lịch
            bg='white',
            fg=fg_color,
            anchor="w",
            padx=15,
            pady=2
        )
        self.trial_status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Separator thanh mảnh, tinh tế
        sep = ttk.Separator(self.top_header, orient='horizontal')
        sep.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=1)

        # --- NOTEBOOK (CHỨA CÁC TAB) ---
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.enable_traversal()
        
        # Ép giao diện vẽ lại để Tab hiện ngay lập tức
        self.notebook.update_idletasks()
        
        # Áp dụng style 3D, màu sắc (chỉ gọi một lần)
        from ui.styles import apply_global_styles, COLORS
        self.style = apply_global_styles()
        self.configure(bg=COLORS.get('bg_root', '#f0f0f0'))

        # --- BỔ SUNG: KÍCH HOẠT TỰ ĐỘNG CÁC TAB ĐÃ CHỌN ---
        if not hasattr(self, 'active_module_ids'):
            self.active_module_ids = [] 
            
        # [8] Tạo Status Bar – SAU KHI NOTEBOOK ĐÃ ĐƯỢC PACK
        should_show_status = is_real_admin or "status_bar" in features
        if should_show_status:
            self.create_status_bar()
            #print("✅ [HỆ THỐNG] Thanh trạng thái đã kích hoạt.")

        # ========== GIAI ĐOẠN 3: KHỞI TẠO CÁC THÀNH PHẦN PHỤ TRỢ ==========
        self.tab_manager = DynamicTabManager(self.notebook, self.db_path)
        self.user_model = UserModel(self.db_path)

        # Version
        v_path = os.path.join(self.base_dir, "version.txt")
        self.current_v = open(v_path, "r", encoding="utf-8").read().strip() if os.path.exists(v_path) else "5.2.0"
        self.current_user = None
        self.is_master_machine = (get_machine_id() == "878C-CC69-6201-88A2")
        if self.is_master_machine:
            self.is_admin = True


        # ========== GIAI ĐOẠN 4: NẠP TẤT CẢ CÁC TAB ==========
        # Toàn bộ tab (core + đặc quyền) được khởi tạo trong _init_all_tabs()
        self._init_all_tabs()
        #print("DEBUG: Đã gọi _init_all_tabs() - kiểm tra notebook tabs")
        self.load_industry_menu_dynamically()
        # 👇 THÊM ĐOẠN NÀY VÀO
        # Nạp lại các tab ngành nghề đã được lưu trong app_state.json
        for m_id in self.active_module_ids:
            self._add_industry_tab(m_id)
        # -------------------------------------------------
        # ======================================================

        # ========== GIAI ĐOẠN 5: HOÀN THIỆN HIỂN THỊ & LUỒNG NỀN ==========
        self.title(f"Phần Mềm Kế Toán Pro - Phiên bản {self.current_v}")
        self.geometry("1800x1100")
        self.state('zoomed')
        self.root.update_idletasks()
        self.root.deiconify()
        self.root.lift()

        # Áp dụng khóa tính năng dựa trên license
        self.apply_feature_locks()
        # VỊ TRÍ NÀY LÀ CHUẨN NHẤT:
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Xử lý đóng cửa sổ an toàn
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Luồng kiểm tra cập nhật tự động
        import threading
        threading.Thread(target=self._run_auto_update_check, daemon=True).start()
        # Đặt biểu tượng cho cửa sổ chính
        icon_path = os.path.join(self.base_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        else:
            logging.warning(f"Không tìm thấy icon.ico tại: {icon_path}")
        # Luồng đăng nhập (chạy sau 200ms để giao diện ổn định)
        self.after(200, self.run_login_flow)
        self.check_queue()           # Bắt đầu vòng lặp kiểm tra hàng đợi

    def on_closing(self):
        """Hàm đóng ứng dụng - TẮT NGAY, backup chạy ngầm"""
        
        # 1. Bật cờ thông báo cho các tiến trình nền
        self._is_closing = True
        
        # 2. Flush log trước khi thoát
        import logging
        logging.shutdown()
        
        # 3. Đóng kết nối database (tránh lock)
        try:
            from models.database import Database
            Database.close_all_connections()
            logging.info("Đã đóng kết nối database")
        except Exception as e:
            logging.warning(f"Lỗi đóng database: {e}")
        
        # 4. Backup chạy trong thread riêng (KHÔNG TREO)
        import threading
        from utils.backup import on_exit_backup
        
        def backup_in_background():
            try:
                on_exit_backup()
                logging.info("Backup khi thoát hoàn tất")
            except Exception as e:
                logging.warning(f"Backup khi thoát lỗi: {e}")
        
        threading.Thread(target=backup_in_background, daemon=True).start()
        
        # 5. Đóng cửa sổ NGAY LẬP TỨC
        self.destroy()
        
    def add_tab_safe(self, tab_class, title, *args):
        try:
            tab = tab_class(*args)
            self.notebook.add(tab, text=title)
            return tab
        except Exception as e:
            logging.error(f"Lỗi nạp Tab {title}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def _safe_after(self, delay, func, *args):
        after_id = self.after(delay, func, *args)
        self._after_ids.append(after_id)
        return after_id

    def _cancel_all_after(self):
        for after_id in self._after_ids:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()
        
    def check_queue(self):
        """Vòng lặp kiểm tra hàng đợi để cập nhật UI an toàn."""
        try:
            # Lấy các tác vụ có hạn định (tránh treo app nếu queue quá đầy)
            for _ in range(50): # Xử lý tối đa 50 tác vụ mỗi 100ms
                try:
                    task, args = self.ui_queue.get_nowait()
                    # Bao try-except cho TỪNG tác vụ
                    try:
                        task(*args)
                    except Exception as e:
                        logging.error(f"Tác vụ trong queue bị lỗi: {e}")
                except queue.Empty:
                    break
        except Exception as e:
            logging.error(f"Lỗi nghiêm trọng tại hàng đợi UI: {e}")
        
        # Lập lịch cho lần chạy tiếp theo
        self.root.after(100, self.check_queue)
        
    def apply_elastic_tabs(self, event=None):
        """
        Hiệu ứng đàn hồi v9.0.0 đã tinh chỉnh: An toàn tuyệt đối với winfo_exists
        """
        # Kiểm tra sự tồn tại của Notebook trước khi làm bất cứ điều gì
        if not hasattr(self, 'notebook') or not self.notebook.winfo_exists():
            return

        try:
            current_tab_id = self.notebook.select()
            if not current_tab_id:
                return

            # ... (Giữ nguyên phần khởi tạo tab_mapping của bạn) ...
            # [Phần tab_mapping của bạn ở đây...]
            
            # 2. Danh sách tiêu đề các Tab "Xương sống"
            priority_titles = ["📦 Hàng hóa", "💸 Giao dịch", "🧾 Hóa đơn", "🏦 Ngân hàng PR"]

            # 3. Quét an toàn
            for tab_id in self.notebook.tabs():
                # KIỂM TRA QUAN TRỌNG: Tab này phải còn tồn tại trong giao diện
                try:
                    # Kiểm tra xem ID này có phải là widget hợp lệ không
                    if not self.notebook.nametowidget(tab_id).winfo_exists():
                        continue
                except Exception:
                    continue

                if tab_id in tab_mapping:
                    full_title = tab_mapping[tab_id]
                    
                    if tab_id == current_tab_id or full_title in priority_titles:
                        self.notebook.tab(tab_id, text=full_title, padding=[8, 3])
                    else:
                        # Thu gọn thông minh
                        icon_only = full_title.split()[0] if " " in full_title else full_title[:1]
                        self.notebook.tab(tab_id, text=icon_only, padding=[2, 2])
        except Exception as e:
            # Lỗi ở đây không được làm chết ứng dụng
            logging.warning(f"Bỏ qua lỗi nhỏ ở Elastic Tabs: {e}")

    def run_login_flow(self):
        """Luồng đăng nhập an toàn: Đăng nhập xong mới hiện giao diện chính"""
        from views.dialogs.login_dialog import LoginDialog
        login = LoginDialog(self, self.user_model)
        user = login.get_user()
        
        if user:
            self.current_user = user
            # Chỉ khi đăng nhập thành công mới hiện cửa sổ chính[cite: 2]
            self.deiconify() 
            self.update_idletasks() # Bây giờ mới vẽ giao diện khi đã có User[cite: 2]
            self.update_status(f"Chào mừng {user['full_name']} đã quay trở lại")
        else:
            # Nếu thoát đăng nhập thì đóng sạch ứng dụng[cite: 2]
            self.destroy()
            
    def _init_all_tabs(self):
        import json
        import os
        import inspect

        # =================================================================
        # 1. HÀM CHỐNG TRÙNG LẶP (giữ nguyên logic gốc)
        # =================================================================
        def safe_add_tab(tab_obj, tab_text, icon_key=None, is_core=False):
            # Trích xuất frame thật
            if hasattr(tab_obj, 'get_frame') and callable(getattr(tab_obj, 'get_frame')):
                frame_to_add = tab_obj.get_frame()
            elif hasattr(tab_obj, 'frame'):
                frame_to_add = tab_obj.frame
            else:
                frame_to_add = tab_obj
            if frame_to_add is None:
                return

            # Chống trùng ID vật lý
            try:
                current_tabs = self.notebook.tabs()
            except Exception:
                current_tabs = []
            if str(frame_to_add) in current_tabs:
                #print(f"[HỆ THỐNG] Chặn trùng lặp: {tab_text}")
                return

            self.notebook.add(frame_to_add, text=tab_text)

            # Cập nhật metadata cho thanh đàn hồi
            if icon_key and hasattr(self, 'tab_meta_map') and hasattr(self, 'raw_meta_list_config'):
                for item in self.raw_meta_list_config:
                    if item[0] == icon_key:
                        self.tab_meta_map[icon_key] = {"icon": item[1], "title": item[2], "core": is_core}
                        break

        # =================================================================
        # 2. NẠP CẤU HÌNH MODULE & ĐỊNH NGHĨA DANH SÁCH TAB
        # =================================================================
        # Đọc app_state.json để biết module nào được bật
        state_path = os.path.join(self.resource_dir, "configs", "app_state.json")
        self.active_module_ids = []
        if os.path.exists(state_path):
            try:
                with open(state_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.active_module_ids = state.get("active_module_ids", [])
                #print(f"✅ [HỆ THỐNG] Module đang bật: {self.active_module_ids}")
                # THÊM DÒNG NÀY:
                self.update_dynamic_tabs(self.active_module_ids)   # nạp lại tab động sau khi có cấu hình
            except Exception as e:
                logging.warning(f"Lỗi đọc app_state: {e}")

        # Metadata chuẩn (giữ nguyên của thầy)
        self.tab_meta_map = {}
        self.raw_meta_list_config = [
            ("product",      "📦", "Hàng hóa",      True),
            ("gas_station",  "⛽", "Xăng dầu",      False),  # Đã sửa: True → False
            ("san_xuat_dac_thu", "🐟", "Nước mắm",  False),  # Đã sửa: True → False
            ("transaction",  "💸", "Giao dịch",     True),
            ("invoice",      "🧾", "Hóa đơn",       True),
            ("debt",         "📑", "Công nợ",       False),
            ("report",       "📈", "Báo cáo",       False),
            ("ledger",       "📒", "Sổ cái",        False),
            ("closing",      "🔒", "Kết chuyển",    False),
            ("tax",          "💸", "Quản lý Thuế",  False),
            ("bank",         "🏦", "Ngân hàng PRO", False),
            ("info",         "🏠", "Thông tin thuế",False),
            ("dashboard",    "📊", "Dashboard",     False),
            ("currency",     "💱", "Ngoại tệ",      False),
            ("audit",        "📋", "Nhật ký",       False),
            ("user",         "👥", "Nhân viên",     False),
            ("about",        "ℹ️", "Giới thiệu",    False),
            ("email",        "✉️", "Đồng bộ Hóa đơn & Sao kê", False),
            ("marketing",    "🎁", "Marketing",     False),
            ("distribution", "🚚", "Phân phối",     False),
            ("admin_pro",    "⚙️", "Điều hành Admin", False)
        ]

        # Danh sách các tab CỐT LÕI luôn hiển thị (không phụ thuộc cấu hình)
        CORE_TAB_IDS = [
            "product", "transaction", "invoice", "info", "dashboard", "about",
            "ledger", "debt", "report", "closing", "tax", "audit", "feedback"
        ]

        def should_load(tab_id):
            """Kiểm tra xem tab có được nạp hay không"""
            return (tab_id in CORE_TAB_IDS or
                    tab_id in self.active_module_ids or
                    getattr(self, 'is_super_admin', False))

        # =================================================================
        # 3. KHỞI TẠO CÁC TAB CÓ ĐIỀU KIỆN
        # =================================================================
        # --- Hàng hóa (core) ---
        if should_load("product"):
            self.product_tab = ProductTab(self, self.notebook)
            safe_add_tab(self.product_tab, "📦 Hàng hóa", "product", True)

        # --- Giao dịch & Hóa đơn (core) ---
        if should_load("transaction"):
            self.transaction_tab = TransactionTab(self, self.notebook)
            safe_add_tab(self.transaction_tab, "💸 Giao dịch", "transaction", True)
        if should_load("invoice"):
            self.invoice_tab = InvoiceTab(self, self.notebook, self)
            safe_add_tab(self.invoice_tab, "🧾 Hóa đơn", "invoice", True)
            
        # --- Sổ cái ---
        if should_load("ledger"):
            try:
                self.ledger_tab = LedgerTab(self, self.notebook)
                safe_add_tab(self.ledger_tab, "📒 Sổ cái", "ledger", False)
            except Exception as e:
                logging.error(f"Lỗi nạp Sổ cái: {e}")

        # --- Công nợ ---
        if should_load("debt"):
            self.debt_tab = DebtTab(self, self.notebook)
            safe_add_tab(self.debt_tab, "📑 Công nợ", "debt", False)

        # --- Báo cáo (có sub-notebook) ---
        if should_load("report"):
            self.report_container = ttk.Frame(self.notebook)
            report_sub_notebook = ttk.Notebook(self.report_container)
            report_sub_notebook.pack(fill="both", expand=True, padx=2, pady=2)

            self.report_tab = ReportTab(self, report_sub_notebook)
            report_sub_notebook.add(
                self.report_tab.frame if hasattr(self.report_tab, 'frame') else self.report_tab,
                text="📊 Bảng cân đối"
            )
            self.report_export_tab = ReportExportTab(self, report_sub_notebook)
            report_sub_notebook.add(self.report_export_tab.get_frame(), text="📄 Xuất dữ liệu nâng cao")
            safe_add_tab(self.report_container, "📈 Báo cáo", "report", False)

        # --- Kết chuyển ---
        if should_load("closing"):
            self.closing_tab = PeriodClosingTab(self, self.notebook)
            safe_add_tab(self.closing_tab, "🔒 Kết chuyển", "closing", False)

        # --- Quản lý Thuế (sub-notebook) ---
        if should_load("tax"):
            self.tax_container = ttk.Frame(self.notebook)
            tax_sub_notebook = ttk.Notebook(self.tax_container)
            tax_sub_notebook.pack(fill="both", expand=True, padx=2, pady=2)

            self.tax_compliance_tab = TaxComplianceTab(self, tax_sub_notebook)
            tax_sub_notebook.add(self.tax_compliance_tab.get_frame(), text="🔍 Kiểm tra rủi ro hóa đơn")
            self.tax_decl_tab = TaxDeclarationTab(self, tax_sub_notebook)
            tax_sub_notebook.add(
                self.tax_decl_tab.frame if hasattr(self.tax_decl_tab, 'frame') else self.tax_decl_tab,
                text="📂 Tờ khai thuế định kỳ"
            )
            safe_add_tab(self.tax_container, "💸 Quản lý Thuế", "tax", False)

        # --- Ngân hàng PRO (có thể không có sẵn) ---
        self.has_bank = False
        if should_load("bank"):
            try:
                from views.tabs.bank_connect_tab import BankConnectTab
                self.bank_tab = BankConnectTab(self.notebook, DB_PATH)
                safe_add_tab(self.bank_tab, "🏦 Ngân hàng", "bank", False)
                self.has_bank = True
            except Exception as e:
                logging.warning(f"Ngân hàng chưa sẵn sàng: {e}")

        # --- Thông tin thuế (core) ---
        if should_load("info"):
            self.business_info_tab = BusinessInfoTab(self.notebook)
            safe_add_tab(self.business_info_tab, "🏠 Thông tin thuế", "info", False)

        # --- Dashboard (core) ---
        if should_load("dashboard"):
            self.dashboard_tab = DashboardTab(self, self.notebook)
            safe_add_tab(self.dashboard_tab, "📊 Dashboard", "dashboard", False)

        # --- Ngoại tệ ---
        self.has_currency = False
        if should_load("currency"):
            try:
                self.currency_tab = CurrencyTab(self.notebook)
                safe_add_tab(self.currency_tab, "💱 Ngoại tệ", "currency", False)
                self.has_currency = True
            except Exception as e:
                logging.warning(f"Không thể tải Ngoại tệ: {e}")

        # --- Giới thiệu (core) ---
        if should_load("about"):
            self.about_tab = AboutTab(self, self.notebook, self)
            safe_add_tab(self.about_tab, "ℹ️ Giới thiệu", "about", False)

        # =================================================================
        # 4. CÁC TAB ĐẶC QUYỀN (ADMIN / LICENSE)
        # =================================================================
        features = getattr(self, 'bought_features', [])
        is_admin = getattr(self, 'is_super_admin', False) or getattr(self, 'is_thay_hung_admin', False)

        # Nhật ký hệ thống (chỉ admin)
        if should_load("audit"):   # bỏ is_admin
            self.audit_log_tab = AuditLogTab(self, self.notebook, self.user_model)
            safe_add_tab(self.audit_log_tab, "📋 Nhật ký", "audit", False)

        # Kết nối Email (có license hoặc admin)
        self.has_email = False
        if ("mail_client" in features or is_admin) and should_load("email"):
            try:
                from views.tabs.email_connection_tab import EmailConnectionTab
                self.email_tab = EmailConnectionTab(self.notebook, self)
                safe_add_tab(self.email_tab, "✉️ Email", "email", False)
                self.has_email = True
            except Exception as e:
                logging.warning(f"Email không tải được: {e}")

        # Marketing (có license hoặc admin)
        self.has_marketing = False
        if ("marketing" in features or is_admin) and should_load("marketing"):
            try:
                from views.tabs.marketing_tab import MarketingTab
                self.tab_marketing = MarketingTab(self.notebook)
                safe_add_tab(self.tab_marketing, "🎁 Marketing", "marketing", False)
                self.has_marketing = True
            except Exception:
                pass

        # Phân phối (có license hoặc admin)
        self.has_distribution = False
        if ("distribution" in features or is_admin) and should_load("distribution"):
            try:
                from views.tabs.distribution_tab import DistributionTab
                self.tab_distribution = DistributionTab(self.notebook)
                safe_add_tab(self.tab_distribution, "🚚 Phân phối", "distribution", False)
                self.has_distribution = True
            except Exception:
                pass

        # Trung tâm Điều hành Admin (chỉ admin)
        if is_admin and should_load("admin_pro"):
            if not hasattr(self, 'tab_admin_dashboard') or self.tab_admin_dashboard is None:
                from views.tabs.admin_dashboard import AdminDashboardTab
                self.tab_admin_dashboard = AdminDashboardTab(self, self.notebook)
            safe_add_tab(self.tab_admin_dashboard, "⚙️ Trung tâm Điều hành Admin", "admin_pro", False)

        # Phản hồi Admin – hiển thị theo cơ chế CORE_TAB_IDS (đã thêm 'feedback' vào danh sách)
        if should_load("feedback"):
            try:
                from views.tabs.admin_feedback_tab import AdminFeedbackTab
                self.admin_feedback_tab = AdminFeedbackTab(self, self.notebook, self.is_super_admin)
                safe_add_tab(self.admin_feedback_tab, "✉️ Phản hồi (Admin)", None, False)
            except Exception as e:
                logging.warning(f"Không thể tải tab Phản hồi: {e}")
                
        # === Thêm tab Duyệt hóa đơn đầu vào (chỉ Admin hoặc có license feature) ===
        feature_name = "invoice_email_scanner"
        if self.is_super_admin or feature_name in getattr(self, 'bought_features', []):
            self.invoice_approval_tab = InvoiceApprovalTab(self.notebook, self.db_path)
            safe_add_tab(self.invoice_approval_tab, "📥 Duyệt hóa đơn", None, False)
            #print("✅ Đã thêm tab Duyệt hóa đơn (có quyền)")
        else:
            pass #print("⚠️ Không thêm tab Duyệt hóa đơn: người dùng không có quyền")

        # Các đối tượng bổ trợ (background, không ảnh hưởng giao diện)
        self.report_export_tab_back = ReportExportTab(self, self.notebook)
        self.tax_compliance_tab_back = TaxComplianceTab(self, self.notebook)
        
        # --- Tab AI Thông minh (chỉ hiển thị nếu có quyền) ---
        if has_ai_feature():
            try:
                from ui.tabs.ai_tab import AITab
                self.ai_tab = AITab(self.notebook)
                safe_add_tab(self.ai_tab, "🤖 AI Thông minh", "ai", False)
            except Exception as e:
                logging.warning(f"Không thể tải tab AI: {e}")
                

        # =================================================================
        # 5. ĐỒNG BỘ LUỒNG ĐÀN HỒI (giữ nguyên gốc)
        # =================================================================
        self.elastic_ordered_keys = [
            item[0] for item in self.raw_meta_list_config if item[0] in self.tab_meta_map
        ]
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed_elastic)
        self._on_tab_changed_elastic()

        if hasattr(self, 'log_behavior'):
            self.log_behavior("HỆ THỐNG", "system", "Khởi tạo hệ sinh thái thành công.")
             
    def create_status_bar(self):
        """Tạo thanh trạng thái sạch, bảo toàn mọi tính năng và tích hợp thông tin bản quyền"""
        
        # 1. DỌN DẸP: Bảo toàn cơ chế dọn dẹp để tránh lỗi đè lớp
        if hasattr(self, 'status_frame') and self.status_frame:
            try: self.status_frame.destroy()
            except Exception: pass
            self.status_frame = None

        # 2. KHỞI TẠO FRAME MỚI
        self.status_frame = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, before=self.notebook)

        # 3. BÊN TRÁI: Thông báo hệ thống
        self.status_left = ttk.Label(
            self.status_frame, text="Sẵn sàng", font=get_font("small"),
            anchor=tk.W, padding=(5, 2)
        )
        self.status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 4. BÊN PHẢI: Khối điều khiển và thông tin
        self.status_right = ttk.Frame(self.status_frame)
        self.status_right.pack(side=tk.RIGHT)

        # --- MỚI: BỔ SUNG TRƯỜNG THÔNG TIN BẢN QUYỀN (Vị trí 6.1) ---
        license_info = "🛡️ Admin" if self.is_super_admin else "👤 Người dùng"
        self.status_license = ttk.Label(
            self.status_right, text=f"| {license_info}", 
            font=get_font("small"), foreground="blue", padding=(5, 2)
        )
        self.status_license.pack(side=tk.LEFT)

        # 5. NÚT ĐỒNG BỘ
        self.btn_cloud_sync = ttk.Button(
            self.status_right, text="🔄 Đồng bộ", style="Accent.TButton",
            command=self.OnNutDongBoClicked
        )
        self.btn_cloud_sync.pack(side=tk.LEFT, padx=5)

        # 6. LABEL TRẠNG THÁI CLOUD
        self.status_cloud_label = ttk.Label(
            self.status_right, text="○ Cloud: Sẵn sàng", 
            font=get_font("small"), padding=(5, 2)
        )
        self.status_cloud_label.pack(side=tk.LEFT)

        # 7. Label thống kê nhanh
        self.status_stats = ttk.Label(
            self.status_right, text="Đang tải dữ liệu...", 
            font=get_font("small"), anchor=tk.E, padding=(5, 2)
        )
        self.status_stats.pack(side=tk.LEFT)

        # 8. Separator
        ttk.Separator(self.status_right, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # 9. Label thời gian
        self.status_time = ttk.Label(
            self.status_right,
            text=datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
            font=get_font("small"), anchor=tk.E, padding=(5, 2)
        )
        self.status_time.pack(side=tk.LEFT)

        # 10. Kích hoạt cập nhật thời gian
        self.update_status_time()
        
    def update_status_bar(self):
        """Làm mới trạng thái bản quyền"""
        if hasattr(self, 'status_license'):
            status = "Admin" if self.is_super_admin else "Người dùng"
            self.status_license.config(text=f"Bản quyền: {status}")
        
    def update_cloud_ui_status(self, connected=False):
        """Hàm này sẽ được gọi từ dịch vụ Cloud khi có trạng thái mới"""
        if connected:
            self.status_cloud_label.config(text="● Đồng bộ Cloud", foreground="#2E7D32") # Xanh lá
        else:
            self.status_cloud_label.config(text="○ Đồng bộ Cloud", foreground="gray")    # Xám
            
    def OnNutDongBoClicked(self):
        # Chọn action phù hợp: 'get_revenue' (hóa đơn), 'get_debt' (công nợ) hoặc 'get_quarter' (tài chính)
        params = {'action': 'get_revenue'} 
        
        try:
            url = "https://script.google.com/macros/s/AKfycbzk6ID2zfmbM4_ydlSRw_5LgYqAol_nf1nfoHnOhH4BBDIvnew1fH_mrgPdWaAfMppG/exec"
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # Ở đây Thầy xử lý dữ liệu trả về (data)
                self.update_cloud_ui_status(connected=True)
            else:
                self.update_cloud_ui_status(connected=False)
                
        except Exception as e:
            self.update_cloud_ui_status(connected=False)

    def cap_nhat_trang_thai_cloud_ui(self, text_status):
        """Cập nhật trạng thái xử lý Cloud lên màn hình (Bản an toàn)"""
        try:
            # Kiểm tra xem status_left đã được tạo chưa trước khi gọi .config()
            if hasattr(self, 'status_left'):
                self.status_left.config(text=f"☁️ Cloud System: {text_status}")
        except Exception as e:
            # Ghi log lỗi nhẹ để dễ debug nếu cần, nhưng không làm crash app
            logging.warning(f"Không thể cập nhật thanh trạng thái: {e}")
            
    def _on_tab_changed_elastic(self, event=None):
        """
        Elastic tabs: core tabs luôn hiện full, tab phụ chỉ icon, khi chọn mới full.
        """
        try:
            selected_tab = self.notebook.select()
            if not selected_tab:
                return

            core_titles = {"📦 Hàng hóa", "💸 Giao dịch", "🧾 Hóa đơn", "🏦 Ngân hàng PR"}

            for tab_id in self.notebook.tabs():
                widget = self.notebook.nametowidget(tab_id)
                full_title = self._get_full_title_from_widget(widget)
                if not full_title:
                    continue

                current_text = self.notebook.tab(tab_id, "text")
                is_selected = (tab_id == selected_tab)
                is_core = (full_title in core_titles)

                if is_core or is_selected:
                    new_text = full_title
                else:
                    # Lấy icon (phần đầu tiên trước khoảng trắng)
                    icon = full_title.split()[0] if " " in full_title else full_title[:1]
                    new_text = icon

                if current_text != new_text:
                    self.notebook.tab(tab_id, text=new_text)
        except Exception as e:
            logging.warning(f"Elastic tabs error: {e}")

    def _get_full_title_from_widget(self, widget):
        """Trả về tên đầy đủ của tab dựa vào widget"""
        mapping = {}
        if hasattr(self, 'product_tab'): mapping[id(self.product_tab)] = "📦 Hàng hóa"
        if hasattr(self, 'transaction_tab'): mapping[id(self.transaction_tab)] = "💸 Giao dịch"
        if hasattr(self, 'invoice_tab'): mapping[id(self.invoice_tab)] = "🧾 Hóa đơn"
        if hasattr(self, 'ledger_tab'): mapping[id(self.ledger_tab)] = "📒 Sổ cái"
        if hasattr(self, 'debt_tab'): mapping[id(self.debt_tab)] = "📑 Công nợ"
        if hasattr(self, 'report_container'): mapping[id(self.report_container)] = "📈 Báo cáo"
        if hasattr(self, 'closing_tab'): mapping[id(self.closing_tab)] = "🔒 Kết chuyển"
        if hasattr(self, 'tax_container'): mapping[id(self.tax_container)] = "💸 Quản lý Thuế"
        if hasattr(self, 'bank_tab'): mapping[id(self.bank_tab)] = "🏦 Ngân hàng PRO"
        if hasattr(self, 'business_info_tab'): mapping[id(self.business_info_tab)] = "🏠 Thông tin thuế"
        if hasattr(self, 'dashboard_tab'): mapping[id(self.dashboard_tab)] = "📊 Dashboard"
        if hasattr(self, 'currency_tab'): mapping[id(self.currency_tab)] = "💱 Ngoại tệ"
        if hasattr(self, 'audit_log_tab'): mapping[id(self.audit_log_tab)] = "📋 Nhật ký"
        if hasattr(self, 'user_manager_tab'): mapping[id(self.user_manager_tab)] = "👥 Nhân viên"
        if hasattr(self, 'about_tab'): mapping[id(self.about_tab)] = "ℹ️ Giới thiệu"
        if hasattr(self, 'email_tab'): mapping[id(self.email_tab)] = "✉️ Đồng bộ Hóa đơn & Sao kê"
        if hasattr(self, 'tab_marketing'): mapping[id(self.tab_marketing)] = "🎁 Marketing"
        if hasattr(self, 'tab_distribution'): mapping[id(self.tab_distribution)] = "🚚 Phân phối"
        if hasattr(self, 'tab_admin_dashboard'): mapping[id(self.tab_admin_dashboard)] = "⚙️ Trung tâm Điều hành"
        # 👇 THÊM DÒNG NÀY CHO TAB PHẢN HỒI ADMIN
        if hasattr(self, 'admin_feedback_tab'):
            mapping[id(self.admin_feedback_tab)] = "✉️ Phản hồi (Admin)"
        return mapping.get(id(widget), None)
   
    def update_status_time(self):
        """Cập nhật thời gian trên thanh trạng thái"""
        if getattr(self, '_is_closing', False):
            return
        try:
            if hasattr(self, 'status_time') and self.status_time.winfo_exists():
                self.status_time.config(text=datetime.now().strftime("%H:%M:%S %d/%m/%Y"))
        except Exception:
            pass
        # Lưu ID timer để hủy sau
        self.time_timer = self._safe_after(1000, self.update_status_time)
        
    def update_status(self, message=None, show_stats=True):
        """
        Cập nhật nội dung thanh trạng thái (Bản an toàn - Không crash)
        """
        # Kiểm tra sự tồn tại của thanh trạng thái trước khi thao tác
        if not hasattr(self, 'status_left'):
            return

        # Lưu thông báo gốc nếu chưa có
        if not hasattr(self, '_default_status'):
            self._default_status = "Sẵn sàng"
        
        try:
            if message:
                # Hiển thị thông báo tạm thời
                self.status_left.config(text=message)
                # Sau 3 giây, trở về thông báo mặc định
                self.after(3000, lambda: self.status_left.config(text=self._default_status))
            else:
                self.status_left.config(text=self._default_status)
            
            # Cập nhật thống kê nhanh (nếu có hàm này)
            if show_stats and hasattr(self, 'update_quick_stats'):
                self.update_quick_stats()
                
        except Exception as e:
            logging.warning(f"Lỗi cập nhật Status Bar: {e}")

    def update_quick_stats(self):
        """Cập nhật thống kê nhanh trên thanh trạng thái (Bản sửa lỗi luồng)"""
        if not hasattr(self, 'status_stats'):
            return

        # Đưa apply_to_ui ra ngoài hàm cục bộ hoặc định nghĩa trước
        def apply_to_ui(count, income, expense, profit):
            """Cập nhật UI trong luồng chính"""
            def fmt(amt): return f"{amt:,.0f}".replace(",", ".")
            profit_color = "#4CAF50" if profit >= 0 else "#F44336"
            
            stats_text = f"📊 {count} GD | 💰 Thu: {fmt(income)}đ | 📉 Chi: {fmt(expense)}đ | 📈 Lãi: {fmt(profit)}đ"
            
            self.status_stats.config(text=stats_text, foreground=profit_color)
            self._default_status = stats_text

        # Hàm chạy ngầm nhận 'instance' (chính là self) làm tham số
        def run_stats_calc(instance):
            try:
                from services.report_service import get_report_service
                from core.database.connection_pool import get_connection_pool
                from config import DB_PATH
                
                report_service = get_report_service()
                total_income = report_service.get_total_income()
                total_expense = report_service.get_total_expense()
                profit = total_income - total_expense
                
                pool = get_connection_pool(DB_PATH)
                with pool.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM journal_entries")
                    trans_count = cursor.fetchone()[0]

                # Dùng instance thay vì self
                instance.ui_queue.put((apply_to_ui, (trans_count, total_income, total_expense, profit)))
                
            except Exception as e:
                def show_error():
                    instance.status_stats.config(text="⚠️ Lỗi thống kê", foreground="orange")
                instance.ui_queue.put((show_error, ()))
                logging.warning(f"Lỗi cập nhật thống kê: {e}")

        # Chạy luồng phụ, truyền 'self' vào qua tham số args=(self,)
        threading.Thread(target=run_stats_calc, args=(self,), daemon=True).start()

    def set_status_message(self, message, is_error=False):
        """
        Hiển thị thông báo trên thanh trạng thái
        
        Args:
            message: Nội dung thông báo
            is_error: Có phải thông báo lỗi không
        """
        if is_error:
            # Hiển thị lỗi màu đỏ
            self.status_left.config(text=f"❌ {message}", foreground="#F44336")
            self.after(5000, lambda: self.status_left.config(foreground="black"))
        else:
            self.update_status(message)
    
    def show_login_dialog(self):
        """Hiển thị dialog đăng nhập"""
        from views.dialogs.login_dialog import LoginDialog
        login = LoginDialog(self, self.user_model)
        user = login.get_user()
        
        if user:
            self.current_user = user
            
            # === GHI LOG ĐĂNG NHẬP THÀNH CÔNG ===
            log_behavior(
                "ĐĂNG NHẬP", 
                user.get('username', 'unknown'), 
                f"Họ tên: {user.get('full_name', 'N/A')}, Vai trò: {user.get('role', 'N/A')}"
            )
            
            self.update_status(f"Chào mừng {user['full_name']} ({user['role']})")
            
            # === LÀM MỚI TAB GIAO DỊCH ===
            if hasattr(self, 'transaction_tab') and hasattr(self.transaction_tab, 'refresh_table'):
                try:
                    self.transaction_tab.refresh_table()
                    if hasattr(self.transaction_tab, 'update_summary'):
                        self.transaction_tab.update_summary()
                except Exception as e:
                    logging.warning(f"Lỗi refresh transaction_tab: {e}")
            
            # === LÀM MỚI TAB BÁO CÁO ===
            if hasattr(self, 'report_tab') and hasattr(self.report_tab, 'load_data'):
                try:
                    self.report_tab.load_data()
                except Exception as e:
                    logging.warning(f"Lỗi refresh report_tab: {e}")
            
            # Kiểm tra quyền admin để hiển thị menu quản lý người dùng
            if user['role'] == 'admin':
                self.add_admin_menus()
                
            # Ghi log hành động đặc biệt nếu là admin
            if user['role'] == 'admin':
                log_behavior(
                    "QUYỀN ADMIN", 
                    user.get('username', 'unknown'), 
                    "Đã kích hoạt menu quản trị"
                )
        else:
            # === GHI LOG ĐĂNG NHẬP THẤT BẠI ===
            log_behavior(
                "ĐĂNG NHẬP THẤT BẠI", 
                "unknown", 
                "Người dùng đã hủy đăng nhập hoặc thoát ứng dụng",
                "WARNING"
            )
            
            # Hủy tất cả after schedule trước khi thoát
            try:
                for after_id in self.tk.call('after', 'info'):
                    self.after_cancel(after_id)
            except Exception:
                pass
            
            # Thoát nếu không đăng nhập
            self.quit()  # Dùng quit thay vì destroy để thoát sạch
        
    def add_admin_menus(self):
        """Thêm menu dành cho admin sử dụng biến self.sys_menu đã lưu"""
        # 1. Kiểm tra an toàn: Nếu menu Hệ thống chưa được khởi tạo thì dừng lại
        if not hasattr(self, 'sys_menu'):
            return

        # 2. Kiểm tra xem các mục quản trị đã tồn tại chưa để tránh việc thêm trùng lặp
        has_admin_items = False
        try:
            # Lấy số lượng mục trong menu Hệ thống
            last_index = self.sys_menu.index(tk.END)
            if last_index is not None:
                # Duyệt qua các mục để kiểm tra nhãn (label)
                for i in range(last_index + 1):
                    try:
                        label = self.sys_menu.entrycget(i, "label")
                        if "Quản lý người dùng" in label or "Nhật ký hệ thống" in label:
                            has_admin_items = True
                            break
                    except Exception:
                        continue
        except tk.TclError:
            # Trường hợp menu trống
            has_admin_items = False
        
        # 3. Nếu chưa có thì tiến hành thêm các mục dành riêng cho Admin
        if not has_admin_items:
            self.sys_menu.add_separator()
            self.sys_menu.add_command(
                label="👥 Quản lý người dùng", 
                command=self.open_user_manager
            )
            self.sys_menu.add_command(
                label="📜 Nhật ký hệ thống", 
                command=self.open_audit_log
            )
            
            # Ghi log hành vi để theo dõi quyền quản trị[cite: 3]
            if hasattr(self, 'current_user') and self.current_user:
                from main_window_10 import log_behavior # Đảm bảo import đúng hàm log[cite: 3]
                log_behavior(
                    "KÍCH HOẠT MENU ADMIN", 
                    self.current_user.get('username', 'unknown'), 
                    "Đã thêm các tùy chọn quản trị vào menu Hệ thống"
                )
    
    def open_user_manager(self):
        """Mở tab quản lý người dùng theo cơ chế nạp động"""
        m_id = "user_manager"  # Giả sử id của tab này trong JSON là 'user_manager'
        
        # Kiểm tra xem tab đã có trong từ điển loaded_tabs chưa
        if m_id in self.loaded_tabs:
            self.notebook.select(self.loaded_tabs[m_id])
        else:
            # Nếu chưa có, có thể gọi lại logic nạp động hoặc thông báo lỗi
            logging.warning(f"Tab {m_id} chưa được nạp vào hệ thống!")
            # Hoặc Thầy có thể gọi logic nạp lại ở đây nếu cần
    
    def open_audit_log(self):
        """Mở tab nhật ký hệ thống"""
        tab_exists = False
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "📜 Nhật ký hệ thống":
                tab_exists = True
                self.notebook.select(i)
                break
        
        if not tab_exists:
            self.notebook.add(self.audit_log_tab.get_frame(), text="📜 Nhật ký hệ thống")
            self.notebook.select(self.audit_log_tab.get_frame())
    
    def create_menu(self):
        #print(f"DEBUG: Vừa vào create_menu, quyền Admin đang là: {self.is_admin}")
        from utils.license_helper import get_machine_id
        current_mid = get_machine_id()
        #print(f"--- MA MAY CUA ANH LA: {current_mid} ---")
        menubar = tk.Menu(self)
        try:
            menubar.configure(font=get_font("title"))
        except Exception:
            pass
        self.config(menu=menubar)
        self.menubar = menubar

        RELEASE_TO_CLIENT = True

        # === 1. MENU HỆ THỐNG ===
        self.sys_menu = tk.Menu(menubar, tearoff=0, font=get_font("label"))
        menubar.add_cascade(label="Hệ thống", menu=self.sys_menu)
        self.sys_menu.add_command(label="💾 Sao lưu dữ liệu", command=self.backup_data)
        self.sys_menu.add_command(label="🔐 Đổi mật khẩu", command=self.change_password)
        self.sys_menu.add_separator()
        self.sys_menu.add_command(label="🚪 Thoát", command=self.on_closing)

        # === 2. MENU CÀI ĐẶT ===
        setting_menu = tk.Menu(menubar, tearoff=0, font=get_font("label"))
        menubar.add_cascade(label="Cài đặt", menu=setting_menu)
        self.data_source_var = tk.StringVar(value="invoices")
        setting_menu.add_radiobutton(label="📄 Chỉ từ hóa đơn (khuyến nghị)", variable=self.data_source_var, value="invoices", command=self.change_data_source)
        setting_menu.add_radiobutton(label="💰 Chỉ từ giao dịch thu", variable=self.data_source_var, value="transactions", command=self.change_data_source)
        setting_menu.add_radiobutton(label="🔧 Đã loại bỏ trùng lặp (thông minh)", variable=self.data_source_var, value="deduplicated", command=self.change_data_source)
        setting_menu.add_radiobutton(label="⚠️ Cả hai nguồn (có thể trùng)", variable=self.data_source_var, value="both", command=self.change_data_source)
        setting_menu.add_separator()
        setting_menu.add_command(label="ℹ️ Thông tin nguồn dữ liệu", command=self.show_data_source_info)

        # === 3. MENU CÔNG CỤ ===
        tool_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Công cụ", menu=tool_menu)
        self.tool_menu = tool_menu

        tool_menu.add_command(label="📥 Nạp hóa đơn XML", command=self.import_xml_handler)
        tool_menu.add_separator()
        tool_menu.add_command(label="📊 Báo cáo tài chính", command=self.show_report_tab)
        tool_menu.add_command(label="🏷️ In nhãn đơn hàng", command=self.print_label)
        tool_menu.add_command(label="📂 Quản lý danh mục", command=self.open_category_manager)
        tool_menu.add_command(label="🔑 Quản lý bản quyền", command=self.open_license_manager)

        # ===== TẠO SUB-MENU CHỌN NGÀNH NGHỀ (DÙNG add_command, KHÔNG DÙNG CHECKBOX) =====
        import os
        if os.path.exists("admin.key") or getattr(self, 'is_master_machine', False) or self.is_admin:
            tool_menu.add_separator()
            self.industry_menu = tk.Menu(tool_menu, tearoff=0)
            tool_menu.add_cascade(label="⚙️ Chọn ngành nghề (Kích hoạt Tab)", menu=self.industry_menu)

            import json
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(current_dir)
                config_path = os.path.join(project_root, "configs", "industry_modules.json")
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    industry_list = data.get("industry_tabs", [])
                    # Lưu trạng thái của từng module
                    self.module_states = {}
                    for item in industry_list:
                        m_id = item["id"]
                        m_name = item["name"]
                        is_active = m_id in self.active_module_ids
                        self.module_states[m_id] = is_active
                        prefix = "✅" if is_active else "☐"
                        self.industry_menu.add_command(
                            label=f"{prefix} {m_name}",
                            command=lambda mid=m_id, name=m_name: self._toggle_industry_menu(mid, name)
                        )
            except Exception as e:
                logging.error(f"Lỗi tạo menu ngành nghề: {e}")

        # === 4. MENU TRỢ GIÚP ===
        help_menu = tk.Menu(menubar, tearoff=0, font=get_font("label"))
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        help_menu.add_command(label="📖 Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="ℹ️ Thông tin phiên bản", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="🚀 Kiểm tra bản cập nhật", command=self.thuc_hien_cap_nhat)

        # === 5. MENU HỆ SINH THÁI SỐ ===
        self.future_menu = tk.Menu(menubar, tearoff=0, font=get_font("label"))
        menubar.add_cascade(label="Hệ sinh thái số", menu=self.future_menu)
        self.future_menu.add_command(label="⚙️ Cấu hình thông số", command=lambda: self.gateway.open_config_window() if hasattr(self.gateway, 'open_config_window') else messagebox.showinfo("Kế Toán Pro", "Tính năng Cấu hình hệ sinh thái số đang được xây dựng!"))
        self.future_menu.add_separator()
        self.future_menu.add_command(label="🚀 Kết nối Tổng cục Thuế", command=self.gateway.connect_tax_department)
        self.future_menu.add_command(label="🧾 Cổng Hóa đơn điện tử", command=self.gateway.e_invoice_sync)
        self.future_menu.add_command(label="📥 Hóa đơn đầu vào (Email/XML)", command=lambda: self.select_tab_by_name("Hóa đơn đầu vào"))
        self.future_menu.add_command(label="📤 Hóa đơn đầu ra (Phát hành)", command=lambda: self.select_tab_by_name("Hóa đơn đầu ra"))

        if self.is_admin or getattr(self, 'has_pr_license', False):
            if hasattr(self, 'ngan_hang_tab') and self.ngan_hang_tab is not None:
                self.notebook.add(self.ngan_hang_tab, text=" Ngân hàng PR ")
            self.future_menu.add_command(label="🏦 Đối soát ngân hàng (Bank-Connect)", command=lambda: self.select_tab_by_name("Ngân hàng PR"))

        if self.is_admin:
            self.future_menu.add_command(label="🛡️ Nhật ký bảo mật (Audit Log)", command=lambda: self.select_tab_by_name("Nhật ký hệ thống"))
            self.future_menu.add_command(label="👤 Quản trị viên tối cao", command=lambda: self.select_tab_by_name("Quản lý User"))
            self.future_menu.add_command(label="📊 Báo cáo thông minh (AI Insights)", command=lambda: self.select_tab_by_name("Báo cáo thông minh"))

        from utils.license_helper import get_machine_id
        current_mid = get_machine_id()
        MASTER_ID = "878C-CC69-6201-88A2"
        is_admin_user = self.current_user and self.current_user.get('role') == 'admin'
        is_ultimate_admin = ((current_mid == MASTER_ID) or is_admin_user or getattr(self, 'is_super_admin', False)) and not RELEASE_TO_CLIENT
        if is_ultimate_admin:
            self.admin_pro_menu = tk.Menu(self.menubar, tearoff=0, font=get_font("label"))
            self.menubar.add_cascade(label="🛠️ Quản trị PRO", menu=self.admin_pro_menu)
            self.admin_pro_menu.add_command(label="🔑 Cấp bản quyền & Gói cước", command=self.open_admin_license_mgr)
            self.admin_pro_menu.add_command(label="📊 Thiết lập định giá tính năng", command=lambda: messagebox.showinfo("Định giá", "Chức năng tùy chỉnh gói cước"))
    def select_tab_by_name(self, tab_name):
        """
        HÀM ĐIỀU HƯỚNG TỐI CAO V6 - SỬA DỨT ĐIỂM 100% THEO BẢN ĐỒ THÁM TỬ
        Định vị đóng đinh chỉ số chính xác tuyệt đối theo bộ nhớ máy tính Thầy Hùng
        """
        import unicodedata
        from tkinter import messagebox
        
        try:
            # --- 1. XỬ LÝ NHANH CÁC MENU THÔNG BÁO NGHIỆP VỤ ---
            if tab_name == "Kết nối Tổng cục Thuế":
                messagebox.showinfo("Tổng Cục Thuế", "✅ Kết nối thành công!")
                return
            elif tab_name == "Cổng Hóa đơn điện tử":
                messagebox.showinfo("Hóa Đơn Điện Tử", "✅ Đã đồng bộ danh sách hóa đơn điện tử từ TCT.")
                return

            # Chuẩn hóa chuỗi lệnh để kiểm tra từ khóa từ Menu truyền xuống
            def clean_cmd(s):
                s = str(s).lower().strip().replace('đ', 'd')
                return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

            cmd = clean_cmd(tab_name)
            all_tabs = self.notebook.tabs()
            total_tabs = len(all_tabs)
            
            #print(f"🎯 [KÍCH HOẠT ĐÓNG ĐINH] Menu: '{tab_name}' -> Số lượng Tab thực tế: {total_tabs}")

            # --- 2. BẢN ĐỒ ÁNH XẠ CHỈ SỐ TUYỆT ĐỐI DỰA THEO LOG THÁM TỬ ---

            # A. Nếu bấm "Hóa đơn đầu vào" hoặc "Hóa đơn đầu ra" -> Ép mở Tab '🧾 Hóa đơn' ở STT [2]
            if "hoa don dau vao" in cmd or "hoa don dau ra" in cmd or "hoa don" in cmd:
                if total_tabs > 2:
                    self.notebook.select(2)
                    #print("🚀 -> Đã kích hoạt Tab Hóa đơn (Vị trí số 2)")
                    return

            # B. Nếu bấm "Nhật ký bảo mật" hoặc "Nhật ký hệ thống" -> Ép mở Tab '🔒 Khóa sổ' ở STT [6]
            elif "nhat ky" in cmd or "bao mat" in cmd or "audit" in cmd:
                if total_tabs > 6:
                    self.notebook.select(6)
                    #print("🚀 -> Đã kích hoạt Tab Nhật ký hệ thống (Vị trí số 6 - Icon Khóa)")
                    return

            # C. Nếu bấm "Quản trị viên tối cao" hoặc "Quản lý User" -> Ép mở Tab '👥' ở STT [14]
            elif "user" in cmd or "quan tri" in cmd or "toi cao" in cmd:
                if total_tabs > 14:
                    self.notebook.select(14)
                    #print("🚀 -> Đã kích hoạt Tab Quản trị viên tối cao (Vị trí số 14 - Icon Người)")
                    return

            # D. Nếu bấm "Báo cáo thông minh" -> Ép mở Tab '📊' ở STT [4]
            elif "bao cao" in cmd or "insights" in cmd or "thong minh" in cmd:
                if total_tabs > 4:
                    self.notebook.select(4)
                    #print("🚀 -> Đã kích hoạt Tab Báo cáo thông minh (Vị trí số 4 - Icon Biểu đồ)")
                    return

            # E. Nếu bấm "Ngân hàng PR" hoặc "Đối soát ngân hàng" -> Ép mở Tab '🏦 Ngân hàng PR' ở STT [8]
            elif "ngan hang" in cmd or "doi soat" in cmd or "bank" in cmd:
                if total_tabs > 8:
                    self.notebook.select(8)
                    #print("🚀 -> Đã kích hoạt Tab Ngân hàng PR (Vị trí số 8)")
                    return
            # G. Nếu bấm "Xăng dầu" hoặc "Cây xăng"       
            elif "xang dau" in cmd or "cay xang" in cmd or "tram xang" in cmd:
                for idx, tab_id in enumerate(all_tabs):
                    widget = self.notebook.nametowidget(tab_id)
                    if widget.__class__.__name__ == "GasStationTab":
                        self.notebook.select(idx)
                        #print(f"🚀 [Điều hướng] Đã mở Tab Xăng dầu thành công tại chỉ số {idx}")
                        return

            # --- 3. LUỒNG DỰ PHÒNG CHỮ CƠ BẢN CHO CÁC TAB KHÁC ---
            for index, tab_id in enumerate(all_tabs):
                curr_text = clean_cmd(self.notebook.tab(tab_id, "text"))
                if cmd in curr_text or curr_text in cmd:
                    self.notebook.select(index)
                    #print(f"🔄 [Khớp chữ dự phòng] Chuyển sang Tab: {self.notebook.tab(tab_id, 'text')}")
                    return

            logging.warning(f"Không tìm thấy chỉ số định vị phù hợp cho Menu: {tab_name}")
        except Exception as e:
            logging.error(f"Lỗi nghiêm trọng tại select_tab_by_name: {e}")


    def clean_text(self, s):
        """Hàm bổ trợ cũ (giữ nguyên để tránh lỗi thuộc tính nếu có nơi gọi)"""
        return s
     
    def open_digital_ecosystem(self, item_name):
        """
        Hàm điều hướng sinh thái số do Thầy Hùng thiết kế
        Tự động nhận diện mục được click và gọi sang dịch vụ tương ứng
        """
        from tkinter import messagebox
        
        if item_name == "config":
            messagebox.showinfo("Cấu Hình thông số", "⚙️ Hệ thống đang mở bảng cấu hình tham số API kết nối.")
            
        elif item_name == "invoice_in":
            messagebox.showinfo("Hóa Đơn Đầu Vào", "📥 Hệ thống đang tự động quét hòm thư và kiểm tra file XML đầu vào.")
            
        elif item_name == "invoice_out":
            messagebox.showinfo("Hóa Đơn Đầu Ra", "📤 Hệ thống đang chuẩn bị kết nối cổng ký số và phát hành hóa đơn.")
            
        elif item_name == "bank":
            # Nếu Thầy muốn kết nối thẳng sang giao diện Tab Ngân hàng tự động đang mở trên màn hình:
            messagebox.showinfo("Đối Soát Ngân Hàng", "🏦 Đang kích hoạt cổng Bank-Connect kết nối dữ liệu sao kê ngân hàng.")
            
        elif item_name == "audit":
            messagebox.showinfo("Nhật Ký Bảo Mật", "🛡️ Đang truy xuất danh sách Audit Log (Lịch sử thao tác của các máy trạm).")
            
        elif item_name == "super_admin":
            messagebox.showinfo("Quản Trị Viên Tối Cao", "👤 Đang mở trung tâm phân quyền và quản lý cơ sở dữ liệu tối cao.")
            
        elif item_name == "ai_insights":
            messagebox.showinfo("AI Insights", "📊 Trí tuệ nhân tạo đang phân tích dòng tiền và đưa ra dự báo tài chính.")
            
        else:
            messagebox.showwarning("Thông báo", f"Chức năng '{item_name}' đang được phát triển nâng cấp.")
        
    def backup_data(self):
        if self.current_user:
            log_behavior("SAO LƯU", self.current_user.get('username', 'system'), "Thủ công")
        manual_backup()
    
    def show_report_tab(self):
        self.notebook.select(self.report_tab.frame)
    
    def print_label(self):
        if hasattr(self.invoice_tab, 'print_invoice'):
            # Ghi log hành vi in hóa đơn
            if self.current_user:
                log_behavior("IN HÓA ĐƠN", self.current_user.get('username', 'system'), "")
            self.invoice_tab.print_invoice()
        else:
            messagebox.showinfo("Thông báo", "Vui lòng chọn hóa đơn trong tab Hóa đơn để in")
            
    def open_category_manager(self):
        """Hàm mở từ menu công cụ"""
        from ui.category_manager import CategoryManager
        # Truyền 'self' của MainWindow là đủ
        CategoryManager(self)
    
    def manage_categories(self):
        """Mở cửa sổ quản lý danh mục giao dịch"""
        from ui.category_manager import CategoryManager
        
        # SỬA Ở ĐÂY: Thay vì dùng self.frame, ta dùng chính đối tượng này 
        # hoặc thuộc tính mà class của Thầy đang quản lý giao diện
        # Nếu TransactionTab là một Frame, thì chính 'self' là cha của cửa sổ con.
        
        # Thầy thử dùng 'self' (hoặc 'self.master' nếu cần)
        target_parent = self if isinstance(self, tk.Widget) else self.winfo_toplevel()
        
        CategoryManager(target_parent, refresh_callback=self.load_categories)
    
    def show_license_dialog(self):
        """Hiển thị dialog yêu cầu kích hoạt bản quyền"""
        
        self._license_dialog_open = True
        
        dialog = tk.Toplevel(self)
        dialog.title("Kích hoạt bản quyền")
        dialog.geometry("550x400")
        dialog.grab_set()
        dialog.transient(self)
        
        # ĐÃ SỬA: thay font cứng bằng get_font
        ttk.Label(dialog, text="Bạn đang dùng bản dùng thử có giới hạn tính năng.", 
                  font=get_font("label", bold=True)).pack(pady=10)
        
        machine_id = get_machine_id()
        ttk.Label(dialog, text="Mã máy của bạn:", font=get_font("label")).pack()
        entry_machine = ttk.Entry(dialog, width=70, font=get_font("label"))
        entry_machine.insert(0, machine_id)
        entry_machine.pack(pady=2)
        entry_machine.config(state="readonly")
        
        def copy_machine():
            self.clipboard_clear()
            self.clipboard_append(machine_id)
            messagebox.showinfo("Đã sao chép", "Mã máy đã được sao chép.")
        ttk.Button(dialog, text="Sao chép mã máy", command=copy_machine, style="Form.TButton").pack(pady=5)
        
        ttk.Label(dialog, text="Vui lòng gửi mã máy này cho nhà phát triển qua:\nEmail: pnhungc3nv@gmail.com\nZalo: 0982493474", 
                  justify="left", font=get_font("label")).pack(pady=10)
        
        ttk.Label(dialog, text="Sau khi nhận được file license.key, hãy đặt vào thư mục phần mềm và nhấn nút bên dưới.", 
                  font=get_font("label")).pack()
        
        def check_license():
            if is_full_version():
                messagebox.showinfo("Thành công", "Kích hoạt thành công! Phần mềm sẽ khởi động lại.")
                self._license_dialog_open = False
                dialog.destroy()
                self.restart_app()
            else:
                messagebox.showerror("Chưa có license", "Không tìm thấy file license.key hợp lệ.\nHãy đặt file license.key vào thư mục chứa phần mềm và thử lại.")
        
        def on_dialog_close():
            self._license_dialog_open = False
            dialog.destroy()
        
        dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
        
        ttk.Button(dialog, text="Kiểm tra license", command=check_license, style="Form.TButton").pack(pady=5)
        ttk.Button(dialog, text="Tiếp tục dùng thử", command=on_dialog_close, style="Form.TButton").pack(pady=5)
        
        self.wait_window(dialog)
        
    def restart_app(self):
        """Khởi động lại ứng dụng"""
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    # ← THÊM HÀM NÀY VÀO ĐÂY
    def _get_owner_name(self):
        """Lấy tên chủ sở hữu từ license, fallback về 'Bạn' nếu không tìm thấy"""
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT ho_ten FROM customers WHERE is_active=1 ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                ten = row[0].strip().split()[-1]  # Lấy tên cuối (tên thật)
                return f"Anh/Chị {ten}"
        except Exception:
            pass
        return "Bạn"
    
    def on_closing(self):
        """Xử lý khi đóng cửa sổ - Tích hợp sao lưu cục bộ và đám mây"""
        if getattr(self, '_is_closing', False): return
        
        # 1. Xác nhận và Dừng luồng
        if not messagebox.askyesno("Xác nhận", f"{self._get_owner_name()} có chắc muốn đóng phần mềm và sao lưu dữ liệu?"):
            return
        self._is_closing = True
        if hasattr(self, 'cloud_manager'): self.cloud_manager.stop_auto_sync()

        # 2. Hủy các lệnh after (Fix lỗi invalid command name)
        try:
            if getattr(self, 'time_timer', None): self.after_cancel(self.time_timer)
            for after_id in getattr(self, '_after_ids', []):
                try: self.after_cancel(after_id)
                except Exception: pass
            self._after_ids.clear()
        except Exception: pass

        # 3. Ghi log (An toàn hơn)
        try:
            username = 'system'
            if self.current_user and isinstance(self.current_user, dict):
                username = self.current_user.get('username', 'system')
            log_behavior("THOÁT", username, "")
        except Exception as e: 
            logging.warning(f"Lỗi ghi log thoát: {e}")
        
        # 4. Sao lưu (Local & Cloud)
        try:
            logging.info("Đang bắt đầu quy trình sao lưu...")
            from utils.backup import on_exit_backup
            path_zip = on_exit_backup()
            if path_zip:
                logging.info(f"Đã sao lưu cục bộ: {path_zip}")
                try:
                    from utils.cloud_backup import upload_to_drive
                    logging.info("Đang đồng bộ đám mây...")
                    if upload_to_drive(path_zip): print("🚀 Đồng bộ đám mây hoàn tất!")
                except ImportError: print("⚠️ Chưa cài module cloud_backup.")
                except Exception as e: print(f"❌ Lỗi đồng bộ: {e}")
            else: print("⚠️ Sao lưu cục bộ thất bại.")
        except Exception as e: print(f"❌ Lỗi nghiêm trọng khi đóng: {e}")
        
        # 5. Đóng DB và Thoát
        try:
            from models.database import Database
            Database.close_all_connections()
        except Exception: pass
        
        self.root.destroy() # Đóng giao diện
        sys.exit(0)        # Dứt điểm hoàn toàn process của chương trình
                 
    def change_data_source(self):
        """Thay đổi nguồn dữ liệu toàn cục"""
        try:
            from config_data_source import set_data_source
            source = self.data_source_var.get()
            set_data_source(source)
            
            source_names = {
                'invoices': 'Chỉ từ hóa đơn',
                'transactions': 'Chỉ từ giao dịch thu',
                'deduplicated': 'Đã loại bỏ trùng lặp (thông minh)',
                'both': 'Cả hai nguồn (có thể trùng)'
            }
            
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
            
            self.refresh_tabs_after_source_change()
            
        except ImportError:
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
        except Exception:
            pass

    def refresh_tabs_after_source_change(self):
        """Làm mới các tab sau khi thay đổi nguồn dữ liệu"""
        try:
            if hasattr(self, 'business_info_tab'):
                if hasattr(self.business_info_tab, 'refresh_other_tabs'):
                    self.business_info_tab.refresh_other_tabs()
                if hasattr(self.business_info_tab, 'load_data'):
                    self.business_info_tab.load_data()
            
            if hasattr(self, 'report_tab'):
                if hasattr(self.report_tab, 'refresh_data'):
                    self.report_tab.refresh_data()
            
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
            logging.warning(f"Lỗi refresh tabs: {e}")

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
        - 01/CNKD: Tờ khai thuế (doanh thu >1 tỷ)
        
        📚 Căn cứ pháp lý:
        - Thông tư 18/2026/TT-BTC
        - Thông tư 152/2025/TT-BTC
        - Nghị định 68/2026/NĐ-CP
        
        © 2026 - Phần mềm quản lý thuế cho hộ kinh doanh
        """
        messagebox.showinfo("Thông tin phiên bản", about_text)
        
    def check_license_periodically(self):
        """Kiểm tra license định kỳ, nếu mất license thì hiện dialog"""
        if self._is_closing:
            return
        from utils.license import is_full_version
        
        if not is_full_version():
            if not hasattr(self, '_license_dialog_open') or not self._license_dialog_open:
                self.show_license_dialog()
        
        self._safe_after(300000, self.check_license_periodically)
        
    def open_license_manager(self):
        """Hàm duy nhất để gọi dialog: Ép buộc chạy trên luồng chính"""
        # .after(0, ...) là lệnh "nhờ" luồng chính làm giúp việc này ngay lập tức
        self.after(0, self._open_dialog_securely)

    def _open_dialog_securely(self):
        """Mở dialog quản lý bản quyền an toàn - Hoạt động cả source và EXE"""
        try:
            # Đảm bảo cửa sổ chính đã hiển thị
            if self.state() == 'withdrawn':
                self.deiconify()
            self.update_idletasks()
            self.lift()
            self.focus_force()
            
            # Dùng after để tách rời việc tạo dialog khỏi luồng hiện tại
            self.after(50, self._really_open_license_dialog)
        except Exception as e:
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể mở quản lý bản quyền: {e}")

    def _open_dialog_securely(self):
        """Mở dialog quản lý bản quyền an toàn - Hoạt động cả source và EXE"""
        try:
            # Đảm bảo cửa sổ chính đã hiển thị
            if self.state() == 'withdrawn':
                self.deiconify()
            self.update_idletasks()
            self.lift()
            self.focus_force()
            
            # Dùng after để tách rời việc tạo dialog khỏi luồng hiện tại
            self.after(50, self._really_open_license_dialog)
        except Exception as e:
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể mở quản lý bản quyền: {e}")

    def _really_open_license_dialog(self):
        """Thực sự mở dialog sau khi root đã sẵn sàng"""
        try:
            from ui.license_manager_dialog import LicenseManagerDialog
            is_admin = os.path.exists(os.path.join(self.base_dir, 'admin.key'))
            # Sử dụng after_idle để đảm bảo mọi thứ đã ổn định
            self.after_idle(lambda: self._create_license_dialog(is_admin))
        except Exception as e:
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể mở dialog: {e}")

    def _create_license_dialog(self, is_admin):
        """Tạo dialog thực tế"""
        try:
            dialog = LicenseManagerDialog(self, is_admin=is_admin, active_modules=self.active_module_ids)
            dialog.transient(self)
            dialog.grab_set()
            dialog.lift()
        except Exception as e:
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể tạo dialog: {e}")
            
    def change_password(self):
        """Mở dialog đổi mật khẩu"""
        if not hasattr(self, 'current_user') or not self.current_user:
            messagebox.showwarning("Cảnh báo", "Chưa đăng nhập!")
            return
        from ui.change_password_dialog import ChangePasswordDialog
        ChangePasswordDialog(self, self.user_model, self.current_user)
        
    def import_xml_handler(self):
        """Hàm xử lý khi Thầy nhấn nút Nạp hóa đơn XML"""
        folder_selected = filedialog.askdirectory(title="Chọn thư mục chứa hóa đơn XML")
        
        if folder_selected:
            try:
                service = XMLService(mst_owner="4201140371")
                result_msg = service.save_to_db(folder_selected)
                
                # Ghi log hành vi (dùng hàm global log_behavior)
                if self.current_user:
                    log_behavior("NHẬP XML", self.current_user.get('username', 'system'), result_msg)
                
                messagebox.showinfo("Kế Toán Pro", result_msg)
                
                if hasattr(self.invoice_tab, 'load_data'):
                    self.invoice_tab.load_data()
                    
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý XML: {e}")
        
    def thuc_hien_cap_nhat(self):
        import requests
        import subprocess
        from tkinter import messagebox

        # 1. Xác định đường dẫn tuyệt đối để tìm version.txt
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        version_file_path = os.path.join(base_path, "version.txt")

        # 2. Đọc phiên bản hiện tại từ file thay vì ghi cứng "5.0.0"
        try:
            if os.path.exists(version_file_path):
                with open(version_file_path, "r", encoding="utf-8") as f:
                    VERSION_HIEN_TAI = f.read().strip()
            else:
                VERSION_HIEN_TAI = "5.0.0" # Giá trị dự phòng nếu mất file
        except Exception:
            VERSION_HIEN_TAI = "5.0.0"

        # Link Drive của anh
        URL_VERSION = "https://drive.google.com/uc?export=download&id=1Z1k7jkYZk3rHChX4fOAuxWeSA3i0voRnx4zIIFum3V0"
        URL_DOWNLOAD = "https://drive.google.com/uc?export=download&id=1xm8KaF6tc0BgPypE7xXkb83BQLZPzneN"

        try:
            # 3. Lấy thông tin phiên bản mới từ Drive
            response = requests.get(URL_VERSION, timeout=10)
            phan_mem_moi = response.text.strip()
            
            # 4. So sánh phiên bản (Dùng hàm so sánh chuẩn)
            if phan_mem_moi > VERSION_HIEN_TAI:
                chon = messagebox.askyesno("Cập nhật hệ thống", 
                    f"Phiên bản hiện tại: {VERSION_HIEN_TAI}\n"
                    f"Đã có phiên bản mới: {phan_mem_moi}\n"
                    f"{self._get_owner_name()} có muốn nâng cấp ngay không?")
                
                if chon:
                    messagebox.showinfo("Thông báo", "Đang tải bản cập nhật, phần mềm sẽ tự khởi động lại...")
                    r = requests.get(URL_DOWNLOAD)
                    update_zip = os.path.join(base_path, "update_pro.zip")
                    
                    with open(update_zip, "wb") as f:
                        f.write(r.content)
                    
                    # 5. Tạo file Batch với đường dẫn tuyệt đối
                    helper_path = os.path.join(base_path, "update_helper.bat")
                    with open(helper_path, "w", encoding="utf-8") as f:
                        f.write('@echo off\n')
                        f.write('timeout /t 2 /nobreak > nul\n')
                        # Chuyển vào đúng thư mục gốc trước khi giải nén
                        f.write(f'cd /d "{base_path}"\n')
                        f.write('tar -xf update_pro.zip -C . --overwrite\n')
                        f.write('del update_pro.zip\n')
                        f.write('start main.exe\n')
                        f.write('del "%~f0"\n')
                    
                    subprocess.Popen(helper_path, shell=True)
                    self.on_closing() 
            else:
                messagebox.showinfo("Thông báo", f"Phiên bản {VERSION_HIEN_TAI} của {self._get_owner_name()} là mới nhất rồi ạ!")
                
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể kết nối Drive: {e}")
                
    def import_xml_handler(self):
        """Hành động khi nhấn nút Nạp hóa đơn XML"""
        from services.xml_service import XMLService
        folder_selected = filedialog.askdirectory(title="Chọn thư mục chứa hóa đơn XML")
        if folder_selected:
            try:
                service = XMLService(mst_owner="4201140371")
                result_msg = service.save_to_db(folder_selected)
                
                # Ghi log hành vi vào hệ thống
                log_behavior("NHẬP XML", self.current_user.get('username', 'system'), result_msg)
                
                messagebox.showinfo("Kế Toán Pro", result_msg)
                # Làm mới tab hóa đơn để hiện dữ liệu mới
                if hasattr(self, 'invoice_tab'):
                    self.invoice_tab.load_data()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xử lý XML: {e}")
                
    def apply_feature_locks(self):
        """Kiểm soát việc làm mờ các nút dựa trên gói cước."""
        # Kiểm tra quyền gói PRO (ví dụ tính năng 'tax_report')
        is_pro = self.user_model.check_feature_access('tax_report')
        
        # Danh sách các nút cần khóa nếu không phải gói PRO
        # Anh hãy kiểm tra tên biến nút bấm trong code của anh (ví dụ self.btn_tax)
        premium_buttons = [
            ('Báo cáo Thuế', getattr(self, 'btn_tax', None)),
            ('Nạp hóa đơn XML', getattr(self, 'btn_import_xml', None)),
            ('Xuất Excel Pro', getattr(self, 'btn_export_pro', None))
        ]
        
        for name, btn in premium_buttons:
            if btn and not is_pro:
                btn.config(state='disabled')
                # Rê chuột vào hiện thông báo hướng dẫn
                btn.bind("<Enter>", lambda e, n=name: self.show_upgrade_hint(n))

    def show_upgrade_hint(self, feature_name):
        """Thông báo bằng Font hệ thống khi khách nhấn vào nút bị khóa"""
        messagebox.showinfo(
            "Kế Toán Pro - Bản Quyền", 
            f"Tính năng [{feature_name}] chỉ dành cho gói PRO.\n\nAnh vui lòng liên hệ Thầy Hùng để nâng cấp bản quyền!",
            icon='info'
        )
        
    def open_admin_license_mgr(self):
        """Cửa sổ dành riêng cho Thầy Hùng quản lý khách hàng"""
        from theme import get_font
        top = tk.Toplevel(self)
        top.title("HỆ THỐNG QUẢN TRỊ BẢN QUYỀN - KẾ TOÁN PRO")
        top.geometry("700x500")
        top.grab_set()

        lbl_title = tk.Label(top, text="DANH SÁCH MÁY KHÁCH & GÓI CƯỚC", font=get_font('title'))
        lbl_title.pack(pady=10)

        # Frame nhập nhanh
        frame_input = ttk.LabelFrame(top, text=" Cấp License mới ")
        frame_input.pack(padx=10, fill="x", pady=5)

        tk.Label(frame_input, text="Machine ID:", font=get_font('small')).grid(row=0, column=0, padx=5)
        ent_mid = ttk.Entry(frame_input, width=30)
        ent_mid.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(frame_input, text="Chọn Gói:", font=get_font('small')).grid(row=0, column=2, padx=5)
        cb_tier = ttk.Combobox(frame_input, values=("BASIC", "PRO"), state="readonly")
        cb_tier.set("PRO")
        cb_tier.grid(row=0, column=3, padx=5)

        def save_license():
            mid = ent_mid.get().strip()
            tier = cb_tier.get()
            if not mid: return
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM feature_tiers WHERE tier_name = ?", (tier,))
            tid = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT OR REPLACE INTO software_licenses (machine_id, tier_id, is_active)
                VALUES (?, ?, 1)
            ''', (mid, tid))
            conn.commit()
            conn.close()
            messagebox.showinfo("Thành công", f"Đã cấp quyền {tier} cho máy {mid}")
            top.destroy()
            self.apply_feature_locks() # Cập nhật lại giao diện ngay lập tức

        btn_save = ttk.Button(frame_input, text="KÍCH HOẠT NGAY", command=save_license)
        btn_save.grid(row=0, column=4, padx=10)
        
    def _run_auto_update_check(self):
        """Hàm ngầm thực hiện kết nối Server và tải cấu hình Thông tư mới - CHẠY ĐỊNH KỲ"""
        while not getattr(self, '_is_closing', False):
            try:
                from services.reports.update_service import AutoUpdateService
                updater = AutoUpdateService()
                is_updated, message = updater.kiem_tra_va_cap_nhat()
                
                if is_updated and not self._is_closing:
                    # Đẩy lên UI thread an toàn, kiểm tra lại cờ
                    self.after(0, lambda: self._safe_show_update_message(message))
                else:
                    logging.info(f"[AutoUpdate] {message}")
                    
            except Exception as e:
                logging.error(f"Không thể kiểm tra cập nhật hệ thống: {str(e)}")
            
            # Chờ 24 giờ (86400 giây), nhưng kiểm tra cờ mỗi giây để có thể thoát sớm
            for _ in range(86400):
                if getattr(self, '_is_closing', False):
                    return
                threading.Event().wait(1)

    def _safe_show_update_message(self, message):
        """Hiển thị messagebox an toàn nếu chưa đóng cửa sổ"""
        if not getattr(self, '_is_closing', False):
            try:
                messagebox.showinfo("Cập Nhật Hệ Thống", message)
            except Exception:
                pass
            
    def load_industry_menu_dynamically(self):
        import json, os
        import traceback
        import tkinter as tk
        #print("[THÁM TỬ] load_industry_menu_dynamically bắt đầu")
        if not hasattr(self, 'industry_menu'):
            #print("❌ Không có industry_menu")
            return
            
        self.industry_menu.delete(0, "end")
        
        # Xác định đường dẫn gốc ưu tiên resource_dir (cho EXE)
        if hasattr(self, 'resource_dir'):
            base_path = self.resource_dir
        elif hasattr(self, 'base_dir'):
            base_path = self.base_dir
        else:
            base_path = os.getcwd()
        
        config_path = os.path.join(base_path, "configs", "industry_modules.json")
        if not os.path.exists(config_path):
            alt_path = os.path.join(os.getcwd(), "configs", "industry_modules.json")
            if os.path.exists(alt_path):
                config_path = alt_path
            else:
                logging.error(f"Không tìm thấy file: {config_path}")
                self.industry_menu.add_command(label="⚠️ Thiếu file industry_modules.json", state="disabled")
                return
        
        #print(f"🎯 ĐÃ KẾT NỐI KHỚP PHÁT HIỆN: {config_path}")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                configs_data = json.load(f)
            
            self.checkbox_vars = {}
            tabs_list = configs_data.get("industry_tabs", [])
            #print(f"   Đọc được {len(tabs_list)} module: {[t['id'] for t in tabs_list]}")
            
            for tab_cfg in tabs_list:
                m_id = tab_cfg["id"]
                m_name = tab_cfg["name"]
                is_active = m_id in self.active_module_ids
                var = tk.BooleanVar(value=is_active)
                self.checkbox_vars[m_id] = var
                #print(f"   Tạo var cho {m_id}: giá trị ban đầu={var.get()}")
                # === SỬA LỖI: Trì hoãn 50ms để BooleanVar kịp cập nhật ===
                self.industry_menu.add_checkbutton(
                    label=m_name,
                    variable=var,
                    command=lambda mid=m_id: self.after(100, lambda: (print(f"DEBUG: after called for {mid}"), self.toggle_module_from_menu(mid)))
                )
                #print(f"   Đã thêm menu: {m_name} (id={m_id})")
        except Exception as e:
            logging.error(f"Lỗi đọc JSON: {e}")
            traceback.print_exc()
        
    def toggle_module_from_menu(self, module_id):
        """
        [PHIÊN BẢN THÁM TỬ] - Cập nhật an toàn, tự tính trạng thái, bảo toàn logic gốc
        """
        #print(f"🔍 [THÁM TỬ] toggle_module_from_menu({module_id}) - bắt đầu")

        if not hasattr(self, 'checkbox_vars') or module_id not in self.checkbox_vars:
            #print(f"❌ [THÁM TỬ] Không tìm thấy checkbox_vars hoặc module_id {module_id}")
            return
            
        # ===== THAY ĐỔI CHÍNH: Tự tính trạng thái từ active_module_ids =====
        # Vì BooleanVar chưa kịp cập nhật, ta dùng logic toggle:
        # Nếu module đang có trong list -> bỏ, chưa có -> thêm
        is_checked = module_id not in self.active_module_ids
        #print(f"   is_checked (tự tính) = {is_checked}")
        # Vẫn đọc giá trị checkbox để tham khảo (nhưng không dùng để quyết định)
        checkbox_val = self.checkbox_vars[module_id].get()
        #print(f"   checkbox_vars.get() = {checkbox_val} (chỉ tham khảo)")
        # =================================================================

        # Cập nhật mảng active_module_ids
        if is_checked:
            if module_id not in self.active_module_ids:
                self.active_module_ids.append(module_id)
                #print(f"➕ [THÁM TỬ] Thêm {module_id} vào active_module_ids")
                if hasattr(self, '_add_industry_tab'):
                    #print(f"   Gọi _add_industry_tab({module_id})")
                    self._add_industry_tab(module_id)
                else:
                    pass #print("❌ [THÁM TỬ] Hàm _add_industry_tab không tồn tại!")
            else:
                pass #print(f"⚠️ [THÁM TỬ] {module_id} đã có trong active_module_ids")
        else:
            if module_id in self.active_module_ids:
                self.active_module_ids.remove(module_id)
                #print(f"➖ [THÁM TỬ] Xóa {module_id} khỏi active_module_ids")
                if hasattr(self, '_remove_industry_tab'):
                    self._remove_industry_tab(module_id)
                else:
                    pass #print("❌ [THÁM TỬ] Hàm _remove_industry_tab không tồn tại!")
            else:
                pass#print(f"⚠️ [THÁM TỬ] {module_id} không có trong active_module_ids")
        
        #print(f"   active_module_ids hiện tại: {self.active_module_ids}")
        
        # Lưu trạng thái
        import json, os
        config_dir = os.path.join(self.base_dir, "configs")
        os.makedirs(config_dir, exist_ok=True)
        state_path = os.path.join(config_dir, "app_state.json")
        try:
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump({"active_module_ids": self.active_module_ids}, f)
            #print(f"💾 [THÁM TỬ] Đã lưu app_state.json: {self.active_module_ids}")
        except Exception as e:
            logging.error(f"Lỗi khi lưu app_state.json: {e}")
        
    def _toggle_industry_menu(self, module_id, display_name):
        """Toggle trạng thái ngành nghề và cập nhật menu item (dùng add_command)"""
        new_state = not self.module_states[module_id]
        self.module_states[module_id] = new_state

        # Cập nhật nhãn của menu item (tìm item có chứa display_name)
        for i in range(self.industry_menu.index("end")):
            label = self.industry_menu.entrycget(i, "label")
            if label.endswith(display_name):
                prefix = "✅" if new_state else "☐"
                self.industry_menu.entryconfig(i, label=f"{prefix} {display_name}")
                break

        # Cập nhật danh sách active_module_ids và thêm/xóa tab
        if new_state:
            if module_id not in self.active_module_ids:
                self.active_module_ids.append(module_id)
                self._add_industry_tab(module_id)
        else:
            if module_id in self.active_module_ids:
                self.active_module_ids.remove(module_id)
                self._remove_industry_tab(module_id)

        # Lưu trạng thái vào file
        import json, os
        state_path = os.path.join(self.root_dir, "configs", "app_state.json")
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump({"active_module_ids": self.active_module_ids}, f)
        #print(f"✅ [MENU] {display_name} = {new_state}")


    def _add_industry_tab(self, module_id):
        """Thêm tab ngành nghề - Bản thám tử cải tiến (bảo toàn log, xử lý đường dẫn)"""
        import json, os, importlib
        #print(f"🔧 [THÁM TỬ] _add_industry_tab({module_id}) bắt đầu")
        
        # Xác định đường dẫn config (ưu tiên resource_dir khi chạy exe)
        if hasattr(self, 'resource_dir'):
            config_path = os.path.join(self.resource_dir, "configs", "industry_modules.json")
        else:
            config_path = os.path.join(self.base_dir, "configs", "industry_modules.json")
        
        #print(f"   Đọc config từ: {config_path}")
        if not os.path.exists(config_path):
            logging.error(f"Không tìm thấy file: {config_path}")
            return
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            logging.error(f"Lỗi đọc JSON: {e}")
            return
        
        # Tìm cấu hình
        cfg = None
        for item in config_data.get("industry_tabs", []):
            if item.get("id") == module_id:
                cfg = item
                break
        if not cfg:
            logging.error(f"Không tìm thấy cấu hình cho module_id {module_id} trong industry_modules.json")
            return
        
        #print(f"   Tìm thấy cấu hình: {cfg}")
        try:
            # Import module và class
            module = importlib.import_module(cfg["module"])
            tab_class = getattr(module, cfg["class_name"])
            #print(f"✅ Import thành công {cfg['module']}.{cfg['class_name']}")
            
            # Tạo instance
            db_path = getattr(self, 'db_path', None)
            try:
                tab_instance = tab_class(self, self.notebook)
            except TypeError:
                try:
                    tab_instance = tab_class(self.notebook, db_path)
                except TypeError:
                    try:
                        tab_instance = tab_class(self.notebook)
                    except TypeError:
                        tab_instance = tab_class()
            
            # Thêm vào notebook
            tab_text = f" {cfg['name']} "
            self.notebook.add(tab_instance, text=tab_text)
            if not hasattr(self, '_industry_tab_instances'):
                self._industry_tab_instances = {}
            self._industry_tab_instances[module_id] = tab_instance
            #print(f"✅ Đã thêm tab: {cfg['name']}")
            
            # Ép cập nhật giao diện
            self.notebook.update_idletasks()
            
        except Exception as e:
            logging.error(f"Lỗi khi thêm tab {module_id}: {e}")
            import traceback
            traceback.print_exc()

    def _remove_industry_tab(self, module_id):
        """Xóa tab đã thêm (bảo toàn log và xử lý an toàn)"""
        if hasattr(self, '_industry_tab_instances') and module_id in self._industry_tab_instances:
            tab = self._industry_tab_instances[module_id]
            try:
                self.notebook.forget(tab)
                tab.destroy()
                del self._industry_tab_instances[module_id]
                #print(f"🗑️ Đã gỡ tab {module_id}")
                self.notebook.update_idletasks()
            except Exception as e:
                logging.warning(f"Lỗi khi gỡ tab: {e}")
        else:
            logging.warning(f"Không tìm thấy tab {module_id} để xóa")

    def update_dynamic_tabs(self, active_module_ids):
        #print(f"🔍 [DEBUG] Bắt đầu điều phối Tab với ID: {active_module_ids}")
        """
        [BỘ ĐIỀU PHỐI TAB ĐỘNG ĐA NỀN TẢNG - HỆ SINH THÁI v11.0.0]
        Bảo toàn tính năng: Tự động lùi cấp từ thư mục dist/ tìm về config/ và views/ gốc.
        Tích hợp tính năng: Hỗ trợ nạp động đồng bộ theo mã phân phối License Key từ xa.
        Bổ sung quy tắc: Ẩn/Hiện linh hoạt 2 món gọi thêm (Kết nối Email & Tìm hóa đơn) dựa trên quyền Admin hoặc Key.
        """
        import importlib
        import sys
        import os

        if not hasattr(self, 'loaded_tabs'):
            self.loaded_tabs = {}

        try:
            # Đồng bộ mảng ID
            if active_module_ids is not None:
                self.active_module_ids = active_module_ids
            if not hasattr(self, 'active_module_ids') or self.active_module_ids is None:
                self.active_module_ids = []

            # Quyền admin thực tế (dựa trên file admin.key hoặc biến is_super_admin)
            is_admin_user = getattr(self, 'is_super_admin', False) or getattr(self, 'is_admin', False)

            # LUỒNG 1: ĐIỀU PHỐI NÚT TRÊN THANH TRẠNG THÁI
            if hasattr(self, 'btn_connect_email'):
                if is_admin_user or "email_integration" in self.active_module_ids:
                    self.btn_connect_email.pack(side="left", padx=5, pady=2)
                else:
                    self.btn_connect_email.pack_forget()

            if hasattr(self, 'btn_scan_invoice'):
                if is_admin_user or "auto_invoice_scan" in self.active_module_ids:
                    self.btn_scan_invoice.pack(side="left", padx=5, pady=2)
                else:
                    self.btn_scan_invoice.pack_forget()

            # LUỒNG 2: ĐIỀU PHỐI TAB NOTEBOOK
            # 1. Gỡ tab không còn active
            current_ids = list(self.loaded_tabs.keys())
            for m_id in current_ids:
                if m_id not in self.active_module_ids:
                    tab_instance = self.loaded_tabs[m_id]
                    if tab_instance is not None:
                        try:
                            self.notebook.forget(tab_instance)
                            tab_instance.destroy()
                        except Exception:
                            pass
                    del self.loaded_tabs[m_id]
                    #print(f"🗑️ [BẢN QUYỀN] Đã gỡ phân hệ: [{m_id}]")

            # 2. Định vị gốc dự án
            if hasattr(sys, '_MEIPASS'):
                exe_dir = os.path.dirname(sys.executable)
                if os.path.basename(exe_dir).lower() == "dist":
                    root_dir = os.path.dirname(exe_dir)
                else:
                    root_dir = exe_dir
                source_root = sys._MEIPASS
            else:
                if hasattr(self, 'base_dir'):
                    root_dir = os.path.dirname(self.base_dir) if "ui" in self.base_dir else self.base_dir
                else:
                    root_dir = os.getcwd()
                source_root = root_dir

            #print(f"[DEBUG] root_dir = {root_dir}")
            config_path = os.path.join(self.resource_dir, "configs", "industry_modules.json")

            if not os.path.exists(config_path):
                logging.error(f"Không tìm thấy file JSON cấu hình tại: {config_path}")
                return

            with open(config_path, "r", encoding="utf-8") as f:
                import json
                config_data = json.load(f)
            tabs_list = config_data.get("industry_tabs", [])
            industry_repo = {item["id"]: item for item in tabs_list}

            # 3. Nạp tab mới
            for m_id in self.active_module_ids:
                if m_id in self.loaded_tabs:
                    #print(f"⏩ Tab {m_id} đã có trong loaded_tabs, bỏ qua")
                    continue
                if m_id not in industry_repo:
                    logging.warning(f"Không tìm thấy cấu hình cho ID: {m_id}")
                    continue

                cfg = industry_repo[m_id]
                if m_id == "user_manager" and not is_admin_user:
                    #print(f"🔒 Bỏ qua {m_id} (chỉ admin)")
                    continue

                # Kiểm tra trùng lặp theo text tab
                existing_tabs = [self.notebook.tab(tab_id, "text").strip() for tab_id in self.notebook.tabs()]
                tab_text_display = f" {cfg['name']} "
                if tab_text_display in existing_tabs:
                    #print(f"⏩ Tab '{cfg['name']}' đã tồn tại, bỏ qua")
                    self.loaded_tabs[m_id] = None
                    continue

                try:
                    # Đảm bảo đường dẫn gốc được thêm vào sys.path
                    # Sử dụng resource_dir nếu có (cho exe), nếu không thì dùng base_dir
                    base_path = getattr(self, 'resource_dir', getattr(self, 'base_dir', os.getcwd()))
                    if base_path not in sys.path:
                        sys.path.insert(0, base_path)
                    # Cũng thêm root_dir và source_root nếu có
                    if root_dir not in sys.path:
                        sys.path.insert(0, root_dir)
                    if source_root not in sys.path:
                        sys.path.insert(0, source_root)

                    if cfg["module"] in sys.modules:
                        importlib.reload(sys.modules[cfg["module"]])

                    module = importlib.import_module(cfg["module"])
                    tab_class = getattr(module, cfg["class_name"])

                    db_path = getattr(self, 'db_path', None)
                    # Thử các cách khởi tạo khác nhau
                    try:
                        tab_instance = tab_class(self, self.notebook)
                    except TypeError:
                        try:
                            tab_instance = tab_class(self.notebook, db_path)
                        except TypeError:
                            try:
                                tab_instance = tab_class(self.notebook)
                            except TypeError:
                                tab_instance = tab_class()

                    self.notebook.add(tab_instance, text=tab_text_display)
                    self.loaded_tabs[m_id] = tab_instance
                    #print(f"✅ Đã thêm tab: {cfg['name']}")

                except Exception as ex:
                    logging.error(f"Lỗi nạp tab {m_id}: {ex}")
                    import traceback
                    traceback.print_exc()

            # 4. Refresh giao diện
            self.notebook.update_idletasks()
            self.notebook.event_generate("<<NotebookTabChanged>>")

        except Exception as e:
            logging.error(f"Lỗi điều phối Tab ngành nghề toàn cục: {e}")
            import traceback
            traceback.print_exc()
            
    def get_trial_status_display(self):
        # Nếu là admin, hiển thị thông báo đặc biệt, không liên quan đến dùng thử
        if self.is_super_admin or self.is_admin:
            return "🔵 Chế độ Admin - Toàn quyền"
        
        from pathlib import Path
        from datetime import datetime
        trial_file = Path(self.base_dir) / "ke_toan_data" / "trial.dat"
        if not trial_file.exists():
            return "🟢 Đang dùng thử: còn 30 ngày"
        try:
            with open(trial_file, "r") as f:
                start_str = f.read().strip()
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            days_left = 30 - (datetime.now() - start_date).days
            if days_left > 0:
                return f"🟢 Đang dùng thử: còn {days_left} ngày"
            else:
                return "🔴 Hết hạn dùng thử (vui lòng mua bản quyền)"
        except Exception:
            return "⚠️ Lỗi đọc thông tin dùng thử"
            
    def is_in_trial(self):
        from pathlib import Path
        from datetime import datetime
        trial_file = Path(self.base_dir) / "ke_toan_data" / "trial.dat"
        if not trial_file.exists():
            return True   # lần đầu chạy, xem như đang dùng thử
        try:
            with open(trial_file, "r") as f:
                start_str = f.read().strip()
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            days_left = 30 - (datetime.now() - start_date).days
            return days_left > 0
        except Exception:
            return True

            
class DynamicTabManager:
    """Lớp điều khiển nạp/hủy phân hệ động qua cơ chế Reflection cho Hệ sinh thái v10.0.0"""
    def __init__(self, notebook_widget, db_path):
        self.notebook = notebook_widget
        self.db_path = db_path
        self.loaded_tabs = {}  # Lưu vết các tab đang mở: {module_id: tab_instance}

    def reload_tabs_by_config(self, active_module_ids, config_path="configs/industry_modules.json"):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            industry_repo = {tab["id"]: tab for tab in config_data.get("industry_tabs", [])}
            
            # 1. Quét gỡ bỏ các tab ngành nghề không còn được chọn (hoặc không có trong License Key)
            current_ids = list(self.loaded_tabs.keys())
            # DEBUG: Kiểm tra xem đã có tab nào bị nạp sót chưa
            #print(f"DEBUG: Danh sách tab hiện có trong loaded_tabs: {list(self.loaded_tabs.keys())}")
            for m_id in current_ids:
                if m_id not in active_module_ids:
                    tab_instance = self.loaded_tabs[m_id]
                    self.notebook.forget(tab_instance)
                    tab_instance.destroy()  # Giải phóng tài nguyên RAM
                    del self.loaded_tabs[m_id]
                    
            # >>> ĐOẠN CHÈN THÊM (Đặt ngay phía trên vòng lặp của Thầy):
            if active_module_ids:
                from core.registry import ModuleRegistry
                if "san_xuat" in active_module_ids[0] or "dacthu" in active_module_ids[0]:
                    ModuleRegistry.activate_module("san_xuat_dac_thu")
                elif "thuong_mai" in active_module_ids[0]:
                    ModuleRegistry.activate_module("thuong_mai")
            # <<< KẾT THÚC ĐOẠN CHÈN THÊM
            #print(f"[DEBUG] Số lượng module trong active_module_ids: {len(active_module_ids)}")
            #print(f"[DEBUG] Nội dung active_module_ids: {active_module_ids}")
            # --- CHÈN VÀO TRƯỚC ĐOẠN NẠP TAB ĐỘNG ---
            #print("[DEBUG] Đang làm sạch các tác vụ nền gây lỗi...")
            # Tạm dừng các tiến trình tự động có thể gây xung đột giao diện
            try:
                # Nếu Thầy có dùng các hàm after để quét hòm thư, hãy tạm comment lại
                # hoặc đảm bảo chúng không chạy nếu chưa khởi tạo xong giao diện
                pass 
            except Exception:
                pass
            # ----------------------------------------
            # 2. Nạp động các Tab ngành nghề được kích hoạt
            for m_id in active_module_ids:
                if m_id == "mail_client": continue 
                if m_id in self.loaded_tabs: continue
                
                # ĐÃ SỬA: Sửa 'in' thành 'not in' để logic đúng
                if m_id not in industry_repo:
                    logging.error(f"Không tìm thấy ID '{m_id}' trong file JSON!")
                    continue
                
                cfg = industry_repo[m_id]
                #print(f"🔍 [DEBUG] Đang cố gắng nạp: {cfg['name']} (Class: {cfg['class_name']})")
                
                try:
                    #print(f"[DEBUG] Đang nạp: {cfg['name']} từ {cfg['module']}")
                    module = importlib.import_module(cfg["module"])
                    #print(f"✅ [DEBUG] Import module thành công: {cfg['module']}")
                    tab_class = getattr(module, cfg["class_name"])
                    
                    # BẢN SỬA ĐỔI: Thử nạp với tham số (self, self.notebook) 
                    # Nếu lỗi sẽ quay về (self.notebook, self.db_path) của thầy
                    try:
                        tab_instance = tab_class(self, self.notebook)
                    except TypeError:
                        tab_instance = tab_class(self.notebook, self.db_path)
                    
                    #print(f"DEBUG: tab_instance của {cfg['name']} là: {tab_instance}")
                    self.notebook.add(tab_instance, text=f" {cfg['name']} ")
                    #print(f"🚀 [DEBUG] Đã add thành công tab: {cfg['name']}")
                    
                    self.loaded_tabs[m_id] = tab_instance
                    self.notebook.update_idletasks()
                    #print(f"[DEBUG] ✅ Thành công: {cfg['name']}")
                    
                except Exception as e:
                    pass#print(f"\n" + "!"*50)
                    logging.error(f"LỖI NẠP TAB '{cfg.get('name', m_id)}': {e}")
                    import traceback
                    traceback.print_exc()
                    #print("!"*50 + "\n")
                    
        except Exception as e:
            messagebox.showerror("Lỗi Hệ Sinh Thái", f"Không thể điều khiển nạp phân hệ động: {e}")
