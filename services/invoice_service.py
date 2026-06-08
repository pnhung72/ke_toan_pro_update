from models.invoice import Invoice
from models.product import Product
from models.journal_entry import JournalEntry
from models.debt import Debt
from datetime import datetime
from utils.logger import get_logger
from models.database import Database

logger = get_logger(__name__)

class InvoiceService:
    """Xử lý logic nghiệp vụ liên quan đến hóa đơn"""
    
    @staticmethod
    def get_all_invoices(limit: int = None) -> list:
        try:
            return Invoice.get_all(limit)
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách hóa đơn: {e}")
            return []
    
    @staticmethod
    def get_invoice_by_id(inv_id: int) -> dict:
        try:
            return Invoice.get_by_id(inv_id)
        except Exception as e:
            logger.error(f"Lỗi lấy hóa đơn {inv_id}: {e}")
            return None
    
    @staticmethod
    def create_invoice(buyer_name: str, phone: str, tax_code: str, address: str, product_code: str,
                   quantity: float, unit_price: float, total_excluding_tax: float, tax_amount: float,
                   total_payment: float, paid: float, payment_method: str, created_date: str = None) -> tuple:
        try:
            if created_date is None:
                created_date = datetime.now().strftime("%d/%m/%Y")
            
            # Kiểm tra tồn kho
            product = Product.get_by_code(product_code)
            if product and product['stock'] < quantity:
                return False, f"Sản phẩm chỉ còn {product['stock']} đơn vị", None
            
            # Tạo hóa đơn
            inv_id = Invoice.create(
                buyer_name, phone, tax_code, address, product_code, quantity,
                unit_price, total_excluding_tax, tax_amount, total_payment,
                paid, payment_method, created_date
            )
            
            # Ghi nhận bút toán kép
            journal_entries = [
                {"account": "131", "debit": total_payment, "credit": 0},
                {"account": "511", "debit": 0, "credit": total_excluding_tax}
            ]
            if tax_amount > 0:
                journal_entries.append({"account": "3331", "debit": 0, "credit": tax_amount})
            
            JournalEntry.create(
                date=created_date,
                description=f"Hóa đơn {inv_id} - {buyer_name}",
                entries=journal_entries
            )
            
            # Xử lý nợ nếu còn
            remaining = total_payment - paid
            if remaining > 0:
                Debt.add_debt(buyer_name, phone, remaining, created_date, 
                             f"Hóa đơn {inv_id} - Còn nợ {remaining:,.0f} VND")
            
            logger.info(f"Đã tạo hóa đơn {inv_id} cho {buyer_name}")
            return True, f"Thêm hóa đơn thành công", inv_id
        except Exception as e:
            logger.error(f"Lỗi tạo hóa đơn: {e}")
            return False, str(e), None
    
    @staticmethod
    def update_invoice(inv_id: int, **kwargs) -> bool:
        try:
            Invoice.update(inv_id, **kwargs)
            logger.info(f"Đã cập nhật hóa đơn {inv_id}")
            return True, "Cập nhật thành công"
        except Exception as e:
            logger.error(f"Lỗi cập nhật hóa đơn {inv_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_invoice(inv_id: int) -> bool:
        try:
            Invoice.delete(inv_id)
            logger.info(f"Đã xóa hóa đơn {inv_id}")
            return True, "Xóa thành công"
        except Exception as e:
            logger.error(f"Lỗi xóa hóa đơn {inv_id}: {e}")
            return False, str(e)
    
    @staticmethod
    def get_total_revenue() -> float:
        try:
            return Invoice.get_total_revenue()
        except Exception as e:
            logger.error(f"Lỗi tính tổng doanh thu: {e}")
            return 0
    
    @staticmethod
    def get_unpaid_invoices() -> list:
        try:
            return Invoice.get_unpaid_invoices()
        except Exception as e:
            logger.error(f"Lỗi lấy hóa đơn chưa thanh toán: {e}")
            return []
    
    @staticmethod
    def get_invoices_by_customer(name: str = None, phone: str = None) -> list:
        """Lấy hóa đơn theo khách hàng"""
        try:
            invoices = Invoice.get_all()
            result = []
            for inv in invoices:
                if name and name.lower() in inv['buyer_name'].lower():
                    result.append(inv)
                elif phone and phone in inv['phone']:
                    result.append(inv)
                elif not name and not phone:
                    result.append(inv)
            return result
        except Exception as e:
            logger.error(f"Lỗi lấy hóa đơn theo khách hàng: {e}")
            return []
    
    @staticmethod
    def get_invoices_by_date_range(start_date: str, end_date: str) -> list:
        """Lấy hóa đơn trong khoảng thời gian"""
        try:
            invoices = Invoice.get_all()
            result = []
            for inv in invoices:
                try:
                    d, m, y = inv['created_date'].split('/')
                    inv_date = f"{y}-{m}-{d}"
                    if start_date <= inv_date <= end_date:
                        result.append(inv)
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.error(f"Lỗi lọc hóa đơn theo ngày: {e}")
            return []
    
    @staticmethod
    def get_monthly_revenue(year: int, month: int) -> float:
        """Lấy doanh thu theo tháng"""
        try:
            month_str = f"{month:02d}"
            invoices = Invoice.get_all()
            total = 0
            for inv in invoices:
                try:
                    d, m, y = inv['created_date'].split('/')
                    if int(y) == year and m == month_str:
                        total += inv['total_payment']
                except Exception:
                    continue
            return total
        except Exception as e:
            logger.error(f"Lỗi tính doanh thu tháng: {e}")
            return 0
    
    @staticmethod
    def get_yearly_revenue(year: int) -> float:
        """Lấy doanh thu theo năm"""
        try:
            invoices = Invoice.get_all()
            total = 0
            for inv in invoices:
                try:
                    _, _, y = inv['created_date'].split('/')
                    if int(y) == year:
                        total += inv['total_payment']
                except Exception:
                    continue
            return total
        except Exception as e:
            logger.error(f"Lỗi tính doanh thu năm: {e}")
            return 0
    
    @staticmethod
    def get_invoice_summary() -> dict:
        """Lấy tóm tắt hóa đơn (tổng số, tổng tiền, nợ)"""
        try:
            invoices = Invoice.get_all()
            total_invoices = len(invoices)
            total_revenue = sum(inv['total_payment'] for inv in invoices)
            total_paid = sum(inv['paid'] for inv in invoices)
            total_debt = total_revenue - total_paid
            
            return {
                'total_invoices': total_invoices,
                'total_revenue': total_revenue,
                'total_paid': total_paid,
                'total_debt': total_debt
            }
        except Exception as e:
            logger.error(f"Lỗi lấy tóm tắt hóa đơn: {e}")
            return {'total_invoices': 0, 'total_revenue': 0, 'total_paid': 0, 'total_debt': 0}
            
