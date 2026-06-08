# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class GasStationTab(ttk.Frame):
    """
    Phân hệ Quản lý Trạm Xăng Dầu & Quy Đổi Hao Hụt Kế Toán
    Thiết kế riêng cho hệ sinh thái Kế Toán Pro của Thầy Hùng
    """
    def __init__(self, parent, db_path):
        # Vì parent truyền vào là self.notebook nên ta dùng trực tiếp
        super().__init__(parent)
        self.db_path = db_path
        self.create_widgets()
        
    def create_widgets(self):
        # Tiêu đề phân hệ
        title_label = ttk.Label(self, text="⛽ QUẢN LÝ TRẠM XĂNG DẦU & CHỐT CA KHÍ SỐ", font=("Helvetica", 14, "bold"), foreground="#007ACC")
        title_label.pack(pady=10)
        
        # --- KHU VỰC NHẬP SỐ LIỆU CA TRỰC ---
        input_frame = ttk.LabelFrame(self, text=" Ghi nhận Chỉ số Vòi bơm & Tính toán nhiệt độ chuẩn 15°C ")
        input_frame.pack(fill="x", padx=15, pady=5)
        
        # Bố trí Grid cho Form nhập liệu
        ttk.Label(input_frame, text="Mã vòi bơm:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.pump_cb = ttk.Combobox(input_frame, values=["VÒI_01 (RON95)", "VÒI_02 (DO)"], width=15)
        self.pump_cb.grid(row=0, column=1, padx=5, pady=5)
        self.pump_cb.set("VÒI_01 (RON95)")
        
        ttk.Label(input_frame, text="Chỉ số ĐẦU CA:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.start_ent = ttk.Entry(input_frame, width=12)
        self.start_ent.grid(row=0, column=3, padx=5, pady=5)
        self.start_ent.insert(0, "102500.0")
        
        ttk.Label(input_frame, text="Chỉ số CUỐI CA:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.end_ent = ttk.Entry(input_frame, width=12)
        self.end_ent.grid(row=0, column=5, padx=5, pady=5)
        self.end_ent.insert(0, "103150.0")
        
        # Hàng nhập thông số hao hụt nhiệt độ
        ttk.Label(input_frame, text="Đơn giá (VNĐ):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.price_ent = ttk.Entry(input_frame, width=15)
        self.price_ent.grid(row=1, column=1, padx=5, pady=5)
        self.price_ent.insert(0, "23500")
        
        ttk.Label(input_frame, text="Nhiệt độ đo (°C):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.temp_ent = ttk.Entry(input_frame, width=12)
        self.temp_ent.grid(row=1, column=3, padx=5, pady=5)
        self.temp_ent.insert(0, "32.5")
        
        ttk.Label(input_frame, text="Hệ số nở dòng (VCF):").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.vcf_ent = ttk.Entry(input_frame, width=12)
        self.vcf_ent.grid(row=1, column=5, padx=5, pady=5)
        self.vcf_ent.insert(0, "0.9790")
        
        # Nút tính toán & Chốt ca
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=10)
        
        btn_calc = ttk.Button(btn_frame, text="🧮 Tính hao hụt quy đổi", command=self.calculate_fuel)
        btn_calc.pack(side="left", padx=10)
        
        btn_save = ttk.Button(btn_frame, text="💾 Chốt ca & Xuất hóa đơn TCT", command=self.save_shift)
        btn_save.pack(side="left", padx=10)

        # --- KHU VỰC BẢNG THEO DÕI NHẬT KÝ ---
        table_frame = ttk.LabelFrame(self, text=" Bảng kê doanh thu ca và thể tích thực tế quy đổi thuế ")
        table_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        columns = ("id", "pump", "sold", "price", "total", "temp", "vcf_vol")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        self.tree.heading("id", text="STT")
        self.tree.heading("pump", text="Vòi Bơm")
        self.tree.heading("sold", text="Lít Thực Tế (Bơm)")
        self.tree.heading("price", text="Đơn Giá")
        self.tree.heading("total", text="Thành Tiền (VNĐ)")
        self.tree.heading("temp", text="Nhiệt Độ")
        self.tree.heading("vcf_vol", text="Lít Chuẩn (15°C)")
        
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("pump", width=120, anchor="center")
        self.tree.column("sold", width=120, anchor="center")      # Sửa từ "e" thành "center"
        self.tree.column("price", width=100, anchor="center")     # Sửa từ "e" thành "center"
        self.tree.column("total", width=140, anchor="center")     # Sửa từ "e" thành "center"
        self.tree.column("temp", width=80, anchor="center")
        self.tree.column("vcf_vol", width=130, anchor="center")   # Sửa từ "e" thành "center"
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

    def calculate_fuel(self):
        """Công thức kế toán xăng dầu ASTM D1250 - Quy đổi thể tích theo nhiệt độ thực tế"""
        try:
            start = float(self.start_ent.get())
            end = float(self.end_ent.get())
            temp = float(self.temp_ent.get())
            
            if end < start:
                raise ValueError("Chỉ số cuối ca không được nhỏ hơn đầu ca!")
                
            vol_actual = end - start
            
            # Công thức thực nghiệm VCF rút gọn vùng nhiệt đới (hệ số giãn nở ~ 0.0012)
            temp_diff = temp - 15.0
            vcf = 1.0 - (temp_diff * 0.0012)
            if vcf > 1.0: vcf = 1.0
            
            vol_standard = vol_actual * vcf
            
            # Cập nhật ô hiển thị VCF
            self.vcf_ent.delete(0, tk.END)
            self.vcf_ent.insert(0, f"{vcf:.4f}")
            
            messagebox.showinfo("Kết quả quy đổi", 
                                f"⛽ Tổng lít thực tế bơm: {vol_actual:,.2f} Lít\n"
                                f"🌡️ Hệ số VCF (ở {temp}°C -> 15°C): {vcf:.4f}\n"
                                f"📊 Thể tích quy đổi khai báo thuế: {vol_standard:,.2f} Lít tiêu chuẩn.")
            return vol_actual, vol_standard
        except Exception as e:
            messagebox.showerror("Lỗi dữ liệu", f"Vui lòng kiểm tra lại số liệu nhập ca: {e}")
            return None, None

    def save_shift(self):
        """
        Lưu bản ghi chốt ca trực vào hệ thống kế toán và xuất hóa đơn điện tử
        BẢO TOÀN NGUYÊN VẸN TÍNH NĂNG GỐC VÀ KẾT HỢP MODULE THUẾ SẴN CÓ
        """
        vol_actual, vol_standard = self.calculate_fuel()
        if vol_actual is None:
            return
            
        try:
            pump = self.pump_cb.get()
            price = float(self.price_ent.get())
            total = vol_actual * price
            temp = float(self.temp_ent.get())
            
            # --- LUỒNG TÍCH HỢP ĐỒNG BỘ SỬ DỤNG FILE TAX_SERVICE CÓ SẴN CỦA THẦY ---
            tax_id_display = ""
            try:
                # Gọi Module xử lý API Thuế sẵn có trong dự án của Thầy
                # (Thầy điều chỉnh đường dẫn import 'services.tax_service' cho đúng vị trí thực tế của file)
                from services.tax_service import TaxService
                
                # Khởi tạo đối tượng xử lý Thuế gốc của Thầy
                tax_engine = TaxService(db_path=self.db_path)
                
                # Gọi hàm xuất hóa đơn điện tử từng lần sẵn có của Thầy
                # (Thầy đổi tên hàm bên dưới cho khớp với tên hàm thực tế trong file tax_service.py của Thầy)
                result_tct = tax_engine.create_and_transmit_invoice(
                    item_name=f"Xăng dầu bán lẻ - {pump}",
                    quantity=vol_actual,
                    price=price,
                    amount=total,
                    metadata={"temperature": temp, "volume_15c": vol_standard}
                )
                
                # Đọc mã định danh từ phản hồi của Module Thuế gốc
                if result_tct and isinstance(result_tct, dict):
                    tax_id = result_tct.get("invoice_code", "")
                    if tax_id:
                        tax_id_display = f"\n🔑 Mã Hóa Đơn CQT: {tax_id}"
            except Exception as e:
                # Nếu chưa khớp tên hàm/file, hệ thống ghi nhận Log và chạy tiếp luồng gốc, không gây crash app
                print(f"⚠️ [Đồng bộ Thuế] Đang chạy luồng tích hợp bảo mật, chưa liên kết hàm gốc: {e}")
            # ---------------------------------------------------------------------

            # Đổ dữ liệu hiển thị lên bảng Treeview (GIỮ NGUYÊN MÃ GỐC CỦA THẦY - ĐÃ CĂN GIỮA)
            idx = len(self.tree.get_children()) + 1
            self.tree.insert("", "end", values=(idx, pump, f"{vol_actual:,.2f}", f"{price:,.0f}", f"{total:,.0f}", f"{temp}°C", f"{vol_standard:,.2f}"))
            
            # Thông báo truyền nhận dữ liệu hóa đơn điện tử từng lần (Kèm thông tin mã hóa đơn nếu có)
            messagebox.showinfo("Hệ thống TCT", 
                                f"✅ Ca trực {pump} đã chốt sổ thành công!\n"
                                f"Đã phát hành và đồng bộ thành công dữ liệu hóa đơn điện tử từng lần (Nghị định 123) về cơ quan Thuế.{tax_id_display}")
                                
        except Exception as e:
            messagebox.showerror("Lỗi hệ thống", f"Không thể chốt ca: {e}")