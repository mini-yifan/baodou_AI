# 包豆电脑 - AI 智能控制系统

## 项目简介

![软件图标](图标.jpg)

包豆电脑是一款基于 AI 视觉模型的智能控制系统，能够通过分析屏幕内容自动执行鼠标和键盘操作，实现任务自动化。该系统结合了 PyQt5 GUI 界面和豆包视觉模型，提供了直观的用户交互方式和强大的自动化能力。

### 核心功能

- 🖥️ **智能屏幕分析**：使用豆包视觉模型实时分析屏幕内容
- 🖱️ **自动鼠标控制**：根据分析结果执行精确的鼠标移动、点击、拖拽等操作
- ⌨️ **键盘自动化**：支持键盘输入、快捷键操作
- 📱 **直观 GUI 界面**：基于 PyQt5 的用户友好界面

## 目录结构

```
baodot_AI/
├── imgs/                  # 图片资源目录
│   └── label/             # 坐标标记图片存储
├── config.json            # 系统配置文件
├── README.md              # 项目说明文档
├── requirements.txt       # 项目依赖库文件
├── pyqt_main.spec         # 程序打包配置文件
├── get_next_action_AI_doubao.txt  # AI 系统提示文件（win版本）
├── get_next_action_AI_doubao_mac.txt  # AI 系统提示文件（mac版本）
├── pyqt_main.py           # 主程序入口 (GUI)
├── vl_model_test_doubao.py   # 豆包视觉模型调用模块，与GUI界面不连接（在本项目中不执行，可用于其他项目使用）
├── vl_model_test_doubao2.py  # 豆包视觉模型调用模块，与GUI界面连接
├── cv_shot_doubao.py      # 截图与坐标处理模块
└── favicon.ico            # 程序图标
```

## 获取项目

### 使用 Git 克隆

如果您已经安装了 Git，可以使用以下命令克隆项目：

```bash
git clone https://github.com/mini-yifan/baodou_AI.git

# 进入项目目录
cd baodou_AI
```

### 直接下载压缩包

如果您没有安装 Git，可以直接下载项目的压缩包：

1. 访问项目的 GitHub 页面
2. 点击右上角的 "Code" 按钮
3. 选择 "Download ZIP"
4. 下载完成后，解压到您想要存放的目录
5. 进入解压后的项目目录

## 环境搭建

### 1. 创建虚拟环境

#### Windows 系统

```bash
# 使用 Python 内置的 venv 模块创建虚拟环境
python -m venv new_venv

# 激活虚拟环境
new_venv\Scripts\activate
```

#### Linux/Mac 系统

```bash
# 创建虚拟环境
python3 -m venv new_venv

# 激活虚拟环境
source new_venv/bin/activate
```

### 2. 安装依赖库

在激活虚拟环境后，执行以下命令安装所需依赖：

一次性安装所有依赖库

```bash
# 升级 pip
pip install --upgrade pip

# 安装相关库
pip install -r requirements.txt
```

或者单独安装每个库：

```bash
# 升级 pip
pip install --upgrade pip

# 安装 PyQt5
pip install PyQt5 PyQt5-tools

# 安装计算机视觉相关库
pip install opencv-python numpy

# 安装自动化控制库
pip install pyautogui pyperclip

# 安装 AI API 客户端
pip install openai pydantic

# 安装截图相关库
pip install pillow
```

## 配置文件说明

配置文件 `config.json` 包含了系统的所有参数设置：

```json
{
  "api_config": {
    "api_key": "",          # 豆包 API 密钥
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",  # API 基础地址
    "model_name": "doubao-seed-1-6-vision-250815"  # 视觉模型名称
  },
  "ai_config": {
    "thinking_type": "disabled"  # AI 思考模式 "enabled" 或 "disabled"
  },
  "execution_config": {
    "max_visual_model_iterations": 80,  # 
    "default_max_iterations": 80        # 默认AI模型最大迭代次数
  },
  "screenshot_config": {
    "optimize_for_speed": true,  # 是否优化速度
    "max_png": 1280,             # 图片压缩后的最大尺寸
    "input_path": "imgs/screen.png",  # 截图保存路径
    "output_path": "imgs/label"        # 标记图片输出路径
  },
  "mouse_config": {
    "move_duration": 0.1,  # 鼠标移动持续时间
    "failsafe": false      # 鼠标安全模式
  }
}
```

## API 密钥申请

要使用本系统，您需要申请豆包 API 密钥：

1. 访问 [豆包开发者平台](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey)
2. 如果没有账号，先注册并登录
3. 进入 API 密钥管理页面
4. 点击 "创建 API 密钥" 按钮
5. 复制生成的 API 密钥
6. 在程序界面的 API 密钥输入框中粘贴，或直接修改 `config.json` 文件

## 使用方法

### 1. 启动程序

在虚拟环境中执行：

```bash
python pyqt_main.py
```

### 2. 配置 API 密钥

- 在程序界面中，找到 "请输入API密钥" 输入框
- 粘贴您申请的豆包 API 密钥
- 系统会自动保存密钥到 `config.json` 文件

### 3. 输入任务需求

在 "请输入您的需求" 文本框中，详细描述您需要完成的任务，例如：

```
请打开浏览器，搜索 "人工智能发展趋势"，并查看第一条搜索结果
```

### 4. 执行任务

点击 "上传并执行" 按钮，系统会：
1. 截取当前屏幕
2. 调用 AI 模型分析屏幕内容
3. 确定下一步操作
4. 执行鼠标/键盘操作
5. 循环以上步骤直到任务完成
(提示，当前版本只支持对电脑的主屏幕进行操作)

### 5. 停止任务

在 AI 执行过程中，您可以随时点击 "停止AI执行" 按钮中断任务。

## 文件功能详细说明

### 1. pyqt_main.py

主程序入口，负责：
- 创建 PyQt5 GUI 界面
- 处理用户输入和交互
- 管理 AI 执行线程
- 窗口防截图和透明化处理
- API 密钥管理

### 2. vl_model_test_doubao2.py

AI 核心控制模块，包含：
- 配置加载与管理
- 屏幕截图调用
- AI 模型 API 调用
- AI 响应解析
- 鼠标/键盘操作执行
- 坐标映射与转换
- 任务状态跟踪

### 3. cv_shot_doubao.py

屏幕处理工具模块，提供：
- `capture_screen_and_save()`: 屏幕截图功能
- `mark_coordinate_on_image()`: 坐标点标记
- `map_coordinates()`: 坐标映射与转换

### 4. get_next_action_AI_doubao.txt

AI 系统提示文件，定义了：
- AI 的行为规则和约束
- 操作类型和输出格式
- 特殊场景处理逻辑
- 示例场景和响应

### 5. config.json

系统配置文件，存储：
- API 密钥和模型参数
- AI 思考模式设置
- 执行参数配置
- 截图参数设置
- 鼠标操作参数

## 系统工作流程

1. **用户输入**：用户在 GUI 界面输入任务需求
2. **屏幕截图**：系统截取当前屏幕内容
3. **AI 分析**：调用豆包视觉模型分析屏幕内容
4. **操作决策**：AI 确定下一步操作（点击输入等）
5. **执行操作**：系统执行鼠标/键盘操作
6. **循环执行**：重复 2-5 步骤，直到任务完成

## 技术特点

### 1. AI 视觉模型

使用豆包最新的视觉模型 `doubao-seed-1-6-vision-250815`，能够：
- 精确识别屏幕元素
- 理解用户意图
- 生成合理的操作序列

### 2. 智能窗口设计

- **窗口置顶**：始终显示在最顶层，方便用户操作
- **透明度调节**：半透明设计，减少视觉干扰
- **防截图保护**：使用 Windows API 防止窗口被截图
- **自动避障**：窗口会自动避开 AI 即将操作的区域

### 3. 安全机制

- **循环限制**：防止无限循环执行
- **错误处理**：完善的异常捕获和处理机制
- **用户中断**：支持随时停止 AI 执行
- **坐标验证**：确保鼠标操作在安全范围内

## 打包程序

本项目支持使用 PyInstaller 打包为可执行文件，方便在没有 Python 环境的电脑上运行。

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 执行打包命令

```bash
pyinstaller pyqt_main.spec
```
（目前该命令仅适用于 Windows 系统）

### 3. 打包完成

打包完成后，可执行文件将生成在 `dist` 目录中：
- `dist/pyqt_main.exe` (Windows)

### 4. 注意事项

- 打包前确保所有依赖已正确安装
- 可能需要手动复制 `config.json` 和 `get_next_action_AI_doubao.txt` 到 `dist` 目录
- 首次运行需要在程序中配置 API 密钥

## 常见问题与解决方案

### 1. API 密钥错误

**问题**：程序显示 "AI执行错误，可能密钥错误或欠费"

**解决方案**：
- 检查 API 密钥是否正确
- 确保豆包账号有足够的余额
- 确认 API 密钥的地域设置正确（北京/新加坡）

### 2. 屏幕截图失败

**问题**：程序无法截取屏幕或保存截图

**解决方案**：
- 确保 `imgs` 目录存在且有写入权限
- 检查屏幕分辨率设置
- 关闭可能阻止截图的安全软件

### 3. 鼠标操作不准确

**问题**：AI 执行的鼠标操作位置不准确

**解决方案**：
- 检查屏幕分辨率和缩放设置
- 确保 `config.json` 中的截图参数正确
- 尝试调整 `mouse_config` 中的 `move_duration` 参数

### 4. 程序闪退

**问题**：程序启动后立即闪退

**解决方案**：
- 检查 Python 版本是否兼容（推荐 Python 3.8+）
- 确保所有依赖库已正确安装
- 尝试以非窗口模式运行，查看错误信息

## 安全注意事项

1. **API 密钥保护**：请勿将 API 密钥分享给他人或上传到公开仓库
2. **自动化风险**：使用自动化工具时请注意，避免执行危险操作
3. **隐私保护**：系统会截取屏幕内容发送到 AI 模型，请确保屏幕上没有敏感信息
4. **权限管理**：建议在受控环境中使用，避免对系统造成意外影响

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。


**感谢使用包豆电脑 AI 智能控制系统！** 🚀

