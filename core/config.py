import json
import os
import datetime

class ConfigManager:
    """统一配置管理器类"""
    
    def __init__(self, app):
        """初始化配置管理器
        Args:
            app: AutoDoorOCR实例
        """
        self.app = app
        self.config_file_path = app.config_file_path
    
    def read_config(self):
        """读取配置文件
        Returns:
            dict or None: 如果成功读取则返回配置字典，否则返回None
        """
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"开始加载配置: {self.config_file_path}")
            else:
                print(f"开始加载配置: {self.config_file_path}")
            return config
        except json.JSONDecodeError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
            else:
                print(f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
        except PermissionError:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"没有权限读取配置文件: {self.config_file_path}")
            else:
                print(f"没有权限读取配置文件: {self.config_file_path}")
        except IOError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件IO错误: {str(e)}")
            else:
                print(f"配置文件IO错误: {str(e)}")
        except Exception as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置加载错误: {str(e)}")
            else:
                print(f"配置加载错误: {str(e)}")
        return None
    
    def save_config(self, config):
        """保存配置到文件
        Args:
            config: 配置字典
        Returns:
            bool: 如果保存成功则返回True，否则返回False
        """
        try:
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)

            # 写入配置文件，使用更紧凑的格式
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)

            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message("配置已保存")
            else:
                print("配置已保存")
            return True
        except PermissionError:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"没有权限写入配置文件: {self.config_file_path}")
            else:
                print(f"没有权限写入配置文件: {self.config_file_path}")
            return False
        except IOError as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置文件IO错误: {str(e)}")
            else:
                print(f"配置文件IO错误: {str(e)}")
            return False
        except Exception as e:
            if hasattr(self.app, 'logging_manager'):
                self.app.logging_manager.log_message(f"配置保存错误: {str(e)}")
            else:
                print(f"配置保存错误: {str(e)}")
            return False
    
    def get_config_value(self, config, key_path, default=None):
        """获取配置值，支持嵌套路径
        Args:
            config: 配置字典
            key_path: 键路径，如 'tesseract.path' 或 ['tesseract', 'path']
            default: 默认值
        
        Returns:
            配置值
        """
        if isinstance(key_path, str):
            key_path = key_path.split('.')

        value = config
        for key in key_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
                # 如果值为None，返回默认值
                if value is None:
                    return default
            else:
                return default
        return value
    
    def get_full_config(self):
        """获取完整的配置数据结构
        Returns:
            dict: 完整的配置字典
        """
        # 获取各部分配置
        timed_groups_config = self.app._get_timed_config()
        number_regions_config = self.app._get_number_config()

        # 完整的配置数据结构，确保所有配置项都被保存
        config = {
            'version': self.app.version,  # 使用应用版本号
            'last_save_time': datetime.datetime.now().isoformat(),
            # 基本OCR配置
            'ocr': self.app._get_ocr_config(),
            # Tesseract配置
            'tesseract': self.app._get_tesseract_config(),
            # 定时功能配置
            'timed_key_press': {
                'groups': timed_groups_config
            },
            # 数字识别配置
            'number_recognition': {
                'regions': number_regions_config
            },
            # 快捷键配置 - 新增
            'shortcuts': self.app._get_shortcuts_config(),
            # 报警功能配置
            'alarm': self.app._get_alarm_config(),
            # 首页功能状态勾选框配置
            'home_checkboxes': self.app._get_home_checkboxes_config(),
            # 脚本和颜色识别配置
            'script': self.app._get_script_config()
        }
        return config
