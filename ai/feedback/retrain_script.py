"""
retrain_script.py
Chạy khi có đủ feedback 'wrong_correction' (mặc định >=10).
Có thể gọi thủ công từ menu hoặc tự động.
"""
import sqlite3
import pandas as pd
import os
import sys
from pathlib import Path

# Thêm đường dẫn gốc để import module
sys.path.append(str(Path(__file__).parent.parent.parent))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

def collect_feedback_data(db_path="ke_toan_data/ke_toan.db"):
    """Lấy các giao dịch có ai_feedback = 'wrong_correction' và đã được người dùng sửa đúng"""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT tm.description, tm.category 
        FROM transaction_metadata tm
        WHERE tm.ai_feedback = 'wrong_correction'
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_original_training_data(csv_path="ai/data/training_data.csv"):
    """Lấy dữ liệu huấn luyện ban đầu"""
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame(columns=['description', 'category'])

def retrain_model(feedback_threshold=10):
    """
    - Nếu số lượng feedback mới >= threshold -> retrain
    - Huấn luyện pipeline (TF-IDF + LogisticRegression)
    - Lưu model mới, backup model cũ
    """
    # 1. Thu thập feedback mới
    feedback_df = collect_feedback_data()
    if len(feedback_df) < feedback_threshold:
        print(f"Chưa đủ feedback: {len(feedback_df)}/{feedback_threshold}. Bỏ qua retrain.")
        return False
    
    # 2. Lấy dữ liệu cũ
    old_df = get_original_training_data()
    
    # 3. Kết hợp
    combined = pd.concat([old_df, feedback_df], ignore_index=True).drop_duplicates()
    print(f"Tổng số mẫu huấn luyện mới: {len(combined)} (thêm {len(feedback_df)} feedback mới)")
    
    # 4. Huấn luyện pipeline
    X = combined['description']
    y = combined['category']
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), min_df=1, max_df=0.9)),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(X, y)
    
    # 5. Lưu model mới (có backup)
    model_path = "ai/data/models/classifier.pkl"
    backup_path = "ai/data/models/classifier_backup.pkl"
    if os.path.exists(model_path):
        import shutil
        shutil.copy(model_path, backup_path)
        print(f"Đã backup model cũ vào {backup_path}")
    
    joblib.dump(pipeline, model_path)
    print(f"Đã lưu model mới vào {model_path}")
    
    # 6. Cập nhật training_data.csv để lần sau dùng
    combined.to_csv("ai/data/training_data.csv", index=False)
    print("Đã cập nhật training_data.csv")
    
    # 7. Xoá cache phân loại để dùng model mới (tuỳ chọn)
    cache_file = "ai/data/cache/classify_cache.pkl"
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Đã xoá cache phân loại cũ")
    
    return True

if __name__ == "__main__":
    retrain_model(feedback_threshold=10)