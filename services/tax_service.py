from datetime import datetime
from utils.logger import get_logger
import config
logger = get_logger(__name__)

class TaxService:
    """Xử lý logic nghiệp vụ liên quan đến tính thuế"""
    
    # Tỷ lệ thuế theo ngành nghề (TT40/2021)
    TAX_RATES = {
        "Phân phối, cung cấp hàng hóa": {"vat": 0.01, "pit": 0.005},
        "Dịch vụ, xây dựng không bao thầu": {"vat": 0.05, "pit": 0.02},
        "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa": {"vat": 0.03, "pit": 0.015},
        "Hoạt động kinh doanh khác": {"vat": 0.02, "pit": 0.01}
    }
    
    @staticmethod
    def calculate_tax(revenue, business_type, industry, tax_year=None):
        """Tính thuế dựa trên doanh thu và loại hình doanh nghiệp (cập nhật TT18/2026)"""
        if tax_year is None:
            tax_year = datetime.now().year
        
        rates = TaxService.TAX_RATES.get(industry, TaxService.TAX_RATES["Phân phối, cung cấp hàng hóa"])
        result = {'vat': 0, 'pit': 0, 'tndn': 0, 'mon_bai': 0, 'note': ''}
        
        try:
            if "Hộ kinh doanh" in business_type:
                # Hộ kinh doanh cá thể - theo TT18/2026 và Nghị định 68/2026
                if tax_year >= 2026:
                    if revenue <= config.get_tax_threshold():
                        # Nhóm 1: Miễn thuế GTGT và TNCN
                        result['vat'] = 0
                        result['pit'] = 0
                        # Tìm dòng result['note'] trong hàm calculate_tax và sửa thành:
                        result['note'] = f"Miễn thuế (doanh thu ≤ {config.get_tax_threshold():,.0f} VNĐ/năm)"
                    else:
                        # Nhóm 2: Thuế theo % doanh thu
                        result['vat'] = revenue * rates['vat']
                        result['pit'] = revenue * rates['pit']
                        result['note'] = f"Áp dụng tỷ lệ GTGT={rates['vat']*100}%, TNCN={rates['pit']*100}% trên doanh thu"
                    # Môn bài đã bãi bỏ từ 2026
                    result['mon_bai'] = 0
                else:
                    # Quy định cũ (trước 2026)
                    if revenue <= 100_000_000:
                        result['vat'] = 0
                        result['pit'] = 0
                        result['mon_bai'] = 0
                    else:
                        result['vat'] = revenue * rates['vat']
                        result['pit'] = revenue * rates['pit']
                        if revenue <= 300_000_000:
                            result['mon_bai'] = 300_000
                        elif revenue <= 500_000_000:
                            result['mon_bai'] = 500_000
                        else:
                            result['mon_bai'] = 1_000_000
            else:
                # Doanh nghiệp - giữ nguyên logic cũ
                profit = revenue * 0.1
                result['tndn'] = profit * 0.20
                result['vat'] = revenue * 0.10
                if tax_year < 2026:
                    if revenue <= 1_000_000_000:
                        result['mon_bai'] = 1_000_000
                    elif revenue <= 3_000_000_000:
                        result['mon_bai'] = 1_500_000
                    else:
                        result['mon_bai'] = 2_000_000
                else:
                    result['mon_bai'] = 0
            
            logger.info(f"Đã tính thuế cho doanh thu {revenue:,.0f} VNĐ, năm {tax_year}")
            return result
        except Exception as e:
            logger.error(f"Lỗi tính thuế: {e}")
            return result
    
    @staticmethod
    def get_industry_rates(industry):
        """Lấy tỷ lệ thuế theo ngành nghề"""
        return TaxService.TAX_RATES.get(industry, TaxService.TAX_RATES["Phân phối, cung cấp hàng hóa"])
    
    @staticmethod
    def get_available_industries():
        """Lấy danh sách ngành nghề có sẵn"""
        return list(TaxService.TAX_RATES.keys())
    
    @staticmethod
    def get_tax_summary(revenue, business_type, industry, tax_year=None):
        """Lấy tóm tắt thuế kèm giải thích (Cập nhật theo ngưỡng 1 tỷ)"""
        try:
            # Tính toán thuế dựa trên logic đã cập nhật trong calculate_tax
            tax = TaxService.calculate_tax(revenue, business_type, industry, tax_year)
            total = tax['vat'] + tax['pit'] + tax['tndn'] + tax['mon_bai']
            
            # Lấy ngưỡng động từ hệ thống để làm thông báo
            nguong_thue = config.get_tax_threshold()
            
            # Tạo ghi chú giải thích
            notes = []
            if tax_year and tax_year >= 2026:
                notes.append("Áp dụng quy định thuế mới từ 2026")
            
            if "Hộ kinh doanh" in business_type:
                # Kiểm tra ngưỡng theo luật mới từ 2026
                if tax_year and tax_year >= 2026:
                    if revenue <= nguong_thue:
                        notes.append(f"Miễn thuế (doanh thu ≤ {nguong_thue:,.0f} VNĐ/năm)")
                # Kiểm tra ngưỡng theo luật cũ trước 2026
                elif revenue <= 100_000_000:
                    notes.append("Miễn thuế (doanh thu ≤ 100 triệu VNĐ/năm)")
            
            return {
                'details': tax,
                'total': total,
                'note': f"Tổng thuế phải nộp: {total:,.0f} VNĐ",
                'notes': notes,
                'business_type': business_type,
                'industry': industry,
                'revenue': revenue,
                'tax_year': tax_year
            }
        except Exception as e:
            logger.error(f"Lỗi lấy tóm tắt thuế: {e}")
            return {'details': {}, 'total': 0, 'note': str(e)}
    
    @staticmethod
    def compare_tax_by_year(revenue, business_type, industry, years=None):
        """So sánh thuế qua các năm"""
        if years is None:
            years = [2025, 2026, 2027]
        
        try:
            result = {}
            for year in years:
                tax = TaxService.calculate_tax(revenue, business_type, industry, year)
                total = tax['vat'] + tax['pit'] + tax['tndn'] + tax['mon_bai']
                result[year] = {
                    'vat': tax['vat'],
                    'pit': tax['pit'],
                    'tndn': tax['tndn'],
                    'mon_bai': tax['mon_bai'],
                    'total': total
                }
            return result
        except Exception as e:
            logger.error(f"Lỗi so sánh thuế theo năm: {e}")
            return {}
    
    @staticmethod
    def get_tax_by_industry_comparison(revenue, business_type, tax_year=None):
        """So sánh thuế giữa các ngành nghề"""
        if tax_year is None:
            tax_year = datetime.now().year
        
        try:
            result = {}
            for industry, rates in TaxService.TAX_RATES.items():
                tax = TaxService.calculate_tax(revenue, business_type, industry, tax_year)
                total = tax['vat'] + tax['pit'] + tax['tndn'] + tax['mon_bai']
                result[industry] = {
                    'rates': rates,
                    'vat': tax['vat'],
                    'pit': tax['pit'],
                    'total': total
                }
            return result
        except Exception as e:
            logger.error(f"Lỗi so sánh thuế theo ngành: {e}")
            return {}
    
    @staticmethod
    def get_tax_recommendation(revenue, business_type, tax_year=None):
        """Đề xuất ngành nghề có mức thuế thấp nhất"""
        if tax_year is None:
            tax_year = datetime.now().year
        
        try:
            comparison = TaxService.get_tax_by_industry_comparison(revenue, business_type, tax_year)
            if not comparison:
                return None
            
            # Tìm ngành có tổng thuế thấp nhất
            best_industry = min(comparison.items(), key=lambda x: x[1]['total'])
            
            return {
                'recommended_industry': best_industry[0],
                'tax_amount': best_industry[1]['total'],
                'rates': best_industry[1]['rates'],
                'all_industries': comparison
            }
        except Exception as e:
            logger.error(f"Lỗi đề xuất ngành nghề: {e}")
            return None