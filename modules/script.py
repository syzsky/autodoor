import threading
import time
import re
import tkinter as tk

from modules.recorder import RecorderBase

class ScriptExecutor(RecorderBase):
    """脚本执行器类"""
    def __init__(self, app):
        super().__init__(app)
        self.is_running = False
        self.is_paused = False
        self.execution_thread = None
        self.recording_thread = None
        self.recording_events = []
        self.recording_start_time = None
        self.last_event_time = None
        self.recording_grace_period = False
        
        # 禁用CoreGraphics相关功能
        self.core_graphics_available = False

    def _optimize_delay(self, command, next_command=None):
        """统一延迟优化逻辑"""
        if command["type"] != "delay" or not next_command:
            return command
        
        # 按键操作前的延迟可减少 100ms（人类感知阈值）
        if next_command["type"] in ["keydown", "keyup", "click"]:
            optimized = command.copy()
            optimized["time"] = max(0, command["time"] - 100)
            return optimized
        
        return command
    
    def _execute_with_optimization(self, command, next_command=None):
        """统一执行入口，自动应用优化"""
        optimized = self._optimize_delay(command, next_command)
        self.execute_command(optimized)

    def run_script(self, script_content):
        """执行脚本（无限循环）"""
        def execute():
            self.is_running = True
            self.is_paused = False
            # 记录当前按下的按键，用于确保最终能抬起所有按键
            pressed_keys = set()
            
            try:
                # 解析脚本内容
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                # 无限循环执行脚本，直到用户停止
                while self.is_running:
                    # 遍历所有命令，执行一次
                    for i, command in enumerate(commands):
                        if not self.is_running:
                            break
                        
                        while self.is_paused:
                            time.sleep(0.1)
                            if not self.is_running:
                                break
                        
                        if not self.is_running:
                            break
                        
                        # 处理按键命令，跟踪按下的按键
                        if command["type"] in ["keydown", "keyup"]:
                            key = command["key"]
                            for _ in range(command["count"]):
                                if not self.is_running:
                                    break
                                while self.is_paused:
                                    time.sleep(0.1)
                                    if not self.is_running:
                                        break
                                if not self.is_running:
                                    break
                                
                                try:
                                    if command["type"] == "keydown":
                                        if key not in pressed_keys:
                                            self.app.input_controller.key_down(key)
                                            pressed_keys.add(key)
                                    elif command["type"] == "keyup":
                                        if key in pressed_keys:
                                            self.app.input_controller.key_up(key)
                                            pressed_keys.remove(key)
                                except Exception as e:
                                    self.app.logging_manager.log_message(f"执行按键 {key} 时出错: {str(e)}")
                        else:
                            # 使用统一的执行入口，自动应用延迟优化
                            next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                            self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.log_message(error_msg)
                self.app.status_var.set(f"执行错误: {str(e)}")
            finally:
                # 确保所有按下的按键都被抬起
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
        
        # 启动执行线程
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def run_script_once(self, script_content):
        """执行脚本（只执行一遍）"""
        def execute():
            self.is_running = True
            self.is_paused = False
            # 记录当前按下的按键，用于确保最终能抬起所有按键
            pressed_keys = set()
            
            try:
                # 解析脚本内容
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                
                # 只执行一遍脚本
                for i, command in enumerate(commands):
                    if not self.is_running:
                        break
                    
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    
                    if not self.is_running:
                        break
                    
                    # 处理按键命令，跟踪按下的按键
                    if command["type"] in ["keydown", "keyup"]:
                        key = command["key"]
                        for _ in range(command["count"]):
                            if not self.is_running:
                                break
                            while self.is_paused:
                                time.sleep(0.1)
                                if not self.is_running:
                                    break
                            if not self.is_running:
                                break
                            
                            if command["type"] == "keydown":
                                if key not in pressed_keys:
                                    self.app.input_controller.key_down(key)
                                    pressed_keys.add(key)
                            elif command["type"] == "keyup":
                                if key in pressed_keys:
                                    self.app.input_controller.key_up(key)
                                    pressed_keys.remove(key)
                    else:
                            # 使用统一的执行入口，自动应用延迟优化
                            next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                            self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.log_message(error_msg)
                self.app.status_var.set(f"执行错误: {str(e)}")
            finally:
                # 确保所有按下的按键都被抬起
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.log_message(f"抬起按键 {key} 时出错: {str(e)}")
                
                self.is_running = False
                self.app.logging_manager.log_message("脚本执行完成")
        
        # 启动执行线程
        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def parse_line(self, line):
        """解析单条伪代码命令"""
        line = line.strip()
        if not line:
            return None  # 跳过空行
        
        # 匹配 KeyDown 或 KeyUp 命令，支持单引号和双引号，大小写不敏感
        key_pattern = re.compile(r'^(KeyDown|KeyUp)\s+["\'](.*?)["\']\s*\,\s*(\d+)$', re.IGNORECASE)
        match = key_pattern.match(line)
        if match:
            command_type = match.group(1).lower()  # 转换为小写：keydown 或 keyup
            key = match.group(2).lower()  # 转换按键名为小写，适配 pyautogui
            count = int(match.group(3))  # 执行次数
            return {
                "type": command_type,
                "key": key,
                "count": count
            }
        
        # 匹配鼠标点击命令，格式：LeftDown 1、RightUp 1等，大小写不敏感
        mouse_pattern = re.compile(r'^(Left|Right|Middle)(Down|Up)\s+(\d+)$', re.IGNORECASE)
        match = mouse_pattern.match(line)
        if match:
            button = match.group(1).lower()  # 转换为小写：left、right、middle
            action = match.group(2).lower()  # 转换为小写：down、up
            count = int(match.group(3))  # 执行次数
            return {
                "type": f"mouse_{action}",
                "button": button,
                "count": count
            }
        
        # 匹配鼠标移动命令，格式：MoveTo 300,200，大小写不敏感
        move_pattern = re.compile(r"^MoveTo\s+(\d+)\s*\,\s*(\d+)$", re.IGNORECASE)
        match = move_pattern.match(line)
        if match:
            x = int(match.group(1))  # x坐标
            y = int(match.group(2))  # y坐标
            return {
                "type": "moveto",
                "x": x,
                "y": y
            }
        
        # 匹配 Delay 命令，大小写不敏感
        delay_pattern = re.compile(r"^Delay\s+(\d+)$", re.IGNORECASE)
        match = delay_pattern.match(line)
        if match:
            delay_time = int(match.group(1))  # 延迟时间（毫秒）
            return {
                "type": "delay",
                "time": delay_time
            }
        
        # 匹配特殊指令：StopScript 和 StartScript
        if line.strip().lower() == "stopscript":
            return {
                "type": "stopscript"
            }
        elif line.strip().lower() == "startscript":
            return {
                "type": "startscript"
            }
        
        # 如果都不匹配，返回 None 表示无效命令
        return None

    def execute_command(self, command):
        """执行单个命令"""
        try:
            if command["type"] in ["keydown", "keyup"]:
                key = command["key"]
                for _ in range(command["count"]):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    # 使用输入控制器执行按键操作
                    if command["type"] == "keydown":
                        self.app.input_controller.key_down(key)
                    else:
                        self.app.input_controller.key_up(key)
            elif command["type"] in ["mouse_down", "mouse_up"]:
                button = command["button"]
                for _ in range(command["count"]):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    # 使用输入控制器执行鼠标操作
                    if command["type"] == "mouse_down":
                        self.app.input_controller.mouse_down(button=button)
                    else:
                        self.app.input_controller.mouse_up(button=button)
            elif command["type"] == "moveto":
                x = command["x"]
                y = command["y"]
                if self.is_running and not self.is_paused:
                    # 使用输入控制器执行鼠标移动
                    self.app.input_controller.move_to(x, y)
            elif command["type"] == "delay":
                delay_time = command["time"] / 1000  # 转换为秒
                self.app.logging_manager.log_message(f"执行: 延迟 {delay_time}秒")
                
                # 分段延迟，以便能够响应暂停/停止命令
                start_time = time.time()
                elapsed_time = 0
                while elapsed_time < delay_time:
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    
                    sleep_time = min(0.1, delay_time - elapsed_time)
                    time.sleep(sleep_time)
                    elapsed_time = time.time() - start_time
            elif command["type"] == "stopscript":
                # 停止脚本执行，确保在主线程中执行
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 停止脚本")
                # 调用应用程序的停止脚本方法，使用after确保在主线程中执行，传递stop_color_recognition=False参数
                self.app.root.after(0, lambda: self.app.stop_script(stop_color_recognition=False))
                # 不立即设置is_running为False，让线程继续执行到下一个命令
            elif command["type"] == "startscript":
                # 启动脚本执行，确保在主线程中执行
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 启动脚本")
                # 调用应用程序的启动脚本方法，使用after确保在主线程中执行，传递start_color_recognition=False参数
                self.app.root.after(0, lambda: self.app.start_script(start_color_recognition=False))
        except Exception as e:
            # 添加错误处理，确保即使执行命令失败也不会导致应用程序崩溃
            error_msg = f"执行命令出错: {str(e)}"
            self.app.logging_manager.log_message(error_msg)
            # 记录详细的错误信息
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            # 继续执行其他命令，而不是终止整个脚本
            return

    def pause_script(self):
        """暂停脚本执行"""
        self.is_paused = True

    def resume_script(self):
        """恢复脚本执行"""
        self.is_paused = False

    def stop_script(self):
        """停止脚本执行"""
        self.is_running = False
        self.is_paused = False

    def start_recording(self):
        """开始录制按键"""
        # 检查平台并进行权限提示
        current_platform = self.app.platform_adapter.platform
        
        # 检查权限（macOS）
        if current_platform == "Darwin":
            try:
                import subprocess
                # 检查是否有辅助功能权限
                result = subprocess.run(["osascript", "-e", "tell application \"System Events\" to key code 1"], capture_output=True, timeout=2)
                if result.returncode != 0:
                    # 显示权限提示
                    self.app.root.after(0, lambda: self.app.show_message("权限提示", "在macOS上录制功能需要辅助功能权限，请在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中允许AutoDoor控制您的电脑。"))
            except Exception as e:
                pass
        
        # macOS平台，提示用户需要的权限
        if current_platform == "Darwin":
            # 使用after将提示延迟到主循环开始后显示
            self.app.root.after(100, lambda: self.app.show_message("提示", "在macOS上录制功能需要辅助功能权限，请在系统偏好设置中允许AutoDoor控制您的电脑。"))
        
        # 设置录制缓冲期，避免记录开始录制时的操作
        self.recording_grace_period = True
        
        def record():
            import time
            self.is_recording = True
            self.recording_events = []
            self.recording_start_time = time.time()
            self.last_event_time = self.recording_start_time
            
            # 记录当前按下的按键，用于避免重复记录
            pressed_keys = set()
            # 记录鼠标移动的最后位置
            last_mouse_position = None
            
            # macOS平台使用MacOSGlobalKeyListener，其他平台使用pynput
            if current_platform == "Darwin":
                # 0.5秒后关闭缓冲期，允许记录操作
                time.sleep(0.5)
                self.recording_grace_period = False
                
                # 添加日志记录
                self.app.logging_manager.log_message("🔴 开始录制操作...")
                
                # 由于CoreGraphics功能已禁用，无法使用全局按键监听器
                self.is_recording = False
                # 生成空脚本，避免后续处理出错
                self.recording_events = []
                self.generate_recorded_script()
                self.app.logging_manager.log_message("🟢 录制完成")
                return
            else:
                # 导入pynput模块
                keyboard = None
                mouse = None
                keyboard_listener = None
                mouse_listener = None
                
                try:
                    from pynput import keyboard, mouse
                except Exception as e:
                    # 给用户提供明确的提醒
                    self.app.root.after(0, lambda: self.app.show_message("提示", "无法启动录制功能，请确保pynput模块已正确安装。"))
                    self.is_recording = False
                    # 生成空脚本，避免后续处理出错
                    self.recording_events = []
                    self.generate_recorded_script()
                    return
                
                # 键盘事件处理
                def on_key_press(key):
                    if not self.is_recording:
                        return False
                    if getattr(self, 'recording_grace_period', False):
                        # 缓冲期结束
                        self.recording_grace_period = False
                        return
                    
                    try:
                        key_name = key.char
                    except AttributeError:
                        key_name = key.name
                    except Exception as e:
                        return
                    
                    # 检查是否是录制快捷键（F11），如果是则不记录
                    if key_name == 'f11':
                        return
                    
                    # 只记录首次按下的事件，避免重复记录
                    if key_name not in pressed_keys:
                        current_time = time.time()
                        delay = int((current_time - self.last_event_time) * 1000)
                        self.last_event_time = current_time
                        
                        try:
                            self.recording_events.append({
                                "type": "keydown",
                                "key": key_name,
                                "delay": delay
                            })
                            pressed_keys.add(key_name)
                        except Exception as e:
                            pass
                
                def on_key_release(key):
                    if not self.is_recording:
                        return False
                    if getattr(self, 'recording_grace_period', False):
                        return
                    
                    try:
                        key_name = key.char
                    except AttributeError:
                        key_name = key.name
                    except Exception as e:
                        return
                    
                    # 检查是否是录制快捷键（F11），如果是则不记录
                    if key_name == 'f11':
                        return
                    
                    # 只记录首次释放的事件
                    if key_name in pressed_keys:
                        current_time = time.time()
                        delay = int((current_time - self.last_event_time) * 1000)
                        self.last_event_time = current_time
                        
                        try:
                            self.recording_events.append({
                                "type": "keyup",
                                "key": key_name,
                                "delay": delay
                            })
                            pressed_keys.remove(key_name)
                        except Exception as e:
                            pass
                
                # 鼠标移动事件处理
                def on_mouse_move(x, y):
                    if not self.is_recording:
                        return False
                    if getattr(self, 'recording_grace_period', False):
                        return
                    
                    # 只记录鼠标位置，不立即添加到事件列表
                    nonlocal last_mouse_position
                    last_mouse_position = (x, y)
                
                # 鼠标点击事件处理
                def on_mouse_click(x, y, button, pressed):
                    if not self.is_recording:
                        return False
                    if getattr(self, 'recording_grace_period', False):
                        return
                    
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    
                    try:
                        button_name = button.name
                    except Exception as e:
                        return
                    
                    # 使用最后记录的鼠标位置或当前位置
                    if last_mouse_position:
                        mouse_x, mouse_y = last_mouse_position
                    else:
                        mouse_x, mouse_y = x, y
                    
                    try:
                        # 添加鼠标移动事件
                        self.recording_events.append({
                            "type": "moveto",
                            "x": int(mouse_x),
                            "y": int(mouse_y),
                            "delay": delay
                        })
                        
                        # 添加鼠标点击事件
                        self.recording_events.append({
                            "type": f"mouse_{'down' if pressed else 'up'}",
                            "button": button_name,
                            "x": int(mouse_x),
                            "y": int(mouse_y),
                            "delay": 0  # 鼠标移动后立即点击，不需要延迟
                        })
                    except Exception as e:
                        pass

                # 使用with语句创建监听器，确保在打包环境中也能正常工作
                import time
                
                # 0.5秒后关闭缓冲期，允许记录操作
                time.sleep(0.5)
                self.recording_grace_period = False
                
                # 添加日志记录
                self.app.logging_manager.log_message("🔴 开始录制操作...")

                try:
                    # 创建监听器
                    keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
                    mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click)
                    
                    # 注册资源
                    self.register_resource(keyboard_listener, lambda listener: listener.stop())
                    self.register_resource(mouse_listener, lambda listener: listener.stop())
                    
                    # 启动监听器
                    keyboard_listener.start()
                    mouse_listener.start()
                    
                    # 等待录制停止
                    while self.is_recording:
                        time.sleep(0.1)
                        
                except Exception as e:
                    # 给用户提供明确的提醒
                    self.app.root.after(0, lambda: self.app.show_message("提示", "无法启动录制功能，请确保pynput模块已正确安装。"))
                    self.is_recording = False
                finally:
                    # 使用统一的资源清理接口
                    self.cleanup_resources()
                    
                    # 生成录制脚本
                    self.generate_recorded_script()
                    self.app.logging_manager.log_message("🟢 录制完成")
        
        # 启动录制线程
        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()
        

    def _keycode_to_name(self, keycode):
        """将macOS keycode转换为按键名称"""
        # 完整的按键映射表
        key_map = {
            # 字母键
            0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x', 8: 'c', 9: 'v',
            11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r', 16: 'y', 17: 't',
            
            # 数字键
            18: '1', 19: '2', 20: '3', 21: '4', 22: '6', 23: '5', 25: '9', 26: '7', 28: '8', 29: '0',
            
            # 符号键
            24: 'equal', 27: 'minus', 30: 'right_bracket', 33: 'left_bracket', 36: 'return',
            39: 'apostrophe', 41: 'semicolon', 42: 'backslash', 43: 'comma', 44: 'slash',
            45: 'n', 46: 'm', 47: 'period',
            
            # 控制键
            48: 'tab', 49: 'space', 50: 'grave', 51: 'delete', 53: 'escape',
            54: 'command', 55: 'shift', 56: 'caps_lock', 57: 'option', 58: 'control',
            59: 'right_shift', 60: 'right_option', 61: 'right_control',
            
            # 功能键
            63: 'function', 64: 'f17', 69: 'f18', 70: 'f19', 71: 'f20',
            72: 'f5', 73: 'f6', 74: 'f7', 75: 'f3', 76: 'f8', 77: 'f9', 78: 'f11',
            79: 'f13', 80: 'f16', 81: 'f14', 82: 'f10', 83: 'f12', 84: 'f15',
            89: 'f4', 91: 'f2', 93: 'f1',
            
            # 特殊键
            65: 'volume_up', 66: 'volume_down', 67: 'mute', 85: 'help',
            86: 'home', 87: 'page_up', 88: 'forward_delete', 90: 'end', 92: 'page_down',
            
            # 方向键
            123: 'left', 124: 'right', 125: 'down', 126: 'up',
            
            # 数字键盘键
            82: 'kp_0', 83: 'kp_1', 84: 'kp_2', 85: 'kp_3', 86: 'kp_4',
            87: 'kp_5', 88: 'kp_6', 89: 'kp_7', 90: 'kp_8', 91: 'kp_9',
            65: 'kp_multiply', 67: 'kp_subtract', 69: 'kp_add', 75: 'kp_decimal',
            76: 'kp_divide', 78: 'kp_enter'
        }
        
        # 尝试获取按键名称
        key_name = key_map.get(keycode, None)
        
        # 如果未找到，返回一个默认值
        if not key_name:
            key_name = f"key_{keycode}"
        
        return key_name

    def stop_recording(self):
        """停止录制按键"""
        import time
        
        # 设置录制缓冲期，避免记录停止录制时的操作
        self.recording_grace_period = True
        self.is_recording = False
        self.is_listening = False  # 确保监听循环退出
        # 等待0.5秒后再生成脚本，确保缓冲期生效
        time.sleep(0.1)
        
        # 显式停止所有监听器
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            except:
                pass
        
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener = None
            except:
                pass
        
        if hasattr(self, 'key_listener') and self.key_listener:
            try:
                self.key_listener.stop_listening()  # 确保 CGEventTap 正确清理
                self.key_listener = None
            except:
                pass
        
        # 调用基类统一清理
        self.cleanup_resources()
        
        # 等待监听线程完全退出（最多 500ms）
        start = time.time()
        while any([hasattr(self, 'keyboard_listener') and self.keyboard_listener,
                   hasattr(self, 'mouse_listener') and self.mouse_listener,
                   hasattr(self, 'key_listener') and self.key_listener]) \
              and time.time() - start < 0.5:
            time.sleep(0.01)
        
        # 生成录制脚本
        try:
            self.generate_recorded_script()
        except Exception as e:
            pass
        
        # 播放停止运行音效
        try:
            self.app.play_stop_sound()
        except Exception as e:
            pass

    def generate_recorded_script(self):
        """生成录制脚本"""
        current_platform = self.app.platform_adapter.platform
        
        script_content = ""
        event_types = {"keydown": 0, "keyup": 0, "moveto": 0, "mouse_down": 0, "mouse_up": 0}
        
        try:
            if hasattr(self, 'recording_events'):
                for event in self.recording_events:
                    if event["delay"] > 0:
                        script_content += f"Delay {event['delay']}\n"
                    
                    if event["type"] in ["keydown", "keyup"]:
                        script_content += f"{event['type'].capitalize()} \"{event['key']}\", 1\n"
                        event_types[event["type"]] += 1
                    elif event["type"] == "moveto":
                        # 生成鼠标移动命令
                        script_content += f"MoveTo {event['x']}, {event['y']}\n"
                        event_types["moveto"] += 1
                    elif event["type"] in ["mouse_down", "mouse_up"]:
                        button = event["button"].capitalize()
                        action = event["type"].split('_')[1].capitalize()
                        script_content += f"{button}{action} 1\n"
                        event_types[event["type"]] += 1
            
            # 将生成的脚本插入到文本框
            self.app.root.after(0, lambda:
                (self.app.script_text.delete(1.0, self.app.script_text.index(tk.END)),
                 self.app.script_text.insert(1.0, script_content),
                 self.app.script_text.see(tk.END))
            )
        except Exception as e:
            pass
