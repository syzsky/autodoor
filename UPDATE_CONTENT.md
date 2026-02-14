#### 更新内容
无

#### 优化内容
- **架构重构**：从单文件单体架构（7282行）重构为多文件模块化架构。
- **GUI框架升级**：从 tkinter/ttk 升级到 CustomTkinter，支持现代主题和更好的跨平台一致性
- **设计模式引入**：
  - 代理模式（Proxy）：`OCRProxy`、`TimedProxy`、`NumberProxy` 等实现模块解耦
  - 单例模式（Singleton）：`ScreenshotManager` 单例优化截图性能
  - 事件驱动模式：`EventManager` 支持优先级事件队列
- 配置管理器独立为 `core/config.py` 模块，支持更好的模块化测试

#### 修复内容
- 修复脚本内容不保存的问题：备份版本的 `_get_script_config()` 方法返回固定空字符串，导致脚本内容无法持久化
- 修复颜色识别配置丢失的问题：备份版本缺少 `color_tolerance`、`color_interval`、`color_recognition_enabled` 等配置项的保存
- 修复脚本延迟设置不保存的问题：新增 `delay_var`、`combo_key_delay`、`combo_after_delay` 配置项保存
- 尝试修复MacOS在V2.0版本更新后的多个兼容性问题
