import joblib
import os
import re
import unicodedata
from ai.engine.cache_manager import ClassifyCache

class Classifier:
    _instance = None
    _model = None
    _cache = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = ClassifyCache()
        return cls._instance

    def _remove_accents(self, text):
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join([c for c in nfkd if not unicodedata.combining(c)])

    def _clean_text(self, text):
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = self._remove_accents(text)
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def load_model(self, model_path="ai/data/models/classifier.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        self._model = joblib.load(model_path)
        return self._model

    def predict(self, description, top_k=3):
        # Kiểm tra cache trước
        cached = self._cache.get(description)
        if cached is not None:
            return cached[:top_k]
        
        if self._model is None:
            self.load_model()
        cleaned = self._clean_text(description)
        proba = self._model.predict_proba([cleaned])[0]
        classes = self._model.classes_
        top_indices = proba.argsort()[-top_k:][::-1]
        results = [(classes[i], proba[i]) for i in top_indices]
        
        # Lưu vào cache (full results)
        full_results = [(classes[i], proba[i]) for i in range(len(classes)) if proba[i] > 0]
        self._cache.set(description, full_results)
        return results

classifier = Classifier()