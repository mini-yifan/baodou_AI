import sys
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QTextCursor, QColor

class LogSignalHandler(QObject):
    """处理日志信号的类，确保在主线程中处理UI更新"""
    log_signal = pyqtSignal(str, str)  # 文本和日志类型
    
    def __init__(self, log_window):
        super().__init__()
        self.log_window = log_window
        # 连接信号到槽函数
        self.log_signal.connect(self.log_window.append_log)

class LogStream(io.StringIO):
    """自定义输出流，用于捕获print语句"""
    
    def __init__(self, signal_handler):
        super().__init__()
        self.signal_handler = signal_handler
        self.buffer = ""
    
    def write(self, text):
        """重写write方法，将文本发送到日志窗口"""
        super().write(text)
        
        # 缓冲文本，直到遇到换行符
        self.buffer += text
        if '\n' in self.buffer:
            # 分割缓冲区中的文本
            lines = self.buffer.split('\n')
            # 保留最后一行（可能不完整）
            self.buffer = lines[-1]
            
            # 发送完整的行到日志窗口
            for line in lines[:-1]:
                if line:  # 忽略空行
                    # 使用信号发送文本到主线程
                    try:
                        self.signal_handler.log_signal.emit(line + '\n', "normal")
                    except:
                        # 如果信号不可用，忽略错误
                        pass
    
    def flush(self):
        """重写flush方法"""
        # 如果缓冲区中有剩余文本，发送它
        if self.buffer:
            try:
                self.signal_handler.log_signal.emit(self.buffer, "normal")
                self.buffer = ""
            except:
                # 如果信号不可用，忽略错误
                pass

class LogWindow(QWidget):
    """日志窗口类，用于显示后台信息"""
    
    def __init__(self):
        super().__init__()
        
        # 创建信号处理器
        self.signal_handler = LogSignalHandler(self)
        
        # 保存原始的stdout和stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # 创建自定义输出流
        self.stdout_stream = LogStream(self.signal_handler)
        self.stderr_stream = LogStream(self.signal_handler)
        
        # 重定向stdout和stderr
        sys.stdout = self.stdout_stream
        sys.stderr = self.stderr_stream
        
        # 日志计数器，用于限制日志行数
        self.log_count = 0
        self.max_log_lines = 1000  # 最大日志行数
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle('后台日志')
        self.setGeometry(800, 100, 600, 400)
        
        # 设置窗口标志：始终在最顶层
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Window)
        
        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标题标签
        title_label = QLabel('后台执行日志')
        title_font = QFont('Microsoft YaHei', 14, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #1976d2;
                padding: 8px;
                margin-bottom: 5px;
                background-color: #e3f2fd;
                border-radius: 8px;
                font-weight: bold;
                border: 1px solid #bbdefb;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_font = QFont('Consolas', 10)
        self.log_text.setFont(log_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #263238;
                color: #eeffff;
                border: 1px solid #37474f;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        main_layout.addWidget(self.log_text)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        
        # 创建清空按钮
        self.clear_btn = QPushButton('清空日志')
        self.clear_btn.clicked.connect(self.clear_log)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        button_layout.addWidget(self.clear_btn)
        
        # 创建保存按钮
        self.save_btn = QPushButton('保存日志')
        self.save_btn.clicked.connect(self.save_log)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        # 添加弹簧，使按钮靠左对齐
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 设置布局
        self.setLayout(main_layout)
        
        # 设置窗口整体样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)
        
        # 添加初始欢迎信息
        self.append_log("=== 后台日志窗口已启动 ===\n", "info")
    
    def append_log(self, text, log_type="normal"):
        """添加日志到文本框"""
        # 根据日志类型设置颜色
        if log_type == "error":
            color = "#ff5252"  # 红色
        elif log_type == "warning":
            color = "#ff9800"  # 橙色
        elif log_type == "info":
            color = "#2196f3"  # 蓝色
        else:
            color = "#eeffff"  # 默认白色
        
        # 使用HTML格式设置文本颜色
        if log_type != "normal":
            text = f'<span style="color:{color}">{text}</span>'
        
        # 移动光标到末尾并插入文本
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 插入文本
        if log_type != "normal":
            self.log_text.insertHtml(text)
        else:
            self.log_text.insertPlainText(text)
        
        # 确保光标可见（滚动到底部）
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
        
        # 限制日志行数
        self.log_count += text.count('\n')
        if self.log_count > self.max_log_lines:
            # 删除前1/4的日志
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, self.max_log_lines // 4)
            cursor.removeSelectedText()
            self.log_count -= self.max_log_lines // 4
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.log_count = 0
        self.append_log("=== 日志已清空 ===\n", "info")
    
    def save_log(self):
        """保存日志到文件"""
        try:
            with open("baodou_log.txt", "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
            self.append_log("日志已保存到 baodou_log.txt\n", "info")
        except Exception as e:
            self.append_log(f"保存日志失败: {str(e)}\n", "error")
    
    def closeEvent(self, event):
        """关闭窗口时恢复原始输出流"""
        # 恢复原始输出流
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        event.accept()

# 全局日志窗口实例
log_window_instance = None

def get_log_window():
    """获取日志窗口实例"""
    global log_window_instance
    if log_window_instance is None:
        # 检查QApplication是否已经创建
        app = QApplication.instance()
        if app is None:
            return None
        
        log_window_instance = LogWindow()
    return log_window_instance

def init_log_window():
    """初始化日志窗口"""
    # 检查QApplication是否已经创建
    app = QApplication.instance()
    if app is None:
        return None
        
    log_window = get_log_window()
    if log_window:
        log_window.show()
    return log_window