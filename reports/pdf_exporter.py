"""
PDFExporter - Xuất báo cáo ra PDF chuyên nghiệp.

Module này cung cấp:
- Xuất Bảng tình hình tài chính ra PDF
- Xuất Báo cáo kết quả kinh doanh ra PDF
- Xuất Báo cáo thuế GTGT ra PDF
- Font hệ thống, không hardcode

Example:
    >>> from reports.pdf_exporter import PDFExporter
    >>> exporter = PDFExporter()
    >>> exporter.export_balance_sheet_pdf(data)
"""

# reports/pdf_exporter.py
# XUẤT BÁO CÁO RA PDF CHUYÊN NGHIỆP
# KHÔNG HARDCODE FONT - DÙNG FONT HỆ THỐNG

import os
import config
"""
PDFExporter - Xuất báo cáo ra PDF chuyên nghiệp.

Module này cung cấp:
- Xuất Bảng tình hình tài chính ra PDF
- Xuất Báo cáo kết quả kinh doanh ra PDF
- Xuất Báo cáo thuế GTGT ra PDF
- Font hệ thống, không hardcode

Example:
    >>> from reports.pdf_exporter import PDFExporter
    >>> exporter = PDFExporter()
    >>> exporter.export_balance_sheet_pdf(data)
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

class PDFExporter:
    """
    Xuất báo cáo ra PDF
    Sử dụng reportlab, font hệ thống
    """
    
    def __init__(self):
        self.output_dir = Path(__file__).parent.parent / "exports"
        self.output_dir.mkdir(exist_ok=True)
        
        # Đăng ký font hệ thống nếu có reportlab
        if HAS_REPORTLAB:
            self._register_system_fonts()
    
    def _register_system_fonts(self):
        """Đăng ký font từ hệ thống (không hardcode)"""
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/verdana.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                    self.font_name = 'CustomFont'
                    break
                except:
                    pass
        
        if not hasattr(self, 'font_name'):
            self.font_name = 'Helvetica'  # Fallback
    
    def export_balance_sheet_pdf(self, data: Dict[str, Any], output_path: str = None) -> str:
        """
        Xuất Bảng tình hình tài chính ra PDF
        """
        if not HAS_REPORTLAB:
            return self._fallback_export(data, "balance_sheet")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"Bang_tinh_hinh_tai_chinh_{timestamp}.pdf"
        
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        y = height - 50
        
        # Tiêu đề
        c.setFont(self.font_name, 16)
        c.drawCentredString(width/2, y, data.get("report_name", "BẢNG TÌNH HÌNH TÀI CHÍNH"))
        y -= 25
        
        c.setFont(self.font_name, 10)
        c.drawString(50, y, f"Ngày lập: {data.get('report_date', datetime.now().strftime('%d/%m/%Y'))}")
        y -= 20
        c.drawString(50, y, f"Ngày xuất: {data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}")
        y -= 35
        
        # Kẻ bảng
        c.setFont(self.font_name, 9)
        
        for group_name, group_info in data.get("groups", {}).items():
            if y < 100:
                c.showPage()
                y = height - 50
                c.setFont(self.font_name, 9)
            
            c.setFont(self.font_name, 10)
            c.drawString(50, y, group_name)
            y -= 15
            
            c.setFont(self.font_name, 9)
            c.drawString(70, y, "Mã TK")
            c.drawString(150, y, "Tên tài khoản")
            c.drawString(400, y, "Số dư (VND)")
            y -= 18
            
            for acc in group_info.get("accounts", [])[:20]:  # Giới hạn 20 dòng
                if y < 80:
                    c.showPage()
                    y = height - 50
                    c.setFont(self.font_name, 9)
                
                c.drawString(70, y, acc.get("code", ""))
                c.drawString(150, y, acc.get("name", "")[:35])
                c.drawRightString(480, y, f"{acc.get('balance', 0):,.0f}")
                y -= 15
            
            c.setFont(self.font_name, 9)
            c.drawString(150, y, "CỘNG")
            c.drawRightString(480, y, f"{group_info.get('total', 0):,.0f}")
            y -= 25
        
        # Tổng kết
        c.setFont(self.font_name, 10)
        c.drawString(50, y, f"TỔNG TÀI SẢN: {data.get('total_assets', 0):,.0f} VND")
        y -= 15
        c.drawString(50, y, f"TỔNG NGUỒN VỐN: {data.get('total_liabilities_equity', 0):,.0f} VND")
        
        c.save()
        return str(output_path)
    
    def export_income_statement_pdf(self, data: Dict[str, Any], output_path: str = None) -> str:
        """
        Xuất Báo cáo Kết quả kinh doanh ra PDF
        """
        if not HAS_REPORTLAB:
            return self._fallback_export(data, "income_statement")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"Bao_cao_KQKD_{timestamp}.pdf"
        
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        y = height - 50
        
        # Tiêu đề
        c.setFont(self.font_name, 16)
        c.drawCentredString(width/2, y, data.get("report_name", "BÁO CÁO KẾT QUẢ KINH DOANH"))
        y -= 25
        
        c.setFont(self.font_name, 10)
        c.drawString(50, y, f"Từ ngày: {data.get('from_date', '')} đến {data.get('to_date', '')}")
        y -= 20
        c.drawString(50, y, f"Ngày xuất: {data.get('created_at', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}")
        y -= 35
        
        # Doanh thu
        c.setFont(self.font_name, 11)
        c.drawString(50, y, "I. DOANH THU")
        y -= 18
        
        c.setFont(self.font_name, 9)
        for item in data.get("revenue", {}).get("details", [])[:15]:
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont(self.font_name, 9)
            
            c.drawString(70, y, item.get("code", ""))
            c.drawString(150, y, item.get("name", "")[:35])
            c.drawRightString(480, y, f"{item.get('amount', 0):,.0f}")
            y -= 15
        
        c.setFont(self.font_name, 10)
        c.drawString(150, y, "Tổng doanh thu")
        c.drawRightString(480, y, f"{data.get('revenue', {}).get('total', 0):,.0f}")
        y -= 25
        
        # Chi phí
        c.setFont(self.font_name, 11)
        c.drawString(50, y, "II. CHI PHÍ")
        y -= 18
        
        c.setFont(self.font_name, 9)
        for item in data.get("expense", {}).get("details", [])[:15]:
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont(self.font_name, 9)
            
            c.drawString(70, y, item.get("code", ""))
            c.drawString(150, y, item.get("name", "")[:35])
            c.drawRightString(480, y, f"{item.get('amount', 0):,.0f}")
            y -= 15
        
        c.setFont(self.font_name, 10)
        c.drawString(150, y, "Tổng chi phí")
        c.drawRightString(480, y, f"{data.get('expense', {}).get('total', 0):,.0f}")
        y -= 25
        
        # Lợi nhuận
        c.setFont(self.font_name, 12)
        c.drawString(50, y, f"LỢI NHUẬN SAU THUẾ: {data.get('net_profit', 0):,.0f} VND")
        
        c.save()
        return str(output_path)
    
    def export_vat_report_pdf(self, data: Dict[str, Any], output_path: str = None) -> str:
        """
        Xuất Báo cáo thuế GTGT ra PDF
        """
        if not HAS_REPORTLAB:
            return self._fallback_export(data, "vat_report")
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"Bao_cao_GTGT_{timestamp}.pdf"
        
        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4
        y = height - 50
        
        # Tiêu đề
        c.setFont(self.font_name, 16)
        c.drawCentredString(width/2, y, data.get("report_name", "BÁO CÁO THUẾ GTGT"))
        y -= 25
        
        c.setFont(self.font_name, 10)
        c.drawString(50, y, f"Kỳ: Từ {data.get('from_date', '')} đến {data.get('to_date', '')}")
        y -= 20
        c.drawString(50, y, f"Thuế suất: {data.get('vat_rate', 10)}%")
        y -= 35
        
        # Đầu ra
        c.setFont(self.font_name, 11)
        c.drawString(50, y, "I. HÓA ĐƠN ĐẦU RA")
        y -= 18
        
        c.setFont(self.font_name, 9)
        output = data.get("output", {})
        c.drawString(70, y, f"Số hóa đơn: {output.get('invoice_count', 0)}")
        y -= 15
        c.drawString(70, y, f"Doanh thu: {output.get('sales_amount', 0):,.0f} VND")
        y -= 15
        c.drawString(70, y, f"Thuế GTGT: {output.get('vat_amount', 0):,.0f} VND")
        y -= 25
        
        # Đầu vào
        c.setFont(self.font_name, 11)
        c.drawString(50, y, "II. HÓA ĐƠN ĐẦU VÀO")
        y -= 18
        
        c.setFont(self.font_name, 9)
        input_data = data.get("input", {})
        c.drawString(70, y, f"Số hóa đơn: {input_data.get('purchase_count', 0)}")
        y -= 15
        c.drawString(70, y, f"Giá mua: {input_data.get('purchase_amount', 0):,.0f} VND")
        y -= 15
        c.drawString(70, y, f"Thuế GTGT: {input_data.get('vat_amount', 0):,.0f} VND")
        y -= 25
        
        # Số phải nộp
        c.setFont(self.font_name, 12)
        c.drawString(50, y, f"III. THUẾ GTGT PHẢI NỘP: {data.get('payable_vat', 0):,.0f} VND")
        
        c.save()
        return str(output_path)
    
    def _fallback_export(self, data: Dict, report_type: str) -> str:
        """Fallback khi không có reportlab - xuất ra text"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"{report_type}_{timestamp}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"BÁO CÁO {report_type.upper()}\n")
            f.write(f"Ngày xuất: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 60 + "\n")
            f.write(str(data))
        
        return str(output_path)
    
    def export_to_pdf(self, report_type: str, data: Dict[str, Any]) -> str:
        """Xuất báo cáo ra PDF theo loại"""
        exporters = {
            "balance_sheet": self.export_balance_sheet_pdf,
            "income_statement": self.export_income_statement_pdf,
            "vat_report": self.export_vat_report_pdf,
        }
        
        exporter = exporters.get(report_type)
        if exporter:
            return exporter(data)
        else:
            return self._fallback_export(data, report_type)


# ========== KIỂM TRA ==========
if __name__ == "__main__":
    print("=== KIỂM TRA PDF EXPORTER ===")
    
    if HAS_REPORTLAB:
        print("✅ Reportlab đã cài đặt")
    else:
        print("⚠️ Reportlab chưa cài, cài bằng: pip install reportlab")
    
    exporter = PDFExporter()
    
    # Test data
    test_data = {
        "report_name": "BÁO CÁO TEST",
        "report_date": "24/04/2026",
        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "from_date": "01/01/2026",
        "to_date": "31/12/2026",
        "vat_rate": 10,
        "output": {"invoice_count": 10, "sales_amount": 100000000, "vat_amount": 10000000},
        "input": {"purchase_count": 5, "purchase_amount": 50000000, "vat_amount": 5000000},
        "payable_vat": 5000000,
        "revenue": {"total": 100000000, "details": []},
        "expense": {"total": 60000000, "details": []},
        "net_profit": 40000000,
        "groups": {},
        # Cập nhật ngưỡng tài sản mẫu lên 1 tỷ cho khớp với logic thuế mới
        "total_assets": config.get_tax_threshold(),
        "total_liabilities_equity": config.get_tax_threshold()
    }
    
    result = exporter.export_to_pdf("vat_report", test_data)
    print(f"✅ Đã xuất: {result}")