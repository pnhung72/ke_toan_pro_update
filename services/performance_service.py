# -*- coding: utf-8 -*-
"""
PerformanceService - Theo doi hieu nang
"""

import time
import threading
from collections import deque
from datetime import datetime

class PerformanceService:
    """Theo doi hieu nang he thong"""
    
    def __init__(self, max_history=100):
        self.metrics = {
            "load_times": deque(maxlen=max_history),
            "query_times": deque(maxlen=max_history),
            "memory_usage": deque(maxlen=max_history),
        }
        self._monitoring = False
    
    def start_monitoring(self):
        """Bat dau theo doi"""
        self._monitoring = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
    
    def _monitor_loop(self):
        """Vong lap theo doi"""
        import psutil
        while self._monitoring:
            memory = psutil.virtual_memory()
            self.metrics["memory_usage"].append({
                "timestamp": datetime.now(),
                "percent": memory.percent,
                "used_mb": memory.used / 1024 / 1024
            })
            time.sleep(60)  # Theo doi moi phut
    
    def record_load_time(self, component, elapsed_ms):
        """Ghi lai thoi gian tai"""
        self.metrics["load_times"].append({
            "component": component,
            "elapsed_ms": elapsed_ms,
            "timestamp": datetime.now()
        })
    
    def record_query_time(self, query, elapsed_ms):
        """Ghi lai thoi gian query"""
        self.metrics["query_times"].append({
            "query": query[:50],
            "elapsed_ms": elapsed_ms,
            "timestamp": datetime.now()
        })
    
    def get_slow_queries(self, threshold_ms=500):
        """Lay cac query cham"""
        return [q for q in self.metrics["query_times"] if q["elapsed_ms"] > threshold_ms]
    
    def get_performance_report(self):
        """Lay bao cao hieu nang"""
        report = {
            "total_queries": len(self.metrics["query_times"]),
            "avg_query_time": 0,
            "max_query_time": 0,
            "total_loads": len(self.metrics["load_times"]),
            "avg_load_time": 0,
            "current_memory_percent": 0,
        }
        
        if self.metrics["query_times"]:
            times = [q["elapsed_ms"] for q in self.metrics["query_times"]]
            report["avg_query_time"] = sum(times) / len(times)
            report["max_query_time"] = max(times)
        
        if self.metrics["load_times"]:
            times = [l["elapsed_ms"] for l in self.metrics["load_times"]]
            report["avg_load_time"] = sum(times) / len(times)
        
        if self.metrics["memory_usage"]:
            report["current_memory_percent"] = self.metrics["memory_usage"][-1]["percent"]
        
        return report
    
    def stop_monitoring(self):
        """Dung theo doi"""
        self._monitoring = False