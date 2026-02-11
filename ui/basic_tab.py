import tkinter as tk
from tkinter import ttk


def create_basic_tab(parent, app):
    """创建基本设置标签页"""
    # 基本设置区域
    basic_frame = ttk.Frame(parent, padding="10")
    basic_frame.pack(fill=tk.BOTH, expand=True)

    # Tesseract配置
    tesseract_frame = ttk.LabelFrame(basic_frame, text="Tesseract配置", padding="10")
    tesseract_frame.pack(fill=tk.X, pady=(0, 10))

    # Tesseract路径
    path_label = ttk.Label(tesseract_frame, text="Tesseract路径:")
    path_label.pack(anchor=tk.W, pady=(0, 5))

    path_frame = ttk.Frame(tesseract_frame)
    path_frame.pack(fill=tk.X, pady=(0, 10))

    app.tesseract_path_var = tk.StringVar(value=app.tesseract_path)
    app.tesseract_path_entry = ttk.Entry(path_frame, textvariable=app.tesseract_path_var)
    app.tesseract_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    app.set_path_btn = ttk.Button(path_frame, text="设置", command=app.set_tesseract_path)
    app.set_path_btn.pack(side=tk.RIGHT)

    # 报警声音设置
    alarm_sound_frame = ttk.LabelFrame(basic_frame, text="报警声音设置", padding="10")
    alarm_sound_frame.pack(fill=tk.X, pady=(10, 10))

    # 报警声音文件选择
    sound_file_frame = ttk.Frame(alarm_sound_frame)
    sound_file_frame.pack(fill=tk.X, pady=(0, 10))

    alarm_sound_label = ttk.Label(sound_file_frame, text="报警声音:", width=12, anchor=tk.W)
    alarm_sound_label.pack(side=tk.LEFT, padx=(0, 10))

    alarm_sound_entry = ttk.Entry(sound_file_frame, textvariable=app.alarm_sound_path, state="readonly", width=30)
    alarm_sound_entry.pack(side=tk.LEFT, padx=(0, 10))

    alarm_sound_btn = ttk.Button(sound_file_frame, text="选择", width=8,
                               command=app.select_alarm_sound)
    alarm_sound_btn.pack(side=tk.LEFT)

    # 报警音量调节
    volume_frame = ttk.Frame(alarm_sound_frame)
    volume_frame.pack(fill=tk.X)
    volume_label = ttk.Label(volume_frame, text="音量调节:", width=12, anchor=tk.W)
    volume_label.pack(side=tk.LEFT, padx=(0, 10))

    # 音量变化跟踪函数，确保显示为整数
    def update_volume_display(*args):
        app.alarm_volume_str.set(str(app.alarm_volume.get()))

    # 绑定音量变化事件
    app.alarm_volume.trace_add("write", update_volume_display)

    volume_scale = ttk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=app.alarm_volume, length=200)
    volume_scale.pack(side=tk.LEFT, padx=(0, 10))

    volume_value_label = ttk.Label(volume_frame, textvariable=app.alarm_volume_str, width=3)
    volume_value_label.pack(side=tk.LEFT)

    volume_percent_label = ttk.Label(volume_frame, text="%")
    volume_percent_label.pack(side=tk.LEFT)

    # 快捷键设置 - 从首页迁移
    shortcut_frame = ttk.LabelFrame(basic_frame, text="快捷键设置", padding="10")
    shortcut_frame.pack(fill=tk.X, pady=(10, 10))

    # 单行布局
    shortcut_row = ttk.Frame(shortcut_frame)
    shortcut_row.pack(fill=tk.X, pady=5)

    # 开始快捷键
    ttk.Label(shortcut_row, text="开始运行:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
    app.start_shortcut_var = tk.StringVar(value="F10")
    start_shortcut_label = ttk.Label(shortcut_row, textvariable=app.start_shortcut_var, relief="sunken", padding=5, width=6)
    start_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
    app.set_start_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
    app.set_start_shortcut_btn.pack(side=tk.LEFT, padx=(0, 20))
    from utils.keyboard import start_key_listening
    app.set_start_shortcut_btn.config(command=lambda: start_key_listening(app, app.start_shortcut_var, app.set_start_shortcut_btn))

    # 结束快捷键
    ttk.Label(shortcut_row, text="结束运行:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
    app.stop_shortcut_var = tk.StringVar(value="F12")
    stop_shortcut_label = ttk.Label(shortcut_row, textvariable=app.stop_shortcut_var, relief="sunken", padding=5, width=6)
    stop_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
    app.set_stop_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
    app.set_stop_shortcut_btn.pack(side=tk.LEFT, padx=(0, 20))
    app.set_stop_shortcut_btn.config(command=lambda: start_key_listening(app, app.stop_shortcut_var, app.set_stop_shortcut_btn))

    # 录制快捷键
    ttk.Label(shortcut_row, text="录制按钮:", width=10, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 10))
    app.record_hotkey_var = tk.StringVar(value="F11")
    record_shortcut_label = ttk.Label(shortcut_row, textvariable=app.record_hotkey_var, relief="sunken", padding=5, width=6)
    record_shortcut_label.pack(side=tk.LEFT, padx=(0, 5))
    app.set_record_shortcut_btn = ttk.Button(shortcut_row, text="修改", width=8)
    app.set_record_shortcut_btn.pack(side=tk.LEFT)
    app.set_record_shortcut_btn.config(command=lambda: start_key_listening(app, app.record_hotkey_var, app.set_record_shortcut_btn))

    # 配置管理
    config_frame = ttk.Frame(basic_frame)
    config_frame.pack(fill=tk.X, pady=(0, 10))

    save_btn = ttk.Button(config_frame, text="保存配置", command=app.save_config)
    save_btn.pack(side=tk.LEFT, padx=(0, 10))

    reset_btn = ttk.Button(config_frame, text="重置配置", command=app.load_config)
    reset_btn.pack(side=tk.LEFT)
