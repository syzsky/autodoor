import tkinter as tk
from tkinter import ttk


def configure_styles():
    """
    配置全局UI样式
    
    Returns:
        ttk.Style: 配置好的样式对象
    """
    style = ttk.Style()
    bg_color = "#f0f0f0"
    green_bg_color = "#e8f4e8"

    style.configure("TFrame", background=bg_color)
    style.configure("TLabel", background=bg_color, font=("Arial", 10))
    style.configure("Header.TLabel", font=("Arial", 12, "bold"), background=bg_color)
    style.configure("TButton", padding=5, background=bg_color)
    style.configure("TEntry", background=bg_color, fieldbackground=bg_color)
    style.configure("TCheckbutton", background=bg_color)
    style.configure("TCombobox", background=bg_color, fieldbackground=bg_color)
    style.configure("TLabelFrame", background=bg_color, bordercolor=bg_color)
    style.configure("TLabelFrame.Label", background=bg_color)

    style.configure(".", background=bg_color)
    style.configure("TLabel", relief="flat")
    style.map("TLabel", background=[("active", bg_color)])
    style.map("TLabelFrame.Label", background=[("active", bg_color)])
    style.map("TFrame", background=[("active", bg_color)])

    style.configure("Green.TFrame", background=green_bg_color)
    style.configure("Green.TLabelframe", 
                  background=green_bg_color, 
                  borderwidth=2, 
                  relief=tk.SOLID, 
                  bordercolor="green")
    style.configure("Green.TLabelframe.Label", 
                  foreground="green", 
                  font=("Arial", 10, "bold"), 
                  background=green_bg_color)
    style.map("Green.TLabelframe", 
             background=[("active", green_bg_color)],
             bordercolor=[("active", "green")])
    style.map("Green.TLabelframe.Label", 
             foreground=[("active", "green")],
             background=[("active", green_bg_color)])
    style.configure("Green.TLabel", background=green_bg_color)
    style.configure("Green.TEntry", background=green_bg_color, fieldbackground=bg_color)
    style.configure("Green.TButton", background=green_bg_color)
    style.configure("Green.TCheckbutton", background=green_bg_color)
    style.configure("Green.TCombobox", background=green_bg_color, fieldbackground=bg_color)

    return style


BG_COLOR = "#f0f0f0"
GREEN_BG_COLOR = "#e8f4e8"
