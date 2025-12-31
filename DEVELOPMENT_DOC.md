# AutoDoor OCR 识别系统开发文档

## 一、功能模块划分与架构设计

### 1. 整体架构设计

#### 1.1 模块划分
| 模块名称 | 主要功能 | 对应界面 |
|---------|---------|---------|
| 核心框架 | 应用初始化、配置管理、日志管理 | 无直接界面 |
| 文字识别 | 关键词识别按键功能 | "文字识别"tab页 |
| 定时功能 | 定时自动按键功能 | "定时功能"tab页 |
| 数字识别 | 数字识别并按键功能 | "数字识别"tab页 |
| 公共组件 | 区域选择组件、按键配置组件 | 各功能模块内 |

#### 1.2 架构图
```
┌─────────────────────────────────────────────────────────────┐
│                   AutoDoor OCR 识别系统                     │
├───────────┬────────────┬────────────────┬─────────────────┤
│  核心框架  │  文字识别   │    定时功能    │    数字识别     │
├───────────┼────────────┼────────────────┼─────────────────┤
│ 配置管理   │ 关键词识别   │ 多组定时按键   │ 双区域数字识别  │
│ 日志管理   │ 区域选择     │ 自定义时间间隔  │ 阈值触发机制    │
│ 事件队列   │ 语言设置     │ 独立开关控制   │ 独立开关控制    │
│ 线程管理   │ 按键自定义   │ 独立运行       │ 独立运行       │
└───────────┴────────────┴────────────────┴─────────────────┘
```

### 2. 事件处理机制设计

#### 2.1 事件队列
- 采用FIFO队列管理所有触发事件
- 每个功能模块产生的事件都会被添加到事件队列
- 单独的事件处理线程按顺序执行事件
- 确保同一时间只有一个事件被处理，避免冲突

#### 2.2 线程管理
- 每个功能模块使用独立的监控线程
- 核心事件处理使用单线程，确保事件顺序执行
- 线程间通过事件队列通信，避免直接共享状态
- 支持优雅的线程启动和停止机制

## 二、核心功能实现思路与技术方案

### 1. 定时自动按键功能

#### 1.1 功能设计
- 支持3组独立的定时按键配置
- 每组可配置：
  - 时间间隔（秒）
  - 按键类型（键盘按键）
  - 启用/禁用状态
- 每组定时任务独立运行，互不干扰
- 支持动态调整配置

#### 1.2 实现思路
```python
class TimedKeyPress:
    def __init__(self):
        self.timer_groups = []  # 存储3组定时配置
        self.timer_threads = []  # 存储3个监控线程
        self.event_queue = None   # 事件队列引用
    
    def start(self):
        # 启动所有启用的定时任务线程
        pass
    
    def stop(self):
        # 停止所有定时任务线程
        pass
    
    def on_timer_trigger(self, key):
        # 将按键事件添加到事件队列
        self.event_queue.put(('keypress', key))
```

#### 1.3 关键技术点
- 使用`threading.Timer`实现定时触发
- 支持动态调整时间间隔
- 线程安全的配置更新机制

### 2. 数字识别并按键功能

#### 2.1 功能设计
- 支持2个独立的监控区域
- 每个区域可配置：
  - 监控区域坐标
  - 触发阈值
  - 触发按键
  - 启用/禁用状态
- 识别格式："X/Y"（如"1000/2000"）
- 当前半部分数值低于阈值时触发按键
- 识别频率：1次/秒

#### 2.2 实现思路
```python
class NumberRecognition:
    def __init__(self):
        self.regions = []  # 存储2个区域配置
        self.ocr_threads = []  # 存储2个识别线程
        self.event_queue = None  # 事件队列引用
        self.tesseract_path = ""  # Tesseract路径
    
    def start(self):
        # 启动所有启用的识别线程
        pass
    
    def stop(self):
        # 停止所有识别线程
        pass
    
    def recognize_number(self, region):
        # 截图并识别数字
        screenshot = self.take_screenshot(region)
        text = self.ocr_number(screenshot)
        return self.parse_number(text)
    
    def check_threshold(self, number, threshold, key):
        # 检查是否低于阈值，触发按键事件
        if number < threshold:
            self.event_queue.put(('keypress', key))
```

#### 2.3 关键技术点
- 使用`pyautogui`进行区域截图
- 使用`pytesseract`进行数字识别
- 正则表达式解析"X/Y"格式的数字
- 1秒间隔的定时识别机制

### 3. 功能兼容机制

#### 3.1 事件队列实现
```python
class EventQueue:
    def __init__(self):
        self.queue = deque()
        self.lock = threading.Lock()
        self.event = threading.Event()
        self.running = False
        self.process_thread = None
    
    def start(self):
        # 启动事件处理线程
        self.running = True
        self.process_thread = threading.Thread(target=self.process_events)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def stop(self):
        # 停止事件处理线程
        self.running = False
        self.event.set()
        if self.process_thread:
            self.process_thread.join()
    
    def put(self, event):
        # 添加事件到队列
        with self.lock:
            self.queue.append(event)
        self.event.set()
    
    def process_events(self):
        # 处理队列中的事件
        while self.running:
            if not self.queue:
                self.event.wait()
                self.event.clear()
                continue
            
            with self.lock:
                event = self.queue.popleft()
            
            # 执行事件
            self.execute_event(event)
    
    def execute_event(self, event):
        # 根据事件类型执行相应操作
        event_type, data = event
        if event_type == 'keypress':
            pyautogui.press(data)
        # 其他事件类型...
```

#### 3.2 线程同步机制
- 使用`threading.Lock`保护共享资源
- 使用`threading.Event`实现线程间通信
- 每个功能模块独立运行，通过事件队列协作
- 事件按顺序执行，避免并发冲突

## 三、前端界面修改设计

### 1. 界面整体结构

#### 1.1 Tab页设计
| Tab页名称 | 包含功能 | 对应模块 |
|----------|---------|---------|
| 文字识别 | 关键词识别按键功能 | 文字识别模块 |
| 定时功能 | 定时自动按键功能 | 定时功能模块 |
| 数字识别 | 数字识别并按键功能 | 数字识别模块 |
| 基本设置 | 坐标选取、通用配置 | 核心框架 |

#### 1.2 界面布局图
```
┌─────────────────────────────────────────────────────────────┐
│                    AutoDoor OCR 识别系统                     │
├─────────┬─────────┬─────────┬─────────┬───────────────────┤
│ 文字识别 │ 定时功能 │ 数字识别 │ 基本设置 │                   │
├─────────┴─────────┴─────────┴─────────┴───────────────────┤
│                                                           │
│                     [Tab页内容区域]                       │
│                                                           │
├───────────────────────────────────────────────────────────┤
│ 状态栏：显示当前状态、Tesseract可用性等                     │
└───────────────────────────────────────────────────────────┘
```

### 2. 各Tab页详细设计

#### 2.1 "文字识别"Tab页
| 区域 | 组件 | 功能 |
|-----|-----|-----|
| 功能开关 | 开关组件 | 启用/禁用文字识别功能 |
| 区域选择 | 按钮 | 启动区域选择功能 |
| 区域显示 | 标签 | 显示当前选择的区域坐标 |
| 识别设置 | 输入框、下拉框 | 设置识别间隔、语言、关键词 |
| 按键设置 | 输入框 | 设置触发按键 |
| 操作按钮 | 按钮 | 开始/停止识别 |

#### 2.2 "定时功能"Tab页
| 区域 | 组件 | 功能 |
|-----|-----|-----|
| 功能开关 | 开关组件 | 启用/禁用定时功能 |
| 定时组1 | 输入框、开关 | 配置第一组定时任务：时间间隔、按键、启用状态 |
| 定时组2 | 输入框、开关 | 配置第二组定时任务：时间间隔、按键、启用状态 |
| 定时组3 | 输入框、开关 | 配置第三组定时任务：时间间隔、按键、启用状态 |
| 操作按钮 | 按钮 | 开始/停止定时任务 |

#### 2.3 "数字识别"Tab页
| 区域 | 组件 | 功能 |
|-----|-----|-----|
| 功能开关 | 开关组件 | 启用/禁用数字识别功能 |
| 区域1配置 | 按钮、输入框、开关 | 区域选择、阈值设置、按键设置、启用状态 |
| 区域2配置 | 按钮、输入框、开关 | 区域选择、阈值设置、按键设置、启用状态 |
| 操作按钮 | 按钮 | 开始/停止数字识别 |

#### 2.4 "基本设置"Tab页
| 区域 | 组件 | 功能 |
|-----|-----|-----|
| 坐标轴选取 | 按钮 | 启动坐标选取功能 |
| 坐标显示 | 标签 | 显示当前选择的坐标 |
| 坐标模式 | 单选框 | 选择点击模式：中心/自定义 |
| 配置管理 | 按钮 | 保存/重置配置 |

## 四、数据存储方案

### 1. 配置文件结构

```json
{
  "tesseract_path": "tesseract/tesseract.exe",
  "ocr_interval": 5,
  "keywords": ["door", "men"],
  "ocr_language": "eng",
  "custom_key": "equal",
  "click_x": 0,
  "click_y": 0,
  "click_mode": "center",
  "selected_region": [0, 0, 0, 0],
  "pause_duration": 180,
  "click_delay": 0.5,
  
  // 定时功能配置
  "timed_key_press": {
    "enabled": false,
    "groups": [
      { "enabled": false, "interval": 10, "key": "space" },
      { "enabled": false, "interval": 20, "key": "enter" },
      { "enabled": false, "interval": 30, "key": "tab" }
    ]
  },
  
  // 数字识别配置
  "number_recognition": {
    "enabled": false,
    "regions": [
      { "enabled": false, "region": [0, 0, 0, 0], "threshold": 500, "key": "f1" },
      { "enabled": false, "region": [0, 0, 0, 0], "threshold": 1000, "key": "f2" }
    ]
  }
}
```

### 2. 配置管理实现

```python
def load_config(self):
    """加载配置文件"""
    if os.path.exists(self.config_file):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载现有配置
            self.tesseract_path = config.get('tesseract_path', '')
            self.ocr_interval = config.get('ocr_interval', 5)
            self.custom_keywords = config.get('keywords', ["door", "men"])
            self.ocr_language = config.get('ocr_language', "eng")
            self.custom_key = config.get('custom_key', "equal")
            self.click_x = config.get('click_x', 0)
            self.click_y = config.get('click_y', 0)
            self.click_mode = config.get('click_mode', "center")
            self.selected_region = tuple(config.get('selected_region', [0, 0, 0, 0]))
            self.pause_duration = config.get('pause_duration', 180)
            self.click_delay = config.get('click_delay', 0.5)
            
            # 加载定时功能配置
            self.timed_key_press_config = config.get('timed_key_press', {
                'enabled': False,
                'groups': [
                    { 'enabled': False, 'interval': 10, 'key': 'space' },
                    { 'enabled': False, 'interval': 20, 'key': 'enter' },
                    { 'enabled': False, 'interval': 30, 'key': 'tab' }
                ]
            })
            
            # 加载数字识别配置
            self.number_recognition_config = config.get('number_recognition', {
                'enabled': False,
                'regions': [
                    { 'enabled': False, 'region': [0, 0, 0, 0], 'threshold': 500, 'key': 'f1' },
                    { 'enabled': False, 'region': [0, 0, 0, 0], 'threshold': 1000, 'key': 'f2' }
                ]
            })
        except Exception as e:
            self.log_error(f"加载配置失败: {str(e)}")
            self.use_default_config()
    else:
        self.use_default_config()
```

## 五、开发进度与任务分解

### 1. 开发阶段划分

| 阶段 | 时间 | 主要任务 |
|-----|-----|---------|
| 阶段1 | 1-2天 | 前端界面重构：创建新Tab页，迁移现有功能 |
| 阶段2 | 2-3天 | 实现事件队列机制，确保功能兼容 |
| 阶段3 | 2-3天 | 实现定时自动按键功能 |
| 阶段4 | 3-4天 | 实现数字识别并按键功能 |
| 阶段5 | 2-3天 | 测试与优化：功能测试、性能测试、bug修复 |

### 2. 详细任务分解

#### 阶段1：前端界面重构
1. 创建4个Tab页：文字识别、定时功能、数字识别、基本设置
2. 迁移关键词识别按键功能到"文字识别"Tab页
3. 迁移"选择区域"功能为文字识别的局部组件
4. 迁移相关设置项到对应Tab页
5. 删除"高级设置"模块，迁移"坐标轴选取"到"基本设置"模块

#### 阶段2：事件队列实现
1. 设计并实现事件队列类
2. 设计事件处理机制
3. 实现线程安全的事件添加和处理
4. 测试事件顺序执行功能

#### 阶段3：定时自动按键功能
1. 设计定时功能的配置结构
2. 实现定时功能的前端界面
3. 实现定时功能的核心逻辑
4. 集成到事件队列系统
5. 测试独立运行和与其他功能的兼容性

#### 阶段4：数字识别并按键功能
1. 设计数字识别的配置结构
2. 实现数字识别的前端界面
3. 实现区域截图和数字识别功能
4. 实现阈值检查和按键触发逻辑
5. 集成到事件队列系统
6. 测试独立运行和与其他功能的兼容性

#### 阶段5：测试与优化
1. 功能测试：验证每个功能的正确性
2. 集成测试：验证多个功能同时运行的兼容性
3. 性能测试：检查CPU和内存占用
4. bug修复：解决发现的问题
5. 代码优化：提高代码质量和性能

## 六、测试计划与验收标准

### 1. 单元测试

| 测试模块 | 测试内容 | 验收标准 |
|---------|---------|---------|
| 事件队列 | 事件添加、事件处理、线程安全 | 事件按顺序执行，无丢失，无重复 |
| 定时功能 | 定时触发、动态调整、开关控制 | 定时准确，调整生效，开关正常 |
| 数字识别 | 区域截图、数字识别、阈值检查 | 识别准确率>95%，阈值判断正确 |
| 配置管理 | 配置加载、配置保存、默认配置 | 配置正确加载和保存，默认配置合理 |

### 2. 集成测试

| 测试场景 | 测试内容 | 验收标准 |
|---------|---------|---------|
| 多功能同时运行 | 文字识别+定时功能+数字识别 | 所有功能正常运行，无冲突 |
| 并发事件处理 | 同一时间触发多个事件 | 事件按顺序执行，无阻塞 |
| 功能开关切换 | 频繁切换各功能开关 | 功能正常启动和停止，无内存泄漏 |

### 3. 功能测试

| 功能模块 | 测试用例 | 验收标准 |
|---------|---------|---------|
| 文字识别 | 1. 设置关键词"test"，在屏幕上显示"test"，检查是否触发按键<br>2. 调整识别间隔，检查是否生效 | 1. 触发按键<br>2. 间隔调整生效 |
| 定时功能 | 1. 设置1秒间隔，检查是否每秒触发按键<br>2. 同时启用3组定时，检查是否都正常触发 | 1. 每秒触发<br>2. 3组都正常触发 |
| 数字识别 | 1. 在区域内显示"500/1000"，设置阈值600，检查是否触发按键<br>2. 显示"700/1000"，检查是否不触发 | 1. 触发按键<br>2. 不触发按键 |

### 4. 性能测试

| 测试项 | 测试方法 | 验收标准 |
|-------|---------|---------|
| CPU占用 | 同时运行所有功能，监控CPU使用率 | CPU使用率<30% |
| 内存占用 | 连续运行24小时，监控内存变化 | 内存稳定，无泄漏 |
| 响应时间 | 触发事件后，测量按键执行时间 | 响应时间<100ms |

## 七、技术栈与依赖

| 技术/依赖 | 版本 | 用途 |
|---------|-----|-----|
| Python | 3.12 | 开发语言 |
| Tkinter | 内置 | GUI框架 |
| pyautogui | 最新 | 屏幕截图、按键模拟 |
| pytesseract | 最新 | OCR识别 |
| opencv-python | 最新 | 图像处理（可选） |
| numpy | 最新 | 图像处理（可选） |
| Pillow | 最新 | 图像处理 |

## 八、代码结构与命名规范

### 1. 代码结构
```
autodoor/
├── autodoor.py          # 主程序文件
├── autodoor.spec        # PyInstaller打包配置
├── autodoor_config.json # 配置文件
├── requirements.txt     # 依赖列表
├── .gitignore          # Git忽略文件
└── tesseract/           # Tesseract OCR引擎
```

### 2. 命名规范
- 类名：使用大驼峰命名法，如`AutoDoorOCR`
- 方法名：使用小驼峰命名法，如`create_widgets`
- 变量名：使用下划线分隔命名法，如`ocr_interval`
- 常量名：使用全大写下划线分隔命名法，如`DEFAULT_INTERVAL`
- 注释：对重要功能和复杂逻辑添加详细注释

## 九、风险评估与应对策略

### 1. 风险评估

| 风险 | 影响 | 概率 |
|-----|-----|-----|
| Tesseract识别准确率问题 | 数字识别功能失效 | 中 |
| 多线程并发问题 | 功能冲突，程序崩溃 | 低 |
| 内存泄漏 | 程序运行时间长后性能下降 | 低 |
| 屏幕分辨率适配问题 | 区域选择不准确 | 中 |

### 2. 应对策略

| 风险 | 应对策略 |
|-----|---------|
| Tesseract识别准确率 | 1. 优化OCR参数<br>2. 添加图像预处理<br>3. 使用正则表达式验证识别结果 |
| 多线程并发问题 | 1. 使用事件队列确保顺序执行<br>2. 线程间通信使用线程安全机制<br>3. 定期检查线程状态 |
| 内存泄漏 | 1. 及时释放资源<br>2. 使用弱引用管理对象<br>3. 定期进行内存监控 |
| 屏幕分辨率适配 | 1. 使用相对坐标<br>2. 提供手动调整选项<br>3. 适配不同DPI设置 |

## 十、后续优化建议

1. **添加日志功能**：记录功能触发事件，便于调试和分析
2. **支持更多按键类型**：如组合键、鼠标事件等
3. **添加统计功能**：显示各功能的触发次数和成功率
4. **支持多语言界面**：提供中文和英文界面切换
5. **添加自动更新功能**：支持程序自动更新
6. **优化Tesseract调用**：提高识别速度和准确率
7. **添加快捷键支持**：方便用户快速操作
