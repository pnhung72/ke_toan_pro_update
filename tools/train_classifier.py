import pandas as pd
import fasttext
import os

def train_classifier(csv_path="ai/data/training_data.csv", model_output="ai/data/models/classifier.bin"):
    if not os.path.exists(csv_path):
        print(f"Lỗi: Không tìm thấy file {csv_path}")
        return
    
    # Đọc dữ liệu
    df = pd.read_csv(csv_path)
    print(f"Đọc được {len(df)} dòng")
    
    # Chuyển sang định dạng FastText: __label__category description
    with open("ai/data/training_data.fasttext", "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            label = row['category'].replace(' ', '_')  # thay khoảng trắng để tránh lỗi
            text = row['description']
            f.write(f"__label__{label} {text}\n")
    
    # Huấn luyện
    model = fasttext.train_supervised(
        input="ai/data/training_data.fasttext",
        lr=0.5,          # learning rate
        epoch=25,        # số lần lặp
        wordNgrams=2,    # n-grams
        dim=100,         # vector dimension
        loss='softmax',
        minCount=1       # cho phép từ chỉ xuất hiện 1 lần (vì dữ liệu ít)
    )
    
    # Lưu model
    os.makedirs(os.path.dirname(model_output), exist_ok=True)
    model.save_model(model_output)
    print(f"Đã lưu model vào {model_output}")
    
    # Kiểm tra nhanh
    test_text = "thu tien ban hang"
    labels, probs = model.predict(test_text, k=3)
    print(f"Thử nghiệm: '{test_text}' -> {labels}, {probs}")

if __name__ == "__main__":
    train_classifier()