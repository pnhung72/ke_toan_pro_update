# -*- coding: utf-8 -*-
import pandas as pd

class AgriParser:
    """Module chuyên biệt cho Agribank - Kế Toán Pro v5.2.4"""
    def __init__(self):
        self.mapping = {
            'date': 'Ngày hạch toán',
            'ref': 'Số tham chiếu',
            'in': 'Phát sinh Có',
            'out': 'Phát sinh Nợ',
            'desc': 'Diễn giải'
        }

    def parse(self, file_path):
        try:
            df = pd.read_excel(file_path)
            return [
                {
                    'trans_date': row.get(self.mapping['date']),
                    'reference': row.get(self.mapping['ref']),
                    'amount_in': float(row.get(self.mapping['in'], 0) or 0),
                    'amount_out': float(row.get(self.mapping['out'], 0) or 0),
                    'description': str(row.get(self.mapping['desc'], '')),
                    'bank_code': 'AGRI'
                }
                for _, row in df.iterrows() if pd.notnull(row.get(self.mapping['date']))
            ]
        except Exception as e:
            raise Exception(f"Lỗi đọc file Agribank: {str(e)}")