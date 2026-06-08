# run_test.py
import sys
import os

# Thêm thư mục hiện tại vào path
sys.path.insert(0, os.path.dirname(__file__))

from ui.transaction_tab import TransactionTab
from core.database.connection_pool import get_connection_pool
from pathlib import Path

print("=== KIỂM TRA TRANSACTION TAB ===")

# Khởi tạo database
data_dir = Path("ke_toan_data")
db_path = str(data_dir / "ke_toan.db")
pool = get_connection_pool(db_path)

# Kiểm tra dữ liệu
with pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM journal_entries")
    count = cursor.fetchone()[0]
    print(f"journal_entries: {count} dòng")
    
    cursor.execute("SELECT COUNT(*) FROM journal_details")
    print(f"journal_details: {cursor.fetchone()[0]} dòng")
    
    cursor.execute("SELECT COUNT(*) FROM transaction_metadata")
    print(f"transaction_metadata: {cursor.fetchone()[0]} dòng")

print("\n✅ Nếu thấy số dòng > 0, dữ liệu đã sẵn sàng!")
print("👉 Hãy build lại với lệnh sau:")
print("pyinstaller --onefile --windowed --name PhanMemKeToan --icon=icon.ico --add-data \"ui;ui\" --add-data \"models;models\" --add-data \"services;services\" --add-data \"utils;utils\" --add-data \"views;views\" --add-data \"reports;reports\" --add-data \"config.py;.\" --add-data \"data_config.py;.\" --add-data \"data_path.txt;.\" --add-data \"version.txt;.\" --add-data \"icon.ico;.\" --add-data \"ACB.jpeg;.\" main.py")