# -*- coding: utf-8 -*-
"""
ReportExportTab - Xuất báo cáo
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from views.tabs.base_tab import BaseTab
from services.report_service import ReportService
from services.transaction_service import TransactionService
from services.invoice_service import InvoiceService
from services.debt_service import DebtService
from datetime import datetime
import os
import pandas as pd
from utils.license import is_full_version
from theme import get_font

class ReportExportTab(BaseTab):
    """Tab xuất báo cáo"""
    
    def __init__(self, parent, notebook, controller=None):
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tạo giao diện xuất báo cáo"""
        self.frame = ttk.Frame(self)
        # === STYLE CHO FONT LỚN ===
        style = ttk.Style()
        style.configure("Export.TLabelframe.Label", font=get_font("bold"))
        style.configure("Export.TButton", font=get_font("label"), padding=8)
        style.configure("Export.TLabel", font=get_font("label"))
        style.configure("Export.TEntry", font=get_font("label"))
        style.configure("Export.TCombobox", font=get_font("label"))
        
        # Tạo khung cuộn chính
        canvas = tk.Canvas(self.frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(canvas)
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
        title_frame.pack(pady=(0, 20))
        ttk.Label(title_frame, text="📊 XUẤT BÁO CÁO", 
                  font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Chọn loại báo cáo và tham số để xuất file", 
                  font=get_font("label"), foreground="gray").pack()
        
        # === KHUNG CHỌN LOẠI BÁO CÁO ===
        type_frame = ttk.LabelFrame(content_frame, text="📋 Chọn loại báo cáo", 
                                    style="Export.TLabelframe", padding=15)
        type_frame.pack(fill="x", pady=10)
        
        self.report_type_var = tk.StringVar(value="revenue")
        
        report_types = [
            ("💰 Doanh thu", "revenue"),
            ("📋 Công nợ", "debt"),
            ("🏛️ Thuế", "tax"),
            ("📦 Hàng tồn kho", "inventory"),
            ("📊 Báo cáo tổng hợp", "summary")
        ]
        
        for i, (text, value) in enumerate(report_types):
            col = i % 3
            row = i // 3
            rb = ttk.Radiobutton(type_frame, text=text, variable=self.report_type_var, 
                                 value=value, style="Export.TLabel")
            rb.grid(row=row, column=col, padx=20, pady=10, sticky="w")
        
        # === KHUNG THAM SỐ ===
        param_frame = ttk.LabelFrame(content_frame, text="⚙️ Tham số báo cáo", 
                                     style="Export.TLabelframe", padding=15)
        param_frame.pack(fill="x", pady=10)
        
        # Dòng 1: Năm
        row1 = ttk.Frame(param_frame)
        row1.pack(fill="x", pady=8)
        ttk.Label(row1, text="Năm:", font=get_font("label"), width=10).pack(side="left")
        self.year_var = tk.StringVar(value=str(datetime.now().year))
        self.year_combo = ttk.Combobox(row1, values=[str(y) for y in range(2023, 2030)], 
                                       width=10, state="readonly", style="Export.TCombobox")
        self.year_combo.pack(side="left", padx=10)
        self.year_combo.set(str(datetime.now().year))
        
        # Dòng 2: Tháng (cho báo cáo doanh thu)
        row2 = ttk.Frame(param_frame)
        row2.pack(fill="x", pady=8)
        ttk.Label(row2, text="Tháng:", font=get_font("label"), width=10).pack(side="left")
        self.month_var = tk.StringVar(value=str(datetime.now().month))
        self.month_combo = ttk.Combobox(row2, values=[str(m) for m in range(1, 13)], 
                                        width=10, state="readonly", style="Export.TCombobox")
        self.month_combo.pack(side="left", padx=10)
        self.month_combo.set(str(datetime.now().month))
        
        # Dòng 3: Quý (cho báo cáo theo quý)
        row3 = ttk.Frame(param_frame)
        row3.pack(fill="x", pady=8)
        ttk.Label(row3, text="Quý:", font=get_font("label"), width=10).pack(side="left")
        self.quarter_var = tk.StringVar(value="1")
        self.quarter_combo = ttk.Combobox(row3, values=["1", "2", "3", "4"], 
                                          width=10, state="readonly", style="Export.TCombobox")
        self.quarter_combo.pack(side="left", padx=10)
        self.quarter_combo.set("1")
        
        # === KHUNG ĐỊNH DẠNG XUẤT ===
        format_frame = ttk.LabelFrame(content_frame, text="📄 Định dạng xuất", 
                                      style="Export.TLabelframe", padding=15)
        format_frame.pack(fill="x", pady=10)
        
        self.format_var = tk.StringVar(value="excel")
        
        formats = [
            ("📊 Excel (.xlsx)", "excel"),
            ("📄 XML (.xml)", "xml"),
            ("📝 CSV (.csv)", "csv")
        ]
        
        for i, (text, value) in enumerate(formats):
            rb = ttk.Radiobutton(format_frame, text=text, variable=self.format_var, 
                                 value=value, style="Export.TLabel")
            rb.pack(side="left", padx=30, pady=10)
        
        # === NÚT XUẤT ===
        btn_frame = ttk.Frame(content_frame)
        btn_frame.pack(pady=20)
        
        export_btn = ttk.Button(btn_frame, text="📥 XUẤT BÁO CÁO", 
                                command=self.export_report, style="Export.TButton", width=25)
        export_btn.pack(pady=10)
        
        # === HƯỚNG DẪN ===
        guide_frame = ttk.LabelFrame(content_frame, text="📌 Hướng dẫn", 
                                     style="Export.TLabelframe", padding=15)
        guide_frame.pack(fill="x", pady=10)
        
        guide_text = """
        • Chọn loại báo cáo phù hợp
        • Chọn năm/tháng/quý cần xuất
        • Chọn định dạng file (Excel, XML, CSV)
        • Nhấn "Xuất báo cáo" để lưu file
        • File sẽ được lưu tại thư mục bạn chọn
        """
        ttk.Label(guide_frame, text=guide_text, font=get_font("small"), 
                  foreground="#666", justify="left").pack(anchor="w", pady=5)
        
        # Status label
        self.status_label = ttk.Label(content_frame, text="", foreground="green", 
                                      font=get_font("label"))
        self.status_label.pack(pady=10)
    
    def export_report(self):
        """Xuất báo cáo theo lựa chọn"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức.\nVui lòng liên hệ để mua.")
            return
        
        report_type = self.report_type_var.get()
        file_format = self.format_var.get()
        
        # Hiển thị đang xử lý
        self.status_label.config(text="⏳ Đang xuất báo cáo...", foreground="blue")
        self.frame.update()
        
        try:
            if report_type == "revenue":
                self.export_revenue_report(file_format)
            elif report_type == "debt":
                self.export_debt_report(file_format)
            elif report_type == "tax":
                self.export_tax_report(file_format)
            elif report_type == "inventory":
                self.export_inventory_report(file_format)
            elif report_type == "summary":
                self.export_summary_report(file_format)
            else:
                messagebox.showerror("Lỗi", "Loại báo cáo không hợp lệ")
        except Exception as e:
            self.status_label.config(text=f"❌ Lỗi: {str(e)}", foreground="red")
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo:\n{str(e)}")
    
    def export_revenue_report(self, file_format):
        """Xuất báo cáo doanh thu"""
        year = self.year_var.get()
        month = self.month_var.get()
        quarter = self.quarter_var.get()
        
        # Lấy dữ liệu
        revenue = ReportService.get_total_income()
        expense = ReportService.get_total_expense()
        profit = revenue - expense
        
        data = [
            ["Chỉ tiêu", "Giá trị (VNĐ)"],
            ["Tổng doanh thu", f"{revenue:,.0f}".replace(",", ".")],
            ["Tổng chi phí", f"{expense:,.0f}".replace(",", ".")],
            ["Lợi nhuận", f"{profit:,.0f}".replace(",", ".")]
        ]
        
        filename = f"Bao_cao_doanh_thu_{year}_{month}"
        self.save_report(data, filename, file_format, "Doanh thu")
    
    def export_debt_report(self, file_format):
        """Xuất báo cáo công nợ"""
        try:
            debt_data = DebtService.get_debt_summary()
            
            data = [
                ["Chỉ tiêu", "Giá trị (VNĐ)"],
                ["Tổng công nợ", f"{debt_data.get('total_debt', 0):,.0f}".replace(",", ".")],
                ["Đã thanh toán", f"{debt_data.get('paid', 0):,.0f}".replace(",", ".")],
                ["Quá hạn", f"{debt_data.get('overdue', 0):,.0f}".replace(",", ".")],
                ["Chưa đến hạn", f"{debt_data.get('total_debt', 0) - debt_data.get('paid', 0) - debt_data.get('overdue', 0):,.0f}".replace(",", ".")]
            ]
            
            filename = f"Bao_cao_cong_no_{datetime.now().strftime('%Y%m%d')}"
            self.save_report(data, filename, file_format, "Công nợ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo công nợ:\n{str(e)}")
    
    def export_tax_report(self, file_format):
        """Xuất báo cáo thuế"""
        year = self.year_var.get()
        revenue = ReportService.get_total_income()
        
        # Tính thuế (giả sử thuế suất 1% cho GTGT và 0.5% cho TNCN)
        vat = revenue * 0.01
        pit = revenue * 0.005
        total_tax = vat + pit
        
        data = [
            ["Chỉ tiêu", "Giá trị (VNĐ)"],
            ["Doanh thu tính thuế", f"{revenue:,.0f}".replace(",", ".")],
            ["Thuế GTGT (1%)", f"{vat:,.0f}".replace(",", ".")],
            ["Thuế TNCN (0.5%)", f"{pit:,.0f}".replace(",", ".")],
            ["Tổng thuế phải nộp", f"{total_tax:,.0f}".replace(",", ".")]
        ]
        
        filename = f"Bao_cao_thue_{year}"
        self.save_report(data, filename, file_format, "Thuế")
    
    def export_inventory_report(self, file_format):
        """Xuất báo cáo hàng tồn kho"""
        try:
            from services.product_service import ProductService
            products = ProductService.get_all_products()
            
            data = [["Mã SP", "Tên SP", "Đơn vị", "Tồn kho", "Giá nhập", "Giá bán"]]
            for p in products:
                data.append([
                    p.get('code', ''),
                    p.get('name', ''),
                    p.get('unit', ''),
                    f"{p.get('stock', 0):,.0f}".replace(",", "."),
                    f"{p.get('price_buy', 0):,.0f}".replace(",", "."),
                    f"{p.get('price_sell', 0):,.0f}".replace(",", ".")
                ])
            
            filename = f"Bao_cao_hang_ton_kho_{datetime.now().strftime('%Y%m%d')}"
            self.save_report(data, filename, file_format, "Hàng tồn kho")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất báo cáo hàng tồn kho:\n{str(e)}")
    
    def export_summary_report(self, file_format):
        """Xuất báo cáo tổng hợp"""
        year = self.year_var.get()
        
        revenue = ReportService.get_total_income()
        expense = ReportService.get_total_expense()
        profit = revenue - expense
        
        try:
            debt_data = DebtService.get_debt_summary()
            total_debt = debt_data.get('total_debt', 0)
        except:
            total_debt = 0
        
        data = [
            ["BÁO CÁO TỔNG HỢP", ""],
            ["", ""],
            ["1. KẾT QUẢ KINH DOANH", ""],
            ["Tổng doanh thu", f"{revenue:,.0f}".replace(",", ".")],
            ["Tổng chi phí", f"{expense:,.0f}".replace(",", ".")],
            ["Lợi nhuận", f"{profit:,.0f}".replace(",", ".")],
            ["", ""],
            ["2. CÔNG NỢ", ""],
            ["Tổng công nợ", f"{total_debt:,.0f}".replace(",", ".")],
            ["", ""],
            ["Ngày lập:", datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
        ]
        
        filename = f"Bao_cao_tong_hop_{year}"
        self.save_report(data, filename, file_format, "Tổng hợp")
    
    def save_report(self, data, filename, file_format, report_name):
        """Lưu báo cáo ra file"""
        from tkinter import filedialog
        
        # Xác định extension
        ext_map = {
            "excel": ".xlsx",
            "xml": ".xml",
            "csv": ".csv"
        }
        ext = ext_map.get(file_format, ".xlsx")
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=[(f"{file_format.upper()} files", f"*{ext}"), ("All files", "*.*")],
            initialfile=f"{filename}{ext}"
        )
        
        if not file_path:
            self.status_label.config(text="Đã hủy xuất báo cáo", foreground="orange")
            return
        
        try:
            if file_format == "excel":
                self.save_to_excel(data, file_path)
            elif file_format == "csv":
                self.save_to_csv(data, file_path)
            elif file_format == "xml":
                self.save_to_xml(data, file_path, report_name)
            
            self.status_label.config(text=f"✅ Đã xuất báo cáo: {os.path.basename(file_path)}", foreground="green")
            if messagebox.askyesno("Thành công", f"Đã xuất báo cáo thành công!\n\n{file_path}\n\nBạn có muốn mở file không?"):
                os.startfile(file_path)
        except Exception as e:
            raise Exception(f"Lỗi khi lưu file: {str(e)}")
    
    def save_to_excel(self, data, file_path):
        """Lưu ra file Excel"""
        import pandas as pd
        
        if len(data) > 0 and isinstance(data[0], list):
            df = pd.DataFrame(data[1:], columns=data[0] if data else None)
        else:
            df = pd.DataFrame(data)
        
        df.to_excel(file_path, index=False, engine='openpyxl')
    
    def save_to_csv(self, data, file_path):
        """Lưu ra file CSV"""
        import pandas as pd
        
        if len(data) > 0 and isinstance(data[0], list):
            df = pd.DataFrame(data[1:], columns=data[0] if data else None)
        else:
            df = pd.DataFrame(data)
        
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    def save_to_xml(self, data, file_path, report_name):
        """Lưu ra file XML"""
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        root = ET.Element("Report")
        ET.SubElement(root, "ReportName").text = report_name
        ET.SubElement(root, "ExportDate").text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data_element = ET.SubElement(root, "Data")
        for row in data:
            if isinstance(row, list) and len(row) >= 2:
                item = ET.SubElement(data_element, "Item")
                ET.SubElement(item, "Label").text = str(row[0])
                ET.SubElement(item, "Value").text = str(row[1])
        
        xml_str = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="  ")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
    
    def bind_events(self):
        pass
    
    def load_data(self):
        """Tải dữ liệu"""
        self.show_message("Sẵn sàng xuất báo cáo", is_error=False)