# -*- coding: utf-8 -*-
from models.transaction import Transaction
from models.journal_entry import JournalEntry
from utils.logger import get_logger
from models.database import Database

logger = get_logger(__name__)

class TransactionService:
    """Xử lý logic nghiệp vụ giao dịch - Bản tối ưu hiệu suất & an toàn dữ liệu"""
    
    @staticmethod
    def get_all_transactions(limit=1000):
        try:
            # Đã loại bỏ các ký tự thừa gây lỗi NameError
            return Transaction.get_all(limit)
        except Exception as e:
            logger.error(f"Lỗi lấy danh sách giao dịch: {e}")
            return []
    
    @staticmethod
    def get_transaction_by_id(trans_id):
        try:
            return Transaction.get_by_id(trans_id)
        except Exception as e:
            logger.error(f"Lỗi lấy giao dịch {trans_id}: {e}")
            return None
    
    @staticmethod
    def create_transaction(date, description, amount, trans_type, category):
        """Tạo giao dịch và bút toán sổ cái đồng bộ (Atomic Transaction)"""
        try:
            if amount <= 0:
                return False, "Số tiền phải lớn hơn 0"
            
            # Sử dụng một kết nối duy nhất cho cả 2 hành động để đảm bảo tính nhất quán
            with Database.get_connection() as conn:
                try:
                    # 1. Ghi vào bảng giao dịch (truyền conn vào model)
                    trans_id = Transaction.create(date, description, amount, trans_type, category, connection=conn)
                    
                    # 2. Định nghĩa bút toán kép chuẩn kế toán
                    if trans_type == "Thu":
                        entries = [
                            {"account": "111", "debit": amount, "credit": 0},
                            {"account": "511", "debit": 0, "credit": amount}
                        ]
                    else:
                        entries = [
                            {"account": "642", "debit": amount, "credit": 0},
                            {"account": "111", "debit": 0, "credit": amount}
                        ]
                    
                    # 3. Ghi bút toán vào sổ cái (dùng chung conn)
                    JournalEntry.create(date=date, description=description, entries=entries, connection=conn)
                    
                    # Xác nhận lưu mọi thay đổi nếu không có lỗi
                    conn.commit()
                    
                    # Log thông báo chuẩn định dạng VN
                    fmt_amount = f"{amount:,.0f}".replace(",", ".")
                    logger.info(f"Đã tạo giao dịch: {description} - {fmt_amount} VNĐ")
                    return True, "Thêm giao dịch thành công"
                
                except Exception as inner_e:
                    conn.rollback() # Hủy bỏ nếu 1 trong 2 bước bị lỗi
                    raise inner_e
                    
        except Exception as e:
            logger.error(f"Lỗi tạo giao dịch: {e}")
            return False, str(e)

    @staticmethod
    def delete_transaction(trans_id):
        """Xóa giao dịch và các bút toán liên quan"""
        try:
            with Database.get_connection() as conn:
                # Xóa cả giao dịch và bút toán trong cùng 1 transaction
                Transaction.delete(trans_id, connection=conn)
                conn.commit()
                
            logger.info(f"Đã xóa giao dịch {trans_id}")
            return True, "Xóa thành công"
        except Exception as e:
            logger.error(f"Lỗi xóa giao dịch {trans_id}: {e}")
            return False, str(e)

    @staticmethod
    def get_monthly_summary(year, month):
        """Lấy tổng hợp thu chi - Tối ưu bằng cách truy vấn trực tiếp từ SQL"""
        try:
            summary = Transaction.get_summary_by_month(year, month)
            return {
                'year': year,
                'month': month,
                'income': summary.get('income', 0),
                'expense': summary.get('expense', 0),
                'profit': summary.get('income', 0) - summary.get('expense', 0)
            }
        except Exception as e:
            logger.error(f"Lỗi tính tổng hợp tháng: {e}")
            return {'income': 0, 'expense': 0, 'profit': 0}

    @staticmethod
    def get_total_income():
        return Transaction.get_total_income()

    @staticmethod
    def get_total_expense():
        return Transaction.get_total_expense()

    @staticmethod
    def get_categories():
        return Transaction.get_categories()