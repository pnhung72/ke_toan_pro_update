import sqlite3
import os
from contextlib import contextmanager
from config import DB_PATH, BACKUP_DIR  # ĐÃ SỬA: bỏ DATA_DIR, thêm BACKUP_DIR

class Database:
    # Sử dụng đường dẫn từ config
    #print(f"DEBUG: File database đang dùng là: {DB_PATH}")
    DB_PATH = DB_PATH

    @staticmethod
    @contextmanager
    def get_connection() -> object:
        # Đảm bảo thư mục tồn tại
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        # Kết nối với timeout và WAL mode
        conn = sqlite3.connect(DB_PATH, timeout=20)
        conn.row_factory = sqlite3.Row

        # Bật chế độ WAL (Write-Ahead Logging) để giảm lock
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def init_db() -> None:
        """Tạo các bảng nếu chưa tồn tại"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()

            # Bảng sản phẩm
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    unit TEXT,
                    price_sell REAL DEFAULT 0,
                    price_buy REAL DEFAULT 0,
                    stock REAL DEFAULT 0,
                    min_stock REAL DEFAULT 0
                )
            ''')

            # Bảng giao dịch
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    type TEXT CHECK(type IN ('Thu','Chi')),
                    category TEXT
                )
            ''')

            # Bảng hóa đơn - thêm cột product_name để lưu tên hàng gốc
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyer_name TEXT NOT NULL,
                    phone TEXT,
                    tax_code TEXT,
                    address TEXT,
                    product_code TEXT,
                    product_name TEXT,
                    quantity REAL,
                    unit_price REAL,
                    total_excluding_tax REAL,
                    tax_amount REAL DEFAULT 0,
                    total_payment REAL,
                    paid REAL DEFAULT 0,
                    payment_method TEXT,
                    created_date TEXT,
                    FOREIGN KEY(product_code) REFERENCES products(code)
                )
            ''')

            # Bảng nợ
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    total_debt REAL DEFAULT 0,
                    paid REAL DEFAULT 0,
                    last_debt_date TEXT,
                    notes TEXT
                )
            ''')

            # Bảng tài khoản kế toán
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT
                )
            ''')

            # Bảng nhật ký chung
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    description TEXT,
                    account_code TEXT,
                    debit REAL DEFAULT 0,
                    credit REAL DEFAULT 0,
                    FOREIGN KEY(account_code) REFERENCES accounts(code)
                )
            ''')

            # Bảng phiếu nhập kho
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    product_code TEXT,
                    quantity REAL,
                    unit_price REAL,
                    supplier TEXT,
                    FOREIGN KEY(product_code) REFERENCES products(code)
                )
            ''')

            # Bảng license
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    hardware_id TEXT PRIMARY KEY,
                    license_key TEXT,
                    status TEXT,
                    created_date TEXT,
                    user_name TEXT,
                    user_phone TEXT,
                    user_email TEXT
                )
            ''')

            # Bảng lịch sử khách hàng
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customer_history (
                    name TEXT PRIMARY KEY,
                    phone TEXT,
                    address TEXT,
                    purchase_count INTEGER DEFAULT 1,
                    last_updated TEXT
                )
            ''')

            # Bảng categories (danh mục giao dịch) - THÊM MỚI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            ''')

            # Tạo dữ liệu mẫu cho tài khoản kế toán nếu bảng rỗng
            cursor.execute("SELECT COUNT(*) FROM accounts")
            if cursor.fetchone()[0] == 0:
                default_accounts = [
                    ("111", "Tiền mặt", "Tài sản"),
                    ("112", "Tiền gửi ngân hàng", "Tài sản"),
                    ("131", "Phải thu khách hàng", "Tài sản"),
                    ("156", "Hàng hóa", "Tài sản"),
                    ("211", "TSCĐ hữu hình", "Tài sản"),
                    ("331", "Phải trả người bán", "Nợ phải trả"),
                    ("411", "Vốn đầu tư của CSH", "Vốn chủ sở hữu"),
                    ("511", "Doanh thu bán hàng", "Doanh thu"),
                    ("632", "Giá vốn hàng bán", "Chi phí"),
                    ("642", "Chi phí quản lý kinh doanh", "Chi phí")
                ]
                cursor.executemany("INSERT INTO accounts (code, name, type) VALUES (?,?,?)", default_accounts)

            # Thêm dữ liệu mặc định cho bảng categories nếu rỗng
            cursor.execute("SELECT COUNT(*) FROM categories")
            if cursor.fetchone()[0] == 0:
                default_categories = [
                    ("Thu từ bán hàng (không hóa đơn)", "Thu"),
                    ("Thu nợ khách hàng", "Thu"),
                    ("Thu ứng trước", "Thu"),
                    ("Thu hóa đơn", "Thu"),
                    ("Thu khác", "Thu"),
                    ("Mua cá cơm tươi", "Chi"),
                    ("Mua muối biển", "Chi"),
                    ("Mua chai thủy tinh", "Chi"),
                    ("Mua nắp/nhãn", "Chi"),
                    ("Mua bao bì", "Chi"),
                    ("Mua chum vại", "Chi"),
                    ("Mua miếng ni lông", "Chi"),
                    ("Mua văn phòng phẩm", "Chi"),
                    ("Tiền công ủ muối", "Chi"),
                    ("Vệ sinh nhà thùng", "Chi"),
                    ("Điện/nước sản xuất", "Chi"),
                    ("Bảo trì thùng gỗ", "Chi"),
                    ("Vận chuyển thành phẩm", "Chi"),
                    ("Chiết khấu đại lý", "Chi"),
                    ("Quảng cáo truyền thống", "Chi"),
                    ("Lương nhân viên", "Chi"),
                    ("Thuê mặt bằng", "Chi"),
                    ("Khấu hao thiết bị", "Chi"),
                    ("Phí ngân hàng", "Chi"),
                    ("Chi phí khác", "Chi"),
                ]
                cursor.executemany("INSERT INTO categories (name, type) VALUES (?, ?)", default_categories)
                
            # Bảng thông tin hộ kinh doanh (thông tin chủ hộ)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS business_info (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ma_so_thue TEXT UNIQUE NOT NULL,
                    ten_ho_kinh_doanh TEXT NOT NULL,
                    dia_chi TEXT,
                    so_dien_thoai TEXT,
                    email TEXT,
                    loai_hinh TEXT DEFAULT 'Hộ kinh doanh',
                    nhom_doi_tuong TEXT DEFAULT 'group1',
                    ngay_bat_dau_kinh_doanh TEXT,
                    nganh_nghe_kinh_doanh TEXT
                )
            ''')

            # Bảng tài khoản ngân hàng / ví điện tử (cho mẫu 01/BK-STK)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_id INTEGER,
                    ten_ngan_hang TEXT NOT NULL,
                    so_tai_khoan TEXT NOT NULL,
                    so_hieu_vi_dien_tu TEXT,
                    la_tai_khoan_chinh INTEGER DEFAULT 0,
                    ngay_thong_bao TEXT,
                    FOREIGN KEY(business_id) REFERENCES business_info(id)
                )
            ''')

            # Bảng lịch sử nộp hồ sơ thuế (để theo dõi đã nộp gì chưa)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tax_filing_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ma_so_thue TEXT,
                    mau_bieu TEXT,
                    ky_khai TEXT,
                    ngay_nop TEXT,
                    trang_thai TEXT,
                    file_xml_path TEXT,
                    ghi_chu TEXT
                )
            ''')            

            # Bảng kỳ kế toán (để quản lý khóa sổ)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounting_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_closed INTEGER DEFAULT 0,
                    closed_date TEXT
                )
            ''')

            # Bảng bút toán kết chuyển (lưu lịch sử kết chuyển)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS closing_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_id INTEGER,
                    date TEXT NOT NULL,
                    description TEXT,
                    debit_account TEXT,
                    credit_account TEXT,
                    amount REAL,
                    FOREIGN KEY(period_id) REFERENCES accounting_periods(id)
                )
            ''')

            # Bảng tờ khai thuế (lưu lịch sử kê khai)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tax_returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tax_year INTEGER,
                    tax_type TEXT,
                    revenue REAL,
                    tax_amount REAL,
                    submitted_date TEXT,
                    status TEXT
                )
            ''')
            
            # Bảng quản lý khách hàng và license (cho admin)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    package TEXT NOT NULL,
                    license_key TEXT UNIQUE,
                    issued_date TEXT,
                    expiry_date TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    @staticmethod
    def backup(backup_path: str = None) -> bool:
        """Sao lưu database"""
        import shutil
        from datetime import datetime

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"ke_toan_backup_{timestamp}.db")

        # Đảm bảo thư mục backup tồn tại
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)

        # Copy file
        shutil.copy2(DB_PATH, backup_path)
        return backup_path

    @staticmethod
    def vacuum() -> None:
        """Tối ưu database"""
        with Database.get_connection() as conn:
            conn.execute("VACUUM")

    @staticmethod
    def get_table_info(table_name: str) -> list:
        """Lấy thông tin về bảng"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            return cursor.fetchall()

    @staticmethod
    def get_table_count(table_name: str) -> int:
        """Lấy số lượng bản ghi trong bảng"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
            
    @staticmethod
    def save_business_info(data: dict) -> bool:
        """Lưu thông tin doanh nghiệp - tránh trùng lặp"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            
            # Kiểm tra đã tồn tại chưa
            cursor.execute("SELECT id FROM business_info LIMIT 1")
            existing = cursor.fetchone()
            
            if existing:
                # Cập nhật dòng hiện tại
                cursor.execute('''
                    UPDATE business_info SET
                        ma_so_thue = ?,
                        ten_ho_kinh_doanh = ?,
                        dia_chi = ?,
                        so_dien_thoai = ?,
                        email = ?,
                        loai_hinh = ?,
                        nhom_doi_tuong = ?,
                        ngay_bat_dau_kinh_doanh = ?,
                        nganh_nghe_kinh_doanh = ?
                    WHERE id = ?
                ''', (
                    data.get('ma_so_thue'),
                    data.get('ten_ho_kinh_doanh'),
                    data.get('dia_chi'),
                    data.get('so_dien_thoai'),
                    data.get('email'),
                    data.get('loai_hinh', 'Hộ kinh doanh'),
                    data.get('nhom_doi_tuong', 'group1'),
                    data.get('ngay_bat_dau_kinh_doanh'),
                    data.get('nganh_nghe_kinh_doanh'),
                    existing['id']
                ))
            else:
                # Thêm mới
                cursor.execute('''
                    INSERT INTO business_info (
                        ma_so_thue, ten_ho_kinh_doanh, dia_chi, so_dien_thoai,
                        email, loai_hinh, nhom_doi_tuong, ngay_bat_dau_kinh_doanh,
                        nganh_nghe_kinh_doanh
                    ) VALUES (?,?,?,?,?,?,?,?,?)
                ''', (
                    data.get('ma_so_thue'),
                    data.get('ten_ho_kinh_doanh'),
                    data.get('dia_chi'),
                    data.get('so_dien_thoai'),
                    data.get('email'),
                    data.get('loai_hinh', 'Hộ kinh doanh'),
                    data.get('nhom_doi_tuong', 'group1'),
                    data.get('ngay_bat_dau_kinh_doanh'),
                    data.get('nganh_nghe_kinh_doanh')
                ))
            return True

    @staticmethod
    def cleanup_duplicate_business_info() -> None:
        """Xóa các dòng trùng lặp trong business_info, giữ lại dòng đầy đủ nhất"""
        try:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                
                # Lấy tất cả dòng
                cursor.execute("SELECT id, ma_so_thue, ten_ho_kinh_doanh, dia_chi, so_dien_thoai, email FROM business_info")
                rows = cursor.fetchall()
                
                if len(rows) > 1:
                    # Tìm dòng có đầy đủ thông tin nhất
                    best_row = None
                    best_score = -1
                    
                    for row in rows:
                        score = 0
                        if row['ma_so_thue'] and len(str(row['ma_so_thue'])) in [10, 13]:
                            score += 2
                        if row['ten_ho_kinh_doanh']:
                            score += 1
                        if row['dia_chi']:
                            score += 1
                        if row['so_dien_thoai']:
                            score += 1
                        if row['email']:
                            score += 1
                        
                        if score > best_score:
                            best_score = score
                            best_row = row
                    
                    if best_row:
                        # Xóa tất cả trừ dòng tốt nhất
                        cursor.execute("DELETE FROM business_info WHERE id != ?", (best_row['id'],))
                        conn.commit()
                        #print(f"✅ Đã dọn dẹp dữ liệu trùng lặp, giữ lại ID: {best_row['id']}")
                        return True
                return False
        except Exception as e:
            #print(f"❌ Lỗi khi dọn dẹp DB: {e}")
            return False

    @staticmethod
    def close_all_connections() -> None:
        """Đóng tất cả kết nối (hữu ích khi thoát)"""
        # SQLite không có pool connection, chỉ cần đảm bảo các kết nối đã đóng
        pass