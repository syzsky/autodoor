import tkinter as tk
from tkinter import ttk


# 从ui.builder导入UIBuilder
from ui.builder import UIBuilder


def create_timed_tab(parent, app):
    """创建定时功能标签页"""
    timed_frame = ttk.Frame(parent, padding="10")
    timed_frame.pack(fill=tk.BOTH, expand=True)

    # 顶部按钮栏
    top_frame = ttk.Frame(timed_frame)
    top_frame.pack(fill=tk.X, pady=(0, 10))

    # 新增组按钮
    app.add_timed_group_btn = ttk.Button(top_frame, text="新增定时组", command=lambda: add_timed_group(app))
    app.add_timed_group_btn.pack(side=tk.LEFT)

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
    app.timed_groups_frame = ttk.Frame(groups_canvas)
    groups_canvas.create_window((0, 0), window=app.timed_groups_frame, anchor="nw", tags="inner_frame")

    # 配置画布尺寸和滚动区域
    def configure_scroll_region(event):
        app._configure_scroll_region(event, groups_canvas, "inner_frame")

    groups_canvas.bind("<Configure>", configure_scroll_region)
    app.timed_groups_frame.bind("<Configure>", configure_scroll_region)

    # 为画布绑定鼠标滚轮事件
    groups_canvas.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 为内部框架绑定鼠标滚轮事件
    app.timed_groups_frame.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 为整个标签页绑定鼠标滚轮事件
    timed_frame.bind("<MouseWheel>", lambda event: app._on_mousewheel(event, groups_canvas))

    # 保存定时功能的画布和框架引用
    app.timed_canvas = groups_canvas
    app.timed_frame = timed_frame
    app.timed_groups_container = groups_container

    # 定时组配置
    app.timed_groups = []
    for i in range(3):
        create_timed_group(app, i)

    # 绑定所有定时组的鼠标滚轮事件
    app._bind_mousewheel_to_widgets(groups_canvas, [group["frame"] for group in app.timed_groups])


def create_timed_group(app, index):
    """创建单个定时组，所有UI元素布局在一行中"""
    # 启用状态变量
    enabled_var = tk.BooleanVar(value=False)
    
    # 创建变量字典
    group_vars = {
        "interval_var": tk.IntVar(value=10*(index+1)),
        "key_var": tk.StringVar(value=["space", "enter", "tab", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"][index % 15]),
        "delay_min_var": tk.IntVar(value=300),
        "delay_max_var": tk.IntVar(value=500),
        "alarm_var": tk.BooleanVar(value=False),
        "click_enabled_var": tk.BooleanVar(value=False),
        "position_var": tk.StringVar(value="未选择位置")
    }
    
    # 命令映射
    command_map = {
        "select_position": lambda: app.timed_module.start_timed_position_selection(index)
    }
    
    # 使用声明式UI构建
    group_frame = UIBuilder.build_module(app.timed_groups_frame, "timed", index, app, command_map, group_vars)

    # 设置组点击事件和样式更新
    app._setup_group_click_handler(group_frame, enabled_var)

    # 初始应用样式
    app.update_group_style(group_frame, enabled_var.get())

    # 添加删除按钮
    row1_frame = group_frame.winfo_children()[0]
    delete_btn = UIBuilder.add_button(row1_frame, "删除", None, side=tk.RIGHT, width=6)
    delete_btn.config(command=lambda btn=delete_btn: delete_timed_group_by_button(app, btn))

    # 保存组配置
    group_config = {
        "frame": group_frame,
        "enabled": enabled_var,
        "interval": group_vars["interval_var"],
        "key": group_vars["key_var"],
        "delay_min": group_vars["delay_min_var"],
        "delay_max": group_vars["delay_max_var"],
        "alarm": group_vars["alarm_var"],
        "click_enabled": group_vars["click_enabled_var"],
        "position_x": tk.IntVar(value=0),
        "position_y": tk.IntVar(value=0),
        "position_var": group_vars["position_var"]
    }
    app.timed_groups.append(group_config)

    # 为新创建的定时组添加配置监听器
    if hasattr(app, '_setup_timed_group_listeners'):
        app._setup_timed_group_listeners(group_config)


def delete_timed_group_by_button(app, button):
    """通过按钮删除对应的定时组"""
    app._delete_group_by_button(button, app.timed_groups, "定时组", lambda i: delete_timed_group(app, i))


def delete_timed_group(app, index, confirm=True):
    """删除定时组
    Args:
        index: 要删除的定时组索引
        confirm: 是否显示确认对话框，默认为True
    """
    app._delete_group(index, app.timed_groups, "定时组", 1, lambda: renumber_timed_groups(app), "定时组", confirm)


def renumber_timed_groups(app):
    """重新编号所有定时组"""
    for i, group in enumerate(app.timed_groups):
        # 保持组名称前的空格，确保布局一致
        group["frame"].configure(text=f"  定时组{i+1}")


def add_timed_group(app):
    """新增定时组"""
    app._add_group(app.timed_groups, 15, lambda i: create_timed_group(app, i), "定时组", "定时组")
