import sqlite3
import pandas as pd
import re
import unicodedata
import os

def remove_accents(text):
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def clean_description(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = remove_accents(text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def prepare_training_data(db_path="ke_toan_data/ke_toan.db", output_csv="ai/data/training_data.csv"):
    if not os.path.exists(db_path):
        print(f"Lỗi: Không tìm thấy database tại {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    # Lấy dữ liệu từ bảng transactions, dùng cột category thay vì account_id
    query = "SELECT description, category FROM transactions WHERE description IS NOT NULL AND category IS NOT NULL"
    df = pd.read_sql_query(query, conn)
    print(f"Tổng số dòng thô: {len(df)}")
    
    # Làm sạch mô tả
    df['description'] = df['description'].apply(clean_description)
    df = df[df['description'].str.len() > 3]
    print(f"Sau khi lọc mô tả quá ngắn: {len(df)}")
    
    # Thống kê nhãn hiếm (dùng cột category)
    label_counts = df['category'].value_counts()
    rare = label_counts[label_counts < 10]
    if len(rare) > 0:
        print("Cảnh báo: các tài khoản (category) có ít hơn 10 mẫu:")
        print(rare.to_string())
    else:
        print("Tất cả tài khoản đều có >= 10 mẫu, tốt!")
    
    # Tạo thư mục output
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Lưu CSV
    df.to_csv(output_csv, index=False)
    print(f"Đã lưu tập huấn luyện vào {output_csv}")
    print(f"Số dòng cuối cùng: {len(df)}")
    
    conn.close()

if __name__ == "__main__":
    prepare_training_data()