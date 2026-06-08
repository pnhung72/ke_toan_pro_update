# -*- coding: utf-8 -*-
import pandas as pd

class VCBParser:
    """Module chuyên biệt cho Vietcombank - Kế Toán Pro v5.2.4"""
    def __init__(self):
        self.mapping = {
            'date': 'Ngày giao dịch',
            'ref': 'Số chứng từ',
            'in': 'Số tiền ghi có',
            'out': 'Số tiền ghi nợ',
            'desc': 'Nội dung giao dịch'
        }

    def parse(self, file_path):
        try:
            # VCB thường có phần Header dài, ta bắt đầu đọc từ dòng tiêu đề (skiprows nếu cần)
            df = pd.read_excel(file_path)
            return [
                {
                    'trans_date': row.get(self.mapping['date']),
                    'reference': row.get(self.mapping['ref']),
                    'amount_in': float(row.get(self.mapping['in'], 0) or 0),
                    'amount_out': float(row.get(self.mapping['out'], 0) or 0),
                    'description': str(row.get(self.mapping['desc'], '')),
                    'bank_code': 'VCB'
                }
                for _, row in df.iterrows() if pd.notnull(row.get(self.mapping['date']))
            ]
        except Exception as e:
            raise Exception(f"Lỗi đọc file VCB: {str(e)}")