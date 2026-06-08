# -*- coding: utf-8 -*-
"""
CacheService - Quan ly cache cho du lieu
"""

import time
from functools import lru_cache, wraps
from datetime import datetime, timedelta

class CacheService:
    """Dich vu cache du lieu"""
    
    def __init__(self, ttl_seconds=300):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, key):
        """Lay du lieu tu cache"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key, value):
        """Luu du lieu vao cache"""
        self._cache[key] = (value, time.time())
    
    def clear(self, key=None):
        """Xoa cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def invalidate_by_prefix(self, prefix):
        """Xoa cache theo prefix"""
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._cache[key]


# Decorator cho caching
def cached(ttl=300):
    """Decorator de cache ket qua ham"""
    def decorator(func):
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Tao key tu tham so
            key = f"{func.__name__}_{args}_{kwargs}"
            
            if key in cache:
                data, timestamp = cache[key]
                if time.time() - timestamp < ttl:
                    return data
            
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            return result
        
        return wrapper
    return decorator


# Cache cho cac ham thong dung
class DataCache:
    """Cache cho du lieu nghiep vu"""
    
    def __init__(self):
        self.revenue_cache = CacheService(ttl_seconds=60)  # Cache doanh thu 1 phut
        self.product_cache = CacheService(ttl_seconds=300)  # Cache san pham 5 phut
        self.customer_cache = CacheService(ttl_seconds=600)  # Cache khach hang 10 phut
    
    def get_revenue(self, period, force_refresh=False):
        """Lay doanh thu tu cache"""
        if force_refresh:
            self.revenue_cache.clear(period)
        return self.revenue_cache.get(period)
    
    def set_revenue(self, period, data):
        """Luu doanh thu vao cache"""
        self.revenue_cache.set(period, data)
    
    def clear_all(self):
        """Xoa toan bo cache"""
        self.revenue_cache.clear()
        self.product_cache.clear()
        self.customer_cache.clear()