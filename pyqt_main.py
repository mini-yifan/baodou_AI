import sys
import time
import ctypes
import os
import json

# 仅在开发环境中设置Qt平台插件路径，打包时自动处理
if os.path.exists('venv/Lib/site-packages'):
    sys.path.append('venv/Lib/site-packages')

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QPushButton, QLabel, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QCursor

# Windows API常量
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOOLWINDOW = 0x00000080  # 工具窗口样式，不会在任务栏显示，也不会被Alt+Tab切换到

# 新增：SetWindowDisplayAffinity 常量，用于防止窗口被截图
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# 定义AI坐标监测常量
AI_COORDINATE_THRESHOLD = 500  # AI输出坐标与窗口的安全距离
WINDOW_MOVE_DISTANCE = 600  # 窗口移动距离，超过500像素

# 导入AI控制相关函数
import vl_model_test_doubao2
from vl_model_test_doubao2 import auto_control_computer, set_coordinate_callback

# 创建一个工作线程来运行AI控制逻辑
class AIWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    ai_coordinate = pyqtSignal(float, float)  # 发送AI输出的坐标信号，使用浮点数类型
    
    def __init__(self, user_content, parent=None):
        super().__init__(parent)
        self.user_content = user_content
        
    def run(self):
        try:
            # 设置坐标回调函数
            def coordinate_callback(coords):
                # 将坐标发送给主线程
                self.ai_coordinate.emit(coords[0], coords[1])
            
            set_coordinate_callback(coordinate_callback)
            
            # 获取时间字符串，年月日时分
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
            # 用户输入内容添加时间
            user_content2 = "当前时间为:"+time_str + "\n" + "用户任务为:"+self.user_content
            result = auto_control_computer(user_content2)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class AIWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ai_thread = None
        self.is_ai_controlling = False  # 标记是否由AI控制鼠标
        self.mouse_monitor_timer = None  # 鼠标监测定时器
        self.initUI()
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle('包豆电脑')
        self.setGeometry(100, 100, 500, 300)
        
        # 设置窗口标志：
        # - Qt.WindowStaysOnTopHint: 窗口始终在最顶层
        # - Qt.Window: 标准窗口样式
        # - Qt.WindowCloseButtonHint: 显示关闭按钮
        # - Qt.WindowMinimizeButtonHint: 显示最小化按钮
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window | 
                          Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # 设置窗口透明度，使其更加隐蔽
        self.setWindowOpacity(0.9)
        
        # 显示窗口
        self.show()
        
        # 获取窗口句柄
        hwnd = self.winId().__int__()
        
        # 使用Windows API设置窗口为分层窗口
        user32 = ctypes.windll.user32
        
        # 获取当前扩展样式
        current_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        
        # 设置新的扩展样式：添加WS_EX_LAYERED
        new_style = current_style | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        
        # 设置窗口为透明，但允许鼠标事件
        user32.SetLayeredWindowAttributes(hwnd, 0, int(255 * 0.9), 0x00000002)
        
        # 新增：使用SetWindowDisplayAffinity使窗口不被CV2等截图工具捕捉
        # 这是Windows 10版本1803及以上支持的功能
        try:
            user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            print("窗口已设置为不可被截图")
        except Exception as e:
            print(f"设置窗口不可被截图时出错: {e}")
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 创建标题标签
        title_label = QLabel('包豆电脑')
        title_label.setFont(QFont('Arial', 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # API密钥设置区域
        api_layout = QHBoxLayout()
        
        # API密钥输入框
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)  # 密码形式显示
        self.api_key_input.setPlaceholderText('请输入API密钥...')
        self.api_key_input.textChanged.connect(self.save_api_key)  # 文本变化时自动保存
        api_layout.addWidget(self.api_key_input)
        
        # 获取API密钥按钮
        self.get_api_key_btn = QPushButton('获取API密钥')
        self.get_api_key_btn.clicked.connect(self.open_api_key_url)
        api_layout.addWidget(self.get_api_key_btn)
        
        layout.addLayout(api_layout)
        
        # 创建输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText('请输入您的需求...')
        self.input_text.setFixedHeight(100)
        layout.addWidget(self.input_text)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建上传按钮
        self.upload_btn = QPushButton('上传并执行')
        self.upload_btn.clicked.connect(self.start_ai)
        button_layout.addWidget(self.upload_btn)
        
        # 创建停止按钮
        self.stop_btn = QPushButton('停止AI执行')
        self.stop_btn.clicked.connect(self.stop_ai)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # 创建状态标签
        self.status_label = QLabel('就绪')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 加载API密钥
        self.load_api_key()
        
        # 设置布局
        self.setLayout(layout)
        
    def open_api_key_url(self):
        """
        打开API密钥获取页面
        """
        import webbrowser
        webbrowser.open('https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey')
    
    def load_api_key(self):
        """
        从config.json加载API密钥
        """
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key = config.get('api_config', {}).get('api_key', '')
            self.api_key_input.setText(api_key)
        except Exception as e:
            print(f"加载API密钥失败: {e}")
    
    def save_api_key(self, text):
        """
        保存API密钥到config.json
        """
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 更新API密钥
            if 'api_config' not in config:
                config['api_config'] = {}
            config['api_config']['api_key'] = text
            
            # 保存到文件
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"保存API密钥失败: {e}")
    
    def start_ai(self):
        # 获取API密钥和用户输入
        api_key = self.api_key_input.text().strip()
        user_input = self.input_text.toPlainText().strip()
        
        # 检查是否都已填写
        if not api_key or not user_input:
            self.status_label.setText('请正确填入密钥和需求')
            return
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 获取时间字符串，年月日时分
        time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        # 用户输入内容添加时间
        user_content = "当前时间为:" + time_str + "\n" + "用户任务为:" + user_input
        
        # 更新状态
        self.status_label.setText('AI正在执行...')
        self.upload_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 隐藏API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(False)
        self.get_api_key_btn.setVisible(False)
        
        # 设置AI控制鼠标标志
        self.is_ai_controlling = True
        
        # 创建并启动AI线程
        self.ai_thread = AIWorker(user_content)
        self.ai_thread.finished.connect(self.ai_finished)
        self.ai_thread.error.connect(self.ai_error)
        self.ai_thread.start()
        
        # 连接AI坐标信号
        self.ai_thread.ai_coordinate.connect(self.handle_ai_coordinate)
        
    def stop_ai(self):
        # 设置全局变量，停止AI执行
        vl_model_test_doubao2.should_exit = True
        
        # 更新状态
        self.status_label.setText('正在停止AI...')
        
    def ai_finished(self, result):
        # AI执行完成
        self.status_label.setText('AI执行完成')
        self.upload_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 显示API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(True)
        self.get_api_key_btn.setVisible(True)
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 重置AI控制鼠标标志
        self.is_ai_controlling = False
        
    def ai_error(self, error):
        # AI执行出错
        self.status_label.setText('AI执行错误，可能密钥错误或欠费')
        self.upload_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # 显示API密钥输入框和获取密钥按钮
        self.api_key_input.setVisible(True)
        self.get_api_key_btn.setVisible(True)
        
        # 重置退出标志
        vl_model_test_doubao2.should_exit = False
        
        # 重置AI控制鼠标标志
        self.is_ai_controlling = False
        
    def handle_ai_coordinate(self, x, y):
        # 只有当AI控制鼠标时才处理
        if not self.is_ai_controlling:
            return
        
        print(f"收到AI输出的坐标: ({x}, {y})")
        
        # 获取窗口几何信息
        window_rect = self.geometry()
        
        # 计算AI输出坐标与窗口中心的距离
        window_center_x = window_rect.center().x()
        window_center_y = window_rect.center().y()
        print(f"窗口中心坐标：({window_center_x},{window_center_y})")
        
        distance = ((x - window_center_x) ** 2 + (y - window_center_y) ** 2) ** 0.5
        print(f"AI坐标与窗口中心的距离: {distance:.2f}像素")
        
        # 如果距离小于阈值，移动窗口
        if distance < AI_COORDINATE_THRESHOLD:
            # 创建QPoint对象表示AI坐标，将float转换为int
            ai_pos = QPoint(int(x), int(y))
            # 移动窗口避开AI坐标
            self.move_window_away(ai_pos, window_rect)
    
    def move_window_away(self, ai_pos, window_rect):
        # 计算窗口新位置，避开AI输出的坐标
        screen_geometry = QApplication.desktop().availableGeometry()
        
        # 窗口尺寸
        win_width = window_rect.width()
        win_height = window_rect.height()
        
        # AI坐标位置
        ai_x = ai_pos.x()
        ai_y = ai_pos.y()
        
        # 计算窗口中心位置
        win_center_x = window_rect.center().x()
        win_center_y = window_rect.center().y()
        
        # 确定移动方向：远离AI坐标
        new_x = win_center_x
        new_y = win_center_y
        
        # 水平方向移动
        if ai_x < win_center_x and (new_x + WINDOW_MOVE_DISTANCE) < screen_geometry.width():
            new_x += WINDOW_MOVE_DISTANCE
        else:
            new_x -= WINDOW_MOVE_DISTANCE
        
        # 垂直方向移动
        if ai_y < win_center_y and (new_y + WINDOW_MOVE_DISTANCE) < screen_geometry.height():
            new_y += WINDOW_MOVE_DISTANCE
        else:
            new_y -= WINDOW_MOVE_DISTANCE
        
        # 确保窗口不会移出屏幕
        new_x = max(0, min(new_x - win_width // 2, screen_geometry.width() - win_width))
        new_y = max(0, min(new_y - win_height // 2, screen_geometry.height() - win_height))
        
        print(f"窗口从 ({window_rect.left()}, {window_rect.top()}) 快速移动到 ({new_x}, {new_y})")
        # 快速移动窗口
        self.move(new_x, new_y)
    
    def closeEvent(self, event):
        # 关闭窗口时停止AI
        self.stop_ai()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AIWindow()
    sys.exit(app.exec_())

    # 打包命令： pyinstaller pyqt_main.spec