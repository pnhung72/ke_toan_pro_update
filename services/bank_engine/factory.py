# -*- coding: utf-8 -*-
from .acb_parser import ACBParser
from .vcb_parser import VCBParser
from .agri_parser import AgriParser

class BankEngineFactory:
    """Bí kíp: Trạm trung chuyển tự động điều hướng ngân hàng"""
    
    @staticmethod
    def get_parser(bank_code):
        parsers = {
            'ACB': ACBParser(),
            'VCB': VCBParser(),
            'AGRI': AgriParser()
        }
        parser = parsers.get(bank_code)
        if not parser:
            raise ValueError(f"Ngân hàng {bank_code} chưa được hỗ trợ trong hệ thống.")
        return parser