import threading
import time
import tkinter as tk

# 尝试导入screeninfo库，如果不可用则提供安装提示
try:
    import screeninfo
except ImportError:
    screeninfo = None

class TimedModule:
    """定时任务模块"""
    def __init__(self, app):
        """
        初始化定时任务模块
        Args:
            app: 主应用实例
        """
        self.app = app
    
    def start_timed_tasks(self):
        """开始定时任务"""
        def start_func():
            start_count = 0
            for i, group in enumerate(self.app.timed_groups):
                if group["enabled"].get():
                    interval = group["interval"].get()
                    key = group["key"].get()
                    # 创建线程并存储
                    thread = threading.Thread(target=self.timed_task_loop, args=(i, interval, key), daemon=True)
                    self.app.timed_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.app.start_module("timed", start_func)

    def stop_timed_tasks(self):
        """停止定时任务"""
        # 清空线程列表
        if self.app.timed_threads:
            self.app.timed_threads.clear()
        # 更新状态标签
        if "timed" in self.app.status_labels:
            self.app.status_labels["timed"].set("定时功能: 未运行")

    def timed_task_loop(self, group_index, interval, key):
        """定时任务循环"""
        current_thread = threading.current_thread()

        # 检查线程是否在timed_threads列表中，以及定时组是否启用
        while current_thread in self.app.timed_threads and self.app.timed_groups[group_index]["enabled"].get():
            try:
                # 等待指定的时间间隔
                for _ in range(interval):
                    time.sleep(1)
                    # 每秒钟检查一次线程是否仍在列表中
                    if current_thread not in self.app.timed_threads:
                        return

                # 检查线程是否仍在列表中
                if current_thread not in self.app.timed_threads:
                    return

                # 获取定时组配置
                group = self.app.timed_groups[group_index]

                # 检查线程是否仍在列表中
                if current_thread not in self.app.timed_threads:
                    return

                # 播放定时模块报警声音
                self.app.alarm_module.play_alarm_sound(group["alarm"])

                # 检查线程是否仍在列表中
                if current_thread not in self.app.timed_threads:
                    return

                # 检查是否启用了鼠标点击
                if group["click_enabled"].get():
                    # 检查线程是否仍在列表中
                    if current_thread not in self.app.timed_threads:
                        return

                    # 获取保存的位置坐标
                    pos_x = group["position_x"].get()
                    pos_y = group["position_y"].get()

                    if pos_x != 0 or pos_y != 0:  # 确保位置已选择
                        # 检查线程是否仍在列表中
                        if current_thread not in self.app.timed_threads:
                            return

                        # 执行鼠标点击操作
                        try:
                            # 使用输入控制器执行鼠标点击操作
                            self.app.input_controller.click(pos_x, pos_y)

                            # 等待0.5秒后触发按键
                            time.sleep(0.5)

                            # 检查线程是否仍在列表中
                            if current_thread not in self.app.timed_threads:
                                return
                        except Exception as e:
                            self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}错误: 鼠标点击失败 - {str(e)}")

                        # 等待0.5秒后触发按键
                        time.sleep(0.5)

                        # 检查线程是否仍在列表中
                        if current_thread not in self.app.timed_threads:
                            return

                # 只有当按键不为空时才执行按键操作
                if key:
                    # 检查线程是否仍在列表中
                    if current_thread not in self.app.timed_threads:
                        return

                    self.app.event_manager.add_event(('keypress', key), ('timed', group_index))
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}触发按键: {key}")
                else:
                    self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}按键配置为空")
            except Exception as e:
                self.app.logging_manager.log_message(f"[{self.app.platform_adapter.platform}] 定时任务{group_index+1}错误: {str(e)}")
                break

    def start_timed_position_selection(self, group_index):
        """开始定时任务屏幕位置选择"""
        self.app.logging_manager.log_message(f"开始定时组{group_index+1}屏幕位置选择...")
        self.app.is_selecting = True
        self.app.current_timed_group = group_index

        # 检查screeninfo库是否可用
        if screeninfo is None:
            self.app.show_message("错误", "screeninfo库未安装，无法支持多显示器选择。请运行 'pip install screeninfo' 安装该库。")
            return

        # 获取虚拟屏幕的尺寸（包含所有显示器）
        monitors = screeninfo.get_monitors()

        # 计算整个虚拟屏幕的边界
        self.app.min_x = min(monitor.x for monitor in monitors)
        self.app.min_y = min(monitor.y for monitor in monitors)
        max_x = max(monitor.x + monitor.width for monitor in monitors)
        max_y = max(monitor.y + monitor.height for monitor in monitors)

        # 创建透明的位置选择窗口，覆盖整个虚拟屏幕
        self.app.select_window = tk.Toplevel(self.app.root)
        self.app.select_window.geometry(f"{max_x - self.app.min_x}x{max_y - self.app.min_y}+{self.app.min_x}+{self.app.min_y}")
        self.app.select_window.overrideredirect(True)  # 移除窗口装饰
        self.app.select_window.attributes("-alpha", 0.3)
        self.app.select_window.attributes("-topmost", True)

        # 创建画布用于显示提示
        self.app.canvas = tk.Canvas(self.app.select_window, cursor="cross", 
                               width=max_x - self.app.min_x, height=max_y - self.app.min_y)
        self.app.canvas.pack(fill=tk.BOTH, expand=True)

        # 显示提示文字
        self.app.canvas.create_text((max_x - self.app.min_x) // 2, (max_y - self.app.min_y) // 2, 
                              text="请点击要记录的屏幕位置", font=("Arial", 16), fill="red")

        # 绑定鼠标事件
        self.app.canvas.bind("<Button-1>", self.on_timed_position_click)
        self.app.select_window.protocol("WM_DELETE_WINDOW", self.app.cancel_selection)

    def on_timed_position_click(self, event):
        """定时任务位置选择鼠标点击事件"""
        # 获取绝对坐标
        pos_x = event.x_root
        pos_y = event.y_root

        self.app.logging_manager.log_message(f"定时组{self.app.current_timed_group+1}已选择位置: {pos_x},{pos_y}")

        # 更新配置
        if 0 <= self.app.current_timed_group < len(self.app.timed_groups):
            group = self.app.timed_groups[self.app.current_timed_group]
            group["position_x"].set(pos_x)
            group["position_y"].set(pos_y)
            group["position_var"].set(f"位置：{pos_x},{pos_y}")

            # 保存配置
            self.app.save_config()

        self.app.cancel_selection()
