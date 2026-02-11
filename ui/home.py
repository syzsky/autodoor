import tkinter as tk
from tkinter import ttk


def create_home_tab(parent, app):
    """创建首页标签页"""
    home_frame = ttk.Frame(parent, padding="20")
    home_frame.pack(fill=tk.BOTH, expand=True)

    # 功能状态显示
    status_frame = ttk.LabelFrame(home_frame, text="功能状态", padding="15")
    status_frame.pack(fill=tk.X, pady=(0, 20))

    # 状态标签和勾选框
    app.status_labels = {
        "ocr": tk.StringVar(value="文字识别: 未运行"),
        "timed": tk.StringVar(value="定时功能: 未运行"),
        "number": tk.StringVar(value="数字识别: 未运行"),
        "script": tk.StringVar(value="脚本运行: 未运行")
    }

    # 勾选框变量
    app.module_check_vars = {
        "ocr": tk.BooleanVar(value=True),
        "timed": tk.BooleanVar(value=True),
        "number": tk.BooleanVar(value=True),
        "script": tk.BooleanVar(value=True)
    }

    # 保存Checkbutton组件引用
    app.module_check_buttons = {}

    # 模块名称映射
    module_names = {
        "ocr": "文字识别",
        "timed": "定时功能",
        "number": "数字识别",
        "script": "脚本运行"
    }

    # 创建带勾选框的状态行
    for module, var in app.status_labels.items():
        row_frame = ttk.Frame(status_frame)
        row_frame.pack(fill=tk.X, pady=2)  # 减少行间隔

        # 勾选框
        check_btn = ttk.Checkbutton(row_frame, variable=app.module_check_vars[module])
        check_btn.pack(side=tk.LEFT, padx=(0, 10))
        app.module_check_buttons[module] = check_btn

        # 状态标签 - 左对齐并填充可用空间，确保文本完整显示
        ttk.Label(row_frame, textvariable=var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 全局控制按钮 - 重新定位至功能状态区域下方
    control_frame = ttk.Frame(status_frame)
    control_frame.pack(fill=tk.X, pady=(15, 0))

    # 开始/结束按钮
    app.global_start_btn = ttk.Button(control_frame, text="开始运行", command=app.start_all, style="TButton")
    app.global_start_btn.pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)

    app.global_stop_btn = ttk.Button(control_frame, text="停止运行", command=app.stop_all, style="TButton", state="disabled")
    app.global_stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)



    # 日志展示模块 - 添加到首页功能状态模块下方
    log_frame = ttk.LabelFrame(home_frame, text="运行日志", padding="15")
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    # 日志显示区域
    log_display_frame = ttk.Frame(log_frame)
    log_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    # 日志文本框
    app.home_log_text = tk.Text(log_display_frame, height=15, width=80, font=("Arial", 9), state=tk.DISABLED)
    app.home_log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    # 日志滚动条
    home_log_scrollbar = ttk.Scrollbar(log_display_frame, orient=tk.VERTICAL, command=app.home_log_text.yview)
    home_log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app.home_log_text.configure(yscrollcommand=home_log_scrollbar.set)

    # 清除日志按钮 - 放置在日志展示窗口下方，固定宽度
    home_clear_btn = ttk.Button(log_frame, text="清除日志", command=app.clear_log, width=12)
    home_clear_btn.pack(side=tk.RIGHT, pady=5)
