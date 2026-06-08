# -*- coding: utf-8 -*-
"""Tương thích ngược - Chuyển tiếp sang theme.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from theme import (
    FONTS, COLORS, SIZES,
    get_font, get_color, get_padding,
    apply_theme,
    create_label, create_button, create_entry, create_treeview
)

__all__ = [
    'FONTS', 'COLORS', 'SIZES',
    'get_font', 'get_color', 'get_padding',
    'apply_theme',
    'create_label', 'create_button', 'create_entry', 'create_treeview'
]

#print("✅ theme_manager.py đã sẵn sàng")
