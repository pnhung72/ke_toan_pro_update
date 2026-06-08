from models.business import Business, BankAccount
from models.database import Database
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

class BankAccountService:
    """Xử lý nghiệp vụ cho mẫu 01/BK-STK (Thông báo tài khoản)"""
    
    @staticmethod
    def get_all_accounts(ma_so_thue=None):
        """Lấy danh sách tài khoản"""
        return BankAccount.get_all(ma_so_thue)
    
    @staticmethod
    def add_account(ma_so_thue, ten_ngan_hang, so_tai_khoan, so_hieu_vi_dien_tu="", la_tai_khoan_chinh=0):
        """Thêm tài khoản ngân hàng"""
        if not ten_ngan_hang or not so_tai_khoan:
            return False, "Vui lòng nhập đầy đủ tên ngân hàng và số tài khoản"
        return BankAccount.add(ma_so_thue, ten_ngan_hang, so_tai_khoan, so_hieu_vi_dien_tu, la_tai_khoan_chinh), "Thành công"
    
    @staticmethod
    def delete_account(account_id):
        """Xóa tài khoản"""
        return BankAccount.delete(account_id)
    
    @staticmethod
    def generate_xml(ma_so_thue):
        """Tạo file XML theo chuẩn Tổng cục Thuế cho mẫu 01/BK-STK"""
        business = Business.get_info(ma_so_thue)
        if not business:
            raise Exception(f"Không tìm thấy hộ kinh doanh với mã số thuế {ma_so_thue}")
        
        accounts = BankAccount.get_all(ma_so_thue)
        if not accounts:
            raise Exception("Chưa có tài khoản ngân hàng nào. Vui lòng thêm tài khoản trước.")
        
        # Tạo XML
        root = ET.Element("ThongBaoTaiKhoan")
        
        # Thông tin chung
        thong_tin_chung = ET.SubElement(root, "ThongTinChung")
        ET.SubElement(thong_tin_chung, "MaSoThue").text = ma_so_thue
        ET.SubElement(thong_tin_chung, "TenNguoiNopThue").text = business.get('ten_ho_kinh_doanh', '')
        ET.SubElement(thong_tin_chung, "NgayLap").text = datetime.now().strftime("%Y-%m-%d")
        
        # Danh sách tài khoản
        danh_sach = ET.SubElement(root, "DanhSachTaiKhoan")
        for acc in accounts:
            tai_khoan = ET.SubElement(danh_sach, "TaiKhoan")
            ET.SubElement(tai_khoan, "TenNganHang").text = acc.get('ten_ngan_hang', '')
            ET.SubElement(tai_khoan, "SoTaiKhoan").text = acc.get('so_tai_khoan', '')
            if acc.get('so_hieu_vi_dien_tu'):
                ET.SubElement(tai_khoan, "SoHieuViDienTu").text = acc.get('so_hieu_vi_dien_tu', '')
            ET.SubElement(tai_khoan, "LaTaiKhoanChinh").text = "true" if acc.get('la_tai_khoan_chinh') else "false"
        
        # Chuyển thành chuỗi XML đẹp
        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')
    
    @staticmethod
    def generate_html_preview(ma_so_thue):
        """Tạo HTML để xem trước khi in (theo mẫu thông báo của cơ quan thuế)"""
        business = Business.get_info(ma_so_thue)
        if not business:
            return None
        
        accounts = BankAccount.get_all(ma_so_thue)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Thông báo số tài khoản - Mẫu 01/BK-STK</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .title {{ font-size: 18px; font-weight: bold; }}
                .subtitle {{ font-size: 14px; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .info-table td {{ padding: 8px; border: 1px solid #ddd; vertical-align: top; }}
                .info-table td:first-child {{ width: 30%; background-color: #f5f5f5; font-weight: bold; }}
                .signature {{ margin-top: 50px; text-align: right; }}
                .note {{ font-size: 12px; color: #666; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">THÔNG BÁO SỐ TÀI KHOẢN/SỐ HIỆU VÍ ĐIỆN TỬ</div>
                <div class="subtitle">(Mẫu số 01/BK-STK ban hành kèm theo Thông tư 18/2026/TT-BTC)</div>
            </div>
            
            <table class="info-table">
                <tr><td>Mã số thuế:</td><td>{business.get('ma_so_thue', '')}</td></tr>
                <tr><td>Tên hộ kinh doanh:</td><td>{business.get('ten_ho_kinh_doanh', '')}</td></tr>
                <tr><td>Địa chỉ:</td><td>{business.get('dia_chi', '')}</td></tr>
                <tr><td>Số điện thoại:</td><td>{business.get('so_dien_thoai', '')}</td></tr>
                <tr><td>Email:</td><td>{business.get('email', '')}</td></tr>
            </table>
            
            <h3>Danh sách tài khoản ngân hàng / ví điện tử:</h3>
            <table class="info-table">
                <tr style="background-color: #e0e0e0;">
                    <th>STT</th>
                    <th>Tên ngân hàng</th>
                    <th>Số tài khoản / Ví điện tử</th>
                    <th>Tài khoản chính</th>
                </tr>
        """
        
        for i, acc in enumerate(accounts, 1):
            html += f"""
                <tr>
                    <td>{i}</td>
                    <td>{acc.get('ten_ngan_hang', '')}</td>
                    <td>{acc.get('so_tai_khoan', '')}{'<br>Ví: ' + acc.get('so_hieu_vi_dien_tu', '') if acc.get('so_hieu_vi_dien_tu') else ''}</td>
                    <td>{'✓' if acc.get('la_tai_khoan_chinh') else ''}</td>
                </tr>
            """
        
        html += f"""
            </table>
            
            <div class="signature">
                <div>Ngày {datetime.now().day} tháng {datetime.now().month} năm {datetime.now().year}</div>
                <div style="margin-top: 40px;"><strong>NGƯỜI ĐẠI DIỆN HỘ KINH DOANH</strong></div>
                <div>(Ký, ghi rõ họ tên, đóng dấu nếu có)</div>
            </div>
            
            <div class="note">
                <strong>Lưu ý:</strong> Hạn nộp mẫu 01/BK-STK là ngày 20/04/2026.<br>
                Khi thay đổi tài khoản ngân hàng hoặc ví điện tử, phải thông báo lại cho cơ quan thuế.
            </div>
        </body>
        </html>
        """
        return html
    
    @staticmethod
    def get_han_nop():
        """Trả về hạn nộp của mẫu 01/BK-STK (20/04/2026)"""
        from datetime import date
        han_nop = date(2026, 4, 20)
        today = date.today()
        
        if today > han_nop:
            return f"Đã quá hạn (hạn nộp: 20/04/2026). Vui lòng nộp càng sớm càng tốt."
        else:
            con_lai = (han_nop - today).days
            return f"Còn {con_lai} ngày đến hạn nộp (20/04/2026)"