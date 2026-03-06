import time
import win32gui
import win32con
from typing import Optional, Tuple

from utils.window_capture import find_window_by_title, get_window_rect


class QuickSwitchBackend:
    """快速窗口切换后台操作实现"""
    
    def __init__(self, app=None):
        self.app = app
        self.hwnd: Optional[int] = None
        self.switch_delay: float = 0.05
        self.restore_delay: float = 0.02
        self._original_fg_window: Optional[int] = None
        self._input_controller = None
    
    def _get_input_controller(self):
        """获取输入控制器"""
        if self._input_controller is None and self.app:
            self._input_controller = self.app.input_controller
        return self._input_controller
    
    def find_window(self, title_keyword: str) -> Tuple[bool, Optional[str]]:
        """
        通过标题关键字查找窗口
        
        Args:
            title_keyword: 窗口标题关键字
        
        Returns:
            tuple: (success, window_title)
        """
        hwnd = find_window_by_title(title_keyword)
        if hwnd:
            self.hwnd = hwnd
            title = win32gui.GetWindowText(hwnd)
            return (True, title)
        return (False, None)
    
    def set_hwnd(self, hwnd: int) -> None:
        """设置目标窗口句柄"""
        self.hwnd = hwnd
    
    def _save_foreground_window(self) -> None:
        """保存当前前台窗口"""
        try:
            self._original_fg_window = win32gui.GetForegroundWindow()
        except Exception:
            self._original_fg_window = None
    
    def _restore_foreground_window(self) -> None:
        """
        恢复原来的前台窗口
        """
        if self._original_fg_window:
            try:
                time.sleep(self.restore_delay)
                
                if not win32gui.IsWindow(self._original_fg_window):
                    self._original_fg_window = None
                    return
                
                # 确保原窗口可见
                if win32gui.IsIconic(self._original_fg_window):
                    win32gui.ShowWindow(self._original_fg_window, win32con.SW_RESTORE)
                    time.sleep(0.1)
                
                # 方法1: 发送Alt+Tab模拟用户操作
                try:
                    import win32api
                    # 发送Alt+Tab组合键
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                    time.sleep(0.05)
                    win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)    # Tab键按下
                    time.sleep(0.05)
                    win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab键释放
                    time.sleep(0.05)
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                    time.sleep(0.1)
                except Exception:
                    pass
                
                # 方法2: 先将窗口设置为最顶层，然后激活
                try:
                    # 先设置为最顶层
                    win32gui.SetWindowPos(self._original_fg_window, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                       win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                    time.sleep(0.1)
                    # 然后激活窗口
                    win32gui.SetForegroundWindow(self._original_fg_window)
                    time.sleep(0.1)
                    # 最后取消最顶层状态
                    win32gui.SetWindowPos(self._original_fg_window, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                       win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                    time.sleep(0.1)
                except Exception:
                    pass
                
                # 方法3: 使用更安全的窗口激活方法
                try:
                    # 使用 SetActiveWindow 先激活窗口
                    win32gui.SetActiveWindow(self._original_fg_window)
                    time.sleep(0.1)
                    # 然后设置为前台窗口
                    win32gui.SetForegroundWindow(self._original_fg_window)
                    time.sleep(0.1)
                except Exception:
                    pass
                
                # 方法4: 直接设置前台窗口
                try:
                    win32gui.SetForegroundWindow(self._original_fg_window)
                    time.sleep(0.1)
                except Exception:
                    pass
                
                # 验证窗口是否成功恢复到前台
                current_fg = win32gui.GetForegroundWindow()
                if current_fg != self._original_fg_window:
                    # 最后尝试：最小化再恢复
                    try:
                        win32gui.ShowWindow(self._original_fg_window, win32con.SW_MINIMIZE)
                        time.sleep(0.1)
                        win32gui.ShowWindow(self._original_fg_window, win32con.SW_RESTORE)
                        time.sleep(0.1)
                        win32gui.SetForegroundWindow(self._original_fg_window)
                        time.sleep(0.1)
                    except Exception:
                        pass
                    
            except Exception:
                pass
        self._original_fg_window = None
    
    def _switch_to_target(self) -> bool:
        """
        切换到目标窗口
        
        Returns:
            bool: 是否成功
        """
        if not self.hwnd:
            return False
        
        try:
            if not win32gui.IsWindow(self.hwnd):
                return False
            
            # 首先确保窗口可见
            if win32gui.IsIconic(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)
            
            # 方法1: 发送Alt+Tab模拟用户操作来绕过限制
            try:
                import win32api
                # 发送Alt+Tab组合键
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_TAB, 0, 0, 0)    # Tab键按下
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)  # Tab键释放
                time.sleep(0.05)
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                time.sleep(0.1)
            except Exception:
                pass
            
            # 方法2: 先将窗口设置为最顶层，然后激活
            try:
                # 先设置为最顶层
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                                   win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                time.sleep(0.1)
                # 然后激活窗口
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.1)
                # 最后取消最顶层状态
                win32gui.SetWindowPos(self.hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                                   win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                time.sleep(0.1)
            except Exception:
                pass
            
            # 方法3: 使用更安全的窗口激活方法
            try:
                # 使用 SetActiveWindow 先激活窗口
                win32gui.SetActiveWindow(self.hwnd)
                time.sleep(0.1)
                # 然后设置为前台窗口
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.1)
            except Exception:
                pass
            
            # 方法4: 直接设置前台窗口（作为最后尝试）
            try:
                win32gui.SetForegroundWindow(self.hwnd)
                time.sleep(0.1)
            except Exception:
                pass
            
            # 验证窗口是否成功切换到前台
            current_fg = win32gui.GetForegroundWindow()
            if current_fg == self.hwnd:
                time.sleep(self.switch_delay)
                return True
            else:
                # 最后尝试：最小化再恢复
                try:
                    win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
                    time.sleep(0.1)
                    win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                    time.sleep(0.1)
                    win32gui.SetForegroundWindow(self.hwnd)
                    time.sleep(0.1)
                    # 再次验证
                    current_fg = win32gui.GetForegroundWindow()
                    if current_fg == self.hwnd:
                        time.sleep(self.switch_delay)
                        return True
                except Exception:
                    pass
            
            time.sleep(self.switch_delay)
            return False
            
        except Exception:
            return False
    
    def press_key(self, key: str, delay_min: int = 100, delay_max: int = 200) -> Tuple[bool, str]:
        """
        发送按键（使用现有输入模块）
        
        Args:
            key: 按键名称 (如 'space', 'enter', 'a', '1' 等)
            delay_min: 按键按下最小时长（毫秒）
            delay_max: 按键按下最大时长（毫秒）
        
        Returns:
            tuple: (success, message)
        """
        if not self.hwnd:
            return (False, "未设置目标窗口")
        
        try:
            input_controller = self._get_input_controller()
            if input_controller:
                import random
                hold_delay = random.randint(delay_min, delay_max) / 1000.0
                
                input_controller.key_down(key, priority=1)
                time.sleep(hold_delay)
                input_controller.key_up(key, priority=1)
            else:
                import win32api
                key_map = {
                    'space': win32con.VK_SPACE,
                    'enter': win32con.VK_RETURN,
                    'tab': win32con.VK_TAB,
                    'escape': win32con.VK_ESCAPE,
                    'esc': win32con.VK_ESCAPE,
                    'backspace': win32con.VK_BACK,
                    'delete': win32con.VK_DELETE,
                    'up': win32con.VK_UP,
                    'down': win32con.VK_DOWN,
                    'left': win32con.VK_LEFT,
                    'right': win32con.VK_RIGHT,
                }
                
                key_lower = key.lower().strip()
                if key_lower in key_map:
                    vk_code = key_map[key_lower]
                elif len(key_lower) == 1:
                    vk_code = ord(key_lower.upper())
                else:
                    return (False, f"未知按键: {key}")
                
                import random
                hold_delay = random.randint(delay_min, delay_max) / 1000.0
                
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(hold_delay)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            return (True, f"按键 {key} 发送成功")
            
        except Exception as e:
            return (False, f"发送按键失败: {str(e)}")
    
    def click(self, x: int, y: int, button: str = 'left') -> Tuple[bool, str]:
        """
        鼠标点击（窗口相对坐标）
        
        Args:
            x, y: 窗口相对坐标
            button: 'left' 或 'right'
        
        Returns:
            tuple: (success, message)
        """
        if not self.hwnd:
            return (False, "未设置目标窗口")
        
        try:
            rect = get_window_rect(self.hwnd)
            if not rect:
                return (False, "获取窗口位置失败")
            
            abs_x = rect[0] + x
            abs_y = rect[1] + y
            
            input_controller = self._get_input_controller()
            if input_controller:
                input_controller.click(abs_x, abs_y, priority=1)
            else:
                import win32api
                win32api.SetCursorPos((abs_x, abs_y))
                time.sleep(0.01)
                
                if button.lower() == 'right':
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                    time.sleep(0.05)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                else:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                    time.sleep(0.05)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            return (True, f"点击 ({x}, {y}) 成功")
            
        except Exception as e:
            return (False, f"点击失败: {str(e)}")
    
    def key_down(self, key: str) -> Tuple[bool, str]:
        """
        按下按键（不抬起）
        
        注意：此方法不会自动切换窗口和恢复窗口，
        需要先调用 switch_to_target() 切换到目标窗口，
        操作完成后调用 restore_foreground_window() 恢复原窗口。
        
        Args:
            key: 按键名称
        
        Returns:
            tuple: (success, message)
        """
        if not self.hwnd:
            return (False, "未设置目标窗口")
        
        try:
            input_controller = self._get_input_controller()
            if input_controller:
                input_controller.key_down(key, priority=1)
            else:
                import win32api
                key_map = {
                    'space': win32con.VK_SPACE,
                    'enter': win32con.VK_RETURN,
                    'tab': win32con.VK_TAB,
                    'escape': win32con.VK_ESCAPE,
                    'esc': win32con.VK_ESCAPE,
                    'shift': win32con.VK_SHIFT,
                    'ctrl': win32con.VK_CONTROL,
                    'alt': win32con.VK_MENU,
                }
                
                key_lower = key.lower().strip()
                if key_lower in key_map:
                    vk_code = key_map[key_lower]
                elif len(key_lower) == 1:
                    vk_code = ord(key_lower.upper())
                else:
                    return (False, f"未知按键: {key}")
                
                win32api.keybd_event(vk_code, 0, 0, 0)
            
            return (True, f"按键 {key} 已按下")
            
        except Exception as e:
            return (False, f"按键按下失败: {str(e)}")
    
    def key_up(self, key: str) -> Tuple[bool, str]:
        """
        抬起按键
        
        注意：此方法不会自动切换窗口和恢复窗口，
        需要先调用 switch_to_target() 切换到目标窗口，
        操作完成后调用 restore_foreground_window() 恢复原窗口。
        
        Args:
            key: 按键名称
        
        Returns:
            tuple: (success, message)
        """
        if not self.hwnd:
            return (False, "未设置目标窗口")
        
        try:
            input_controller = self._get_input_controller()
            if input_controller:
                input_controller.key_up(key, priority=1)
            else:
                import win32api
                key_map = {
                    'space': win32con.VK_SPACE,
                    'enter': win32con.VK_RETURN,
                    'tab': win32con.VK_TAB,
                    'escape': win32con.VK_ESCAPE,
                    'esc': win32con.VK_ESCAPE,
                    'shift': win32con.VK_SHIFT,
                    'ctrl': win32con.VK_CONTROL,
                    'alt': win32con.VK_MENU,
                }
                
                key_lower = key.lower().strip()
                if key_lower in key_map:
                    vk_code = key_map[key_lower]
                elif len(key_lower) == 1:
                    vk_code = ord(key_lower.upper())
                else:
                    return (False, f"未知按键: {key}")
                
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            return (True, f"按键 {key} 已抬起")
            
        except Exception as e:
            return (False, f"按键抬起失败: {str(e)}")
    
    def switch_to_target(self) -> bool:
        """
        切换到目标窗口并保存原窗口
        
        Returns:
            bool: 是否成功
        """
        self._save_foreground_window()
        return self._switch_to_target()
    
    def restore_foreground_window(self) -> None:
        """
        恢复原来的前台窗口
        """
        self._restore_foreground_window()
    
    def send_text(self, text: str) -> Tuple[bool, str]:
        """
        发送文本
        
        Args:
            text: 要发送的文本
        
        Returns:
            tuple: (success, message)
        """
        if not self.hwnd:
            return (False, "未设置目标窗口")
        
        if not text:
            return (True, "文本为空")
        
        self._save_foreground_window()
        
        try:
            if not self._switch_to_target():
                return (False, "切换窗口失败")
            
            import win32api
            for char in text:
                vk_code = ord(char.upper())
                shift_needed = char.isupper() or char in '!@#$%^&*()_+{}|:"<>?'
                
                if shift_needed:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
                
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(0.01)
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                if shift_needed:
                    win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
                
                time.sleep(0.01)
            
            self._restore_foreground_window()
            return (True, f"文本 '{text}' 发送成功")
            
        except Exception as e:
            self._restore_foreground_window()
            return (False, f"发送文本失败: {str(e)}")
