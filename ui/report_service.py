from models.transaction import Transaction
from models.invoice import Invoice
from datetime import datetime

class ReportService:
    @staticmethod
    def get_total_income():
        # from transactions
        trans_income = Transaction.get_total_income()
        # from invoices (total payment)
        invoice_income = Invoice.get_total_revenue()
        return trans_income + invoice_income

    @staticmethod
    def get_total_expense():
        return Transaction.get_total_expense()

    @staticmethod
    def get_categories_summary():
        # returns dict category -> total amount (positive for income, negative for expense)
        categories = {}
        # from transactions
        for t in Transaction.get_all():
            cat = t['category']
            amount = t['amount'] if t['type'] == 'Thu' else -t['amount']
            categories[cat] = categories.get(cat, 0) + amount
        # from invoices (treated as income under category "Bán hàng")
        invoice_income = Invoice.get_total_revenue()
        if invoice_income > 0:
            cat = "Bán hàng (hóa đơn)"
            categories[cat] = categories.get(cat, 0) + invoice_income
        return categories

    @staticmethod
    def get_quarterly_report():
        # Returns dict year -> quarter -> {'income':, 'expense':}
        result = {}
        # process transactions
        for t in Transaction.get_all():
            try:
                d, m, y = t['date'].split('/')
                year = int(y)
                month = int(m)
                quarter = (month-1)//3 + 1
                q_key = f"Q{quarter}"
                if year not in result:
                    result[year] = {f"Q{i}": {'income': 0, 'expense': 0} for i in range(1,5)}
                if t['type'] == 'Thu':
                    result[year][q_key]['income'] += t['amount']
                else:
                    result[year][q_key]['expense'] += t['amount']
            except Exception:
                continue
        # process invoices (use created_date)
        for inv in Invoice.get_all():
            try:
                date_str = inv['created_date']
                d, m, y = date_str.split('/')
                year = int(y)
                month = int(m)
                quarter = (month-1)//3 + 1
                q_key = f"Q{quarter}"
                if year not in result:
                    result[year] = {f"Q{i}": {'income': 0, 'expense': 0} for i in range(1,5)}
                # invoice total payment is income
                result[year][q_key]['income'] += inv['total_payment']
            except Exception:
                continue
        return result

    @staticmethod
    def get_yearly_report():
        # returns dict year -> {'income':, 'expense':}
        result = {}
        for t in Transaction.get_all():
            try:
                y = t['date'].split('/')[2]
                year = int(y)
                if year not in result:
                    result[year] = {'income': 0, 'expense': 0}
                if t['type'] == 'Thu':
                    result[year]['income'] += t['amount']
                else:
                    result[year]['expense'] += t['amount']
            except Exception:
                continue
        for inv in Invoice.get_all():
            try:
                y = inv['created_date'].split('/')[2]
                year = int(y)
                if year not in result:
                    result[year] = {'income': 0, 'expense': 0}
                result[year]['income'] += inv['total_payment']
            except Exception:
                continue
        return result

    @staticmethod
    def calculate_tax(revenue, business_type='Hộ kinh doanh cá thể', industry='Phân phối, cung cấp hàng hóa', tax_year=None):
        # simplified tax calculation
        if tax_year is None:
            tax_year = datetime.now().year
        
        tax_rates = {
            "Phân phối, cung cấp hàng hóa": {"vat": 0.01, "pit": 0.005},
            "Dịch vụ, xây dựng không bao thầu": {"vat": 0.05, "pit": 0.02},
            "Sản xuất, vận tải, dịch vụ có gắn với hàng hóa": {"vat": 0.03, "pit": 0.015},
            "Hoạt động kinh doanh khác": {"vat": 0.02, "pit": 0.01}
        }
        rates = tax_rates.get(industry, tax_rates["Phân phối, cung cấp hàng hóa"])
        
        result = {'vat': 0, 'pit': 0, 'tndn': 0, 'mon_bai': 0}
        if "Hộ kinh doanh" in business_type:
            if tax_year >= 2026:
                if revenue <= 500_000_000:
                    # exempt
                    result['vat'] = 0
                    result['pit'] = 0
                else:
                    result['vat'] = revenue * rates['vat']
                    result['pit'] = revenue * rates['pit']
                result['mon_bai'] = 0
            else:
                if revenue <= 100_000_000:
                    result['vat'] = result['pit'] = result['mon_bai'] = 0
                else:
                    result['vat'] = revenue * rates['vat']
                    result['pit'] = revenue * rates['pit']
                    if revenue <= 300_000_000:
                        result['mon_bai'] = 300_000
                    elif revenue <= 500_000_000:
                        result['mon_bai'] = 500_000
                    else:
                        result['mon_bai'] = 1_000_000
        elif "Doanh nghiệp" in business_type:
            profit = revenue * 0.1  # assume 10% margin
            result['tndn'] = profit * 0.20
            result['vat'] = revenue * 0.10
            if revenue <= 1_000_000_000:
                result['mon_bai'] = 1_000_000
            elif revenue <= 3_000_000_000:
                result['mon_bai'] = 1_500_000
            else:
                result['mon_bai'] = 2_000_000
        return result