from collections import defaultdict

class ThreadManager:
    """统一线程管理器"""
    def __init__(self, app):
        self.app = app
        self.threads = defaultdict(list)  # {module: [thread1, thread2...]}
    
    def start(self, module, start_func, stop_func, log_prefix):
        """启动模块线程"""
        # 停止现有线程
        self.stop(module, stop_func, log_prefix)
        
        self.app.logging_manager.log_message(f"开始{log_prefix}")
        
        # 启动新线程
        start_count = start_func()
        
        # 更新状态标签
        module_display_name = {
            "定时功能": "定时功能",
            "数字识别": "数字识别",
            "文字识别": "文字识别",
            "脚本运行": "脚本运行"
        }.get(log_prefix, log_prefix)
        
        if start_count > 0:
            self.app.status_labels[module].set(f"{module_display_name}: 运行中")
        else:
            self.app.status_labels[module].set(f"{module_display_name}: 未运行")
        
        if start_count == 0:
            self.app.logging_manager.log_message(f"没有启用任何{module_display_name}")
        
        return start_count
    
    def stop(self, module, stop_func, log_prefix):
        """停止模块线程"""
        stop_func()
        
        # 清空线程列表
        if module in self.threads:
            self.threads[module].clear()
        
        # 更新状态标签
        module_display_name = {
            "定时功能": "定时功能",
            "数字识别": "数字识别",
            "文字识别": "文字识别",
            "脚本运行": "脚本运行"
        }.get(log_prefix, log_prefix)
        
        if hasattr(self.app, 'status_labels') and module in self.app.status_labels:
            self.app.status_labels[module].set(f"{module_display_name}: 未运行")
    
    def add_thread(self, module, thread):
        """添加线程到管理器"""
        self.threads[module].append(thread)
    
    def get_threads(self, module):
        """获取模块的线程列表"""
        return self.threads.get(module, [])
    
    def stop_all(self):
        """停止所有线程"""
        for module in list(self.threads.keys()):
            if hasattr(self.app, f"stop_{module}_tasks"):
                stop_func = getattr(self.app, f"stop_{module}_tasks")
                self.stop(module, stop_func, module)
            elif hasattr(self.app, f"stop_{module}_recognition"):
                stop_func = getattr(self.app, f"stop_{module}_recognition")
                self.stop(module, stop_func, module)
