# -*- coding: utf-8 -*-
import os
import json
import re
import logging
import ast

class ReportEngine:
    def __init__(self, db_connection, config_path: str = None) -> None:
        """
        Khoi tao Engine tinh toan bao cao dong theo Thong tu
        :param db_connection: Ket noi tu Pool SQLite hien tai cua he thong
        """
        self.db = db_connection
        if config_path is None:
            # Tu dong lay duong dan tuyet doi den file bctc_formula.json trong config/templates
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.abspath(os.path.join(current_dir, '../../configs/templates/bctc_formula.json'))
        else:
            self.config_path = config_path

    def lay_so_du_no(self, tai_khoan: str) -> float:
        """
        Truy van tinh tong so du No cua Tai khoan tu bang chung tu (journal_details)
        Lay chinh xac cac tai khoan bat dau bang ky tu truyen vao (Vi du: 111 bao gom 1111, 1112)
        """
        try:
            cursor = self.db.cursor()
            # Kiem tra xem gia tri no tru co co > 0 khong de lay so du No phat sinh
            query = "SELECT SUM(debit - credit) FROM journal_details WHERE account_code LIKE ?"
            cursor.execute(query, (f"{tai_khoan}%",))
            result = cursor.fetchone()[0]
            return float(result) if result and result > 0 else 0.0
        except Exception:
            return 0.0

    def lay_so_du_co(self, tai_khoan: str) -> float:
        """
        Truy van tinh tong so du Co cua Tai khoan tu bang chung tu (journal_details)
        """
        try:
            cursor = self.db.cursor()
            # Kiem tra xem gia tri co tru no co > 0 khong de lay so du Co phat sinh
            query = "SELECT SUM(credit - debit) FROM journal_details WHERE account_code LIKE ?"
            cursor.execute(query, (f"{tai_khoan}%",))
            result = cursor.fetchone()[0]
            return float(result) if result and result > 0 else 0.0
        except Exception:
            return 0.0

    def phan_tich_va_tinh_cong_thuc(self, chuoi_cong_thuc: str) -> float:
        """
        Bo phan giai ma bieu thuc: bien doi chuoi "DU_NO(111) + DU_NO(112)" thanh so lieu cu the
        """
        if not chuoi_cong_thuc or chuoi_cong_thuc.strip() == "":
            return 0.0
            
        cong_thuc_so = chuoi_cong_thuc
        
        # 1. Quet tat ca cac bieu thuc DU_NO(xxx) de lay so lieu tu database thay vao
        cac_tk_no = re.findall(r'DU_NO\((\d+)\)', chuoi_cong_thuc)
        for tk in cac_tk_no:
            so_tien = self.lay_so_du_no(tk)
            cong_thuc_so = cong_thuc_so.replace(f"DU_NO({tk})", str(so_tien))
            
        # 2. Quet tat ca cac bieu thuc DU_CO(xxx) de lay so lieu tu database thay vao
        cac_tk_co = re.findall(r'DU_CO\((\d+)\)', chuoi_cong_thuc)
        for tk in cac_tk_co:
            so_tien = self.lay_so_du_co(tk)
            cong_thuc_so = cong_thuc_so.replace(f"DU_CO({tk})", str(so_tien))
            
        # 3. Kiem tra tinh toan toan bieu thuc so an toan (tranh loi bao mat eval)
        try:
            # Chi thuc thi neu chuoi sau khi thay the chi co chua so va phep tinh toan hoc basic
            if re.match(r'^[0-9\s\+\-\*\/\.\(\)]+$', cong_thuc_so):
                return float(ast.literal_eval(cong_thuc_so))
            return 0.0
        except Exception:
            return 0.0

    def xuat_bao_cao_tai_chinh(self) -> list:
        """
        Ham trung tam duoc goi tu file UI de tra ve mang ket qua phuc vu render do hoa
        """
        if not os.path.exists(self.config_path):
            logging.error(f"Không tìm thấy file bctc_formula.json tại: {self.config_path}")
            return []

        # Doc va phan tich file JSON cau hinh bieu mau
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except Exception as e:
            logging.error(f"Lỗi cú pháp JSON file cấu hình: {str(e)}")
            return []

        ket_qua_bao_cao = []
        
        # Doc va tinh toan tung dong chi tieu mot cach khep kin
        for chi_tieu in config_data.get("cac_chi_tieu", []):
            so_tien_tinh_duoc = self.phan_tich_va_tinh_cong_thuc(chi_tieu.get("cong_thuc", ""))
            
            ket_qua_bao_cao.append({
                "ma_so": chi_tieu.get("ma_so", ""),
                "ten_chi_tieu": chi_tieu.get("ten_chi_tieu", ""),
                "co_in_dam": chi_tieu.get("co_in_dam", False),
                "so_tien": so_tien_tinh_duoc
            })
            
        return ket_qua_bao_cao