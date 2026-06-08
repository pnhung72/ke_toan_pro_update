from .database import Database
from datetime import datetime

class Business:
    """Quản lý thông tin hộ kinh doanh"""
    
    @staticmethod
    def get_info(ma_so_thue=None):
        """Lấy thông tin hộ kinh doanh"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            if ma_so_thue:
                cursor.execute("SELECT * FROM business_info WHERE ma_so_thue = ?", (ma_so_thue,))
            else:
                cursor.execute("SELECT * FROM business_info LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def save_or_update(ma_so_thue, ten_ho_kinh_doanh, dia_chi=None, so_dien_thoai=None, 
                       email=None, loai_hinh="Hộ kinh doanh", nhom_doi_tuong="group1",
                       ngay_bat_dau_kinh_doanh=None, nganh_nghe_kinh_doanh=None):
        """Lưu hoặc cập nhật thông tin hộ kinh doanh"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            existing = Business.get_info(ma_so_thue)
            
            if existing:
                cursor.execute('''
                    UPDATE business_info SET
                        ten_ho_kinh_doanh = ?,
                        dia_chi = ?,
                        so_dien_thoai = ?,
                        email = ?,
                        loai_hinh = ?,
                        nhom_doi_tuong = ?,
                        ngay_bat_dau_kinh_doanh = ?,
                        nganh_nghe_kinh_doanh = ?
                    WHERE ma_so_thue = ?
                ''', (ten_ho_kinh_doanh, dia_chi, so_dien_thoai, email, loai_hinh,
                      nhom_doi_tuong, ngay_bat_dau_kinh_doanh, nganh_nghe_kinh_doanh, ma_so_thue))
            else:
                cursor.execute('''
                    INSERT INTO business_info (
                        ma_so_thue, ten_ho_kinh_doanh, dia_chi, so_dien_thoai,
                        email, loai_hinh, nhom_doi_tuong, ngay_bat_dau_kinh_doanh, nganh_nghe_kinh_doanh
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (ma_so_thue, ten_ho_kinh_doanh, dia_chi, so_dien_thoai,
                      email, loai_hinh, nhom_doi_tuong, ngay_bat_dau_kinh_doanh, nganh_nghe_kinh_doanh))
            return True
    
    @staticmethod
    def get_all_nhom_doi_tuong():
        """Lấy danh sách nhóm đối tượng để hiển thị trong dropdown"""
        return {
            "group1": "Doanh thu < 500tr (không chịu thuế GTGT, không nộp TNCN)",
            "group2": "Doanh thu 500tr - 3 tỷ (thuế theo % doanh thu)",
            "group3": "Doanh thu 3 - 50 tỷ (thuế TNCN theo thu nhập tính thuế)",
            "group4": "Doanh thu > 50 tỷ (kê khai theo tháng)"
        }


class BankAccount:
    """Quản lý tài khoản ngân hàng (mẫu 01/BK-STK)"""
    
    @staticmethod
    def get_all(ma_so_thue=None):
        """Lấy danh sách tài khoản ngân hàng"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            if ma_so_thue:
                cursor.execute('''
                    SELECT ba.*, bi.ma_so_thue 
                    FROM bank_accounts ba
                    JOIN business_info bi ON ba.business_id = bi.id
                    WHERE bi.ma_so_thue = ?
                    ORDER BY ba.la_tai_khoan_chinh DESC
                ''', (ma_so_thue,))
            else:
                cursor.execute('''
                    SELECT ba.*, bi.ma_so_thue 
                    FROM bank_accounts ba
                    JOIN business_info bi ON ba.business_id = bi.id
                    ORDER BY ba.la_tai_khoan_chinh DESC
                ''')
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def add(ma_so_thue, ten_ngan_hang, so_tai_khoan, so_hieu_vi_dien_tu="", la_tai_khoan_chinh=0):
        """Thêm tài khoản ngân hàng"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            # Lấy business_id từ ma_so_thue
            cursor.execute("SELECT id FROM business_info WHERE ma_so_thue = ?", (ma_so_thue,))
            business = cursor.fetchone()
            if not business:
                raise Exception(f"Không tìm thấy hộ kinh doanh với mã số thuế {ma_so_thue}")
            
            # Nếu đặt là tài khoản chính, bỏ chính các tài khoản khác
            if la_tai_khoan_chinh == 1:
                cursor.execute("UPDATE bank_accounts SET la_tai_khoan_chinh = 0 WHERE business_id = ?", (business['id'],))
            
            cursor.execute('''
                INSERT INTO bank_accounts (business_id, ten_ngan_hang, so_tai_khoan, so_hieu_vi_dien_tu, la_tai_khoan_chinh, ngay_thong_bao)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (business['id'], ten_ngan_hang, so_tai_khoan, so_hieu_vi_dien_tu, la_tai_khoan_chinh, 
                  datetime.now().strftime("%d/%m/%Y")))
            return True
    
    @staticmethod
    def delete(account_id):
        """Xóa tài khoản ngân hàng"""
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bank_accounts WHERE id = ?", (account_id,))
            return cursor.rowcount > 0