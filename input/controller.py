import pyautogui
import threading
import time

class InputController:
    """输入控制器类，提供通用的按键和鼠标操作方法"""
    
    def __init__(self, app=None):
        self.app = app
        self.core_graphics_available = False
        self.key_lock = threading.Lock()
        self.mouse_lock = threading.Lock()
        if self.app:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("InputController初始化完成，使用PyAutoGUI执行所有输入操作")
            else:
                print("InputController初始化完成，使用PyAutoGUI执行所有输入操作")
    
    @staticmethod
    def handle_permission_errors(func):
        """统一处理权限相关错误"""
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if self.app and ("accessibility" in error_msg or "permission" in error_msg):
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message("❌ 辅助功能权限缺失，请授权后重试")
                    else:
                        print("❌ 辅助功能权限缺失，请授权后重试")
                    if hasattr(self.app, 'root') and hasattr(self.app, '_guide_accessibility_setup'):
                        self.app.root.after(0, self.app._guide_accessibility_setup)
                elif self.app:
                    if hasattr(self.app, 'logging_manager'):
                        self.app.logging_manager.log_message(f"❌ 操作错误: {e}")
                    else:
                        print(f"❌ 操作错误: {e}")
                raise
        return wrapper
    
    @handle_permission_errors
    def press_key(self, key, delay=0, module_info=None):
        with self.key_lock:
            try:
                if delay > 0:
                    time.sleep(delay)
                
                pyautogui.press(key.lower(), interval=delay)
                if self.app:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行按键: {key}")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            except pyautogui.ImageNotFoundException:
                if self.app:
                    self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
                if hasattr(self, 'fallback_keys') and key in self.fallback_keys:
                    if self.app:
                        self.app.logging_manager.log_message(f"  → 尝试备用按键: {self.fallback_keys[key]}")
                    try:
                        pyautogui.press(self.fallback_keys[key].lower(), interval=delay)
                        if self.app:
                            self.app.logging_manager.log_message(f"执行: 按下备用按键 {self.fallback_keys[key]}")
                    except Exception as e:
                        if self.app:
                            self.app.logging_manager.log_message(f"备用按键执行错误: {str(e)}")
    
    @handle_permission_errors
    def key_down(self, key):
        with self.key_lock:
            try:
                pyautogui.keyDown(key.lower())
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 按下 {key}")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
            except pyautogui.ImageNotFoundException:
                if self.app:
                    self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
                if hasattr(self, 'fallback_keys') and key in self.fallback_keys:
                    if self.app:
                        self.app.logging_manager.log_message(f"  → 尝试备用按键: {self.fallback_keys[key]}")
                    try:
                        pyautogui.keyDown(self.fallback_keys[key].lower())
                        if self.app:
                            self.app.logging_manager.log_message(f"执行: 按下备用按键 {self.fallback_keys[key]}")
                    except Exception as e:
                        if self.app:
                            self.app.logging_manager.log_message(f"备用按键执行错误: {str(e)}")
    
    @handle_permission_errors
    def key_up(self, key):
        with self.key_lock:
            try:
                pyautogui.keyUp(key.lower())
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 抬起 {key}")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def click(self, x, y):
        with self.mouse_lock:
            try:
                pyautogui.click(x, y)
                if self.app:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行鼠标点击: ({x}, {y})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def mouse_down(self, x=None, y=None, button='left'):
        with self.mouse_lock:
            try:
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                pyautogui.mouseDown(button=button)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 按下鼠标{button}键")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def mouse_up(self, x=None, y=None, button='left'):
        with self.mouse_lock:
            try:
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y)
                pyautogui.mouseUp(button=button)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 抬起鼠标{button}键")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @handle_permission_errors
    def move_to(self, x, y):
        with self.mouse_lock:
            try:
                pyautogui.moveTo(x, y)
                if self.app:
                    self.app.logging_manager.log_message(f"执行: 移动鼠标到 ({x}, {y})")
            except pyautogui.FailSafeException:
                if self.app:
                    self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
