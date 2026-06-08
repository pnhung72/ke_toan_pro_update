# -*- coding: utf-8 -*-
import os
import json
import re

class ReportEngine:
    def __init__(self, db_connection, config_path=None):
        """
        Khoi tao Engine tinh bao cao dong
        :param db_connection: Ket noi den Database Sqlite hien tai cua thay
        """
        self.db = db_connection
        if config_path is None:
            # Tu dong lay duong dan den file config trong thu muc config/templates
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.abspath(os.path.join(current_dir, '../../configs/templates/bctc_formula.json'))
        else:
            self.config_path = config_path

    def lay_so_du_no(self, tai_khoan):
        """
        Truy van vao database de lay tong so du No cua Tai khoan
        """
        cursor = self.db.cursor()
        # Cau lenh SQL lay tong so du no tu bang journal_details hoac accounts cua thay
        query = "SELECT SUM(debit - credit) FROM journal_details WHERE account_code LIKE ?"
        cursor.execute(query, (f"{tai_khoan}%",))
        result = cursor.fetchone()[0]
        return float(result) if result else 0.0

    def lay_so_du_co(self, tai_khoan):
        """
        Truy van vao database de lay tong so du Co cua Tai khoan
        """
        cursor = self.db.cursor()
        query = "SELECT SUM(credit - debit) FROM journal_details WHERE account_code LIKE ?"
        cursor.execute(query, (f"{tai_khoan}%",))
        result = cursor.fetchone()[0]
        return float(result) if result else 0.0

    def phan_tich_va_tinh_cong_thuc(self, chuoi_cong_thuc):
        """
        Giai ma chuoi cong thuc nhu 'DU_NO(111) + DU_NO(112)' thanh so lieu
        """
        cong_thuc_so = chuoi_cong_thuc
        
        # 1. Quet va thay the cac ham DU_NO(xxx)
        cac_tk_no = re.findall(r'DU_NO\((\d+)\)', chuoi_cong_thuc)
        for tk in cac_tk_no:
            so_tien = self.lay_so_du_no(tk)
            cong_thuc_so = cong_thuc_so.replace(f"DU_NO({tk})", str(so_tien))
            
        # 2. Quet va thay the cac ham DU_CO(xxx)
        cac_tk_co = re.findall(r'DU_CO\((\d+)\)', chuoi_cong_thuc)
        for tk in cac_tk_co:
            so_tien = self.lay_so_du_co(tk)
            cong_thuc_so = cong_thuc_so.replace(f"DU_CO({tk})", str(so_tien))
            
        # 3. Tinh toan chuoi bieu thuc so an toan
        try:
            # Loc sach chuoi chi cho phep so, dau cach va cac phep tinh +, -, *, /
            if re.match(r'^[0-9\s\+\-\*\/\.\(\)]+$', cong_thuc_so):
                return eval(cong_thuc_so)
            return 0.0
        except Exception:
            return 0.0

    def xuat_bao_cao_tai_chinh(self):
        """
        Ham chinh de ui goi den va lay du lieu ra ve len giao dien
        """
        if not os.path.exists(self.config_path):
            print(f"Loi: Khong tim thay file cau hinh tai {self.config_path}")
            return []

        # Doc file JSON cau hinh thong tu
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        ket_qua_bao_cao = []
        
        # Duyet qua tung chi tieu trong file cau hinh de tinh toan dong
        for chi_tieu in config_data.get("cac_chi_tieu", []):
            so_tien = self.phan_tich_va_tinh_cong_thuc(chi_tieu["cong_thuc"])
            
            ket_qua_bao_cao.append({
                "ma_so": chi_tieu["ma_so"],
                "ten_chi_tieu": chi_tieu["ten_chi_tieu"],
                "co_in_dam": chi_tieu["co_in_dam"],
                "so_tien": so_tien
            })
            
        return ket_qua_bao_cao