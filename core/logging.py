import datetime
import tkinter as tk


class LoggingManager:
    """
    日志管理类，负责记录和显示日志信息
    """
    
    def __init__(self, app):
        """
        初始化日志管理器
        Args:
            app: 应用程序实例
        """
        self.app = app
    
    def log_message(self, message):
        """
        记录日志信息
        Args:
            message: 要记录的日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # 写入日志文件
        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")

        # 写入首页的日志文本框
        if hasattr(self.app, 'home_log_text'):
            self.app.home_log_text.config(state=tk.NORMAL)
            self.app.home_log_text.insert(tk.END, log_entry)
            self.app.home_log_text.see(tk.END)
            self.app.home_log_text.config(state=tk.DISABLED)

        # 更新状态标签（仅当status_var已创建）
        if hasattr(self.app, 'status_var'):
            self.app.status_var.set(message.split(":")[0] if ":" in message else message)

    def clear_log(self):
        """清除日志"""
        if hasattr(self.app, 'home_log_text'):
            self.app.home_log_text.config(state=tk.NORMAL)
            self.app.home_log_text.delete("1.0", tk.END)
            self.app.home_log_text.config(state=tk.DISABLED)

        self.log_message("已清除日志")
