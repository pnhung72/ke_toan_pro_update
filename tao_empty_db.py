import sqlite3, sys
from pathlib import Path

src = Path('dist/ke_toan_data/ke_toan.db')
dst = Path('ke_toan_data/ke_toan_empty.db')

if not src.exists():
    print('[LOI] Khong tim thay dist/ke_toan_data/ke_toan.db')
    sys.exit(1)

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)
for line in src_conn.iterdump():
    if line.startswith('INSERT'):
        continue
    try:
        dst_conn.execute(line)
    except:
        pass
dst_conn.commit()
src_conn.close()
dst_conn.close()
print('[OK] Da tao ke_toan_empty.db thanh cong.')