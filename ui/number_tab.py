import tkinter as tk
from tkinter import ttk

from utils.region import _start_selection
from ui.utils import update_group_style, setup_group_click_handler, bind_mousewheel_to_widgets, on_mousewheel, configure_scroll_region
from core.utils import delete_group_by_button, delete_group, add_group

# 从ui.builder导入UIBuilder
from ui.builder import UIBuilder


def create_number_tab(parent, app):
    """创建数字识别标签页"""
    number_frame = ttk.Frame(parent, padding="10")
    number_frame.pack(fill=tk.BOTH, expand=True)

    # 顶部按钮栏
    top_frame = ttk.Frame(number_frame)
    top_frame.pack(fill=tk.X, pady=(0, 10))

    app.add_number_region_btn = ttk.Button(top_frame, text="新增识别组", command=app.number.add_region)
    app.add_number_region_btn.pack(side=tk.LEFT)

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
    app.number_regions_frame = ttk.Frame(regions_canvas)
    regions_canvas.create_window((0, 0), window=app.number_regions_frame, anchor="nw", tags="inner_frame")

    # 配置画布尺寸和滚动区域
    def configure_scroll_region_handler(event):
        configure_scroll_region(event, regions_canvas, "inner_frame")

    regions_canvas.bind("<Configure>", configure_scroll_region_handler)
    app.number_regions_frame.bind("<Configure>", configure_scroll_region_handler)

    # 为画布绑定鼠标滚轮事件
    regions_canvas.bind("<MouseWheel>", lambda event: on_mousewheel(event, regions_canvas))

    # 为内部框架绑定鼠标滚轮事件
    app.number_regions_frame.bind("<MouseWheel>", lambda event: on_mousewheel(event, regions_canvas))

    # 为整个标签页绑定鼠标滚轮事件
    number_frame.bind("<MouseWheel>", lambda event: on_mousewheel(event, regions_canvas))

    # 保存数字识别的画布和框架引用
    app.number_canvas = regions_canvas
    app.number_frame = number_frame
    app.number_regions_container = regions_container

    # 区域配置
    app.number_regions = []
    for i in range(2):
        create_number_region(app, i)

    # 绑定所有数字识别区域的鼠标滚轮事件
    bind_mousewheel_to_widgets(regions_canvas, [region["frame"] for region in app.number_regions])

    # 操作按钮已移除，统一由首页全局控制


def create_number_region(app, index):
    """创建单个数字识别区域"""
    # 启用状态变量
    enabled_var = tk.BooleanVar(value=False)
    
    # 创建变量字典
    group_vars = {
        "region_var": tk.StringVar(value="未选择区域"),
        "threshold_var": tk.IntVar(value=500 if index == 0 else 1000),
        "key_var": tk.StringVar(value=["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "space", "enter", "tab"][index % 15]),
        "delay_min_var": tk.IntVar(value=100),
        "delay_max_var": tk.IntVar(value=200),
        "alarm_var": tk.BooleanVar(value=False)
    }
    
    # 命令映射
    command_map = {
        "select_region": lambda: start_number_region_selection(app, index)
    }
    
    # 使用声明式UI构建
    region_frame = UIBuilder.build_module(app.number_regions_frame, "number", index, app, command_map, group_vars)

    # 设置组点击事件和样式更新
    setup_group_click_handler(app, region_frame, enabled_var)

    # 初始应用样式
    update_group_style(region_frame, enabled_var.get())

    # 添加删除按钮
    row1_frame = region_frame.winfo_children()[0]
    delete_btn = UIBuilder.add_button(row1_frame, "删除", None, side=tk.RIGHT, width=6)
    delete_btn.config(command=lambda btn=delete_btn: delete_number_region_by_button(app, btn))

    # 保存区域配置
    region_config = {
        "frame": region_frame,
        "enabled": enabled_var,
        "region_var": group_vars["region_var"],
        "region": None,
        "threshold": group_vars["threshold_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"]
    }
    app.number_regions.append(region_config)

    # 为新创建的数字识别区域添加配置监听器
    if hasattr(app, '_setup_region_listeners'):
        app._setup_region_listeners(region_config)

    # 为新创建的数字识别区域绑定鼠标滚轮事件
    # 获取当前标签页的画布
    canvas = app.number_regions_frame.master
    if isinstance(canvas, tk.Canvas):
        bind_mousewheel_to_widgets(canvas, [region_frame])


def delete_number_region_by_button(app, button):
    """通过按钮删除对应的数字识别区域"""
    delete_group_by_button(app, button, app.number_regions, "数字识别区域", lambda i: delete_number_region(app, i))


def delete_number_region(app, index, confirm=True):
    """删除数字识别区域
    Args:
        index: 要删除的区域索引
        confirm: 是否显示确认对话框，默认为True
    """
    delete_group(app, index, app.number_regions, "数字识别区域", 1, lambda: renumber_number_regions(app), "识别组", confirm)


def renumber_number_regions(app):
    """重新编号所有数字识别区域"""
    for i, region in enumerate(app.number_regions):
        # 更新区域标题为"识别组"，保持名称前的空格
        region["frame"].configure(text=f"  识别组{i+1}")


def add_number_region(app):
    """新增数字识别区域"""
    add_group(app, app.number_regions, 15, lambda i: create_number_region(app, i), "识别区域", "识别区域")


def start_number_region_selection(app, region_index):
    """开始选择数字识别区域"""
    _start_selection(app, "number", region_index)
