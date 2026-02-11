import os
import sys
import subprocess
import pytesseract
from PIL import Image


class TesseractManager:
    """
    Tesseract管理类，负责管理Tesseract OCR引擎的配置和验证
    """
    
    def __init__(self, app):
        """
        初始化Tesseract管理器
        Args:
            app: 应用程序实例
        """
        self.app = app
    
    def get_default_tesseract_path(self):
        """
        获取默认的Tesseract路径，使用项目自带的tesseract
        支持Windows和Mac平台，同时支持打包后的环境
        Returns:
            str: Tesseract可执行文件的路径，如果未找到则返回空字符串
        """
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            # 打包后的环境，使用_MEIPASS获取运行目录
            app_root = sys._MEIPASS
        else:
            # 开发环境，使用当前文件所在目录
            app_root = os.path.dirname(os.path.abspath(__file__))

        # 使用平台适配器获取可能的Tesseract路径
        possible_paths = self.app.platform_adapter.get_tesseract_paths(app_root)
        
        # 查找存在的Tesseract可执行文件
        tesseract_path = ""
        for path in possible_paths:
            if os.path.exists(path):
                tesseract_path = path
                break

        # 确保tessdata目录存在
        if tesseract_path:
            # 尝试多个可能的tessdata目录路径
            possible_tessdata_paths = [
                os.path.join(os.path.dirname(tesseract_path), "tessdata"),  # tesseract同目录下的tessdata
                os.path.join(app_root, "tessdata"),  # 应用根目录下的tessdata
                os.path.join(app_root, "tesseract", "tessdata"),  # tesseract子目录下的tessdata
                # macOS应用包路径
                os.path.join(os.path.dirname(os.path.dirname(app_root)), "Resources", "tesseract", "tessdata"),
                # macOS系统路径
                "/usr/local/share/tessdata",  # Homebrew (Intel)
                "/opt/homebrew/share/tessdata",  # Homebrew (Apple Silicon)
            ]
            
            for tessdata_path in possible_tessdata_paths:
                if os.path.exists(tessdata_path):
                    self.app.logging_manager.log_message(f"找到tessdata目录: {tessdata_path}")
                    # 设置TESSDATA_PREFIX环境变量
                    os.environ["TESSDATA_PREFIX"] = tessdata_path
                    self.app.logging_manager.log_message(f"设置TESSDATA_PREFIX环境变量: {tessdata_path}")
                    break

        self.app.logging_manager.log_message(f"默认Tesseract路径: {tesseract_path}")
        return tesseract_path
    
    def _validate_tesseract_path(self):
        """
        验证Tesseract路径有效性

        Returns:
            bool: 如果路径有效则返回True，否则返回False
        """
        if not self.app.tesseract_path:
            self.app.logging_manager.log_message("Tesseract路径未配置")
            return False

        if not os.path.exists(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不存在: {self.app.tesseract_path}")
            return False

        if not os.path.isfile(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不是文件: {self.app.tesseract_path}")
            return False

        return True
    
    def _check_tesseract_permissions(self):
        """
        检查并修复Tesseract执行权限
        Returns:
            bool: 如果权限正确则返回True，否则返回False
        """
        if not self.app.platform_adapter.is_valid_tesseract_path(self.app.tesseract_path):
            self.app.logging_manager.log_message(f"Tesseract路径不是有效可执行文件: {self.app.tesseract_path}")
            return False

        if self.app.platform_adapter.platform == "Darwin":  # macOS
            if not os.access(self.app.tesseract_path, os.X_OK):
                self.app.logging_manager.log_message(f"Tesseract文件缺少执行权限，尝试修复: {self.app.tesseract_path}")
                try:
                    subprocess.run(["chmod", "+x", self.app.tesseract_path], 
                                  capture_output=True, check=True, timeout=5)
                    self.app.logging_manager.log_message("成功添加执行权限")
                except Exception as e:
                    self.app.logging_manager.log_message(f"添加执行权限失败: {str(e)}")
                    return False
        # 其他平台不做严格检查
        return True

    def _check_tesseract_version(self):
        """
        检查Tesseract版本兼容性
        Returns:
            bool: 如果版本兼容则返回True，否则返回False
        """
        try:
            version_result = subprocess.run(
                [self.app.tesseract_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )

            version_output = version_result.stdout.strip()
            if "tesseract" in version_output.lower():
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    self.app.logging_manager.log_message(f"检测到Tesseract版本: {version_str}")

                    try:
                        cleaned_version = version_str.lstrip('v')
                        major_version = int(cleaned_version.split('.')[0])
                        if major_version < 4:
                            self.app.logging_manager.log_message(f"Tesseract版本太旧 ({version_str})，建议使用4.x或更高版本")
                            return False
                    except (ValueError, IndexError):
                        self.app.logging_manager.log_message(f"无法解析Tesseract版本: {version_str}")
                        # 继续执行，不因为版本解析失败而直接返回False
            return True
        except Exception as e:
            self.app.logging_manager.log_message(f"版本检查失败: {str(e)}")
            return False

    def _get_test_file_path(self):
        """
        获取测试文件路径
        Returns:
            str: 测试文件路径
        """
        return self.app.platform_adapter.get_test_file_path()

    def _cleanup_test_files(self, test_file_path):
        """
        清理测试文件
        Args:
            test_file_path: 测试文件路径
        """
        if os.path.exists(test_file_path):
            try:
                os.remove(test_file_path)
            except Exception as e:
                self.app.logging_manager.log_message(f"清理测试文件失败: {str(e)}")

    def _test_tesseract_functionality(self):
        """
        测试Tesseract基本功能
        Returns:
            bool: 如果功能测试通过则返回True，否则返回False
        """
        try:
            pytesseract.pytesseract.tesseract_cmd = self.app.tesseract_path

            test_file_path = self._get_test_file_path()
            test_image = Image.new('RGB', (100, 30), color='white')
            test_image.save(test_file_path)

            test_result = pytesseract.image_to_string(test_file_path, lang='eng', timeout=5)

            self._cleanup_test_files(test_file_path)
            return True
        except Exception as e:
            test_file_path = self._get_test_file_path()
            self._cleanup_test_files(test_file_path)
            self.app.logging_manager.log_message(f"功能测试失败: {str(e)}")
            return False

    def check_tesseract_availability(self):
        """
        检查Tesseract OCR是否可用

        包括：
        1. 路径有效性验证
        2. 版本兼容性检查
        3. 基础功能测试

        Returns:
            bool: 如果Tesseract OCR可用则返回True，否则返回False
        """
        # 如果tesseract路径为空，尝试获取默认路径
        if not self.app.tesseract_path:
            self.app.tesseract_path = self.get_default_tesseract_path()
            if not self.app.tesseract_path:
                self.app.logging_manager.log_message("Tesseract路径未配置")
                return False
            else:
                self.app.logging_manager.log_message(f"使用默认Tesseract路径: {self.app.tesseract_path}")
                # 保存配置，确保默认路径被保存到配置文件
                self.app._defer_save_config()

        try:
            if not self._validate_tesseract_path():
                return False

            if not self._check_tesseract_permissions():
                return False

            if not self._check_tesseract_version():
                return False

            if not self._test_tesseract_functionality():
                return False

            # 配置界面中的路径变量
            if hasattr(self.app, 'tesseract_path_var'):
                self.app.tesseract_path_var.set(self.app.tesseract_path)

            self.app.logging_manager.log_message("Tesseract OCR引擎检测通过")
            return True

        except subprocess.TimeoutExpired:
            self.app.logging_manager.log_message(f"Tesseract命令执行超时: {self.app.tesseract_path}")
            return False
        except subprocess.CalledProcessError as e:
            self.app.logging_manager.log_message(f"Tesseract命令执行失败: {e}")
            return False
        except FileNotFoundError:
            self.app.logging_manager.log_message(f"Tesseract可执行文件未找到: {self.app.tesseract_path}")
            return False
        except pytesseract.TesseractError as e:
            self.app.logging_manager.log_message(f"Tesseract OCR测试失败: {e}")
            return False
        except PermissionError as e:
            self.app.logging_manager.log_message(f"Tesseract权限错误: {str(e)}")
            return False
        except Exception as e:
            self.app.logging_manager.log_message(f"Tesseract检测发生未知错误: {str(e)}")
            return False
