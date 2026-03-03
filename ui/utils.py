from ui.theme import Theme
from tkinter import messagebox


def update_group_style(group_frame, enabled):
    """更新组的样式"""
    if enabled:
        group_frame.configure(fg_color=Theme.COLORS['info_light'], 
                            border_color=Theme.COLORS['primary'])
    else:
        group_frame.configure(fg_color='#ffffff', 
                            border_color=Theme.COLORS['border'])


def toggle_group_bg(frame, enabled):
    """切换组背景色（update_group_style 的别名）"""
    update_group_style(frame, enabled)


def add_group(app, groups, create_func, listener_setup_func=None, max_count=15):
    """通用新增组方法
    
    Args:
        app: 主应用实例
        groups: 组列表（如 app.ocr_groups）
        create_func: 创建组的函数（如 lambda idx: create_ocr_group(app, idx)）
        listener_setup_func: 设置监听器的函数（可选）
        max_count: 最大允许数量，默认 15
    
    Returns:
        bool: 是否成功创建
    """
    if len(groups) >= max_count:
        messagebox.showwarning("警告", f"最多只能创建{max_count}个组！")
        return False
    
    create_func(len(groups))
    
    if listener_setup_func and groups:
        listener_setup_func(groups[-1])
    
    if hasattr(app, 'config_manager'):
        app.config_manager.defer_save_config()
    
    return True


def delete_group(app, groups, group_frame, renumber_func, confirm=True, confirm_message="确定要删除该组吗？"):
    """通用删除组方法
    
    Args:
        app: 主应用实例
        groups: 组列表（如 app.ocr_groups）
        group_frame: 要删除的组框架
        renumber_func: 重新编号函数（如 lambda: renumber_ocr_groups(app)）
        confirm: 是否显示确认对话框
        confirm_message: 确认消息
    
    Returns:
        bool: 是否成功删除
    """
    if confirm:
        if not messagebox.askyesno("确认删除", confirm_message):
            return False
    
    for i, group in enumerate(groups):
        if group["frame"] == group_frame:
            group["frame"].destroy()
            groups.pop(i)
            renumber_func()
            
            if hasattr(app, 'config_manager'):
                app.config_manager.defer_save_config()
            
            return True
    
    return False
