from .database import Database


class JournalEntry:

    @staticmethod
    def create(date, description, entries):
        """entries: list of dict [{'account': code, 'debit': 0, 'credit': x}]"""
        if not entries:
            raise ValueError("Danh sách bút toán không được rỗng")

        total_debit = sum(e.get('debit', 0) for e in entries)
        total_credit = sum(e.get('credit', 0) for e in entries)
        if abs(total_debit - total_credit) > 0.001:
            raise ValueError(
                f"Bút toán không cân bằng Nợ/Có: "
                f"Nợ={total_debit:,.0f} | Có={total_credit:,.0f}"
            )

        with Database.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute("BEGIN")
                for e in entries:
                    cursor.execute('''
                        INSERT INTO journal_entries
                            (date, description, account_code, debit, credit)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (date, description, e['account'], e.get('debit', 0), e.get('credit', 0)))
                conn.commit()
                return True
            except Exception as ex:
                conn.rollback()
                raise RuntimeError(f"Lỗi khi lưu bút toán: {ex}")

    @staticmethod
    def get_by_account(account_code):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM journal_entries
                WHERE account_code = ?
                ORDER BY date, id
            ''', (account_code,))
            return cursor.fetchall()

    @staticmethod
    def get_by_account_period(account_code, from_date, to_date):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM journal_entries
                WHERE account_code = ? AND date BETWEEN ? AND ?
                ORDER BY date, id
            ''', (account_code, from_date, to_date))
            return cursor.fetchall()

    @staticmethod
    def get_balance_up_to(account_code, date):
        with Database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT SUM(debit) - SUM(credit) FROM journal_entries
                WHERE account_code = ? AND date <= ?
            ''', (account_code, date))
            result = cursor.fetchone()[0]
            return result if result else 0