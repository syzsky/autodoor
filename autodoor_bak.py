import os
import time
import logging
import threading
import json
import keyboard
from PIL import Image, ImageGrab
import pytesseract
import pyautogui
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import Canvas

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autodoor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = 'config.json'

# 默认配置
DEFAULT_CONFIG = {
    'monitor_area': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080},
    'trigger_key': 'enter',
    'ocr_interval': 1.0,
    'action_interval': 180.0,  # 执行间隔，默认180秒
    'sensitivity': 0.8,
    'start_hotkey': 'ctrl+shift+s',
    'stop_hotkey': 'ctrl+shift+q',
    'tesseract_path': r'E:\tesseract\tesseract.exe'
}

class AutoDoorApp:
    def __init__(self):
        self.config = self.load_config()
        self.is_running = False
        self.monitor_thread = None
        self.last_screenshot = None
        self.last_ocr_result = None
        self.last_action_time = 0  # 上次执行操作的时间
        self.last_operation_time = 0  # 上次操作（点击或按键）的时间，用于实现0.5秒间隔
        self.action_lock = threading.Lock()  # 操作锁，确保同一时间只有一个操作执行
        
        # 设置Tesseract路径
        pytesseract.pytesseract.tesseract_cmd = self.config['tesseract_path']
        
        # 创建GUI
        self.root = tk.Tk()
        self.root.title('AutoDoor - 自动门控制脚本')
        self.root.geometry('500x800')  # 增加窗口高度以显示所有控件
        self.root.resizable(False, False)
        
        # 检查Tesseract是否可用
        self.check_tesseract()
        
        # 设置GUI
        self.setup_gui()
        
        # 设置热键
        self.setup_hotkeys()
        
    def check_tesseract(self):
        """检查Tesseract是否可用"""
        if not os.path.exists(self.config['tesseract_path']):
            messagebox.showwarning(
                '警告',
                f'Tesseract OCR未找到，请安装并在配置中设置正确路径。\n默认路径: {DEFAULT_CONFIG["tesseract_path"]}'
            )
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                logger.error(f'加载配置文件失败: {e}')
                messagebox.showerror('错误', f'加载配置文件失败: {e}')
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info('配置已保存')
            messagebox.showinfo('成功', '配置已保存')
        except Exception as e:
            logger.error(f'保存配置文件失败: {e}')
            messagebox.showerror('错误', f'保存配置文件失败: {e}')
    
    def setup_gui(self):
        """设置GUI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding='20')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text='AutoDoor 配置', font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # 监控区域配置
        area_frame = ttk.LabelFrame(main_frame, text='监控区域', padding='10')
        area_frame.pack(fill=tk.X, pady=10)
        
        # 监控区域输入框
        ttk.Label(area_frame, text='X坐标:').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.x_entry = ttk.Entry(area_frame, width=10)
        self.x_entry.grid(row=0, column=1, padx=5, pady=5)
        self.x_entry.insert(0, str(self.config['monitor_area']['x']))
        
        ttk.Label(area_frame, text='Y坐标:').grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.y_entry = ttk.Entry(area_frame, width=10)
        self.y_entry.grid(row=0, column=3, padx=5, pady=5)
        self.y_entry.insert(0, str(self.config['monitor_area']['y']))
        
        ttk.Label(area_frame, text='宽度:').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.width_entry = ttk.Entry(area_frame, width=10)
        self.width_entry.grid(row=1, column=1, padx=5, pady=5)
        self.width_entry.insert(0, str(self.config['monitor_area']['width']))
        
        ttk.Label(area_frame, text='高度:').grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.height_entry = ttk.Entry(area_frame, width=10)
        self.height_entry.grid(row=1, column=3, padx=5, pady=5)
        self.height_entry.insert(0, str(self.config['monitor_area']['height']))
        
        # 区域选择按钮
        self.select_area_button = ttk.Button(area_frame, text='选择区域', command=self.select_monitor_area, width=15)
        self.select_area_button.grid(row=2, column=0, padx=5, pady=10, columnspan=4)
        
        # 功能配置
        func_frame = ttk.LabelFrame(main_frame, text='功能配置', padding='10')
        func_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(func_frame, text='触发按键:').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.trigger_key_entry = ttk.Entry(func_frame, width=20)
        self.trigger_key_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=3)
        self.trigger_key_entry.insert(0, self.config['trigger_key'])
        
        ttk.Label(func_frame, text='OCR间隔(秒):').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ocr_interval_entry = ttk.Entry(func_frame, width=10)
        self.ocr_interval_entry.grid(row=1, column=1, padx=5, pady=5)
        self.ocr_interval_entry.insert(0, str(self.config['ocr_interval']))
        
        ttk.Label(func_frame, text='执行间隔(秒):').grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.action_interval_entry = ttk.Entry(func_frame, width=10)
        self.action_interval_entry.grid(row=2, column=1, padx=5, pady=5)
        self.action_interval_entry.insert(0, str(self.config['action_interval']))
        
        ttk.Label(func_frame, text='Tesseract路径:').grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.tesseract_entry = ttk.Entry(func_frame, width=40)
        self.tesseract_entry.grid(row=3, column=1, padx=5, pady=5, columnspan=3)
        self.tesseract_entry.insert(0, self.config['tesseract_path'])
        
        # 热键配置
        hotkey_frame = ttk.LabelFrame(main_frame, text='热键配置', padding='10')
        hotkey_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(hotkey_frame, text='启动热键:').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_hotkey_entry = ttk.Entry(hotkey_frame, width=20)
        self.start_hotkey_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=3)
        self.start_hotkey_entry.insert(0, self.config['start_hotkey'])
        
        ttk.Label(hotkey_frame, text='停止热键:').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.stop_hotkey_entry = ttk.Entry(hotkey_frame, width=20)
        self.stop_hotkey_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=3)
        self.stop_hotkey_entry.insert(0, self.config['stop_hotkey'])
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        self.start_button = ttk.Button(button_frame, text='启动', command=self.start_monitoring, width=15)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        self.stop_button = ttk.Button(button_frame, text='停止', command=self.stop_monitoring, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        self.save_button = ttk.Button(button_frame, text='保存配置', command=self.update_config, width=15)
        self.save_button.pack(side=tk.LEFT, padx=10)
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_var.set('就绪')
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground='blue')
        self.status_label.pack(pady=5)
        
        # 操作状态标签（用于显示延迟和加载状态）
        self.operation_status_var = tk.StringVar()
        self.operation_status_var.set('')
        self.operation_status_label = ttk.Label(main_frame, textvariable=self.operation_status_var, foreground='orange')
        self.operation_status_label.pack(pady=5)
    
    def setup_hotkeys(self):
        """设置热键"""
        keyboard.add_hotkey(self.config['start_hotkey'], self.start_monitoring)
        keyboard.add_hotkey(self.config['stop_hotkey'], self.stop_monitoring)
    
    def update_config(self):
        """更新配置"""
        try:
            self.config['monitor_area'] = {
                'x': int(self.x_entry.get()),
                'y': int(self.y_entry.get()),
                'width': int(self.width_entry.get()),
                'height': int(self.height_entry.get())
            }
            
            self.config['trigger_key'] = self.trigger_key_entry.get()
            self.config['ocr_interval'] = float(self.ocr_interval_entry.get())
            self.config['action_interval'] = float(self.action_interval_entry.get())  # 更新执行间隔
            self.config['tesseract_path'] = self.tesseract_entry.get()
            
            # 更新热键
            old_start_hotkey = self.config['start_hotkey']
            old_stop_hotkey = self.config['stop_hotkey']
            
            self.config['start_hotkey'] = self.start_hotkey_entry.get()
            self.config['stop_hotkey'] = self.stop_hotkey_entry.get()
            
            # 重新设置热键
            keyboard.remove_hotkey(old_start_hotkey)
            keyboard.remove_hotkey(old_stop_hotkey)
            self.setup_hotkeys()
            
            # 保存配置
            self.save_config()
            
            # 更新Tesseract路径
            pytesseract.pytesseract.tesseract_cmd = self.config['tesseract_path']
            
        except Exception as e:
            logger.error(f'更新配置失败: {e}')
            messagebox.showerror('错误', f'更新配置失败: {e}')
    
    def start_monitoring(self):
        """开始监控"""
        if not self.is_running:
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_var.set('运行中')
            self.status_label.config(foreground='green')
            
            logger.info('开始监控')
            
            # 启动监控线程
            self.monitor_thread = threading.Thread(target=self.monitor_screen)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_var.set('已停止')
            self.status_label.config(foreground='red')
            
            logger.info('停止监控')
    
    def monitor_screen(self):
        """监控屏幕"""
        while self.is_running:
            try:
                # 捕获屏幕
                screenshot = self.capture_screen()
                
                # 检查是否与上次截图相同
                if screenshot == self.last_screenshot:
                    time.sleep(self.config['ocr_interval'])
                    continue
                
                self.last_screenshot = screenshot
                
                # 执行OCR
                ocr_result = self.perform_ocr(screenshot)
                
                # 增强的OCR日志输出
                area = self.config['monitor_area']
                logger.info(f'OCR识别 - 监控区域: {area}, 识别结果: {repr(ocr_result.strip())}')
                
                # 检查是否包含"men"或"door"
                if 'men' in ocr_result.lower() or 'door' in ocr_result.lower():
                    # 查找关键词的位置
                    door_position = self.find_door_position(screenshot, ocr_result)
                    if door_position:
                        # 确定具体匹配的关键词
                        detected_word = 'men' if 'men' in ocr_result.lower() else 'door'
                        logger.info(f'检测到关键词"{detected_word}"，位置: {door_position}')
                        
                        # 检查执行间隔
                        current_time = time.time()
                        if current_time - self.last_action_time >= self.config['action_interval']:
                            self.perform_action(door_position)
                            self.last_action_time = current_time  # 更新上次执行时间
                        else:
                            remaining_time = self.config['action_interval'] - (current_time - self.last_action_time)
                            logger.info(f'执行间隔未到，剩余时间: {remaining_time:.1f}秒')
                            logger.info(f'进入休眠状态，减少系统资源占用')
                            
                            # 计算休眠时间，确保在间隔结束后准确恢复
                            # 分多次休眠，每次不超过OCR间隔的10倍，避免长时间阻塞
                            sleep_chunk = min(remaining_time, self.config['ocr_interval'] * 10)
                            total_slept = 0
                            
                            while total_slept < remaining_time and self.is_running:
                                # 计算本次休眠时间
                                current_sleep = min(sleep_chunk, remaining_time - total_slept)
                                time.sleep(current_sleep)
                                total_slept += current_sleep
                            
                            logger.info(f'休眠结束，恢复正常监控')
                            # 跳过本次循环的剩余部分，直接进入下一次监控
                            continue
                
                # 计算延迟并调整睡眠时间
                sleep_time = self.config['ocr_interval']
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f'监控线程错误: {e}')
                time.sleep(1)  # 出错时暂停1秒
    
    def capture_screen(self):
        """捕获屏幕指定区域"""
        area = self.config['monitor_area']
        screenshot = ImageGrab.grab(
            bbox=(area['x'], area['y'], area['x'] + area['width'], area['y'] + area['height']),
            all_screens=True
        )
        return screenshot
    
    def perform_ocr(self, image):
        """执行OCR识别（使用英文语言包）"""
        try:
            # 使用Tesseract进行英文OCR
            result = pytesseract.image_to_string(image, lang='eng')
            return result
        except Exception as e:
            logger.error(f'OCR识别错误: {e}')
            return ''
    
    def find_door_position(self, image, ocr_result):
        """查找"men"或"door"关键词的位置"""
        try:
            # 使用Tesseract获取文字位置信息（使用英文语言包）
            data = pytesseract.image_to_data(image, lang='eng', output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip().lower()
                # 查找"men"或"door"关键词
                if 'men' in text or 'door' in text:
                    # 获取文字的边界框
                    left = data['left'][i]
                    top = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]
                    
                    # 计算中心坐标（相对于监控区域）
                    center_x = left + width // 2
                    center_y = top + height // 2
                    
                    # 转换为屏幕坐标
                    screen_x = self.config['monitor_area']['x'] + center_x
                    screen_y = self.config['monitor_area']['y'] + center_y
                    
                    return (screen_x, screen_y)
            
            return None
        except Exception as e:
            logger.error(f'查找文字位置错误: {e}')
            return None
    
    def select_monitor_area(self):
        """选择监控区域（支持多显示器）"""
        # 获取所有显示器的边界
        import ctypes
        user32 = ctypes.windll.user32
        
        # 获取所有显示器的设备上下文
        hdc = user32.GetDC(None)
        
        # 计算所有显示器的总边界
        left = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        top = user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        width = user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
        height = user32.GetSystemMetrics(79)# SM_CYVIRTUALSCREEN
        
        user32.ReleaseDC(None, hdc)
        
        # 创建覆盖所有显示器的窗口
        root = tk.Toplevel(self.root)
        root.geometry(f'{width}x{height}+{left}+{top}')
        root.overrideredirect(True)  # 移除窗口边框
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)
        root.config(cursor='cross')
        
        # 创建画布
        canvas = Canvas(root, bg='gray', highlightthickness=0, width=width, height=height)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 变量
        start_x = start_y = end_x = end_y = 0
        rect_id = None
        selecting = False
        
        def on_mouse_down(event):
            nonlocal start_x, start_y, end_x, end_y, rect_id, selecting
            # 获取相对于整个虚拟屏幕的坐标
            start_x = event.x_root
            start_y = event.y_root
            end_x = event.x_root
            end_y = event.y_root
            selecting = True
            rect_id = canvas.create_rectangle(
                start_x - left, start_y - top, 
                end_x - left, end_y - top, 
                outline='red', width=2, fill=''
            )
        
        def on_mouse_move(event):
            nonlocal end_x, end_y, rect_id, selecting
            if selecting:
                # 获取相对于整个虚拟屏幕的坐标
                end_x = event.x_root
                end_y = event.y_root
                canvas.coords(
                    rect_id, 
                    min(start_x, end_x) - left, min(start_y, end_y) - top, 
                    max(start_x, end_x) - left, max(start_y, end_y) - top
                )
        
        def on_mouse_up(event):
            nonlocal selecting
            selecting = False
        
        def confirm_selection():
            nonlocal start_x, start_y, end_x, end_y
            # 计算区域坐标（相对于整个虚拟屏幕）
            x = min(start_x, end_x)
            y = min(start_y, end_y)
            width = abs(end_x - start_x)
            height = abs(end_y - start_y)
            
            if width > 0 and height > 0:
                # 更新配置
                self.x_entry.delete(0, tk.END)
                self.x_entry.insert(0, str(x))
                self.y_entry.delete(0, tk.END)
                self.y_entry.insert(0, str(y))
                self.width_entry.delete(0, tk.END)
                self.width_entry.insert(0, str(width))
                self.height_entry.delete(0, tk.END)
                self.height_entry.insert(0, str(height))
                
                logger.info(f'选择监控区域: x={x}, y={y}, width={width}, height={height}')
                root.destroy()
            else:
                messagebox.showwarning('警告', '请选择有效的监控区域')
        
        def cancel_selection():
            root.destroy()
        
        # 绑定事件
        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        
        # 添加确认和取消按钮
        button_frame = ttk.Frame(root)
        button_frame.place(relx=0.5, rely=0.95, anchor=tk.S)
        
        confirm_btn = ttk.Button(button_frame, text='确认', command=confirm_selection, width=15)
        confirm_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = ttk.Button(button_frame, text='取消', command=cancel_selection, width=15)
        cancel_btn.pack(side=tk.LEFT, padx=10)
        
        # 绑定键盘事件
        root.bind('<Return>', lambda e: confirm_selection())
        root.bind('<Escape>', lambda e: cancel_selection())
        
        # 显示提示信息
        canvas.create_text(
            width//2, height//2, 
            text='拖拽鼠标选择监控区域，按Enter确认，按Esc取消', 
            fill='white', font=('Arial', 16, 'bold')
        )
    
    def perform_action(self, position):
        """执行自动化操作，实现点击与按键之间0.5秒的执行间隔"""
        with self.action_lock:  # 确保同一时间只有一个操作执行
            try:
                current_time = time.time()
                operation_interval = 0.5  # 点击与按键之间的执行间隔
                
                # 更新GUI状态，显示操作进行中
                def update_gui_status(message):
                    """在GUI线程中更新状态"""
                    self.operation_status_var.set(message)
                    self.root.update_idletasks()
                
                # 检查上次操作时间，确保间隔0.5秒
                if current_time - self.last_operation_time < operation_interval:
                    wait_time = operation_interval - (current_time - self.last_operation_time)
                    wait_msg = f'等待操作间隔: {wait_time:.2f}秒'
                    logger.info(wait_msg)
                    self.root.after(0, update_gui_status, wait_msg)
                    time.sleep(wait_time)
                
                # 移动鼠标到指定位置
                pyautogui.moveTo(position[0], position[1], duration=0.2)
                
                # 执行左键单击
                pyautogui.click()
                click_msg = f'执行左键点击: 位置 {position}'
                logger.info(click_msg)
                self.root.after(0, update_gui_status, click_msg)
                
                # 更新操作时间
                self.last_operation_time = time.time()
                
                # 等待0.5秒后再执行按键操作
                wait_msg = '等待0.5秒后执行按键操作'
                logger.info(wait_msg)
                self.root.after(0, update_gui_status, wait_msg)
                time.sleep(0.5)
                
                # 触发自定义按键
                if self.config['trigger_key']:
                    pyautogui.press(self.config['trigger_key'])
                    key_msg = f'执行触发按键: {self.config["trigger_key"]}'
                    logger.info(key_msg)
                    self.root.after(0, update_gui_status, key_msg)
                
                # 更新最后操作时间
                self.last_operation_time = time.time()
                self.last_action_time = time.time()  # 更新执行操作时间
                
                # 清除操作状态
                self.root.after(1000, lambda: self.root.after(0, update_gui_status, ''))
                
            except Exception as e:
                logger.error(f'执行操作错误: {e}')
                self.root.after(0, update_gui_status, f'操作错误: {str(e)}')
                self.root.after(2000, lambda: self.root.after(0, update_gui_status, ''))
    
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == '__main__':
    app = AutoDoorApp()
    app.run()