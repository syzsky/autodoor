import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import threading
import os

from ui.basic_tab import create_basic_tab
from ui.styles import configure_styles
from core.config import ConfigManager
from core.platform import PlatformAdapter
from core.threading import ThreadManager
from core.events import EventManager
from core.logging import LoggingManager
from core.utils import exit_program
from core.controller import ModuleController
from core.proxy import OCRProxy, TimedProxy, NumberProxy, ScriptProxy, ColorProxy, UIProxy
from input.permissions import PermissionManager
from input.controller import InputController
from input.keyboard import setup_shortcuts
from utils.version import VersionChecker, open_bilibili, open_tool_intro
from utils.tesseract import TesseractManager
from modules.ocr import OCRModule
from modules.timed import TimedModule
from modules.number import NumberModule
from modules.alarm import AlarmModule
from modules.script import ScriptModule
from modules.color import ColorRecognitionManager

# 导入pynput用于全局键盘监听
try:
    from pynput import keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    PYINPUT_AVAILABLE = False

# 导入pygame用于音频播放
try:
    import pygame
    try:
        pygame.mixer.init()
        PYGAME_AVAILABLE = True
    except pygame.error:
        PYGAME_AVAILABLE = False
except ImportError:
    PYGAME_AVAILABLE = False

# 全局版本号配置
VERSION = "2.0.4"

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class AutoDoorOCR:
    """
    AutoDoor OCR 识别系统主类
    该类实现了一个基于OCR的自动识别和操作系统，主要功能包括：
    1. 文字识别：监控指定区域，识别关键词并触发动作
    2. 定时功能：按照设定的时间间隔执行按键操作
    3. 数字识别：监控指定区域的数字变化并触发动作
    4. 报警功能：在触发动作时播放报警声音
    使用Tesseract OCR引擎进行文字识别，PyAutoGUI进行鼠标和键盘操作。
    """

    def __init__(self):
        """
        初始化AutoDoor OCR系统
        主要初始化工作：
        1. 创建主窗口
        2. 初始化版本检查器
        3. 设置配置参数和状态变量
        4. 确定配置文件和日志文件路径
        5. 初始化线程控制和事件队列
        6. 创建界面元素
        7. 加载配置
        8. 检测Tesseract OCR引擎可用性
        9. 设置配置监听器和快捷键
        10. 启动事件处理线程
        """
        self._init_basic_settings()
        self._init_platform()
        self._init_managers()
        self._init_proxy_classes()
        self._init_ui()
        self._init_modules()
        self._load_config()
        self._start_services()

    def _init_basic_settings(self):
        """初始化基础设置"""
        pyautogui.FAILSAFE = False
        self.version = VERSION
        self.state_lock = threading.Lock()

        self.is_running = False
        self.is_paused = False
        self.is_selecting = False
        self.last_trigger_time = 0
        self.system_stopped = False

        self.last_recognition_times = {}
        self.last_trigger_times = {}
        self._number_cache = {}

        self.click_delay = 0.5
        self.default_custom_key = "equal"
        self.default_keywords = ["men", "door"]
        self.default_ocr_language = "eng"

        self.ocr_thread = None
        self.timed_threads = []
        self.number_threads = []

        self.PRIORITIES = {
            "number": 5,
            "timed": 4,
            "ocr": 3,
            "color": 2,
            "script": 1
        }

        self.timed_enabled_var = None
        self.timed_groups = []
        self.number_enabled_var = None
        self.number_regions = []
        self.current_number_region_index = None
        self.tesseract_path = ""
        self.tesseract_available = False

        self.alarm_enabled = {}
        self.ocr_delay_min = None
        self.ocr_delay_max = None
        self.ocr_groups = []
        self.current_ocr_region_index = None

    def _init_platform(self):
        """初始化平台适配"""
        self.platform_adapter = PlatformAdapter(self)
        config_dir = self.platform_adapter.get_config_dir()
        os.makedirs(config_dir, exist_ok=True)
        self.config_file_path = os.path.join(config_dir, "autodoor_config.json")
        self.log_file_path = self.platform_adapter.get_log_file_path()

    def _init_managers(self):
        """初始化管理器"""
        self.logging_manager = LoggingManager(self)
        self.logging_manager.log_message(f"[{self.platform_adapter.platform}] 日志文件路径: {self.log_file_path}")
        self.version_checker = VersionChecker(self)
        self.version_checker.start_auto_check()
        self.version_checker.check_for_updates()
        self.input_controller = InputController(self)
        self.thread_manager = ThreadManager(self)
        self.event_manager = EventManager(self)
        self.config_manager = ConfigManager(self)
        self.permission_manager = PermissionManager(self)

    def _init_proxy_classes(self):
        """初始化代理类（需要在UI创建之前）"""
        self.ocr = OCRProxy(self)
        self.timed = TimedProxy(self)
        self.number = NumberProxy(self)
        self.script = ScriptProxy(self)
        self.color = ColorProxy(self)
        self.ui = UIProxy(self)

    def _init_ui(self):
        """初始化用户界面"""
        self.root = tk.Tk()
        self.root.title(f"AutoDoor OCR 识别系统 v{VERSION}")
        self.root.geometry("900x850")
        self.root.resizable(True, True)
        self.root.minsize(900, 850)
        self._init_tk_variables()
        self.create_widgets()

    def _init_tk_variables(self):
        """初始化Tkinter变量（需要在root创建之后）"""
        self.alarm_sound_path = tk.StringVar(value="")
        self.alarm_volume = tk.IntVar(value=70)
        self.alarm_volume_str = tk.StringVar(value="70")
        for module in ["ocr", "timed", "number"]:
            self.alarm_enabled[module] = tk.BooleanVar(value=False)
        self.ocr_delay_min = tk.IntVar(value=300)
        self.ocr_delay_max = tk.IntVar(value=500)

    def _init_modules(self):
        """初始化功能模块"""
        self.ocr_module = OCRModule(self)
        self.timed_module = TimedModule(self)
        self.number_module = NumberModule(self)
        self.alarm_module = AlarmModule(self)
        self.script_module = ScriptModule(self)
        self.tesseract_manager = TesseractManager(self)
        self.color_recognition_manager = ColorRecognitionManager(self)
        self.MODULES = {
            "ocr": {"threads": "ocr_threads", "stop_func": "ocr.stop_monitoring", "label": "文字识别"},
            "timed": {"threads": "timed_threads", "stop_func": "timed.stop_tasks", "label": "定时功能"},
            "number": {"threads": "number_threads", "stop_func": "number.stop_recognition", "label": "数字识别"},
            "color": {"threads": "color_threads", "stop_func": "color.stop_recognition", "label": "颜色识别"}
        }
        self.module_controller = ModuleController(self)

    def _load_config(self):
        """加载配置"""
        self.config_manager.load_config()
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = ""
            config_updated = True

        if not self.alarm_sound_path.get():
            self.alarm_sound_path.set(self.alarm_module.get_default_alarm_sound_path())
            config_updated = True

        self.tesseract_available = self.tesseract_manager.check_tesseract_availability()

        if config_updated:
            self.config_manager.defer_save_config()

    def _start_services(self):
        """启动服务"""
        if self.platform_adapter.platform == "Darwin":
            self.root.after(100, self.permission_manager.check_macos_permissions)

        self.config_manager.setup_config_listeners()

        if not self.tesseract_available:
            self.status_var.set("Tesseract未配置")
            self.root.after(100, lambda: messagebox.showinfo("提示", "未检测到Tesseract OCR引擎，请在设置中配置Tesseract路径后使用文字识别功能！"))

        self.setup_shortcuts()
        self.event_manager.start_event_thread()

    def create_widgets(self):
        """
        创建应用程序的所有界面元素

        主要工作：
        1. 设置全局样式和主题
        2. 创建主容器和状态栏
        3. 创建标签页布局（首页、文字识别、定时功能、数字识别、基本设置）
        4. 添加控制按钮和页脚信息
        """
        configure_styles()
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Header.TLabel", foreground="green")
        status_label.pack(side=tk.LEFT)

        # 区域信息已移至文字识别标签页内，此处不再显示
        self.region_var = tk.StringVar(value="未选择区域")

        # 主内容区域 - 使用笔记本(tab)布局
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        home_frame = ttk.Frame(notebook)
        notebook.add(home_frame, text="首页")
        self.ui.create_home_tab(home_frame)

        ocr_frame = ttk.Frame(notebook)
        notebook.add(ocr_frame, text="文字识别")
        self.ocr.create_tab(ocr_frame)

        timed_frame = ttk.Frame(notebook)
        notebook.add(timed_frame, text="定时功能")
        self.timed.create_tab(timed_frame)

        number_frame = ttk.Frame(notebook)
        notebook.add(number_frame, text="数字识别")
        self.number.create_tab(number_frame)

        script_frame = ttk.Frame(notebook)
        notebook.add(script_frame, text="脚本运行")
        self.script.create_tab(script_frame)

        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        create_basic_tab(basic_frame, self)

        # 控制按钮区域 - 简化布局，让退出按钮靠近右下角
        control_frame = ttk.Frame(main_frame, padding="10 5 10 0")
        control_frame.pack(fill=tk.X, pady=(10, 0))

        # 左侧声明区域
        footer_frame = ttk.Frame(control_frame)
        footer_frame.pack(side=tk.LEFT, anchor=tk.W)

        # 禁止商用声明
        footer_label = ttk.Label(footer_frame, text="本程序仅供个人学习研究使用，禁止商用 | 制作人：", 
                                  font=("等线", 10), foreground="#888888", cursor="arrow")
        footer_label.pack(side=tk.LEFT)

        # 制作人Bilibili超链接
        author_label = ttk.Label(footer_frame, text="Flown王砖家", 
                                  font=("等线", 10), foreground="blue", cursor="hand2")
        author_label.pack(side=tk.LEFT)
        author_label.bind("<Button-1>", lambda e: open_bilibili())

        # 右侧按钮区域 - 简化布局
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(side=tk.RIGHT, anchor=tk.E)

        # 工具介绍按钮（左侧），与退出按钮保持20px间距
        tool_intro_btn = ttk.Button(buttons_frame, text="工具介绍", command=open_tool_intro)
        tool_intro_btn.pack(side=tk.RIGHT, padx=(0, 20))

        # 检查更新按钮
        check_update_btn = ttk.Button(buttons_frame, text="检查更新", command=self.check_for_updates)
        check_update_btn.pack(side=tk.RIGHT, padx=(0, 20))

        # 退出程序按钮（右侧）
        exit_btn = ttk.Button(buttons_frame, text="退出程序", command=lambda: exit_program(self))
        exit_btn.pack(side=tk.RIGHT)

    def check_for_updates(self):
        """手动检查更新"""
        self.version_checker.check_for_updates(manual=True)

    def cancel_selection(self):
        """取消区域选择"""
        from utils.region import cancel_selection
        cancel_selection(self)

    def log_message(self, message):
        """记录日志信息"""
        self.logging_manager.log_message(message)

    def get_available_keys(self):
        """获取可用按键列表"""
        from input.keyboard import get_available_keys
        return get_available_keys()

    def _clear_ocr_groups(self):
        """清空所有OCR组"""
        self.config_manager.clear_ocr_groups()

    def _load_group_config(self, group, group_config):
        """加载单个OCR组的配置"""
        self.config_manager.load_group_config(group, group_config)

    def _load_enabled_config(self, group, enabled):
        """加载启用状态配置"""
        self.config_manager.load_enabled_config(group, enabled)

    def setup_shortcuts(self):
        """设置快捷键绑定"""
        setup_shortcuts(self)

    def clear_log(self):
        """清除日志"""
        self.logging_manager.clear_log()

    def set_tesseract_path(self):
        """设置Tesseract OCR路径"""
        self.tesseract_manager.set_tesseract_path()

    def save_config(self):
        """保存配置"""
        try:
            config = self.config_manager.get_full_config()
            self.config_manager.save_config(config)
        except Exception as e:
            self.logging_manager.log_message(f"配置保存错误: {str(e)}")

    def start_module(self, module_name, start_func):
        """统一启动模块"""
        self.module_controller.start_module(module_name, start_func)

    def start_all(self):
        """开始运行"""
        self.module_controller.start_all()

    def stop_all(self):
        """停止运行"""
        self.module_controller.stop_all()

    def run(self):
        """运行程序"""
        self.root.mainloop()


def main():
    """主函数，用于命令行调用"""
    app = AutoDoorOCR()
    app.run()

if __name__ == "__main__":
    main()