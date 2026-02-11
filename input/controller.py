import pyautogui
import threading
import time

class InputController:
    """输入控制器类，提供通用的按键和鼠标操作方法"""
    
    def __init__(self, app=None):
        self.app = app
        # 初始化标志
        self.core_graphics_available = False
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
                raise  # 保持异常传播语义
        return wrapper
    
    @staticmethod
    def main_thread_required(func):
        """自动将方法调用调度到主线程"""
        import threading
        def wrapper(self, *args, **kwargs):
            if threading.current_thread() is threading.main_thread():
                return func(self, *args, **kwargs)
            
            # 调度到主线程（同步等待结果）
            result = []
            event = threading.Event()
            
            def _execute():
                try:
                    result.append(func(self, *args, **kwargs))
                except Exception as e:
                    result.append(e)
                finally:
                    event.set()
            
            # 使用 Tkinter 的 after() 确保在主线程执行
            if self.app and hasattr(self.app, 'root') and hasattr(self.app.root, 'after'):
                self.app.root.after(0, _execute)
                event.wait(timeout=5.0)  # 最多等待5秒
            else:
                # 如果没有 Tkinter 根窗口，直接执行（可能会在 macOS 上崩溃）
                return func(self, *args, **kwargs)
            
            if not result:
                raise TimeoutError("Input operation timed out")
            if isinstance(result[0], Exception):
                raise result[0]
            return result[0]
        return wrapper
    
    @main_thread_required
    @handle_permission_errors
    def press_key(self, key, delay=0, module_info=None):
        """
        执行按键操作
        Args:
            key: 按键名称
            delay: 延迟时间（秒）
            module_info: 模块信息，用于获取延迟范围
        """
        try:
            # 处理延迟
            if delay > 0:
                time.sleep(delay)
            
            # 跨平台实现：统一使用pyautogui
            # pyautogui.press 期望按键名称是小写的
            pyautogui.press(key.lower(), interval=delay)
            if self.app:
                self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行按键: {key}")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
        except pyautogui.ImageNotFoundException:
            if self.app:
                self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
            # 智能降级：尝试备用按键
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
    
    @main_thread_required
    @handle_permission_errors
    def key_down(self, key):
        """
        按下按键
        Args:
            key: 按键名称
        """
        try:
            # 跨平台实现：统一使用pyautogui
            # pyautogui.keyDown 期望按键名称是小写的
            pyautogui.keyDown(key.lower())
            if self.app:
                self.app.logging_manager.log_message(f"执行: 按下 {key}")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
        except pyautogui.ImageNotFoundException:
            if self.app:
                self.app.logging_manager.log_message(f"⚠️ 未找到目标图像: {key}")
            # 智能降级：尝试备用按键
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
    
    @main_thread_required
    @handle_permission_errors
    def key_up(self, key):
        """
        抬起按键
        Args:
            key: 按键名称
        """
        try:
            # 跨平台实现：统一使用pyautogui
            # pyautogui.keyUp 期望按键名称是小写的
            pyautogui.keyUp(key.lower())
            if self.app:
                self.app.logging_manager.log_message(f"执行: 抬起 {key}")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @main_thread_required
    @handle_permission_errors
    def click(self, x, y):
        """
        执行鼠标点击操作
        Args:
            x: x坐标
            y: y坐标
        """
        try:
            # 跨平台实现：统一使用pyautogui
            pyautogui.click(x, y)
            if self.app:
                self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 执行鼠标点击: ({x}, {y})")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @main_thread_required
    @handle_permission_errors
    def mouse_down(self, x=None, y=None, button='left'):
        """
        按下鼠标按钮
        Args:
            x: x坐标（可选）
            y: y坐标（可选）
            button: 鼠标按钮（left, right, middle）
        """
        try:
            # 跨平台实现：统一使用pyautogui
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.mouseDown(button=button)
            if self.app:
                self.app.logging_manager.log_message(f"执行: 按下鼠标{button}键")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @main_thread_required
    @handle_permission_errors
    def mouse_up(self, x=None, y=None, button='left'):
        """
        抬起鼠标按钮
        Args:
            x: x坐标（可选）
            y: y坐标（可选）
            button: 鼠标按钮（left, right, middle）
        """
        try:
            # 跨平台实现：统一使用pyautogui
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.mouseUp(button=button)
            if self.app:
                self.app.logging_manager.log_message(f"执行: 抬起鼠标{button}键")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
    
    @main_thread_required
    @handle_permission_errors
    def move_to(self, x, y):
        """
        移动鼠标到指定位置
        Args:
            x: x坐标
            y: y坐标
        """
        try:
            # 跨平台实现：统一使用pyautogui
            pyautogui.moveTo(x, y)
            if self.app:
                self.app.logging_manager.log_message(f"执行: 移动鼠标到 ({x}, {y})")
        except pyautogui.FailSafeException:
            if self.app:
                self.app.logging_manager.log_message("⚠️ 检测到用户移动鼠标到屏幕角落，操作已取消")
