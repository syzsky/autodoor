import tkinter as tk
from tkinter import messagebox


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
    """显示带按钮的消息框"""
    if buttons is None:
        messagebox.showinfo(title, message)
        return
    
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.geometry("400x250")
    dialog.transient(root)
    dialog.grab_set()
    
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
    
    from tkinter import ttk
    frame = ttk.Frame(dialog, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text=message, wraplength=360).pack(pady=(0, 20))
    
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, pady=(10, 0))
    
    for text, command in buttons:
        ttk.Button(button_frame, text=text, command=lambda c=command, d=dialog: (c() if c else None, d.destroy())).pack(side=tk.LEFT, padx=(0, 10))


def show_progress(status_var, message):
    """显示进度提示"""
    status_var.set(message)
    status_var.get()


def hide_progress(status_var):
    """隐藏进度提示"""
    status_var.set("就绪")
    status_var.get()


def toggle_ui_state(root_widget, state, global_stop_btn=None):
    """递归地禁用或启用根控件及其所有子控件"""
    if root_widget == global_stop_btn:
        return

    try:
        root_widget.configure(state=state)
    except (tk.TclError, AttributeError):
        pass

    for child in root_widget.winfo_children():
        toggle_ui_state(child, state, global_stop_btn)


def update_group_style(group_frame, enabled):
    """更新组样式 - CustomTkinter版本
    Args:
        group_frame: 要更新样式的组框架
        enabled: 组是否启用
    """
    try:
        from ui.theme import Theme
        if enabled:
            group_frame.configure(fg_color=Theme.COLORS['info_light'], border_color=Theme.COLORS['primary'])
        else:
            group_frame.configure(fg_color='#ffffff', border_color=Theme.COLORS['border'])
    except Exception:
        pass


def create_group_frame(parent_frame, index, group_type):
    """创建组框架 - CustomTkinter版本"""
    import customtkinter as ctk
    from ui.theme import Theme
    from ui.widgets import CardFrame
    
    group_frame = CardFrame(parent_frame, fg_color='#ffffff', border_width=1, border_color=Theme.COLORS['border'])
    group_frame.pack(fill='x', pady=(0, 10))
    return group_frame


def setup_group_click_handler(app, group_frame, enabled_var):
    """设置组点击事件处理器 - CustomTkinter版本"""
    def on_group_click(event):
        try:
            import customtkinter as ctk
            if isinstance(event.widget, (ctk.CTkEntry, ctk.CTkButton, ctk.CTkComboBox, ctk.CTkSwitch)):
                return
        except:
            pass

        new_state = not enabled_var.get()
        enabled_var.set(new_state)
        
        app.logging_manager.log_message(f"状态切换为{'启用' if new_state else '禁用'}")

        update_group_style(group_frame, new_state)

    enabled_var.trace_add("write", lambda *args: update_group_style(group_frame, enabled_var.get()))
