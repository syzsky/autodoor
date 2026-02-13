import threading
import time
import random
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageGrab
import imagehash

from utils.image import _preprocess_image

class OCRModule:
    """
    OCR模块，负责文字识别核心逻辑
    """
    def __init__(self, app):
        self.app = app
        self.last_recognition_times = {}
        self.last_trigger_times = {}
    
    def start_monitoring(self):
        """开始监控"""
        if not self.app.tesseract_available:
            messagebox.showinfo("提示", "Tesseract OCR引擎未配置，请在设置中配置Tesseract路径后使用文字识别功能！")
            return

        has_enabled_group = False
        for group in self.app.ocr_groups:
            if group["enabled"].get() and group["region"]:
                has_enabled_group = True
                break

        if not has_enabled_group:
            messagebox.showwarning("警告", "请至少启用一个识别组并选择区域")
            return

        with self.app.state_lock:
            self.app.is_running = True
            self.app.is_paused = False

        self.app.status_labels["ocr"].set("文字识别: 运行中")
        self.app.logging_manager.log_message("开始监控...")

        self.app.ocr_thread = threading.Thread(target=self.ocr_loop, daemon=True)
        self.app.ocr_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        with self.app.state_lock:
            self.app.is_running = False

        self.app.status_labels["ocr"].set("文字识别: 未运行")
    
    def ocr_loop(self):
        """
        OCR识别循环
        """
        # 初始化每个组的上次识别时间和上次触发时间
        self.last_recognition_times = {i: 0 for i in range(len(self.app.ocr_groups))}  # 用于识别间隔
        self.last_trigger_times = {i: 0 for i in range(len(self.app.ocr_groups))}  # 用于暂停期
        
        # 初始化图像哈希缓存，用于增量截图优化
        last_hashes = {i: None for i in range(len(self.app.ocr_groups))}
        frame_counts = {i: 0 for i in range(len(self.app.ocr_groups))}

        while True:
            with self.app.state_lock:
                if not self.app.is_running:
                    break
            try:
                # 等待下一次识别，使用最小间隔
                min_interval = self._calculate_min_interval()
                self._wait_for_interval(min_interval)

                # 检查是否需要暂停
                with self.app.state_lock:
                    if self.app.is_paused:
                        continue

                current_time = time.time()

                # 遍历所有OCR组，并行处理
                for i, group in enumerate(self.app.ocr_groups):
                    if self._should_process_group(group, i, current_time):
                        # 执行OCR识别（使用优化后的版本）
                        self.perform_ocr_for_group_optimized(group, i, last_hashes, frame_counts)
                        # 更新上次识别时间
                        self.last_recognition_times[i] = current_time
            except Exception as e:
                self.app.logging_manager.log_message(f"错误: {str(e)}")
                time.sleep(5)
    
    def _calculate_min_interval(self):
        """
        计算所有启用组的最小间隔时间
        Returns:
            int: 最小间隔时间
        """
        enabled_groups = [group for group in self.app.ocr_groups if group["enabled"].get()]
        if enabled_groups:
            return min(group["interval"].get() for group in enabled_groups)
        return 5
    
    def _wait_for_interval(self, interval):
        """
        等待设定的间隔时间
        Args:
            interval: 间隔时间（秒）
        """
        for _ in range(interval):
            with self.app.state_lock:
                if not self.app.is_running:
                    break
            time.sleep(1)
    
    def _should_process_group(self, group, i, current_time):
        """
        检查是否应该处理指定的OCR组
        Args:
            group: OCR组配置
            i: 组索引
            current_time: 当前时间

        Returns:
            bool: 是否应该处理
        """
        # 检查组是否启用且已选择区域
        if not group["enabled"].get() or not group["region"]:
            return False

        # 获取组配置
        pause_duration = group["pause"].get()
        group_interval = group["interval"].get()

        # 检查是否在暂停期（触发动作后）
        if current_time - self.last_trigger_times[i] < pause_duration:
            return False

        # 检查是否达到识别间隔
        if current_time - self.last_recognition_times[i] < group_interval:
            return False

        return True
    
    def _validate_ocr_group_input(self, group, group_index):
        """
        验证OCR组输入参数
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, region, keywords_str, current_lang, click_enabled)
        """
        if not group:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None

        region = group.get("region")
        if not region:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置识别区域")
            return False, None, None, None, None

        keywords_str = group.get("keywords", tk.StringVar(value="")).get().strip()
        current_lang = group.get("language", tk.StringVar(value="eng")).get()
        click_enabled = group.get("click", tk.BooleanVar(value=False)).get()
        return True, region, keywords_str, current_lang, click_enabled
    
    def _validate_region_coordinates(self, region, group_index):
        """
        验证并规范化区域坐标
        Args:
            region: 区域坐标
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, left, top, right, bottom)
        """
        try:
            x1, y1, x2, y2 = region
            if len(region) != 4:
                raise ValueError("区域坐标格式错误")
        except (ValueError, TypeError) as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return False, None, None, None, None

        # 确保坐标是(left, top, right, bottom)格式
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        # 验证区域大小
        if (right - left) < 10 or (bottom - top) < 10:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 识别区域太小")
            return False, None, None, None, None

        return True, left, top, right, bottom
    
    def _capture_screen_region(self, left, top, right, bottom, group_index):
        """
        截取屏幕区域
        Args:
            left: 左上角x坐标
            top: 左上角y坐标
            right: 右下角x坐标
            bottom: 右下角y坐标
            group_index: OCR组索引

        Returns:
            Image: 截图图像
        """
        # 检查屏幕录制权限（macOS）
        if self.app.platform_adapter.platform == "Darwin":
            from input.permissions import PermissionManager
            permission_manager = PermissionManager(self.app)
            if not permission_manager.check_screen_recording():
                # 在主线程中显示权限引导
                self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 缺少屏幕录制权限")
                return None
        
        try:
            return ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 屏幕截图失败 - {str(e)}")
            return None
    

    
    def _perform_ocr(self, image, lang, group_index):
        """
        执行OCR识别
        Args:
            image: 处理后的图像
            lang: 识别语言
            group_index: OCR组索引

        Returns:
            str: 识别结果
        """
        try:
            import pytesseract
            # 使用优化的Tesseract配置进行OCR识别
            custom_config = r'--psm 6 --oem 3'
            text = pytesseract.image_to_string(image, lang=lang, config=custom_config)
            return text
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: OCR识别失败 - {str(e)}")
            return None
    
    def _find_keyword_position(self, image, keywords, lang, left, top, right, bottom, group_index):
        """
        查找关键词位置
        Args:
            image: 处理后的图像
            keywords: 关键词列表
            lang: 识别语言
            left: 左上角x坐标
            top: 左上角y坐标
            right: 右下角x坐标
            bottom: 右下角y坐标
            group_index: OCR组索引

        Returns:
            tuple: 点击位置坐标
        """
        try:
            import pytesseract
            # 使用image_to_data获取文字位置信息，使用相同的优化配置
            custom_config = r'--psm 6 --oem 3'
            data = pytesseract.image_to_data(image, lang=lang, config=custom_config, output_type=pytesseract.Output.DICT)

            # 遍历所有识别到的文字，找到关键词的位置
            for i in range(len(data['text'])):
                word = data['text'][i].lower().strip()
                if word in keywords or any(keyword in word for keyword in keywords):
                    # 获取文字的边界框
                    left_word = data['left'][i]
                    top_word = data['top'][i]
                    width = data['width'][i]
                    height = data['height'][i]

                    # 计算文字中心位置（相对于截图）
                    center_x = left_word + width // 2
                    center_y = top_word + height // 2

                    # 转换为屏幕坐标
                    return (left + center_x, top + center_y)

            # 如果没有找到关键词位置，使用区域中心
            return ((left + right) // 2, (top + bottom) // 2)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 获取文字位置失败 - {str(e)}")
            # 失败时使用区域中心
            return ((left + right) // 2, (top + bottom) // 2)
    
    def perform_ocr_for_group(self, group, group_index):
        """
        为单个OCR组执行OCR识别
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        """
        try:
            # 检查是否正在运行
            with self.app.state_lock:
                if not self.app.is_running:
                    return

            # 验证输入参数
            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            # 验证区域坐标
            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            # 截取屏幕区域
            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return

            # 图像预处理
            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                return

            # OCR识别
            text = self._perform_ocr(processed_image, current_lang, group_index)
            if not text:
                return

            self.app.logging_manager.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}'")

            # 检查是否包含关键词
            lower_text = text.lower()
            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                if any(keyword in lower_text for keyword in keywords):
                    # 确定点击位置
                    if click_enabled:
                        click_pos = self._find_keyword_position(processed_image, keywords, current_lang, left, top, right, bottom, group_index)
                    else:
                        # 未启用点击，使用区域中心
                        click_pos = ((left + right) // 2, (top + bottom) // 2)

                    # 触发动作，传递文字位置
                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)

        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
    
    def perform_ocr_for_group_optimized(self, group, group_index, last_hashes, frame_counts):
        """
        为单个OCR组执行OCR识别（优化版本，使用增量截图和自适应帧率）
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
            last_hashes: 上次图像哈希缓存
            frame_counts: 帧计数
        """
        try:
            # 检查是否正在运行
            with self.app.state_lock:
                if not self.app.is_running:
                    return

            # 验证输入参数
            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            # 验证区域坐标
            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            # 截取屏幕区域
            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return

            # 计算图像哈希，用于检测画面变化
            current_hash = imagehash.average_hash(screenshot.resize((64, 64)))
            
            # 检查画面是否变化，避免重复OCR
            if current_hash == last_hashes.get(group_index) and frame_counts.get(group_index, 0) % 5 != 0:
                # 画面未变化，跳过OCR（节省80%+ CPU）
                frame_counts[group_index] += 1
                return
            
            # 更新哈希缓存
            last_hashes[group_index] = current_hash
            frame_counts[group_index] += 1

            # 开始计时，用于自适应帧率
            start_time = time.time()

            # 图像预处理
            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                return

            # OCR识别
            text = self._perform_ocr(processed_image, current_lang, group_index)
            if not text:
                return

            # 计算OCR耗时
            elapsed_time = time.time() - start_time
            
            # 自适应帧率：根据OCR耗时调整延迟
            # 目标10 FPS，根据实际耗时调整睡眠时间
            sleep_time = max(0.01, 0.1 - elapsed_time)
            time.sleep(sleep_time)

            self.app.logging_manager.log_message(f"识别组{group_index+1}识别结果: '{text.strip()}' (耗时: {elapsed_time:.2f}s, 延迟: {sleep_time:.2f}s)")

            # 检查是否包含关键词
            lower_text = text.lower()
            if keywords_str:
                keywords = [keyword.strip().lower() for keyword in keywords_str.split(",") if keyword.strip()]
                if any(keyword in lower_text for keyword in keywords):
                    # 确定点击位置
                    if click_enabled:
                        click_pos = self._find_keyword_position(processed_image, keywords, current_lang, left, top, right, bottom, group_index)
                    else:
                        # 未启用点击，使用区域中心
                        click_pos = ((left + right) // 2, (top + bottom) // 2)

                    # 触发动作，传递文字位置
                    self.trigger_action_for_group(group, group_index, click_enabled, click_pos)

        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
    
    def _validate_trigger_input(self, group, group_index):
        """
        验证触发动作的输入参数
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
        
        Returns:
            tuple: (valid, key, delay_min, delay_max, alarm_enabled, region)
        """
        if not group:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None, None

        # 获取组配置
        key = group.get("key", tk.StringVar(value="")).get()
        delay_min = group.get("delay_min", tk.IntVar(value=300)).get()
        delay_max = group.get("delay_max", tk.IntVar(value=500)).get()
        alarm_enabled = group.get("alarm", tk.BooleanVar(value=False)).get()
        region = group.get("region")

        # 验证必要参数
        if not key:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置触发按键")
            return False, None, None, None, None, None

        # 验证延迟参数
        if delay_min < 0 or delay_max < delay_min:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 延迟参数无效")
            delay_min = 300
            delay_max = 500

        return True, key, delay_min, delay_max, alarm_enabled, region
    
    def _calculate_click_position(self, click_pos, region, group_index):
        """
        计算点击位置
        Args:
            click_pos: 点击位置坐标
            region: 区域坐标
            group_index: OCR组索引

        Returns:
            tuple: (click_x, click_y)
        """
        if click_pos is not None:
            return click_pos

        if not region:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 未设置识别区域，无法计算点击位置")
            return None, None

        try:
            # 计算点击位置（区域中心）
            x1, y1, x2, y2 = region
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
            return click_x, click_y
        except (ValueError, TypeError) as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return None, None
    
    def _execute_mouse_click(self, click_x, click_y, group_index):
        """
        执行鼠标点击
        Args:
            click_x: 点击x坐标
            click_y: 点击y坐标
            group_index: OCR组索引
        """
        # 检查是否正在运行
        if not self.app.is_running or getattr(self.app, 'system_stopped', False):
            return

        if click_x is not None and click_y is not None:
            # 使用输入控制器执行鼠标点击操作
            self.app.input_controller.click(click_x, click_y)
            # 等待固定时间
            time.sleep(self.app.click_delay)
    
    def _execute_key_press(self, key, delay, group_index):
        """
        执行按键操作
        Args:
            key: 按键
            delay: 延迟时间
            group_index: OCR组索引
        """
        # 检查是否正在运行
        if not self.app.is_running or getattr(self.app, 'system_stopped', False):
            return

        # 使用输入控制器执行按键操作
        self.app.input_controller.press_key(key, delay)

        # 更新该组的上次触发时间，进入暂停期
        self.last_trigger_times[group_index] = time.time()
    
    def _play_alarm_if_enabled(self, alarm_enabled, group_index):
        """
        播放报警声音（如果启用）
        Args:
            alarm_enabled: 是否启用报警
            group_index: OCR组索引
        """
        try:
            if alarm_enabled and self.app.PYGAME_AVAILABLE:
                # 创建一个临时的BooleanVar对象来传递给play_alarm_sound方法
                import tkinter as tk
                temp_alarm_var = tk.BooleanVar(value=True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 播放报警声音失败 - {str(e)}")
    
    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None):
        """
        为单个OCR组触发动作
        Args:
            group: OCR组配置字典
            group_index: OCR组索引
            click_enabled: 是否启用点击
            click_pos: 点击位置坐标
        """
        try:
            # 检查是否正在运行
            with self.app.state_lock:
                if not self.app.is_running or getattr(self.app, 'system_stopped', False):
                    return

            # 验证输入参数
            valid, key, delay_min, delay_max, alarm_enabled, region = self._validate_trigger_input(group, group_index)
            if not valid:
                return

            self.app.logging_manager.log_message(f"识别组{group_index+1}触发动作，按键: {key}")

            # 生成随机延迟
            delay = random.randint(delay_min, delay_max) / 1000.0

            # 如果启用点击，执行鼠标点击
            if click_enabled:
                click_x, click_y = self._calculate_click_position(click_pos, region, group_index)
                self._execute_mouse_click(click_x, click_y, group_index)

            # 执行按键操作
            self._execute_key_press(key, delay, group_index)
        except Exception as e:
            self.app.logging_manager.log_message(f"识别组{group_index+1}错误: 触发动作失败 - {str(e)}")
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")

        # 播放报警声音（如果启用）
        if 'alarm_enabled' in locals():
            self._play_alarm_if_enabled(alarm_enabled, group_index)
