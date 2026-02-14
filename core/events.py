import queue
import time
import threading


class EventManager:
    """
    事件管理器类，负责事件队列的管理和处理
    """
    def __init__(self, app):
        """
        初始化事件管理器
        Args:
            app: 应用实例
        """
        self.app = app
        self.is_event_running = False
        self.event_thread = None
        self.event_queue = queue.PriorityQueue()
        
    def start_event_thread(self):
        """启动事件处理线程"""
        self.is_event_running = True
        self.event_thread = threading.Thread(target=self.process_events, daemon=True)
        self.event_thread.start()
        if hasattr(self.app, 'logging_manager'):
            self.app.logging_manager.log_message("事件处理线程已启动")
        else:
            print("事件处理线程已启动")

    def process_events(self):
        """
        处理事件队列中的事件
        """
        while self.is_event_running:
            try:
                # 从优先级队列中取出事件
                event_data = self.event_queue.get(block=True, timeout=1)
                
                # 执行事件
                self.execute_event(event_data)
                # 标记事件完成
                self.event_queue.task_done()
                # 等待0.1秒后再执行下一个事件
                time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                if hasattr(self.app, 'logging_manager'):
                    self.app.logging_manager.log_message(f"事件处理错误: {str(e)}")
                else:
                    print(f"事件处理错误: {str(e)}")
                time.sleep(1)

    def add_event(self, event, module_info=None, priority=None):
        """
        添加事件到队列，支持优先级
        Args:
            event: 事件元组
            module_info: 模块信息，可选
            priority: 优先级，可选
        """
        # 根据module_info自动确定优先级
        if priority is None and module_info:
            module_type = module_info[0]
            priority = self.app.PRIORITIES.get(module_type, 0)
        elif priority is None:
            priority = 0
        
        # 注意：内置的PriorityQueue是按优先级从小到大排序的，所以需要取反
        # 这样优先级高的事件会先被处理
        priority = -priority
        
        # 添加事件到优先级队列
        self.event_queue.put((priority, event, module_info))

    def clear_events(self):
        """
        清空事件队列
        """
        # 由于内置的PriorityQueue没有clear方法，我们需要逐个取出所有事件
        try:
            while True:
                self.event_queue.get(block=False)
                self.event_queue.task_done()
        except queue.Empty:
            pass

    def execute_event(self, event_data):
        """执行具体事件"""
        if len(event_data) == 3:
            priority, event, module_info = event_data
        else:
            event, module_info = event_data
        event_type, data = event

        if event_type == 'keypress':
            key = data
            try:
                if module_info:
                    module_type, module_index = module_info
                    if module_type == 'ocr':
                        delay_min_var = self.app.ocr_groups[module_index]['delay_min']
                        delay_max_var = self.app.ocr_groups[module_index]['delay_max']
                    elif module_type == 'timed':
                        delay_min_var = self.app.timed_groups[module_index]['delay_min']
                        delay_max_var = self.app.timed_groups[module_index]['delay_max']
                    elif module_type == 'number':
                        delay_min_var = self.app.number_regions[module_index]['delay_min']
                        delay_max_var = self.app.number_regions[module_index]['delay_max']
                    else:
                        class DefaultVar:
                            def get(self):
                                return "300"
                        delay_min_var = DefaultVar()
                        delay_max_var = DefaultVar()
                else:
                    class DefaultVar:
                        def get(self):
                            return "300"
                    delay_min_var = DefaultVar()
                    delay_max_var = DefaultVar()

                from modules.input import KeyEventExecutor
                executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var)
                executor.execute_keypress(key)

                delay_min = max(1, int(delay_min_var.get()))
                delay_max = max(delay_min, int(delay_max_var.get()))
                self.app.logging_manager.log_message(f"按下了 {key} 键，延迟范围 {delay_min}-{delay_max} 毫秒")
            except Exception as e:
                self.app.logging_manager.log_message(f"按键执行错误: {str(e)}")
        elif event_type == 'exit':
            pass
