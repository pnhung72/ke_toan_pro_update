from models.database import Database
from models.transaction import Transaction
from models.invoice import Invoice
from models.business import Business
from services.tax_service import TaxService
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class BusinessTaxReturnService:
    """Xử lý nghiệp vụ cho mẫu 01/CNKD (Tờ khai thuế đối với hộ kinh doanh)"""
    
    @staticmethod
    def get_quarter_revenue(ma_so_thue, quy, nam):
        """
        Lấy doanh thu theo quý
        quy: 1, 2, 3, 4
        nam: năm
        """
        from datetime import datetime
        
        # Hàm chuyển đổi chuỗi ngày dd/mm/yyyy thành datetime để so sánh chính xác
        def parse_date(date_str):
            try:
                d, m, y = date_str.split('/')
                return datetime(int(y), int(m), int(d))
            except Exception:
                return None
        
        def is_date_in_range(date_str, start_dt, end_dt):
            """Kiểm tra ngày có nằm trong khoảng không"""
            date_dt = parse_date(date_str)
            if date_dt:
                return start_dt <= date_dt <= end_dt
            return False
        
        # Xác định khoảng thời gian (dùng datetime object)
        if quy == 1:
            start_dt = datetime(nam, 1, 1)
            end_dt = datetime(nam, 3, 31)
            start_date_str = f"01/01/{nam}"
            end_date_str = f"31/03/{nam}"
        elif quy == 2:
            start_dt = datetime(nam, 4, 1)
            end_dt = datetime(nam, 6, 30)
            start_date_str = f"01/04/{nam}"
            end_date_str = f"30/06/{nam}"
        elif quy == 3:
            start_dt = datetime(nam, 7, 1)
            end_dt = datetime(nam, 9, 30)
            start_date_str = f"01/07/{nam}"
            end_date_str = f"30/09/{nam}"
        else:  # quy 4
            start_dt = datetime(nam, 10, 1)
            end_dt = datetime(nam, 12, 31)
            start_date_str = f"01/10/{nam}"
            end_date_str = f"31/12/{nam}"
        
        # Lấy tất cả transactions và lọc bằng datetime
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, amount
                FROM transactions
                WHERE type = 'Thu'
            ''')
            all_transactions = cursor.fetchall()
        
        transaction_revenue = 0
        for t in all_transactions:
            if is_date_in_range(t['date'], start_dt, end_dt):
                transaction_revenue += t['amount']
        
        # Lấy tất cả invoices và lọc bằng datetime
        all_invoices = Invoice.get_all()
        invoice_revenue = 0
        for inv in all_invoices:
            try:
                d, m, y = inv['created_date'].split('/')
                inv_date = f"{int(d):02d}/{int(m):02d}/{y}"
                if is_date_in_range(inv_date, start_dt, end_dt):
                    invoice_revenue += inv['total_payment']
            except Exception:
                continue
        
        total_revenue = transaction_revenue + invoice_revenue
        return total_revenue
    
    @staticmethod
    def get_quarter_expense(ma_so_thue, quy, nam):
        """Lấy chi phí theo quý (cho nhóm 3 - tính thu nhập)"""
        from datetime import datetime
        
        def parse_date(date_str):
            try:
                d, m, y = date_str.split('/')
                return datetime(int(y), int(m), int(d))
            except Exception:
                return None
        
        def is_date_in_range(date_str, start_dt, end_dt):
            date_dt = parse_date(date_str)
            if date_dt:
                return start_dt <= date_dt <= end_dt
            return False
        
        if quy == 1:
            start_dt = datetime(nam, 1, 1)
            end_dt = datetime(nam, 3, 31)
        elif quy == 2:
            start_dt = datetime(nam, 4, 1)
            end_dt = datetime(nam, 6, 30)
        elif quy == 3:
            start_dt = datetime(nam, 7, 1)
            end_dt = datetime(nam, 9, 30)
        else:
            start_dt = datetime(nam, 10, 1)
            end_dt = datetime(nam, 12, 31)
        
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, amount
                FROM transactions
                WHERE type = 'Chi'
            ''')
            all_transactions = cursor.fetchall()
        
        total_expense = 0
        for t in all_transactions:
            if is_date_in_range(t['date'], start_dt, end_dt):
                total_expense += t['amount']
        
        return total_expense
    
    @staticmethod
    def calculate_tax_for_group2(revenue, industry, nam):
        """Tính thuế cho nhóm 2 (1 tỷ - 3 tỷ) - thuế theo % doanh thu"""
        rates = TaxService.TAX_RATES.get(industry, TaxService.TAX_RATES["Phân phối, cung cấp hàng hóa"])
        
        vat = revenue * rates['vat']
        pit = revenue * rates['pit']
        
        return {
            'vat': vat,
            'pit': pit,
            'total': vat + pit,
            'vat_rate': rates['vat'] * 100,
            'pit_rate': rates['pit'] * 100
        }
    
    @staticmethod
    def calculate_tax_for_group3(revenue, expense, industry, nam):
        """Tính thuế cho nhóm 3 (3 tỷ - 50 tỷ) - TNCN theo thu nhập tính thuế"""
        # Thu nhập tính thuế = Doanh thu - Chi phí
        taxable_income = revenue - expense
        
        # Thuế suất TNCN theo bảng lũy tiến (giả định)
        if taxable_income <= 60_000_000:
            pit_rate = 0.05
        elif taxable_income <= 120_000_000:
            pit_rate = 0.10
        elif taxable_income <= 216_000_000:
            pit_rate = 0.15
        elif taxable_income <= 384_000_000:
            pit_rate = 0.20
        elif taxable_income <= 624_000_000:
            pit_rate = 0.25
        elif taxable_income <= 960_000_000:
            pit_rate = 0.30
        else:
            pit_rate = 0.35
        
        pit = taxable_income * pit_rate
        
        # GTGT vẫn tính theo % doanh thu (như nhóm 2)
        rates = TaxService.TAX_RATES.get(industry, TaxService.TAX_RATES["Phân phối, cung cấp hàng hóa"])
        vat = revenue * rates['vat']
        
        return {
            'vat': vat,
            'vat_rate': rates['vat'] * 100,
            'pit': pit,
            'pit_rate': pit_rate * 100,
            'taxable_income': taxable_income,
            'total': vat + pit
        }
    
    @staticmethod
    def generate_html_cnkd(ma_so_thue, quy, nam, business_info):
        """Tạo HTML cho mẫu 01/CNKD"""
        revenue = BusinessTaxReturnService.get_quarter_revenue(ma_so_thue, quy, nam)
        expense = BusinessTaxReturnService.get_quarter_expense(ma_so_thue, quy, nam)
        
        nhom_doi_tuong = business_info.get('nhom_doi_tuong', 'group2')
        nganh_nghe = business_info.get('nganh_nghe_kinh_doanh', 'Phân phối, cung cấp hàng hóa')
        
        if nhom_doi_tuong == 'group2':
            tax = BusinessTaxReturnService.calculate_tax_for_group2(revenue, nganh_nghe, nam)
            tax_method = "Thuế tính theo tỷ lệ % trên doanh thu"
        else:  # group3
            tax = BusinessTaxReturnService.calculate_tax_for_group3(revenue, expense, nganh_nghe, nam)
            tax_method = "Thuế TNCN tính theo thu nhập tính thuế (doanh thu - chi phí)"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Tờ khai thuế 01/CNKD - Quý {quy}/{nam}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ font-size: 18px; font-weight: bold; }}
                .subtitle {{ font-size: 14px; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; }}
                .info-table td {{ padding: 8px; border: 1px solid #000; vertical-align: top; }}
                .info-table td:first-child {{ width: 30%; background-color: #f5f5f5; font-weight: bold; }}
                .tax-table {{ width: 60%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; }}
                .tax-table td {{ padding: 8px; border: 1px solid #000; }}
                .tax-table td:first-child {{ background-color: #f5f5f5; font-weight: bold; }}
                .total {{ font-size: 14px; font-weight: bold; color: red; }}
                .signature {{ margin-top: 50px; text-align: right; }}
                .footer {{ font-size: 10px; margin-top: 30px; text-align: center; border-top: 1px solid #ccc; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">TỜ KHAI THUẾ ĐỐI VỚI HỘ KINH DOANH, CÁ NHÂN KINH DOANH</div>
                <div class="subtitle">(Mẫu số 01/CNKD ban hành kèm theo Thông tư 18/2026/TT-BTC)</div>
            </div>
            
            <table class="info-table">
                <tr><td>Hộ kinh doanh: </td><td colspan="3">{business_info.get('ten_ho_kinh_doanh', '')}</td></tr>
                <tr><td>Mã số thuế: </td><td colspan="3">{business_info.get('ma_so_thue', '')}</td></tr>
                <tr><td>Địa chỉ: </td><td colspan="3">{business_info.get('dia_chi', '')}</td></tr>
                <tr><td>Ngành nghề: </td><td colspan="3">{nganh_nghe}</td></tr>
                <tr><td>Kỳ khai thuế: </td><td colspan="3">Quý {quy}/{nam}</td></tr>
                <tr><td>Phương pháp tính: </td><td colspan="3">{tax_method}</td></tr>
            </table>
            
            <h3>Kết quả tính thuế:</h3>
            <table class="tax-table">
                <tr><td>Doanh thu kỳ khai thuế:</td><td style="text-align: right;">{revenue:,.0f} VNĐ</td></tr>"""
        
        if nhom_doi_tuong == 'group2':
            html += f"""
                <tr><td>Thuế GTGT phải nộp ({tax['vat_rate']:.1f}%):</td><td style="text-align: right;">{tax['vat']:,.0f} VNĐ</td></tr>
                <tr><td>Thuế TNCN phải nộp ({tax['pit_rate']:.1f}%):</td><td style="text-align: right;">{tax['pit']:,.0f} VNĐ</td></tr>"""
        else:
            html += f"""
                <tr><td>Thu nhập tính thuế (Doanh thu - Chi phí):</td><td style="text-align: right;">{tax['taxable_income']:,.0f} VNĐ</td></tr>
                <tr><td>Thuế GTGT phải nộp ({tax['vat_rate']:.1f}%):</td><td style="text-align: right;">{tax['vat']:,.0f} VNĐ</td></tr>
                <tr><td>Thuế TNCN phải nộp ({tax['pit_rate']:.1f}%):</td><td style="text-align: right;">{tax['pit']:,.0f} VNĐ</td></tr>
                <tr><td>Chi phí kỳ khai thuế:</td><td style="text-align: right;">{expense:,.0f} VNĐ</td></tr>"""
        
        html += f"""
                <tr class="total">
                    <td>TỔNG THUẾ PHẢI NỘP:</td>
                    <td style="text-align: right;">{tax['total']:,.0f} VNĐ</td>
                </tr>
            </table>
            
            <div class="signature">
                <div>Ngày ... tháng ... năm ...</div>
                <div style="margin-top: 40px;"><strong>NGƯỜI ĐẠI DIỆN HỘ KINH DOANH</strong></div>
                <div>(Ký, ghi rõ họ tên, đóng dấu nếu có)</div>
            </div>
            
            <div class="footer">
                <div>Hạn nộp tờ khai: Chậm nhất ngày cuối cùng của tháng đầu tiên của quý sau.</div>
                <div>Hạn nộp thuế: Chậm nhất là ngày cuối cùng của thời hạn nộp hồ sơ khai thuế.</div>
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def get_han_nop(quy, nam):
        """Trả về hạn nộp của mẫu 01/CNKD"""
        if quy == 1:
            return f"30/04/{nam}"
        elif quy == 2:
            return f"31/07/{nam}"
        elif quy == 3:
            return f"30/10/{nam}"
        else:
            return f"31/01/{nam+1}"