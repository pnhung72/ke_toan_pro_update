import pickle
import os
from difflib import SequenceMatcher

class ClassifyCache:
    def __init__(self, cache_file="ai/data/cache/classify_cache.pkl"):
        self.cache_file = cache_file
        self.cache = {}
        self.load()
    
    def load(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except:
                self.cache = {}
    
    def save(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def _normalize(self, text):
        return text.strip().lower()
    
    def get(self, description):
        """Tìm kiếm chính xác hoặc gần đúng"""
        desc_norm = self._normalize(description)
        # Exact match
        if desc_norm in self.cache:
            return self.cache[desc_norm]
        # Fuzzy match (có thể bỏ qua nếu muốn đơn giản)
        for key, value in self.cache.items():
            ratio = SequenceMatcher(None, desc_norm, key).ratio()
            if ratio > 0.85:
                return value
        return None
    
    def set(self, description, suggestions):
        desc_norm = self._normalize(description)
        self.cache[desc_norm] = suggestions
        self.save()