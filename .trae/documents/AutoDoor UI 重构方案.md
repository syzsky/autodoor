## 重构方案概要

### 重构目标
将 Tkinter UI 迁移到 CustomTkinter，实现现代化界面，保证 Windows/macOS 双端兼容。

### 重构步骤

**阶段一：基础框架搭建**
1. 添加 `customtkinter>=5.2.0` 依赖
2. 创建 `ui/theme.py` - 主题配置
3. 创建 `ui/widgets.py` - 自定义组件

**阶段二：主程序重构**
1. 修改 `autodoor.py` 主入口
2. 实现侧边栏导航 + 内容区布局

**阶段三：标签页重构**
1. 重写 `ui/home.py` - 首页
2. 重写 `ui/ocr_tab.py` - 文字识别
3. 重写 `ui/timed_tab.py` - 定时功能
4. 重写 `ui/number_tab.py` - 数字识别
5. 重写 `ui/script_tab.py` - 脚本运行
6. 重写 `ui/basic_tab.py` - 基本设置

**阶段四：功能对接**
1. 连接UI与业务逻辑
2. 适配区域选择功能
3. 适配按键捕获功能

**阶段五：测试与优化**
1. 功能测试
2. 跨平台测试
3. 性能优化

### 不修改的文件
- `core/` 目录 - 核心逻辑
- `modules/` 目录 - 功能模块
- `input/` 目录 - 输入控制
- `utils/` 目录 - 工具函数

### 预计时间
约6天完成全部重构

详细方案已保存到 `design/REFACTOR_PLAN.md`