# -*- coding: utf-8 -*-
import pandas as pd

class ACBParser:
    """
    Module chuyên biệt xử lý sao kê ACB cho Kế Toán Pro v5.2.4.
    Tối ưu: Tách biệt cấu trúc cột (Mapping) để bảo trì độc lập.
    """
    def __init__(self):
        # Chốt danh sách cột chuẩn của ACB. 
        # Nếu ngân hàng đổi mẫu, Thầy chỉ cần sửa duy nhất tại đây.
        self.mapping = {
            'date': 'Ngày giao dịch',
            'ref': 'Số chứng từ',
            'in': 'Số tiền ghi có',
            'out': 'Số tiền ghi nợ',
            'desc': 'Nội dung'
        }

    def parse(self, file_path):
        """Đọc file Excel ACB và chuyển đổi sang định dạng chuẩn hệ thống"""
        try:
            # Đọc file Excel (Sử dụng engine openpyxl mặc định của pandas)
            df = pd.read_excel(file_path)
            
            # Chuyển đổi dữ liệu sang List[Dict] để khớp với Repository.py
            return [
                {
                    'trans_date': row.get(self.mapping['date']),
                    'reference': row.get(self.mapping['ref']),
                    'amount_in': float(row.get(self.mapping['in'], 0) or 0),
                    'amount_out': float(row.get(self.mapping['out'], 0) or 0),
                    'description': str(row.get(self.mapping['desc'], '')),
                    'bank_code': 'ACB'
                }
                for _, row in df.iterrows() 
                if pd.notnull(row.get(self.mapping['date'])) # Chỉ lấy dòng có dữ liệu
            ]
        except Exception as e:
            raise Exception(f"Lỗi đọc file ACB: {str(e)}")

# Chốt phương án: Module độc lập, dữ liệu đầu ra chuẩn hóa.