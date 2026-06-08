# create_license.py
import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta
import sys

SECRET_KEY = b'KeToanPro_2026_Secret_Key_DoNotShare'  # Đổi thành key bí mật của bạn

def get_machine_id():
    print("\n--- TAO LICENSE KEY CHO KHACH HANG ---")
    machine_id = input("Nhap ma may (machine ID) khach hang gui: ").strip()
    if not machine_id:
        print("Loi: Ma may khong duoc de trong")
        sys.exit(1)
    return machine_id

def select_package():
    print("\nChon goi san pham:")
    print("1. Goi Co ban (500.000 VND)")
    print("2. Goi Pro (800.000 VND)")
    print("3. Goi Doanh nghiep (1.000.000 VND)")
    choice = input("Nhap so (1-3): ").strip()
    packages = {
        '1': {'id': 'basic', 'name': 'Goi Co ban', 'features': ['basic']},
        '2': {'id': 'pro', 'name': 'Goi Pro', 'features': ['basic', 'dashboard', 'advanced_report']},
        '3': {'id': 'enterprise', 'name': 'Goi Doanh nghiep', 'features': ['basic', 'dashboard', 'advanced_report', 'multi_user', 'audit_log']}
    }
    return packages.get(choice, packages['1'])

def get_customer_info():
    print("\nNhap thong tin khach hang:")
    name = input("Ho ten: ").strip()
    email = input("Email: ").strip()
    phone = input("So dien thoai: ").strip()
    return {'name': name, 'email': email, 'phone': phone}

def get_expiry_date():
    print("\nThoi han license:")
    print("1. Vinh vien")
    print("2. 1 nam")
    print("3. 6 thang")
    choice = input("Nhap so (1-3): ").strip()
    if choice == '2':
        return (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
    elif choice == '3':
        return (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d')
    else:
        return None

def generate_license(machine_id, package, customer, expiry):
    license_data = {
        'machine_id': machine_id,
        'package': package['id'],
        'package_name': package['name'],
        'customer': customer,
        'issued_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'expiry_date': expiry,
        'features': package['features']
    }
    data_str = json.dumps(license_data, sort_keys=True)
    signature = hmac.new(SECRET_KEY, data_str.encode(), hashlib.sha256).hexdigest()
    license_data['signature'] = signature
    return license_data

def save_license(license_data, output_file='license.key'):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(license_data, f, indent=4, ensure_ascii=False)
    print(f"\nDa tao file license: {os.path.abspath(output_file)}")
    log_file = 'license_log.txt'
    with open(log_file, 'a', encoding='utf-8') as log:
        log.write(f"{datetime.now().isoformat()} | Machine: {license_data['machine_id']} | Package: {license_data['package_name']} | Customer: {license_data['customer']['name']} | Expiry: {license_data['expiry_date']}\n")
    print(f"Da ghi log vao: {log_file}")

def main():
    machine_id = get_machine_id()
    package = select_package()
    customer = get_customer_info()
    expiry = get_expiry_date()
    license_data = generate_license(machine_id, package, customer, expiry)
    save_license(license_data)
    print("\nHoan tat. Gui file license.key cho khach hang.")

if __name__ == '__main__':
    main()