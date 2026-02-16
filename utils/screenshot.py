import threading
import time
from PIL import Image, ImageGrab
from core.priority_lock import PriorityLock, get_module_priority


class ScreenshotManager:
    """
    全局截图管理器，实现截图资源共享
    
    使用优先级锁确保高优先级模块优先获取截图资源。
    优先级顺序：Number(5) > Timed(4) > OCR(3) > Color(2) > Script(1)
    """
    
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
        self.screenshot_lock = PriorityLock()
    
    def get_full_screenshot(self, priority: int = 0):
        """
        获取全屏截图（带缓存和优先级）
        
        Args:
            priority: 优先级，数值越大优先级越高
        
        Returns:
            PIL.Image: 截图副本，失败返回 None
        """
        with self.screenshot_lock.acquire(priority):
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
    
    def get_region_screenshot(self, region, priority: int = 0):
        """
        获取区域截图（带缓存和优先级）
        
        Args:
            region: 区域坐标 (x1, y1, x2, y2)
            priority: 优先级
        
        Returns:
            PIL.Image: 区域截图，失败返回 None
        """
        if not region:
            return None
        
        full_screenshot = self.get_full_screenshot(priority)
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
        with self.screenshot_lock.acquire(10):
            self.last_full_screenshot = None
            self.last_time = 0
    
    def set_cache_duration(self, duration):
        """设置缓存持续时间"""
        self.cache_duration = duration
