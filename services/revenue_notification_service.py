from models.database import Database
from models.transaction import Transaction
from models.invoice import Invoice
from models.business import Business
from datetime import datetime
from utils.logger import get_logger
import config
logger = get_logger(__name__)

class RevenueNotificationService:
    """Xử lý nghiệp vụ cho mẫu 01/TKN-CNKD (Thông báo doanh thu thực tế phát sinh)"""
    
    @staticmethod
    def detect_duplicates(ma_so_thue, start_date, end_date):
        """Phát hiện giao dịch và hóa đơn trùng lặp trong kỳ"""
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
        
        # Chuyển đổi start_date và end_date thành datetime except Exception:
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        
        if not start_dt or not end_dt:
            # Nếu không parse được, fallback về so sánh chuỗi (giữ nguyên hành vi cũ)
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT date, amount, description, id as trans_id
                    FROM transactions
                    WHERE type = 'Thu'
                    AND date >= ? AND date <= ?
                ''', (start_date, end_date))
                transactions = cursor.fetchall()
            
            # Lấy hóa đơn
            invoices = Invoice.get_all()
            invoice_list = []
            for inv in invoices:
                try:
                    d, m, y = inv['created_date'].split('/')
                    inv_date = f"{int(d):02d}/{int(m):02d}/{y}"
                    if start_date <= inv_date <= end_date:
                        invoice_list.append({
                            'date': inv_date,
                            'amount': inv['total_payment'],
                            'description': f"Hóa đơn {inv['id']} - {inv['buyer_name']}",
                            'inv_id': inv['id']
                        })
                except Exception:
                    continue
            
            # Phát hiện trùng lặp
            duplicates = []
            for t in transactions:
                for inv in invoice_list:
                    if t['date'] == inv['date'] and abs(t['amount'] - inv['amount']) < 1000:
                        duplicates.append({
                            'date': t['date'],
                            'amount': t['amount'],
                            'transaction_id': t['trans_id'],
                            'invoice_id': inv['inv_id'],
                            'transaction_desc': t['description'],
                            'invoice_desc': inv['description']
                        })
            return duplicates
        
        # === SỬ DỤNG DATETIME ĐỂ SO SÁNH CHÍNH XÁC ===
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            # Lấy tất cả giao dịch thu (không lọc bằng SQL để tránh lỗi so sánh chuỗi)
            cursor.execute('''
                SELECT date, amount, description, id as trans_id
                FROM transactions
                WHERE type = 'Thu'
            ''')
            all_transactions = cursor.fetchall()
        
        # Lọc transactions bằng datetime
        transactions = []
        for t in all_transactions:
            if is_date_in_range(t['date'], start_dt, end_dt):
                transactions.append({
                    'date': t['date'],
                    'amount': t['amount'],
                    'description': t['description'],
                    'trans_id': t['trans_id']
                })
        
        # Lấy hóa đơn và lọc bằng datetime
        invoices = Invoice.get_all()
        invoice_list = []
        for inv in invoices:
            try:
                d, m, y = inv['created_date'].split('/')
                inv_date = f"{int(d):02d}/{int(m):02d}/{y}"
                if is_date_in_range(inv_date, start_dt, end_dt):
                    invoice_list.append({
                        'date': inv_date,
                        'amount': inv['total_payment'],
                        'description': f"Hóa đơn {inv['id']} - {inv['buyer_name']}",
                        'inv_id': inv['id']
                    })
            except Exception:
                continue
        
        # Phát hiện trùng lặp (cùng ngày và số tiền chênh lệch không quá 1000)
        duplicates = []
        for t in transactions:
            for inv in invoice_list:
                if t['date'] == inv['date'] and abs(t['amount'] - inv['amount']) < 1000:
                    duplicates.append({
                        'date': t['date'],
                        'amount': t['amount'],
                        'transaction_id': t['trans_id'],
                        'invoice_id': inv['inv_id'],
                        'transaction_desc': t['description'],
                        'invoice_desc': inv['description']
                    })
        
        # Loại bỏ các cặp trùng lặp trùng lặp (cùng ngày và số tiền)
        unique_duplicates = []
        seen_keys = set()
        for dup in duplicates:
            key = f"{dup['date']}_{dup['amount']}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_duplicates.append(dup)
        
        return unique_duplicates
    
    @staticmethod
    def get_revenue_by_period(ma_so_thue, ky_thong_bao, nam, source='auto'):
        """
        Lấy tổng doanh thu theo kỳ thông báo với phát hiện thông minh
        
        Args:
            ma_so_thue: Mã số thuế
            ky_thong_bao: '6_thang_dau' hoặc 'ca_nam'
            nam: năm cần lấy dữ liệu
            source: 'auto', 'invoices', 'transactions', 'both', 'deduplicated'
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
        
        # Xác định khoảng thời gian (dùng datetime except Exception:)
        if ky_thong_bao == '6_thang_dau':
            start_dt = datetime(nam, 1, 1)
            end_dt = datetime(nam, 6, 30)
            start_date_str = f"01/01/{nam}"
            end_date_str = f"30/06/{nam}"
            ten_ky = f"6 tháng đầu năm {nam}"
        else:
            start_dt = datetime(nam, 1, 1)
            end_dt = datetime(nam, 12, 31)
            start_date_str = f"01/01/{nam}"
            end_date_str = f"31/12/{nam}"
            ten_ky = f"Cả năm {nam}"
        
        # Lấy tất cả transactions và lọc theo ngày thực tế
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, amount, description, id
                FROM transactions
                WHERE type = 'Thu'
            ''')
            all_transactions = cursor.fetchall()
        
        transaction_revenue = 0
        transaction_list = []
        for t in all_transactions:
            if is_date_in_range(t['date'], start_dt, end_dt):
                transaction_revenue += t['amount']
                transaction_list.append({
                    'date': t['date'],
                    'amount': t['amount'],
                    'description': t['description'],
                    'id': t['id']
                })
        
        # Lấy tất cả invoices và lọc theo ngày thực tế
        all_invoices = Invoice.get_all()
        invoice_revenue = 0
        invoice_list = []
        for inv in all_invoices:
            try:
                d, m, y = inv['created_date'].split('/')
                inv_date = f"{int(d):02d}/{int(m):02d}/{y}"
                if is_date_in_range(inv_date, start_dt, end_dt):
                    invoice_revenue += inv['total_payment']
                    invoice_list.append({
                        'date': inv_date,
                        'amount': inv['total_payment'],
                        'description': f"Hóa đơn {inv['id']} - {inv['buyer_name']}",
                        'id': inv['id']
                    })
            except Exception:
                continue
        
        # === PHÁT HIỆN TRÙNG LẶP (cùng ngày, cùng số tiền) ===
        duplicates = []
        for t in transaction_list:
            for inv in invoice_list:
                if t['date'] == inv['date'] and abs(t['amount'] - inv['amount']) < 1000:
                    duplicates.append({
                        'date': t['date'],
                        'amount': t['amount'],
                        'transaction_id': t['id'],
                        'invoice_id': inv['id'],
                        'transaction_desc': t['description'],
                        'invoice_desc': inv['description']
                    })
        
        # Loại bỏ trùng lặp để tránh đếm nhiều lần
        unique_duplicates = []
        seen_keys = set()
        for dup in duplicates:
            key = f"{dup['date']}_{dup['amount']}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_duplicates.append(dup)
        duplicates = unique_duplicates
        duplicate_amount = sum(d['amount'] for d in duplicates)
        
        # Tính toán theo từng chế độ
        if source == 'invoices':
            total_revenue = invoice_revenue
            note = "Chỉ tính từ hóa đơn (khuyến nghị cho kê khai thuế)"
            recommendation = "✅ Nên dùng cho báo cáo chính thức"
        elif source == 'transactions':
            total_revenue = transaction_revenue
            note = "Chỉ tính từ giao dịch thu (phù hợp nếu không xuất hóa đơn)"
            recommendation = "⚠️ Chỉ dùng khi không có hóa đơn"
        elif source == 'both':
            total_revenue = transaction_revenue + invoice_revenue
            note = "Tính từ cả hai nguồn (có thể bị trùng lặp)"
            recommendation = "❌ Không khuyến nghị do trùng lặp"
        elif source == 'deduplicated':
            total_revenue = transaction_revenue + invoice_revenue - duplicate_amount
            note = "Đã loại bỏ trùng lặp tự động"
            recommendation = "✅ Tốt nhất khi có cả hai nguồn"
        else:  # 'auto' - tự động chọn tốt nhất
            if invoice_revenue > 0:
                total_revenue = invoice_revenue
                source_used = "invoices"
                note = "Tự động chọn: Từ hóa đơn (phát hiện có dữ liệu hóa đơn)"
                recommendation = "✅ Khuyến nghị cho kê khai"
            elif transaction_revenue > 0:
                total_revenue = transaction_revenue
                source_used = "transactions"
                note = "Tự động chọn: Từ giao dịch thu (không có hóa đơn)"
                recommendation = "⚠️ Chấp nhận được"
            else:
                total_revenue = 0
                source_used = "none"
                note = "Không có dữ liệu doanh thu"
                recommendation = "❌ Cần nhập dữ liệu"
            
            # Ghi đè để trả về đúng
            return RevenueNotificationService.get_revenue_by_period(
                ma_so_thue, ky_thong_bao, nam, source_used
            )
        
        vuot_nguong = total_revenue > config.get_tax_threshold()
        has_duplicates = len(duplicates) > 0
        
        # Kiểm tra ngưỡng doanh thu từ hệ thống (1 tỷ)
        tax_threshold = config.get_tax_threshold()
        vuot_nguong = total_revenue > tax_threshold

        return {
            'ky_thong_bao': ten_ky,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'total_revenue': total_revenue,
            'transaction_revenue': transaction_revenue,
            'invoice_revenue': invoice_revenue,
            'duplicate_amount': duplicate_amount,
            'duplicate_count': len(duplicates),
            'duplicates': duplicates,
            'has_duplicates': has_duplicates,
            'vuot_nguong': vuot_nguong, # Đã đổi tên biến cho chuẩn
            'source': source,
            'note': note,
            'recommendation': recommendation,
            'canh_bao': f"Doanh thu vượt {tax_threshold:,.0f} đồng. Quý tiếp theo phải chuyển sang kê khai thuế theo mẫu 01/CNKD." if vuot_nguong else None,
            'canh_bao_trung': f"Phát hiện {len(duplicates)} cặp giao dịch trùng lặp (tổng {duplicate_amount:,.0f} VNĐ). Nên chọn chế độ 'Đã loại bỏ trùng lặp'." if has_duplicates else None
        }
    
    @staticmethod
    def get_han_nop(ky_thong_bao, nam):
        """Trả về hạn nộp của mẫu 01/TKN-CNKD"""
        if ky_thong_bao == '6_thang_dau':
            return f"31/07/{nam}"
        else:
            return f"31/01/{nam+1}"
    
    @staticmethod
    def generate_html_tkn(ma_so_thue, ky_thong_bao, nam, business_info, source='auto'):
        """Tạo HTML cho mẫu 01/TKN-CNKD"""
        data = RevenueNotificationService.get_revenue_by_period(ma_so_thue, ky_thong_bao, nam, source)
        
        han_nop = RevenueNotificationService.get_han_nop(ky_thong_bao, nam)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Thong bao doanh thu - 01/TKN-CNKD</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ font-size: 18px; font-weight: bold; }}
                .subtitle {{ font-size: 14px; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; }}
                .info-table td {{ padding: 8px; border: 1px solid #000; vertical-align: top; }}
                .info-table td:first-child {{ width: 30%; background-color: #f5f5f5; font-weight: bold; }}
                .revenue-table {{ width: 60%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; }}
                .revenue-table td {{ padding: 8px; border: 1px solid #000; }}
                .revenue-table td:first-child {{ background-color: #f5f5f5; font-weight: bold; }}
                .warning {{ color: red; font-weight: bold; margin: 20px 0; padding: 10px; background-color: #ffeeee; border: 1px solid red; }}
                .info {{ color: blue; margin: 10px 0; padding: 8px; background-color: #eef; border: 1px solid blue; }}
                .signature {{ margin-top: 50px; text-align: right; }}
                .footer {{ font-size: 10px; margin-top: 30px; text-align: center; border-top: 1px solid #ccc; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">THÔNG BÁO DOANH THU THỰC TẾ PHÁT SINH</div>
                <div class="subtitle">(Mẫu số 01/TKN-CNKD ban hành kèm theo Thông tư 18/2026/TT-BTC)</div>
            </div>
            
            <table class="info-table">
                <tr><td>Hộ kinh doanh: </td><td colspan="3">{business_info.get('ten_ho_kinh_doanh', '')}</td></tr>
                <tr><td>Mã số thuế: </td><td colspan="3">{business_info.get('ma_so_thue', '')}</td></tr>
                <tr><td>Địa chỉ: </td><td colspan="3">{business_info.get('dia_chi', '')}</td></tr>
                <tr><td>Kỳ thông báo: </td><td colspan="3">{data['ky_thong_bao']}</td></tr>
                <tr><td>Hạn nộp: </td><td colspan="3">{han_nop}</td></tr>
                <tr><td colspan="4" style="background-color: #f0f0f0;">{data['note']}</td></tr>
            </table>
            
            <h3>Doanh thu thực tế phát sinh:</h3>
            <table class="revenue-table">
                <tr><td colspan="2" style="text-align: center; background-color: #e0e0e0;">CHI TIẾT DOANH THU</td></tr>
                <tr><td>Từ giao dịch thu: </td><td style="text-align: right;">{data['transaction_revenue']:,.0f} VNĐ</td></tr>
                <tr><td>Từ hóa đơn: </td><td style="text-align: right;">{data['invoice_revenue']:,.0f} VNĐ</td></tr>
                <tr style="font-weight: bold; background-color: #e0e0e0;">
                    <td>TỔNG DOANH THU: </td>
                    <td style="text-align: right; font-size: 14px;">{data['total_revenue']:,.0f} VNĐ</td>
                </tr>
            </table>
            """
        
        if data['has_duplicates']:
            html += f"""
            <div class="warning">
                ⚠️ CẢNH BÁO: Phát hiện {data['duplicate_count']} giao dịch trùng lặp (tổng {data['duplicate_amount']:,.0f} VNĐ)<br>
                Khuyến nghị: Kiểm tra lại dữ liệu hoặc sử dụng chế độ "Đã loại bỏ trùng lặp"
            </div>
            """
        
        if data['vuot_1 tỷ']:
            html += f"""
            <div class="warning">
                ⚠️ CẢNH BÁO: Doanh thu vượt 1 tỷ!<br>
                {data['canh_bao']}
            </div>
            """
        
        html += f"""
            <div class="info">
                💡 {data['recommendation']}
            </div>
            
            <div class="signature">
                <div>Ngày {datetime.now().day} tháng {datetime.now().month} năm {datetime.now().year}</div>
                <div style="margin-top: 40px;"><strong>NGƯỜI ĐẠI DIỆN HỘ KINH DOANH</strong></div>
                <div>(Ký, ghi rõ họ tên, đóng dấu nếu có)</div>
            </div>
            
            <div class="footer">
                <div>Lưu ý: Hộ kinh doanh có doanh thu từ 500 triệu đồng trở xuống chỉ cần nộp Thông báo doanh thu theo mẫu 01/TKN-CNKD,</div>
                <div>không phải nộp tờ khai thuế theo quý. Thời hạn nộp chậm nhất là ngày 31/01 của năm sau đối với thông báo cả năm,</div>
                <div>hoặc 31/07 đối với thông báo 6 tháng đầu năm đối với hộ mới ra kinh doanh.</div>
            </div>
        </body>
        </html>
        """
        return html