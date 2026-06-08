import sqlite3
from datetime import datetime

db_path = r"D:\ke_toan_pro_v3\ke_toan_data\ke_toan.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Thử thêm mới
    cursor.execute('''
        INSERT INTO email_configurations (email_address, app_password, created_at)
        VALUES (?, ?, ?)
    ''', ('pnhungc3nvt@gmail.com', 'huxk kiul vely ngpc', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    print("✅ Đã thêm thành công!")
except sqlite3.IntegrityError:
    # Nếu email đã tồn tại, cập nhật mật khẩu
    cursor.execute('''
        UPDATE email_configurations
        SET app_password = ?, created_at = ?
        WHERE email_address = ?
    ''', ('huxk kiul vely ngpc', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'pnhungc3nvt@gmail.com'))
    conn.commit()
    print("✅ Email đã tồn tại, đã cập nhật mật khẩu mới!")
except Exception as e:
    print(f"❌ Lỗi: {e}")
finally:
    conn.close()