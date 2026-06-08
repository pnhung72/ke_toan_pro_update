try:
    from config import VERSION
except ImportError:
    VERSION = '8.0.0'

# ui/license_manager_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from utils.license_manager import (
    get_machine_id, save_customer, export_license_file, get_all_customers
)
from models.database import Database
from theme import get_font
from utils.excel_export import export_to_excel
import os


class LicenseManagerDialog(tk.Toplevel):
    def __init__(self, parent, is_admin=False, active_modules=None):
        #print("[THÁM TỬ] LicenseManagerDialog.__init__ bắt đầu")
        super().__init__(parent)
        self.parent = parent
        self.is_admin = is_admin
        self.active_modules = active_modules if active_modules else []
        #print(f"   is_admin={is_admin}, active_modules={active_modules}")
        
        # === SỬA: Định nghĩa các biến cấu hình trước, không tạo Tkinter vars sớm ===
        self.package_prices = {
            'Cơ bản': 1000000,
            'Chuyên nghiệp': 2000000,
            'Vĩnh viễn': 5000000
        }
        self.extra_features = {
            'marketing': {'title': '🎁 Marketing & Coupon', 'price': 500000},
            'distribution': {'title': '🚚 Quản lý Phân phối', 'price': 1000000},
            'ai_analytics': {'title': '📈 Phân tích AI', 'price': 700000},
            'email_auto': {'title': '✉️ Tự động hóa Email', 'price': 300000},
            'invoice_scanner': {'title': '📥 Tự động hóa hóa đơn đầu vào (Quét email XML)', 'price': 400000},
            'gas_station': {'title': '⛽ Quản lý Trạm Xăng Dầu', 'price': 800000},   # Thêm
            'production_yatrang': {'title': '🐟 Sản Xuất Nước Mắm YaTrang', 'price': 1000000},  # Thêm
        }
                
        # === SỬA: Khởi tạo các biến Tkinter SAU KHI đã có master (self) và tránh gọi hàm chưa có ===
        # Lưu ý: Không gọi self.load_license_info() ở đây nữa, vì nó chưa được định nghĩa.
        # Nếu cần, có thể định nghĩa hàm rỗng hoặc bỏ qua.
        
        # Thiết lập cửa sổ trước khi tạo widget
        if self.is_admin:
            self.title(f"ADMIN: Cấu hình hệ thống {VERSION}")
            self.geometry("900x750")
        else:
            self.title("THÔNG TIN BẢN QUYỀN CỦA BẠN")
            self.geometry("600x750")
        #print("   Đã thiết lập title và geometry")
        
        # Khởi tạo các biến Tkinter với master=self
        self.selected_package = tk.StringVar(master=self, value='Cơ bản')
        self.addon_vars = {}
        self.feature_vars = {}
        # Các biến khác (nếu cần cho chức năng trial, có thể bỏ qua hoặc định nghĩa sau)
        self.is_trial = tk.BooleanVar(master=self, value=True)
        self.status_var = tk.StringVar(master=self, value="Chưa kích hoạt")
        self.expiry_var = tk.StringVar(master=self, value="Không có")
        self.key_entry_var = tk.StringVar(master=self, value="")
        self.days_left_var = tk.StringVar(master=self, value="0 ngày")
        self.active_modules_var = tk.StringVar(master=self, value="")
        #print("   Đã tạo các biến Tkinter")
        
        # Vẽ giao diện
        self.create_widgets()
        #print("   Đã tạo widgets")
        
        # Chỉ gọi grab_set sau khi mọi thứ đã sẵn sàng
        self.transient(parent)
        self.grab_set()
        #print("[THÁM TỬ] LicenseManagerDialog.__init__ kết thúc")
        
    def show_error_safe(self, title, message):
        """Hiển thị thông báo lỗi an toàn khi root đang bị ẩn"""
        def _show():
            dummy = tk.Toplevel(self.parent)
            dummy.withdraw()
            messagebox.showerror(title, message, parent=dummy)
            dummy.destroy()
        self.parent.after(100, _show)
        
    def get_trial_status(self):
        """Lấy thông tin trạng thái dùng thử (trial)"""
        from pathlib import Path
        from datetime import datetime
        import os
        
        # Xác định đường dẫn file trial.dat (giống như trong main.py)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        real_data_dir = os.path.join(base_dir, "ke_toan_data")
        trial_file = Path(real_data_dir) / "trial.dat"
        
        if not trial_file.exists():
            return "Chưa kích hoạt dùng thử (lần đầu chạy phần mềm)"
        try:
            with open(trial_file, "r") as f:
                start_str = f.read().strip()
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            days_left = 30 - (datetime.now() - start_date).days
            if days_left > 0:
                return f"✅ Đang dùng thử: còn {days_left} ngày"
            else:
                return "❌ Hết hạn dùng thử. Vui lòng mua bản quyền."
        except Exception as e:
            return f"⚠️ Không thể đọc thông tin dùng thử: {e}"
        
    def create_widgets(self):
        #print("[THÁM TỬ] create_widgets bắt đầu")
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="THÔNG TIN BẢN QUYỀN", font=get_font("title"), foreground="#2196F3").pack(pady=10)
        
        if not self.is_admin:
            machine_id = get_machine_id()
            ttk.Label(main_frame, text=f"Mã máy: {machine_id}").pack()
            
            # === HIỂN THỊ TRẠNG THÁI DÙNG THỬ ===
            trial_status = self.get_trial_status()
            trial_label = ttk.Label(main_frame, text=trial_status, font=get_font("label"), foreground="green")
            if "Hết hạn" in trial_status:
                trial_label.config(foreground="red")
            elif "Chưa kích hoạt" in trial_status:
                trial_label.config(foreground="orange")
            trial_label.pack(pady=5)

            pkg_frame = ttk.LabelFrame(main_frame, text="Chọn Gói Bản Quyền", padding=10)
            pkg_frame.pack(fill="x", pady=10)
            for pkg, price in self.package_prices.items():
                ttk.Radiobutton(pkg_frame, text=f"{pkg} ({price:,}đ)", 
                                variable=self.selected_package, value=pkg, 
                                command=self.update_total).pack(anchor="w")

            addon_frame = ttk.LabelFrame(main_frame, text="Tiện ích mua thêm", padding=10)
            addon_frame.pack(fill="x", pady=10)
            for key, info in self.extra_features.items():
                var = tk.BooleanVar(master=self)
                self.addon_vars[key] = var
                ttk.Checkbutton(addon_frame, text=f"{info['title']} ({info['price']:,}đ)", 
                                variable=var, command=self.update_total).pack(anchor="w")

            # === YÊU CẦU TÍNH NĂNG RIÊNG ===
            req_frame = ttk.LabelFrame(main_frame, text="📝 Yêu cầu tính năng riêng (nếu có)", padding=10)
            req_frame.pack(fill="x", pady=10)
            self.custom_request_text = tk.Text(req_frame, height=5, font=get_font("label"), wrap=tk.WORD)
            self.custom_request_text.pack(fill="both", expand=True, padx=5, pady=5)
            ttk.Label(req_frame, text="Mô tả chi tiết tính năng bạn cần thêm (ví dụ: theo dõi hạn sử dụng, quản lý lô hàng, báo giá tự động...):", 
                      font=get_font("small")).pack(anchor="w", padx=5)
                                
            self.lbl_total = ttk.Label(main_frame, text="Tổng tiền: 1,000,000 VND", 
                                       font=("Arial", 12, "bold"), foreground="red")
            self.lbl_total.pack(pady=10)
            
            # === Ô nhập license key và nút kích hoạt ===
            key_frame = ttk.LabelFrame(main_frame, text="Nhập mã kích hoạt (nếu có)", padding=10)
            key_frame.pack(fill="x", pady=10)
            
            self.license_key_entry = ttk.Entry(key_frame, width=50, font=get_font("label"))
            self.license_key_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
            
            def activate_license():
                key = self.license_key_entry.get().strip()
                if not key:
                    messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập mã kích hoạt")
                    return
                # Gọi hàm xử lý kích hoạt (cần viết thêm)
                from utils.license_manager import activate_license_key
                success, msg = activate_license_key(key)
                messagebox.showinfo("Kết quả", msg)
                if success:
                    # Tải lại giao diện hoặc thông báo khởi động lại
                    pass
            
            ttk.Button(key_frame, text="Kích hoạt", command=activate_license).pack(side=tk.LEFT, padx=5)
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="📩 Gửi Email", command=lambda: self.send_contact("email")).pack(side="left", padx=5)
            ttk.Button(btn_frame, text="💬 Liên hệ Zalo", command=lambda: self.send_contact("zalo")).pack(side="left", padx=5)
        else:
            self.create_admin_panel(main_frame)
        #print("[THÁM TỬ] create_widgets kết thúc")
    
    def create_admin_panel(self, parent):
        #print("[THÁM TỬ] create_admin_panel bắt đầu")
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, pady=10)
        
        tab_create = ttk.Frame(notebook)
        notebook.add(tab_create, text="Tạo license")
        self.create_tab_create(tab_create)
        
        tab_list = ttk.Frame(notebook)
        notebook.add(tab_list, text="Danh sách khách hàng")
        self.create_tab_list(tab_list)
        #print("[THÁM TỬ] create_admin_panel kết thúc")
    
    def create_tab_create(self, parent):
        #print("[THÁM TỬ] create_tab_create bắt đầu")
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Nhập mã máy khách hàng:", font=get_font("label")).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_machine = ttk.Entry(frame, width=60, font=get_font("label"))
        self.entry_machine.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(frame, text="Họ tên khách hàng:", font=get_font("label")).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_name = ttk.Entry(frame, width=60, font=get_font("label"))
        self.entry_name.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(frame, text="Email:", font=get_font("label")).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_email = ttk.Entry(frame, width=60, font=get_font("label"))
        self.entry_email.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(frame, text="SĐT:", font=get_font("label")).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_phone = ttk.Entry(frame, width=60, font=get_font("label"))
        self.entry_phone.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        ttk.Label(frame, text="Gói sản phẩm:", font=get_font("label")).grid(row=4, column=0, sticky="w", pady=5)
        self.combo_package = ttk.Combobox(frame, values=["basic", "pro", "enterprise"], state="readonly", font=get_font("label"))
        self.combo_package.grid(row=4, column=1, padx=10, pady=5, sticky="w")
        self.combo_package.current(0)
        self.combo_package.bind("<<ComboboxSelected>>", self.recalculate_total)
        
        ttk.Label(frame, text="Thời hạn:", font=get_font("label")).grid(row=5, column=0, sticky="w", pady=5)
        self.combo_expiry = ttk.Combobox(frame, values=["Vĩnh viễn", "1 năm", "6 tháng"], state="readonly", font=get_font("label"))
        self.combo_expiry.grid(row=5, column=1, padx=10, pady=5, sticky="w")
        self.combo_expiry.current(0)

        ext_frame = ttk.LabelFrame(frame, text="📦 TIỆN ÍCH MỞ RỘNG (GỌI MÓN THÊM)", padding=10)
        ext_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=15)
        for i, (key, info) in enumerate(self.extra_features.items()):
            var = tk.BooleanVar(master=self)
            self.feature_vars[key] = var
            chk = ttk.Checkbutton(ext_frame, text=f"{info['title']} (+{info['price']:,}đ)", 
                                  variable=var, command=self.recalculate_total)
            chk.grid(row=i//2, column=i%2, sticky="w", padx=30, pady=5)

        self.lbl_total = ttk.Label(frame, text="THÀNH TIỀN: 0 VNĐ", 
                                   font=get_font("title"), foreground="#d32f2f")
        self.lbl_total.grid(row=7, column=0, columnspan=2, pady=10)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Tạo license và lưu", command=self.create_license).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Xuất file license.key", command=self.export_license).pack(side="left", padx=10)
        
        self.status_label = ttk.Label(frame, text="", font=get_font("label"), foreground="green")
        self.status_label.grid(row=9, column=0, columnspan=2, pady=5)
        
        self.recalculate_total()
        #print("[THÁM TỬ] create_tab_create kết thúc")
        
    def recalculate_total(self, event=None):
        package_prices = {"basic": 1000000, "pro": 2500000, "enterprise": 5000000}
        base_price = package_prices.get(self.combo_package.get(), 1000000)
        extra_total = sum(info['price'] for key, info in self.extra_features.items() if self.feature_vars[key].get())
        final_total = base_price + extra_total
        self.lbl_total.config(text=f"THÀNH TIỀN: {final_total:,} VNĐ")
    
    def create_tab_list(self, parent):
        #print("[THÁM TỬ] create_tab_list bắt đầu")
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill="both", expand=True)
        
        columns = ("ID", "Mã máy", "Họ tên", "Email", "SĐT", "Gói", "Ngày cấp", "Hạn", "Trạng thái")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        col_widths = [50, 180, 150, 150, 100, 80, 100, 100, 100]
        anchors = ["center", "center", "w", "w", "center", "center", "center", "center", "center"]
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[i], anchor=anchors[i])
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.load_customers()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="Làm mới", command=self.load_customers).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Xuất Excel", command=self.export_customers).pack(side="left", padx=5)
        #print("[THÁM TỬ] create_tab_list kết thúc")
    
    def load_customers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        customers = get_all_customers()
        for row in customers:
            status = row['status']
            status_text = "🟢 Hoạt động" if status == "active" else ("🔴 Hết hạn" if status == "expired" else "⚫ Đã khóa")
            expiry = row['expiry_date'] if row['expiry_date'] else "Vĩnh viễn"
            self.tree.insert("", "end", values=(
                row['id'], row['machine_id'], row['full_name'], row['email'],
                row['phone'], row['package'], row['issued_date'][:10] if row['issued_date'] else "",
                expiry, status_text
            ))
    
    def create_license(self):
        #print("[THÁM TỬ] create_license được gọi")
        machine_id = self.entry_machine.get().strip()
        name = self.entry_name.get().strip()
        email = self.entry_email.get().strip()
        phone = self.entry_phone.get().strip()
        package = self.combo_package.get()
        expiry_option = self.combo_expiry.get()
        
        if not machine_id or not name:
            self.parent.after(100, lambda: messagebox.showerror("Lỗi", "Vui lòng nhập mã máy và họ tên khách hàng", parent=self.parent if self.parent.winfo_exists() else None))
            return
        
        expiry_date = None
        if expiry_option == "1 năm":
            expiry_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        elif expiry_option == "6 tháng":
            expiry_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        
        try:
            license_key = save_customer(machine_id, name, email, phone, package, expiry_date)
            self.status_label.config(text=f"Đã tạo license: {license_key}", foreground="green")
            self.load_customers()
        except Exception as e:
            self.status_label.config(text=f"Lỗi: {str(e)}", foreground="red")
    
    def export_license(self):
        #print("[THÁM TỬ] export_license được gọi")
        machine_id = self.entry_machine.get().strip()
        package = self.combo_package.get()
        expiry_option = self.combo_expiry.get()
        
        expiry_date = None
        if expiry_option == "1 năm":
            expiry_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        elif expiry_option == "6 tháng":
            expiry_date = (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
        
        if not machine_id:
            self.parent.after(100, lambda: messagebox.showerror("Lỗi", "Nhập mã máy trước khi xuất file", parent=self.parent if self.parent.winfo_exists() else None))
            return

        selected_modules = []
        if hasattr(self.parent, 'active_module_ids') and self.parent.active_module_ids:
            selected_modules = self.parent.active_module_ids

        selected_features = [key for key, var in self.feature_vars.items() if var.get()]
        all_features = selected_modules + selected_features
        features_str = ",".join(all_features)

        file_path = export_license_file(machine_id, package, expiry_date, features=features_str)

        msg = f"Đã xuất license.key tại:\n{file_path}"
        if selected_modules:
            msg += f"\n\n📦 Module ngành nghề đã chọn: {', '.join(selected_modules)}"
        if selected_features:
            feature_titles = [self.extra_features[f]['title'] for f in selected_features]
            msg += f"\n🎁 Tiện ích mở rộng: {', '.join(feature_titles)}"

        self.parent.after(100, lambda: messagebox.showinfo("Thành công", msg, parent=self.parent if self.parent.winfo_exists() else None))
        self.status_label.config(text=f"Đã xuất file {file_path}", foreground="green")
    
    def export_customers(self):
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            data.append({
                "ID": values[0], "Mã máy": values[1], "Họ tên": values[2],
                "Email": values[3], "SĐT": values[4], "Gói": values[5],
                "Ngày cấp": values[6], "Hạn": values[7], "Trạng thái": values[8]
            })
        if data:
            export_to_excel(data, list(data[0].keys()), "Danh_sach_khach_hang")
        else:
            self.parent.after(100, lambda: messagebox.showinfo("Thông báo", "Không có dữ liệu để xuất", parent=self.parent if self.parent.winfo_exists() else None))
    
    def copy_to_clipboard(self, text):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(text)
        self.parent.after(100, lambda: messagebox.showinfo("Đã sao chép", "Mã máy đã được sao chép vào clipboard", parent=self.parent if self.parent.winfo_exists() else None))
        
    def update_total(self):
        total = self.package_prices.get(self.selected_package.get(), 0)
        for key, var in self.addon_vars.items():
            if var.get():
                total += self.extra_features[key]['price']
        self.lbl_total.config(text=f"Tổng tiền: {total:,} VND")

    def send_contact(self, method):
        ten_khach = "Khách hàng"
        selected_pkg = self.selected_package.get()
        tong_tien = self.lbl_total.cget('text')
        ma_may = get_machine_id()
        
        features = [self.extra_features[key]['title'] for key, var in self.addon_vars.items() if var.get()]
        str_features = ", ".join(features) if features else "Không có"

        # Lấy yêu cầu riêng (nếu có widget)
        custom_section = ""
        if hasattr(self, 'custom_request_text'):
            custom_request = self.custom_request_text.get("1.0", tk.END).strip()
            if custom_request:
                custom_section = f"\n\n📌 YÊU CẦU RIÊNG:\n{custom_request}"

        noi_dung = f"""--- HỢP ĐỒNG TẠM THỜI: MUA BẢN QUYỀN KẾ TOÁN PRO ---
Người mua: {ten_khach}
Gói dịch vụ: {selected_pkg}
Tính năng mua thêm: {str_features}{custom_section}
{tong_tien}
Mã máy: {ma_may}
-------------------------------------------------------
Gửi cho: Phan Ngọc Hùng (0982493474)
Email: yatrangmn@gmail.com
"""

        base_path = os.getcwd()
        file_path = os.path.join(base_path, "hop_dong_tam_thoi.txt")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(noi_dung)
            os.startfile(file_path)
        except Exception as e:
            self.parent.after(100, lambda: messagebox.showwarning("Thông báo", f"Lỗi tạo/mở file: {e}", parent=self.parent if self.parent.winfo_exists() else None))

        import webbrowser
        if method == "email":
            subject = "Dang ky ban quyen Ke Toan Pro"
            webbrowser.open(f"mailto:yatrangmn@gmail.com?subject={subject}")
        elif method == "zalo":
            webbrowser.open("https://zalo.me/0982493474")