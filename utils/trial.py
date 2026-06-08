import os
import json
from datetime import datetime, timedelta
import sys

TRIAL_DAYS = 30
config_FOLDER = os.path.join(os.environ.get('APPDATA', ''), 'KeToanPro')
config_FILE = os.path.join(config_FOLDER, 'trial.json')

def _ensure_config_folder():
    if not os.path.exists(config_FOLDER):
        os.makedirs(config_FOLDER)

def is_admin():
    """Kiểm tra sự tồn tại của file admin.key trong thư mục chứa ứng dụng"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(__file__)
    admin_file = os.path.join(base_dir, 'admin.key')
    return os.path.exists(admin_file)

def get_install_date():
    _ensure_config_folder()
    try:
        with open(config_FILE, 'r') as f:
            data = json.load(f)
            return datetime.strptime(data['install_date'], '%Y-%m-%d')
    except Exception:
        now = datetime.now().strftime('%Y-%m-%d')
        with open(config_FILE, 'w') as f:
            json.dump({'install_date': now}, f)
        return datetime.now()

def is_trial_valid():
    if is_admin():
        return True
    install_date = get_install_date()
    return datetime.now() - install_date <= timedelta(days=TRIAL_DAYS)

def get_remaining_days():
    if is_admin():
        return -1
    install_date = get_install_date()
    remaining = TRIAL_DAYS - (datetime.now() - install_date).days
    return max(0, remaining)

def show_trial_warning(parent):
    if is_admin():
        return
    from tkinter import messagebox
    remaining = get_remaining_days()
    if remaining > 0:
        messagebox.showinfo("Dùng thử", f"Bạn còn {remaining} ngày dùng thử.\nHãy liên hệ để mua bản quyền.")
    else:
        messagebox.showwarning("Hết hạn dùng thử",
            "Bạn đã hết thời gian dùng thử.\n"
            "Vui lòng mua bản quyền để tiếp tục sử dụng các tính năng xuất Excel và in ấn.\n"
            "Liên hệ: [email/phone]")