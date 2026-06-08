# models/account.py
from .database import Database

class Account:
    @staticmethod
    def load_accounts():
        # Trả về danh sách tài khoản mặc định (nếu cần)
        return [
            {"Ma TK": "111", "Ten TK": "Tiền mặt", "Loai": "Tài sản"},
            {"Ma TK": "112", "Ten TK": "Tiền gửi ngân hàng", "Loai": "Tài sản"},
            {"Ma TK": "131", "Ten TK": "Phải thu khách hàng", "Loai": "Tài sản"},
            {"Ma TK": "156", "Ten TK": "Hàng hóa", "Loai": "Tài sản"},
            {"Ma TK": "211", "Ten TK": "TSCĐ hữu hình", "Loai": "Tài sản"},
            {"Ma TK": "331", "Ten TK": "Phải trả người bán", "Loai": "Nợ phải trả"},
            {"Ma TK": "411", "Ten TK": "Vốn đầu tư của CSH", "Loai": "Vốn chủ sở hữu"},
            {"Ma TK": "511", "Ten TK": "Doanh thu bán hàng", "Loai": "Doanh thu"},
            {"Ma TK": "632", "Ten TK": "Giá vốn hàng bán", "Loai": "Chi phí"},
            {"Ma TK": "642", "Ten TK": "Chi phí quản lý kinh doanh", "Loai": "Chi phí"},
        ]

    @staticmethod
    def get_balance(account_code):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(debit) - SUM(credit) FROM journal_entries WHERE account_code=?", (account_code,))
            result = cursor.fetchone()[0]
            return result if result else 0