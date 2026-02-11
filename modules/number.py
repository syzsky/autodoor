import threading
import time
import re
from PIL import Image, ImageGrab
from input.permissions import PermissionManager

class NumberModule:
    """数字识别模块"""
    def __init__(self, app):
        """
        初始化数字识别模块
        Args:
            app: 主应用实例
        """
        self.app = app
    
    def start_number_recognition(self):
        """开始数字识别"""
        def start_func():
            start_count = 0
            for i, region_config in enumerate(self.app.number_regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    threshold = region_config["threshold"].get()
                    key = region_config["key"].get()
                    # 创建线程并存储
                    thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key), daemon=True)
                    self.app.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.app.start_module("number", start_func)

    def stop_number_recognition(self):
        """停止数字识别"""
        # 清空线程列表
        if self.app.number_threads:
            self.app.number_threads.clear()
        # 更新状态标签
        if "number" in self.app.status_labels:
            self.app.status_labels["number"].set("数字识别: 未运行")

    def number_recognition_loop(self, region_index, region, threshold, key):
        """数字识别循环"""
        current_thread = threading.current_thread()

        # 检查线程是否在number_threads列表中，以及数字识别区域是否启用
        while current_thread in self.app.number_threads and self.app.number_regions[region_index]["enabled"].get():
            with self.app.state_lock:
                if not self.app.is_running:
                    break
            try:
                time.sleep(1)  # 1秒间隔

                # 截图并识别数字
                screenshot = self.take_screenshot(region)
                if screenshot is None:
                    continue
                text = self.ocr_number(screenshot)

                number = self.parse_number(text)
                if number is not None:
                    self.app.logging_manager.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        # 播放数字识别模块报警声音
                        self.app.alarm_module.play_alarm_sound(self.app.number_regions[region_index]["alarm"])

                        # 只有当数字小于阈值且按键不为空时才执行按键操作
                        if key:
                            self.app.event_manager.add_event(('keypress', key), ('number', region_index))
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}触发按键: {key}")
                        else:
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
                else:
                    # 识别失败时，输出原始识别结果
                    self.app.logging_manager.log_message(f"数字识别{region_index+1}结果: '{text}'")
            except Exception as e:
                self.app.logging_manager.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)

    def parse_number(self, text):
        """解析数字，支持X/Y格式
        只在识别失败时输出详细日志
        """
        # 移除可能的空格和换行符
        text = text.strip()
        if not text:
            return None

        # 检查缓存
        cache_key = text.lower()
        if cache_key in self.app._number_cache:
            return self.app._number_cache[cache_key]

        number = None
        try:
            # 策略1: X/Y格式（"123/456" → 123）
            match = re.search(r'^\s*(\d+)[/\s]', text)
            if match:
                number = int(match.group(1))
            else:
                # 策略2: 独立数字（"HP: 123" → 123）
                match = re.search(r'\b(\d+)\b', text)
                if match:
                    number = int(match.group(1))
                else:
                    # 策略3: 所有数字字符（"abc123def" → 123）
                    digits = ''.join(filter(str.isdigit, text))
                    if digits:
                        number = int(digits[:10])  # 限制长度防溢出
        except Exception as e:
            self.app.logging_manager.log_message(f"数字识别解析错误: {str(e)}")
            number = None

        # 缓存结果
        if number is not None:
            self.app._number_cache[cache_key] = number

        return number

    def take_screenshot(self, region):
        """截取指定区域的屏幕"""
        # 检查屏幕录制权限（macOS）
        if self.app.platform_adapter.platform == "Darwin":
            permission_manager = PermissionManager(self.app)
            if not permission_manager.check_screen_recording():
                # 在主线程中显示权限引导
                self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                return None
        
        x1, y1, x2, y2 = region
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        try:
            return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        except Exception as e:
            self.app.logging_manager.log_message(f"数字识别错误: 屏幕截图失败 - {str(e)}")
            return None

    def ocr_number(self, image):
        """识别数字，支持X/Y格式
        简化图像预处理，保留字符白名单以避免'ee'错误识别
        """
        import pytesseract
        
        image = image.convert('L')
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(image, lang='eng', config=config)

        # 4. 额外的文本清理，移除可能的换行符和空格
        text = text.strip().replace('\n', '').replace('\r', '')

        return text
