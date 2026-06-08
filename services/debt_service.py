from models.debt import Debt
from models.transaction import Transaction
from models.journal_entry import JournalEntry
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class DebtService:
    """Xử lý logic nghiệp vụ liên quan đến công nợ"""
    
    @staticmethod
    def get_all_debts():
        try:
            return Debt.get_all()
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách nợ: {e}")
            return []
    
    @staticmethod
    def get_debt_by_name_phone(name, phone):
        try:
            return Debt.get_by_name_phone(name, phone)
        except Exception as e:
            logger.error(f"Lỗi lấy nợ của {name}: {e}")
            return None
    
    @staticmethod
    def add_debt(name, phone, amount, date=None, notes=""):
        try:
            if date is None:
                date = datetime.now().strftime("%d/%m/%Y")
            Debt.add_debt(name, phone, amount, date, notes)
            logger.info(f"Đã thêm nợ {amount:,.0f} VNĐ cho {name}")
            return True, "Thêm nợ thành công"
        except Exception as e:
            logger.error(f"Lỗi thêm nợ: {e}")
            return False, str(e)
    
    @staticmethod
    def record_payment(name, phone, amount, date=None, notes=""):
        try:
            if date is None:
                date = datetime.now().strftime("%d/%m/%Y")
            
            # Kiểm tra nợ hiện tại
            debt = Debt.get_by_name_phone(name, phone)
            if not debt:
                return False, "Không tìm thấy khoản nợ"
            
            remaining = debt['total_debt'] - debt['paid']
            if amount > remaining:
                return False, f"Số tiền trả vượt quá nợ còn lại ({remaining:,.0f} VNĐ)"
            
            # Ghi nhận trả nợ
            Debt.record_payment(name, phone, amount, date, notes)
            
            # Ghi nhận giao dịch thu nợ
            Transaction.create(
                date=date,
                description=f"Thu nợ từ {name} - {phone}",
                amount=amount,
                trans_type="Thu",
                category="Thu nợ"
            )
            
            # Ghi nhận bút toán kép
            JournalEntry.create(
                date=date,
                description=f"Thu nợ từ {name} - {phone}",
                entries=[
                    {"account": "111", "debit": amount, "credit": 0},
                    {"account": "131", "debit": 0, "credit": amount}
                ]
            )
            
            logger.info(f"Đã ghi nhận trả nợ {amount:,.0f} VNĐ từ {name}")
            return True, "Ghi nhận trả nợ thành công"
        except Exception as e:
            logger.error(f"Lỗi ghi nhận trả nợ: {e}")
            return False, str(e)
    
    @staticmethod
    def delete_debt(name, phone):
        try:
            Debt.delete(name, phone)
            logger.info(f"Đã xóa nợ của {name}")
            return True, "Xóa thành công"
        except Exception as e:
            logger.error(f"Lỗi xóa nợ: {e}")
            return False, str(e)
    
    @staticmethod
    def get_total_remaining_debt():
        try:
            debts = Debt.get_all()
            total = sum(d['total_debt'] - d['paid'] for d in debts)
            return total
        except Exception as e:
            logger.error(f"Lỗi tính tổng nợ: {e}")
            return 0
    
    @staticmethod
    def get_debts_by_customer(name=None, phone=None):
        """Lọc nợ theo khách hàng"""
        try:
            debts = Debt.get_all()
            result = []
            for d in debts:
                if name and name.lower() in d['name'].lower():
                    result.append(d)
                elif phone and phone in d['phone']:
                    result.append(d)
                elif not name and not phone:
                    result.append(d)
            return result
        except Exception as e:
            logger.error(f"Lỗi lọc nợ theo khách hàng: {e}")
            return []
    
    @staticmethod
    def get_debts_with_high_risk(threshold_days=30):
        """Lấy danh sách nợ có nguy cơ cao (quá hạn)"""
        try:
            from datetime import datetime, timedelta
            debts = Debt.get_all()
            today = datetime.now()
            result = []
            for d in debts:
                try:
                    last_date = datetime.strptime(d['last_debt_date'], "%d/%m/%Y")
                    days_overdue = (today - last_date).days
                    if days_overdue > threshold_days and (d['total_debt'] - d['paid']) > 0:
                        result.append({
                            'name': d['name'],
                            'phone': d['phone'],
                            'remaining': d['total_debt'] - d['paid'],
                            'days_overdue': days_overdue,
                            'last_date': d['last_debt_date']
                        })
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.error(f"Lỗi lấy nợ quá hạn: {e}")
            return []
    
    @staticmethod
    def get_debt_summary():
        """Lấy tóm tắt công nợ"""
        try:
            debts = Debt.get_all()
            total_debt = sum(d['total_debt'] for d in debts)
            total_paid = sum(d['paid'] for d in debts)
            total_remaining = total_debt - total_paid
            active_debts = len([d for d in debts if (d['total_debt'] - d['paid']) > 0])
            
            return {
                'total_debt': total_debt,
                'total_paid': total_paid,
                'total_remaining': total_remaining,
                'active_debts': active_debts,
                'total_customers': len(debts)
            }
        except Exception as e:
            logger.error(f"Lỗi lấy tóm tắt nợ: {e}")
            return {
                'total_debt': 0, 'total_paid': 0, 'total_remaining': 0,
                'active_debts': 0, 'total_customers': 0
            }
    
    @staticmethod
    def get_customer_debt_history(name, phone):
        """Lấy lịch sử nợ của khách hàng"""
        try:
            debt = Debt.get_by_name_phone(name, phone)
            if not debt:
                return None
            
            # Chỉ lấy giao dịch thu nợ của khách này thay vì lấy tất cả
            transactions = Transaction.get_all()
            payment_history = [
                {
                    'date': t['date'],
                    'amount': t['amount'],
                    'description': t['description']
                }
                for t in transactions
                if t['category'] == "Thu nợ" and name in t['description']
            ]
            
            return {
                'current_debt': {
                    'total_debt': debt['total_debt'],
                    'paid': debt['paid'],
                    'remaining': debt['total_debt'] - debt['paid'],
                    'last_date': debt['last_debt_date'],
                    'notes': debt['notes']
                },
                'payment_history': sorted(
                    payment_history,
                    key=lambda x: x['date'],
                    reverse=True
                )
            }
        except Exception as e:
            logger.error(f"Lỗi lấy lịch sử nợ của {name}: {e}")
            return None