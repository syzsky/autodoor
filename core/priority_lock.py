import threading
import time
import heapq
from typing import Optional, Tuple


class PriorityLock:
    """
    优先级锁实现
    
    确保高优先级的请求优先获取锁。
    优先级数值越大，优先级越高。
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._waiters = []
        self._sequence = 0
        self._locked = False
    
    def acquire(self, priority: int = 0):
        """获取锁，返回上下文管理器"""
        return _PriorityLockContext(self, priority)
    
    def _acquire(self, priority: int) -> None:
        """内部获取锁方法"""
        with self._lock:
            if not self._locked and not self._waiters:
                self._locked = True
                return
            
            self._sequence += 1
            event = threading.Event()
            heapq.heappush(self._waiters, (-priority, self._sequence, event))
        
        event.wait()
    
    def _release(self) -> None:
        """内部释放锁方法"""
        with self._lock:
            if not self._waiters:
                self._locked = False
                return
            
            _, _, event = heapq.heappop(self._waiters)
            event.set()
    
    def locked(self) -> bool:
        """检查锁是否被持有"""
        return self._locked


class _PriorityLockContext:
    """优先级锁上下文管理器"""
    
    def __init__(self, lock: PriorityLock, priority: int):
        self._lock = lock
        self._priority = priority
    
    def __enter__(self):
        self._lock._acquire(self._priority)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock._release()
        return False


MODULE_PRIORITIES = {
    'number': 5,
    'timed': 4,
    'ocr': 3,
    'color': 2,
    'script': 1,
}


def get_module_priority(module_name: str) -> int:
    """获取模块的默认优先级"""
    return MODULE_PRIORITIES.get(module_name, 0)
