import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pyautogui
import pytesseract
from PIL import Image, ImageGrab
import threading
import time
import random
import datetime
import subprocess
import os
import sys
import json
import platform
from collections import deque

# 导入pynput用于全局键盘监听
try:
    from pynput import keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    PYINPUT_AVAILABLE = False

# 导入pygame用于音频播放
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# 全局版本号配置
VERSION = "1.4.1"

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class AutoDoorOCR:
    def __init__(self):
        # 禁用PyAutoGUI的故障安全机制，防止鼠标移动到屏幕角落时触发异常
        pyautogui.FAILSAFE = False
        
        self.root = tk.Tk()
        self.root.title(f"AutoDoor OCR 识别系统 v{VERSION}")
        self.root.geometry("800x850")  # 增加默认高度
        self.root.resizable(True, True) 
        self.root.minsize(750, 800)  # 增加最小高度
        
        # 配置参数
        self.ocr_interval = 5
        self.pause_duration = 180
        self.click_delay = 0.5
        self.custom_key = "equal"
        
        # 关键词配置
        self.custom_keywords = ["men", "door"]
        self.ocr_language = "eng"
        
        # 坐标轴参数
        self.click_x = 0 
        self.click_y = 0
        self.click_mode = "center"
        
        # 状态变量
        self.selected_region = None
        self.is_running = False
        self.is_paused = False
        self.is_selecting = False
        self.last_trigger_time = 0
        
        # 用于OCR组的触发时间跟踪
        self.last_recognition_times = {}  # 用于识别间隔
        self.last_trigger_times = {}  # 用于暂停期
        
        # 配置文件路径 - 使用系统标准配置目录
        app_name = "AutoDoorOCR"
        
        # 根据不同操作系统选择配置文件目录
        if platform.system() == "Windows":
            # Windows: 使用APPDATA环境变量
            config_dir = os.path.join(os.environ.get("APPDATA"), app_name)
        elif platform.system() == "Darwin":
            # macOS: 使用Library/Preferences目录
            config_dir = os.path.join(os.path.expanduser("~"), "Library", "Preferences", app_name)
        else:
            # 其他系统: 回退到程序运行目录
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
        
        # 确保配置目录存在
        os.makedirs(config_dir, exist_ok=True)
        
        # 配置文件路径
        self.config_file = os.path.join(config_dir, "autodoor_config.json")
        
        # 日志文件路径 - 也放在配置目录下
        self.log_file = os.path.join(config_dir, "autodoor.log")
        
        # 线程控制
        self.ocr_thread = None
        self.timed_threads = []
        self.number_threads = []
        
        # 事件队列
        self.event_queue = deque()
        self.event_lock = threading.Lock()
        self.event_cond = threading.Condition(self.event_lock)
        self.is_event_running = False
        self.event_thread = None
        
        # 定时功能相关
        self.timed_enabled_var = None
        self.timed_groups = []
        
        # 数字识别相关
        self.number_enabled_var = None
        self.number_regions = []
        self.current_number_region = None
        
        # 初始化Tesseract相关变量
        self.tesseract_path = ""
        self.tesseract_available = False
        
        # 报警功能相关
        self.alarm_enabled = {}
        self.alarm_sound = tk.StringVar(value="")  # 全局报警声音
        self.alarm_volume = tk.IntVar(value=70)  # 全局报警音量，默认70%
        self.alarm_volume_str = tk.StringVar(value="70")  # 用于显示的音量字符串
        
        # 初始化报警配置
        for module in ["ocr", "timed", "number"]:
            self.alarm_enabled[module] = tk.BooleanVar(value=False)
        
        # 按键延迟配置 - 文字识别模块
        self.ocr_delay_min = tk.IntVar(value=300)
        self.ocr_delay_max = tk.IntVar(value=500)
        
        # OCR组管理相关变量
        self.ocr_groups = []
        self.current_ocr_region = None
        
        # 先创建界面元素，确保所有UI变量都被初始化
        self.create_widgets()
        
        # 加载配置（包括Tesseract路径和报警设置）
        self.load_config()
        
        # 如果配置中没有Tesseract路径，使用项目自带的tesseract
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = self.get_default_tesseract_path()
            config_updated = True
        
        # 如果配置中没有报警声音路径，使用项目自带的alarm.mp3
        if not self.alarm_sound.get():
            self.alarm_sound.set(self.get_default_alarm_sound_path())
            config_updated = True
        
        # 执行Tesseract引擎的存在性检测和可用性验证
        self.tesseract_available = self.check_tesseract_availability()
        
        # 如果使用了默认Tesseract路径，将其保存到配置文件
        if config_updated:
            self.save_config()
        
        # 检查tesseract可用性
        if not self.tesseract_available:
            messagebox.showwarning("警告", "未检测到Tesseract OCR引擎，请先安装并配置环境变量！")
            self.status_var.set("Tesseract未安装")
        
        # 设置配置监听器
        self.setup_config_listeners()
        
        # 设置快捷键绑定
        self.setup_shortcuts()
        
        # 移除全局鼠标滚轮事件处理，让每个标签页自己处理滚动事件
        
        # 启动事件处理线程
        self.start_event_thread()
    

    
    def get_default_tesseract_path(self):
        """获取默认的Tesseract路径，使用项目自带的tesseract
        支持Windows和Mac平台，同时支持打包后的环境
        """
        
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))
        
        # 根据操作系统选择不同的tesseract路径
        tesseract_path = ""
        if platform.system() == "Windows":
            # Windows平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract.exe")
        elif platform.system() == "Darwin":
            # macOS平台
            # 检查可能的路径 - 针对.app包结构优化
            possible_paths = [
                os.path.join(app_root, "tesseract", "tesseract"),  # 主要路径
                os.path.join(app_root, "tesseract"),  # 备选路径
                os.path.join(os.path.dirname(app_root), "tesseract", "tesseract"),  # 应用包外部路径
                # 针对.app包结构的额外路径
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract", "tesseract"),
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    tesseract_path = path
                    break
        else:
            # 其他平台，返回空
            tesseract_path = ""
        
        self.log_message(f"默认Tesseract路径: {tesseract_path}")
        return tesseract_path
    
    def get_default_alarm_sound_path(self):
        """获取默认的报警声音路径，使用项目自带的alarm.mp3
        支持Windows和Mac平台，同时支持打包后的环境
        """
        
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))
        
        # 构建跨平台的报警声音路径
        alarm_path = os.path.join(app_root, "voice", "alarm.mp3")
        
        # 确保路径格式正确
        alarm_path = os.path.normpath(alarm_path)
        
        self.log_message(f"默认报警声音路径: {alarm_path}")
        return alarm_path
    
    def check_tesseract_availability(self):
        """检查Tesseract OCR是否可用
        包括：路径有效性验证、版本兼容性检查、基础功能测试
        """
        if not self.tesseract_path:
            self.log_message("Tesseract路径未配置")
            return False
        
        # 1. 路径有效性验证
        if not os.path.exists(self.tesseract_path):
            self.log_message(f"Tesseract路径不存在: {self.tesseract_path}")
            return False
        
        if not os.path.isfile(self.tesseract_path):
            self.log_message(f"Tesseract路径不是文件: {self.tesseract_path}")
            return False
        
        # 根据操作系统检查可执行文件格式和权限
        if platform.system() == "Windows":
            if not self.tesseract_path.endswith("tesseract.exe"):
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False
        elif platform.system() == "Darwin":  # macOS
            if not os.path.basename(self.tesseract_path) == "tesseract":
                self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
                return False
            
            # 检查并修复macOS上的执行权限
            if not os.access(self.tesseract_path, os.X_OK):
                self.log_message(f"Tesseract文件缺少执行权限，尝试修复: {self.tesseract_path}")
                try:
                    # 尝试添加执行权限
                    subprocess.run(["chmod", "+x", self.tesseract_path], 
                                  capture_output=True, check=True, timeout=5)
                    self.log_message("成功添加执行权限")
                except Exception as e:
                    self.log_message(f"添加执行权限失败: {str(e)}")
                    return False
        # 其他平台不做严格检查
        
        try:
            # 2. 版本兼容性检查
            version_result = subprocess.run(
                [self.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            
            # 解析版本信息
            version_output = version_result.stdout.strip()
            if "tesseract" in version_output.lower():
                # 提取版本号，格式类似 "tesseract 5.3.3"
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    self.log_message(f"检测到Tesseract版本: {version_str}")
                    
                    # 检查主要版本号，确保至少是4.x
                    try:
                        # 移除版本号开头的'v'字符（如果存在）
                        cleaned_version = version_str.lstrip('v')
                        major_version = int(cleaned_version.split('.')[0])
                        if major_version < 4:
                            self.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        self.log_message(f"无法解析Tesseract版本: {version_str}")
                        # 继续执行，不因为版本解析失败而直接返回False
            
            # 3. 基础功能测试 - 在macOS上添加更安全的处理
            # 配置pytesseract使用找到的路径
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            # 在macOS上，确保测试文件保存在可写位置
            test_file_path = 'test_tesseract.png'
            if platform.system() == "Darwin":
                # 在macOS上，使用用户主目录或临时目录保存测试文件
                test_file_path = os.path.join(os.path.expanduser("~"), "test_tesseract.png")
            
            # 创建一个简单的测试图像
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save(test_file_path)
            
            # 尝试执行OCR识别
            test_result = pytesseract.image_to_string(test_file_path, lang='eng', timeout=5)
            
            # 清理测试文件
            if os.path.exists(test_file_path):
                try:
                    os.remove(test_file_path)
                except Exception as e:
                    self.log_message(f"清理测试文件失败: {str(e)}")
            
            # 配置界面中的路径变量
            if hasattr(self, 'tesseract_path_var'):
                self.tesseract_path_var.set(self.tesseract_path)
            
            self.log_message("Tesseract OCR引擎检测通过")
            return True
            
        except subprocess.TimeoutExpired:
            self.log_message(f"Tesseract命令执行超时: {self.tesseract_path}")
            return False
        except subprocess.CalledProcessError as e:
            self.log_message(f"Tesseract命令执行失败: {e}")
            return False
        except FileNotFoundError:
            self.log_message(f"Tesseract可执行文件未找到: {self.tesseract_path}")
            return False
        except pytesseract.TesseractError as e:
            self.log_message(f"Tesseract OCR测试失败: {e}")
            return False
        except PermissionError as e:
            self.log_message(f"Tesseract权限错误: {str(e)}")
            # 在macOS上，权限错误可能是由于安全机制导致，返回False但不崩溃
            return False
        except Exception as e:
            self.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            # 在macOS上，未知错误也应该返回False而不是崩溃
            return False
        
    def create_widgets(self):
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
        style.configure("Green.TLabelframe", background=green_bg_color, borderwidth=2, relief=tk.SOLID)
        style.configure("Green.TLabelframe.Label", foreground="green", font=("Arial", 10, "bold"), background=green_bg_color)
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
        
        # 基本设置标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        self.create_basic_tab(basic_frame)
        
        # 日志功能已迁移到首页，删除独立的日志标签页
        
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
        
        # 工具介绍按钮（左侧），与退出按钮保持20px间距
        tool_intro_btn = ttk.Button(buttons_frame, text="工具介绍", command=open_tool_intro)
        tool_intro_btn.pack(side=tk.RIGHT, padx=(0, 20))
    
    def open_bilibili(self):
        """打开Bilibili主页"""
        import webbrowser
        webbrowser.open("https://space.bilibili.com/263150759")
    
    def create_ocr_tab(self, parent):
        """创建文字识别标签页"""
        ocr_frame = ttk.Frame(parent, padding="10")
        ocr_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮栏
        top_frame = ttk.Frame(ocr_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 新增组按钮
        self.add_ocr_group_btn = ttk.Button(top_frame, text="新增识别组", command=self.add_ocr_group)
        self.add_ocr_group_btn.pack(side=tk.LEFT)
        
        # 识别组容器，带滚动条
        groups_container = ttk.Frame(ocr_frame)
        groups_container.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        groups_scrollbar = ttk.Scrollbar(groups_container, orient=tk.VERTICAL)
        groups_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 画布，用于实现滚动
        groups_canvas = tk.Canvas(groups_container, yscrollcommand=groups_scrollbar.set, highlightthickness=0)
        groups_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        groups_scrollbar.config(command=groups_canvas.yview)
        
        # 内部容器，用于放置所有识别组
        self.ocr_groups_frame = ttk.Frame(groups_canvas)
        groups_canvas.create_window((0, 0), window=self.ocr_groups_frame, anchor="nw", tags="inner_frame")
        
        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, groups_canvas, "inner_frame")
        
        groups_canvas.bind("<Configure>", configure_scroll_region)
        self.ocr_groups_frame.bind("<Configure>", configure_scroll_region)
        
        # 为画布绑定鼠标滚轮事件
        groups_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 为内部框架绑定鼠标滚轮事件
        self.ocr_groups_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 为整个标签页绑定鼠标滚轮事件
        ocr_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 保存文字识别的画布和框架引用
        self.ocr_canvas = groups_canvas
        self.ocr_frame = ocr_frame
        self.ocr_groups_container = groups_container
        
        # 区域配置
        self.ocr_groups = []
        for i in range(2):
            self.create_ocr_group(i)
        
        # 绑定所有文字识别区域的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in self.ocr_groups])
    
    def create_ocr_group(self, index):
        """创建单个文字识别组"""
        # 创建识别组框架，移除名称前的空格，使用默认样式
        group_frame = ttk.LabelFrame(self.ocr_groups_frame, text=f"识别组{index+1}", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 设置初始边框样式
        group_frame.configure(relief=tk.GROOVE, borderwidth=2)
        
        # 定义背景色变量，用于样式设置
        bg_color = "#f0f0f0"
        
        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)
        
        # 点击事件处理函数
        def on_group_click(event):
            # 检查点击事件是否来自输入控件
            if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                return  # 输入控件事件不处理
            
            # 切换启用状态
            enabled_var.set(not enabled_var.get())
            
            # 根据启用状态调整样式
            update_group_style(enabled_var.get())
        
        # 使用类方法更新组样式
        def update_group_style(enabled):
            self.update_group_style(group_frame, enabled)
        
        # 为enabled变量添加trace监听，当状态变化时自动更新样式
        enabled_var.trace_add("write", lambda *args: update_group_style(enabled_var.get()))
        
        # 绑定点击事件到框架及其子组件
        group_frame.bind("<Button-1>", on_group_click)
        
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
        
        # 初始应用样式
        update_group_style(enabled_var.get())
        
        # 第一行：区域选择、区域坐标、删除按钮
        row1_frame = ttk.Frame(group_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 区域选择和区域坐标
        select_btn = ttk.Button(row1_frame, text="选择区域", command=lambda idx=index: self.start_ocr_region_selection(idx))
        select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(row1_frame, textvariable=region_var, width=25)
        region_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_ocr_group(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第二行：间隔(秒)、暂停时长（秒）、触发按键、按键时长、启用报警
        row2_frame = ttk.Frame(group_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 间隔(秒)输入框 - 水平排列
        ttk.Label(row2_frame, text="间隔(秒):", width=10).pack(side=tk.LEFT, padx=(0, 5))
        interval_var = tk.IntVar(value=5)
        ttk.Entry(row2_frame, textvariable=interval_var, width=6).pack(side=tk.LEFT, padx=(0, 10))
        
        # 暂停时长（秒）输入框 - 水平排列
        ttk.Label(row2_frame, text="暂停时长(秒):", width=12).pack(side=tk.LEFT, padx=(0, 5))
        pause_var = tk.IntVar(value=180)
        ttk.Entry(row2_frame, textvariable=pause_var, width=6).pack(side=tk.LEFT, padx=(0, 10))
        
        # 触发按键选择器 - 水平排列
        ttk.Label(row2_frame, text="按键:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        key_var = tk.StringVar(value="equal")
        key_label = ttk.Label(row2_frame, textvariable=key_var, relief="sunken", padding=2, width=8)
        key_label.pack(side=tk.LEFT, padx=(0, 5))
        set_key_btn = ttk.Button(row2_frame, text="修改", width=6)
        set_key_btn.pack(side=tk.LEFT, padx=(0, 10))
        set_key_btn.config(command=lambda v=key_var, b=set_key_btn: self.start_key_listening(v, b))
        
        # 按键时长设置框 - 水平排列
        ttk.Label(row2_frame, text="按键时长:", width=10).pack(side=tk.LEFT, padx=(0, 5))
        delay_min_var = tk.IntVar(value=300)
        delay_max_var = tk.IntVar(value=500)
        
        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False
        
        delay_min_entry = ttk.Entry(row2_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))
        ttk.Label(row2_frame, text=" - ", width=2).pack(side=tk.LEFT)
        delay_max_entry = ttk.Entry(row2_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))
        ttk.Label(row2_frame, text="ms", width=3).pack(side=tk.LEFT, padx=(0, 10))
        
        # 启用报警复选框 - 水平排列
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(row2_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(0, 10))
        
        # 第三行：识别关键词、识别语言、是否点击识别文字
        row3_frame = ttk.Frame(group_frame)
        row3_frame.pack(fill=tk.X)
        
        # 识别关键词输入框 - 水平排列
        ttk.Label(row3_frame, text="识别关键词:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        keywords_var = tk.StringVar(value="men,door")
        ttk.Entry(row3_frame, textvariable=keywords_var, width=20).pack(side=tk.LEFT, padx=(0, 10))
        
        # 识别语言选择下拉菜单 - 水平排列
        ttk.Label(row3_frame, text="识别语言:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 5))
        language_var = tk.StringVar(value="eng")
        ttk.Combobox(row3_frame, textvariable=language_var, values=["eng", "chi_sim", "chi_tra"], width=12).pack(side=tk.LEFT, padx=(0, 10))
        
        # 是否点击识别文字复选框 - 水平排列
        click_var = tk.BooleanVar(value=True)
        click_switch = ttk.Checkbutton(row3_frame, text="点击识别文字", variable=click_var)
        click_switch.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存组配置
        group_config = {
            "frame": group_frame,
            "enabled": enabled_var,
            "region_var": region_var,
            "region": None,
            "interval": interval_var,
            "pause": pause_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var,
            "keywords": keywords_var,
            "language": language_var,
            "click": click_var
        }
        self.ocr_groups.append(group_config)
        
        # 为新创建的识别组添加配置监听器
        if hasattr(self, '_setup_ocr_group_listeners'):
            self._setup_ocr_group_listeners(group_config)
        
        # 为新创建的识别组绑定鼠标滚轮事件
        canvas = self.ocr_groups_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [group_frame])
    
    def add_ocr_group(self):
        """新增文字识别组"""
        if len(self.ocr_groups) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个识别组！")
            return
        
        self.create_ocr_group(len(self.ocr_groups))
        self.log_message(f"新增文字识别组{len(self.ocr_groups)}")
    
    def delete_ocr_group(self, index, confirm=True):
        """删除文字识别组"""
        if len(self.ocr_groups) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个识别组！")
            return
        
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除识别组{index+1}吗？"):
                return
        
        if 0 <= index < len(self.ocr_groups):
            self.ocr_groups[index]["frame"].destroy()
            del self.ocr_groups[index]
            self.renumber_ocr_groups()
            self.log_message(f"已删除文字识别组{index+1}")
    
    def renumber_ocr_groups(self):
        """重新编号所有文字识别组"""
        for i, group in enumerate(self.ocr_groups):
            # 保持组名称前的空格，确保布局一致
            group["frame"].configure(text=f"  识别组{i+1}")
    
    def start_ocr_region_selection(self, index):
        """开始选择OCR识别区域"""
        self._start_selection("ocr", index)
    
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
        timed_frame = ttk.Frame(parent, padding="10")
        timed_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮栏
        top_frame = ttk.Frame(timed_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 新增组按钮
        self.add_timed_group_btn = ttk.Button(top_frame, text="新增定时组", command=self.add_timed_group)
        self.add_timed_group_btn.pack(side=tk.LEFT)
        
        # 定时组容器，带滚动条
        groups_container = ttk.Frame(timed_frame)
        groups_container.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        groups_scrollbar = ttk.Scrollbar(groups_container, orient=tk.VERTICAL)
        groups_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 画布，用于实现滚动
        groups_canvas = tk.Canvas(groups_container, yscrollcommand=groups_scrollbar.set, highlightthickness=0)
        groups_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        groups_scrollbar.config(command=groups_canvas.yview)
        
        # 内部容器，用于放置所有定时组
        self.timed_groups_frame = ttk.Frame(groups_canvas)
        groups_canvas.create_window((0, 0), window=self.timed_groups_frame, anchor="nw", tags="inner_frame")
        
        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, groups_canvas, "inner_frame")
        
        groups_canvas.bind("<Configure>", configure_scroll_region)
        self.timed_groups_frame.bind("<Configure>", configure_scroll_region)
        
        # 为画布绑定鼠标滚轮事件
        groups_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 为内部框架绑定鼠标滚轮事件
        self.timed_groups_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 为整个标签页绑定鼠标滚轮事件
        timed_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, groups_canvas))
        
        # 保存定时功能的画布和框架引用
        self.timed_canvas = groups_canvas
        self.timed_frame = timed_frame
        self.timed_groups_container = groups_container
        
        # 定时组配置
        self.timed_groups = []
        for i in range(3):
            self.create_timed_group(i)
        
        # 绑定所有定时组的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in self.timed_groups])
        
        # 操作按钮已移除，统一由首页全局控制
    
    def create_timed_group(self, index):
        """创建单个定时组，所有UI元素布局在一行中"""
        # 创建定时组框架，移除名称前的空格，使用默认样式
        group_frame = ttk.LabelFrame(self.timed_groups_frame, text=f"定时组{index+1}", padding="10")
        group_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 设置初始边框样式
        group_frame.configure(relief=tk.GROOVE, borderwidth=2)
        
        # 定义背景色变量，用于样式设置
        bg_color = "#f0f0f0"
        
        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)
        
        # 点击事件处理函数
        def on_group_click(event):
            # 检查点击事件是否来自输入控件
            if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                return  # 输入控件事件不处理
            
            # 切换启用状态
            enabled_var.set(not enabled_var.get())
            
            # 根据启用状态调整样式
            update_group_style(enabled_var.get())
        
        # 使用类方法更新组样式
        def update_group_style(enabled):
            self.update_group_style(group_frame, enabled)
        
        # 为enabled变量添加trace监听，当状态变化时自动更新样式
        enabled_var.trace_add("write", lambda *args: update_group_style(enabled_var.get()))
        
        # 绑定点击事件到框架及其子组件
        group_frame.bind("<Button-1>", on_group_click)
        
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
        
        # 第一行：基本配置
        row1_frame = ttk.Frame(group_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 时间间隔
        interval_label = ttk.Label(row1_frame, text="间隔(秒):", width=10)
        interval_label.pack(side=tk.LEFT)
        
        interval_var = tk.IntVar(value=10*(index+1))
        interval_entry = ttk.Entry(row1_frame, textvariable=interval_var, width=6)  # 调整宽度为6，能显示4位整数
        interval_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 按键选择
        key_label = ttk.Label(row1_frame, text="按键:", width=5)
        key_label.pack(side=tk.LEFT)
        
        key_var = tk.StringVar(value=["space", "enter", "tab", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"][index % 15])
        
        # 显示当前按键的标签
        timed_current_key_label = ttk.Label(row1_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
        timed_current_key_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置按键按钮
        set_timed_key_btn = ttk.Button(row1_frame, text="修改按键", width=8)
        set_timed_key_btn.pack(side=tk.LEFT, padx=(0, 10))
        # 单独绑定事件，避免UnboundLocalError
        set_timed_key_btn.config(command=lambda v=key_var, b=set_timed_key_btn: self.start_key_listening(v, b))
        
        # 按键延迟配置
        delay_min_var = tk.IntVar(value=300)
        delay_max_var = tk.IntVar(value=500)
        
        # 添加"按键时长："文本
        ttk.Label(row1_frame, text="按键时长：").pack(side=tk.LEFT)
        
        # 延迟最小值输入框
        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False
        
        delay_min_entry = ttk.Entry(row1_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))
        
        # 失去焦点时的验证，确保值为正整数
        def validate_min_on_focusout(event):
            value = delay_min_var.get()
            if value <= 0:
                delay_min_var.set(300)
        delay_min_entry.bind("<FocusOut>", validate_min_on_focusout)
        
        ttk.Label(row1_frame, text=" - ", width=2).pack(side=tk.LEFT)
        
        delay_max_entry = ttk.Entry(row1_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))
        
        # 失去焦点时的验证，确保值为正整数且不小于最小值
        def validate_max_on_focusout(event):
            min_val = delay_min_var.get()
            max_val = delay_max_var.get()
            if max_val <= 0:
                delay_max_var.set(500)
            elif max_val < min_val:
                delay_max_var.set(min_val)
        delay_max_entry.bind("<FocusOut>", validate_max_on_focusout)
        
        ttk.Label(row1_frame, text="ms", width=3).pack(side=tk.LEFT, padx=(0, 10))
        
        # 报警开关 - 为每个定时组创建独立变量
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(row1_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧：删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_timed_group(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第二行：鼠标点击配置
        row2_frame = ttk.Frame(group_frame)
        row2_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 启用鼠标点击复选框
        click_enabled_var = tk.BooleanVar(value=False)
        click_enabled_switch = ttk.Checkbutton(row2_frame, text="启用鼠标点击", variable=click_enabled_var)
        click_enabled_switch.pack(side=tk.LEFT, padx=(0, 10))
        
        # 左侧：选择位置按钮
        select_pos_btn = ttk.Button(row2_frame, text="选择位置", width=8, command=lambda idx=index: self.start_timed_position_selection(idx))
        select_pos_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧：位置显示 - 移除边框和凹陷效果，与文字识别和数字识别的显示风格保持一致
        position_var = tk.StringVar(value="未选择位置")
        position_label = ttk.Label(row2_frame, textvariable=position_var, width=15, anchor=tk.W)
        position_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 保存组配置
        group_config = {
            "frame": group_frame,
            "enabled": enabled_var,
            "interval": interval_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var,
            "click_enabled": click_enabled_var,
            "position": position_var,
            "position_x": tk.IntVar(value=0),
            "position_y": tk.IntVar(value=0)
        }
        self.timed_groups.append(group_config)
        
        # 为新创建的定时组添加配置监听器
        if hasattr(self, '_setup_group_listeners'):
            self._setup_group_listeners(group_config)
        
        # 为新创建的定时组绑定鼠标滚轮事件
        # 获取当前标签页的画布
        canvas = self.timed_groups_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [group_frame])
    
    def delete_timed_group(self, index, confirm=True):
        """删除定时组
        
        Args:
            index: 要删除的定时组索引
            confirm: 是否显示确认对话框，默认为True
        """
        if len(self.timed_groups) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个定时组！")
            return
        
        # 只有在confirm为True时才显示确认对话框
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除定时组{index+1}吗？"):
                return
        
        # 检查索引是否有效，避免删除后索引过期导致的IndexError
        if 0 <= index < len(self.timed_groups):
            # 移除组框架
            self.timed_groups[index]["frame"].destroy()
            # 从列表中删除
            del self.timed_groups[index]
            # 重新编号所有定时组
            self.renumber_timed_groups()
            self.log_message(f"已删除定时组{index+1}")
    
    def renumber_timed_groups(self):
        """重新编号所有定时组"""
        for i, group in enumerate(self.timed_groups):
            # 保持组名称前的空格，确保布局一致
            group["frame"].configure(text=f"  定时组{i+1}")
    
    def add_timed_group(self):
        """新增定时组"""
        if len(self.timed_groups) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个定时组！")
            return
        
        self.create_timed_group(len(self.timed_groups))
        self.log_message(f"新增定时组{len(self.timed_groups)}")
        
    def create_number_tab(self, parent):
        """创建数字识别标签页"""
        number_frame = ttk.Frame(parent, padding="10")
        number_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部按钮栏
        top_frame = ttk.Frame(number_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 新增区域按钮
        self.add_number_region_btn = ttk.Button(top_frame, text="新增识别组", command=self.add_number_region)
        self.add_number_region_btn.pack(side=tk.LEFT)
        
        # 区域容器，带滚动条
        regions_container = ttk.Frame(number_frame)
        regions_container.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        regions_scrollbar = ttk.Scrollbar(regions_container, orient=tk.VERTICAL)
        regions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 画布，用于实现滚动
        regions_canvas = tk.Canvas(regions_container, yscrollcommand=regions_scrollbar.set, highlightthickness=0)
        regions_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        regions_scrollbar.config(command=regions_canvas.yview)
        
        # 内部容器，用于放置所有识别区域
        self.number_regions_frame = ttk.Frame(regions_canvas)
        regions_canvas.create_window((0, 0), window=self.number_regions_frame, anchor="nw", tags="inner_frame")
        
        # 配置画布尺寸和滚动区域
        def configure_scroll_region(event):
            self._configure_scroll_region(event, regions_canvas, "inner_frame")
        
        regions_canvas.bind("<Configure>", configure_scroll_region)
        self.number_regions_frame.bind("<Configure>", configure_scroll_region)
        
        # 为画布绑定鼠标滚轮事件
        regions_canvas.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))
        
        # 为内部框架绑定鼠标滚轮事件
        self.number_regions_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))
        
        # 为整个标签页绑定鼠标滚轮事件
        number_frame.bind("<MouseWheel>", lambda event: self._on_mousewheel(event, regions_canvas))
        
        # 保存数字识别的画布和框架引用
        self.number_canvas = regions_canvas
        self.number_frame = number_frame
        self.number_regions_container = regions_container
        
        # 区域配置
        self.number_regions = []
        for i in range(2):
            self.create_number_region(i)
        
        # 绑定所有数字识别区域的鼠标滚轮事件
        self._bind_mousewheel_to_widgets(regions_canvas, [region["frame"] for region in self.number_regions])
        
        # 操作按钮已移除，统一由首页全局控制
    
    def create_number_region(self, index):
        """创建单个数字识别区域"""
        # 创建识别组框架，移除名称前的空格，使用默认样式
        region_frame = ttk.LabelFrame(self.number_regions_frame, text=f"识别组{index+1}", padding="10")
        region_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 设置初始边框样式
        region_frame.configure(relief=tk.GROOVE, borderwidth=2)
        
        # 定义背景色变量，用于样式设置
        bg_color = "#f0f0f0"
        
        # 启用状态变量
        enabled_var = tk.BooleanVar(value=False)
        
        # 点击事件处理函数
        def on_group_click(event):
            # 检查点击事件是否来自输入控件
            if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                return  # 输入控件事件不处理
            
            # 切换启用状态
            enabled_var.set(not enabled_var.get())
            
            # 根据启用状态调整样式
            update_group_style(enabled_var.get())
        
        # 使用类方法更新组样式
        def update_group_style(enabled):
            self.update_group_style(region_frame, enabled)
        
        # 为enabled变量添加trace监听，当状态变化时自动更新样式
        enabled_var.trace_add("write", lambda *args: update_group_style(enabled_var.get()))
        
        # 绑定点击事件到框架及其子组件
        region_frame.bind("<Button-1>", on_group_click)
        
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
        
        bind_child_events(region_frame)
        
        # 初始应用样式
        update_group_style(enabled_var.get())
        
        # 第一行：区域选择、区域坐标、删除按钮
        row1_frame = ttk.Frame(region_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 中间：区域选择和区域坐标
        select_btn = ttk.Button(row1_frame, text="选择区域", command=lambda idx=index: self.start_number_region_selection(idx))
        select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(row1_frame, textvariable=region_var, width=25)  # 设置固定宽度
        region_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 右侧：删除按钮
        delete_btn = ttk.Button(row1_frame, text="删除", width=6, command=lambda idx=index: self.delete_number_region(idx))
        delete_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 第二行：阈值设置、按键设置、延迟配置、报警开关
        row2_frame = ttk.Frame(region_frame)
        row2_frame.pack(fill=tk.X)
        
        # 阈值设置
        threshold_label = ttk.Label(row2_frame, text="阈值:", width=5)  # 减小宽度
        threshold_label.pack(side=tk.LEFT)
        
        threshold_var = tk.IntVar(value=500 if index == 0 else 1000)
        threshold_entry = ttk.Entry(row2_frame, textvariable=threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 按键设置
        key_label = ttk.Label(row2_frame, text="按键:", width=5)
        key_label.pack(side=tk.LEFT)
        
        key_var = tk.StringVar(value=["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "space", "enter", "tab"][index % 15])
        
        # 按键配置区域
        number_key_config_frame = ttk.Frame(row2_frame)
        number_key_config_frame.pack(side=tk.LEFT)
        
        # 显示当前按键的标签
        number_current_key_label = ttk.Label(number_key_config_frame, textvariable=key_var, relief="sunken", padding=2, width=5)
        number_current_key_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # 设置按键按钮
        set_number_key_btn = ttk.Button(number_key_config_frame, text="修改按键", width=8)
        set_number_key_btn.pack(side=tk.LEFT)
        # 单独绑定事件，避免UnboundLocalError
        set_number_key_btn.config(command=lambda v=key_var, b=set_number_key_btn: self.start_key_listening(v, b))
        
        # 按键延迟配置
        delay_min_var = tk.IntVar(value=100)
        delay_max_var = tk.IntVar(value=200)
        
        delay_frame = ttk.Frame(number_key_config_frame)
        delay_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        # 添加"延迟："文本，确保使用全局字体样式
        ttk.Label(delay_frame, text="按键时长：").pack(side=tk.LEFT)
        
        # 延迟最小值输入框
        def validate_positive_int(P):
            if P == "":
                return True
            try:
                val = int(P)
                return val > 0
            except ValueError:
                return False
        
        delay_min_entry = ttk.Entry(delay_frame, textvariable=delay_min_var, width=5, validate="key")
        delay_min_entry.pack(side=tk.LEFT)
        delay_min_entry.configure(validatecommand=(delay_min_entry.register(validate_positive_int), '%P'))
        
        # 失去焦点时的验证，确保值为正整数
        def validate_min_on_focusout(event):
            value = delay_min_var.get()
            if value <= 0:
                delay_min_var.set(100)
        delay_min_entry.bind("<FocusOut>", validate_min_on_focusout)
        
        ttk.Label(delay_frame, text=" - ", width=2).pack(side=tk.LEFT)
        
        delay_max_entry = ttk.Entry(delay_frame, textvariable=delay_max_var, width=5, validate="key")
        delay_max_entry.pack(side=tk.LEFT)
        delay_max_entry.configure(validatecommand=(delay_max_entry.register(validate_positive_int), '%P'))
        
        # 失去焦点时的验证，确保值为正整数且不小于最小值
        def validate_max_on_focusout(event):
            min_val = delay_min_var.get()
            max_val = delay_max_var.get()
            if max_val <= 0:
                delay_max_var.set(200)
            elif max_val < min_val:
                delay_max_var.set(min_val)
        delay_max_entry.bind("<FocusOut>", validate_max_on_focusout)
        
        ttk.Label(delay_frame, text="ms", width=3).pack(side=tk.LEFT)
        
        # 报警开关 - 为每个数字识别区域创建独立变量
        alarm_var = tk.BooleanVar(value=False)
        alarm_switch = ttk.Checkbutton(number_key_config_frame, text="启用报警", variable=alarm_var)
        alarm_switch.pack(side=tk.LEFT, padx=(10, 0))
        
        # 保存区域配置
        region_config = {
            "frame": region_frame,
            "enabled": enabled_var,
            "region_var": region_var,
            "region": None,
            "threshold": threshold_var,
            "key": key_var,
            "delay_min": delay_min_var,
            "delay_max": delay_max_var,
            "alarm": alarm_var
        }
        self.number_regions.append(region_config)
        
        # 为新创建的数字识别区域添加配置监听器
        if hasattr(self, '_setup_region_listeners'):
            self._setup_region_listeners(region_config)
        
        # 为新创建的数字识别区域绑定鼠标滚轮事件
        # 获取当前标签页的画布
        canvas = self.number_regions_frame.master
        if isinstance(canvas, tk.Canvas):
            self._bind_mousewheel_to_widgets(canvas, [region_frame])
    
    def delete_number_region(self, index, confirm=True):
        """删除数字识别区域
        
        Args:
            index: 要删除的区域索引
            confirm: 是否显示确认对话框，默认为True
        """
        if len(self.number_regions) <= 1:
            messagebox.showwarning("警告", "至少需要保留一个识别区域！")
            return
        
        # 只有在confirm为True时才显示确认对话框
        if confirm:
            if not messagebox.askyesno("确认", f"确定要删除区域{index+1}吗？"):
                return
        
        # 检查索引是否有效，避免删除后索引过期导致的IndexError
        if 0 <= index < len(self.number_regions):
            # 移除区域框架
            self.number_regions[index]["frame"].destroy()
            # 从列表中删除
            del self.number_regions[index]
            # 重新编号所有区域
            self.renumber_number_regions()
            self.log_message(f"已删除识别组{index+1}")
    
    def renumber_number_regions(self):
        """重新编号所有数字识别区域"""
        for i, region in enumerate(self.number_regions):
            # 更新区域标题为"识别组"，保持名称前的空格
            region["frame"].configure(text=f"  识别组{i+1}")
    
    def add_number_region(self):
        """新增数字识别区域"""
        if len(self.number_regions) >= 15:
            messagebox.showwarning("警告", "最多只能创建15个识别区域！")
            return
        
        self.create_number_region(len(self.number_regions))
        self.log_message(f"新增识别区域{len(self.number_regions)}")
    
    def create_basic_tab(self, parent):
        """创建基本设置标签页"""
        # 基本设置区域
        basic_frame = ttk.Frame(parent, padding="10")
        basic_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tesseract配置
        tesseract_frame = ttk.LabelFrame(basic_frame, text="Tesseract配置", padding="10")
        tesseract_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tesseract路径
        path_label = ttk.Label(tesseract_frame, text="Tesseract路径:")
        path_label.pack(anchor=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(tesseract_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.tesseract_path_var = tk.StringVar(value=self.tesseract_path)
        self.tesseract_path_entry = ttk.Entry(path_frame, textvariable=self.tesseract_path_var)
        self.tesseract_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.set_path_btn = ttk.Button(path_frame, text="设置", command=self.set_tesseract_path)
        self.set_path_btn.pack(side=tk.RIGHT)
        
        # 坐标模式设置
        coord_frame = ttk.LabelFrame(basic_frame, text="坐标模式", padding="10")
        coord_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 点击模式选择
        mode_frame = ttk.Frame(coord_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.click_mode_var = tk.StringVar(value=self.click_mode)
        
        center_rbtn = ttk.Radiobutton(mode_frame, text="区域中心", variable=self.click_mode_var, value="center", command=self.update_axis_inputs)
        center_rbtn.pack(side=tk.LEFT, padx=(0, 15))
        
        custom_rbtn = ttk.Radiobutton(mode_frame, text="自定义坐标", variable=self.click_mode_var, value="custom", command=self.update_axis_inputs)
        custom_rbtn.pack(side=tk.LEFT)
        
        # 自定义坐标输入
        self.x_coord_var = tk.IntVar(value=self.click_x)
        self.y_coord_var = tk.IntVar(value=self.click_y)
        
        x_frame = ttk.Frame(coord_frame)
        x_frame.pack(fill=tk.X, pady=(0, 10))
        
        x_label = ttk.Label(x_frame, text="X轴坐标:", width=10)
        x_label.pack(side=tk.LEFT)
        
        self.x_coord_entry = ttk.Entry(x_frame, textvariable=self.x_coord_var, width=10, state="disabled")
        self.x_coord_entry.pack(side=tk.LEFT)
        
        y_frame = ttk.Frame(coord_frame)
        y_frame.pack(fill=tk.X)
        
        y_label = ttk.Label(y_frame, text="Y轴坐标:", width=10)
        y_label.pack(side=tk.LEFT)
        
        self.y_coord_entry = ttk.Entry(y_frame, textvariable=self.y_coord_var, width=10, state="disabled")
        self.y_coord_entry.pack(side=tk.LEFT)
        
        # 报警声音设置
        alarm_sound_frame = ttk.LabelFrame(basic_frame, text="报警声音设置", padding="10")
        alarm_sound_frame.pack(fill=tk.X, pady=(10, 10))
        
        # 报警声音文件选择
        sound_file_frame = ttk.Frame(alarm_sound_frame)
        sound_file_frame.pack(fill=tk.X, pady=(0, 10))
        
        alarm_sound_label = ttk.Label(sound_file_frame, text="报警声音:", width=12, anchor=tk.W)
        alarm_sound_label.pack(side=tk.LEFT, padx=(0, 10))
        
        alarm_sound_entry = ttk.Entry(sound_file_frame, textvariable=self.alarm_sound, state="readonly", width=30)
        alarm_sound_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        alarm_sound_btn = ttk.Button(sound_file_frame, text="选择", width=8,
                                   command=self.select_alarm_sound)
        alarm_sound_btn.pack(side=tk.LEFT)
        
        # 报警音量调节
        volume_frame = ttk.Frame(alarm_sound_frame)
        volume_frame.pack(fill=tk.X)
        
        volume_label = ttk.Label(volume_frame, text="音量调节:", width=12, anchor=tk.W)
        volume_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # 音量变化跟踪函数，确保显示为整数
        def update_volume_display(*args):
            self.alarm_volume_str.set(str(self.alarm_volume.get()))
        
        # 绑定音量变化事件
        self.alarm_volume.trace_add("write", update_volume_display)
        
        volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.alarm_volume, length=200)
        volume_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        volume_value_label = ttk.Label(volume_frame, textvariable=self.alarm_volume_str, width=3)
        volume_value_label.pack(side=tk.LEFT)
        
        volume_percent_label = ttk.Label(volume_frame, text="%")
        volume_percent_label.pack(side=tk.LEFT)
        
        # 快捷键设置 - 从首页迁移
        shortcut_frame = ttk.LabelFrame(basic_frame, text="快捷键设置", padding="10")
        shortcut_frame.pack(fill=tk.X, pady=(10, 10))
        
        # 单行布局
        shortcut_row = ttk.Frame(shortcut_frame)
        shortcut_row.pack(fill=tk.X, pady=5)
        
        # 开始快捷键
        ttk.Label(shortcut_row, text="开始快捷键:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        self.start_shortcut_var = tk.StringVar(value="F10")
        start_shortcut_label = ttk.Label(shortcut_row, textvariable=self.start_shortcut_var, relief="sunken", padding=5, width=10)
        start_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
        self.set_start_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
        self.set_start_shortcut_btn.pack(side=tk.LEFT, padx=(0, 20))
        self.set_start_shortcut_btn.config(command=lambda: self.start_key_listening(self.start_shortcut_var, self.set_start_shortcut_btn))
        
        # 结束快捷键
        ttk.Label(shortcut_row, text="结束快捷键:", width=12, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
        self.stop_shortcut_var = tk.StringVar(value="F12")
        stop_shortcut_label = ttk.Label(shortcut_row, textvariable=self.stop_shortcut_var, relief="sunken", padding=5, width=10)
        stop_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
        self.set_stop_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
        self.set_stop_shortcut_btn.pack(side=tk.LEFT)
        self.set_stop_shortcut_btn.config(command=lambda: self.start_key_listening(self.stop_shortcut_var, self.set_stop_shortcut_btn))
        
        # 配置管理
        config_frame = ttk.Frame(basic_frame)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        save_btn = ttk.Button(config_frame, text="保存配置", command=self.save_config)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_btn = ttk.Button(config_frame, text="重置配置", command=self.load_config)
        reset_btn.pack(side=tk.LEFT)
    

    
    def create_home_tab(self, parent):
        """创建首页标签页"""
        home_frame = ttk.Frame(parent, padding="20")
        home_frame.pack(fill=tk.BOTH, expand=True)
        
        # 功能状态显示
        status_frame = ttk.LabelFrame(home_frame, text="功能状态", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 状态标签和勾选框
        self.status_labels = {
            "ocr": tk.StringVar(value="文字识别: 未运行"),
            "timed": tk.StringVar(value="定时功能: 未运行"),
            "number": tk.StringVar(value="数字识别: 未运行")
        }
        
        # 勾选框变量
        self.module_check_vars = {
            "ocr": tk.BooleanVar(value=True),
            "timed": tk.BooleanVar(value=True),
            "number": tk.BooleanVar(value=True)
        }
        
        # 保存Checkbutton组件引用
        self.module_check_buttons = {}
        
        # 模块名称映射
        module_names = {
            "ocr": "文字识别",
            "timed": "定时功能",
            "number": "数字识别"
        }
        
        # 创建带勾选框的状态行
        for module, var in self.status_labels.items():
            row_frame = ttk.Frame(status_frame)
            row_frame.pack(fill=tk.X, pady=2)  # 减少行间隔
            
            # 勾选框
            check_btn = ttk.Checkbutton(row_frame, variable=self.module_check_vars[module])
            check_btn.pack(side=tk.LEFT, padx=(0, 10))
            self.module_check_buttons[module] = check_btn
            
            # 状态标签
            ttk.Label(row_frame, textvariable=var).pack(side=tk.LEFT)
        
        # 全局控制按钮 - 重新定位至功能状态区域下方
        control_frame = ttk.Frame(status_frame)
        control_frame.pack(fill=tk.X, pady=(15, 0))
        
        # 开始/结束按钮
        self.global_start_btn = ttk.Button(control_frame, text="开始运行", command=self.start_all, style="TButton")
        self.global_start_btn.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        self.global_stop_btn = ttk.Button(control_frame, text="停止运行", command=self.stop_all, style="TButton")
        self.global_stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 日志展示模块 - 添加到首页功能状态模块下方
        log_frame = ttk.LabelFrame(home_frame, text="运行日志", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 日志显示区域
        log_display_frame = ttk.Frame(log_frame)
        log_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 日志文本框
        self.home_log_text = tk.Text(log_display_frame, height=15, width=80, font=("Arial", 9), state=tk.DISABLED)
        self.home_log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 日志滚动条
        home_log_scrollbar = ttk.Scrollbar(log_display_frame, orient=tk.VERTICAL, command=self.home_log_text.yview)
        home_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.home_log_text.configure(yscrollcommand=home_log_scrollbar.set)
        
        # 清除日志按钮 - 放置在日志展示窗口下方，固定宽度
        home_clear_btn = ttk.Button(log_frame, text="清除日志", command=self.clear_log, width=12)
        home_clear_btn.pack(side=tk.RIGHT, pady=5)
    
    # 日志功能已迁移到首页，删除create_log_tab方法
    

        
    def update_axis_inputs(self):
        """根据点击模式更新坐标轴输入状态"""
        mode = self.click_mode_var.get()
        if mode == "custom":
            self.x_coord_entry.config(state="normal")
            self.y_coord_entry.config(state="normal")
        else:
            self.x_coord_entry.config(state="disabled")
            self.y_coord_entry.config(state="disabled")
    
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
    
    def preview_key(self):
        """预览按键效果"""
        key = self.key_var.get()
        messagebox.showinfo("按键预览", f"将模拟按下: {key}")
        self.log_message(f"预览按键: {key}")
    
    def restore_default_key(self):
        """恢复默认按键"""
        self.key_var.set("equal")
        self.log_message("已恢复默认按键设置")
        self.save_config()
    
    def start_key_listening(self, target_var, button):
        """开始监听用户按下的按键
        
        Args:
            target_var: 保存按键的StringVar变量
            button: 触发监听的按钮，用于更新按钮状态
        """
        # 保存当前焦点
        current_focus = self.root.focus_get()
        
        # 保存原始状态文本，用于恢复
        original_status = self.status_var.get()
        
        # 更新按钮状态
        original_text = button.cget("text")
        button.config(state="disabled")
        
        # 在原有状态栏显示提示信息
        self.status_var.set("请按任意按键进行设置，按ESC键清空当前记录")
        
        # 创建按键监听函数
        def on_key_press(event):
            """处理按键按下事件"""
            # 恢复原始状态文本
            self.status_var.set(original_status)
            
            # 获取按键名称
            keysym = event.keysym
            
            # 特殊处理ESC键：清空当前记录的按键
            if keysym == "Escape":
                # 清空当前按键配置
                target_var.set("")
                
                # 恢复按钮状态
                button.config(state="normal")
                
                # 解除按键监听
                self.root.unbind("<KeyPress>", funcid=key_listener_id)
                
                # 恢复焦点
                if current_focus:
                    current_focus.focus_set()
                
                # 记录日志
                self.log_message("已清空当前按键设置")
                # 保存配置
                self.save_config()
                return "break"  # 阻止事件继续传播
            
            # 直接使用keysym，不转换为小写，保持功能键的大小写一致性
            key = keysym
            
            # 确保按键在可用列表中
            available_keys = self.get_available_keys()
            if key.lower() not in available_keys:
                self.log_message(f"不支持的按键: {key}")
                # 恢复按钮状态
                button.config(state="normal")
                # 解除按键监听
                self.root.unbind("<KeyPress>", funcid=key_listener_id)
                # 恢复焦点
                if current_focus:
                    current_focus.focus_set()
                return "break"  # 阻止事件继续传播
            
            # 快捷键唯一性校验
            # 判断当前正在设置的是哪个快捷键
            is_setting_start = target_var is self.start_shortcut_var
            is_setting_stop = target_var is self.stop_shortcut_var
            
            if is_setting_start:
                # 检查是否与结束快捷键冲突
                if key == self.stop_shortcut_var.get():
                    messagebox.showwarning("警告", "该按键已被设置为结束快捷键，请选择其他按键！")
                    # 恢复按钮状态
                    button.config(state="normal")
                    # 解除按键监听
                    self.root.unbind("<KeyPress>", funcid=key_listener_id)
                    # 恢复焦点
                    if current_focus:
                        current_focus.focus_set()
                    return "break"  # 阻止事件继续传播
            elif is_setting_stop:
                # 检查是否与开始快捷键冲突
                if key == self.start_shortcut_var.get():
                    messagebox.showwarning("警告", "该按键已被设置为开始快捷键，请选择其他按键！")
                    # 恢复按钮状态
                    button.config(state="normal")
                    # 解除按键监听
                    self.root.unbind("<KeyPress>", funcid=key_listener_id)
                    # 恢复焦点
                    if current_focus:
                        current_focus.focus_set()
                    return "break"  # 阻止事件继续传播
            
            # 保存按键（保持原始大小写，如F10而不是f10）
            target_var.set(key)
            
            # 恢复按钮状态
            button.config(state="normal")
            
            # 解除按键监听
            self.root.unbind("<KeyPress>", funcid=key_listener_id)
            
            # 恢复焦点
            if current_focus:
                current_focus.focus_set()
            
            # 记录日志
            self.log_message(f"已设置按键: {key}")
            
            # 保存配置
            self.save_config()
            
            return "break"  # 阻止事件继续传播
        
        # 绑定按键事件，并保存绑定ID
        key_listener_id = self.root.bind("<KeyPress>", on_key_press, add="+")
        
        # 设置超时，防止永久监听
        def timeout():
            if button.cget("state") == "disabled":
                # 恢复原始状态文本
                self.status_var.set(original_status)
                # 恢复按钮状态
                button.config(state="normal")
                self.root.unbind("<KeyPress>", funcid=key_listener_id)
                if current_focus:
                    current_focus.focus_set()
                self.log_message("按键监听已超时")
        
        self.root.after(5000, timeout)  # 5秒超时
    
    def set_custom_keywords(self):
        """设置自定义关键词"""
        keywords_str = self.keywords_var.get().strip()
        if keywords_str:
            # 分割关键词并去除空格
            self.custom_keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
            self.log_message(f"已设置自定义关键词: {', '.join(self.custom_keywords)}")
            messagebox.showinfo("成功", "关键词设置成功！")
            self.save_config()
        else:
            messagebox.showwarning("警告", "请至少输入一个关键词！")
    
    def restore_default_keywords(self):
        """恢复默认关键词"""
        self.custom_keywords = ["door", "men"]
        self.keywords_var.set(",".join(self.custom_keywords))
        self.log_message("已恢复默认关键词设置")
        self.save_config()
    
    def _get_config_value(self, config, key_path, default=None):
        """获取配置值，支持嵌套路径
        
        Args:
            config: 配置字典
            key_path: 键路径，如 'tesseract.path' 或 ['tesseract', 'path']
            default: 默认值
        
        Returns:
            配置值
        """
        if isinstance(key_path, str):
            key_path = key_path.split('.')
        
        value = config
        for key in key_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def _load_tesseract_config(self, config):
        """加载Tesseract配置"""
        tesseract_path = self._get_config_value(config, 'tesseract.path')
        if not tesseract_path:
            # 兼容旧格式
            tesseract_path = config.get('tesseract_path')
        
        if tesseract_path and tesseract_path.strip():
            temp_path = tesseract_path.strip()
            # 检查路径是否存在
            if os.path.exists(temp_path):
                self.tesseract_path = temp_path
                self.log_message(f"从配置文件加载Tesseract路径: {self.tesseract_path}")
            else:
                self.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")
    
    def _load_ocr_config(self, config):
        """加载OCR配置"""
        ocr_config = self._get_config_value(config, 'ocr', {})
        groups = self._get_config_value(ocr_config, 'groups', [])
        
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
                        if 'enabled' in group_config:
                            enabled = group_config['enabled']
                            self.ocr_groups[i]['enabled'].set(enabled)
                            # 使用类方法更新样式
                            group_frame = self.ocr_groups[i]['frame']
                            self.update_group_style(group_frame, enabled)
                        if 'region' in group_config and group_config['region'] is not None:
                            try:
                                region = tuple(group_config['region'])
                                self.ocr_groups[i]['region'] = region
                                self.ocr_groups[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                            except (TypeError, ValueError):
                                self.log_message(f"配置文件中的OCR区域格式错误: {group_config['region']}")
                        if 'interval' in group_config:
                            self.ocr_groups[i]['interval'].set(group_config['interval'])
                        if 'pause' in group_config:
                            self.ocr_groups[i]['pause'].set(group_config['pause'])
                        if 'key' in group_config:
                            self.ocr_groups[i]['key'].set(group_config['key'])
                        if 'delay_min' in group_config:
                            self.ocr_groups[i]['delay_min'].set(group_config['delay_min'])
                        if 'delay_max' in group_config:
                            self.ocr_groups[i]['delay_max'].set(group_config['delay_max'])
                        if 'alarm' in group_config:
                            self.ocr_groups[i]['alarm'].set(group_config['alarm'])
                        if 'keywords' in group_config:
                            self.ocr_groups[i]['keywords'].set(group_config['keywords'])
                        if 'language' in group_config:
                            self.ocr_groups[i]['language'].set(group_config['language'])
                        if 'click' in group_config:
                            self.ocr_groups[i]['click'].set(group_config['click'])
                        

            
            # 如果没有配置，至少创建一个OCR组
            if len(self.ocr_groups) == 0:
                self.create_ocr_group(0)
        else:
            # 兼容旧格式
            if 'interval' in ocr_config and ocr_config['interval'] is not None:
                self.ocr_interval = ocr_config['interval']
            if 'pause_duration' in ocr_config and ocr_config['pause_duration'] is not None:
                self.pause_duration = ocr_config['pause_duration']
            if 'selected_region' in ocr_config and ocr_config['selected_region'] is not None:
                try:
                    self.selected_region = tuple(ocr_config['selected_region'])
                except (TypeError, ValueError):
                    self.log_message(f"配置文件中的选择区域格式错误: {ocr_config['selected_region']}")
            if 'custom_key' in ocr_config:
                self.custom_key = ocr_config['custom_key']
            if 'custom_keywords' in ocr_config and ocr_config['custom_keywords']:
                self.custom_keywords = ocr_config['custom_keywords']
            if 'language' in ocr_config:
                self.ocr_language = ocr_config['language']
    
    def _load_click_config(self, config):
        """加载点击模式和坐标配置"""
        click_config = self._get_config_value(config, 'click', {})
        if not click_config:
            # 兼容旧格式
            click_config = {
                'mode': config.get('click_mode'),
                'x': config.get('click_x'),
                'y': config.get('click_y')
            }
        
        if 'mode' in click_config:
            self.click_mode_var.set(click_config['mode'])
        if 'x' in click_config and click_config['x'] is not None:
            self.x_coord_var.set(click_config['x'])
        if 'y' in click_config and click_config['y'] is not None:
            self.y_coord_var.set(click_config['y'])
    
    def _load_timed_config(self, config):
        """加载定时功能配置"""
        timed_config = config.get('timed_key_press', {})
        groups = self._get_config_value(timed_config, 'groups', [])
        
        if isinstance(groups, list):
            # 直接清空所有定时组
            for group in self.timed_groups:
                group['frame'].destroy()
            self.timed_groups.clear()
            
            # 然后根据配置重新创建所有定时组
            for i, group in enumerate(groups):
                if isinstance(group, dict):
                    # 直接调用create_timed_group创建定时组
                    self.create_timed_group(i)
                    # 设置组配置
                    if i < len(self.timed_groups):
                        if 'enabled' in group:
                            enabled = group['enabled']
                            self.timed_groups[i]['enabled'].set(enabled)
                            # 使用类方法更新样式
                            group_frame = self.timed_groups[i]['frame']
                            self.update_group_style(group_frame, enabled)
                        if 'interval' in group:
                            self.timed_groups[i]['interval'].set(group['interval'])
                        if 'key' in group:
                            self.timed_groups[i]['key'].set(group['key'])
                        if 'delay_min' in group:
                            self.timed_groups[i]['delay_min'].set(group['delay_min'])
                        if 'delay_max' in group:
                            self.timed_groups[i]['delay_max'].set(group['delay_max'])
                        if 'click_enabled' in group:
                            self.timed_groups[i]['click_enabled'].set(group['click_enabled'])
                        if 'position_x' in group:
                            self.timed_groups[i]['position_x'].set(group['position_x'])
                        if 'position_y' in group:
                            self.timed_groups[i]['position_y'].set(group['position_y'])
                        if 'position' in group:
                            self.timed_groups[i]['position'].set(group['position'])
            
            # 如果没有配置，至少创建一个定时组
            if len(self.timed_groups) == 0:
                self.create_timed_group(0)
    
    def _load_number_config(self, config):
        """加载数字识别配置"""
        number_config = config.get('number_recognition', {})
        regions = self._get_config_value(number_config, 'regions', [])
        
        if isinstance(regions, list):
            # 直接清空所有数字识别区域
            for region in self.number_regions:
                region['frame'].destroy()
            self.number_regions.clear()
            
            # 然后根据配置重新创建所有数字识别区域
            for i, region_config in enumerate(regions):
                if isinstance(region_config, dict):
                    # 直接调用create_number_region创建数字识别区域
                    self.create_number_region(i)
                    # 设置区域配置
                    if i < len(self.number_regions):
                        if 'enabled' in region_config:
                            enabled = region_config['enabled']
                            self.number_regions[i]['enabled'].set(enabled)
                            # 使用类方法更新样式
                            region_frame = self.number_regions[i]['frame']
                            self.update_group_style(region_frame, enabled)
                        if 'region' in region_config and region_config['region'] is not None:
                            try:
                                region = tuple(region_config['region'])
                                self.number_regions[i]['region'] = region
                                self.number_regions[i]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                            except (TypeError, ValueError):
                                self.log_message(f"配置文件中的数字识别区域格式错误: {region_config['region']}")
                        if 'threshold' in region_config:
                            self.number_regions[i]['threshold'].set(region_config['threshold'])
                        if 'key' in region_config:
                            self.number_regions[i]['key'].set(region_config['key'])
                        if 'delay_min' in region_config:
                            self.number_regions[i]['delay_min'].set(region_config['delay_min'])
                        if 'delay_max' in region_config:
                            self.number_regions[i]['delay_max'].set(region_config['delay_max'])
            
            # 如果没有配置，至少创建一个数字识别区域
            if len(self.number_regions) == 0:
                self.create_number_region(0)
    
    def _load_alarm_config(self, config):
        """加载报警配置"""
        alarm_config = self._get_config_value(config, 'alarm', {})
        
        # 加载全局报警声音
        if 'sound' in alarm_config:
            self.alarm_sound.set(alarm_config['sound'])
        
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
        shortcuts_config = self._get_config_value(config, 'shortcuts', {})
        if hasattr(self, 'start_shortcut_var') and 'start' in shortcuts_config:
            self.start_shortcut_var.set(shortcuts_config['start'])
        if hasattr(self, 'stop_shortcut_var') and 'stop' in shortcuts_config:
            self.stop_shortcut_var.set(shortcuts_config['stop'])
    
    def _load_home_checkboxes_config(self, config):
        """加载首页勾选框配置"""
        if 'home_checkboxes' in config and hasattr(self, 'module_check_vars'):
            home_checkboxes = config['home_checkboxes']
            for module in ['ocr', 'timed', 'number']:
                if module in home_checkboxes:
                    self.module_check_vars[module].set(home_checkboxes[module])
    
    def load_config(self):
        """加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        确保加载所有前端设置，包括新增功能的相关配置
        支持新旧配置格式的兼容处理
        """
        # 初始化配置加载结果
        config_loaded = False
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.log_message(f"开始加载配置: {self.config_file}")
                
                # 获取配置版本，默认为1.0.0
                config_version = self._get_config_value(config, 'version', '1.0.0')
                self.log_message(f"配置版本: {config_version}")
                
                # 加载各部分配置
                self._load_tesseract_config(config)
                self._load_ocr_config(config)
                self._load_click_config(config)
                self._load_timed_config(config)
                self._load_number_config(config)
                self._load_alarm_config(config)
                self._load_shortcuts_config(config)
                self._load_home_checkboxes_config(config)
                
                # 更新界面控件状态
                self.update_axis_inputs()
                
                self.log_message("配置加载成功")
                config_loaded = True
                
            except json.JSONDecodeError as e:
                self.log_message(f"配置文件格式错误: {self.config_file}，错误详情: {str(e)}")
            except PermissionError:
                self.log_message(f"没有权限读取配置文件: {self.config_file}")
            except IOError as e:
                self.log_message(f"配置文件IO错误: {str(e)}")
            except Exception as e:
                self.log_message(f"配置加载错误: {str(e)}")
        else:
            self.log_message(f"配置文件不存在: {self.config_file}")
        
        # 更新配置文件版本号（如果与当前版本不一致）
        if config_loaded:
            if config_version != VERSION:
                self.log_message(f"配置版本更新: {config_version} → {VERSION}")
                # 更新配置版本并保存
                config['version'] = VERSION
                config['last_save_time'] = datetime.datetime.now().isoformat()
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
        
        # 无论配置是否加载成功，都更新界面中的Tesseract路径变量
        if hasattr(self, 'tesseract_path_var'):
            self.tesseract_path_var.set(self.tesseract_path)
            
        return config_loaded
    

    
    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        # 通用的延迟保存函数，避免频繁保存
        def delayed_save(*args):
            self.root.after(1000, self.save_config)
        
        # 即时保存函数
        def immediate_save(*args):
            self.save_config()
        
        # 1. 点击模式和坐标监听器
        self.click_mode_var.trace_add("write", immediate_save)
        self.x_coord_var.trace_add("write", delayed_save)
        self.y_coord_var.trace_add("write", delayed_save)
        
        # 4. 定时任务配置监听器
        def setup_group_listeners(group):
            group["enabled"].trace_add("write", immediate_save)
            group["interval"].trace_add("write", delayed_save)
            group["key"].trace_add("write", immediate_save)
        
        # 为所有现有定时组添加监听器
        for group in self.timed_groups:
            setup_group_listeners(group)
        
        # 保存监听器函数，以便后续新增定时组时使用
        self._setup_group_listeners = setup_group_listeners
        
        # 5. 数字识别配置监听器
        def setup_region_listeners(region_config):
            region_config["enabled"].trace_add("write", immediate_save)
            region_config["threshold"].trace_add("write", delayed_save)
            region_config["key"].trace_add("write", immediate_save)
        
        # 为所有现有区域添加监听器
        for region_config in self.number_regions:
            setup_region_listeners(region_config)
        
        # 保存监听器函数，以便后续新增区域时使用
        self._setup_region_listeners = setup_region_listeners
        
        # 6. OCR组配置监听器
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
        
        # 6. 首页模块勾选状态监听器
        if hasattr(self, 'module_check_vars'):
            for module, var in self.module_check_vars.items():
                var.trace_add("write", immediate_save)
        
        # 6. 快捷键配置监听器
        self.start_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))
        self.stop_shortcut_var.trace_add("write", lambda *args: (immediate_save(), self.setup_shortcuts()))
    
    def setup_shortcuts(self):
        """设置快捷键绑定"""
        # 停止旧的全局键盘监听器（如果存在）
        if hasattr(self, 'global_listener') and self.global_listener:
            self.global_listener.stop()
        
        # 使用pynput实现全局键盘监听
        if PYINPUT_AVAILABLE:
            def on_press(key):
                try:
                    # 获取按键名称
                    if hasattr(key, 'name'):
                        # 普通按键
                        key_name = key.name.upper()
                    elif hasattr(key, 'char') and key.char:
                        # 字符按键
                        key_name = key.char.upper()
                    elif hasattr(key, 'vk'):
                        # 特殊按键（F键等）
                        if 112 <= key.vk <= 123:  # VK_F1=112, VK_F12=123
                            key_name = f"F{key.vk - 111}"  # F1=112-111=1, 依此类推
                        else:
                            key_name = str(key)
                    else:
                        key_name = str(key)
                        
                    # 检查是否是开始快捷键
                    if key_name == self.start_shortcut_var.get().upper():
                        self.root.after(0, self.start_all)
                    # 检查是否是结束快捷键
                    if key_name == self.stop_shortcut_var.get().upper():
                        self.root.after(0, self.stop_all)
                except Exception as e:
                    self.log_message(f"全局快捷键处理错误: {str(e)}")
            
            # 创建并启动全局键盘监听器
            self.global_listener = keyboard.Listener(on_press=on_press)
            self.global_listener.start()
            self.log_message("全局快捷键监听已启动")
        else:
            # 回退到Tkinter的窗口内快捷键绑定
            # 先解绑旧的快捷键绑定（如果存在）
            if hasattr(self, 'shortcut_bind_id'):
                self.root.unbind("<KeyPress>", funcid=self.shortcut_bind_id)
            
            def on_shortcut_press(event):
                # 获取按键名称
                keysym = event.keysym
                
                # 检查是否是开始快捷键
                if keysym == self.start_shortcut_var.get():
                    self.start_all()
                    return "break"  # 阻止事件继续传播
                
                # 检查是否是结束快捷键
                if keysym == self.stop_shortcut_var.get():
                    self.stop_all()
                    return "break"  # 阻止事件继续传播
                
                return None
            
            # 绑定窗口内按键事件，并保存绑定ID
            self.shortcut_bind_id = self.root.bind("<KeyPress>", on_shortcut_press, add="+")
            self.log_message("窗口内快捷键绑定已设置")
    
    def clear_log(self):
        """清除日志"""
        # 清除首页的日志文本框
        if hasattr(self, 'home_log_text'):
            self.home_log_text.config(state=tk.NORMAL)
            self.home_log_text.delete("1.0", tk.END)
            self.home_log_text.config(state=tk.DISABLED)
            
        self.log_message("已清除日志")
    
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
        if platform.system() == "Windows":
            if not new_path.endswith("tesseract.exe"):
                messagebox.showwarning("警告", "请指定tesseract.exe可执行文件！")
                return
        elif platform.system() == "Darwin":  # macOS
            if not os.path.basename(new_path) == "tesseract":
                messagebox.showwarning("警告", "请指定tesseract可执行文件！")
                return
        
        try:
            # 测试新路径是否可用
            result = subprocess.run(
                [new_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 更新路径和配置
            self.tesseract_path = new_path
            pytesseract.pytesseract.tesseract_cmd = new_path
            self.tesseract_available = True
            
            self.log_message(f"已设置Tesseract路径: {new_path}")
            self.status_var.set("就绪")
            messagebox.showinfo("成功", "Tesseract路径设置成功！")
            
            # 保存配置
            self.save_config()
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            messagebox.showwarning("警告", "无法使用指定的Tesseract路径！")
            return
        
    def log_message(self, message):
        """记录日志信息"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")
        
        # 写入首页的日志文本框
        if hasattr(self, 'home_log_text'):
            self.home_log_text.config(state=tk.NORMAL)
            self.home_log_text.insert(tk.END, log_entry)
            self.home_log_text.see(tk.END)
            self.home_log_text.config(state=tk.DISABLED)
        
        # 更新状态标签（仅当status_var已创建）
        if hasattr(self, 'status_var'):
            self.status_var.set(message.split(":")[0] if ":" in message else message)
    
    def start_region_selection(self):
        """开始区域选择（兼容旧方法）"""
        if self.ocr_groups:
            self.start_ocr_region_selection(0)
        else:
            self._start_selection("ocr", 0)
    
    def _start_selection(self, selection_type, region_index):
        """通用的区域选择方法
        
        Args:
            selection_type: 选择类型，"normal"、"number"或"ocr"
            region_index: 识别区域索引，仅当selection_type为"number"或"ocr"时有效
        """
        self.log_message(f"开始{'数字识别区域' if selection_type == 'number' else '文字识别区域' if selection_type == 'ocr' else ''}区域选择...")
        self.is_selecting = True
        self.selection_type = selection_type
        
        if selection_type == "number":
            self.current_number_region = region_index
        elif selection_type == "ocr":
            self.current_ocr_region = region_index
        
        # 检查screeninfo库是否可用
        if screeninfo is None:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        
        # 获取虚拟屏幕的尺寸（包含所有显示器）
        monitors = screeninfo.get_monitors()
        
        # 计算整个虚拟屏幕的边界
        self.min_x = min(monitor.x for monitor in monitors)
        self.min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        # 创建透明的区域选择窗口，覆盖整个虚拟屏幕
        self.select_window = tk.Toplevel(self.root)
        self.select_window.geometry(f"{max_x - self.min_x}x{max_y - self.min_y}+{self.min_x}+{self.min_y}")
        self.select_window.overrideredirect(True)  # 移除窗口装饰
        self.select_window.attributes("-alpha", 0.3)
        self.select_window.attributes("-topmost", True)
        
        # 创建画布用于绘制选择框
        self.canvas = tk.Canvas(self.select_window, cursor="cross", 
                               width=max_x - self.min_x, height=max_y - self.min_y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        
        # 根据选择类型绑定不同的鼠标释放事件
        if selection_type == "number":
            self.canvas.bind("<ButtonRelease-1>", self.on_number_region_mouse_up)
        else:
            self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        self.select_window.protocol("WM_DELETE_WINDOW", self.cancel_selection)
    
    def on_mouse_down(self, event):
        """鼠标按下事件"""
        # 保存绝对坐标用于最终区域保存
        self.start_x_abs = event.x_root
        self.start_y_abs = event.y_root
        # 计算相对Canvas的坐标用于绘制
        self.start_x_rel = event.x_root - self.min_x
        self.start_y_rel = event.y_root - self.min_y
        self.rect = None
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        # 获取当前绝对坐标
        current_x_abs = event.x_root
        current_y_abs = event.y_root
        # 计算相对Canvas的坐标用于绘制
        current_x_rel = current_x_abs - self.min_x
        current_y_rel = current_y_abs - self.min_y
        
        if self.rect:
            self.canvas.delete(self.rect)
        
        # 使用相对坐标绘制选择框，确保视觉上与鼠标位置一致
        self.rect = self.canvas.create_rectangle(
            self.start_x_rel, self.start_y_rel, current_x_rel, current_y_rel,
            outline="red", width=2, fill="red"
        )
    
    def _save_selection(self, start_x, start_y, end_x, end_y):
        """保存选择区域的公共方法"""
        # 确保选择区域有效
        if abs(end_x - start_x) < 10 or abs(end_y - start_y) < 10:
            messagebox.showwarning("警告", "选择的区域太小，请重新选择")
            self.cancel_selection()
            return None
        
        # 保存选择区域（使用绝对坐标）
        region = (
            min(start_x, end_x),
            min(start_y, end_y),
            max(start_x, end_x),
            max(start_y, end_y)
        )
        
        return region
    
    def on_mouse_up(self, event):
        """鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root
        
        # 保存选择区域
        region = self._save_selection(self.start_x_abs, self.start_y_abs, end_x_abs, end_y_abs)
        if region is None:
            return
        
        # 根据选择类型保存区域
        if hasattr(self, 'selection_type') and self.selection_type == 'ocr':
            # OCR组区域选择
            if self.current_ocr_region is not None and 0 <= self.current_ocr_region < len(self.ocr_groups):
                self.ocr_groups[self.current_ocr_region]['region'] = region
                self.ocr_groups[self.current_ocr_region]['region_var'].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
                self.log_message(f"已为识别组{self.current_ocr_region+1}选择区域: {region}")
        else:
            # 兼容旧方法
            self.selected_region = region
            if hasattr(self, 'region_var'):
                self.region_var.set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
            self.log_message(f"已选择区域: {region}")
        
        self.cancel_selection()
        
        # 保存配置
        self.save_config()
    
    def cancel_selection(self):
        """取消区域选择"""
        self.is_selecting = False
        if hasattr(self, 'select_window') and self.select_window.winfo_exists():
            self.select_window.destroy()
    
    def start_monitoring(self):
        """开始监控"""
        if not self.tesseract_available:
            messagebox.showwarning("警告", "Tesseract OCR引擎不可用，请先安装并配置环境变量！")
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
        
        self.is_running = True
        self.is_paused = False
        
        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 运行中")
        
        self.log_message("开始监控...")
        
        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
        self.ocr_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        
        # 更新状态标签
        self.status_labels["ocr"].set("文字识别: 未运行")
        
        self.log_message("已停止监控")
    
    def ocr_loop(self):
        """OCR识别循环"""
        # 初始化每个组的上次识别时间和上次触发时间
        self.last_recognition_times = {i: 0 for i in range(len(self.ocr_groups))}  # 用于识别间隔
        self.last_trigger_times = {i: 0 for i in range(len(self.ocr_groups))}  # 用于暂停期
        
        while self.is_running:
            try:
                # 等待下一次识别，使用最小间隔
                min_interval = min(group["interval"].get() for group in self.ocr_groups if group["enabled"].get()) if any(group["enabled"].get() for group in self.ocr_groups) else 5
                
                # 等待设定的间隔时间
                for _ in range(min_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
                # 检查是否需要暂停
                if self.is_paused:
                    continue
                
                current_time = time.time()
                
                # 遍历所有OCR组，并行处理
                for i, group in enumerate(self.ocr_groups):
                    # 检查组是否启用且已选择区域
                    if not group["enabled"].get() or not group["region"]:
                        continue
                    
                    # 获取组配置
                    group_interval = group["interval"].get()
                    pause_duration = group["pause"].get()
                    
                    # 检查是否在暂停期（触发动作后）
                    if current_time - self.last_trigger_times[i] < pause_duration:
                        continue
                    
                    # 检查是否达到识别间隔
                    if current_time - self.last_recognition_times[i] < group_interval:
                        continue
                    
                    # 执行OCR识别
                    self.perform_ocr_for_group(group, i)
                    
                    # 更新上次识别时间
                    self.last_recognition_times[i] = current_time
            except Exception as e:
                self.log_message(f"错误: {str(e)}")
                time.sleep(5)
    
    def perform_ocr(self):
        """执行OCR识别（兼容旧方法）"""
        # 如果有OCR组，使用第一个组的配置
        if self.ocr_groups:
            self.perform_ocr_for_group(self.ocr_groups[0], 0)
        else:
            try:
                # 截取屏幕区域
                if hasattr(self, 'selected_region') and self.selected_region:
                    x1, y1, x2, y2 = self.selected_region
                    
                    # 确保坐标是(left, top, right, bottom)格式，且left < right, top < bottom
                    left = min(x1, x2)
                    top = min(y1, y2)
                    right = max(x1, x2)
                    bottom = max(y1, y2)
                    
                    # 使用PIL的ImageGrab.grab()方法，设置all_screens=True捕获所有屏幕
                    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
                    
                    # 转换为灰度图像以提高识别率
                    screenshot = screenshot.convert('L')
                    
                    # 进行OCR识别
                    current_lang = self.language_var.get() if hasattr(self, 'language_var') else 'eng'
                    text = pytesseract.image_to_string(screenshot, lang=current_lang)
                    
                    self.log_message(f"识别结果: '{text.strip()}'")
                    
                    # 检查是否包含关键词
                    lower_text = text.lower()
                    keywords = self.custom_keywords if hasattr(self, 'custom_keywords') else ['men', 'door']
                    if any(keyword in lower_text for keyword in keywords):
                        self.trigger_action()
            except Exception as e:
                self.log_message(f"OCR错误: {str(e)}")
    
    def perform_ocr_for_group(self, group, group_index):
        """为单个OCR组执行OCR识别"""
        try:
            # 获取组配置
            region = group["region"]
            keywords_str = group["keywords"].get().strip()
            current_lang = group["language"].get()
            click_enabled = group["click"].get()
            
            # 截取屏幕区域
            x1, y1, x2, y2 = region
            
            # 确保坐标是(left, top, right, bottom)格式，且left < right, top < bottom
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # 使用PIL的ImageGrab.grab()方法，设置all_screens=True捕获所有屏幕
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
            
            # 转换为灰度图像以提高识别率
            screenshot = screenshot.convert('L')
            
            # 添加图像预处理，提高识别精度
            from PIL import ImageEnhance, ImageFilter
            
            # 提高对比度
            enhancer = ImageEnhance.Contrast(screenshot)
            screenshot = enhancer.enhance(1.5)
            
            # 锐化图像
            screenshot = screenshot.filter(ImageFilter.SHARPEN)
            
            # 添加阈值处理，增强文字与背景的对比度
            screenshot = screenshot.point(lambda p: p > 128 and 255)
            
            # 使用优化的Tesseract配置进行OCR识别
            # --psm 6: 假设一个统一的块文本
            # --oem 3: 使用默认的OCR引擎
            # -c tessedit_char_whitelist=...: 可选，根据需要设置字符白名单
            custom_config = r'--psm 6 --oem 3'
            
            # 进行OCR识别，获取文字内容和位置信息
            text = pytesseract.image_to_string(screenshot, lang=current_lang, config=custom_config)
            
            self.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}'")
            
            # 检查是否包含关键词
            lower_text = text.lower()
            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                if any(keyword in lower_text for keyword in keywords):
                    # 如果启用点击，获取文字位置信息
                    click_pos = None
                    if click_enabled:
                        try:
                            # 使用image_to_data获取文字位置信息，使用相同的优化配置
                            data = pytesseract.image_to_data(screenshot, lang=current_lang, config=custom_config, output_type=pytesseract.Output.DICT)
                            
                            # 遍历所有识别到的文字，找到关键词的位置
                            for i in range(len(data['text'])):
                                word = data['text'][i].lower().strip()
                                if word in keywords or any(keyword in word for keyword in keywords):
                                    # 获取文字的边界框
                                    left_word = data['left'][i]
                                    top_word = data['top'][i]
                                    width = data['width'][i]
                                    height = data['height'][i]
                                    
                                    # 计算文字中心位置（相对于截图）
                                    center_x = left_word + width // 2
                                    center_y = top_word + height // 2
                                    
                                    # 转换为屏幕坐标
                                    click_pos = (left + center_x, top + center_y)
                                    break
                            
                            # 如果没有找到关键词位置，使用区域中心
                            if click_pos is None:
                                click_pos = ((left + right) // 2, (top + bottom) // 2)
                        except Exception as e:
                            self.log_message(f"识别组{group_index+1}获取文字位置失败: {str(e)}")
                            # 失败时使用区域中心
                            click_pos = ((left + right) // 2, (top + bottom) // 2)
                    
                    # 触发动作，传递文字位置
                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)
                    
        except Exception as e:
            self.log_message(f"识别组{group_index+1}OCR错误: {str(e)}")
    
    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None):
        """为单个OCR组触发动作"""
        key = group["key"].get()
        delay_min = group["delay_min"].get()
        delay_max = group["delay_max"].get()
        alarm_enabled = group["alarm"].get()
        region = group["region"]
        
        self.log_message(f"识别组{group_index+1}触发动作，按键: {key}")
        
        # 生成随机延迟
        delay = random.randint(delay_min, delay_max) / 1000.0
        
        try:
            # 如果启用点击识别文字，先执行鼠标点击
            if click_enabled:
                # 如果没有传递点击位置，使用区域中心作为备选
                if click_pos is None:
                    # 计算点击位置（区域中心）
                    x1, y1, x2, y2 = region
                    click_x = (x1 + x2) // 2
                    click_y = (y1 + y2) // 2
                else:
                    click_x, click_y = click_pos
                
                # 执行鼠标点击
                pyautogui.click(click_x, click_y)
                self.log_message(f"识别组{group_index+1}点击位置: ({click_x}, {click_y})")
                
                # 等待固定时间
                time.sleep(self.click_delay)
            
            # 执行按键操作
            pyautogui.press(key, interval=delay)
            self.log_message(f"识别组{group_index+1}已模拟按键: {key}，延迟: {delay*1000}ms")
            
            # 更新该组的上次触发时间，进入暂停期
            self.last_trigger_times[group_index] = time.time()
        except Exception as e:
            self.log_message(f"识别组{group_index+1}动作执行失败: {str(e)}")
        
        # 播放报警声音（如果启用）
        if alarm_enabled and PYGAME_AVAILABLE:
            self.play_alarm_sound()
    
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
                'position': group['position'].get()
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
    
    def _get_click_config(self):
        """获取点击模式和坐标配置"""
        return {
            'mode': self.click_mode_var.get(),
            'x': self.x_coord_var.get(),
            'y': self.y_coord_var.get()
        }
    
    def _get_shortcuts_config(self):
        """获取快捷键配置"""
        return {
            'start': self.start_shortcut_var.get(),
            'stop': self.stop_shortcut_var.get()
        }
    
    def _get_alarm_config(self):
        """获取报警功能配置"""
        return {
            'sound': self.alarm_sound.get(),
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
    
    def save_config(self):
        """保存配置
        保存所有前端用户设置，包括新增功能的相关配置
        确保数据结构完整、一致，并处理边界情况
        """
        try:
            # 获取各部分配置
            timed_groups_config = self._get_timed_config()
            number_regions_config = self._get_number_config()
            
            # 完整的配置数据结构，确保所有配置项都被保存
            config = {
                'version': VERSION,  # 使用全局版本号，自动同步
                'last_save_time': datetime.datetime.now().isoformat(),
                
                # 基本OCR配置
                'ocr': self._get_ocr_config(),
                
                # Tesseract配置
                'tesseract': self._get_tesseract_config(),
                
                # 坐标模式配置
                'click': self._get_click_config(),
                
                # 定时功能配置
                'timed_key_press': {
                    'groups': timed_groups_config
                },
                
                # 数字识别配置
                'number_recognition': {
                    'regions': number_regions_config
                },
                
                # 快捷键配置 - 新增
                'shortcuts': self._get_shortcuts_config(),
                
                # 报警功能配置
                'alarm': self._get_alarm_config(),
                
                # 首页功能状态勾选框配置
                'home_checkboxes': self._get_home_checkboxes_config()
            }
            
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 写入配置文件，使用更紧凑的格式
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            
            self.log_message("配置已保存")
            
        except PermissionError:
            self.log_message(f"没有权限写入配置文件: {self.config_file}")
        except IOError as e:
            self.log_message(f"配置文件IO错误: {str(e)}")
        except json.JSONDecodeError as e:
            self.log_message(f"配置JSON编码错误: {str(e)}")
        except Exception as e:
            self.log_message(f"配置保存错误: {str(e)}")
    
    def trigger_action(self):
        """触发动作序列"""
        self.log_message("检测到关键词，执行动作...")
        
        # 播放OCR模块报警声音
        self.play_alarm_sound(self.alarm_enabled["ocr"])
        
        # 获取自定义按键
        custom_key = self.key_var.get()
        
        # 只有当按键不为空时才执行按键操作
        if custom_key:
            # 计算点击位置
            click_x, click_y = self.calculate_click_position()
            
            try:
                # 1. 鼠标左键点击指定位置
                pyautogui.click(click_x, click_y)
                self.log_message(f"点击位置: ({click_x}, {click_y})")
                
                # 2. 等待固定时间（无需用户修改）
                time.sleep(self.click_delay)
                
                # 3. 通过事件队列按下自定义按键
                self.add_event(('keypress', custom_key), ('ocr', 0))
                
                # 记录触发时间
                self.last_trigger_time = time.time()
                
            except Exception as e:
                self.log_message(f"动作执行错误: {str(e)}")
        else:
            self.log_message("按键配置为空，仅执行报警操作")
    
    def calculate_click_position(self):
        """计算点击位置"""
        mode = self.click_mode_var.get()
        
        if mode == "custom":
            # 使用自定义坐标（相对于选择区域左上角）
            x_offset = self.x_coord_var.get()
            y_offset = self.y_coord_var.get()
            
            # 计算实际屏幕坐标
            click_x = self.selected_region[0] + x_offset
            click_y = self.selected_region[1] + y_offset
            
            # 确保坐标在选择区域内
            click_x = max(self.selected_region[0], min(click_x, self.selected_region[2]))
            click_y = max(self.selected_region[1], min(click_y, self.selected_region[3]))
        else:
            # 计算区域中心
            click_x = (self.selected_region[0] + self.selected_region[2]) // 2
            click_y = (self.selected_region[1] + self.selected_region[3]) // 2
        
        return click_x, click_y
    
    def start_event_thread(self):
        """启动事件处理线程"""
        self.is_event_running = True
        self.event_thread = threading.Thread(target=self.process_events, daemon=True)
        self.event_thread.start()
        self.log_message("事件处理线程已启动")
    
    def process_events(self):
        """处理事件队列中的事件"""
        while self.is_event_running:
            try:
                with self.event_cond:
                    while not self.event_queue:
                        self.event_cond.wait()
                    event_data = self.event_queue.popleft()
                
                # 执行事件
                self.execute_event(event_data)
            except Exception as e:
                self.log_message(f"事件处理错误: {str(e)}")
                time.sleep(1)
    
    def add_event(self, event, module_info=None):
        """添加事件到队列"""
        with self.event_cond:
            self.event_queue.append((event, module_info))
            self.event_cond.notify()
    
    def execute_event(self, event_data):
        """执行具体事件"""
        event, module_info = event_data
        event_type, data = event
        
        if event_type == 'keypress':
            key = data
            try:
                # 立即按下按键
                pyautogui.keyDown(key)
                
                # 根据模块信息获取延迟范围
                if module_info:
                    module_type, module_index = module_info
                    if module_type == 'ocr':
                        delay_min = self.ocr_delay_min.get()
                        delay_max = self.ocr_delay_max.get()
                    elif module_type == 'timed':
                        delay_min = self.timed_groups[module_index]['delay_min'].get()
                        delay_max = self.timed_groups[module_index]['delay_max'].get()
                    elif module_type == 'number':
                        delay_min = self.number_regions[module_index]['delay_min'].get()
                        delay_max = self.number_regions[module_index]['delay_max'].get()
                    else:
                        delay_min = 300
                        delay_max = 500
                else:
                    # 默认延迟
                    delay_min = 300
                    delay_max = 500
                
                # 确保延迟范围有效
                delay_min = max(1, delay_min)  # 至少1ms
                delay_max = max(delay_min, delay_max)  # 确保max不小于min
                
                # 生成随机延迟
                delay = random.randint(delay_min, delay_max) / 1000  # 转换为秒
                
                # 延迟等待（不会影响UI主线程，因为事件处理在单独线程中）
                time.sleep(delay)
                
                # 延迟后弹起按键
                pyautogui.keyUp(key)
                
                self.log_message(f"按下了 {key} 键，延迟 {delay*1000:.0f} 毫秒")
            except Exception as e:
                self.log_message(f"按键执行错误: {str(e)}")
        elif event_type == 'exit':
            # 退出事件，什么都不做
            pass
        # 其他事件类型...
    
    def _manage_threads(self, module_type, start_func, stop_func, thread_list, status_var_key, log_prefix):
        """线程管理的公共方法"""
        # 停止现有线程
        stop_func()
        
        self.log_message(f"开始{log_prefix}")
        
        # 统计要启动的线程数量
        start_count = start_func()
        
        # 更新状态标签
        if start_count > 0:
            self.status_labels[status_var_key].set(f"{log_prefix[:-1]}: 运行中")
        else:
            self.status_labels[status_var_key].set(f"{log_prefix[:-1]}: 未运行")
        
        if start_count == 0:
            self.log_message(f"没有启用任何{log_prefix[:-2]}")
    
    def _stop_threads(self, thread_list, module_name, status_var_key):
        """停止线程的公共方法"""
        # 停止所有线程
        self.log_message(f"停止所有{module_name}")
        
        # 清空线程列表
        if thread_list:
            self.log_message(f"停止{len(thread_list)}个{module_name}线程")
            thread_list.clear()
        
        # 更新状态标签
        self.status_labels[status_var_key].set(f"{module_name[:-1]}: 未运行")
        
        self.log_message(f"已停止{module_name}")
    
    def start_timed_tasks(self):
        """开始定时任务"""
        def start_func():
            start_count = 0
            for i, group in enumerate(self.timed_groups):
                if group["enabled"].get():
                    interval = group["interval"].get()
                    key = group["key"].get()
                    # 创建线程并存储
                    thread = threading.Thread(target=self.timed_task_loop, args=(i, interval, key), daemon=True)
                    self.timed_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count
        
        self._manage_threads("timed", start_func, self.stop_timed_tasks, self.timed_threads, "timed", "定时任务")
    
    def stop_timed_tasks(self):
        """停止定时任务"""
        self._stop_threads(self.timed_threads, "定时任务", "timed")
    
    def timed_task_loop(self, group_index, interval, key):
        """定时任务循环"""
        current_thread = threading.current_thread()
        
        # 检查线程是否在timed_threads列表中，以及定时组是否启用
        while current_thread in self.timed_threads and self.timed_groups[group_index]["enabled"].get():
            try:
                # 等待指定的时间间隔
                for _ in range(interval):
                    time.sleep(1)
                    # 每秒钟检查一次线程是否仍在列表中
                    if current_thread not in self.timed_threads:
                        return
                
                # 获取定时组配置
                group = self.timed_groups[group_index]
                
                # 播放定时模块报警声音
                self.play_alarm_sound(group["alarm"])
                
                # 检查是否启用了鼠标点击
                if group["click_enabled"].get():
                    # 获取保存的位置坐标
                    pos_x = group["position_x"].get()
                    pos_y = group["position_y"].get()
                    
                    if pos_x != 0 or pos_y != 0:  # 确保位置已选择
                        # 执行鼠标点击操作
                        pyautogui.click(pos_x, pos_y)
                        self.log_message(f"定时任务{group_index+1}执行鼠标点击: ({pos_x}, {pos_y})")
                        
                        # 等待0.5秒后触发按键
                        time.sleep(0.5)
                
                # 只有当按键不为空时才执行按键操作
                if key:
                    self.add_event(('keypress', key), ('timed', group_index))
                    self.log_message(f"定时任务{group_index+1}触发按键: {key}")
                else:
                    self.log_message(f"定时任务{group_index+1}按键配置为空")
            except Exception as e:
                self.log_message(f"定时任务{group_index+1}错误: {str(e)}")
                break
    
    def start_number_region_selection(self, region_index):
        """开始数字识别区域选择"""
        self._start_selection("number", region_index)
    
    def start_timed_position_selection(self, group_index):
        """开始定时任务屏幕位置选择"""
        self.log_message(f"开始定时组{group_index+1}屏幕位置选择...")
        self.is_selecting = True
        self.current_timed_group = group_index
        
        # 检查screeninfo库是否可用
        if screeninfo is None:
            messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return
        
        # 获取虚拟屏幕的尺寸（包含所有显示器）
        monitors = screeninfo.get_monitors()
        
        # 计算整个虚拟屏幕的边界
        self.min_x = min(monitor.x for monitor in monitors)
        self.min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
        
        # 创建透明的位置选择窗口，覆盖整个虚拟屏幕
        self.select_window = tk.Toplevel(self.root)
        self.select_window.geometry(f"{max_x - self.min_x}x{max_y - self.min_y}+{self.min_x}+{self.min_y}")
        self.select_window.overrideredirect(True)  # 移除窗口装饰
        self.select_window.attributes("-alpha", 0.3)
        self.select_window.attributes("-topmost", True)
        
        # 创建画布用于显示提示
        self.canvas = tk.Canvas(self.select_window, cursor="cross", 
                               width=max_x - self.min_x, height=max_y - self.min_y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 显示提示文字
        self.canvas.create_text((max_x - self.min_x) // 2, (max_y - self.min_y) // 2, 
                              text="请点击要记录的屏幕位置", font=("Arial", 16), fill="red")
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_timed_position_click)
        
        self.select_window.protocol("WM_DELETE_WINDOW", self.cancel_selection)
    
    def on_timed_position_click(self, event):
        """定时任务位置选择鼠标点击事件"""
        # 获取绝对坐标
        pos_x = event.x_root
        pos_y = event.y_root
        
        self.log_message(f"定时组{self.current_timed_group+1}已选择位置: {pos_x},{pos_y}")
        
        # 更新配置
        if 0 <= self.current_timed_group < len(self.timed_groups):
            group = self.timed_groups[self.current_timed_group]
            group["position_x"].set(pos_x)
            group["position_y"].set(pos_y)
            group["position"].set(f"位置：{pos_x},{pos_y}")
            
            # 保存配置
            self.save_config()
        
        self.cancel_selection()
    
    def on_number_region_mouse_up(self, event):
        """数字识别区域鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root
        
        # 保存选择区域
        region = self._save_selection(self.start_x_abs, self.start_y_abs, end_x_abs, end_y_abs)
        if region is None:
            return
        
        # 更新界面
        region_index = self.current_number_region
        self.number_regions[region_index]["region"] = region
        self.number_regions[region_index]["region_var"].set(f"区域: {region[0]},{region[1]} - {region[2]},{region[3]}")
        
        self.log_message(f"已选择数字识别区域{region_index+1}: {region}")
        self.cancel_selection()
        
        # 保存配置
        self.save_config()
    
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
        
        self._manage_threads("number", start_func, self.stop_number_recognition, self.number_threads, "number", "数字识别")
    
    def stop_number_recognition(self):
        """停止数字识别"""
        self._stop_threads(self.number_threads, "数字识别", "number")
    
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
        self.log_message("开始运行")
        
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
            self.start_timed_tasks()
        
        if self.module_check_vars["number"].get():
            self.start_number_recognition()
        
        # 播放开始运行的音频
        self.play_start_sound()
    
    def stop_all(self):
        """停止运行"""
        self.log_message("停止运行")
        
        # 停止运行
        self.stop_monitoring()
        self.stop_timed_tasks()
        self.stop_number_recognition()
        
        # 播放停止运行的反向音频
        self.play_stop_sound()
        
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
    
    def number_recognition_loop(self, region_index, region, threshold, key):
        """数字识别循环"""
        current_thread = threading.current_thread()
        
        # 检查线程是否在number_threads列表中，以及数字识别区域是否启用
        while current_thread in self.number_threads and self.number_regions[region_index]["enabled"].get():
            try:
                # 等待1秒间隔
                time.sleep(1)  # 1秒间隔
                
                # 截图并识别数字
                screenshot = self.take_screenshot(region)
                text = self.ocr_number(screenshot)
                self.log_message(f"数字识别{region_index+1}结果: '{text}'")
                
                number = self.parse_number(text)
                if number is not None:
                    self.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        # 播放数字识别模块报警声音
                        self.play_alarm_sound(self.number_regions[region_index]["alarm"])
                        
                        # 只有当数字小于阈值且按键不为空时才执行按键操作
                        if key:
                            self.add_event(('keypress', key), ('number', region_index))
                            self.log_message(f"数字识别{region_index+1}触发按键: {key}")
                        else:
                            self.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
            except Exception as e:
                self.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)
    
    def parse_number(self, text):
        """解析数字，支持X/Y格式
        打印详细日志以帮助排查问题
        """
        # 打印当前识别到的文字内容
        self.log_message(f"数字识别解析: 当前文字内容为 '{text}'")
        
        # 移除可能的空格和换行符
        text = text.strip()
        
        # 检查是否为X/Y格式
        if '/' in text:
            self.log_message("数字识别解析: 检测到X/Y格式文字 '{0}'".format(text))
            parts = text.split('/')
            self.log_message("数字识别解析: 分割结果为 {0}".format(parts))
            
            if len(parts) == 2:
                # 尝试解析X部分
                x_part = parts[0].strip()
                self.log_message("数字识别解析: 尝试解析X部分 '{0}'".format(x_part))
                try:
                    x_number = int(x_part)
                    self.log_message("数字识别解析: 成功解析X部分为 {0}".format(x_number))
                    return x_number
                except ValueError as e:
                    self.log_message("数字识别解析: 无法解析X部分 '{0}'，错误: {1}".format(x_part, str(e)))
                    # 尝试清理X部分，移除非数字字符
                    cleaned_x = ''.join(filter(str.isdigit, x_part))
                    if cleaned_x:
                        self.log_message("数字识别解析: 清理后X部分为 '{0}'".format(cleaned_x))
                        try:
                            return int(cleaned_x)
                        except ValueError:
                            self.log_message("数字识别解析: 清理后仍无法解析X部分 '{0}'".format(cleaned_x))
        else:
            self.log_message("数字识别解析: 未检测到X/Y格式，尝试直接解析数字 '{0}'".format(text))
            
        # 尝试直接解析为数字
        try:
            # 清理文字，移除非数字字符
            cleaned_text = ''.join(filter(str.isdigit, text))
            if cleaned_text:
                self.log_message(f"数字识别解析: 清理后文字为 '{cleaned_text}'")
                number = int(cleaned_text)
                self.log_message(f"数字识别解析: 成功解析为数字 {number}")
                return number
            else:
                self.log_message(f"数字识别解析: 清理后无数字字符")
                return None
        except ValueError as e:
            self.log_message(f"数字识别解析: 无法直接解析为数字，错误: {str(e)}")
            return None
    
    def take_screenshot(self, region):
        """截取指定区域的屏幕"""
        x1, y1, x2, y2 = region
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    
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
    
    def play_alarm_sound(self, alarm_var):
        """播放报警声音
        
        Args:
            alarm_var: 报警开关的BooleanVar变量
        """
        if not PYGAME_AVAILABLE:
            self.log_message("pygame库未安装，无法播放报警声音")
            return
        
        if not alarm_var.get():
            return
        
        sound_file = self.alarm_sound.get()
        if not sound_file or not os.path.exists(sound_file):
            self.log_message("未设置有效的全局报警声音文件")
            return
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(self.alarm_volume.get() / 100)  # 设置音量
            pygame.mixer.music.play()
            self.log_message("报警声音已播放")
        except Exception as e:
            self.log_message(f"播放报警声音失败: {str(e)}")
    
    def play_start_sound(self):
        """播放开始运行的音频"""
        if not PYGAME_AVAILABLE:
            self.log_message("pygame库未安装，无法播放开始运行音效")
            return
        
        # 直接使用固定的音频文件路径，不受报警声音设置的影响
        sound_file = self.get_default_alarm_sound_path()
        if not sound_file or not os.path.exists(sound_file):
            self.log_message("未找到默认音频文件，无法播放开始运行音效")
            return
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
            pygame.mixer.music.play()
            self.log_message("开始运行音效已播放")
        except pygame.error as e:
            self.log_message(f"音频文件格式错误或损坏: {str(e)}")
        except Exception as e:
            self.log_message(f"播放开始运行音效失败: {str(e)}")
    
    def play_stop_sound(self):
        """播放停止运行的反向音频"""
        if not PYGAME_AVAILABLE:
            self.log_message("pygame库未安装，无法播放停止运行音效")
            return
        
        # 直接使用固定的音频文件路径，不受报警声音设置的影响
        sound_file = self.get_default_alarm_sound_path()
        if not sound_file or not os.path.exists(sound_file):
            self.log_message("未找到默认音频文件，无法播放停止运行音效")
            return
        
        try:
            # 尝试创建并播放反向音频
            reversed_file = self._create_reversed_audio(sound_file)
            if reversed_file:
                try:
                    pygame.mixer.music.load(reversed_file)
                    pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                    pygame.mixer.music.play()
                    self.log_message("停止运行音效已播放")
                    # 移除清理临时文件的逻辑，避免文件被占用的错误
                except pygame.error as e:
                    self.log_message(f"反向音频文件格式错误或损坏: {str(e)}")
                    # 播放原始音频作为备选
                    try:
                        pygame.mixer.music.load(sound_file)
                        pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                        pygame.mixer.music.play()
                        self.log_message("播放原始音频作为备选")
                    except Exception as e2:
                        self.log_message(f"播放原始音频也失败: {str(e2)}")
            else:
                # 如果反向处理失败，播放原始音频
                try:
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.set_volume(0.7)  # 使用固定音量 70%
                    pygame.mixer.music.play()
                    self.log_message("反向音频处理失败，播放原始音频")
                except Exception as e:
                    self.log_message(f"播放原始音频失败: {str(e)}")
        except Exception as e:
            self.log_message(f"播放停止运行音效失败: {str(e)}")
    
    def _create_reversed_audio(self, input_file):
        """创建反向音频文件
        
        Args:
            input_file: 输入音频文件路径
            
        Returns:
            反向音频文件路径，失败返回None
        """
        try:
            # 创建临时文件路径
            # 在macOS上，确保临时文件保存在可写位置
            if platform.system() == "Darwin":
                temp_dir = os.path.expanduser("~")  # 使用用户主目录
            else:
                temp_dir = os.path.dirname(input_file)
            
            temp_file = os.path.join(temp_dir, "temp_reversed.mp3")
            
            # 检查临时文件是否已存在，如果存在则直接返回
            if os.path.exists(temp_file):
                self.log_message("临时反向音频文件已存在，直接使用")
                return temp_file
            
            # 由于pygame的限制，我们使用一种替代方法：
            # 1. 尝试使用外部库如pydub（如果可用）
            try:
                from pydub import AudioSegment
                
                # 加载音频文件
                audio = AudioSegment.from_mp3(input_file)
                
                # 反转音频
                reversed_audio = audio.reverse()
                
                # 导出为临时文件
                reversed_audio.export(temp_file, format="mp3")
                
                return temp_file
            except ImportError:
                # 如果pydub不可用，使用pygame的有限功能
                # 注意：这种方法可能无法实现真正的音频反转
                # 但为了兼容性，我们仍然返回原始文件
                return input_file
            except Exception as e:
                self.log_message(f"pydub处理音频失败: {str(e)}")
                return input_file
        except Exception as e:
            self.log_message(f"创建反向音频失败: {str(e)}")
            return None
    
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
            self.alarm_sound.set(filename)
            self.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")
            self.save_config()
    
    def toggle_alarm(self, module):
        """切换报警开关状态
        
        Args:
            module: 模块名称，如"ocr"、"timed"或"number"
        """
        self.log_message(f"{module}模块报警状态已{'启用' if self.alarm_enabled[module].get() else '禁用'}")
        self.save_config()
    
    def update_child_styles(self, widget, is_enabled):
        """递归更新所有子组件样式
        
        Args:
            widget: 要更新样式的组件
            is_enabled: 组件是否启用
        """
        # 根据组件类型应用不同样式
        if isinstance(widget, ttk.Frame):
            widget.configure(style="Green.TFrame" if is_enabled else "TFrame")
        elif isinstance(widget, ttk.Label):
            # 检查是否为显示按键的标签（有sunken relief）
            if widget.cget("relief") == "sunken":
                widget.configure(style="TLabel")  # 始终使用默认样式
            else:
                widget.configure(style="Green.TLabel" if is_enabled else "TLabel")
        elif isinstance(widget, ttk.Button):
            widget.configure(style="Green.TButton" if is_enabled else "TButton")
        elif isinstance(widget, ttk.Checkbutton):
            widget.configure(style="Green.TCheckbutton" if is_enabled else "TCheckbutton")
        elif isinstance(widget, ttk.Combobox):
            widget.configure(style="Green.TCombobox" if is_enabled else "TCombobox")
        elif isinstance(widget, ttk.Entry):
            widget.configure(style="TEntry")  # 始终使用默认样式，不随组启用状态变化
        elif isinstance(widget, ttk.LabelFrame):
            widget.configure(style="Green.TLabelframe" if is_enabled else "TLabelframe")
        
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
    

    
    def exit_program(self):
        """退出程序"""
        if self.is_running:
            self.stop_monitoring()
        self.stop_timed_tasks()
        self.stop_number_recognition()
        
        # 停止全局键盘监听器
        if hasattr(self, 'global_listener') and self.global_listener:
            self.global_listener.stop()
        
        # 停止事件线程
        self.is_event_running = False
        if self.event_thread:
            self.add_event(('exit', None), None)
            self.event_thread.join(timeout=1)
        
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()

def main():
    """主函数，用于命令行调用"""
    app = AutoDoorOCR()
    app.run()

if __name__ == "__main__":
    main()
