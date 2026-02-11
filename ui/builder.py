import tkinter as tk
from tkinter import ttk

from utils.keyboard import start_key_listening
from ui.validators import Validators

# 声明式UI配置
UI_CONFIG = {
    "ocr": {
        "title": "识别组",
        "fields": [
            {"type": "button", "label": "选择区域", "command": "select_region"},
            {"type": "label", "var": "region_var", "width": 25},
            {"type": "entry", "label": "间隔(秒):", "var": "interval_var", "width": 6},
            {"type": "entry", "label": "暂停时长(秒):", "var": "pause_var", "width": 6},
            {"type": "keybind", "label": "按键:", "var": "key_var"},
            {"type": "range", "label": "按键时长:", "min_var": "delay_min_var", "max_var": "delay_max_var", "unit": "ms"},
            {"type": "checkbox", "label": "启用报警", "var": "alarm_var"},
            {"type": "entry", "label": "识别关键词:", "var": "keywords_var", "width": 20},
            {"type": "combobox", "label": "识别语言:", "var": "language_var", "values": ["eng", "chi_sim", "chi_tra"], "width": 12},
            {"type": "checkbox", "label": "点击识别文字", "var": "click_var"}
        ]
    },
    "timed": {
        "title": "定时组",
        "fields": [
            {"type": "entry", "label": "间隔(秒):", "var": "interval_var", "width": 6},
            {"type": "keybind", "label": "按键:", "var": "key_var"},
            {"type": "range", "label": "按键时长：", "min_var": "delay_min_var", "max_var": "delay_max_var", "unit": "ms"},
            {"type": "checkbox", "label": "启用报警", "var": "alarm_var"},
            {"type": "checkbox", "label": "启用鼠标点击", "var": "click_enabled_var"},
            {"type": "button", "label": "选择位置", "command": "select_position", "width": 8},
            {"type": "label", "var": "position_var", "width": 15}
        ]
    },
    "number": {
        "title": "识别组",
        "fields": [
            {"type": "button", "label": "选择区域", "command": "select_region"},
            {"type": "label", "var": "region_var", "width": 25},
            {"type": "entry", "label": "阈值:", "var": "threshold_var", "width": 10},
            {"type": "keybind", "label": "按键:", "var": "key_var"},
            {"type": "range", "label": "按键时长:", "min_var": "delay_min_var", "max_var": "delay_max_var", "unit": "ms"},
            {"type": "checkbox", "label": "启用报警", "var": "alarm_var"}
        ]
    }
}

class UIBuilder:
    """统一UI构建器类"""
    
    @staticmethod
    def create_group_frame(parent, index, title):
        """创建组框架
        Args:
            parent: 父容器
            index: 组索引
            title: 组标题
        Returns:
            组框架
        """
        frame = ttk.LabelFrame(parent, text=f"{title} {index + 1}", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))
        return frame
    
    @staticmethod
    def add_checkbox(frame, label, var):
        """添加复选框
        Args:
            frame: 父容器
            label: 标签文本
            var: 变量
        Returns:
            复选框
        """
        checkbox = ttk.Checkbutton(frame, text=label, variable=var)
        checkbox.pack(side=tk.LEFT, padx=(0, 10))
        return checkbox
    
    @staticmethod
    def add_button(frame, label, command, side=tk.LEFT, width=None):
        """添加按钮
        Args:
            frame: 父容器
            label: 按钮文本
            command: 命令
            side: 位置
            width: 宽度
        Returns:
            按钮
        """
        button = ttk.Button(frame, text=label, command=command, width=width)
        button.pack(side=side, padx=(0, 10))
        return button
    
    @staticmethod
    def add_label(frame, text, var, width=None, side=tk.LEFT):
        """添加标签
        Args:
            frame: 父容器
            text: 标签文本
            var: 变量
            width: 宽度
            side: 位置
        Returns:
            标签
        """
        if text:
            ttk.Label(frame, text=text).pack(side=side, padx=(0, 5))
        label = ttk.Label(frame, textvariable=var, width=width)
        label.pack(side=side, padx=(0, 10))
        return label
    
    @staticmethod
    def add_entry(frame, var, width=None, side=tk.LEFT):
        """添加输入框
        Args:
            frame: 父容器
            var: 变量
            width: 宽度
            side: 位置
        Returns:
            输入框
        """
        entry = ttk.Entry(frame, textvariable=var, width=width)
        entry.pack(side=side, padx=(0, 10))
        return entry
    
    @staticmethod
    def add_range(frame, label, min_var, max_var, unit=None, side=tk.LEFT):
        """添加范围输入
        Args:
            frame: 父容器
            label: 标签文本
            min_var: 最小值变量
            max_var: 最大值变量
            unit: 单位
            side: 位置
        Returns:
            (最小值输入框, 最大值输入框)
        """
        if label:
            ttk.Label(frame, text=label).pack(side=side, padx=(0, 5))
        min_entry = UIBuilder.add_entry(frame, min_var, width=6, side=side)
        ttk.Label(frame, text=" - ", width=2).pack(side=side)
        max_entry = UIBuilder.add_entry(frame, max_var, width=6, side=side)
        if unit:
            ttk.Label(frame, text=unit, width=3).pack(side=side, padx=(0, 10))
        return min_entry, max_entry
    
    @staticmethod
    def add_keybind(frame, label, key_var, app, side=tk.LEFT):
        """添加按键绑定
        Args:
            frame: 父容器
            label: 标签文本
            key_var: 按键变量
            app: AutoDoorOCR实例
            side: 位置
        Returns:
            (按键标签, 设置按钮)
        """
        if label:
            ttk.Label(frame, text=label).pack(side=side, padx=(0, 5))
        key_label = ttk.Label(frame, textvariable=key_var, relief="sunken", padding=2, width=8)
        key_label.pack(side=side, padx=(0, 5))
        set_key_btn = ttk.Button(frame, text="修改", width=6)
        set_key_btn.pack(side=side, padx=(0, 10))
        set_key_btn.config(command=lambda v=key_var, b=set_key_btn: start_key_listening(app, v, b))
        return key_label, set_key_btn
    
    @staticmethod
    def add_combobox(frame, label, var, values=None, width=None, side=tk.LEFT):
        """添加下拉框
        Args:
            frame: 父容器
            label: 标签文本
            var: 变量
            values: 选项值列表
            width: 宽度
            side: 位置
        Returns:
            下拉框
        """
        if label:
            ttk.Label(frame, text=label, width=10).pack(side=side, padx=(0, 5))
        combobox = ttk.Combobox(frame, textvariable=var, values=values or [], width=width)
        combobox.pack(side=side, padx=(0, 10))
        return combobox
    
    @staticmethod
    def _add_field(frame, field, group_vars, app, command_map):
        """添加单个字段到指定框架
        Args:
            frame: 父容器
            field: 字段配置
            group_vars: 变量字典
            app: 应用实例
            command_map: 命令映射
        """
        field_type = field["type"]
        
        if field_type == "button":
            command = command_map.get(field["command"])
            UIBuilder.add_button(frame, field["label"], command, width=field.get("width"))
        elif field_type == "label":
            var = group_vars.get(field["var"])
            UIBuilder.add_label(frame, "", var, field.get("width"))
        elif field_type == "entry":
            var = group_vars.get(field["var"])
            if field.get("label"):
                ttk.Label(frame, text=field["label"], width=12).pack(side=tk.LEFT, padx=(0, 5))
            UIBuilder.add_entry(frame, var, field.get("width"))
        elif field_type == "keybind":
            var = group_vars.get(field["var"])
            UIBuilder.add_keybind(frame, field.get("label"), var, app)
        elif field_type == "range":
            if field.get("label"):
                ttk.Label(frame, text=field["label"], width=10).pack(side=tk.LEFT, padx=(0, 5))
            min_var = group_vars.get(field["min_var"])
            max_var = group_vars.get(field["max_var"])
            min_entry = UIBuilder.add_entry(frame, min_var, width=5)
            Validators.register_entry(min_entry, min_var)
            ttk.Label(frame, text=" - ", width=2).pack(side=tk.LEFT)
            max_entry = UIBuilder.add_entry(frame, max_var, width=5)
            Validators.register_entry(max_entry, max_var)
            if field.get("unit"):
                ttk.Label(frame, text=field.get("unit"), width=3).pack(side=tk.LEFT, padx=(0, 10))
        elif field_type == "checkbox":
            var = group_vars.get(field["var"])
            UIBuilder.add_checkbox(frame, field["label"], var)
        elif field_type == "combobox":
            var = group_vars.get(field["var"])
            UIBuilder.add_combobox(frame, field.get("label"), var, field.get("values"), field.get("width"))
    
    @staticmethod
    def build_module(parent, config_name, index, app, command_map, group_vars):
        """根据配置构建模块UI
        Args:
            parent: 父容器
            config_name: 配置名称
            index: 组索引
            app: 应用实例
            command_map: 命令映射
            group_vars: 变量字典
        Returns:
            组框架
        """
        config = UI_CONFIG[config_name]
        frame = UIBuilder.create_group_frame(parent, index, config["title"])
        
        # 创建行框架
        row_frames = {
            0: ttk.Frame(frame),  # 第一行
            1: ttk.Frame(frame),  # 第二行
            2: ttk.Frame(frame)   # 第三行
        }
        
        # 打包行框架
        for i in range(3):
            row_frames[i].pack(fill=tk.X, pady=(0, 10))
        
        # 字段布局映射
        field_layouts = {
            "ocr": [(0, 2), (1, 7), (2, None)],  # (行索引, 结束索引)
            "timed": [(0, 4), (1, None), (2, None)],
            "number": [(0, 2), (1, None), (2, None)]
        }
        
        layout = field_layouts.get(config_name, [(0, None), (1, None), (2, None)])
        
        # 根据布局添加字段
        for i, field in enumerate(config["fields"]):
            # 确定字段应该放在哪一行
            target_row = 0
            for row_idx, (row, end_idx) in enumerate(layout):
                if end_idx is None or i < end_idx:
                    target_row = row
                    break
            
            # 添加字段到目标行
            UIBuilder._add_field(row_frames[target_row], field, group_vars, app, command_map)
        
        return frame
