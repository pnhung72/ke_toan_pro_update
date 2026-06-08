import pandas as pd
import sqlite3
import numpy as np
from sklearn.ensemble import IsolationForest
import pickle
import os

class AnomalyDetector:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_transactions(self, db_path="ke_toan_data/ke_toan.db"):
        """Lấy các giao dịch có số tiền > 0 (dùng debit_amount và credit_amount)"""
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                jd.debit_amount,
                jd.credit_amount,
                jd.account_code,
                je.date
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
            WHERE (jd.debit_amount > 0 OR jd.credit_amount > 0)
            ORDER BY je.date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return pd.DataFrame()
        # Tạo cột amount: lấy debit_amount nếu >0, ngược lại lấy credit_amount
        df['amount'] = df.apply(lambda row: row['debit_amount'] if row['debit_amount'] > 0 else row['credit_amount'], axis=1)
        # Log transform
        df['amount_log'] = np.log1p(df['amount'])
        # Chỉ giữ cột amount_log và date
        df = df[['amount_log', 'date']]
        return df

    def train(self, contamination=0.05):
        X = self.load_transactions()
        if X.empty or len(X) < 30:
            print("Không đủ dữ liệu để huấn luyện phát hiện bất thường (cần ít nhất 30 giao dịch)")
            return None
        X_train = X[['amount_log']].copy()
        model = IsolationForest(contamination=contamination, random_state=42)
        model.fit(X_train)
        self._model = model
        os.makedirs("ai/data/models", exist_ok=True)
        with open("ai/data/models/anomaly.pkl", "wb") as f:
            pickle.dump(model, f)
        return model

    def predict(self, amount):
        if self._model is None:
            if os.path.exists("ai/data/models/anomaly.pkl"):
                with open("ai/data/models/anomaly.pkl", "rb") as f:
                    self._model = pickle.load(f)
            else:
                self.train()
        if self._model is None:
            return 1
        amount_log = np.log1p(amount)
        pred = self._model.predict([[amount_log]])[0]
        return pred

    def get_recent_anomalies(self, db_path="ke_toan_data/ke_toan.db", days=30):
        """Trả về DataFrame các giao dịch bất thường trong 'days' gần đây"""
        conn = sqlite3.connect(db_path)
        query = """
            SELECT 
                je.id,
                je.date,
                jd.debit_amount,
                jd.credit_amount,
                jd.account_code,
                je.description
            FROM journal_details jd
            JOIN journal_entries je ON jd.journal_entry_id = je.id
            WHERE (jd.debit_amount > 0 OR jd.credit_amount > 0)
              AND je.date >= date('now', ?)
            ORDER BY je.date DESC
        """
        df = pd.read_sql_query(query, conn, params=(f'-{days} days',))
        conn.close()
        if df.empty:
            return pd.DataFrame()
        df['amount'] = df.apply(lambda row: row['debit_amount'] if row['debit_amount'] > 0 else row['credit_amount'], axis=1)
        if self._model is None:
            self.train()
        if self._model is None:
            return pd.DataFrame()
        amounts_log = np.log1p(df['amount'].values).reshape(-1, 1)
        predictions = self._model.predict(amounts_log)
        df['is_anomaly'] = predictions
        anomalies = df[df['is_anomaly'] == -1].copy()
        return anomalies

anomaly_detector = AnomalyDetector()