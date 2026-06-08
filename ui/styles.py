# -*- coding: utf-8 -*-
from tkinter import ttk

FONT_SIZES = {
    'title': 22,
    'heading': 18,
    'normal': 14,
    'small': 12,
    'button': 13,
    'tree': 13,
}
FONT_FAMILY = 'Segoe UI'

ICONS = {
    'home': '🏠', 'bank': '🏦', 'add': '➕', 'edit': '✏️', 'delete': '🗑️',
    'refresh': '🔄', 'save': '💾', 'print': '🖨️', 'export': '📎',
    'export_xml': '📄', 'help': '❓', 'info': 'ℹ️', 'warning': '⚠️',
    'success': '✅', 'error': '❌', 'upload': '📤', 'book': '📒',
    'notification': '📢', 'tax_return': '📋', 'product': '📦',
    'transaction': '💰', 'invoice': '📄', 'debt': '📊', 'report': '📈',
    'dashboard': '📊', 'about': '⭐', 'user_manager': '👥',
    'business_info': '🏠', 'tax_compliance': '⚖️', 'audit_log': '📜',
    'report_export': '📎', 'closing': '🔒', 'ledger': '📒',
    'tax_declaration': '📋', 'settings': '⚙️', 'search': '🔍',
    'backup': '💿', 'download': '📥',
}

def get_icon(name):
    return ICONS.get(name, '📌')

def get_font(size_name, bold=False):
    weight = 'bold' if bold else 'normal'
    return (FONT_FAMILY, FONT_SIZES.get(size_name, 14), weight)

# Bảng màu tươi sáng, hiện đại, tăng độ tương phản
COLORS = {
    'bg_root': '#F8F9FA',        # nền cửa sổ chính (sáng)
    'bg_notebook': '#E9ECEF',    # nền vùng tab (xám nhạt)
    'bg_card': '#FFFFFF',        # nền trắng cho nội dung
    'tab_normal': '#6C757D',     # tab chưa chọn (xám)
    'tab_selected': '#0D6EFD',   # tab được chọn (xanh dương nổi)
    'primary': '#0D6EFD',        # màu chính cho nút accent
    'success': '#198754',        # xanh lá
    'danger': '#DC3545',         # đỏ
    'warning': '#FFC107',        # vàng
    'info': '#0DCAF0',           # xanh dương nhạt
    'border_light': '#DEE2E6',   # màu viền nhạt
}

def apply_global_styles():
    style = ttk.Style()
    style.theme_use('clam')
    
    # ---------- Tab 3D nổi ----------
    style.configure('TNotebook', background=COLORS['bg_notebook'], borderwidth=0)
    style.configure('TNotebook.Tab',
                    font=get_font('normal', bold=True),
                    padding=[30, 12],
                    background=COLORS['tab_normal'],
                    foreground='white',
                    relief='raised',
                    borderwidth=2)
    style.map('TNotebook.Tab',
              background=[('selected', COLORS['tab_selected'])],
              relief=[('selected', 'sunken')])
    
    # ---------- Frame nội dung (thẻ) ----------
    style.configure('Card.TFrame', 
                    background=COLORS['bg_card'], 
                    relief='ridge', 
                    borderwidth=1)
    
    # ---------- Treeview (bảng) ----------
    style.configure('Treeview', 
                    font=get_font('tree'), 
                    rowheight=32,
                    background='white',
                    fieldbackground='white',
                    foreground='#212529',
                    borderwidth=1,
                    relief='solid')
    style.map('Treeview',
              background=[('selected', COLORS['primary'])],
              foreground=[('selected', 'white')])
    style.configure('Treeview.Heading', 
                    font=get_font('heading', True), 
                    background=COLORS['bg_notebook'],
                    foreground=COLORS['primary'],
                    relief='raised')
    
    # ---------- Các widget cơ bản ----------
    style.configure('TLabel', font=get_font('normal'), background=COLORS['bg_card'])
    style.configure('TButton', 
                    font=get_font('button'), 
                    padding=6, 
                    relief='raised',
                    background=COLORS['bg_card'])
    style.map('TButton', 
              relief=[('pressed', 'sunken')],
              background=[('active', '#E9ECEF')])
    
    # ---------- Nút chính (Accent) ----------
    style.configure('Accent.TButton',
                    font=get_font('button', bold=True),
                    background=COLORS['primary'],
                    foreground='white',
                    padding=8,
                    relief='raised')
    style.map('Accent.TButton',
              background=[('active', '#0B5ED7'), ('pressed', '#0A58CA')],
              relief=[('pressed', 'sunken')])
    
    # ---------- Nút xóa (Danger) ----------
    style.configure('Danger.TButton',
                    font=get_font('button', bold=True),
                    background=COLORS['danger'],
                    foreground='white',
                    padding=8,
                    relief='raised')
    style.map('Danger.TButton',
              background=[('active', '#B02A37'), ('pressed', '#A71D2A')],
              relief=[('pressed', 'sunken')])
    
    # ---------- Nút thành công (Success) ----------
    style.configure('Success.TButton',
                    font=get_font('button'),
                    background=COLORS['success'],
                    foreground='white',
                    padding=6,
                    relief='raised')
    style.map('Success.TButton',
              background=[('active', '#157347'), ('pressed', '#146C43')],
              relief=[('pressed', 'sunken')])
    
    # ---------- Entry và Combobox ----------
    style.configure('TEntry', 
                    fieldbackground='white', 
                    relief='solid', 
                    borderwidth=1,
                    foreground='#212529')
    style.map('TEntry',
              fieldbackground=[('focus', '#E6F0FF')],
              bordercolor=[('focus', COLORS['primary'])])
    
    style.configure('TCombobox', 
                    fieldbackground='white', 
                    relief='solid', 
                    borderwidth=1,
                    foreground='#212529')
    style.map('TCombobox',
              fieldbackground=[('focus', '#E6F0FF')],
              bordercolor=[('focus', COLORS['primary'])])
    
    # ---------- LabelFrame (khung có viền) ----------
    style.configure('TLabelframe', 
                    background=COLORS['bg_card'], 
                    relief='ridge', 
                    borderwidth=1)
    style.configure('TLabelframe.Label', 
                    font=get_font('heading', True), 
                    foreground=COLORS['primary'],
                    background=COLORS['bg_card'])
    
    # ---------- OptionMenu (nếu dùng) ----------
    style.configure('TMenubutton', 
                    font=get_font('normal'),
                    relief='raised',
                    borderwidth=1)
    
    # ---------- Progressbar ----------
    style.configure('TProgressbar', 
                    background=COLORS['primary'],
                    troughcolor=COLORS['bg_notebook'],
                    borderwidth=0)
    
    return style