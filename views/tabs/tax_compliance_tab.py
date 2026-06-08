# -*- coding: utf-8 -*-
"""
TaxComplianceTab - Kiểm tra tuân thủ pháp lý về thuế
"""

import tkinter as tk
from tkinter import ttk, messagebox
from views.tabs.base_tab import BaseTab
from datetime import datetime
from services.report_service import ReportService
from utils.license import is_full_version
from theme import get_font

class TaxComplianceTab(BaseTab):
    """Tab kiểm tra tuân thủ pháp lý về thuế"""
    
    def __init__(self, parent, notebook, controller=None):
        super().__init__(parent, notebook, controller)
    
    def setup_ui(self):
        """Tạo giao diện kiểm tra tuân thủ thuế"""
        self.frame = ttk.Frame(self)
        # === STYLE CHO FONT LỚN ===
        style = ttk.Style()
        style.configure("Compliance.TLabelframe.Label", font=get_font("bold"))
        style.configure("Compliance.TButton", font=get_font("label"), padding=8)
        style.configure("Compliance.TLabel", font=get_font("label"))
        style.configure("Compliance.TEntry", font=get_font("label"))
        
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
        ttk.Label(title_frame, text="📋 KIỂM TRA TUÂN THỦ PHÁP LÝ VỀ THUẾ", 
                  font=get_font("title"), foreground="#2196F3").pack()
        ttk.Label(title_frame, text="Đánh giá nghĩa vụ thuế và hạn nộp các mẫu biểu", 
                  font=get_font("label"), foreground="gray").pack()
        
        # === KHUNG DOANH THU NĂM ===
        revenue_frame = ttk.LabelFrame(content_frame, text="💰 DOANH THU NĂM", 
                                       style="Compliance.TLabelframe", padding=20)
        revenue_frame.pack(fill="x", pady=10)
        
        # Nhập doanh thu
        input_frame = ttk.Frame(revenue_frame)
        input_frame.pack(fill="x", pady=10)
        
        ttk.Label(input_frame, text="Nhập doanh thu ước tính trong năm:", 
                  font=get_font("label")).pack(side="left", padx=(0, 15))
        
        self.revenue_var = tk.StringVar()
        self.revenue_entry = ttk.Entry(input_frame, textvariable=self.revenue_var, 
                                       width=20, font=get_font("label"))
        self.revenue_entry.pack(side="left", padx=(0, 15))
        
        ttk.Label(input_frame, text="VNĐ", font=get_font("label")).pack(side="left")
        
        # Nút kiểm tra
        check_btn = ttk.Button(revenue_frame, text="🔍 KIỂM TRA", 
                               command=self.check_compliance, style="Compliance.TButton", width=15)
        check_btn.pack(pady=10)
        
        # === KHUNG KẾT QUẢ ===
        result_frame = ttk.LabelFrame(content_frame, text="📊 KẾT QUẢ", 
                                      style="Compliance.TLabelframe", padding=20)
        result_frame.pack(fill="both", expand=True, pady=10)
        
        self.result_text = tk.Text(result_frame, height=12, wrap="word", 
                                   font=get_font("label"), bg="#f8f9fa", relief="solid", borderwidth=1)
        self.result_text.pack(fill="both", expand=True, pady=5)
        
        # Cấu hình tag màu cho text
        self.result_text.tag_configure("title", font=get_font("title"), foreground="#2196F3")
        self.result_text.tag_configure("success", foreground="#4CAF50")
        self.result_text.tag_configure("warning", foreground="#FF9800")
        self.result_text.tag_configure("error", foreground="#F44336")
        self.result_text.tag_configure("normal", font=get_font("label"))
        self.result_text.tag_configure("bold", font=get_font("bold"))
        
        # === KHUNG HẠN NỘP CÁC MẪU BIỂU ===
        deadline_frame = ttk.LabelFrame(content_frame, text="⏰ HẠN NỘP CÁC MẪU BIỂU", 
                                        style="Compliance.TLabelframe", padding=15)
        deadline_frame.pack(fill="x", pady=10)
        
        # Tạo grid cho các mẫu biểu
        self.deadline_labels = {}
        
        forms = [
            ("01/BK-STK", "Thông báo tài khoản ngân hàng"),
            ("01/TKN-CNKD", "Thông báo doanh thu (dưới 1 tỷ)"),
            ("01/CNKD", "Tờ khai thuế (trên 1 tỷ)")
        ]
        
        for i, (form_code, form_name) in enumerate(forms):
            frame = ttk.Frame(deadline_frame)
            frame.pack(fill="x", pady=10)
            
            ttk.Label(frame, text=f"📄 {form_code}:", font=get_font("bold"), 
                      width=15, anchor="w").pack(side="left")
            ttk.Label(frame, text=form_name, font=get_font("label"), 
                      foreground="gray").pack(side="left", padx=10)
            
            # Label hiển thị hạn nộp
            deadline_label = ttk.Label(frame, text="Chưa kiểm tra", font=get_font("label"))
            deadline_label.pack(side="right", padx=10)
            self.deadline_labels[form_code] = deadline_label
        
        # Nút kiểm tra hạn nộp
        check_deadline_btn = ttk.Button(deadline_frame, text="⏰ KIỂM TRA HẠN NỘP", 
                                        command=self.check_all_deadlines, 
                                        style="Compliance.TButton", width=20)
        check_deadline_btn.pack(pady=10)
        
        # === HƯỚNG DẪN ===
        guide_frame = ttk.LabelFrame(content_frame, text="📌 HƯỚNG DẪN", 
                                     style="Compliance.TLabelframe", padding=15)
        guide_frame.pack(fill="x", pady=10)
        
        guide_text = """
        • Nhập doanh thu ước tính trong năm để xác định nhóm đối tượng
        • Hệ thống sẽ đề xuất các mẫu biểu cần nộp và hạn nộp tương ứng
        • Kiểm tra hạn nộp để đảm bảo tuân thủ quy định pháp luật
        • Liên hệ cơ quan thuế nếu có thắc mắc về nghĩa vụ thuế
        """
        ttk.Label(guide_frame, text=guide_text, font=get_font("small"), 
                  foreground="#666", justify="left").pack(anchor="w", pady=5)
        
        # Khởi tạo nội dung mặc định
        self.show_default_result()
    
    def show_default_result(self):
        """Hiển thị kết quả mặc định"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", "🔍 Nhập doanh thu và nhấn 'KIỂM TRA' để xem kết quả\n\n", "title")
        self.result_text.insert(tk.END, "Hệ thống sẽ phân tích và đề xuất:\n", "normal")
        self.result_text.insert(tk.END, "• Nhóm đối tượng theo doanh thu\n", "normal")
        self.result_text.insert(tk.END, "• Các mẫu biểu cần kê khai\n", "normal")
        self.result_text.insert(tk.END, "• Mức thuế suất áp dụng\n", "normal")
        self.result_text.insert(tk.END, "• Hạn nộp các mẫu biểu\n", "normal")
    
    def check_compliance(self):
        """Kiểm tra tuân thủ dựa trên doanh thu"""
        try:
            revenue_str = self.revenue_var.get().strip()
            if not revenue_str:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập doanh thu ước tính")
                return
            
            # Xử lý định dạng số (có thể có dấu . hoặc ,)
            revenue_str = revenue_str.replace(".", "").replace(",", "")
            revenue = float(revenue_str)
            
            # Xác định nhóm đối tượng
            group_info = self.determine_tax_group(revenue)
            
            # Hiển thị kết quả
            self.result_text.delete("1.0", tk.END)
            
            # Tiêu đề
            self.result_text.insert("1.0", "📊 KẾT QUẢ PHÂN TÍCH\n\n", "title")
            
            # Thông tin doanh thu
            self.result_text.insert(tk.END, f"Doanh thu năm: ", "bold")
            self.result_text.insert(tk.END, f"{self.format_money(revenue)} VNĐ\n\n", "normal")
            
            # Nhóm đối tượng
            self.result_text.insert(tk.END, f"🏷️ Nhóm đối tượng: ", "bold")
            self.result_text.insert(tk.END, f"{group_info['group_name']}\n", group_info['color'])
            self.result_text.insert(tk.END, f"   {group_info['description']}\n\n", "normal")
            
            # Các mẫu biểu cần nộp
            self.result_text.insert(tk.END, "📋 CÁC MẪU BIỂU CẦN KÊ KHAI:\n", "bold")
            for form in group_info['forms']:
                self.result_text.insert(tk.END, f"   • {form}\n", "normal")
            
            # Thuế suất
            self.result_text.insert(tk.END, f"\n💰 THUẾ SUẤT ÁP DỤNG:\n", "bold")
            self.result_text.insert(tk.END, f"   • GTGT: {group_info['vat_rate']}\n", "normal")
            self.result_text.insert(tk.END, f"   • TNCN: {group_info['pit_rate']}\n", "normal")
            
            # Cập nhật hạn nộp các mẫu biểu
            self.update_deadlines_for_group(group_info['group_id'])
            
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số tiền hợp lệ")
    
    def determine_tax_group(self, revenue):
        """Xác định nhóm đối tượng dựa trên doanh thu"""
        if revenue <= 1000_000_000:
            return {
                'group_id': 1,
                'group_name': "Nhóm 1: Hộ kinh doanh có doanh thu dưới 1 tỷ/năm",
                'description': "✅ Được miễn thuế GTGT và TNCN, chỉ cần ghi chép sổ doanh thu",
                'color': 'success',
                'forms': [
                    "📒 Sổ doanh thu S1a-HKD (lưu tại hộ kinh doanh)",
                    "📢 Thông báo doanh thu mẫu 01/TKN-CNKD (nếu có thay đổi)"
                ],
                'vat_rate': "Miễn thuế",
                'pit_rate': "Miễn thuế"
            }
        elif revenue <= 3_000_000_000:
            return {
                'group_id': 2,
                'group_name': "Nhóm 2: Doanh thu từ 1 tỷ đến 3 tỷ/năm",
                'description': "⚠️ Thuế tính theo tỷ lệ % trên doanh thu",
                'color': 'warning',
                'forms': [
                    "📊 Tờ khai thuế mẫu 01/CNKD (theo quý)",
                    "📒 Sổ doanh thu S1a-HKD",
                    "📢 Thông báo doanh thu (nếu phát sinh)"
                ],
                'vat_rate': "1% trên doanh thu",
                'pit_rate': "0.5% trên doanh thu"
            }
        elif revenue <= 50_000_000_000:
            return {
                'group_id': 3,
                'group_name': "Nhóm 3: Doanh thu từ 3 tỷ đến 50 tỷ/năm",
                'description': "⚠️ Thuế TNCN theo thu nhập tính thuế (lũy tiến)",
                'color': 'warning',
                'forms': [
                    "📊 Tờ khai thuế mẫu 01/CNKD (theo quý)",
                    "📒 Sổ doanh thu S1a-HKD",
                    "📋 Báo cáo tài chính"
                ],
                'vat_rate': "10% (khấu trừ) hoặc 1% (trực tiếp)",
                'pit_rate': "Lũy tiến từng phần (5% - 35%)"
            }
        else:
            return {
                'group_id': 4,
                'group_name': "Nhóm 4: Doanh thu trên 50 tỷ/năm",
                'description': "🔴 Kê khai thuế theo tháng",
                'color': 'error',
                'forms': [
                    "📊 Tờ khai thuế GTGT (theo tháng)",
                    "📊 Tờ khai thuế TNCN/TNDN (theo tháng)",
                    "📋 Báo cáo tài chính năm",
                    "📒 Sổ doanh thu S1a-HKD"
                ],
                'vat_rate': "10% (khấu trừ)",
                'pit_rate': "Lũy tiến từng phần (5% - 35%)"
            }
    
    def update_deadlines_for_group(self, group_id):
        """Cập nhật hạn nộp dựa trên nhóm đối tượng"""
        current_year = datetime.now().year
        
        # Cập nhật hạn nộp 01/BK-STK
        self.update_deadline("01/BK-STK", "20/04/2026", "⚠️ Đã quá hạn" if datetime.now().day > 20 else "⏰ Còn 2 ngày")
        
        if group_id == 1:
            # Nhóm 1: Không cần nộp tờ khai
            self.update_deadline("01/TKN-CNKD", "31/07/2026", "📢 Chỉ nộp khi có thay đổi")
            self.update_deadline("01/CNKD", "Không áp dụng", "✅ Không cần nộp tờ khai")
        elif group_id == 2 or group_id == 3:
            # Nhóm 2 và 3: Nộp theo quý
            current_quarter = (datetime.now().month - 1) // 3 + 1
            quarter_deadlines = {1: "30/04", 2: "31/07", 3: "30/10", 4: "31/01"}
            deadline_date = quarter_deadlines.get(current_quarter, "31/01")
            deadline_full = f"{deadline_date}/{current_year + 1 if current_quarter == 4 else current_year}"
            self.update_deadline("01/CNKD", deadline_full, "⏰ Cần nộp theo quý")
            self.update_deadline("01/TKN-CNKD", "31/01/2027", "📢 Nộp 1 lần/năm")
        else:
            # Nhóm 4: Nộp theo tháng
            self.update_deadline("01/CNKD", f"20/{datetime.now().month + 1}/{current_year}", "⏰ Nộp theo tháng")
            self.update_deadline("01/TKN-CNKD", "31/01/2027", "📢 Nộp 1 lần/năm")
    
    def check_all_deadlines(self):
        """Kiểm tra tất cả hạn nộp"""
        self.update_deadline("01/BK-STK", "20/04/2026", self.get_deadline_status("20/04/2026"))
        self.update_deadline("01/TKN-CNKD", "31/07/2026", self.get_deadline_status("31/07/2026"))
        self.update_deadline("01/CNKD", "31/07/2026", self.get_deadline_status("31/07/2026"))
        
        messagebox.showinfo("Thông báo", "Đã cập nhật hạn nộp các mẫu biểu")
    
    def update_deadline(self, form_code, deadline, status):
        """Cập nhật hiển thị hạn nộp"""
        if form_code in self.deadline_labels:
            text = f"Hạn: {deadline} | {status}"
            self.deadline_labels[form_code].config(text=text)
            
            # Đổi màu theo trạng thái
            if "quá hạn" in status.lower():
                self.deadline_labels[form_code].config(foreground="#F44336")
            elif "còn" in status.lower():
                self.deadline_labels[form_code].config(foreground="#FF9800")
            elif "không cần" in status.lower() or "không áp dụng" in status:
                self.deadline_labels[form_code].config(foreground="#4CAF50")
            else:
                self.deadline_labels[form_code].config(foreground="#2196F3")
    
    def get_deadline_status(self, deadline_str):
        """Lấy trạng thái hạn nộp"""
        try:
            day, month, year = map(int, deadline_str.split('/'))
            deadline_date = datetime(year, month, day)
            today = datetime.now()
            
            if today > deadline_date:
                return "🔴 Đã quá hạn"
            elif (deadline_date - today).days <= 7:
                return f"⚠️ Còn {(deadline_date - today).days} ngày"
            else:
                return "🟢 Còn hạn"
        except:
            return "📅 Chưa xác định"
    
    def format_money(self, amount):
        """Định dạng số tiền"""
        if amount == 0:
            return "0"
        return f"{amount:,.0f}".replace(",", ".")
    
    def bind_events(self):
        pass
    
    def load_data(self):
        """Tải dữ liệu"""
        self.show_message("Sẵn sàng kiểm tra tuân thủ thuế", is_error=False)