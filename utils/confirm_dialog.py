# -*- coding: utf-8 -*-
"""
Confirm Dialog - Hộp thoại xác nhận thống nhất
"""

import tkinter as tk
from tkinter import ttk, messagebox
from theme import get_font


def confirm_delete(parent, item_type, item_id, item_name, extra_info=""):
    """
    Hộp thoại xác nhận xóa thống nhất
    
    Args:
        parent: Widget cha
        item_type: Loại đối tượng (VD: "giao dịch", "hóa đơn", "khách hàng")
        item_id: Mã đối tượng
        item_name: Tên đối tượng
        extra_info: Thông tin bổ sung
    
    Returns:
        bool: True nếu người dùng xác nhận xóa
    """
    # Xây dựng nội dung thông báo
    messages = {
        "transaction": {
            "title": "Xác nhận xóa giao dịch",
            "msg": f"Bạn có chắc chắn muốn xóa giao dịch?\n\n"
                   f"📋 Mã: #{item_id}\n"
                   f"📝 Mô tả: {item_name}\n"
                   f"{extra_info}\n"
                   f"⚠️ Hành động này KHÔNG THỂ hoàn tác!"
        },
        "invoice": {
            "title": "Xác nhận xóa hóa đơn",
            "msg": f"Bạn có chắc chắn muốn xóa hóa đơn?\n\n"
                   f"🧾 Số: #{item_id}\n"
                   f"👤 Khách hàng: {item_name}\n"
                   f"{extra_info}\n"
                   f"⚠️ Hành động này KHÔNG THỂ hoàn tác!"
        },
        "customer": {
            "title": "Xác nhận xóa khách hàng",
            "msg": f"Bạn có chắc chắn muốn xóa khách hàng?\n\n"
                   f"👤 Tên: {item_name}\n"
                   f"📋 Mã: #{item_id}\n"
                   f"{extra_info}\n"
                   f"⚠️ Hành động này KHÔNG THỂ hoàn tác!"
        },
        "product": {
            "title": "Xác nhận xóa sản phẩm",
            "msg": f"Bạn có chắc chắn muốn xóa sản phẩm?\n\n"
                   f"📦 Tên: {item_name}\n"
                   f"📋 Mã: #{item_id}\n"
                   f"{extra_info}\n"
                   f"⚠️ Hành động này KHÔNG THỂ hoàn tác!"
        }
    }
    
    info = messages.get(item_type, messages["transaction"])
    
    # Hộp thoại xác nhận lần 1
    confirm = messagebox.askyesno(
        info["title"],
        info["msg"],
        icon='warning',
        parent=parent
    )
    
    if not confirm:
        return False
    
    # Xác nhận lần 2 (an toàn hơn)
    confirm2 = messagebox.askyesno(
        "Xác nhận lần cuối",
        f"❌ Bạn có chắc chắn muốn XÓA VĨNH VIỄN {item_type} #{item_id}?\n\nHành động này không thể phục hồi!",
        icon='warning',
        parent=parent
    )
    
    return confirm2


def confirm_action(parent, title, message, icon='warning'):
    """
    Hộp thoại xác nhận hành động chung
    
    Args:
        parent: Widget cha
        title: Tiêu đề hộp thoại
        message: Nội dung thông báo
        icon: Loại icon ('warning', 'info', 'error', 'question')
    
    Returns:
        bool: True nếu người dùng xác nhận
    """
    icon_map = {
        'warning': 'warning',
        'info': 'info',
        'error': 'error',
        'question': 'question'
    }
    
    return messagebox.askyesno(
        title,
        message,
        icon=icon_map.get(icon, 'warning'),
        parent=parent
    )