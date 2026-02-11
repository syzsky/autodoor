import threading
import time
import numpy as np
from PIL import Image, ImageGrab
import imagehash

class ColorRecognition:
    """颜色识别类"""
    def __init__(self, app):
        self.app = app
        self.is_running = False
        self.recognition_thread = None
        self.region = None
        self.target_color = None
        self.tolerance = 10
        self.interval = 5.0
        self.commands = ""
        
        # 禁用CoreGraphics相关功能
        self.core_graphics_available = False
        
        # 图像哈希缓存，用于检测区域是否变化
        self.last_image_hash = None

    def set_region(self, region):
        """设置颜色识别区域"""
        self.region = region

    def start_recognition(self, target_color, tolerance, interval, commands):
        """开始颜色识别"""
        self.target_color = target_color
        self.tolerance = tolerance
        self.interval = interval
        self.commands = commands
        
        def recognize():
            self.is_running = True
            
            while self.is_running:
                # 检查是否需要暂停（处理事件插队）
                if hasattr(self.app, 'event_queue') and not self.app.event_queue.empty():
                    # 如果队列非空，等待一段时间让事件处理线程处理事件
                    time.sleep(0.1)
                    continue
                
                # 执行颜色识别
                if self.recognize_color():
                    # 识别到目标颜色，执行命令
                    self.execute_commands()
                    # 执行后暂停一段时间
                    time.sleep(5)  # 避免频繁执行
                
                # 检查间隔
                time.sleep(self.interval)
            
            self.is_running = False
            self.app.status_var.set("颜色识别已停止")
            
            # 更新UI状态
            self.app.root.after(0, lambda:
                (self.app.status_var.set("颜色识别已停止"),)
            )
        
        # 启动识别线程
        self.recognition_thread = threading.Thread(target=recognize, daemon=True)
        self.recognition_thread.start()

    def recognize_color(self):
        """执行颜色识别（优化版本）"""
        if not self.region:
            self.app.logging_manager.log_message("颜色识别失败: 未设置识别区域")
            return False
        
        try:
            # 检查屏幕录制权限（macOS）
            if self.app.platform_adapter.platform == "Darwin":
                from input.permissions import PermissionManager
                permission_manager = PermissionManager(self.app)
                if not permission_manager.check_screen_recording():
                    # 在主线程中显示权限引导
                    self.app.root.after(0, lambda: self.app._guide_screen_recording_setup())
                    self.app.logging_manager.log_message("颜色识别失败: 缺少屏幕录制权限")
                    return False
            
            # 截取区域图像
            screenshot = None
            
            # 尝试使用ImageGrab.grab()
            try:
                screenshot = ImageGrab.grab(bbox=self.region, all_screens=True)
            except Exception as e:
                self.app.logging_manager.log_message(f"ImageGrab.grab()失败: {str(e)}")
            
            # 检查截图是否成功获取
            if not screenshot:
                self.app.logging_manager.log_message("颜色识别失败: 无法获取截图")
                return False
            
            # 检查截图是否为空
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.logging_manager.log_message("颜色识别失败: 截图为空")
                return False
            
            # 使用图像哈希检测区域是否变化
            current_hash = imagehash.average_hash(screenshot.resize((32, 32)))
            
            if self.last_image_hash and current_hash == self.last_image_hash:
                # 区域未变化，跳过颜色识别
                return False
            
            # 更新哈希缓存
            self.last_image_hash = current_hash
            
            # 转换为numpy数组
            img_array = np.array(screenshot)
            
            # 优化匹配逻辑，考虑RGB值范围限制
            valid_target_color = np.clip(np.array(self.target_color), 0, 255)
            lower_bound = np.maximum(0, valid_target_color - self.tolerance)
            upper_bound = np.minimum(255, valid_target_color + self.tolerance)
            
            # 区域采样：每隔几个像素检查一个，减少计算量
            sample_step = 2  # 每隔2个像素检查一个
            sampled_array = img_array[::sample_step, ::sample_step]
            
            # 向量化颜色匹配（NumPy 加速 100 倍+）
            is_match = np.all((sampled_array >= lower_bound) & (sampled_array <= upper_bound), axis=2)
            match_pixels = np.sum(is_match)
            
            # 计算匹配比例
            total_pixels = sampled_array.shape[0] * sampled_array.shape[1]
            match_ratio = match_pixels / total_pixels if total_pixels > 0 else 0
            
            if match_ratio > 0.1:  # 匹配比例超过10%认为识别到目标颜色
                # 识别到目标颜色
                self.app.logging_manager.log_message(f"✅ 识别到目标颜色，匹配比例: {match_ratio:.2f}")
                return True
            else:
                # 未识别到目标颜色
                return False
        except Exception as e:
            self.app.logging_manager.log_message(f"颜色识别错误: {str(e)}")
            # 添加详细的错误信息，帮助调试
            import traceback
            self.app.logging_manager.log_message(f"错误详情: {traceback.format_exc()}")
            # 即使出错也返回False，确保应用程序不会崩溃
            return False
    
    def execute_commands(self):
        """执行识别后命令（只执行一遍）"""
        if not self.commands:
            return
        
        # 创建临时脚本执行器
        from modules.script import ScriptExecutor
        temp_executor = ScriptExecutor(self.app)
        
        # 执行命令（只执行一遍）
        temp_executor.run_script_once(self.commands)

    def stop_recognition(self):
        """停止颜色识别"""
        self.is_running = False
        if hasattr(self, 'recognition_thread') and self.recognition_thread.is_alive():
            # 等待线程结束
            self.recognition_thread.join(timeout=1)