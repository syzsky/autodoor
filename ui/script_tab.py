import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import ImageGrab
import screeninfo

from utils.keyboard import start_key_listening

def create_script_tab(parent, app):
    """创建脚本运行标签页"""
    script_frame = ttk.Frame(parent, padding="10")
    script_frame.pack(fill=tk.BOTH, expand=True)

    # 左右容器
    left_right_frame = ttk.Frame(script_frame)
    left_right_frame.pack(fill=tk.BOTH, expand=True)

    # 左侧：命令输入区域，占据剩余空间
    left_frame = ttk.LabelFrame(left_right_frame, text="命令输入", padding="10")
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    # 按键命令组
    key_cmd_frame = ttk.LabelFrame(left_frame, text="按键命令", padding="8")
    key_cmd_frame.pack(fill=tk.X, pady=(0, 8))

    # 参数行 - 所有参数和插入按钮在同一行
    params_row = ttk.Frame(key_cmd_frame)
    params_row.pack(fill=tk.X)

    # 按键名称
    ttk.Label(params_row, text="按键:", width=5).pack(side=tk.LEFT)
    app.key_var = tk.StringVar(value="1")
    current_key_label = ttk.Label(params_row, textvariable=app.key_var, relief="sunken", padding=4, width=5)
    current_key_label.pack(side=tk.LEFT, padx=(0, 2))

    # 设置按键按钮 - 缩短为"修改"并减小宽度
    app.set_key_btn = ttk.Button(params_row, text="修改", width=4, 
                                command=lambda: start_key_listening(app, app.key_var, app.set_key_btn))
    app.set_key_btn.pack(side=tk.LEFT, padx=(0, 2))

    # 按键指令类型（按下/抬起）- 增加宽度和间距，确保完整显示
    ttk.Label(params_row, text="类型:", width=5).pack(side=tk.LEFT, padx=(0, 5))
    app.key_type = tk.StringVar(value="KeyDown")
    key_type_combo = ttk.Combobox(params_row, textvariable=app.key_type, values=["KeyDown", "KeyUp"], width=8)
    key_type_combo.pack(side=tk.LEFT, padx=(0, 5))

    # 执行次数变量（保留供逻辑使用）
    app.key_count = tk.IntVar(value=1)

    # 插入按键命令按钮 - 放在同一行，固定宽度
    app.insert_key_btn = ttk.Button(params_row, text="插入命令", command=lambda: insert_key_command(app), width=10)
    app.insert_key_btn.pack(side=tk.LEFT, padx=(10, 0))

    # 延迟命令组
    delay_cmd_frame = ttk.LabelFrame(left_frame, text="延迟命令", padding="8")
    delay_cmd_frame.pack(fill=tk.X, pady=(0, 8))

    # 延迟时间和插入按钮在同一行
    delay_row = ttk.Frame(delay_cmd_frame)
    delay_row.pack(fill=tk.X)

    ttk.Label(delay_row, text="延迟(ms):", width=8).pack(side=tk.LEFT, padx=(0, 5))
    app.delay_entry = ttk.Entry(delay_row, width=8)
    app.delay_entry.pack(side=tk.LEFT, padx=(0, 10))
    app.delay_entry.insert(0, "250")

    # 插入延迟命令按钮 - 放在同一行，固定宽度
    app.insert_delay_btn = ttk.Button(delay_row, text="插入命令", command=lambda: insert_delay_command(app), width=10)
    app.insert_delay_btn.pack(side=tk.LEFT, padx=(10, 0))

    # 鼠标命令组
    mouse_cmd_frame = ttk.LabelFrame(left_frame, text="鼠标命令", padding="8")
    mouse_cmd_frame.pack(fill=tk.X, pady=(0, 8))

    # 鼠标点击命令和插入按钮在同一行
    mouse_click_frame = ttk.Frame(mouse_cmd_frame)
    mouse_click_frame.pack(fill=tk.X, pady=(0, 4))

    # 鼠标按键选择
    ttk.Label(mouse_click_frame, text="按键:", width=5).pack(side=tk.LEFT)
    app.mouse_button_var = tk.StringVar(value="Left")
    mouse_button_combo = ttk.Combobox(mouse_click_frame, textvariable=app.mouse_button_var, values=["Left", "Right", "Middle"], width=8)
    mouse_button_combo.pack(side=tk.LEFT, padx=(0, 5))

    # 鼠标操作类型
    ttk.Label(mouse_click_frame, text="操作:", width=5).pack(side=tk.LEFT)
    app.mouse_action_var = tk.StringVar(value="Down")
    mouse_action_combo = ttk.Combobox(mouse_click_frame, textvariable=app.mouse_action_var, values=["Down", "Up"], width=8)
    mouse_action_combo.pack(side=tk.LEFT, padx=(0, 5))

    # 执行次数变量（保留供逻辑使用）
    app.mouse_count_var = tk.IntVar(value=1)

    # 插入鼠标点击命令按钮 - 放在同一行，固定宽度
    app.insert_mouse_click_btn = ttk.Button(mouse_click_frame, text="插入命令", command=lambda: insert_mouse_click_command(app), width=10)
    app.insert_mouse_click_btn.pack(side=tk.LEFT, padx=(10, 0))

    # 选择坐标点按钮
    select_coordinate_frame = ttk.Frame(mouse_cmd_frame)
    select_coordinate_frame.pack(fill=tk.X, pady=(4, 0))

    # 左键选择坐标
    app.select_coordinate_btn = ttk.Button(select_coordinate_frame, text="选择坐标点", command=lambda: select_coordinate(app))
    app.select_coordinate_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 组合按键命令组
    combo_key_frame = ttk.LabelFrame(left_frame, text="组合按键命令", padding="8")
    combo_key_frame.pack(fill=tk.X, pady=(0, 8))

    # 脚本控制按钮组
    control_cmd_frame = ttk.LabelFrame(left_frame, text="脚本控制", padding="8")
    control_cmd_frame.pack(fill=tk.X, pady=(0, 8))

    # 控制按钮行 - 只保留录制按钮
    control_buttons_row = ttk.Frame(control_cmd_frame)
    control_buttons_row.pack(fill=tk.X, pady=(0, 8))

    app.record_btn = ttk.Button(control_buttons_row, text="开始录制", command=app.script.start_recording)
    app.record_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    app.stop_record_btn = ttk.Button(control_buttons_row, text="停止录制", command=app.script.stop_recording)
    app.stop_record_btn.config(state="disabled")
    app.stop_record_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 脚本操作按钮行
    script_buttons_row = ttk.Frame(control_cmd_frame)
    script_buttons_row.pack(fill=tk.X)

    # 清空脚本按钮
    clear_script_btn = ttk.Button(script_buttons_row, text="清空脚本", command=lambda: clear_script(app))
    clear_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    # 导入脚本按钮
    import_script_btn = ttk.Button(script_buttons_row, text="导入脚本", command=lambda: load_script(app))
    import_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

    # 导出脚本按钮
    export_script_btn = ttk.Button(script_buttons_row, text="导出脚本", command=lambda: save_script(app))
    export_script_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 组合命令第一行 - 按键和修改按钮
    combo_row1 = ttk.Frame(combo_key_frame)
    combo_row1.pack(fill=tk.X, pady=(0, 4))

    # 按键
    ttk.Label(combo_row1, text="按键:", width=4).pack(side=tk.LEFT)
    app.combo_key_var = tk.StringVar(value="1")
    combo_key_label = ttk.Label(combo_row1, textvariable=app.combo_key_var, relief="sunken", padding=4, width=5)
    combo_key_label.pack(side=tk.LEFT, padx=(0, 2))

    # 设置组合命令按键按钮 - 缩短为"修改"并减小宽度
    app.set_combo_key_btn = ttk.Button(combo_row1, text="修改", width=4, 
                                       command=lambda: start_key_listening(app, app.combo_key_var, app.set_combo_key_btn))
    app.set_combo_key_btn.pack(side=tk.LEFT)

    # 组合命令第二行 - 按键延迟、抬起延迟和插入按钮，增加宽度和间距
    combo_row2 = ttk.Frame(combo_key_frame)
    combo_row2.pack(fill=tk.X, pady=(0, 4))

    # 按键延迟 - 增加宽度和间距，确保完整显示
    ttk.Label(combo_row2, text="按键延迟:", width=8).pack(side=tk.LEFT, padx=(0, 5))
    app.combo_key_delay = tk.StringVar(value="2500")
    combo_delay_entry = ttk.Entry(combo_row2, textvariable=app.combo_key_delay, width=8)
    combo_delay_entry.pack(side=tk.LEFT, padx=(0, 10))

    # 抬起后延迟 - 增加宽度和间距，确保完整显示
    ttk.Label(combo_row2, text="抬起延迟:", width=8).pack(side=tk.LEFT, padx=(0, 5))
    app.combo_after_delay = tk.StringVar(value="300")
    combo_after_delay_entry = ttk.Entry(combo_row2, textvariable=app.combo_after_delay, width=8)
    combo_after_delay_entry.pack(side=tk.LEFT, padx=(0, 10))

    # 插入组合命令按钮 - 放在同一行，固定宽度
    app.insert_combo_btn = ttk.Button(combo_row2, text="插入命令", command=lambda: insert_combo_command(app), width=10)
    app.insert_combo_btn.pack(side=tk.LEFT, padx=(10, 0))

    # 右侧：使用Notebook实现多tab页，固定宽度450px
    right_frame = ttk.Frame(left_right_frame, width=450)
    right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    right_frame.pack_propagate(False)  # 禁止子组件影响固定宽度

    # 创建Notebook
    app.script_notebook = ttk.Notebook(right_frame)
    app.script_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # 第一个tab页：脚本编辑
    script_tab = ttk.Frame(app.script_notebook)
    app.script_notebook.add(script_tab, text="脚本编辑")

    # 脚本文本框
    script_text_frame = ttk.Frame(script_tab)
    script_text_frame.pack(fill=tk.BOTH, expand=True)

    # 脚本内容文本框
    app.script_text = tk.Text(script_text_frame, wrap=tk.NONE, font=("Consolas", 10))
    app.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 垂直滚动条
    v_scrollbar = ttk.Scrollbar(script_text_frame, orient=tk.VERTICAL, command=app.script_text.yview)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app.script_text.config(yscrollcommand=v_scrollbar.set)

    # 水平滚动条
    h_scrollbar = ttk.Scrollbar(script_tab, orient=tk.HORIZONTAL, command=app.script_text.xview)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    app.script_text.config(xscrollcommand=h_scrollbar.set)

    # 第二个tab页：颜色识别
    color_tab = ttk.Frame(app.script_notebook)
    app.script_notebook.add(color_tab, text="颜色识别")
    create_color_recognition_tab(app, color_tab)

def create_color_recognition_tab(app, parent):
    """创建颜色识别标签页"""
    # 主容器
    main_frame = ttk.Frame(parent, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 颜色识别勾选框
    color_recognition_frame = ttk.Frame(main_frame, padding="8")
    color_recognition_frame.pack(fill=tk.X, pady=(0, 8))
    
    app.color_recognition_enabled = tk.BooleanVar(value=False)
    color_recognition_checkbox = ttk.Checkbutton(color_recognition_frame, text="颜色识别", variable=app.color_recognition_enabled)
    color_recognition_checkbox.pack(side=tk.LEFT)
    color_recognition_checkbox.bind("<Enter>", lambda e: show_tooltip(e, app, "勾选后，启动脚本运行时会自动激活颜色识别功能"))
    color_recognition_checkbox.bind("<Leave>", lambda e: hide_tooltip(app))
    
    # 区域选择
    region_frame = ttk.LabelFrame(main_frame, text="区域选择", padding="8")
    region_frame.pack(fill=tk.X, pady=(0, 8))
    
    region_btn = ttk.Button(region_frame, text="选择区域", command=app.color.select_region)
    region_btn.pack(side=tk.LEFT, padx=(0, 8))
    
    app.region_var = tk.StringVar(value="未选择区域")
    region_label = ttk.Label(region_frame, textvariable=app.region_var, width=30)
    region_label.pack(side=tk.LEFT)
    
    color_frame = ttk.LabelFrame(main_frame, text="颜色选择", padding="8")
    color_frame.pack(fill=tk.X, pady=(0, 8))
    
    color_btn = ttk.Button(color_frame, text="选择颜色", command=app.color.select_color)
    color_btn.pack(side=tk.LEFT, padx=(0, 8))
    
    app.color_var = tk.StringVar(value="未选择颜色")
    color_label = ttk.Label(color_frame, textvariable=app.color_var, width=20)
    color_label.pack(side=tk.LEFT, padx=(0, 8))
    
    # 颜色展示槽
    app.color_display = tk.Frame(color_frame, width=30, height=20, relief="sunken", borderwidth=1)
    app.color_display.pack(side=tk.LEFT, padx=(0, 15))
    app.color_display.config(background="gray")  # 默认灰色
    
    # 颜色容差
    ttk.Label(color_frame, text="容差:").pack(side=tk.LEFT)
    app.tolerance_var = tk.IntVar(value=10)
    tolerance_entry = ttk.Entry(color_frame, textvariable=app.tolerance_var, width=5)
    tolerance_entry.pack(side=tk.LEFT, padx=(0, 8))
    
    # 检查间隔
    interval_frame = ttk.LabelFrame(main_frame, text="检查设置", padding="8")
    interval_frame.pack(fill=tk.X, pady=(0, 8))
    
    ttk.Label(interval_frame, text="检查间隔(秒):").pack(side=tk.LEFT, padx=(0, 8))
    app.interval_var = tk.DoubleVar(value=5.0)
    interval_entry = ttk.Entry(interval_frame, textvariable=app.interval_var, width=6)
    interval_entry.pack(side=tk.LEFT, padx=(0, 8))
    
    # 命令输入区域
    commands_frame = ttk.LabelFrame(main_frame, text="颜色识别执行命令", padding="8")
    commands_frame.pack(fill=tk.BOTH, expand=True)
    
    app.color_commands_text = tk.Text(commands_frame, wrap=tk.NONE, font=("Consolas", 10), height=10)
    app.color_commands_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # 垂直滚动条
    v_scrollbar = ttk.Scrollbar(commands_frame, orient=tk.VERTICAL, command=app.color_commands_text.yview)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app.color_commands_text.config(yscrollcommand=v_scrollbar.set)
    
    # 水平滚动条
    h_scrollbar = ttk.Scrollbar(commands_frame, orient=tk.HORIZONTAL, command=app.color_commands_text.xview)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    app.color_commands_text.config(xscrollcommand=h_scrollbar.set)
    
    # 命令说明
    info_frame = ttk.Frame(main_frame, padding="8")
    info_frame.pack(fill=tk.X)
    
    info_label = ttk.Label(info_frame, text="额外命令: StartScript/StopScript；用于开始/停止脚本运行", 
                          font=("Arial", 9), foreground="gray")
    info_label.pack(anchor=tk.W)



def insert_key_command(app):
    """插入按键命令到当前选中的文本框"""
    key = app.key_var.get().strip()
    key_type = app.key_type.get()
    count = app.key_count.get()
    
    if not key:
        messagebox.showwarning("警告", "请输入按键名称！")
        return
    
    if count < 1:
        messagebox.showwarning("警告", "请输入有效的执行次数！")
        return
    
    # 格式化命令
    command = f"{key_type} \"{key}\", {count}\n"
    
    # 获取当前选中的标签页
    if hasattr(app, 'script_notebook'):
        current_tab = app.script_notebook.select()
        tab_text = app.script_notebook.tab(current_tab, "text")
        
        # 插入到对应的文本框
        if tab_text == "颜色识别" and hasattr(app, 'color_commands_text'):
            app.color_commands_text.insert(tk.INSERT, command)
            app.color_commands_text.see(tk.END)
        elif hasattr(app, 'script_text'):
            app.script_text.insert(tk.INSERT, command)
            app.script_text.see(tk.END)

def insert_delay_command(app):
    """插入延迟命令到当前选中的文本框"""
    delay = app.delay_entry.get().strip()
    
    if not delay.isdigit() or int(delay) < 0:
        messagebox.showwarning("警告", "请输入有效的延迟时间！")
        return
    
    # 格式化命令
    command = f"Delay {delay}\n"
    
    # 获取当前选中的标签页
    if hasattr(app, 'script_notebook'):
        current_tab = app.script_notebook.select()
        tab_text = app.script_notebook.tab(current_tab, "text")
        
        # 插入到对应的文本框
        if tab_text == "颜色识别" and hasattr(app, 'color_commands_text'):
            app.color_commands_text.insert(tk.INSERT, command)
            app.color_commands_text.see(tk.END)
        elif hasattr(app, 'script_text'):
            app.script_text.insert(tk.INSERT, command)
            app.script_text.see(tk.END)

def insert_mouse_click_command(app):
    """插入鼠标点击命令"""
    button = app.mouse_button_var.get()
    action = app.mouse_action_var.get()
    count = app.mouse_count_var.get()
    
    if count < 1:
        messagebox.showwarning("警告", "请输入有效的执行次数！")
        return
    
    # 格式化鼠标点击命令
    mouse_command = f"{button}{action} {count}\n"
    
    # 获取当前选中的标签页
    if hasattr(app, 'script_notebook'):
        current_tab = app.script_notebook.select()
        tab_text = app.script_notebook.tab(current_tab, "text")
        
        # 插入到对应的文本框
        if tab_text == "颜色识别" and hasattr(app, 'color_commands_text'):
            app.color_commands_text.insert(tk.INSERT, mouse_command)
            app.color_commands_text.see(tk.END)
        elif hasattr(app, 'script_text'):
            app.script_text.insert(tk.INSERT, mouse_command)
            app.script_text.see(tk.END)

def select_coordinate(app):
    """选择坐标点"""
    app.log_message("开始选择坐标点...")
    # 创建坐标点选择窗口
    create_coordinate_selection_window(app)

def create_coordinate_selection_window(app):
    """创建坐标点选择窗口"""
    # 检查screeninfo库是否可用
    try:
        import screeninfo
        monitors = screeninfo.get_monitors()
        
        # 计算整个虚拟屏幕的边界
        min_x = min(monitor.x for monitor in monitors)
        min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)
    except ImportError:
        messagebox.showerror("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
        return
    except Exception as e:
        # 如果获取显示器信息失败，使用默认值
        min_x, min_y, max_x, max_y = 0, 0, 1920, 1080
    
    # 创建覆盖整个虚拟屏幕的选择窗口
    app.coordinate_window = tk.Toplevel(app.root)
    # 移除窗口装饰，确保窗口能够覆盖整个屏幕，包括顶部区域
    app.coordinate_window.overrideredirect(True)
    app.coordinate_window.geometry(f"{max_x - min_x}x{max_y - min_y}+{min_x}+{min_y}")
    app.coordinate_window.attributes("-alpha", 0.3)
    app.coordinate_window.attributes("-topmost", True)
    app.coordinate_window.config(cursor="crosshair")
    
    # 创建画布
    app.coordinate_canvas = tk.Canvas(app.coordinate_window, bg="white", highlightthickness=0)
    app.coordinate_canvas.pack(fill=tk.BOTH, expand=True)
    
    # 绑定鼠标事件
    app.coordinate_canvas.bind("<Button-1>", lambda e: on_coordinate_select(app, e))
    
    # 绑定ESC键退出选择
    app.coordinate_window.bind("<Escape>", lambda e: app.coordinate_window.destroy())

def on_coordinate_select(app, event):
    """坐标点选择事件处理"""
    # 获取鼠标在屏幕上的绝对坐标
    abs_x = event.x_root
    abs_y = event.y_root
    
    # 关闭选择窗口
    app.coordinate_window.destroy()
    
    # 格式化坐标命令
    coordinate_command = f"MoveTo {abs_x}, {abs_y}\n"
    
    # 获取当前选中的标签页
    if hasattr(app, 'script_notebook'):
        current_tab = app.script_notebook.select()
        tab_text = app.script_notebook.tab(current_tab, "text")
        
        # 插入到对应的文本框
        if tab_text == "颜色识别" and hasattr(app, 'color_commands_text'):
            app.color_commands_text.insert(tk.INSERT, coordinate_command)
            app.color_commands_text.see(tk.END)
        elif hasattr(app, 'script_text'):
            app.script_text.insert(tk.INSERT, coordinate_command)
            app.script_text.see(tk.END)
    
    # 记录日志
    app.log_message(f"已选择坐标点: ({abs_x}, {abs_y})")

def insert_combo_command(app):
    """插入组合按键命令到当前选中的文本框"""
    key = app.combo_key_var.get().strip()
    key_delay = app.combo_key_delay.get().strip()
    after_delay = app.combo_after_delay.get().strip()
    
    if not key:
        messagebox.showwarning("警告", "请输入按键名称！")
        return
    
    if not key_delay.isdigit() or int(key_delay) < 0:
        messagebox.showwarning("警告", "请输入有效的按键延迟时间！")
        return
    
    if not after_delay.isdigit() or int(after_delay) < 0:
        messagebox.showwarning("警告", "请输入有效的抬起后延迟时间！")
        return
    
    # 格式化组合命令序列
    combo_command = f"Delay {key_delay}\nKeyDown \"{key}\", 1\nDelay {after_delay}\nKeyUp \"{key}\", 1\n"
    
    # 获取当前选中的标签页
    if hasattr(app, 'script_notebook'):
        current_tab = app.script_notebook.select()
        tab_text = app.script_notebook.tab(current_tab, "text")
        
        # 插入到对应的文本框
        if tab_text == "颜色识别" and hasattr(app, 'color_commands_text'):
            app.color_commands_text.insert(tk.INSERT, combo_command)
            app.color_commands_text.see(tk.END)
        elif hasattr(app, 'script_text'):
            app.script_text.insert(tk.INSERT, combo_command)
            app.script_text.see(tk.END)

def clear_script(app):
    """清空脚本文本框"""
    if messagebox.askyesno("确认", "确定要清空当前脚本吗？"):
        app.script_text.delete(1.0, tk.END)

def save_script(app):
    """保存脚本到文件"""
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        title="保存脚本"
    )
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(app.script_text.get(1.0, tk.END))
            messagebox.showinfo("成功", f"脚本已保存到: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存脚本失败: {str(e)}")

def load_script(app):
    """从文件加载脚本"""
    file_path = filedialog.askopenfilename(
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        title="加载脚本"
    )
    if file_path:
        try:
            # 尝试不同编码读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'ansi']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                messagebox.showerror("错误", "无法读取文件，编码不支持！")
                return
            
            app.script_text.delete(1.0, tk.END)
            app.script_text.insert(1.0, content)
            messagebox.showinfo("成功", f"脚本已从: {file_path} 加载")
        except Exception as e:
            messagebox.showerror("错误", f"加载脚本失败: {str(e)}")

def show_tooltip(event, app, text):
    """显示工具提示"""
    app.tooltip = tk.Toplevel(app.root)
    app.tooltip.wm_overrideredirect(True)
    app.tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root-10}")
    label = ttk.Label(app.tooltip, text=text, background="lightyellow", relief="solid", borderwidth=1, padding=(5, 2))
    label.pack()

def hide_tooltip(app):
    """隐藏工具提示"""
    if hasattr(app, 'tooltip'):
        app.tooltip.destroy()