import threading
import time
import re
from PIL import Image, ImageGrab
from input.permissions import PermissionManager

class NumberModule:
    """数字识别模块"""
    def __init__(self, app):
        self.app = app
    
    def start_number_recognition(self):
        def start_func():
            start_count = 0
            for i, region_config in enumerate(self.app.number_regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    try:
                        threshold = int(region_config["threshold"].get())
                    except (ValueError, TypeError):
                        threshold = 500
                    key = region_config["key"].get()
                    stop_event = threading.Event()
                    self.app.number_stop_events[i] = stop_event
                    thread = threading.Thread(target=self.number_recognition_loop, args=(i, region, threshold, key, stop_event), daemon=True)
                    self.app.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        self.app.start_module("number", start_func)

    def stop_number_recognition(self):
        for stop_event in self.app.number_stop_events.values():
            stop_event.set()
        self.app.number_stop_events.clear()
        if self.app.number_threads:
            self.app.number_threads.clear()
        if "number" in self.app.status_labels:
            self.app.status_labels["number"].set("数字识别: 未运行")

    def number_recognition_loop(self, region_index, region, threshold, key, stop_event):
        while not stop_event.is_set() and self.app.number_regions[region_index]["enabled"].get():
            with self.app.state_lock:
                if not self.app.is_running:
                    break
            try:
                time.sleep(1)

                if stop_event.is_set():
                    return

                screenshot = self.take_screenshot(region)
                if screenshot is None:
                    continue
                text = self.ocr_number(screenshot)

                number = self.parse_number(text)
                if number is not None:
                    self.app.logging_manager.log_message(f"数字识别{region_index+1}解析结果: {number}")
                    if number < threshold:
                        self.app.alarm_module.play_alarm_sound(self.app.number_regions[region_index]["alarm"])

                        if key:
                            self.app.event_manager.add_event(('keypress', key), ('number', region_index))
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}触发按键: {key}")
                        else:
                            self.app.logging_manager.log_message(f"数字识别{region_index+1}按键配置为空，仅执行报警操作")
                else:
                    self.app.logging_manager.log_message(f"数字识别{region_index+1}结果: '{text}'")
            except Exception as e:
                self.app.logging_manager.log_message(f"数字识别{region_index+1}错误: {str(e)}")
                time.sleep(5)

    def parse_number(self, text):
        text = text.strip()
        if not text:
            return None

        cache_key = text.lower()
        if cache_key in self.app._number_cache:
            return self.app._number_cache[cache_key]

        number = None
        try:
            match = re.search(r'^\s*(\d+)\s*/', text)
            if match:
                number = int(match.group(1))
        except Exception as e:
            self.app.logging_manager.log_message(f"数字识别解析错误: {str(e)}")
            number = None

        if number is not None:
            self.app._number_cache[cache_key] = number

        return number

    def take_screenshot(self, region):
        if self.app.platform_adapter.platform == "Darwin":
            permission_manager = PermissionManager(self.app)
            if not permission_manager.check_screen_recording():
                self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                return None
        
        try:
            from utils.screenshot import ScreenshotManager
            screenshot_manager = ScreenshotManager()
            return screenshot_manager.get_region_screenshot(region)
        except Exception as e:
            self.app.logging_manager.log_message(f"数字识别错误: 屏幕截图失败 - {str(e)}")
            return None

    def ocr_number(self, image):
        import pytesseract
        
        image = image.convert('L')
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(image, lang='eng', config=config)

        text = text.strip().replace('\n', '').replace('\r', '')

        return text
