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
        if hasattr(self.app, '_check_accessibility_permission'):
            return self.app._check_accessibility_permission()
        return False
    
    def check_screen_recording(self):
        """检查屏幕录制权限"""
        if hasattr(self.app, '_check_screen_recording_permission'):
            return self.app._check_screen_recording_permission()
        return False
    
    def check_all(self):
        """检查所有权限"""
        return self.check_accessibility() and self.check_screen_recording()
    
    def prompt_accessibility(self):
        """提示用户授权辅助功能权限"""
        if hasattr(self.app, '_guide_accessibility_setup'):
            self.app._guide_accessibility_setup()
    
    def prompt_screen_recording(self):
        """提示用户授权屏幕录制权限"""
        if hasattr(self.app, '_guide_screen_recording_setup'):
            self.app._guide_screen_recording_setup()
