# -*- coding: utf-8 -*-
"""
TaxCompliance - Tuan thu phap ly ve thue
Theo Thong tu 18/2026/TT-BTC, TT152/2025/TT-BTC, Nghi dinh 68/2026/ND-CP
"""

from datetime import datetime
import config
class TaxCompliance:
    """Kiem tra tuan thu cac quy dinh ve thue"""
    
    # Nguong doanh thu theo Nghi dinh 68/2026/ND-CP
    THRESHOLD_NGUONG = config.get_tax_threshold()  # 500 trieu dong/nam
    
    # Cac han nop theo quy dinh
    DEADLINES = {
        "01/BK-STK": "20/04/2026",  # Thong bao tai khoan ngan hang
        "01/TKN-CNKD": "31/07/2026",  # Thong bao doanh thu 6 thang dau
        "01/CNKD": "31/01/2027",  # To khai thue ca nam
    }
    
    @classmethod
    def check_revenue_threshold(cls, yearly_revenue):
        """Kiem tra doanh thu co vuot nguong 500tr khong"""
        if yearly_revenue >= cls.THRESHOLD_NGUONG:
            return {
                "exceeded": True,
                "message": f"Doanh thu {yearly_revenue:,.0f} VND vuot nguong {cls.THRESHOLD_NGUONG:,.0f} VND",
                "required_form": "01/CNKD",
                "action": "Phai nop to khai thue theo mau 01/CNKD"
            }
        else:
            return {
                "exceeded": False,
                "message": f"Doanh thu {yearly_revenue:,.0f} VND duoi nguong {config.get_tax_threshold():,.0f} VND",
                "required_form": "S1a-HKD",
                "action": "Chi can nop so doanh thu theo mau S1a-HKD"
            }
    
    @classmethod
    def get_deadline(cls, form_type):
        """Lay han nop cho tung mau bieu"""
        return cls.DEADLINES.get(form_type, "Chua xac dinh")
    
    @classmethod
    def check_deadline(cls, form_type):
        """Kiem tra con han nop khong"""
        deadline_str = cls.get_deadline(form_type)
        if deadline_str == "Chua xac dinh":
            return {"status": "unknown", "message": "Khong xac dinh duoc han nop"}
        
        try:
            deadline = datetime.strptime(deadline_str, "%d/%m/%Y")
            today = datetime.now()
            
            if today > deadline:
                return {
                    "status": "overdue",
                    "message": f"DA QUA HAN! Han nop la {deadline_str}",
                    "days_overdue": (today - deadline).days
                }
            else:
                days_left = (deadline - today).days
                return {
                    "status": "pending",
                    "message": f"Con {days_left} ngay den han nop {deadline_str}",
                    "days_left": days_left
                }
        except Exception as e:
            return {"status": "error", "message": f"Loi kiem tra: {e}"}
    
    @classmethod
    def get_required_forms(cls, yearly_revenue):
        """Lay danh sach mau bieu can nop"""
        forms = []
        
        # Mau 01/BK-STK (Thong bao tai khoan)
        forms.append({
            "code": "01/BK-STK",
            "name": "Thong bao tai khoan ngan hang",
            "deadline": cls.get_deadline("01/BK-STK")
        })
        
        # Kiem tra nguong doanh thu
        threshold_result = cls.check_revenue_threshold(yearly_revenue)
        
        if threshold_result["exceeded"]:
            forms.append({
                "code": "01/CNKD",
                "name": "To khai thue (doanh thu > 1 tỷ)",
                "deadline": cls.get_deadline("01/CNKD")
            })
        else:
            forms.append({
                "code": "S1a-HKD",
                "name": "So doanh thu ban hang",
                "deadline": "Theo ky ke khai"
            })
        
        # Mau 01/TKN-CNKD (Thong bao doanh thu 6 thang)
        forms.append({
            "code": "01/TKN-CNKD",
            "name": "Thong bao doanh thu (6 thang dau)",
            "deadline": cls.get_deadline("01/TKN-CNKD")
        })
        
        return forms