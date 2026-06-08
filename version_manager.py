import json
import os
from datetime import datetime

VERSION_FILE = "version.json"
VERSION_TXT = "version.txt"
PROJECT_INFO = "PROJECT_INFO.txt"

def update_version(version):
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    version_data = {
        "version": version,
        "release_date": datetime.now().strftime('%d/%m/%Y'),
        "last_update": timestamp,
        "author": "Phan Ngoc Hung",
        "email": "pnhungc3nvt@gmail.com",
        "zalo": "0982493474"
    }
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, ensure_ascii=False, indent=4)
    with open(VERSION_TXT, 'w', encoding='utf-8') as f:
        f.write(version)
    print(f"Da cap nhat phien ban {version}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        update_version(sys.argv[1])
