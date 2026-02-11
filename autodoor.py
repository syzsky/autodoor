import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
from collections import defaultdict
import threading
import time
import random
import datetime
import subprocess
import os
import sys
import json
import queue
import numpy as np

# 导入新模块
from ui.validators import Validators
from ui.builder import UIBuilder, UI_CONFIG
from ui.home import create_home_tab
from ui.ocr_tab import create_ocr_tab, create_ocr_group, add_ocr_group, delete_ocr_group_by_button, delete_ocr_group, renumber_ocr_groups, start_ocr_region_selection
from ui.timed_tab import create_timed_tab, create_timed_group, add_timed_group, delete_timed_group_by_button, delete_timed_group, renumber_timed_groups
from ui.number_tab import create_number_tab, create_number_region, add_number_region, delete_number_region_by_button, delete_number_region, renumber_number_regions, start_number_region_selection
from ui.script_tab import create_script_tab
from ui.basic_tab import create_basic_tab
from core.config import ConfigManager
from core.platform import PlatformAdapter
from core.threading import ThreadManager
from core.events import EventManager
from core.logging import LoggingManager
from input.permissions import PermissionManager
from input.controller import InputController
from utils.version import VersionChecker
from utils.region import _start_selection
from utils.keyboard import start_key_listening
from utils.image import _preprocess_image
from utils.tesseract import TesseractManager
from modules.ocr import OCRModule
from modules.timed import TimedModule
from modules.number import NumberModule
from modules.alarm import AlarmModule
from modules.script import ScriptExecutor
from modules.color import ColorRecognition
from modules.input import KeyEventExecutor



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
        # 禁用PyAutoGUI的故障安全机制，防止鼠标移动到屏幕角落时触发异常
        pyautogui.FAILSAFE = False

        # 版本号
        self.version = VERSION

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(f"AutoDoor OCR 识别系统 v{VERSION}")
        self.root.geometry("900x850")  # 增加默认高度
        self.root.resizable(True, True) 
        self.root.minsize(900, 850)  # 增加最小高度

        # ========== 配置参数 ==========
        # OCR相关配置
        self.click_delay = 0.5  # 点击后的延迟时间（秒）
        self.default_custom_key = "equal"  # 默认自定义按键

        # 关键词配置
        self.default_keywords = ["men", "door"]  # 默认识别关键词
        self.default_ocr_language = "eng"  # 默认OCR识别语言

        # 状态变量
        self.is_running = False  # 是否正在运行
        self.is_paused = False  # 是否暂停
        self.is_selecting = False  # 是否正在选择区域
        self.last_trigger_time = 0  # 上次触发动作的时间
        self.system_stopped = False  # 系统完全停止标志，用于阻止外部命令唤醒
        
        # 线程锁，用于保护共享状态
        self.state_lock = threading.Lock()

        # OCR组触发时间跟踪
        self.last_recognition_times = {}  # 识别间隔时间记录
        self.last_trigger_times = {}  # 暂停期时间记录

        # 数字识别缓存
        self._number_cache = {}  # 缓存：text → number

        # ========== 文件路径配置 ==========
        # 确保平台适配器已初始化
        if not hasattr(self, 'platform_adapter'):
            self.platform_adapter = PlatformAdapter(self)

        # 获取配置文件目录
        config_dir = self.platform_adapter.get_config_dir()

        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)

        # 配置文件路径
        self.config_file_path = os.path.join(config_dir, "autodoor_config.json")

        # 日志文件路径设置
        self.log_file_path = self.platform_adapter.get_log_file_path()
        
        # 初始化日志管理器
        self.logging_manager = LoggingManager(self)
        
        # 记录日志文件路径
        self.logging_manager.log_message(f"[{self.platform_adapter.platform}] 日志文件路径: {self.log_file_path}")

        # 初始化版本检查器
        self.version_checker = VersionChecker(self)

        # 启动自动检查
        self.version_checker.start_auto_check()

        # 应用启动时检查一次
        self.version_checker.check_for_updates()

        # 权限检查（macOS）
        if self.platform_adapter.platform == "Darwin":
            # 延迟到主循环开始后检查权限，避免UI尚未就绪
            self.root.after(100, self._check_macos_permissions)

        # ========== 线程控制 ==========
        self.ocr_thread = None  # OCR识别线程
        self.timed_threads = []  # 定时功能线程列表
        self.number_threads = []  # 数字识别线程列表

        # 优先级定义
        self.PRIORITIES = {
            "number": 5,  # 数字识别 - 最高优先级
            "timed": 4,   # 定时功能
            "ocr": 3,     # OCR识别
            "color": 2,   # 颜色识别
            "script": 1   # 脚本运行 - 最低优先级
        }

        # ========== 功能模块配置 ==========
        # 定时功能相关
        self.timed_enabled_var = None  # 定时功能启用状态变量
        self.timed_groups = []  # 定时功能组列表

        # 数字识别相关
        self.number_enabled_var = None  # 数字识别启用状态变量
        self.number_regions = []  # 数字识别区域列表
        self.current_number_region_index = None  # 当前正在配置的数字识别区域索引
        
        # Tesseract相关
        self.tesseract_path = ""  # Tesseract OCR引擎路径
        self.tesseract_available = False  # Tesseract OCR引擎是否可用

        # 报警功能相关
        self.alarm_enabled = {}  # 各模块报警启用状态
        self.alarm_sound_path = tk.StringVar(value="")  # 全局报警声音路径
        self.alarm_volume = tk.IntVar(value=70)  # 全局报警音量，默认70%
        self.alarm_volume_str = tk.StringVar(value="70")  # 用于显示的音量字符串

        # 初始化报警配置
        for module in ["ocr", "timed", "number"]:
            self.alarm_enabled[module] = tk.BooleanVar(value=False)

        # 按键延迟配置
        self.ocr_delay_min = tk.IntVar(value=300)  # 按键按下最小延迟（毫秒）
        self.ocr_delay_max = tk.IntVar(value=500)  # 按键按下最大延迟（毫秒）

        # OCR组管理相关
        self.ocr_groups = []  # OCR识别组列表
        self.current_ocr_region_index = None  # 当前正在配置的OCR识别区域索引

        # 创建输入控制器实例
        self.input_controller = InputController(self)

        # 创建平台适配器实例
        self.platform_adapter = PlatformAdapter(self)

        # 初始化线程管理器
        self.thread_manager = ThreadManager(self)
        
        # 初始化事件管理器
        self.event_manager = EventManager(self)
        
        # 初始化配置管理器
        self.config_manager = ConfigManager(self)
        
        # 初始化OCR模块
        self.ocr_module = OCRModule(self)
        # 初始化定时任务模块
        self.timed_module = TimedModule(self)
        # 初始化数字识别模块
        self.number_module = NumberModule(self)
        # 初始化报警模块
        self.alarm_module = AlarmModule(self)
        # 初始化Tesseract管理器
        self.tesseract_manager = TesseractManager(self)

        # 先创建界面元素，确保所有UI变量都被初始化
        self.create_widgets()

        # 加载配置（包括Tesseract路径和报警设置）
        self.load_config()

        # 如果配置中没有Tesseract路径，使用空字符串（不强制使用项目自带的tesseract）
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = ""  # 初始为空，让用户后续自行配置
            config_updated = True

        # 如果配置中没有报警声音路径，使用项目自带的alarm.mp3
        if not self.alarm_sound_path.get():
            self.alarm_sound_path.set(self.alarm_module.get_default_alarm_sound_path())
            config_updated = True
        
        # 模块注册表
        self.MODULES = {
            "ocr": {"threads": "ocr_threads", "stop_func": "stop_ocr", "label": "文字识别"},
            "timed": {"threads": "timed_threads", "stop_func": "stop_timed_tasks", "label": "定时功能"},
            "number": {"threads": "number_threads", "stop_func": "stop_number_recognition", "label": "数字识别"},
            "color": {"threads": "color_threads", "stop_func": "stop_color_recognition", "label": "颜色识别"}
        }

        # 执行Tesseract引擎的存在性检测和可用性验证
        self.tesseract_available = self.tesseract_manager.check_tesseract_availability()

        # 如果使用了默认配置，将其保存到配置文件
        if config_updated:
            self._defer_save_config()

        # 设置配置监听器
        self.setup_config_listeners()

        # 检查tesseract可用性，在主循环开始后显示提示
        if not self.tesseract_available:
            self.status_var.set("Tesseract未配置")
            # 使用after将提示延迟到主循环开始后显示
            self.root.after(100, lambda: messagebox.showinfo("提示", "未检测到Tesseract OCR引擎，请在设置中配置Tesseract路径后使用文字识别功能！"))

        # 设置快捷键绑定
        self.setup_shortcuts()

        # 启动事件处理线程
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
        # 设置全局样式
        style = ttk.Style()
        # 统一背景色
        bg_color = "#f0f0f0"
        green_bg_color = "#e8f4e8"

        # 基本样式配置，所有组件背景色与整体背景色一致
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"), background=bg_color)
        style.configure("TButton", padding=5, background=bg_color)
        style.configure("TEntry", background=bg_color, fieldbackground=bg_color)
        style.configure("TCheckbutton", background=bg_color)
        style.configure("TCombobox", background=bg_color, fieldbackground=bg_color)
        style.configure("TLabelFrame", background=bg_color, bordercolor=bg_color)
        style.configure("TLabelFrame.Label", background=bg_color)

        # 修复文本元素底部灰色问题，确保所有标签相关组件都使用正确背景色
        style.configure(".", background=bg_color)  # 设置所有组件的默认背景色
        style.configure("TLabel", relief="flat")  # 移除标签的默认边框
        style.map("TLabel", background=[("active", bg_color)])  # 确保选中时背景色正确
        style.map("TLabelFrame.Label", background=[("active", bg_color)])  # 标签框架标题选中时背景色
        style.map("TFrame", background=[("active", bg_color)])  # 框架选中时背景色

        # 添加绿色边框样式，用于标记启用的识别组
        style.configure("Green.TFrame", background=green_bg_color)
        # 增强Green.TLabelframe样式定义，确保在所有平台上都能正确显示
        style.configure("Green.TLabelframe", 
                      background=green_bg_color, 
                      borderwidth=2, 
                      relief=tk.SOLID, 
                      bordercolor="green")
        style.configure("Green.TLabelframe.Label", 
                      foreground="green", 
                      font=("Arial", 10, "bold"), 
                      background=green_bg_color)
        style.map("Green.TLabelframe", 
                 background=[("active", green_bg_color)],
                 bordercolor=[("active", "green")])
        style.map("Green.TLabelframe.Label", 
                 foreground=[("active", "green")],
                 background=[("active", green_bg_color)])
        style.configure("Green.TLabel", background=green_bg_color)
        style.configure("Green.TEntry", background=green_bg_color, fieldbackground=bg_color)
        style.configure("Green.TButton", background=green_bg_color)
        style.configure("Green.TCheckbutton", background=green_bg_color)
        style.configure("Green.TCombobox", background=green_bg_color, fieldbackground=bg_color)

        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        # 状态显示
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Header.TLabel", foreground="green")
        status_label.pack(side=tk.LEFT)

        # 区域信息已移至文字识别标签页内，此处不再显示
        self.region_var = tk.StringVar(value="未选择区域")

        # 主内容区域 - 使用笔记本(tab)布局
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 首页标签页 - 新增
        home_frame = ttk.Frame(notebook)
        notebook.add(home_frame, text="首页")
        self.create_home_tab(home_frame)

        # 文字识别标签页
        ocr_frame = ttk.Frame(notebook)
        notebook.add(ocr_frame, text="文字识别")
        self.create_ocr_tab(ocr_frame)

        # 定时功能标签页
        timed_frame = ttk.Frame(notebook)
        notebook.add(timed_frame, text="定时功能")
        self.create_timed_tab(timed_frame)

        # 数字识别标签页
        number_frame = ttk.Frame(notebook)
        notebook.add(number_frame, text="数字识别")
        self.create_number_tab(number_frame)

        # 脚本运行标签页
        script_frame = ttk.Frame(notebook)
        notebook.add(script_frame, text="脚本运行")
        self.create_script_tab(script_frame)

        # 基本设置标签页
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
        author_label.bind("<Button-1>", lambda e: self.open_bilibili())

        # 右侧按钮区域 - 简化布局
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(side=tk.RIGHT, anchor=tk.E)

        # 定义工具介绍按钮的点击事件
        def open_tool_intro():
            import webbrowser
            webbrowser.open("https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink")

        # 退出程序按钮（右侧）
        exit_btn = ttk.Button(buttons_frame, text="退出程序", command=self.exit_program)
        exit_btn.pack(side=tk.RIGHT)

        # 检查更新按钮
        check_update_btn = ttk.Button(buttons_frame, text="检查更新", command=self.check_for_updates)
        check_update_btn.pack(side=tk.RIGHT, padx=(0, 20))

        # 工具介绍按钮（左侧），与退出按钮保持20px间距
        tool_intro_btn = ttk.Button(buttons_frame, text="工具介绍", command=open_tool_intro)
        tool_intro_btn.pack(side=tk.RIGHT, padx=(0, 20))

    def open_bilibili(self):
        """打开Bilibili主页"""
        import webbrowser
        webbrowser.open("https://space.bilibili.com/263150759")

    def check_for_updates(self):
        """手动检查更新"""
        self.version_checker.check_for_updates(manual=True)

    def create_ocr_tab(self, parent):
        """创建文字识别标签页"""
        create_ocr_tab(parent, self)

    def create_ocr_group(self, index):
        """创建单个文字识别组"""
        create_ocr_group(self, index)

    def add_ocr_group(self):
        """新增文字识别组"""
        add_ocr_group(self)

    def delete_ocr_group_by_button(self, button):
        """通过按钮删除对应的文字识别组"""
        delete_ocr_group_by_button(self, button)

    def delete_ocr_group(self, index, confirm=True):
        """删除文字识别组"""
        delete_ocr_group(self, index, confirm)

    def renumber_ocr_groups(self):
        """重新编号所有文字识别组"""
        renumber_ocr_groups(self)

    def start_ocr_region_selection(self, index):
        """开始选择OCR识别区域"""
        start_ocr_region_selection(self, index)

    def start_number_region_selection(self, region_index):
        """开始数字识别区域选择"""
        start_number_region_selection(self, region_index)

    def _delete_group_by_button(self, button, groups, group_type, delete_func):
        """通用的通过按钮删除组的方法
        Args:
            button: 触发删除的按钮
            groups: 组列表
            group_type: 组类型名称（用于日志）
            delete_func: 删除函数
        """
        # 遍历所有组，找到包含该按钮的组
        for i, group in enumerate(groups):
            group_frame = group["frame"]
            # 检查按钮是否在当前组的框架中
            if button.winfo_parent() == str(group_frame):
                # 直接使用当前索引删除
                delete_func(i)
                return
            
            # 检查按钮是否在组框架的子框架中
            for child in group_frame.winfo_children():
                if button.winfo_parent() == str(child):
                    delete_func(i)
                    return
        
        messagebox.showerror("错误", f"无法找到对应的{group_type}，请重试！")

    def _delete_group(self, index, groups, group_type, min_count, rename_func, log_prefix, confirm=True):
        """通用的删除组方法
        Args:
            index: 要删除的组索引
            groups: 组列表
            group_type: 组类型名称（用于日志和提示）
            min_count: 最小保留数量
            rename_func: 重新编号函数
            log_prefix: 日志前缀
            confirm: 是否显示确认对话框，默认为True
        """
        if len(groups) <= min_count:
            messagebox.showwarning("警告", f"至少需要保留{min_count}个{group_type}！")
            return

        # 只有在confirm为True时才显示确认对话框
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除{group_type}{index+1}吗？"):
                return

        # 检查索引是否有效，避免删除后索引过期导致的IndexError
        if index >= len(groups):
            # 如果索引超出范围，可能是因为组已经被重新编号
            # 尝试使用最后一个索引
            index = len(groups) - 1

        if 0 <= index < len(groups):
            # 移除组框架
            groups[index]["frame"].destroy()
            # 从列表中删除
            del groups[index]
            # 重新编号所有组
            rename_func()
            self.logging_manager.log_message(f"已删除{log_prefix}{index+1}")
        else:
            messagebox.showerror("错误", f"索引无效，无法删除{group_type}！")

    def _add_group(self, groups, max_count, create_func, group_type, log_prefix):
        """通用的新增组方法
        Args:
            groups: 组列表
            max_count: 最大允许数量
            create_func: 创建组的函数
            group_type: 组类型名称（用于提示）
            log_prefix: 日志前缀
        """
        if len(groups) >= max_count:
            messagebox.showwarning("警告", f"最多只能创建{max_count}个{group_type}！")
            return

        create_func(len(groups))
        self.logging_manager.log_message(f"新增{log_prefix}{len(groups)}")

    def _on_mousewheel(self, event, canvas):
        """公共的鼠标滚轮事件处理函数"""
        # 使用yview_moveto方法实现平滑滚动
        current_pos = canvas.yview()
        scroll_amount = event.delta / 120 / 10  # 调整滚动速度
        new_pos = current_pos[0] - scroll_amount
        new_pos = max(0, min(1, new_pos))
        canvas.yview_moveto(new_pos)
        # 阻止事件继续传播
        return "break"

    def _configure_scroll_region(self, event, canvas, frame_tag):
        """公共的滚动区域配置函数"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        # 确保内部框架宽度与画布一致
        canvas.itemconfig(frame_tag, width=canvas.winfo_width())

    def _bind_mousewheel_to_widgets(self, canvas, widgets):
        """为指定的控件及其子控件绑定鼠标滚轮事件"""
        def on_mousewheel(event):
            return self._on_mousewheel(event, canvas)

        for widget in widgets:
            widget.bind("<MouseWheel>", on_mousewheel)
            # 为控件内所有子组件绑定鼠标滚轮事件
            for child in widget.winfo_children():
                child.bind("<MouseWheel>", on_mousewheel)
                # 递归绑定到所有子组件的子组件
                for grandchild in child.winfo_children():
                    grandchild.bind("<MouseWheel>", on_mousewheel)

    def create_timed_tab(self, parent):
        """创建定时功能标签页"""
        create_timed_tab(parent, self)

    def create_timed_group(self, index):
        """创建单个定时组，所有UI元素布局在一行中"""
        create_timed_group(self, index)



    def delete_timed_group_by_button(self, button):
        """通过按钮删除对应的定时组"""
        delete_timed_group_by_button(self, button)

    def delete_timed_group(self, index, confirm=True):
        """删除定时组
        Args:
            index: 要删除的定时组索引
            confirm: 是否显示确认对话框，默认为True
        """
        delete_timed_group(self, index, confirm)

    def renumber_timed_groups(self):
        """重新编号所有定时组"""
        renumber_timed_groups(self)

    def add_timed_group(self):
        """新增定时组"""
        add_timed_group(self)

    def create_number_tab(self, parent):
        """创建数字识别标签页"""
        create_number_tab(parent, self)

    def create_number_region(self, index):
        """创建单个数字识别区域"""
        create_number_region(self, index)

    def delete_number_region_by_button(self, button):
        """通过按钮删除对应的数字识别区域"""
        delete_number_region_by_button(self, button)

    def delete_number_region(self, index, confirm=True):
        """删除数字识别区域
        Args:
            index: 要删除的区域索引
            confirm: 是否显示确认对话框，默认为True
        """
        delete_number_region(self, index, confirm)

    def renumber_number_regions(self):
        """重新编号所有数字识别区域"""
        renumber_number_regions(self)

    def add_number_region(self):
        """新增数字识别区域"""
        add_number_region(self)




    
    def create_home_tab(self, parent):
        """创建首页标签页"""
        create_home_tab(parent, self)

    def get_available_keys(self):
        """获取可用按键列表"""
        return [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            "space", "enter", "tab", "escape", "backspace", "delete", "insert",
            "equal", "plus", "minus", "asterisk", "slash", "backslash",
            "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
        ]



    def _load_tesseract_config(self, config):
        """加载Tesseract配置"""
        tesseract_path = self.config_manager.get_config_value(config, 'tesseract.path')
        if not tesseract_path:
            # 兼容旧格式
            tesseract_path = config.get('tesseract_path')

        if tesseract_path and tesseract_path.strip():
            temp_path = tesseract_path.strip()
            # 检查路径是否存在
            if os.path.exists(temp_path):
                self.tesseract_path = temp_path
                self.logging_manager.log_message(f"从配置文件加载Tesseract路径: {self.tesseract_path}")
            else:
                self.logging_manager.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")

    def _create_group_ui(self, parent, index, group_type, create_specific_ui):
        """
        创建组 UI 的通用方法
        Args:
            parent: 父容器
            index: 组索引
            group_type: 组类型
            create_specific_ui: 创建特定UI元素的函数
        Returns:
            组配置字典
        """
        # 创建组框架
        group_frame = self._create_group_frame(parent, index, group_type)

        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)

        # 设置组点击事件和样式更新
        self._setup_group_click_handler(group_frame, enabled_var)

        # 初始应用样式
        self.update_group_style(group_frame, enabled_var.get())

        # 创建特定的 UI 元素
        group_config = create_specific_ui(group_frame, enabled_var)

        # 添加到组列表
        groups = getattr(self, f"{group_type.lower()}_groups", [])
        groups.append(group_config)

        return group_config

    def _clear_ocr_groups(self):
        """清空所有OCR组"""
        for group in self.ocr_groups:
            group['frame'].destroy()
        self.ocr_groups.clear()

    def _load_group_config(self, group, group_config):
        """加载单个OCR组的配置
        Args:
            group: OCR组配置字典
            group_config: 从配置文件读取的组配置
        """
        # 配置项映射
        config_mappings = {
            'enabled': lambda val: self._load_enabled_config(group, val),
            'region': lambda val: self._load_region_config(group, val),
            'interval': lambda val: group['interval'].set(val),
            'pause': lambda val: group['pause'].set(val),
            'key': lambda val: group['key'].set(val),
            'delay_min': lambda val: group['delay_min'].set(val),
            'delay_max': lambda val: group['delay_max'].set(val),
            'alarm': lambda val: group['alarm'].set(val),
            'keywords': lambda val: group['keywords'].set(val),
            'language': lambda val: group['language'].set(val),
            'click': lambda val: group['click'].set(val)
        }

        # 应用配置
        for key, setter in config_mappings.items():
            if key in group_config:
                setter(group_config[key])

    def _load_enabled_config(self, group, enabled):
        """加载启用状态配置
        Args:
            group: OCR组配置字典
            enabled: 是否启用
        """
        group['enabled'].set(enabled)
        group_frame = group['frame']
        self.update_group_style(group_frame, enabled)

    def _load_region_config(self, group, region):
        """加载区域配置
        Args:
            group: OCR组配置字典
            region: 区域坐标
        """
        if region is not None:
            try:
                region_tuple = tuple(region)
                group['region'] = region_tuple
                group['region_var'].set(f"区域: {region_tuple[0]},{region_tuple[1]} - {region_tuple[2]},{region_tuple[3]}")
            except (TypeError, ValueError):
                self.logging_manager.log_message(f"配置文件中的OCR区域格式错误: {region}")

    def _load_legacy_ocr_config(self, ocr_config):
        """加载旧格式的OCR配置
        Args:
            ocr_config: OCR配置字典
        """
        # 旧格式的OCR配置已经被组配置所替代
        # 这里只需要加载自定义按键和关键词等全局配置
        if 'custom_key' in ocr_config:
            self.custom_key = ocr_config['custom_key']
        if 'custom_keywords' in ocr_config and ocr_config['custom_keywords']:
            self.custom_keywords = ocr_config['custom_keywords']
        if 'language' in ocr_config:
            self.ocr_language = ocr_config['language']

    def _load_ocr_config(self, config):
        """加载OCR配置"""
        ocr_config = self.config_manager.get_config_value(config, 'ocr', {})
        groups = self.config_manager.get_config_value(ocr_config, 'groups', [])

        if isinstance(groups, list):
            # 直接清空所有OCR组
            for group in self.ocr_groups:
                group['frame'].destroy()
            self.ocr_groups.clear()

            # 然后根据配置重新创建所有OCR组
            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    # 直接调用create_ocr_group创建OCR组
                    self.create_ocr_group(i)
                    # 设置组配置
                    if i < len(self.ocr_groups):
                        for key, value in group_config.items():
                            if key in self.ocr_groups[i]:
                                if key == 'enabled':
                                    self.ocr_groups[i][key].set(value)
                                    # 使用类方法更新样式
                                    group_frame = self.ocr_groups[i]['frame']
                                    self.update_group_style(group_frame, value)
                                elif key == 'region' and value is not None:
                                    try:
                                        region = tuple(value)
                                        self.ocr_groups[i][key] = region
                                        self.ocr_groups[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                                    except (TypeError, ValueError):
                                        self.logging_manager.log_message(f"配置文件中的OCR区域格式错误: {value}")
                                else:
                                    if hasattr(self.ocr_groups[i][key], 'set'):
                                        self.ocr_groups[i][key].set(value)

            # 如果没有配置，至少创建一个OCR组
            if len(self.ocr_groups) == 0:
                self.create_ocr_group(0)

    def _load_click_config(self, config):
        """加载点击模式和坐标配置（保持兼容性）"""
        # 保持配置文件兼容性，但不再加载坐标模式配置
        # 旧配置文件中的click部分将被忽略
        pass

    def _clear_timed_groups(self):
        """清空所有定时组"""
        for group in self.timed_groups:
            group['frame'].destroy()
        self.timed_groups.clear()

    def _load_timed_enabled_config(self, group, enabled):
        """加载定时组启用状态配置
        Args:
            group: 定时组配置字典
            enabled: 是否启用
        """
        group['enabled'].set(enabled)
        group_frame = group['frame']
        self.update_group_style(group_frame, enabled)

    def _load_timed_config(self, config):
        """加载定时功能配置"""
        timed_config = config.get('timed_key_press', {})
        groups = self.config_manager.get_config_value(timed_config, 'groups', [])

        if isinstance(groups, list):
            self._clear_timed_groups()

            # 根据配置重新创建所有定时组
            for i, group_config in enumerate(groups):
                if isinstance(group_config, dict):
                    self.create_timed_group(i)
                    # 设置组配置
                    if i < len(self.timed_groups):
                        for key, value in group_config.items():
                            if key in self.timed_groups[i]:
                                if hasattr(self.timed_groups[i][key], 'set'):
                                    self.timed_groups[i][key].set(value)

            # 如果没有配置，至少创建一个定时组
            if len(self.timed_groups) == 0:
                self.create_timed_group(0)

    def _clear_number_regions(self):
        """清空所有数字识别区域"""
        for region in self.number_regions:
            region['frame'].destroy()
        self.number_regions.clear()

    def _load_number_enabled_config(self, number_region, enabled):
        """加载数字识别区域启用状态配置
        Args:
            number_region: 数字识别区域配置
            enabled: 是否启用
        """
        number_region['enabled'].set(enabled)
        region_frame = number_region['frame']
        self.update_group_style(region_frame, enabled)

    def _load_number_region_coordinates(self, number_region, region_config):
        """加载数字识别区域坐标配置
        Args:
            number_region: 数字识别区域配置
            region_config: 从配置文件读取的区域配置
        """
        if 'region' in region_config and region_config['region'] is not None:
            try:
                region = tuple(region_config['region'])
                number_region['region'] = region
                number_region['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
            except (TypeError, ValueError):
                self.logging_manager.log_message(f"配置文件中的数字识别区域格式错误: {region_config['region']}")

    def _load_number_config(self, config):
        """加载数字识别配置"""
        number_config = config.get('number_recognition', {})
        regions = self.config_manager.get_config_value(number_config, 'regions', [])

        if isinstance(regions, list):
            self._clear_number_regions()

            # 根据配置重新创建所有数字识别区域
            for i, region_config in enumerate(regions):
                if isinstance(region_config, dict):
                    self.create_number_region(i)
                    # 设置区域配置
                    if i < len(self.number_regions):
                        for key, value in region_config.items():
                            if key in self.number_regions[i]:
                                if key == 'region' and value is not None:
                                    try:
                                        region = tuple(value)
                                        self.number_regions[i][key] = region
                                        self.number_regions[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                                    except (TypeError, ValueError):
                                        self.logging_manager.log_message(f"配置文件中的数字识别区域格式错误: {value}")
                                elif hasattr(self.number_regions[i][key], 'set'):
                                    self.number_regions[i][key].set(value)

            # 如果没有配置，至少创建一个数字识别区域
            if len(self.number_regions) == 0:
                self.create_number_region(0)

    def _load_alarm_config(self, config):
        """
        加载报警配置
        Args:
            config: 配置字典
        """
        alarm_config = self.config_manager.get_config_value(config, 'alarm', {})

        # 加载全局报警声音
        if 'sound' in alarm_config:
            self.alarm_sound_path.set(alarm_config['sound'])

        # 加载报警音量
        if 'volume' in alarm_config:
            self.alarm_volume.set(alarm_config['volume'])
            self.alarm_volume_str.set(str(alarm_config['volume']))

        # 加载各模块报警开关状态
        for module in ["ocr", "timed", "number"]:
            module_config = alarm_config.get(module, {})
            if 'enabled' in module_config:
                self.alarm_enabled[module].set(module_config['enabled'])

    def _load_shortcuts_config(self, config):
        """加载快捷键配置"""
        shortcuts_config = self.config_manager.get_config_value(config, 'shortcuts', {})
        if hasattr(self, 'start_shortcut_var') and 'start' in shortcuts_config:
            self.start_shortcut_var.set(shortcuts_config['start'])
        if hasattr(self, 'stop_shortcut_var') and 'stop' in shortcuts_config:
            self.stop_shortcut_var.set(shortcuts_config['stop'])

    def _load_home_checkboxes_config(self, config):
        """加载首页勾选框配置"""
        if 'home_checkboxes' in config and hasattr(self, 'module_check_vars'):
            home_checkboxes = config['home_checkboxes']
            if home_checkboxes:
                for module in ['ocr', 'timed', 'number']:
                    if module in home_checkboxes:
                        self.module_check_vars[module].set(home_checkboxes[module])

    def _load_script_config(self, config):
        """加载脚本和颜色识别配置"""
        script_config = self.config_manager.get_config_value(config, 'script', {})

        # 加载脚本内容
        if 'script_content' in script_config and hasattr(self, 'script_text'):
            script_content = script_config['script_content']
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(1.0, script_content)

        # 加载颜色识别命令内容
        if 'color_commands' in script_config and hasattr(self, 'color_commands_text'):
            color_commands_content = script_config['color_commands']
            self.color_commands_text.delete(1.0, tk.END)
            self.color_commands_text.insert(1.0, color_commands_content)

        # 加载颜色识别区域
        if 'color_recognition_region' in script_config and script_config['color_recognition_region']:
            color_recognition_region = script_config['color_recognition_region']
            if hasattr(self, 'region_var'):
                try:
                    x1, y1, x2, y2 = color_recognition_region
                    self.region_var.set(f"({x1}, {y1}) - ({x2}, {y2})")
                    # 同时更新实际使用的属性
                    self.color_recognition_region = color_recognition_region
                except (TypeError, ValueError):
                    self.logging_manager.log_message(f"配置文件中的颜色识别区域格式错误: {color_recognition_region}")

        # 加载目标颜色
        if 'target_color' in script_config and script_config['target_color']:
            target_color = script_config['target_color']
            if hasattr(self, 'color_var'):
                try:
                    r, g, b = target_color
                    self.color_var.set(f"RGB({r}, {g}, {b})")
                    if hasattr(self, 'color_display'):
                        self.color_display.config(background=f"#{r:02x}{g:02x}{b:02x}")
                    # 同时更新实际使用的属性
                    self.target_color = target_color
                except (TypeError, ValueError):
                    self.logging_manager.log_message(f"配置文件中的目标颜色格式错误: {target_color}")

        # 加载颜色容差
        if 'color_tolerance' in script_config and hasattr(self, 'tolerance_var'):
            color_tolerance = script_config['color_tolerance']
            self.tolerance_var.set(color_tolerance)

        # 加载检查间隔
        if 'color_interval' in script_config and hasattr(self, 'interval_var'):
            color_interval = script_config['color_interval']
            self.interval_var.set(color_interval)

        # 加载颜色识别启用状态
        if 'color_recognition_enabled' in script_config and hasattr(self, 'color_recognition_enabled'):
            color_recognition_enabled = script_config['color_recognition_enabled']
            self.color_recognition_enabled.set(color_recognition_enabled)

    def load_config(self):
        """
        加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        确保加载所有前端设置，包括新增功能的相关配置
        支持新旧配置格式的兼容处理
        
        Returns:
            bool: 如果配置加载成功则返回True，否则返回False
        """
        # 初始化配置加载结果
        config_loaded = False
        config_version = '1.0.0'
        config = None

        # 使用配置管理器读取配置文件
        config = self.config_manager.read_config()

        # 如果成功读取配置文件，则加载配置
        if config:
            config_loaded, config_version = self._process_config(config)

        # 更新配置文件版本号（如果与当前版本不一致）
        if config_loaded and config:
            self._update_config_version(config, config_version)

        # 无论配置是否加载成功，都更新界面中的Tesseract路径变量
        self._update_tesseract_path_var()

        return config_loaded

    def _process_config(self, config):
        """
        处理配置数据
        Args:
            config: 配置字典
        
        Returns:
            tuple: (config_loaded, config_version)，其中config_loaded是布尔值，config_version是配置版本字符串
        """
        try:
            # 获取配置版本，默认为1.0.0
            config_version = self.config_manager.get_config_value(config, 'version', '1.0.0')
            self.logging_manager.log_message(f"配置版本: {config_version}")

            # 加载各部分配置
            self._load_tesseract_config(config)
            self._load_ocr_config(config)
            self._load_click_config(config)
            self._load_timed_config(config)
            self._load_number_config(config)
            self._load_alarm_config(config)
            self._load_shortcuts_config(config)
            self._load_home_checkboxes_config(config)
            self._load_script_config(config)

            # 更新界面控件状态
            # 移除不存在的方法调用

            self.logging_manager.log_message("配置加载成功")
            return True, config_version
        except Exception as e:
            self.logging_manager.log_message(f"处理配置时发生错误: {str(e)}")
            return False, '1.0.0'

    def _update_config_version(self, config, config_version):
        """
        更新配置文件版本号
        Args:
            config: 配置字典
            config_version: 当前配置版本
        """
        if config_version != VERSION:
            self.logging_manager.log_message(f"配置版本更新: {config_version} → {VERSION}")
            # 更新配置版本并保存
            config['version'] = VERSION
            config['last_save_time'] = datetime.datetime.now().isoformat()
            try:
                with open(self.config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception as e:
                self.logging_manager.log_message(f"更新配置版本失败: {str(e)}")

    def _update_tesseract_path_var(self):
        """
        更新界面中的Tesseract路径变量
        """
        if hasattr(self, 'tesseract_path_var'):
            self.tesseract_path_var.set(self.tesseract_path)

    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        # 通用的延迟保存函数，避免频繁保存
        def delayed_save(*args):
            self.root.after(1000, self.save_config)

        # 即时保存函数
        def immediate_save(*args):
            self._defer_save_config()

        # 定时任务配置监听器
        def setup_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)

        # 为所有现有定时组添加监听器
        for group in self.timed_groups:
            setup_group_listeners(group)

        # 保存监听器函数，以便后续新增定时组时使用
        self._setup_group_listeners = setup_group_listeners

        # 数字识别配置监听器
        def setup_region_listeners(region_config):
            region_config["enabled"].trace_add("write", immediate_save)
            region_config["threshold"].trace_add("write", delayed_save)
            region_config["key"].trace_add("write", immediate_save)

        # 为所有现有区域添加监听器
        for region_config in self.number_regions:
            setup_region_listeners(region_config)

        # 保存监听器函数，以便后续新增区域时使用
        self._setup_region_listeners = setup_region_listeners

        #  OCR组配置监听器
        def setup_ocr_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["pause"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)
            group["delay_min"].trace_add("write", delayed_save)
            group["delay_max"].trace_add("write", delayed_save)
            group["alarm"].trace_add("write", immediate_save)
            group["keywords"].trace_add("write", delayed_save)
            group["language"].trace_add("write", immediate_save)
            group["click"].trace_add("write", immediate_save)

        # 为所有现有OCR组添加监听器
        for group in self.ocr_groups:
            setup_ocr_group_listeners(group)

        # 保存监听器函数，以便后续新增OCR组时使用
        self._setup_ocr_group_listeners = setup_ocr_group_listeners

        # 首页模块勾选状态监听器
        if hasattr(self, 'module_check_vars'):
            for module, var in self.module_check_vars.items():
                var.trace_add("write", immediate_save)

        # 快捷键配置监听器
        self.start_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))
        self.stop_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))

        # 脚本和颜色识别配置监听器
        # 为脚本文本框添加内容变化监听器
        if hasattr(self, 'script_text'):
            def on_script_change(event):
                if self.script_text.edit_modified():
                    delayed_save()
                    self.script_text.edit_modified(False)
            self.script_text.bind("<<Modified>>", on_script_change)
            self.script_text.edit_modified(False)

        # 为颜色识别命令文本框添加内容变化监听器
        if hasattr(self, 'color_commands_text'):
            def on_color_commands_change(event):
                if self.color_commands_text.edit_modified():
                    delayed_save()
                    self.color_commands_text.edit_modified(False)
            self.color_commands_text.bind("<<Modified>>", on_color_commands_change)
            self.color_commands_text.edit_modified(False)

        # 为颜色识别启用状态添加监听器
        if hasattr(self, 'color_recognition_enabled'):
            self.color_recognition_enabled.trace_add("write", immediate_save)

        # 为颜色容差添加监听器
        if hasattr(self, 'tolerance_var'):
            self.tolerance_var.trace_add("write", delayed_save)

        # 为检查间隔添加监听器
        if hasattr(self, 'interval_var'):
            self.interval_var.trace_add("write", delayed_save)

    def _stop_old_listener(self):
        """停止旧的全局键盘监听器（如果存在）"""
        # 停止pynput监听器
        if hasattr(self, 'global_listener') and self.global_listener:
            try:
                self.global_listener.stop()
                self.logging_manager.log_message("旧的全局键盘监听器已停止")
            except Exception as e:
                self.logging_manager.log_message(f"停止旧的全局键盘监听器时出错: {str(e)}")

    def _get_key_name(self, key):
        """获取按键名称
        Args:
            key: 按键对象
        
        Returns:
            str: 按键名称
        """
        if hasattr(key, 'name'):
            # 普通按键
            return key.name.upper()
        elif hasattr(key, 'char') and key.char:
            # 字符按键
            return key.char.upper()
        elif hasattr(key, 'vk'):
            # 特殊按键（F键等）
            if 112 <= key.vk <= 123:  # VK_F1=112, VK_F12=123
                return f"F{key.vk - 111}"  # F1=112-111=1, 依此类推
            else:
                return str(key)
        else:
            return str(key)

    def _handle_global_key_press(self, key):
        """处理全局按键事件
        Args:
            key: 按键对象
        """
        try:
            key_name = self._get_key_name(key)

            # 检查是否是开始快捷键
            if key_name == self.start_shortcut_var.get().upper() and not self.is_running:
                self.root.after(0, self.start_all)
            # 检查是否是结束快捷键
            if key_name == self.stop_shortcut_var.get().upper() and self.is_running:
                self.root.after(0, self.stop_all)
            # 检查是否是录制快捷键
            if key_name == self.record_hotkey_var.get().upper():
                self.root.after(0, lambda: (
                    self.start_recording() if not hasattr(self, 'script_executor') or not getattr(self.script_executor, 'is_recording', False) else self.stop_recording()
                ))
        except Exception as e:
            self.logging_manager.log_message(f"全局快捷键处理错误: {str(e)}")

    def _setup_global_shortcuts(self):
        """设置全局快捷键"""
        # 其他平台使用pynput
        if PYINPUT_AVAILABLE:
            try:
                # 创建并启动全局键盘监听器
                self.global_listener = keyboard.Listener(on_press=self._handle_global_key_press)
                self.global_listener.start()
                self.logging_manager.log_message("全局快捷键监听已启动 (使用pynput)")
                return True
            except Exception as e:
                self.logging_manager.log_message(f"pynput全局快捷键设置失败: {str(e)}")
        return False



    def setup_shortcuts(self):
        """设置快捷键绑定"""
        # 停止旧的全局键盘监听器（如果存在）
        self._stop_old_listener()

        # 只使用全局快捷键
        if self._setup_global_shortcuts():
            self.logging_manager.log_message("全局快捷键设置成功")
        else:
            self.logging_manager.log_message("全局快捷键设置失败，快捷键功能将不可用")

    def clear_log(self):
        """清除日志"""
        # 清除首页的日志文本框
        if hasattr(self, 'home_log_text'):
            self.home_log_text.config(state=tk.NORMAL)
            self.home_log_text.delete("1.0", tk.END)
            self.home_log_text.config(state=tk.DISABLED)

        self.logging_manager.log_message("已清除日志")

    def set_tesseract_path(self):
        """设置Tesseract OCR路径"""
        new_path = self.tesseract_path_var.get().strip()

        if not new_path:
            messagebox.showwarning("警告", "请输入有效的Tesseract路径！")
            return

        if not os.path.exists(new_path):
            messagebox.showwarning("警告", "指定的路径不存在！")
            return

        # 根据操作系统检查可执行文件格式
        if self.platform_adapter.platform == "Windows":
            if not new_path.endswith("tesseract.exe"):
                messagebox.showwarning("警告", "请指定tesseract.exe可执行文件！")
                return
        elif self.platform_adapter.platform == "Darwin":  # macOS
            if not os.path.basename(new_path) == "tesseract":
                messagebox.showwarning("警告", "请指定tesseract可执行文件！")
                return

        try:
            # 测试新路径是否可用
            subprocess.run(
                [new_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )

            # 更新路径和配置
            self.tesseract_path = new_path
            pytesseract.pytesseract.tesseract_cmd = new_path
            self.tesseract_available = True

            self.logging_manager.log_message(f"已设置Tesseract路径: {new_path}")
            self.status_var.set("就绪")
            messagebox.showinfo("成功", "Tesseract路径设置成功！")

            # 保存配置
            self._defer_save_config()

        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showwarning("警告", "无法使用指定的Tesseract路径！")
            return





    def start_monitoring(self):
        """开始监控"""
        if not self.tesseract_available:
            messagebox.showinfo("提示", "Tesseract OCR引擎未配置，请在设置中配置Tesseract路径后使用文字识别功能！")
            return

        # 检查是否有启用的OCR组且已选择区域
        has_enabled_group = False
        for group in self.ocr_groups:
            if group["enabled"].get() and group["region"]:
                has_enabled_group = True
                break

        if not has_enabled_group:
            messagebox.showwarning("警告", "请至少启用一个识别组并选择区域")
            return

        with self.state_lock:
            self.is_running = True
            self.is_paused = False

        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 运行中")
        self.logging_manager.log_message("开始监控...")

        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self.ocr_module.ocr_loop, daemon=True)
        self.ocr_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        with self.state_lock:
            self.is_running = False

        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 未运行")

    def _calculate_min_interval(self):
        """计算所有启用组的最小间隔时间
        Returns:
            int: 最小间隔时间
        """
        enabled_groups = [group for group in self.ocr_groups if group["enabled"].get()]
        if enabled_groups:
            return min(group["interval"].get() for group in enabled_groups)
        return 5

    def _wait_for_interval(self, interval):
        """等待设定的间隔时间
        Args:
            interval: 间隔时间（秒）
        """
        for _ in range(interval):
            with self.state_lock:
                if not self.is_running:
                    break
            time.sleep(1)

    def _should_process_group(self, group, i, current_time):
        """检查是否应该处理指定的OCR组
        Args:
            group: OCR组配置
            i: 组索引
            current_time: 当前时间

        Returns:
            bool: 是否应该处理
        """
        # 检查组是否启用且已选择区域
        if not group["enabled"].get() or not group["region"]:
            return False

        # 获取组配置
        pause_duration = group["pause"].get()
        group_interval = group["interval"].get()

        # 检查是否在暂停期（触发动作后）
        if current_time - self.last_trigger_times[i] < pause_duration:
            return False

        # 检查是否达到识别间隔
        if current_time - self.last_recognition_times[i] < group_interval:
            return False

        return True

    def perform_ocr_for_group_optimized(self, group, group_index, last_hashes, frame_counts):
        """
        为单个OCR组执行OCR识别（优化版本，使用增量截图和自适应帧率）
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
            last_hashes: 上次图像哈希缓存
            frame_counts: 帧计数
        """
        try:
            # 检查是否正在运行
            with self.state_lock:
                if not self.is_running:
                    return

            # 验证输入参数
            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            # 验证区域坐标
            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            # 截取屏幕区域
            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return

            # 计算图像哈希，用于检测画面变化
            import imagehash
            current_hash = imagehash.average_hash(screenshot.resize((64, 64)))
            
            # 检查画面是否变化，避免重复OCR
            if current_hash == last_hashes.get(group_index) and frame_counts.get(group_index, 0) % 5 != 0:
                # 画面未变化，跳过OCR（节省80%+ CPU）
                frame_counts[group_index] += 1
                return
            
            # 更新哈希缓存
            last_hashes[group_index] = current_hash
            frame_counts[group_index] += 1

            # 开始计时，用于自适应帧率
            start_time = time.time()

            # 图像预处理
            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                return

            # OCR识别
            text = self._perform_ocr(processed_image, current_lang, group_index)
            if not text:
                return

            # 计算OCR耗时
            elapsed_time = time.time() - start_time
            
            # 自适应帧率：根据OCR耗时调整延迟
            # 目标10 FPS，根据实际耗时调整睡眠时间
            sleep_time = max(0.01, 0.1 - elapsed_time)
            time.sleep(sleep_time)

            self.logging_manager.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}' (耗时: {elapsed_time:.2f}s, 延迟: {sleep_time:.2f}s)")

            # 检查是否包含关键词
            lower_text = text.lower()
            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                if any(keyword in lower_text for keyword in keywords):
                    # 确定点击位置
                    if click_enabled:
                        click_pos = self._find_keyword_position(processed_image, keywords, current_lang, left, top, right, bottom, group_index)
                    else:
                        # 未启用点击，使用区域中心
                        click_pos = ((left + right) // 2, (top + bottom) // 2)

                    # 触发动作，传递文字位置
                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)

        except Exception as e:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")

    def _validate_trigger_input(self, group, group_index):
        """
        验证触发动作的输入参数
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, key, delay_min, delay_max, alarm_enabled, region)
        """
        if not group:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None, None

        # 获取组配置
        key = group.get("key", tk.StringVar(value="")).get()
        delay_min = group.get("delay_min", tk.IntVar(value=300)).get()
        delay_max = group.get("delay_max", tk.IntVar(value=500)).get()
        alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
        region = group.get("region")

        # 验证必要参数
        if not key:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置触发按键")
            return False, None, None, None, None, None

        # 验证延迟参数
        if delay_min < 0 or delay_max < delay_min:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 延迟参数无效")
            delay_min = 300
            delay_max = 500

        return True, key, delay_min, delay_max, alarm_enabled, region

    def _calculate_click_position(self, click_pos, region, group_index):
        """
        计算点击位置
        Args:
            click_pos: 点击位置坐标
            region: 区域坐标
            group_index: OCR组索引

        Returns:
            tuple: (click_x, click_y)
        """
        if click_pos is not None:
            return click_pos

        if not region:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置识别区域，无法计算点击位置")
            return None, None

        try:
            # 计算点击位置（区域中心）
            x1, y1, x2, y2 = region
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
            return click_x, click_y
        except (ValueError, TypeError) as e:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return None, None

    def _handle_error(self, func, *args, **kwargs):
        """
        处理函数执行错误的通用方法
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 关键字参数
        Returns:
            函数执行结果，出错时返回None
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 获取调用信息
            import traceback
            caller_frame = traceback.extract_stack()[-3]
            caller_func = caller_frame.name
            
            # 构造错误信息
            error_msg = f"{caller_func}错误: {str(e)}"
            self.logging_manager.log_message(error_msg)
            self.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            return None

    def _execute_mouse_click(self, click_x, click_y, group_index):
        """
        执行鼠标点击
        Args:
            click_x: 点击x坐标
            click_y: 点击y坐标
            group_index: OCR组索引
        """
        # 检查是否正在运行
        if not self.is_running or getattr(self, 'system_stopped', False):
            return

        if click_x is not None and click_y is not None:
            # 使用输入控制器执行鼠标点击操作
            self.input_controller.click(click_x, click_y)
            # 等待固定时间
            time.sleep(self.click_delay)

    def _defer_save_config(self):
        """
        延迟保存配置，避免频繁保存
        """
        if not hasattr(self, '_save_config_timer'):
            self._save_config_timer = None
        
        # 取消之前的定时器
        if self._save_config_timer:
            self.root.after_cancel(self._save_config_timer)
        
        # 设置新的定时器
        self._save_config_timer = self.root.after(1000, self.save_config)

    def _execute_key_press(self, key, delay, group_index):
        """
        执行按键操作
        Args:
            key: 按键
            delay: 延迟时间
            group_index: OCR组索引
        """
        # 检查是否正在运行
        if not self.is_running or getattr(self, 'system_stopped', False):
            return

        # 使用输入控制器执行按键操作
        self.input_controller.press_key(key, delay)

        # 更新该组的上次触发时间，进入暂停期
        self.last_trigger_times[group_index] = time.time()

    def _play_alarm_if_enabled(self, alarm_enabled, group_index):
        """
        播放报警声音（如果启用）
        Args:
            alarm_enabled: 是否启用报警
            group_index: OCR组索引
        """
        if alarm_enabled and PYGAME_AVAILABLE:
            try:
                self.play_alarm_sound()
            except Exception as e:
                self.logging_manager.log_message(f"识别组{group_index+1}错误: 播放报警声音失败 - {str(e)}")

    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None):
        """
        为单个OCR组触发动作
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
            click_enabled: 是否启用点击
            click_pos: 点击位置坐标
        """
        try:
            # 检查是否正在运行
            with self.state_lock:
                if not self.is_running or getattr(self, 'system_stopped', False):
                    return

            # 验证输入参数
            valid, key, delay_min, delay_max, alarm_enabled, region = self._validate_trigger_input(group, group_index)
            if not valid:
                return

            self.logging_manager.log_message(f"识别组{group_index+1}触发动作，按键: {key}")

            # 生成随机延迟
            delay = random.randint(delay_min, delay_max) / 1000.0

            # 如果启用点击，执行鼠标点击
            if click_enabled:
                click_x, click_y = self._calculate_click_position(click_pos, region, group_index)
                self._execute_mouse_click(click_x, click_y, group_index)

            # 执行按键操作
            self._execute_key_press(key, delay, group_index)
        except Exception as e:
            self.logging_manager.log_message(f"识别组{group_index+1}错误: 触发动作失败 - {str(e)}")
            import traceback
            self.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")

        # 播放报警声音（如果启用）
        if 'alarm_enabled' in locals():
            self._play_alarm_if_enabled(alarm_enabled, group_index)

    def _get_keywords_config(self):
        """获取关键词配置"""
        keywords_str = self.keywords_var.get().strip()
        current_keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
        if not current_keywords:
            current_keywords = self.custom_keywords  # 保留原有关键词作为备份

        # 更新内部关键词列表，确保一致性
        self.custom_keywords = current_keywords
        return current_keywords

    def _get_timed_config(self):
        """获取定时功能配置"""
        timed_groups_config = []
        for group in self.timed_groups:
            timed_groups_config.append({
                'enabled': group['enabled'].get(),
                'interval': group['interval'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'click_enabled': group['click_enabled'].get(),
                'position_x': group['position_x'].get(),
                'position_y': group['position_y'].get(),
                'position': group['position_var'].get()
            })
        return timed_groups_config

    def _get_number_config(self):
        """获取数字识别配置"""
        number_regions_config = []
        for region_config in self.number_regions:
            number_regions_config.append({
                'enabled': region_config['enabled'].get(),
                'region': list(region_config['region']) if region_config['region'] else None,
                'threshold': region_config['threshold'].get(),
                'key': region_config['key'].get(),
                'delay_min': region_config['delay_min'].get(),
                'delay_max': region_config['delay_max'].get()
            })
        return number_regions_config

    def _get_ocr_config(self):
        """获取OCR配置"""
        ocr_groups_config = []
        for group in self.ocr_groups:
            ocr_groups_config.append({
                'enabled': group['enabled'].get(),
                'region': list(group['region']) if group['region'] else None,
                'interval': group['interval'].get(),
                'pause': group['pause'].get(),
                'key': group['key'].get(),
                'delay_min': group['delay_min'].get(),
                'delay_max': group['delay_max'].get(),
                'alarm': group['alarm'].get(),
                'keywords': group['keywords'].get(),
                'language': group['language'].get(),
                'click': group['click'].get()
            })
        return {
            'groups': ocr_groups_config
        }

    def _get_tesseract_config(self):
        """获取Tesseract配置"""
        return {
            'path': self.tesseract_path
        }

    def _get_shortcuts_config(self):
        """获取快捷键配置"""
        return {
            'start': self.start_shortcut_var.get(),
            'stop': self.stop_shortcut_var.get()
        }

    def _get_alarm_config(self):
        """
        获取报警功能配置
        Returns:
            dict: 报警功能配置字典
        """
        return {
            'sound': self.alarm_sound_path.get(),
            'volume': self.alarm_volume.get(),
            'ocr': {
                'enabled': self.alarm_enabled['ocr'].get()
            },
            'timed': {
                'enabled': self.alarm_enabled['timed'].get()
            },
            'number': {
                'enabled': self.alarm_enabled['number'].get()
            }
        }

    def _get_home_checkboxes_config(self):
        """获取首页勾选框配置"""
        return {
            'ocr': self.module_check_vars['ocr'].get(),
            'timed': self.module_check_vars['timed'].get(),
            'number': self.module_check_vars['number'].get()
        }

    def _get_script_config(self):
        """获取脚本和颜色识别配置"""
        # 获取脚本内容
        script_content = ''
        if hasattr(self, 'script_text'):
            script_content = self.script_text.get(1.0, tk.END)
        
        # 获取颜色识别命令内容
        color_commands_content = ''
        if hasattr(self, 'color_commands_text'):
            color_commands_content = self.color_commands_text.get(1.0, tk.END)
        
        # 获取颜色识别区域
        color_recognition_region = None
        if hasattr(self, 'color_recognition_region'):
            color_recognition_region = self.color_recognition_region
        
        # 获取目标颜色
        target_color = None
        if hasattr(self, 'target_color'):
            target_color = self.target_color
        
        # 获取颜色容差
        color_tolerance = 10
        if hasattr(self, 'tolerance_var'):
            color_tolerance = self.tolerance_var.get()
        
        # 获取检查间隔
        color_interval = 1.0
        if hasattr(self, 'interval_var'):
            color_interval = self.interval_var.get()
        
        # 获取颜色识别启用状态
        color_recognition_enabled = False
        if hasattr(self, 'color_recognition_enabled'):
            color_recognition_enabled = self.color_recognition_enabled.get()
        
        return {
            'script_content': script_content,
            'color_commands': color_commands_content,
            'color_recognition_region': color_recognition_region,
            'target_color': target_color,
            'color_tolerance': color_tolerance,
            'color_interval': color_interval,
            'color_recognition_enabled': color_recognition_enabled
        }

    def _check_macos_permissions(self):
        """检查macOS权限（异步版本）"""
        self.logging_manager.log_message("开始检查系统权限...")
        
        # 显示进度提示
        self.show_progress("正在检查系统权限...")
        
        def check_in_thread():
            """在后台线程中执行权限检查"""
            # 使用平台适配器检查权限
            has_permissions = self.platform_adapter.check_permissions()
            
            # 通过after()回调主线程更新UI
            self.root.after(0, lambda: self._on_permissions_checked(has_permissions, has_permissions))
        
        # 启动后台线程执行权限检查
        threading.Thread(target=check_in_thread, daemon=True).start()
    
    def _on_permissions_checked(self, has_accessibility, has_screen_capture):
        """权限检查完成后的回调处理"""
        # 隐藏进度提示
        self.hide_progress()
        
        # 检查权限结果
        if not has_accessibility or not has_screen_capture:
            self._guide_permission_setup(has_accessibility, has_screen_capture)
        
        self.logging_manager.log_message("macOS权限检查完成")
    
    def _guide_permission_setup(self, has_accessibility, has_screen_capture):
        """引导用户设置权限"""
        if not has_accessibility:
            self._guide_accessibility_setup()
        if not has_screen_capture:
            self._guide_screen_recording_setup()
    
    def show_progress(self, message):
        """显示进度提示"""
        # 更新状态栏
        self.status_var.set(message)
        # 强制更新UI
        self.root.update_idletasks()
    
    def hide_progress(self):
        """隐藏进度提示"""
        # 恢复状态栏
        self.status_var.set("就绪")
        # 强制更新UI
        self.root.update_idletasks()

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
            from PIL import ImageGrab
            import numpy as np
            
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

    def _check_permissions_async(self, callback=None):
        """异步权限检查（不阻塞 UI）"""
        def check_in_thread():
            has_accessibility = self._check_accessibility_permission_sync()
            has_screen_capture = self._check_screen_recording_permission_sync()
            
            # 通过 after() 回调主线程
            self.root.after(0, lambda: self._on_permissions_checked(
                has_accessibility, has_screen_capture, callback
            ))
        
        # 显示进度指示器
        self.logging_manager.log_message("🔍 检查系统权限...")
        
        # 启动后台线程
        threading.Thread(target=check_in_thread, daemon=True).start()

    def _on_permissions_checked(self, has_accessibility, has_screen_capture, callback=None):
        """权限检查完成后的回调"""
        self.logging_manager.log_message(f"权限检查结果 - 辅助功能: {'✅' if has_accessibility else '❌'}, 屏幕录制: {'✅' if has_screen_capture else '❌'}")
        
        if not has_accessibility:
            self._guide_accessibility_setup()
        
        if not has_screen_capture:
            self._guide_screen_recording_setup()
        
        if callback:
            callback(has_accessibility and has_screen_capture)

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
        
        self.show_message(
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
        
        self.show_message(
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

    def show_message(self, title, message, buttons=None):
        """显示带按钮的消息框"""
        if buttons is None:
            messagebox.showinfo(title, message)
            return
        
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 计算位置，使对话框居中显示
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        dialog_width = 400
        dialog_height = 250
        pos_x = root_x + (root_width // 2) - (dialog_width // 2)
        pos_y = root_y + (root_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{pos_x}+{pos_y}")
        
        # 添加内容
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=message, wraplength=360).pack(pady=(0, 20))
        
        # 添加按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=lambda c=command, d=dialog: (c() if c else None, d.destroy())).pack(side=tk.LEFT, padx=(0, 10))
        color_tolerance = 10
        color_interval = 1.0
        color_recognition_enabled = False

        # 获取脚本内容
        if hasattr(self, 'script_text'):
            script_content = self.script_text.get(1.0, tk.END)

        # 获取颜色识别命令内容
        if hasattr(self, 'color_commands_text'):
            color_commands_content = self.color_commands_text.get(1.0, tk.END)

        # 获取颜色识别区域
        if hasattr(self, 'region_var'):
            # 从region_var中解析区域信息
            region_text = self.region_var.get()
            import re
            match = re.search(r'\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)', region_text)
            if match:
                try:
                    color_recognition_region = [
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3)),
                        int(match.group(4))
                    ]
                except (ValueError, IndexError):
                    pass

        # 获取目标颜色
        if hasattr(self, 'color_var'):
            # 从color_var中解析颜色信息
            color_text = self.color_var.get()
            match = re.search(r'RGB\((\d+),\s*(\d+),\s*(\d+)\)', color_text)
            if match:
                try:
                    target_color = [
                        int(match.group(1)),
                        int(match.group(2)),
                        int(match.group(3))
                    ]
                except (ValueError, IndexError):
                    pass

        # 获取颜色容差
        if hasattr(self, 'tolerance_var'):
            color_tolerance = self.tolerance_var.get()

        # 获取检查间隔
        if hasattr(self, 'interval_var'):
            color_interval = self.interval_var.get()

        # 获取颜色识别启用状态
        if hasattr(self, 'color_recognition_enabled'):
            color_recognition_enabled = self.color_recognition_enabled.get()

        return {
            'script_content': script_content,
            'color_commands': color_commands_content,
            'color_recognition_region': color_recognition_region,
            'target_color': target_color,
            'color_tolerance': color_tolerance,
            'color_interval': color_interval,
            'color_recognition_enabled': color_recognition_enabled
        }

    def save_config(self):
        """
        保存配置
        保存所有前端用户设置，包括新增功能的相关配置
        确保数据结构完整、一致，并处理边界情况
        """
        try:
            # 使用配置管理器获取完整的配置数据结构
            config = self.config_manager.get_full_config()

            # 使用配置管理器保存配置
            self.config_manager.save_config(config)

        except Exception as e:
            self.logging_manager.log_message(f"配置保存错误: {str(e)}")

    def start_number_recognition(self):
        """开始数字识别"""
        def start_func():
            start_count = 0
            for i, region_config in enumerate(self.number_regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    threshold = region_config["threshold"].get()
                    key = region_config["key"].get()
                    # 创建线程并存储
                    thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key), daemon=True)
                    self.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.start_module("number", start_func)

    def stop_number_recognition(self):
        """停止数字识别"""
        # 清空线程列表
        if self.number_threads:
            self.number_threads.clear()
        # 更新状态标签
        if "number" in self.status_labels:
            self.status_labels["number"].set("数字识别: 未运行")
    
    def stop_timed_tasks(self):
        """停止定时功能"""
        self.timed_module.stop_timed_tasks()
    
    def start_module(self, module_name, start_func):
        """统一启动模块
        Args:
            module_name: 模块名称
            start_func: 启动函数
        """
        if module_name in self.MODULES:
            config = self.MODULES[module_name]
            stop_func = getattr(self, config["stop_func"])
            label = config["label"]
            self.thread_manager.start(module_name, start_func, stop_func, label)
        else:
            self.logging_manager.log_message(f"未知模块: {module_name}")

    def _toggle_ui_state(self, root_widget, state):
        """递归地禁用或启用根控件及其所有子控件
        Args:
            root_widget: 根控件
            state: 控件状态，"disabled" 或 "normal"
        """
        # 跳过停止运行按钮，始终保持可用
        if root_widget == self.global_stop_btn:
            return

        try:
            # 尝试设置控件状态
            root_widget.configure(state=state)
        except (tk.TclError, AttributeError):
            # 某些控件（如Frame）没有state属性，跳过
            pass

        # 递归处理所有子控件
        for child in root_widget.winfo_children():
            self._toggle_ui_state(child, state)

    def start_all(self):
        """开始运行"""
        self.logging_manager.log_message("开始运行")

        # 重置系统完全停止标志
        self.system_stopped = False

        # 禁用首页的功能状态勾选框
        for button in self.module_check_buttons.values():
            button.configure(state="disabled")

        # 禁用开始运行按钮
        self.global_start_btn.configure(state="disabled")

        # 禁用所有其他UI控件
        for child in self.root.winfo_children():
            self._toggle_ui_state(child, "disabled")

        # 确保停止运行按钮可用
        self.global_stop_btn.configure(state="normal")

        # 开始勾选的功能
        if self.module_check_vars["ocr"].get():
            self.start_monitoring()

        if self.module_check_vars["timed"].get():
            self.timed_module.start_timed_tasks()

        if self.module_check_vars["number"].get():
            self.number_module.start_number_recognition()

        if self.module_check_vars["script"].get():
            # 启动脚本
            self.start_script()

        # 播放开始运行的音频
        self.alarm_module.play_start_sound()
        
        # 设置运行状态
        with self.state_lock:
            self.is_running = True

    def stop_all(self):
        """停止运行"""
        self.logging_manager.log_message("停止运行")

        # 设置系统完全停止标志，阻止任何外部命令唤醒
        self.system_stopped = True

        # 停止运行
        self.stop_monitoring()
        self.timed_module.stop_timed_tasks()
        self.number_module.stop_number_recognition()
        
        # 停止脚本（不在这里停止颜色识别，留到下面统一处理）
        self.stop_script(stop_color_recognition=False)
        
        # 停止颜色识别 - 无论color_recognition_enabled状态如何，都停止颜色识别线程
        if hasattr(self, 'color_recognition'):
            # 检查线程是否正在运行
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread is not None and self.color_recognition.recognition_thread.is_alive():
                # 如果is_running为False但是线程仍然在运行，强制停止
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)

        # 清空事件队列
        self.event_manager.clear_events()

        # 播放停止运行的反向音频
        self.alarm_module.play_stop_sound()

        # 启用首页的功能状态勾选框
        for button in self.module_check_buttons.values():
            button.configure(state="normal")

        # 启用开始运行按钮
        self.global_start_btn.configure(state="normal")

        # 启用所有其他UI控件
        for child in self.root.winfo_children():
            self._toggle_ui_state(child, "normal")

        # 确保开始运行按钮可用
        self.global_start_btn.configure(state="normal")
        
        # 禁用停止运行按钮，因为系统已经停止
        self.global_stop_btn.configure(state="disabled")
        
        # 设置停止状态
        with self.state_lock:
            self.is_running = False

    def number_recognition_loop(self, region_index, region, threshold, key):
        """数字识别循环"""
        current_thread = threading.current_thread()

        # 检查线程是否在number_threads列表中，以及数字识别区域是否启用
        while current_thread in self.number_threads and self.number_regions[region_index]["enabled"].get():
            with self.state_lock:
                if not self.is_running:
                    break
            try:
                time.sleep(1)  # 1秒间隔

                # 截图并识别数字
                screenshot = self.take_screenshot(region)
                text = self.ocr_number(screenshot)
                number = self.parse_number(text)
                if number is not None:
                    self.logging_manager.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        # 播放数字识别模块报警声音
                        self.alarm_module.play_alarm_sound(self.number_regions[region_index]["alarm"])

                        # 只有当数字小于阈值且按键不为空时才执行按键操作
                        if key:
                            self.event_manager.add_event(('keypress', key), ('number', region_index))
                            self.logging_manager.log_message(f"数字识别{region_index+1}触发按键: {key}")
                        else:
                            self.logging_manager.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
                else:
                    # 识别失败时，输出原始识别结果
                    self.logging_manager.log_message(f"数字识别{region_index+1}结果: '{text}'")
            except Exception as e:
                self.logging_manager.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)

    def parse_number(self, text):
        """解析数字，支持X/Y格式
        只在识别失败时输出详细日志
        """
        # 移除可能的空格和换行符
        text = text.strip()
        if not text:
            return None

        # 检查缓存
        cache_key = text.lower()
        if cache_key in self._number_cache:
            return self._number_cache[cache_key]

        number = None
        try:
            # 策略1: X/Y格式（"123/456" → 123）
            import re
            match = re.search(r'^\s*(\d+)[/\s]', text)
            if match:
                number = int(match.group(1))
            else:
                # 策略2: 独立数字（"HP: 123" → 123）
                match = re.search(r'\b(\d+)\b', text)
                if match:
                    number = int(match.group(1))
                else:
                    # 策略3: 所有数字字符（"abc123def" → 123）
                    digits = ''.join(filter(str.isdigit, text))
                    if digits:
                        number = int(digits[:10])  # 限制长度防溢出
        except Exception as e:
            self.logging_manager.log_message(f"数字识别解析错误: {str(e)}")
            number = None

        # 缓存结果
        if number is not None:
            self._number_cache[cache_key] = number

        return number

    def take_screenshot(self, region):
        """截取指定区域的屏幕"""
        # 检查屏幕录制权限（macOS）
        if self.platform_adapter.platform == "Darwin":
            permission_manager = PermissionManager(self)
            if not permission_manager.check_screen_recording():
                # 在主线程中显示权限引导
                self.root.after(0, lambda: self._guide_screen_recording_setup())
                return None
        
        x1, y1, x2, y2 = region
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        try:
            return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        except Exception as e:
            self.logging_manager.log_message(f"数字识别错误: 屏幕截图失败 - {str(e)}")
            return None

    def ocr_number(self, image):
        """识别数字，支持X/Y格式
        简化图像预处理，保留字符白名单以避免'ee'错误识别
        """
        image = image.convert('L')
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(image, lang='eng', config=config)

        # 4. 额外的文本清理，移除可能的换行符和空格
        text = text.strip().replace('\n', '').replace('\r', '')

        return text

    def select_alarm_sound(self):
        """选择全局报警声音文件
        """
        filetypes = [
            ("音频文件", "*.mp3 *.wav *.ogg *.flac"),
            ("所有文件", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="选择全局报警声音",
            filetypes=filetypes
        )

        if filename:
            self.alarm_sound_path.set(filename)
            self.logging_manager.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")
            self.save_config()

    def update_child_styles(self, widget, is_enabled):
        """递归更新所有子组件样式
        Args:
            widget: 要更新样式的组件
            is_enabled: 组件是否启用
        """
        # 组件样式映射
        style_mappings = {
            ttk.Frame: lambda: "Green.TFrame" if is_enabled else "TFrame",
            ttk.Button: lambda: "Green.TButton" if is_enabled else "TButton",
            ttk.Checkbutton: lambda: "Green.TCheckbutton" if is_enabled else "TCheckbutton",
            ttk.Combobox: lambda: "Green.TCombobox" if is_enabled else "TCombobox",
            ttk.Entry: lambda: "TEntry",  # 始终使用默认样式，不随组启用状态变化
            ttk.LabelFrame: lambda: "Green.TLabelframe" if is_enabled else "TLabelframe"
        }

        # 特殊处理Label组件
        if isinstance(widget, ttk.Label):
            # 检查是否为显示按键的标签（有sunken relief）
            if widget.cget("relief") != "sunken":
                widget.configure(style="Green.TLabel" if is_enabled else "TLabel")
        # 处理其他组件类型
        else:
            for widget_type, style_func in style_mappings.items():
                if isinstance(widget, widget_type):
                    widget.configure(style=style_func())
                    break

        # 递归处理所有子组件
        for child in widget.winfo_children():
            self.update_child_styles(child, is_enabled)

    def update_group_style(self, group_frame, enabled):
        """更新组样式
        Args:
            group_frame: 要更新样式的组框架
            enabled: 组是否启用
        """
        # 更新当前框架样式
        if enabled:
            group_frame.configure(style="Green.TLabelframe")
        else:
            group_frame.configure(style="TLabelframe")

        # 递归更新所有子组件样式
        self.update_child_styles(group_frame, enabled)

    def _create_group_frame(self, parent_frame, index, group_type):
        """创建组框架"""
        group_frame = ttk.LabelFrame(parent_frame, text=f"{group_type}{index+1}", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        group_frame.configure(relief=tk.GROOVE, borderwidth=2)
        return group_frame

    def _setup_group_click_handler(self, group_frame, enabled_var):
        """
        设置组点击事件处理器
        Args:
            group_frame: 组框架
            enabled_var: 启用状态变量
        """
        # 点击事件处理函数
        def on_group_click(event):
            # 检查点击事件是否来自输入控件
            if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                return  # 输入控件事件不处理

            # 切换启用状态
            new_state = not enabled_var.get()
            enabled_var.set(new_state)
            
            # 记录点击事件日志，包括平台信息
            frame_text = group_frame.cget("text")
            self.logging_manager.log_message(f"[{self.platform_adapter.platform}] 点击{frame_text}，状态切换为{'启用' if new_state else '禁用'}")

            # 根据启用状态调整样式
            update_group_style(new_state)

        # 使用类方法更新组样式
        def update_group_style(enabled):
            self.update_group_style(group_frame, enabled)

        # 为enabled变量添加trace监听，当状态变化时自动更新样式
        enabled_var.trace_add("write", lambda *args: update_group_style(enabled_var.get()))

        # 绑定点击事件到框架及其子组件
        group_frame.bind("<Button-1>", on_group_click)

        # 为组框架的标签绑定点击事件（针对macOS）
        if hasattr(group_frame, 'label'):
            group_frame.label.bind("<Button-1>", on_group_click)

        # 为子组件绑定事件
        def bind_child_events(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                    # 输入控件保持原有功能
                    pass
                else:
                    # 其他组件继续绑定点击事件
                    child.bind("<Button-1>", on_group_click)
                    bind_child_events(child)

        bind_child_events(group_frame)

        # 针对macOS的特殊处理：设置组框架的边框区域可点击
        group_frame.configure(cursor="hand2")  # 设置鼠标悬停时的光标
        # 确保组框架有足够的padding，使得边框区域可见且可点击
        group_frame.configure(padding="12")

    def exit_program(self):
        """退出程序"""
        # 停止所有运行中的任务
        if self.is_running:
            self.stop_monitoring()
        self.timed_module.stop_timed_tasks()
        self.number_module.stop_number_recognition()

        # 停止脚本执行
        if hasattr(self, 'script_executor') and self.script_executor.is_running:
            self.script_executor.stop_script()

        # 停止颜色识别
        if hasattr(self, 'color_recognition') and self.color_recognition.is_running:
            self.color_recognition.stop_recognition()

        # 停止全局键盘监听器
        if hasattr(self, 'global_listener') and self.global_listener:
            self.global_listener.stop()

        # 停止事件线程
        self.is_event_running = False
        
        # 退出程序
        self.logging_manager.log_message("程序正在退出...")
        self.root.quit()
        self.root.destroy()

    def show_message(self, title, message):
        """显示消息对话框
        Args:
            title: 对话框标题
            message: 对话框内容
        """
        messagebox.showinfo(title, message)

    def run(self):
        """运行程序"""
        self.root.mainloop()

    def create_script_tab(self, parent):
        """创建脚本运行标签页"""
        create_script_tab(parent, self)

    def start_script(self, start_color_recognition=True):
        """从首页启动脚本
        
        Args:
            start_color_recognition: 是否同时启动颜色识别线程，默认值为True
        """
        # 检查系统是否已完全停止，如果是则拒绝启动脚本
        if self.system_stopped:
            self.logging_manager.log_message("系统已完全停止，拒绝执行StartScript命令")
            return
        
        if not hasattr(self, 'script_executor'):
            self.script_executor = ScriptExecutor(self)
        
        # 获取脚本内容
        if hasattr(self, 'script_text'):
            script_content = self.script_text.get(1.0, tk.END)
            if not script_content.strip():
                messagebox.showwarning("警告", "脚本内容为空，请先编写脚本！")
                return
            
            self.script_executor.run_script(script_content)
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 运行中")
            self.status_var.set("脚本执行中...")
            self.logging_manager.log_message("脚本已启动")
        
        # 根据参数决定是否启动颜色识别
        if start_color_recognition and hasattr(self, 'color_recognition_enabled') and self.color_recognition_enabled.get():
            self.start_color_recognition()
            self.logging_manager.log_message("颜色识别已自动启动")

    def stop_script(self, stop_color_recognition=True):
        """停止脚本执行
        
        Args:
            stop_color_recognition: 是否同时停止颜色识别线程，默认值为True
        """
        if hasattr(self, 'script_executor') and hasattr(self.script_executor, 'is_running') and self.script_executor.is_running:
            self.script_executor.stop_script()
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 未运行")
            self.status_var.set("脚本已停止")
        
        # 根据参数决定是否停止颜色识别
        if stop_color_recognition:
            # 无论color_recognition_enabled状态如何，都停止颜色识别线程
            self.stop_color_recognition()

    def start_recording(self):
        """开始录制脚本"""
        if not hasattr(self, 'script_executor'):
            self.script_executor = ScriptExecutor(self)
        
        self.script_executor.start_recording()
        if hasattr(self, 'record_btn'):
            self.record_btn.config(text="录制中...", state="disabled")
        if hasattr(self, 'stop_record_btn'):
            self.stop_record_btn.config(state="normal")
        if hasattr(self, 'status_labels') and "script" in self.status_labels:
            self.status_labels["script"].set("脚本运行: 录制中")
        self.status_var.set("录制中...")
        # 播放开始运行音效
        self.alarm_module.play_start_sound()

    def stop_recording(self):
        """停止录制脚本"""
        if hasattr(self, 'script_executor'):
            self.script_executor.stop_recording()
            if hasattr(self, 'record_btn'):
                self.record_btn.config(text="开始录制", state="normal")
            if hasattr(self, 'stop_record_btn'):
                self.stop_record_btn.config(state="disabled")
            if hasattr(self, 'status_labels') and "script" in self.status_labels:
                self.status_labels["script"].set("脚本运行: 未运行")
            self.status_var.set("录制已停止")
            # 播放停止运行音效
            self.alarm_module.play_stop_sound()

    def select_color_region(self):
        """选择颜色识别区域"""
        self.logging_manager.log_message("开始选择颜色识别区域...")
        # 使用通用的区域选择方法
        _start_selection(self, "color", 0)

    def select_color(self):
        """选择颜色"""
        self.logging_manager.log_message("开始选择目标颜色...")
        # 创建颜色选择窗口
        self.create_color_selection_window()

    def create_color_selection_window(self):
        """创建颜色选择窗口"""
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            
            # 计算整个虚拟屏幕的边界
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
            max_x = max(monitor.x + monitor.width for monitor in monitors)
            max_y = max(monitor.y + monitor.height for monitor in monitors)
        except ImportError:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        except Exception as e:
            # 如果获取显示器信息失败，使用默认值
            min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
        
        # 创建覆盖整个虚拟屏幕的选择窗口
        self.color_selection_window = tk.Toplevel(self.root)
        # 移除窗口装饰，确保窗口能够覆盖整个屏幕，包括顶部区域
        self.color_selection_window.overrideredirect(True)
        self.color_selection_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
        self.color_selection_window.attributes("-alpha", 0.3)
        self.color_selection_window.attributes("-topmost", True)
        self.color_selection_window.config(cursor="crosshair")
        
        # 创建画布
        self.color_canvas = tk.Canvas(self.color_selection_window, bg="white", highlightthickness=0)
        self.color_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.color_canvas.bind("<Button-1>", self.on_color_select)
        
        # 绑定ESC键退出选择
        self.color_selection_window.bind("<Escape>", lambda e: self.color_selection_window.destroy())

    def on_color_select(self, event):
        """处理颜色选择事件"""
        # 先隐藏选择窗口，避免捕获到蒙版
        self.color_selection_window.withdraw()
        
        # 等待窗口隐藏
        self.color_selection_window.update()
        
        # 获取鼠标在屏幕上的实际位置，使用event.x_root和event.y_root获取绝对坐标
        abs_x, abs_y = event.x_root, event.y_root
        
        # 截取屏幕像素，使用all_screens=True确保捕获所有屏幕
        screen = ImageGrab.grab(all_screens=True)
        
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            min_x = min(monitor.x for monitor in monitors)
            min_y = min(monitor.y for monitor in monitors)
        except:
            min_x, min_y = 0, 0
        
        # 将绝对坐标转换为截图内的相对坐标
        rel_x = abs_x - min_x
        rel_y = abs_y - min_y
        
        # 获取像素颜色
        pixel = screen.getpixel((rel_x, rel_y))
        
        # 保存目标颜色
        self.target_color = pixel
        r, g, b = pixel
        self.color_var.set(f"RGB({r}, {g}, {b})")
        self.logging_manager.log_message(f"选择颜色: RGB({r}, {g}, {b})")
        self.logging_manager.log_message(f"选择位置: ({abs_x}, {abs_y})")
        
        # 更新颜色显示槽
        self.color_display.config(background=f"#{r:02x}{g:02x}{b:02x}")
        
        # 关闭选择窗口
        self.color_selection_window.destroy()

    def start_color_recognition(self):
        """开始颜色识别"""
        if not hasattr(self, 'color_recognition'):
            self.color_recognition = ColorRecognition(self)
        
        # 获取设置参数
        try:
            # 从目标颜色变量获取颜色值
            if hasattr(self, 'target_color') and self.target_color:
                target_color = self.target_color
            else:
                messagebox.showwarning("警告", "请先选择目标颜色！")
                return
            
            tolerance = int(self.tolerance_var.get())
            interval = float(self.interval_var.get())
            commands = self.color_commands_text.get(1.0, tk.END)
        except ValueError:
            messagebox.showwarning("警告", "颜色设置参数格式错误，请检查！")
            return
        
        # 检查区域是否已选择
        if not hasattr(self, 'color_recognition_region') or not self.color_recognition_region:
            messagebox.showwarning("警告", "请先选择颜色识别区域！")
            return
        
        # 设置颜色识别区域
        self.color_recognition.set_region(self.color_recognition_region)
        
        # 启动颜色识别
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)
        self.status_var.set("颜色识别中...")

    def stop_color_recognition(self):
        """停止颜色识别"""
        if hasattr(self, 'color_recognition'):
            # 检查线程是否正在运行
            if hasattr(self.color_recognition, 'is_running') and self.color_recognition.is_running:
                self.color_recognition.stop_recognition()
                self.status_var.set("颜色识别已停止")
            elif hasattr(self.color_recognition, 'recognition_thread') and self.color_recognition.recognition_thread.is_alive():
                # 如果is_running为False但是线程仍然在运行，强制停止
                self.color_recognition.is_running = False
                self.color_recognition.recognition_thread.join(timeout=2)
                self.status_var.set("颜色识别已停止")
                
def main():
    """主函数，用于命令行调用"""
    app = AutoDoorOCR()
    app.run()

if __name__ == "__main__":
    main()