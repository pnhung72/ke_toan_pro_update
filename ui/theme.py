# -*- coding: utf-8 -*-
"""
CẤU HÌNH GIAO DIỆN TẬP TRUNG
- TRÁNH LỖI "Too early to use font" bằng cách chỉ tạo font khi cần.
- KHÔNG CÓ root = tk.Tk() ở đây.
"""

import tkinter as tk
from tkinter import ttk, font
import logging

# ==================== BIẾN TOÀN CỤC ====================
DEFAULT_FONT_FAMILY = "Segoe UI"
DEFAULT_FONT_SIZE = 9

# Cache cho các font (chỉ khởi tạo một lần khi cần)
_cached_fonts = None

# ==================== HÀM TẠO FONT (TUẦN TỰ, AN TOÀN) ====================
def make_font(weight="normal", size=None):
    """Trả về tuple (family, size, weight) – an toàn dùng mọi lúc."""
    sz = size if size is not None else DEFAULT_FONT_SIZE
    if weight == "bold":
        return (DEFAULT_FONT_FAMILY, sz, "bold")
    return (DEFAULT_FONT_FAMILY, sz)

def get_fonts():
    """Lazy loading: chỉ tạo dict font khi lần đầu được gọi."""
    global _cached_fonts
    if _cached_fonts is None:
        _cached_fonts = {
            'menu': make_font(),
            'tab': make_font(size=8),
            'label': make_font(),
            'label_bold': make_font("bold"),
            'entry': make_font(),
            'button': make_font(),
            'tree': make_font(),
            'tree_header': make_font("bold"),
            'title': make_font("bold", size=14),
            'subtitle': make_font("bold", size=12),
            'status': make_font(size=9),
            'icon': make_font(size=12),
            'large_icon': make_font(size=14),
        }
    return _cached_fonts

# ==================== Lazy Dict để tương thích code cũ ====================
class _LazyFontDict:
    def __getitem__(self, key):
        return get_fonts()[key]
    def get(self, key, default=None):
        return get_fonts().get(key, default)
    def __contains__(self, key):
        return key in get_fonts()
    def items(self):
        return get_fonts().items()
    def keys(self):
        return get_fonts().keys()
    def values(self):
        return get_fonts().values()

FONTS = _LazyFontDict()

# ==================== MÀU SẮC & KÍCH THƯỚC ====================
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

SIZES = {
    'tree_rowheight': 24,
    'tree_width': {
        'id': 50, 'name': 200, 'phone': 120, 'address': 200,
        'tax': 120, 'product': 180, 'quantity': 80, 'price': 120,
        'total': 140, 'paid': 120, 'remaining': 120, 'payment': 100, 'date': 120,
    },
    'padding': {'small': 5, 'medium': 10, 'large': 15},
    'entry_width': 30,
    'button_width': 15,
    'tree_height': 12,
}

# ==================== HÀM LẤY GIÁ TRỊ ====================
def get_font(key, bold=False):
    f = FONTS.get(key, make_font())
    if bold and len(f) == 2:
        return (f[0], f[1], 'bold')
    return f

def get_color(key):
    return COLORS.get(key, '#333333')

def get_padding(key):
    return SIZES['padding'].get(key, 10)

# ==================== CẬP NHẬT THEME ĐỘNG ====================
def apply_theme_to_style():
    """Áp dụng style cho ttk với cấu trúc tạo chiều sâu (Card UI)"""
    style = ttk.Style()
    
    # 1. Cấu trúc nền chung (Light Gray cho background, White cho nội dung)
    style.configure('.', background='#EAEAEA', foreground='#333333')
    
    # 2. Notebook và Tab
    style.configure('TNotebook', background='#EAEAEA', borderwidth=0)
    style.configure('TNotebook.Tab', font=FONTS['tab'], padding=[10, 6], 
                    background='#D1D1D1', foreground='#333333')
    style.map('TNotebook.Tab', background=[('selected', '#FFFFFF')], foreground=[('selected', COLORS['primary'])])
    
    # 3. Treeview (Danh sách)
    style.configure('Treeview', font=FONTS['tree'], rowheight=26, 
                    background='white', fieldbackground='white', borderwidth=1)
    style.configure('Treeview.Heading', font=FONTS['tree_header'], 
                    background='#E0E0E0', foreground='#333333', relief='flat')
    
    # 4. Buttons
    style.configure('TButton', font=FONTS['button'], background='#FFFFFF', borderwidth=1)
    style.configure('Accent.TButton', font=FONTS['button'], foreground='white', background=COLORS['primary'])
    style.configure('Primary.TButton', font=FONTS['button'], background=COLORS['primary'], foreground='white')
    style.configure('Success.TButton', font=FONTS['button'], background=COLORS['success'], foreground='white')
    style.configure('Danger.TButton', font=FONTS['button'], background=COLORS['danger'], foreground='white')
    
    # 5. Khung chứa (Card/Frame) - TẠO CHIỀU SÂU
    # Các LabelFrame sẽ có màu trắng để nổi bật trên nền xám nhạt của cửa sổ
    style.configure('TLabelframe', background='#FFFFFF', borderwidth=1, relief='solid')
    style.configure('TLabelframe.Label', font=FONTS['label_bold'], background='#FFFFFF', foreground=COLORS['primary'])
    
    # 6. Inputs (Entry/Combobox)
    style.configure('TEntry', font=FONTS['entry'], fieldbackground='white', borderwidth=1)
    style.configure('TCombobox', font=FONTS['entry'], fieldbackground='white', borderwidth=1)
    
    # 7. Labels
    style.configure('TLabel', font=FONTS['label'], background='#EAEAEA')

def apply_theme_to_tk_widgets(widget):
    """Đệ quy gán font cho widget tk thuần."""
    try:
        if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Text, tk.Listbox, tk.Menu)):
            current_font = widget.cget('font')
            if isinstance(current_font, str) and current_font in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
                widget.configure(font=make_font())
            elif current_font == ('Segoe UI', 13) or current_font == ('Segoe UI', 13, 'bold'):
                widget.configure(font=make_font())
    except Exception:
        pass
    for child in widget.winfo_children():
        apply_theme_to_tk_widgets(child)

def apply_theme_to_all_windows():
    """Áp dụng theme lên tất cả cửa sổ – kiểm tra root tồn tại."""
    try:
        default_font = font.nametofont('TkDefaultFont')
        default_font.configure(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE)
        menu_font = font.nametofont('TkMenuFont')
        menu_font.configure(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE)
        text_font = font.nametofont('TkTextFont')
        text_font.configure(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE)
    except Exception:
        pass
    apply_theme_to_style()
    if tk._default_root:
        apply_theme_to_tk_widgets(tk._default_root)

# ==================== HÀM TIỆN ÍCH TẠO WIDGET ====================
def create_label(parent, text, bold=False, color=None, **kwargs):
    lbl_font = make_font("bold" if bold else "normal")
    label = tk.Label(parent, text=text, font=lbl_font, **kwargs)
    if color:
        label.config(fg=color)
    return label

def create_button(parent, text, command, width=None, accent=False, **kwargs):
    if width is None:
        width = SIZES.get('button_width', 15)
    style = 'Accent.TButton' if accent else 'TButton'
    return ttk.Button(parent, text=text, command=command, width=width, style=style, **kwargs)

def create_entry(parent, width=None, **kwargs):
    if width is None:
        width = SIZES.get('entry_width', 30)
    return ttk.Entry(parent, width=width, **kwargs)

def create_treeview(parent, columns, col_widths, anchors, height=None, **kwargs):
    if height is None:
        height = SIZES.get('tree_height', 12)
    tree = ttk.Treeview(parent, columns=columns, show='headings', height=height, **kwargs)
    for idx, col in enumerate(columns):
        tree.heading(col, text=col)
        anchor = anchors[idx] if idx < len(anchors) else 'w'
        width = col_widths[idx] if idx < len(col_widths) else 100
        tree.column(col, width=width, anchor=anchor)
    return tree

def create_combobox(parent, values, width=None, **kwargs):
    if width is None:
        width = SIZES.get('entry_width', 30)
    return ttk.Combobox(parent, values=values, width=width, **kwargs)

def create_frame(parent, padding=None, **kwargs):
    if padding is None:
        padding = get_padding('medium')
    return ttk.Frame(parent, padding=padding, **kwargs)

def set_global_font(family=None, size=None, apply_now=True):
    global DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, _cached_fonts
    if family:
        DEFAULT_FONT_FAMILY = family
    if size:
        DEFAULT_FONT_SIZE = size
    _cached_fonts = None   # Reset cache, fonts sẽ được tạo lại khi cần
    if apply_now:
        apply_theme_to_all_windows()
    logging.info(f"Đã đổi font toàn cục thành {DEFAULT_FONT_FAMILY} size {DEFAULT_FONT_SIZE}")

def apply_theme():
    apply_theme_to_all_windows()

def print_theme_info():
    print("=" * 40)
    print("THÔNG TIN THEME HIỆN TẠI")
    print("=" * 40)
    print(f"Font: {DEFAULT_FONT_FAMILY}")
    print(f"Cỡ chữ: {DEFAULT_FONT_SIZE}")
    print(f"Màu chính: {COLORS['primary']}")
    print("=" * 40)

if __name__ == "__main__":
    print_theme_info()
    root = tk.Tk()
    root.title("Test Theme")
    create_label(root, "Đây là label dùng font toàn cục", bold=True).pack(pady=5)
    create_button(root, "Nút bấm", lambda: None).pack(pady=5)
    apply_theme()
    root.mainloop()