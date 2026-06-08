import pandas as pd
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

def train_classifier(csv_path="ai/data/training_data.csv", model_output="ai/data/models/classifier.pkl"):
    if not os.path.exists(csv_path):
        print(f"Lỗi: Không tìm thấy file {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    print(f"Đọc được {len(df)} dòng")
    
    X = df['description']
    y = df['category']
    
    # Pipeline: TF-IDF + Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), min_df=1, max_df=0.9)),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    
    pipeline.fit(X, y)
    print("Huấn luyện hoàn tất")
    
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    joblib.dump(pipeline, model_output)
    print(f"Đã lưu model vào {model_output}")
    
    # Thử nghiệm
    test_text = "thu tien ban hang"
    pred = pipeline.predict([test_text])[0]
    proba = pipeline.predict_proba([test_text]).max()
    print(f"Thử nghiệm: '{test_text}' -> {pred} (độ tin cậy {proba:.2f})")

if __name__ == "__main__":
    train_classifier()