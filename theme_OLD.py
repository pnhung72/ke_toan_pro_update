# -*- coding: utf-8 -*-
"""
Cấu hình giao diện tập trung - Font chữ, màu sắc, style
CỠ CHỮ ĐÃ ĐƯỢC TĂNG LÊN ĐỂ DỄ ĐỌC
"""

from tkinter import ttk
import tkinter as tk
from tkinter import font

# ============ CẤU HÌNH FONT CHỮ - CỠ LỚN ============
FONTS = {
    'menu': ('Segoe UI', 13),
    'tab': ('Segoe UI', 13),
    'label': ('Segoe UI', 12),
    'label_bold': ('Segoe UI', 12, 'bold'),
    'entry': ('Segoe UI', 12),
    'button': ('Segoe UI', 12),
    'tree': ('Segoe UI', 12),
    'tree_header': ('Segoe UI', 12, 'bold'),
    'title': ('Segoe UI', 18, 'bold'),
    'subtitle': ('Segoe UI', 14, 'bold'),
    'status': ('Segoe UI', 11),
}

# ============ CẤU HÌNH MÀU SẮC ============
COLORS = {
    'primary': '#2196F3',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'danger': '#F44336',
    'info': '#00BCD4',
    'dark': '#333333',
    'light': '#F5F5F5',
    'white': '#FFFFFF',
}

# ============ CẤU HÌNH KÍCH THƯỚC ============
SIZES = {
    'tree_rowheight': 35,
    'entry_width': 35,
    'button_width': 18,
    'tree_height': 15,
    'padding': {
        'small': 8,
        'medium': 12,
        'large': 18,
    }
}

def apply_theme():
    """Áp dụng theme cho toàn bộ ứng dụng"""
    style = ttk.Style()
    
    try:
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(family='Segoe UI', size=12)
        menu_font = font.nametofont('TkMenuFont')
        menu_font.configure(family='Segoe UI', size=13)
        text_font = font.nametofont('TkTextFont')
        text_font.configure(family='Segoe UI', size=12)
    except:
        pass
    
    style.configure('TNotebook.Tab', font=FONTS['tab'], padding=[20, 12])
    style.configure('Treeview', font=FONTS['tree'], rowheight=SIZES['tree_rowheight'])
    style.configure('Treeview.Heading', font=FONTS['tree_header'])
    style.configure('TButton', font=FONTS['button'])
    style.configure('Accent.TButton', font=FONTS['button'], foreground='white', background=COLORS['primary'])
    style.configure('TLabelframe.Label', font=FONTS['label_bold'])
    style.configure('TEntry', font=FONTS['entry'])
    style.configure('TCombobox', font=FONTS['entry'])
    style.configure('TLabel', font=FONTS['label'])
    
    print("✅ Đã áp dụng theme - Cỡ chữ đã được tăng lên")

def get_font(size_key, bold=False):
    font_tuple = FONTS.get(size_key, ('Segoe UI', 12))
    if bold and len(font_tuple) == 2:
        return (font_tuple[0], font_tuple[1], 'bold')
    return font_tuple

def get_color(color_key):
    return COLORS.get(color_key, '#333333')

def get_padding(padding_key):
    return SIZES['padding'].get(padding_key, 12)

def create_label(parent, text, bold=False, color=None, **kwargs):
    label = ttk.Label(parent, text=text, **kwargs)
    if bold:
        label.configure(font=get_font('label', bold=True))
    if color:
        label.configure(foreground=color)
    return label

def create_button(parent, text, command, width=None, accent=False, **kwargs):
    if width is None:
        width = SIZES['button_width']
    style = 'Accent.TButton' if accent else 'TButton'
    return ttk.Button(parent, text=text, command=command, width=width, style=style, **kwargs)

def create_entry(parent, width=None, **kwargs):
    if width is None:
        width = SIZES['entry_width']
    return ttk.Entry(parent, width=width, **kwargs)

def create_treeview(parent, columns, col_widths, anchors, height=None, **kwargs):
    if height is None:
        height = SIZES['tree_height']
    tree = ttk.Treeview(parent, columns=columns, show='headings', height=height, **kwargs)
    for idx, col in enumerate(columns):
        tree.heading(col, text=col)
        anchor = anchors[idx] if idx < len(anchors) else 'w'
        width = col_widths[idx] if idx < len(col_widths) else 120
        tree.column(col, width=width, anchor=anchor)
    return tree

if __name__ == "__main__":
    apply_theme()
