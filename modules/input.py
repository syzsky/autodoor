import time
import random


class KeyEventExecutor:
    """统一按键执行器类"""
    def __init__(self, input_controller, delay_min_var, delay_max_var):
        """初始化按键执行器
        Args:
            input_controller: 输入控制器实例
            delay_min_var: 最小延迟变量
            delay_max_var: 最大延迟变量
        """
        self.input_controller = input_controller
        self.delay_min_var = delay_min_var
        self.delay_max_var = delay_max_var
    
    def execute_keypress(self, key):
        """执行按键操作
        Args:
            key: 按键名称
        """
        delay_min = max(1, self.delay_min_var.get())
        delay_max = max(delay_min, self.delay_max_var.get())
        delay = random.randint(delay_min, delay_max) / 1000
        time.sleep(delay)
        self.input_controller.key_down(key)
        time.sleep(0.1)
        self.input_controller.key_up(key)
