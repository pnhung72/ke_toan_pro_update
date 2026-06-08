# -*- coding: utf-8 -*-
"""
LazyLoader - Tai du lieu khi can thiet
"""

import threading
from tkinter import ttk

class LazyLoader:
    """Tai du lieu bat dong bo"""
    
    def __init__(self, parent, load_func, on_complete=None):
        self.parent = parent
        self.load_func = load_func
        self.on_complete = on_complete
        self.is_loading = False
    
    def load_async(self):
        """Tai du lieu bat dong bo"""
        if self.is_loading:
            return
        
        self.is_loading = True
        thread = threading.Thread(target=self._load)
        thread.daemon = True
        thread.start()
    
    def _load(self):
        """Thread xu ly tai du lieu"""
        try:
            result = self.load_func()
            if self.on_complete:
                self.parent.after(0, lambda: self.on_complete(result))
        except Exception as e:
            if self.on_complete:
                self.parent.after(0, lambda: self.on_complete(None, error=str(e)))
        finally:
            self.is_loading = False


class LazyTab:
    """Mixin cho cac tab co lazy loading"""
    
    def __init__(self):
        self._loaded = False
        self._loading = False
    
    def on_tab_selected(self):
        """Tai du lieu khi tab duoc chon"""
        if not self._loaded and not self._loading:
            self._loading = True
            self.parent.after(100, self._load_data_async)
    
    def _load_data_async(self):
        """Tai du lieu bat dong bo"""
        try:
            self.load_data()
            self._loaded = True
        finally:
            self._loading = False
    
    def refresh(self):
        """Lam moi du lieu (reset loaded state)"""
        self._loaded = False
        self.on_tab_selected()