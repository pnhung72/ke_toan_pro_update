from models.database import Database
from models.account import Account
from models.journal_entry import JournalEntry
from datetime import datetime

class ClosingService:
    @staticmethod
    def get_periods():
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounting_periods ORDER BY start_date DESC")
            return cursor.fetchall()

    @staticmethod
    def create_period(name, start_date, end_date):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounting_periods (period_name, start_date, end_date)
                VALUES (?, ?, ?)
            ''', (name, start_date, end_date))
            return cursor.lastrowid

    @staticmethod
    def close_period(period_id):
        # 1. Tính lợi nhuận trong kỳ
        from services.report_service import ReportService
        start_date, end_date = ClosingService._get_period_dates(period_id)
        # Lấy tổng thu và chi từ giao dịch trong kỳ
        total_income = ReportService.get_period_income(start_date, end_date)
        total_expense = ReportService.get_period_expense(start_date, end_date)
        profit = total_income - total_expense

        # 2. Tạo bút toán kết chuyển
        # Kết chuyển doanh thu
        JournalEntry.create(
            date=datetime.now().strftime("%d/%m/%Y"),
            description=f"Kết chuyển doanh thu kỳ {start_date} - {end_date}",
            entries=[
                {"account": "511", "debit": total_income, "credit": 0},
                {"account": "911", "debit": 0, "credit": total_income}
            ]
        )
        # Kết chuyển chi phí
        JournalEntry.create(
            date=datetime.now().strftime("%d/%m/%Y"),
            description=f"Kết chuyển chi phí kỳ {start_date} - {end_date}",
            entries=[
                {"account": "911", "debit": total_expense, "credit": 0},
                {"account": "632", "debit": 0, "credit": total_expense},
                # ... thêm các tài khoản chi phí khác nếu cần
            ]
        )
        # Kết chuyển lãi/lỗ
        if profit > 0:
            JournalEntry.create(
                date=datetime.now().strftime("%d/%m/%Y"),
                description=f"Kết chuyển lãi kỳ {start_date} - {end_date}",
                entries=[
                    {"account": "911", "debit": profit, "credit": 0},
                    {"account": "421", "debit": 0, "credit": profit}
                ]
            )
        else:
            JournalEntry.create(
                date=datetime.now().strftime("%d/%m/%Y"),
                description=f"Kết chuyển lỗ kỳ {start_date} - {end_date}",
                entries=[
                    {"account": "421", "debit": abs(profit), "credit": 0},
                    {"account": "911", "debit": 0, "credit": abs(profit)}
                ]
            )

        # 3. Cập nhật trạng thái kỳ đã khóa
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE accounting_periods SET is_closed = 1, closed_date = ?
                WHERE id = ?
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), period_id))

        return True

    @staticmethod
    def _get_period_dates(period_id):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT start_date, end_date FROM accounting_periods WHERE id=?", (period_id,))
            row = cursor.fetchone()
            return row['start_date'], row['end_date']