import subprocess
import threading
from PIL import ImageGrab
import numpy as np


class PermissionManager:
    """统一权限管理器类"""
    
    def __init__(self, app):
        """初始化权限管理器
        Args:
            app: AutoDoorOCR实例
        """
        self.app = app
    
    def check_accessibility(self):
        """检查辅助功能权限"""
        return self._check_accessibility_permission_sync()
    
    def check_screen_recording(self):
        """检查屏幕录制权限"""
        return self._check_screen_recording_permission_sync()
    
    def check_all(self):
        """检查所有权限"""
        return self.check_accessibility() and self.check_screen_recording()
    
    def prompt_accessibility(self):
        """提示用户授权辅助功能权限"""
        self._guide_accessibility_setup()
    
    def prompt_screen_recording(self):
        """提示用户授权屏幕录制权限"""
        self._guide_screen_recording_setup()
    
    def check_macos_permissions(self):
        """检查macOS权限（异步版本）"""
        self.app.logging_manager.log_message("开始检查系统权限...")
        
        # 显示进度提示
        self.app.show_progress("正在检查系统权限...")
        
        def check_in_thread():
            """在后台线程中执行权限检查"""
            # 使用平台适配器检查权限
            has_accessibility = self._check_accessibility_permission_sync()
            has_screen_capture = self._check_screen_recording_permission_sync()
            
            # 通过after()回调主线程更新UI
            self.app.root.after(0, lambda: self._on_permissions_checked(has_accessibility, has_screen_capture))
        
        # 启动后台线程执行权限检查
        threading.Thread(target=check_in_thread, daemon=True).start()
    
    def _on_permissions_checked(self, has_accessibility, has_screen_capture, callback=None):
        """权限检查完成后的回调处理"""
        # 隐藏进度提示
        self.app.hide_progress()
        
        # 检查权限结果
        if not has_accessibility or not has_screen_capture:
            self._guide_permission_setup(has_accessibility, has_screen_capture)
        
        self.app.logging_manager.log_message("macOS权限检查完成")
        
        if callback:
            callback(has_accessibility and has_screen_capture)
    
    def _guide_permission_setup(self, has_accessibility, has_screen_capture):
        """引导用户设置权限"""
        if not has_accessibility:
            self._guide_accessibility_setup()
        if not has_screen_capture:
            self._guide_screen_recording_setup()
    
    def _check_accessibility_permission_sync(self):
        """同步检查辅助功能权限"""
        try:
            result = subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to keystroke "a"'
            ], capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def _check_screen_recording_permission_sync(self):
        """同步检查屏幕录制权限（macOS 10.15+ 必需）"""
        try:
            # 截取小区域（10x10 像素）
            screenshot = ImageGrab.grab(bbox=(0, 0, 10, 10))
            img_array = np.array(screenshot)
            
            # 检查是否为纯黑屏（无权限时的典型表现）
            if np.all(img_array == 0):
                return False
            
            # 检查图像尺寸是否异常
            if screenshot.size != (10, 10):
                return False
            
            return True
        except Exception as e:
            return False
    
    def check_permissions_async(self, callback=None):
        """异步权限检查（不阻塞 UI）"""
        def check_in_thread():
            has_accessibility = self._check_accessibility_permission_sync()
            has_screen_capture = self._check_screen_recording_permission_sync()
            
            # 通过 after() 回调主线程
            self.app.root.after(0, lambda: self._on_permissions_checked(
                has_accessibility, has_screen_capture, callback
            ))
        
        # 显示进度指示器
        self.app.logging_manager.log_message("🔍 检查系统权限...")
        
        # 启动后台线程
        threading.Thread(target=check_in_thread, daemon=True).start()
    
    def _check_accessibility_permission(self):
        """检查辅助功能权限（保持兼容性，内部使用同步方法）"""
        return self._check_accessibility_permission_sync()
    
    def _check_screen_recording_permission(self):
        """检查屏幕录制权限（保持兼容性，内部使用同步方法）"""
        return self._check_screen_recording_permission_sync()
    
    def _guide_accessibility_setup(self):
        """引导用户授权辅助功能权限"""
        def open_accessibility_settings():
            subprocess.run([
                "open", 
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            ])
        
        self.app.show_message(
            title="⚠️ 需要辅助功能权限",
            message=(
                "AutoDoor 需要控制键盘和鼠标以实现自动操作功能。\n\n"
                "macOS 安全机制要求您手动授权：\n"
                "1. 点击「打开系统设置」按钮\n"
                "2. 点击左下角 🔒 解锁（输入密码）\n"
                "3. 在列表中找到 AutoDoor 并勾选 ✅\n"
                "4. 返回 AutoDoor 重新启动功能"
            ),
            buttons=[
                ("打开系统设置", open_accessibility_settings),
                ("取消", None)
            ]
        )
    
    def _guide_screen_recording_setup(self):
        """引导用户授权屏幕录制权限"""
        def open_privacy_settings():
            subprocess.run([
                "open", 
                "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
            ])
        
        self.app.show_message(
            title="⚠️ 需要屏幕录制权限",
            message=(
                "AutoDoor 需要截取屏幕内容以实现 OCR/数字/颜色识别功能。\n\n"
                "macOS 安全机制要求您手动授权：\n"
                "1. 点击「打开系统设置」按钮\n"
                "2. 点击左下角 🔒 解锁（输入密码）\n"
                "3. 在列表中找到 AutoDoor 并勾选 ✅\n"
                "4. 返回 AutoDoor 重新启动识别功能"
            ),
            buttons=[
                ("打开系统设置", open_privacy_settings),
                ("取消", None)
            ]
        )
