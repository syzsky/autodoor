import time
import random
from typing import Optional


class KeyEventExecutor:
    """
    统一按键执行器类
    
    执行流程：按下 -> 等待(delay) -> 抬起
    delay_min/max 表示按键按住的时长范围（毫秒）
    """
    
    def __init__(self, input_controller, delay_min_var, delay_max_var, priority=0):
        self.input_controller = input_controller
        self.delay_min_var = delay_min_var
        self.delay_max_var = delay_max_var
        self.priority = priority
    
    def execute_keypress(self, key):
        delay_min = max(1, int(self.delay_min_var.get()))
        delay_max = max(delay_min, int(self.delay_max_var.get()))
        
        hold_delay = random.randint(delay_min, delay_max) / 1000
        
        self.input_controller.key_down(key, priority=self.priority)
        time.sleep(hold_delay)
        self.input_controller.key_up(key, priority=self.priority)


class BackgroundKeyEventExecutor:
    """
    后台按键执行器类
    
    用于后台监控模块，通过 QuickSwitchBackend 在目标窗口执行按键操作。
    支持在不切换前台窗口的情况下向目标窗口发送按键。
    """
    
    def __init__(self, quick_switch, delay_min: int, delay_max: int, priority: int = 0):
        """
        初始化后台按键执行器
        
        Args:
            quick_switch: QuickSwitchBackend 实例
            delay_min: 按键按下最小时长（毫秒）
            delay_max: 按键按下最大时长（毫秒）
            priority: 优先级
        """
        self.quick_switch = quick_switch
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.priority = priority
    
    def execute_keypress(self, key: str) -> tuple:
        """
        执行按键操作
        
        Args:
            key: 按键名称
        
        Returns:
            tuple: (success, message)
        """
        if not key:
            return (False, "未设置按键")
        
        delay_min = max(1, self.delay_min)
        delay_max = max(delay_min, self.delay_max)
        
        return self.quick_switch.press_key(key, delay_min, delay_max)
    
    @classmethod
    def create_from_group(cls, quick_switch, group: dict, priority: int = 0):
        """
        从组配置创建后台按键执行器
        
        Args:
            quick_switch: QuickSwitchBackend 实例
            group: 组配置字典
            priority: 优先级
        
        Returns:
            BackgroundKeyEventExecutor: 后台按键执行器实例
        """
        import tkinter as tk
        
        try:
            delay_min = int(group.get("delay_min", tk.StringVar(value="100")).get())
        except (ValueError, TypeError):
            delay_min = 100
        
        try:
            delay_max = int(group.get("delay_max", tk.StringVar(value="200")).get())
        except (ValueError, TypeError):
            delay_max = 200
        
        return cls(quick_switch, delay_min, delay_max, priority)
