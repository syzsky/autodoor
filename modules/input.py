import time
import random


class KeyEventExecutor:
    """统一按键执行器类"""
    def __init__(self, input_controller, delay_min_var, delay_max_var):
        self.input_controller = input_controller
        self.delay_min_var = delay_min_var
        self.delay_max_var = delay_max_var
    
    def execute_keypress(self, key):
        delay_min = max(1, int(self.delay_min_var.get()))
        delay_max = max(delay_min, int(self.delay_max_var.get()))
        delay = random.randint(delay_min, delay_max) / 1000
        time.sleep(delay)
        self.input_controller.key_down(key)
        time.sleep(0.1)
        self.input_controller.key_up(key)
