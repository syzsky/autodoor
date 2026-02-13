import tkinter as tk
from tkinter import messagebox, ttk


def on_mousewheel(event, canvas):
    """公共的鼠标滚轮事件处理函数"""
    current_pos = canvas.yview()
    scroll_amount = event.delta / 120 / 10
    new_pos = current_pos[0] - scroll_amount
    new_pos = max(0, min(1, new_pos))
    canvas.yview_moveto(new_pos)
    return "break"


def configure_scroll_region(event, canvas, frame_tag):
    """公共的滚动区域配置函数"""
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig(frame_tag, width=canvas.winfo_width())


def bind_mousewheel_to_widgets(canvas, widgets):
    """为指定的控件及其子控件绑定鼠标滚轮事件"""
    def on_mousewheel_handler(event):
        return on_mousewheel(event, canvas)

    for widget in widgets:
        widget.bind("<MouseWheel>", on_mousewheel_handler)
        for child in widget.winfo_children():
            child.bind("<MouseWheel>", on_mousewheel_handler)
            for grandchild in child.winfo_children():
                grandchild.bind("<MouseWheel>", on_mousewheel_handler)


def show_message(root, title, message, buttons=None):
    """显示带按钮的消息框
    Args:
        root: 根窗口
        title: 消息框标题
        message: 消息内容
        buttons: 按钮列表，每个元素为 (文本, 命令) 元组
    """
    if buttons is None:
        messagebox.showinfo(title, message)
        return
    
    # 创建自定义对话框
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry("400x250")
    dialog.transient(root)
    dialog.grab_set()
    
    # 计算位置，使对话框居中显示
    root.update_idletasks()
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    
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


def show_progress(status_var, message):
    """显示进度提示
    Args:
        status_var: 状态栏变量
        message: 进度消息
    """
    # 更新状态栏
    status_var.set(message)
    # 强制更新UI
    status_var.get()  # 触发变量获取，确保更新


def hide_progress(status_var):
    """隐藏进度提示
    Args:
        status_var: 状态栏变量
    """
    # 恢复状态栏
    status_var.set("就绪")
    # 强制更新UI
    status_var.get()  # 触发变量获取，确保更新


def toggle_ui_state(root_widget, state, global_stop_btn=None):
    """递归地禁用或启用根控件及其所有子控件
    Args:
        root_widget: 根控件
        state: 控件状态，"disabled" 或 "normal"
        global_stop_btn: 全局停止按钮，始终保持可用
    """
    # 跳过停止运行按钮，始终保持可用
    if root_widget == global_stop_btn:
        return

    try:
        # 尝试设置控件状态
        root_widget.configure(state=state)
    except (tk.TclError, AttributeError):
        # 某些控件（如Frame）没有state属性，跳过
        pass

    # 递归处理所有子控件
    for child in root_widget.winfo_children():
        toggle_ui_state(child, state, global_stop_btn)


def update_child_styles(widget, is_enabled):
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
        ttk.Entry: lambda: "TEntry",
        ttk.LabelFrame: lambda: "Green.TLabelframe" if is_enabled else "TLabelframe"
    }

    # 特殊处理Label组件
    if isinstance(widget, ttk.Label):
        if widget.cget("relief") != "sunken":
            widget.configure(style="Green.TLabel" if is_enabled else "TLabel")
    else:
        for widget_type, style_func in style_mappings.items():
            if isinstance(widget, widget_type):
                widget.configure(style=style_func())
                break

    # 递归处理所有子组件
    for child in widget.winfo_children():
        update_child_styles(child, is_enabled)


def update_group_style(group_frame, enabled):
    """更新组样式
    Args:
        group_frame: 要更新样式的组框架
        enabled: 组是否启用
    """
    if enabled:
        group_frame.configure(style="Green.TLabelframe")
    else:
        group_frame.configure(style="TLabelframe")

    update_child_styles(group_frame, enabled)


def create_group_frame(parent_frame, index, group_type):
    """创建组框架
    Args:
        parent_frame: 父框架
        index: 组索引
        group_type: 组类型名称
    
    Returns:
        组框架
    """
    group_frame = ttk.LabelFrame(parent_frame, text=f"{group_type}{index+1}", padding="10")
    group_frame.pack(fill=tk.X, pady=(0, 10))
    group_frame.configure(relief=tk.GROOVE, borderwidth=2)
    return group_frame


def setup_group_click_handler(app, group_frame, enabled_var):
    """设置组点击事件处理器
    Args:
        app: 主应用实例
        group_frame: 组框架
        enabled_var: 启用状态变量
    """
    def on_group_click(event):
        if isinstance(event.widget, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
            return

        new_state = not enabled_var.get()
        enabled_var.set(new_state)
        
        frame_text = group_frame.cget("text")
        app.logging_manager.log_message(f"[{app.platform_adapter.platform}] 点击{frame_text}，状态切换为{'启用' if new_state else '禁用'}")

        update_group_style(group_frame, new_state)

    enabled_var.trace_add("write", lambda *args: update_group_style(group_frame, enabled_var.get()))

    group_frame.bind("<Button-1>", on_group_click)

    if hasattr(group_frame, 'label'):
        group_frame.label.bind("<Button-1>", on_group_click)

    def bind_child_events(widget):
        for child in widget.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                pass
            else:
                child.bind("<Button-1>", on_group_click)
                bind_child_events(child)

    bind_child_events(group_frame)

    group_frame.configure(cursor="hand2")
    group_frame.configure(padding="12")
