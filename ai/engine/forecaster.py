import pandas as pd
import sqlite3
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import pickle
import os

class CashFlowForecaster:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_data(self, db_path="ke_toan_data/ke_toan.db"):
        conn = sqlite3.connect(db_path)
        # Lấy doanh thu thuần theo ngày (tài khoản 511)
        query = """
            SELECT je.date, SUM(jd.credit_amount) as revenue
            FROM journal_entries je
            JOIN journal_details jd ON je.id = jd.journal_entry_id
            WHERE jd.account_code LIKE '5%' 
              AND je.date >= date('now', '-180 days')
            GROUP BY je.date
            ORDER BY je.date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            # Trả về DataFrame rỗng với cột date, revenue
            return pd.DataFrame(columns=['date', 'revenue'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').asfreq('D').fillna(0)
        return df

    def train(self, data=None):
        if data is None:
            data = self.load_data()
        if data.empty or len(data) < 14:
            print("Không đủ dữ liệu để huấn luyện dự báo (cần ít nhất 14 ngày)")
            return None
        model = ExponentialSmoothing(data['revenue'], trend='add', seasonal='add', seasonal_periods=7)
        fitted = model.fit()
        self._model = fitted
        os.makedirs("ai/data/models", exist_ok=True)
        with open("ai/data/models/forecaster.pkl", "wb") as f:
            pickle.dump(fitted, f)
        return fitted

    def forecast(self, steps=30):
        if self._model is None:
            if os.path.exists("ai/data/models/forecaster.pkl"):
                with open("ai/data/models/forecaster.pkl", "rb") as f:
                    self._model = pickle.load(f)
            else:
                self.train()
        if self._model is None:
            return pd.Series()
        pred = self._model.forecast(steps)
        return pred

forecaster = CashFlowForecaster()