import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import pytesseract
from PIL import Image, ImageTk
import cv2
import numpy as np
import threading
import time
import datetime
import subprocess
import os

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class AutoDoorOCR:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AutoDoor OCR 识别系统")
        self.root.geometry("700x600")  # 增大窗口尺寸以容纳更多控件
        self.root.resizable(True, True)  # 允许调整窗口大小
        self.root.minsize(650, 550)  # 设置最小尺寸
        
        # 配置参数
        self.ocr_interval = 5  # OCR识别间隔（秒）
        self.pause_duration = 180  # 暂停时长（秒）
        self.click_delay = 0.5  # 点击后等待时间（秒）
        self.custom_key = "equal"  # 自定义按键，默认为等号键
        
        # 关键词和语言配置
        self.custom_keywords = ["door", "men"]  # 自定义关键词列表
        self.ocr_language = "eng"  # OCR识别语言，默认为英文（eng）
        
        # 坐标轴参数
        self.click_x = 0  # 点击x坐标（相对于选择区域）
        self.click_y = 0  # 点击y坐标（相对于选择区域）
        self.click_mode = "center"  # 点击模式：center或custom
        
        # 状态变量
        self.selected_region = None  # (x1, y1, x2, y2)
        self.is_running = False
        self.is_paused = False
        self.is_selecting = False
        self.last_trigger_time = 0
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autodoor_config.json")
        
        # 日志文件路径
        self.log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "autodoor.log")
        
        # 线程控制
        self.ocr_thread = None
        
        # 初始化Tesseract相关变量
        self.tesseract_path = ""
        self.tesseract_available = False
        
        # 先创建界面元素，确保所有UI变量都被初始化
        self.create_widgets()
        
        # 加载配置（包括Tesseract路径）
        self.load_config()
        
        # 如果配置中没有Tesseract路径，使用项目自带的tesseract
        config_updated = False
        if not self.tesseract_path:
            self.tesseract_path = self.get_default_tesseract_path()
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
    

    
    def get_default_tesseract_path(self):
        """获取默认的Tesseract路径，使用项目自带的tesseract
        支持Windows和Mac平台，同时支持打包后的环境
        """
        import platform
        import sys
        
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))
        
        # 根据操作系统选择不同的tesseract路径
        if platform.system() == "Windows":
            # Windows平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract.exe")
        elif platform.system() == "Darwin":
            # macOS平台
            tesseract_path = os.path.join(app_root, "tesseract", "tesseract")
        else:
            # 其他平台，返回空
            tesseract_path = ""
        
        self.log_message(f"默认Tesseract路径: {tesseract_path}")
        return tesseract_path
    
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
        
        if not self.tesseract_path.endswith("tesseract.exe"):
            self.log_message(f"Tesseract路径不是可执行文件: {self.tesseract_path}")
            return False
        
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
                        major_version = int(version_str.split('.')[0])
                        if major_version < 4:
                            self.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        self.log_message(f"无法解析Tesseract版本: {version_str}")
                        # 继续执行，不因为版本解析失败而直接返回False
            
            # 3. 基础功能测试
            # 配置pytesseract使用找到的路径
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            
            # 创建一个简单的测试图像
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save('test_tesseract.png')
            
            # 尝试执行OCR识别
            test_result = pytesseract.image_to_string('test_tesseract.png', lang='eng', timeout=5)
            
            # 清理测试文件
            if os.path.exists('test_tesseract.png'):
                os.remove('test_tesseract.png')
            
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
        except Exception as e:
            self.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            return False
        
    def create_widgets(self):
        # 设置全局样式
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        style.configure("TButton", padding=5)
        
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
        
        # 区域信息
        self.region_var = tk.StringVar(value="未选择区域")
        region_label = ttk.Label(status_frame, textvariable=self.region_var, font=("Arial", 10))
        region_label.pack(side=tk.RIGHT)
        
        # 主内容区域 - 使用笔记本(tab)布局
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本设置标签页
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="基本设置")
        self.create_basic_tab(basic_frame)
        
        # 高级设置标签页
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="高级设置")
        self.create_advanced_tab(advanced_frame)
        
        # 日志标签页
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="日志")
        self.create_log_tab(log_frame)
        
        # 控制按钮区域
        control_frame = ttk.Frame(main_frame, padding="10 5 10 0")
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.select_btn = ttk.Button(control_frame, text="选择区域", command=self.start_region_selection)
        self.select_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="开始监控", command=self.start_monitoring, state="disabled")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="停止监控", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side=tk.LEFT)
        
        # 退出按钮在右侧
        exit_btn = ttk.Button(control_frame, text="退出程序", command=self.exit_program)
        exit_btn.pack(side=tk.RIGHT)
    
    def create_basic_tab(self, parent):
        """创建基本设置标签页"""
        # 基本设置区域
        basic_frame = ttk.Frame(parent, padding="10")
        basic_frame.pack(fill=tk.BOTH, expand=True)
        
        # 第一行：Tesseract配置和时间间隔设置
        top_frame = ttk.Frame(basic_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 左侧：Tesseract配置
        tesseract_frame = ttk.LabelFrame(top_frame, text="Tesseract配置", padding="10")
        tesseract_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
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
        
        # 右侧：时间间隔设置
        interval_frame = ttk.LabelFrame(top_frame, text="时间间隔设置", padding="10")
        interval_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 第二行：关键词和语言设置
        bottom_frame = ttk.Frame(basic_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：关键词设置
        keywords_frame = ttk.LabelFrame(bottom_frame, text="关键词设置", padding="10")
        keywords_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 关键词输入
        keywords_label = ttk.Label(keywords_frame, text="识别关键词（英文逗号分隔）:")
        keywords_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.keywords_var = tk.StringVar(value=",".join(self.custom_keywords))
        self.keywords_entry = ttk.Entry(keywords_frame, textvariable=self.keywords_var)
        self.keywords_entry.pack(fill=tk.X, pady=(0, 10))
        
        # 关键词操作按钮
        keyword_btn_frame = ttk.Frame(keywords_frame)
        keyword_btn_frame.pack(fill=tk.X)
        
        self.set_keywords_btn = ttk.Button(keyword_btn_frame, text="应用关键词", command=self.set_custom_keywords)
        self.set_keywords_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.reset_keywords_btn = ttk.Button(keyword_btn_frame, text="恢复默认", command=self.restore_default_keywords)
        self.reset_keywords_btn.pack(side=tk.LEFT)
        
        # 右侧：语言设置
        language_frame = ttk.LabelFrame(bottom_frame, text="语言设置", padding="10")
        language_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 语言选择
        language_label = ttk.Label(language_frame, text="OCR识别语言:")
        language_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.language_var = tk.StringVar(value=self.ocr_language)
        language_combobox = ttk.Combobox(language_frame, textvariable=self.language_var, 
                                        values=["eng", "chi_sim", "chi_tra"], 
                                        width=10)
        language_combobox.pack(fill=tk.X, pady=(0, 10))
        
        # 语言说明
        language_desc = ttk.Label(language_frame, text="eng: 英文 | chi_sim: 简体中文 | chi_tra: 繁体中文", 
                                font=("Arial", 8), foreground="gray")
        language_desc.pack(anchor=tk.W)
        
        # OCR识别间隔
        ocr_interval_label = ttk.Label(interval_frame, text=f"识别间隔: {self.ocr_interval}秒")
        ocr_interval_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.ocr_interval_var = tk.IntVar(value=self.ocr_interval)
        self.ocr_interval_scale = ttk.Scale(interval_frame, from_=1, to=30, orient=tk.HORIZONTAL,
                                         variable=self.ocr_interval_var, command=lambda x: self.update_interval_label(ocr_interval_label, "识别间隔", self.ocr_interval_var))
        self.ocr_interval_scale.pack(fill=tk.X, pady=(0, 10))
        
        ocr_interval_entry = ttk.Entry(interval_frame, textvariable=self.ocr_interval_var, width=5)
        ocr_interval_entry.pack(side=tk.RIGHT)
        
        # 暂停时长（检测到关键词后暂停识别的时间）
        pause_duration_label = ttk.Label(interval_frame, text=f"暂停时长: {self.pause_duration}秒")
        pause_duration_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.pause_duration_var = tk.IntVar(value=self.pause_duration)
        self.pause_duration_scale = ttk.Scale(interval_frame, from_=30, to=300, orient=tk.HORIZONTAL, length=150,
                                          variable=self.pause_duration_var, command=lambda x: self.update_interval_label(pause_duration_label, "暂停时长", self.pause_duration_var))
        self.pause_duration_scale.pack(fill=tk.X, pady=(0, 10))
        
        pause_duration_entry = ttk.Entry(interval_frame, textvariable=self.pause_duration_var, width=5)
        pause_duration_entry.pack(side=tk.RIGHT)
    
    def create_advanced_tab(self, parent):
        """创建高级设置标签页"""
        advanced_frame = ttk.Frame(parent, padding="10")
        advanced_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：坐标轴选取
        axis_frame = ttk.LabelFrame(advanced_frame, text="坐标轴选取", padding="10")
        axis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.create_axis_section(axis_frame)
        
        # 右侧：键位自定义
        key_frame = ttk.LabelFrame(advanced_frame, text="键位自定义", padding="10")
        key_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.create_key_section(key_frame)
        
        # 为配置变量添加监听器，自动保存配置
        self.setup_config_listeners()
    
    def create_axis_section(self, parent):
        """创建坐标轴选取区域"""
        # 点击模式选择
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.click_mode_var = tk.StringVar(value=self.click_mode)
        
        center_rbtn = ttk.Radiobutton(mode_frame, text="区域中心", variable=self.click_mode_var, value="center", command=self.update_axis_inputs)
        center_rbtn.pack(side=tk.LEFT, padx=(0, 15))
        
        custom_rbtn = ttk.Radiobutton(mode_frame, text="自定义坐标", variable=self.click_mode_var, value="custom", command=self.update_axis_inputs)
        custom_rbtn.pack(side=tk.LEFT)
        
        # 自定义坐标输入
        coord_frame = ttk.Frame(parent)
        coord_frame.pack(fill=tk.X)
        
        # X轴坐标
        x_frame = ttk.Frame(coord_frame)
        x_frame.pack(fill=tk.X, pady=(0, 10))
        
        x_label = ttk.Label(x_frame, text="X轴坐标:", width=10)
        x_label.pack(side=tk.LEFT)
        
        self.x_coord_var = tk.IntVar(value=self.click_x)
        self.x_coord_entry = ttk.Entry(x_frame, textvariable=self.x_coord_var, width=10, state="disabled")
        self.x_coord_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # Y轴坐标
        y_frame = ttk.Frame(coord_frame)
        y_frame.pack(fill=tk.X)
        
        y_label = ttk.Label(y_frame, text="Y轴坐标:", width=10)
        y_label.pack(side=tk.LEFT)
        
        self.y_coord_var = tk.IntVar(value=self.click_y)
        self.y_coord_entry = ttk.Entry(y_frame, textvariable=self.y_coord_var, width=10, state="disabled")
        self.y_coord_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 提示信息
        tip_label = ttk.Label(parent, text="自定义坐标相对于选择区域的左上角", font=("Arial", 8), foreground="gray")
        tip_label.pack(anchor=tk.W, pady=(10, 0))
    
    def create_key_section(self, parent):
        """创建键位自定义区域"""
        # 按键选择
        key_label = ttk.Label(parent, text="自动按键:")
        key_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 按键下拉菜单
        self.key_var = tk.StringVar(value=self.custom_key)
        self.key_combobox = ttk.Combobox(parent, textvariable=self.key_var, values=self.get_available_keys(), width=10)
        self.key_combobox.pack(fill=tk.X, pady=(0, 10))
        
        # 按键预览
        preview_frame = ttk.Frame(parent)
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        preview_btn = ttk.Button(preview_frame, text="预览按键", command=self.preview_key)
        preview_btn.pack(side=tk.LEFT)
        
        # 恢复默认
        default_btn = ttk.Button(preview_frame, text="恢复默认", command=self.restore_default_key)
        default_btn.pack(side=tk.RIGHT)
        
        # 提示信息
        key_tip_label = ttk.Label(parent, text="选择识别到关键词后自动按下的按键", font=("Arial", 8), foreground="gray")
        key_tip_label.pack(anchor=tk.W, pady=(10, 0))
    
    def create_log_tab(self, parent):
        """创建日志标签页"""
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=20, width=80, font=("Arial", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 滚动条
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 清除日志按钮
        clear_btn = ttk.Button(parent, text="清除日志", command=self.clear_log)
        clear_btn.pack(side=tk.BOTTOM, pady=5, anchor=tk.E)
    
    def update_interval_label(self, label, prefix, var, is_float=False):
        """更新时间间隔标签"""
        value = var.get()
        if is_float:
            value = round(value, 1)
        label.config(text=f"{prefix}: {value}秒")
        
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
            "space", "enter", "tab", "escape", "backspace", "delete",
            "equal", "plus", "minus", "asterisk", "slash", "backslash",
            "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down",
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
    
    def load_config(self):
        """加载配置
        增强错误处理，能够处理文件不存在、格式错误或路径配置缺失等异常情况
        """
        import json
        
        # 初始化配置加载结果
        config_loaded = False
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载Tesseract路径 - 最优先处理
                config_has_tesseract = False
                if 'tesseract_path' in config and config['tesseract_path']:
                    temp_path = config['tesseract_path'].strip()
                    # 检查路径是否存在
                    if os.path.exists(temp_path):
                        self.tesseract_path = temp_path
                        self.log_message(f"从配置文件加载Tesseract路径: {self.tesseract_path}")
                        config_has_tesseract = True
                    else:
                        self.log_message(f"配置文件中的Tesseract路径不存在: {temp_path}")
                
                # 加载时间间隔
                if 'ocr_interval' in config:
                    self.ocr_interval = config['ocr_interval']
                    self.ocr_interval_var.set(self.ocr_interval)
                
                if 'pause_duration' in config:
                    self.pause_duration = config['pause_duration']
                    self.pause_duration_var.set(self.pause_duration)
                
                # 加载选择区域
                if 'selected_region' in config:
                    self.selected_region = tuple(config['selected_region'])
                    self.region_var.set(f"区域: {self.selected_region[0]},{self.selected_region[1]} - {self.selected_region[2]},{self.selected_region[3]}")
                    self.start_btn.config(state="normal")
                
                # 加载自定义按键
                if 'custom_key' in config:
                    self.custom_key = config['custom_key']
                    self.key_var.set(self.custom_key)
                
                # 加载关键词
                if 'custom_keywords' in config:
                    self.custom_keywords = config['custom_keywords']
                    self.keywords_var.set(",".join(self.custom_keywords))
                
                # 加载语言设置
                if 'ocr_language' in config:
                    self.ocr_language = config['ocr_language']
                    self.language_var.set(self.ocr_language)
                
                self.log_message("配置加载成功")
                config_loaded = True
                
            except json.JSONDecodeError:
                self.log_message(f"配置文件格式错误: {self.config_file}")
            except PermissionError:
                self.log_message(f"没有权限读取配置文件: {self.config_file}")
            except Exception as e:
                self.log_message(f"配置加载错误: {str(e)}")
        else:
            self.log_message(f"配置文件不存在: {self.config_file}")
        
        # 如果配置加载成功，更新界面中的Tesseract路径变量
        if config_loaded and hasattr(self, 'tesseract_path_var'):
            self.tesseract_path_var.set(self.tesseract_path)
    

    
    def setup_config_listeners(self):
        """为配置变量添加监听器，自动保存配置"""
        # 为时间间隔变量添加监听器
        def on_interval_change(*args):
            # 延迟保存，避免频繁保存
            self.root.after(1000, self.save_config)
        
        # 为按键变量添加监听器
        def on_key_change(*args):
            self.save_config()
        
        # 为语言变量添加监听器
        def on_language_change(*args):
            self.save_config()
        
        # 添加监听器
        self.ocr_interval_var.trace_add("write", on_interval_change)
        self.pause_duration_var.trace_add("write", on_interval_change)
        self.key_var.trace_add("write", on_key_change)
        self.language_var.trace_add("write", on_language_change)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
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
        
        if not new_path.endswith("tesseract.exe"):
            messagebox.showwarning("警告", "请指定tesseract.exe可执行文件！")
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
        
        # 只有当log_text已经创建时才写入界面日志
        if hasattr(self, 'log_text'):
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # 更新状态标签（仅当status_var已创建）
        if hasattr(self, 'status_var'):
            self.status_var.set(message.split(":")[0] if ":" in message else message)
    
    def start_region_selection(self):
        """开始区域选择"""
        self.log_message("开始区域选择...")
        self.is_selecting = True
        
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
    
    def on_mouse_up(self, event):
        """鼠标释放事件"""
        # 获取结束绝对坐标
        end_x_abs = event.x_root
        end_y_abs = event.y_root
        
        # 确保选择区域有效
        if abs(end_x_abs - self.start_x_abs) < 10 or abs(end_y_abs - self.start_y_abs) < 10:
            messagebox.showwarning("警告", "选择的区域太小，请重新选择")
            self.cancel_selection()
            return
        
        # 保存选择区域（使用绝对坐标）
        self.selected_region = (
            min(self.start_x_abs, end_x_abs),
            min(self.start_y_abs, end_y_abs),
            max(self.start_x_abs, end_x_abs),
            max(self.start_y_abs, end_y_abs)
        )
        
        # 更新界面
        self.region_var.set(f"区域: {self.selected_region[0]},{self.selected_region[1]} - {self.selected_region[2]},{self.selected_region[3]}")
        self.start_btn.config(state="normal")
        
        self.log_message(f"已选择区域: {self.selected_region}")
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
            
        if not self.selected_region:
            messagebox.showwarning("警告", "请先选择监控区域")
            return
        
        self.is_running = True
        self.is_paused = False
        
        # 更新按钮状态
        self.select_btn.config(state="disabled")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        self.log_message("开始监控...")
        
        # 启动OCR线程
        self.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
        self.ocr_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        
        # 更新按钮状态
        self.select_btn.config(state="normal")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self.log_message("已停止监控")
    
    def ocr_loop(self):
        """OCR识别循环"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 检查是否需要暂停
                if self.is_paused:
                    time.sleep(1)
                    continue
                
                # 检查是否在暂停期
                pause_duration = self.pause_duration_var.get()
                if current_time - self.last_trigger_time < pause_duration:
                    remaining = int(pause_duration - (current_time - self.last_trigger_time))
                    self.status_var.set(f"暂停中... {remaining}秒")
                    time.sleep(1)
                    continue
                
                # 执行OCR识别
                self.perform_ocr()
                
                # 等待下一次识别
                ocr_interval = self.ocr_interval_var.get()
                for _ in range(ocr_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.log_message(f"错误: {str(e)}")
                time.sleep(5)
    
    def perform_ocr(self):
        """执行OCR识别"""
        try:
            # 截取屏幕区域
            x1, y1, x2, y2 = self.selected_region
            
            # 确保坐标是(left, top, right, bottom)格式，且left < right, top < bottom
            left = min(x1, x2)
            top = min(y1, y2)
            right = max(x1, x2)
            bottom = max(y1, y2)
            
            # 使用PIL的ImageGrab.grab()方法，设置all_screens=True捕获所有屏幕
            from PIL import ImageGrab
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
            
            # 转换为灰度图像以提高识别率
            screenshot = screenshot.convert('L')
            
            # 进行OCR识别
            current_lang = self.language_var.get()
            text = pytesseract.image_to_string(screenshot, lang=current_lang)
            
            self.log_message(f"识别结果: '{text.strip()}'")
            
            # 检查是否包含关键词
            lower_text = text.lower()
            if any(keyword in lower_text for keyword in self.custom_keywords):
                self.trigger_action()
                
        except Exception as e:
            self.log_message(f"OCR错误: {str(e)}")
    
    def save_config(self):
        """保存配置"""
        import json
        config = {
            'tesseract_path': self.tesseract_path,
            'ocr_interval': self.ocr_interval_var.get(),
            'pause_duration': self.pause_duration_var.get(),
            'selected_region': self.selected_region,
            'custom_key': self.key_var.get(),
            'custom_keywords': self.custom_keywords,
            'ocr_language': self.language_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            self.log_message("配置已保存")
        except Exception as e:
            self.log_message(f"配置保存错误: {str(e)}")
    
    def trigger_action(self):
        """触发动作序列"""
        self.log_message("检测到关键词，执行动作...")
        
        # 计算点击位置
        click_x, click_y = self.calculate_click_position()
        
        try:
            # 1. 鼠标左键点击指定位置
            pyautogui.click(click_x, click_y)
            self.log_message(f"点击位置: ({click_x}, {click_y})")
            
            # 2. 等待固定时间（无需用户修改）
            time.sleep(self.click_delay)
            
            # 3. 按下自定义按键
            custom_key = self.key_var.get()
            pyautogui.press(custom_key)
            self.log_message(f"按下了 {custom_key} 键")
            
            # 记录触发时间
            self.last_trigger_time = time.time()
            
        except Exception as e:
            self.log_message(f"动作执行错误: {str(e)}")
    
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
    
    def exit_program(self):
        """退出程序"""
        if self.is_running:
            self.stop_monitoring()
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
