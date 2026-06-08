import tkinter as tk
from tkinter import ttk, messagebox
from services.tax_service import TaxService
from services.report_service import ReportService
from datetime import datetime
from utils.license import is_full_version
from utils.printer import show_print_preview
from theme import get_fonts, get_font

class TaxDeclarationTab:
    def __init__(self, parent, notebook):
        self.parent = parent
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text="Kê khai thuế")
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # === STYLE CHO FONT LỚN ===
        style = ttk.Style()
        style.configure("TaxDeclare.TLabelframe.Label", font=get_fonts()["label_bold"])
        style.configure("TaxDeclare.TButton", font=get_font("label"), padding=8)
        style.configure("TaxDeclare.TLabel", font=get_font("label"))
        style.configure("TaxDeclare.Treeview", font=get_font("small"), rowheight=28)
        style.configure("TaxDeclare.Treeview.Heading", font=get_font("bold"))
        style.configure("TaxDeclare.TCombobox", font=get_font("label"))
        
        # === KHUNG CHỌN NĂM VÀ LOẠI THUẾ ===
        filter_frame = ttk.LabelFrame(self.frame, text="Thông tin kê khai", style="TaxDeclare.TLabelframe")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Dòng 1: Năm và Loại thuế
        row1_frame = ttk.Frame(filter_frame)
        row1_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        ttk.Label(row1_frame, text="Năm:", font=get_font("label")).pack(side="left", padx=(0, 10))
        self.year_combo = ttk.Combobox(row1_frame, values=[str(y) for y in range(2023, 2030)], 
                                       width=8, style="TaxDeclare.TCombobox")
        self.year_combo.pack(side="left", padx=(0, 30))
        self.year_combo.set(str(datetime.now().year))
        
        ttk.Label(row1_frame, text="Loại thuế:", font=get_font("label")).pack(side="left", padx=(0, 10))
        self.tax_type_combo = ttk.Combobox(row1_frame, 
                                           values=["GTGT", "TNCN", "TNDN", "Môn bài"],
                                           width=10, style="TaxDeclare.TCombobox")
        self.tax_type_combo.pack(side="left", padx=(0, 30))
        self.tax_type_combo.set("GTGT")
        
        ttk.Label(row1_frame, text="Tình trạng:", font=get_font("label")).pack(side="left", padx=(0, 10))
        self.status_combo = ttk.Combobox(row1_frame, 
                                         values=["Đã kê khai", "Chưa kê khai", "Đã nộp", "Quá hạn"],
                                         width=12, style="TaxDeclare.TCombobox")
        self.status_combo.pack(side="left", padx=(0, 30))
        self.status_combo.set("Chưa kê khai")
        
        # Dòng 2: Nút chức năng
        row2_frame = ttk.Frame(filter_frame)
        row2_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ttk.Button(row2_frame, text="📊 Tính thuế", command=self.calculate_tax,
                   style="TaxDeclare.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="📄 In tờ khai", command=self.print_declaration,
                   style="TaxDeclare.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="📥 Xuất XML", command=self.export_xml,
                   style="TaxDeclare.TButton", width=12).pack(side="left", padx=5)
        ttk.Button(row2_frame, text="🔄 Làm mới", command=self.load_data,
                   style="TaxDeclare.TButton", width=12).pack(side="left", padx=5)
        
        # === KHUNG KẾT QUẢ TÍNH THUẾ ===
        result_frame = ttk.LabelFrame(self.frame, text="Kết quả tính thuế", style="TaxDeclare.TLabelframe")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Frame chứa nội dung kết quả
        self.result_container = ttk.Frame(result_frame)
        self.result_container.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Khởi tạo các label hiển thị kết quả
        self.create_result_display()
    
    def create_result_display(self):
        """Tạo các label hiển thị kết quả tính thuế"""
        # Xóa nội dung cũ
        for widget in self.result_container.winfo_children():
            widget.destroy()
        
        # Font chữ
        title_font = get_font("title")
        label_font = get_font("label")
        value_font = get_font("bold")
        note_font = get_font("small")
        
        # Tiêu đề
        self.title_label = ttk.Label(self.result_container, text="TỜ KHAI THUẾ GTGT", 
                                      font=title_font, foreground="#2196F3")
        self.title_label.pack(anchor="center", pady=(0, 20))
        
        # Khung thông tin
        info_frame = ttk.Frame(self.result_container)
        info_frame.pack(fill="x", pady=5)
        
        # Dòng 1: Năm
        row1 = ttk.Frame(info_frame)
        row1.pack(fill="x", pady=8)
        ttk.Label(row1, text="Năm tính thuế:", font=label_font, width=18, anchor="w").pack(side="left")
        self.year_value_label = ttk.Label(row1, text="", font=value_font, foreground="#333")
        self.year_value_label.pack(side="left", padx=10)
        
        # Dòng 2: Doanh thu
        row2 = ttk.Frame(info_frame)
        row2.pack(fill="x", pady=8)
        ttk.Label(row2, text="Doanh thu:", font=label_font, width=18, anchor="w").pack(side="left")
        self.revenue_label = ttk.Label(row2, text="", font=value_font, foreground="#4CAF50")
        self.revenue_label.pack(side="left", padx=10)
        
        # Dòng 3: Thuế phải nộp
        row3 = ttk.Frame(info_frame)
        row3.pack(fill="x", pady=8)
        ttk.Label(row3, text="Thuế phải nộp:", font=label_font, width=18, anchor="w").pack(side="left")
        self.tax_amount_label = ttk.Label(row3, text="", font=value_font, foreground="#F44336")
        self.tax_amount_label.pack(side="left", padx=10)
        
        # Dòng 4: Ghi chú
        row4 = ttk.Frame(info_frame)
        row4.pack(fill="x", pady=8)
        ttk.Label(row4, text="Ghi chú:", font=label_font, width=18, anchor="w").pack(side="left")
        self.note_label = ttk.Label(row4, text="", font=note_font, foreground="#666", wraplength=500, justify="left")
        self.note_label.pack(side="left", padx=10)
        
        # Dòng 5: Ngày lập
        row5 = ttk.Frame(info_frame)
        row5.pack(fill="x", pady=8)
        ttk.Label(row5, text="Ngày lập:", font=label_font, width=18, anchor="w").pack(side="left")
        self.date_label = ttk.Label(row5, text=datetime.now().strftime("%d/%m/%Y"), 
                                    font=label_font, foreground="#666")
        self.date_label.pack(side="left", padx=10)
        
        # Dòng 6: Hạn nộp
        row6 = ttk.Frame(info_frame)
        row6.pack(fill="x", pady=8)
        ttk.Label(row6, text="Hạn nộp:", font=label_font, width=18, anchor="w").pack(side="left")
        self.deadline_label = ttk.Label(row6, text="", font=label_font, foreground="#FF9800")
        self.deadline_label.pack(side="left", padx=10)
    
    def load_data(self):
        """Tải dữ liệu và cập nhật hiển thị"""
        self.calculate_tax()
    
    def calculate_tax(self):
        """Tính thuế dựa trên năm và loại thuế đã chọn"""
        try:
            year = int(self.year_combo.get())
            tax_type = self.tax_type_combo.get()
            
            # Lấy doanh thu trong năm
            revenue = self.get_yearly_revenue(year)
            
            # Tính thuế theo loại
            if tax_type == "GTGT":
                tax_amount = self.calculate_vat(revenue)
                tax_name = "THUẾ GTGT"
                note = "Thuế GTGT phải nộp (doanh thu chịu thuế)"
                deadline = f"20/{4 if year == datetime.now().year else 3}/{year}"
            elif tax_type == "TNCN":
                tax_amount = self.calculate_pit(revenue)
                tax_name = "THUẾ TNCN"
                note = "Thuế thu nhập cá nhân từ hộ kinh doanh"
                deadline = f"31/{3 if year == datetime.now().year else 3}/{year + 1}"
            elif tax_type == "TNDN":
                tax_amount = self.calculate_cit(revenue)
                tax_name = "THUẾ TNDN"
                note = "Thuế thu nhập doanh nghiệp tạm tính"
                deadline = f"30/{10 if year == datetime.now().year else 3}/{year + 1}"
            else:  # Môn bài
                tax_amount = self.calculate_license_fee(revenue)
                tax_name = "LỆ PHÍ MÔN BÀI"
                note = "Lệ phí môn bài theo doanh thu bình quân năm"
                deadline = f"30/{1 if year == datetime.now().year else 1}/{year + 1}"
            
            # Cập nhật giao diện
            self.title_label.config(text=f"TỜ KHAI {tax_name} NĂM {year}")
            self.year_value_label.config(text=str(year))
            self.revenue_label.config(text=self.format_money(revenue) + " VNĐ")
            self.tax_amount_label.config(text=self.format_money(tax_amount) + " VNĐ")
            self.note_label.config(text=note)
            self.deadline_label.config(text=deadline)
            
            # Đổi màu thuế theo giá trị
            if tax_amount > 0:
                self.tax_amount_label.config(foreground="#F44336")
            else:
                self.tax_amount_label.config(foreground="#4CAF50")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tính thuế: {str(e)}")
    
    def get_yearly_revenue(self, year):
        """Lấy tổng doanh thu trong năm"""
        try:
            from services.transaction_service import TransactionService
            from services.invoice_service import InvoiceService
            
            # Lọc giao dịch theo năm
            transactions = TransactionService.get_all_transactions()
            invoices = InvoiceService.get_all_invoices()
            
            total = 0
            
            # Cộng doanh thu từ giao dịch
            for t in transactions:
                try:
                    if t['type'] == 'Thu':
                        date = t.get('date', '')
                        if date and date.endswith(str(year)):
                            total += t.get('amount', 0)
                except Exception:
                    pass
            
            # Cộng doanh thu từ hóa đơn
            for inv in invoices:
                try:
                    date = inv.get('created_date', '')
                    if date and date.endswith(str(year)):
                        total += inv.get('total_payment', 0)
                except Exception:
                    pass
            
            return total
        except Exception:
            report_service = ReportService()
            return report_service.get_total_income()
    
    def calculate_vat(self, revenue):
        """Tính thuế GTGT (giả sử thuế suất 10%)"""
        # Hộ kinh doanh nộp thuế GTGT theo phương pháp trực tiếp
        if revenue <= 100_000_000:  # Dưới 100 triệu
            return 0
        else:
            return revenue * 0.01  # 1% trên doanh thu
    
    def calculate_pit(self, revenue):
        """Tính thuế TNCN (thuế suất lũy tiến từng phần)"""
        if revenue <= 100_000_000:
            return 0
        elif revenue <= 300_000_000:
            return revenue * 0.005
        elif revenue <= 500_000_000:
            return revenue * 0.01
        else:
            return revenue * 0.015
    
    def calculate_cit(self, revenue):
        """Tính thuế TNDN (giả sử thuế suất 20%)"""
        # Giả sử lợi nhuận = 20% doanh thu
        profit = revenue * 0.2
        return profit * 0.2  # 20% trên lợi nhuận
    
    def calculate_license_fee(self, revenue):
        """Tính lệ phí môn bài"""
        if revenue <= 100_000_000:
            return 300_000
        elif revenue <= 300_000_000:
            return 500_000
        elif revenue <= 500_000_000:
            return 1_000_000
        else:
            return 3_000_000
    
    def print_declaration(self):
        """In tờ khai thuế"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        
        year = self.year_combo.get()
        tax_type = self.tax_type_combo.get()
        revenue = self.revenue_label.cget("text")
        tax_amount = self.tax_amount_label.cget("text")
        note = self.note_label.cget("text")
        deadline = self.deadline_label.cget("text")
        
        content = f"""
{'='*60}
{'TỜ KHAI THUẾ ' + tax_type:^60}
{'='*60}

Năm tính thuế: {year}
Ngày lập: {datetime.now().strftime('%d/%m/%Y %H:%M')}

{'─'*60}
KẾT QUẢ TÍNH THUẾ
{'─'*60}

Doanh thu: {revenue}
Thuế phải nộp: {tax_amount}
Ghi chú: {note}
Hạn nộp: {deadline}

{'─'*60}
THÔNG TIN NGƯỜI NỘP THUẾ
{'─'*60}

Tên người nộp thuế: {self.get_taxpayer_name()}
Mã số thuế: {self.get_tax_code()}
Địa chỉ: {self.get_address()}

{'='*60}
        """
        
        show_print_preview(content, f"Tờ khai thuế {tax_type} năm {year}", self.frame)
    
    def export_xml(self):
        """Xuất tờ khai thuế dạng XML"""
        if not is_full_version():
            messagebox.showwarning("Bản quyền", "Tính năng này chỉ dành cho bản quyền chính thức. Vui lòng liên hệ để mua.")
            return
        
        from tkinter import filedialog
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
        
        try:
            year = self.year_combo.get()
            tax_type = self.tax_type_combo.get()
            revenue_text = self.revenue_label.cget("text")
            revenue = float(revenue_text.replace(" VNĐ", "").replace(".", ""))
            tax_text = self.tax_amount_label.cget("text")
            tax_amount = float(tax_text.replace(" VNĐ", "").replace(".", ""))
            
            # Tạo cấu trúc XML
            root = ET.Element("TaxDeclaration")
            ET.SubElement(root, "TaxType").text = tax_type
            ET.SubElement(root, "Year").text = year
            ET.SubElement(root, "DeclaredDate").text = datetime.now().strftime("%Y-%m-%d")
            ET.SubElement(root, "Revenue").text = str(int(revenue))
            ET.SubElement(root, "TaxAmount").text = str(int(tax_amount))
            ET.SubElement(root, "Taxpayer").text = self.get_taxpayer_name()
            ET.SubElement(root, "TaxCode").text = self.get_tax_code()
            ET.SubElement(root, "Address").text = self.get_address()
            
            # Format XML đẹp
            xml_str = minidom.parseString(ET.tostring(root, encoding='utf-8')).toprettyxml(indent="  ")
            
            # Lưu file
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=[("XML files", "*.xml")],
                initialfile=f"Thue_{tax_type}_{year}.xml"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                messagebox.showinfo("Thành công", f"Đã xuất tờ khai XML:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất XML: {str(e)}")
    
    def get_taxpayer_name(self):
        """Lấy tên người nộp thuế"""
        try:
            from config import SOFTWARE_OWNER
            return SOFTWARE_OWNER
        except Exception:
            return "Phan Ngọc Hùng"
    
    def get_tax_code(self):
        """Lấy mã số thuế"""
        # Có thể lấy từ database hoặc config
        return "1234567890"
    
    def get_address(self):
        """Lấy địa chỉ"""
        try:
            from config import SOFTWARE_OWNER
            return "Khánh Hòa"
        except Exception:
            return "Khánh Hòa"
    
    def format_money(self, amount):
        """Định dạng số tiền"""
        if amount == 0:
            return "0"
        return f"{amount:,.0f}".replace(",", ".")