# -*- mode: python ; coding: utf-8 -*-

# 包豆AI - 自动化控制应用打包配置
# 适用于macOS平台的PyInstaller配置文件

# 分析阶段 - 确定所有需要的文件和依赖
a = Analysis(
    ['pyqt_main.py'],  # 主入口文件
    pathex=[],  # 额外的导入路径
    binaries=[],  # 二进制文件
    datas=[
        # 应用图标文件
        ('favicon.icns', '.'),  # macOS应用图标
        
        # 配置文件
        ('config.json', '.'),  # 应用配置文件
        
        # 资源文件夹
        ('imgs', 'imgs'),  # 图片资源文件夹
        
        # AI提示文本文件
        ('get_next_action_AI_doubao.txt', '.'),  # AI提示模板
        ('get_next_action_AI_doubao_mac.txt', '.'),  # macOS专用AI提示模板
        
        # 核心Python模块
        ('cv_shot_doubao.py', '.'),  # 截图处理模块
        ('log_window.py', '.'),  # 日志窗口模块
        ('vl_model_test_doubao2.py', '.'),  # AI模型测试模块
    ],
    hiddenimports=[
        # 自定义模块
        'cv_shot_doubao', 
        'vl_model_test_doubao2',
        'log_window',
        
        # PyQt5相关模块 - 确保所有GUI组件正确打包
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        
        # 图像处理和计算机视觉
        'cv2',
        'numpy',
        'PIL',  # Pillow图像库
        
        # 自动化控制
        'pyautogui',
        'pyperclip',
        'pygetwindow',
        'pyscreeze',
        'pymsgbox',
        'pyrect',
        'pytweening',
        'mouseinfo',
        
        # AI和API
        'openai',
        'httpx',
        
        # 数据验证和处理
        'pydantic',
        'pydantic_core',
        
        # 系统相关
        'platform',
        'ctypes',
        
        # 其他依赖
        'annotated_types',
        'jiter',
        'sniffio',
        'idna',
        'certifi',
        'httpcore',
        'h11',
        'anyio',
        'distro',
        'tqdm',
        'packaging',
        'pefile',
        'typing_extensions',
        'typing_inspection',
    ],
    hookspath=[],  # 自定义钩子路径
    hooksconfig={},  # 钩子配置
    runtime_hooks=[],  # 运行时钩子
    excludes=[
        # 排除不需要的模块以减小打包体积
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'jupyter',
        'IPython',
    ],
    noarchive=False,  # 不创建单一归档文件
    optimize=0,  # 不优化字节码
)

# 创建PYZ归档
pyz = PYZ(a.pure)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # 排除二进制文件，将在BUNDLE中包含
    name='baodou_AI',  # 可执行文件名
    debug=False,  # 不包含调试信息
    bootloader_ignore_signals=False,  # 不忽略引导加载器信号
    strip=False,  # 不剥离符号表
    upx=True,  # 使用UPX压缩
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,  # 启用窗口化错误追踪
    argv_emulation=False,  # 不模拟argv
    target_arch=None,  # 目标架构（None表示当前架构）
    codesign_identity=None,  # 代码签名身份（None表示不签名）
    entitlements_file=None,  # 权限文件
    icon='favicon.icns',  # 应用图标
)

# 创建macOS应用包
app = BUNDLE(
    exe,
    a.binaries,
    a.datas,
    name='baodou_AI.app',  # 应用包名
    icon='favicon.icns',  # 应用图标
    bundle_identifier='com.baodou.ai',  # 全球唯一标识符
    info_plist={
        # 应用信息
        'CFBundleName': '包豆AI',
        'CFBundleDisplayName': '包豆AI',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        
        # 应用类型和标识
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': 'baodou_AI',
        
        # 系统要求
        'LSMinimumSystemVersion': '10.14',  # 最低支持macOS Mojave
        'NSHighResolutionCapable': 'True',  # 支持高分辨率
        'NSSupportsAutomaticGraphicsSwitching': 'True',  # 支持自动图形切换
        
        # 界面设置
        'LSUIElement': '0',  # 0 显示 Dock 图标；1 仅菜单栏
        'NSAppTransportSecurity': {  # 网络安全设置
            'NSAllowsArbitraryLoads': True
        },
        
        # 权限设置
        'NSCameraUsageDescription': '包豆AI需要访问摄像头进行图像分析',
        'NSMicrophoneUsageDescription': '包豆AI需要访问麦克风进行语音控制',
        'NSDesktopFolderUsageDescription': '包豆AI需要访问桌面文件夹进行文件操作',
        'NSDocumentsFolderUsageDescription': '包豆AI需要访问文档文件夹进行文件操作',
        'NSDownloadsFolderUsageDescription': '包豆AI需要访问下载文件夹进行文件操作',
        
        # 其他设置
        'CFBundleGetInfoString': '包豆AI - 智能自动化控制工具',
        'CFBundleCopyright': 'Copyright © 2025 包豆AI. All rights reserved.',
    }
)