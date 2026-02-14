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

        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")

        if hasattr(self.app, 'home_log_text'):
            try:
                self.app.home_log_text.configure(state='normal')
                self.app.home_log_text.insert(tk.END, log_entry)
                self.app.home_log_text.see(tk.END)
                self.app.home_log_text.configure(state='disabled')
            except Exception as e:
                print(f"写入日志文本框失败: {str(e)}")

        if hasattr(self.app, 'status_var'):
            self.app.status_var.set(message.split(":")[0] if ":" in message else message)

    def clear_log(self):
        """清除日志"""
        if hasattr(self.app, 'home_log_text'):
            try:
                self.app.home_log_text.configure(state='normal')
                self.app.home_log_text.delete("1.0", tk.END)
                self.app.home_log_text.configure(state='disabled')
            except Exception as e:
                print(f"清除日志失败: {str(e)}")

        self.log_message("已清除日志")
