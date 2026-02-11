import tkinter as tk
from tkinter import ttk


def start_key_listening(app, target_var, button, is_shortcut=False):
    """开始监听用户按下的按键"""
    # 保存当前焦点
    current_focus = app.root.focus_get()
    
    # 保存原始状态文本，用于恢复
    original_status = app.status_var.get()
    
    # 更新按钮状态
    original_text = button.cget("text")
    button.config(state="disabled")
    
    # 在原有状态栏显示提示信息
    app.status_var.set("请按任意按键进行设置，按ESC键清空当前记录")
    
    # 创建按键监听函数
    def on_key_press(event):
        """处理按键按下事件
        屏蔽中文输入法，只处理物理按键事件
        """
        # 恢复原始状态文本
        app.status_var.set(original_status)
        
        # 获取按键名称 - 使用keysym获取物理按键，而非字符
        keysym = event.keysym
        
        # 过滤掉中文输入法相关事件
        # 只处理物理按键，不处理输入法生成的字符
        # 允许的按键类型：
        # 1. 单个字符（如字母、数字、符号）
        # 2. 功能按键（如Insert、Delete、Home、End、PageUp、PageDown等）
        if not keysym:
            # 无效按键，跳过
            return "break"
        
        # 允许的功能按键列表
        allowed_function_keys = [
            "Insert", "Delete", "Home", "End", "Prior", "Next", "PageUp", "PageDown",
            "Up", "Down", "Left", "Right",
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Escape", "Tab", "Return", "Enter", "Space", "space", "BackSpace", "Backspace",
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"
        ]
        
        # 检查按键是否允许：
        # - 单个字符，或
        # - 在允许的功能按键列表中，或
        # - 以"Key"开头的按键
        if not (
            len(keysym) == 1 or 
            keysym in allowed_function_keys or 
            keysym.startswith("Key")
        ):
            # 这可能是一个输入法生成的字符，跳过
            return "break"
        
        # 按键名称映射表 - 将系统按键名称转换为用户友好的名称
        keysym_map = {
            "Prior": "PageUp",    # PageUp键在Tkinter中可能被识别为Prior
            "Next": "PageDown",   # PageDown键在Tkinter中可能被识别为Next
            "Return": "Enter",    # Return键转换为更常用的Enter
            "space": "Space"      # 确保空格键名称一致
        }
        
        # 转换按键名称为用户友好的名称
        keysym = keysym_map.get(keysym, keysym)
        
        # 特殊处理ESC键：清空当前记录的按键
        if keysym == "Escape":
            # 清空当前按键配置
            target_var.set("")
            
            # 恢复按钮状态
            button.config(state="normal")
            
            # 解除按键监听
            app.root.unbind("<KeyPress>", funcid=key_listener_id)
            
            # 恢复焦点
            if current_focus:
                current_focus.focus_set()
            
            return "break"  # 阻止事件继续传播
        
        # 设置按键值
        target_var.set(keysym)
        
        # 如果是快捷键设置，更新快捷键对象
        if is_shortcut:
            app.update_hotkey()
        
        # 恢复按钮状态
        button.config(state="normal")
        
        # 解除按键监听
        app.root.unbind("<KeyPress>", funcid=key_listener_id)
        
        # 恢复焦点
        if current_focus:
            current_focus.focus_set()
        
        return "break"  # 阻止事件继续传播
    
    # 绑定按键事件
    key_listener_id = app.root.bind("<KeyPress>", on_key_press)
    
    # 设置窗口焦点，确保能捕获按键事件
    app.root.focus_set()
