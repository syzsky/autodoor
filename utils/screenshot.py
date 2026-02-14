import threading
import time
from PIL import Image, ImageGrab


class ScreenshotManager:
    """全局截图管理器，实现截图资源共享"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, cache_duration=0.1):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        self.last_full_screenshot = None
        self.last_time = 0
        self.cache_duration = cache_duration
        self.screenshot_lock = threading.Lock()
    
    def get_full_screenshot(self):
        """获取全屏截图（带缓存）"""
        with self.screenshot_lock:
            current_time = time.time()
            
            if (self.last_full_screenshot is not None and 
                current_time - self.last_time < self.cache_duration):
                return self.last_full_screenshot.copy()
            
            try:
                self.last_full_screenshot = ImageGrab.grab(all_screens=True)
                self.last_time = current_time
                return self.last_full_screenshot.copy()
            except Exception:
                return None
    
    def get_region_screenshot(self, region):
        """获取区域截图（带缓存）"""
        if not region:
            return None
        
        full_screenshot = self.get_full_screenshot()
        if full_screenshot is None:
            return None
        
        try:
            x1, y1, x2, y2 = region
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            return full_screenshot.crop((left, top, right, bottom))
        except Exception:
            return None
    
    def clear_cache(self):
        """清除缓存"""
        with self.screenshot_lock:
            self.last_full_screenshot = None
            self.last_time = 0
    
    def set_cache_duration(self, duration):
        """设置缓存持续时间"""
        self.cache_duration = duration
