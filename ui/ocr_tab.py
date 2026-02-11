import tkinter as tk
from tkinter import ttk

from utils.region import _start_selection

# 从ui.builder导入UIBuilder
from ui.builder import UIBuilder


def create_ocr_tab(parent, app):
    """创建文字识别标签页"""
    ocr_frame = ttk.Frame(parent, padding="10")
    ocr_frame.pack(fill=tk.BOTH, expand=True)

    # 顶部按钮栏
    top_frame = ttk.Frame(ocr_frame)
    top_frame.pack(fill=tk.X, pady=(0, 10))

    # 新增组按钮
    app.add_ocr_group_btn = ttk.Button(top_frame, text="新增识别组", command=app.add_ocr_group)
    app.add_ocr_group_btn.pack(side=tk.LEFT)

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
    app.ocr_groups_frame = ttk.Frame(groups_canvas)
    groups_canvas.create_window((0, 0), window=app.ocr_groups_frame, anchor="nw", tags="inner_frame")

    # 配置画布尺寸和滚动区域
    def configure_scroll_region(event):
        app._configure_scroll_region(event, groups_canvas, "inner_frame")

    groups_canvas.bind("<Configure>", configure_scroll_region)
    app.ocr_groups_frame.bind("<Configure>", configure_scroll_region)

    # 为画布绑定鼠标滚轮事件
    groups_canvas.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 为内部框架绑定鼠标滚轮事件
    app.ocr_groups_frame.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 为整个标签页绑定鼠标滚轮事件
    ocr_frame.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 保存文字识别的画布和框架引用
    app.ocr_canvas = groups_canvas
    app.ocr_frame = ocr_frame
    app.ocr_groups_container = groups_container

    # 区域配置
    app.ocr_groups = []
    for i in range(2):
        create_ocr_group(app, i)

    # 绑定所有文字识别区域的鼠标滚轮事件
    app._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in app.ocr_groups])


def create_ocr_group(app, index):
    """创建单个文字识别组"""
    # 启用状态变量
    enabled_var = tk.BooleanVar(value=False)
    
    # 创建变量字典
    group_vars = {
        "region_var": tk.StringVar(value="未选择区域"),
        "interval_var": tk.IntVar(value=5),
        "pause_var": tk.IntVar(value=180),
        "key_var": tk.StringVar(value="equal"),
        "delay_min_var": tk.IntVar(value=300),
        "delay_max_var": tk.IntVar(value=500),
        "alarm_var": tk.BooleanVar(value=False),
        "keywords_var": tk.StringVar(value="men,door"),
        "language_var": tk.StringVar(value="eng"),
        "click_var": tk.BooleanVar(value=True)
    }
    
    # 命令映射
    command_map = {
        "select_region": lambda: start_ocr_region_selection(app, index)
    }
    
    # 使用声明式UI构建
    group_frame = UIBuilder.build_module(app.ocr_groups_frame, "ocr", index, app, command_map, group_vars)

    # 设置组点击事件和样式更新
    app._setup_group_click_handler(group_frame, enabled_var)

    # 初始应用样式
    app.update_group_style(group_frame, enabled_var.get())

    # 添加删除按钮
    row1_frame = group_frame.winfo_children()[0]
    delete_btn = UIBuilder.add_button(row1_frame, "删除", None, side=tk.RIGHT, width=6)
    delete_btn.config(command=lambda btn=delete_btn: delete_ocr_group_by_button(app, btn))

    # 保存组配置
    group_config = {
        "frame": group_frame,
        "enabled": enabled_var,
        "region_var": group_vars["region_var"],
        "region": None,
        "interval": group_vars["interval_var"],
        "pause": group_vars["pause_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"],
        "keywords": group_vars["keywords_var"],
        "language": group_vars["language_var"],
        "click": group_vars["click_var"]
    }
    app.ocr_groups.append(group_config)

    # 为新创建的识别组添加配置监听器
    if hasattr(app, '_setup_ocr_group_listeners'):
        app._setup_ocr_group_listeners(group_config)

    # 为新创建的识别组绑定鼠标滚轮事件
    canvas = app.ocr_groups_frame.master
    if isinstance(canvas, tk.Canvas):
        app._bind_mousewheel_to_widgets(canvas, [group_frame])


def add_ocr_group(app):
    """新增文字识别组"""
    app._add_group(app.ocr_groups, 15, lambda i: create_ocr_group(app, i), "识别组", "文字识别组")


def delete_ocr_group_by_button(app, button):
    """通过按钮删除对应的文字识别组"""
    app._delete_group_by_button(button, app.ocr_groups, "识别组", lambda i: delete_ocr_group(app, i))


def delete_ocr_group(app, index, confirm=True):
    """删除文字识别组"""
    app._delete_group(index, app.ocr_groups, "识别组", 1, lambda: renumber_ocr_groups(app), "文字识别组", confirm)


def renumber_ocr_groups(app):
    """重新编号所有文字识别组"""
    for i, group in enumerate(app.ocr_groups):
        # 保持组名称前的空格，确保布局一致
        group["frame"].configure(text=f"  识别组{i+1}")


def start_ocr_region_selection(app, index):
    """开始选择OCR识别区域"""
    _start_selection(app, "ocr", index)
