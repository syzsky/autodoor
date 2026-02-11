import os
import sys
import platform

class BaseInputAdapter:
    """输入适配器基类"""
    def __init__(self, app):
        self.app = app
    
    def press_key(self, key, delay):
        pass
    
    def key_down(self, key):
        pass
    
    def key_up(self, key):
        pass
    
    def click(self, x, y):
        pass

class WindowsInputAdapter(BaseInputAdapter):
    """Windows输入适配器"""
    def press_key(self, key, delay):
        self.app.input_controller.press_key(key, delay)
    
    def key_down(self, key):
        self.app.input_controller.key_down(key)
    
    def key_up(self, key):
        self.app.input_controller.key_up(key)
    
    def click(self, x, y):
        self.app.input_controller.click(x, y)

class MacOSInputAdapter(BaseInputAdapter):
    """macOS输入适配器"""
    def press_key(self, key, delay):
        self.app.input_controller.press_key(key, delay)
    
    def key_down(self, key):
        self.app.input_controller.key_down(key)
    
    def key_up(self, key):
        self.app.input_controller.key_up(key)
    
    def click(self, x, y):
        self.app.input_controller.click(x, y)

class BaseRecorderAdapter:
    """录制器适配器基类"""
    def __init__(self, app):
        self.app = app
    
    def start(self):
        pass

class WindowsRecorderAdapter(BaseRecorderAdapter):
    """Windows录制器适配器"""
    def start(self):
        # Windows录制逻辑
        pass

class MacOSRecorderAdapter(BaseRecorderAdapter):
    """macOS录制器适配器"""
    def start(self):
        # macOS录制逻辑
        pass

class BasePermissionAdapter:
    """权限适配器基类"""
    def check(self):
        pass

class WindowsPermissionAdapter(BasePermissionAdapter):
    """Windows权限适配器"""
    def check(self):
        # Windows权限检查逻辑
        return True

class MacOSPermissionAdapter(BasePermissionAdapter):
    """macOS权限适配器"""
    def __init__(self, app):
        self.app = app
    
    def check(self):
        # 使用PermissionManager统一检查权限
        from input.permissions import PermissionManager
        permission_manager = PermissionManager(self.app)
        return permission_manager.check_all()

class PlatformAdapter:
    """平台适配器：统一管理平台特定逻辑"""
    def __init__(self, app):
        self.app = app
        self.platform = platform.system()
        self._init_adapters()
        self.app_name = "AutoDoorOCR"
    
    def _init_adapters(self):
        if self.platform == "Windows":
            self.input = WindowsInputAdapter(self.app)
            self.recorder = WindowsRecorderAdapter(self.app)
            self.permission = WindowsPermissionAdapter()
        elif self.platform == "Darwin":
            self.input = MacOSInputAdapter(self.app)
            self.recorder = MacOSRecorderAdapter(self.app)
            self.permission = MacOSPermissionAdapter(self.app)

    # 统一接口
    def start_recording(self):
        return self.recorder.start()
    
    def check_permissions(self):
        return self.permission.check()
    
    def get_config_dir(self):
        """获取配置文件目录"""
        if self.platform == "Windows":
            # Windows: 使用APPDATA环境变量
            return os.path.join(os.environ.get("APPDATA"), self.app_name)
        elif self.platform == "Darwin":
            # macOS: 使用Library/Preferences目录
            return os.path.join(os.path.expanduser("~"), "Library", "Preferences", self.app_name)
        else:
            # 其他系统: 回退到程序运行目录
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    
    def get_log_file_path(self):
        """获取日志文件路径"""
        if self.platform == "Darwin":
            # macOS平台
            if hasattr(sys, '_MEIPASS'):
                # 打包后的环境，使用应用包同级目录
                app_path = os.path.dirname(os.path.dirname(sys._MEIPASS))
                return os.path.join(app_path, "autodoor.log")
            else:
                # 开发环境，使用当前项目目录
                project_root = os.path.abspath('.')
                return os.path.join(project_root, "autodoor.log")
        else:
            # 其他平台，使用当前项目目录
            project_root = os.path.abspath('.')
            return os.path.join(project_root, "autodoor.log")
    
    def get_tesseract_paths(self, app_root):
        """获取Tesseract可执行文件的可能路径"""
        possible_paths = []
        if self.platform == "Windows":
            # Windows平台
            possible_paths = [
                os.path.join(app_root, "tesseract", "tesseract.exe"),  # 子目录路径
                os.path.join(app_root, "tesseract.exe"),  # 根目录路径（PyInstaller打包后）
            ]
        elif self.platform == "Darwin":
            # macOS平台
            possible_paths = [
                os.path.join(app_root, "tesseract", "tesseract"),  # 主要路径
                os.path.join(app_root, "tesseract"),  # 备选路径
                os.path.join(os.path.dirname(app_root), "tesseract", "tesseract"),  # 应用包外部路径
                # 针对.app包结构的额外路径
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract", "tesseract"),
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract"),
                # macOS系统路径
                "/usr/local/bin/tesseract",  # Homebrew (Intel)
                "/opt/homebrew/bin/tesseract",  # Homebrew (Apple Silicon)
                # 其他可能的系统路径
                "/usr/bin/tesseract"
            ]
        return possible_paths
    
    def is_valid_tesseract_path(self, path):
        """验证Tesseract路径是否有效"""
        if not path:
            return False
        
        if not os.path.exists(path):
            return False
        
        if not os.path.isfile(path):
            return False
        
        if self.platform == "Windows":
            return path.endswith("tesseract.exe")
        elif self.platform == "Darwin":
            return os.path.basename(path) == "tesseract"
        
        return True
    
    def get_test_file_path(self):
        """获取测试文件路径"""
        if self.platform == "Darwin":
            return os.path.join(os.path.expanduser("~"), "test_tesseract.png")
        return 'test_tesseract.png'
