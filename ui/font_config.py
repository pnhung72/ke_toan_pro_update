# -*- coding: utf-8 -*-
"""
CẤU HÌNH FONT CHỮ TẬP TRUNG CHO TOÀN BỘ ỨNG DỤNG
"""

from tkinter import font
import tkinter as tk
from tkinter import ttk
import logging

# === KÍCH THƯỚC FONT TOÀN CỤC (TĂNG LÊN) ===
FONT_SIZES = {
    'menu': 13,
    'tab': 13,
    'label': 13,
    'label_bold': (13, 'bold'),
    'entry': 13,
    'button': 13,
    'tree': 13,
    'tree_header': (13, 'bold'),
    'title': 18,
    'subtitle': 15,
    'status': 12,
}

FONT_FAMILY = "Segoe UI"

def setup_fonts():
    """Áp dụng font cho toàn bộ ứng dụng"""
    try:
        # Font mặc định
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(family=FONT_FAMILY, size=FONT_SIZES['label'])
        
        # Font menu
        menu_font = font.nametofont('TkMenuFont')
        menu_font.configure(family=FONT_FAMILY, size=FONT_SIZES['menu'])
        
        # Font text
        text_font = font.nametofont('TkTextFont')
        text_font.configure(family=FONT_FAMILY, size=FONT_SIZES['label'])
        
        # Cấu hình style
        configure_ttk_styles()
        
        logging.info(f'Đã cấu hình font: {FONT_FAMILY} size {FONT_SIZES["label"]}')
    except Exception as e:
        logging.error(f'Lỗi cấu hình font: {e}')

def configure_ttk_styles():
    """Cấu hình style cho ttk widgets"""
    style = ttk.Style()
    
    style.configure("Treeview", 
                    font=(FONT_FAMILY, FONT_SIZES['tree']), 
                    rowheight=FONT_SIZES['tree'] + 25)
    style.configure("Treeview.Heading", 
                    font=(FONT_FAMILY, FONT_SIZES['tree_header'][0], 'bold'))
    style.configure("TNotebook.Tab", 
                    font=(FONT_FAMILY, FONT_SIZES['tab']), 
                    padding=[20, 10])
    style.configure("TButton", 
                    font=(FONT_FAMILY, FONT_SIZES['button']))
    style.configure("TLabelframe.Label", 
                    font=(FONT_FAMILY, FONT_SIZES['label_bold'][0], 'bold'))
    style.configure("TLabel", 
                    font=(FONT_FAMILY, FONT_SIZES['label']))
    style.configure("TEntry", 
                    font=(FONT_FAMILY, FONT_SIZES['entry']))
    style.configure("TCombobox", 
                    font=(FONT_FAMILY, FONT_SIZES['entry']))

def get_font(size_key, bold=False):
    size = FONT_SIZES.get(size_key, 13)
    if isinstance(size, tuple):
        size, is_bold = size
        bold = bold or is_bold
    weight = "bold" if bold else "normal"
    return (FONT_FAMILY, size, weight)