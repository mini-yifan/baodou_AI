"""这个版本可以执行大部分的操作"""

import os
import base64
import cv2
import numpy as np
from openai import OpenAI
import json
import re
from cv_shot_doubao import mark_coordinate_on_image, capture_screen_and_save, map_coordinates
import time
import pyautogui
import pyperclip
import signal
from pydantic import BaseModel
import platform

# 全局退出标志
should_exit = False

# 全局回调函数，用于通知主窗口AI输出的坐标
coordinate_callback = None

current_os = platform.system()

# 尝试导入日志窗口模块
try:
    from log_window import get_log_window
    LOG_WINDOW_AVAILABLE = True
except ImportError:
    LOG_WINDOW_AVAILABLE = False

# 全局信号处理器实例
_signal_handler = None

def get_signal_handler():
    """获取全局信号处理器实例"""
    global _signal_handler
    if _signal_handler is None and LOG_WINDOW_AVAILABLE:
        try:
            log_window = get_log_window()
            if log_window:
                _signal_handler = log_window.signal_handler
        except:
            pass
    return _signal_handler

# 初始化日志窗口函数
def init_log_if_available():
    """如果日志窗口可用，则初始化它"""
    if LOG_WINDOW_AVAILABLE:
        try:
            log_window = get_log_window()
            return log_window
        except:
            return None
    return None

# 日志打印函数，确保日志能显示在日志窗口中
def log_print(*args, **kwargs):
    """自定义打印函数，仅使用原始print函数"""
    # 由于系统已经重定向了stdout/stderr，直接使用原始print函数即可
    # 不需要额外发送到日志窗口，否则会导致重复输出
    import builtins
    original_print = builtins.print
    original_print(*args, **kwargs)

# 设置坐标回调函数
def set_coordinate_callback(callback):
    global coordinate_callback
    coordinate_callback = callback

# 信号处理函数
def signal_handler(sig, frame):
    global should_exit
    log_print("\n收到中断信号，正在优雅退出...")
    should_exit = True

# 设置信号处理器
# 所有系统都支持SIGINT信号（Ctrl+C）
signal.signal(signal.SIGINT, signal_handler)

# 加载配置文件
def load_config(config_path="config.json"):
    """
    加载配置文件
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        log_print(f"成功加载配置文件: {config_path}")
        return config
    except Exception as e:
        log_print(f"加载配置文件失败: {e}")
        return None

# 加载配置
config = load_config()

# 设置默认值，防止配置文件加载失败
DEFAULT_CONFIG = {
    "api_config": {
        "api_key": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model_name": "doubao-seed-1-6-vision-250815"
    },
    "ai_config": {
        "enable_thinking": False,
        "thinking_type": "disabled",
        "vl_high_resolution_images": True
    },
    "execution_config": {
        "max_visual_model_iterations": 80,
        "default_max_iterations": 15
    },
    "screenshot_config": {
        "optimize_for_speed": True,
        "max_png": 1280,
        "input_path": "imgs/screen.png",
        "output_path": "imgs/screen_label.png"
    },
    "mouse_config": {
        "move_duration": 0.1,
        "failsafe": False
    }
}

# 使用配置文件或默认值
if config:
    API_CONFIG = config.get("api_config", DEFAULT_CONFIG["api_config"])
    AI_CONFIG = config.get("ai_config", DEFAULT_CONFIG["ai_config"])
    EXECUTION_CONFIG = config.get("execution_config", DEFAULT_CONFIG["execution_config"])
    SCREENSHOT_CONFIG = config.get("screenshot_config", DEFAULT_CONFIG["screenshot_config"])
    MOUSE_CONFIG = config.get("mouse_config", DEFAULT_CONFIG["mouse_config"])
else:
    API_CONFIG = DEFAULT_CONFIG["api_config"]
    AI_CONFIG = DEFAULT_CONFIG["ai_config"]
    EXECUTION_CONFIG = DEFAULT_CONFIG["execution_config"]
    SCREENSHOT_CONFIG = DEFAULT_CONFIG["screenshot_config"]
    MOUSE_CONFIG = DEFAULT_CONFIG["mouse_config"]

# 在文件开头导入后添加
pyautogui.FAILSAFE = MOUSE_CONFIG["failsafe"]  # 禁用安全机制

def read_local_image(image_path):
    """
    读取本地图片并转换为base64编码
    """
    try:
        # 使用cv2读取图片
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"无法读取图片: {image_path}")
        
        # 获取图片信息
        height, width, channels = img.shape
        log_print(f"成功读取图片: {image_path}")
        log_print(f"图片尺寸: {width} x {height} 像素")
        log_print(f"图片通道数: {channels}")
        
        # 将图片编码为base64
        _, buffer = cv2.imencode('.png', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 返回data URL格式的图片数据
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        log_print(f"读取图片时出错: {e}")
        return None

class MathResponse(BaseModel):
    current_status: str
    whether_completed: str
    element_info: str
    coordinates: list
    action: str
    type_information: str

# 读取本地图片
def get_next_element(user_content):
    # 重新加载配置文件，确保使用最新的API密钥
    global API_CONFIG, AI_CONFIG, EXECUTION_CONFIG, SCREENSHOT_CONFIG, MOUSE_CONFIG
    config = load_config()
    if config:
        API_CONFIG = config.get("api_config", DEFAULT_CONFIG["api_config"])
        AI_CONFIG = config.get("ai_config", DEFAULT_CONFIG["ai_config"])
        EXECUTION_CONFIG = config.get("execution_config", DEFAULT_CONFIG["execution_config"])
        SCREENSHOT_CONFIG = config.get("screenshot_config", DEFAULT_CONFIG["screenshot_config"])
        MOUSE_CONFIG = config.get("mouse_config", DEFAULT_CONFIG["mouse_config"])
    else:
        API_CONFIG = DEFAULT_CONFIG["api_config"]
        AI_CONFIG = DEFAULT_CONFIG["ai_config"]
        EXECUTION_CONFIG = DEFAULT_CONFIG["execution_config"]
        SCREENSHOT_CONFIG = DEFAULT_CONFIG["screenshot_config"]
        MOUSE_CONFIG = DEFAULT_CONFIG["mouse_config"]
    
    # 本地图片路径
    image_path = SCREENSHOT_CONFIG["input_path"]
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        log_print(f"错误：图片文件不存在 - {os.path.abspath(image_path)}")
        return
    
    # 读取并转换图片
    image_data_url = read_local_image(image_path)
    if not image_data_url:
        log_print("无法继续，图片读取失败")
        return
    
    # 尝试获取API Key
    api_key = API_CONFIG["api_key"]
    if not api_key:
        log_print("\n提示：配置文件中未设置API Key，跳过模型分析")
        log_print("图片已成功读取并转换，可以手动复制base64数据或保存结果")
        # 可以选择保存处理后的图片信息到文件
        return
    
    log_print("\n正在初始化OpenAI客户端并调用多模态模型分析图片...")
    
    client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=api_key,
    
    # 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text-generation/generation
    base_url=API_CONFIG["base_url"],
    )

    # 读取get_next_action_AI_doubao.txt文件
    if current_os == "Darwin":  # macOS
        with open("get_next_action_AI_doubao_mac.txt", "r", encoding="utf-8") as file:
            system_content = file.read().strip()
    else:
        with open("get_next_action_AI_doubao.txt", "r", encoding="utf-8") as file:
            system_content = file.read().strip()
    #log_print(f"系统内容：{system_content}")

    completion = client.beta.chat.completions.parse(
        model=API_CONFIG["model_name"],  # 此处以doubao-1-5-ui-tars-250428为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
        messages=[
            {"role": "system",
            "content": system_content},
            {"role": "user",
            "content": [{"type": "image_url",
                        "image_url": {"url": image_data_url},},
                        {"type": "text", "text": user_content}]}],
        #stream=True,
        # extra_body={'enable_thinking': False,
        #             "vl_high_resolution_images":True},
        # response_format={"type": "json_object"}
        response_format=MathResponse,
        extra_body={
        "thinking": {
            "type": AI_CONFIG["thinking_type"]  # 从配置文件获取深度思考设置
        },
    },
    )

    log_print(completion.choices[0].message.content)
    return completion.choices[0].message.content


# 一个解析json的函数
def parse_json(json_str):
    """
    解析AI输出的JSON字符串，能够处理格式不规范的情况
    例如：移除多余的大括号、处理代码块标记、从文本中提取JSON等
    """
    try:
        # 预处理：移除代码块标记
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        
        # 去除首尾空白字符
        json_str = json_str.strip()
        
        # 使用正则表达式匹配JSON内容
        # 这个正则表达式会匹配完整的JSON对象（包括嵌套结构）
        json_pattern = r'\{\s*"(?:[^"\\]|\\.)*"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+\.?\d*|true|false|null|\[.*?\]|\{.*?\})\s*(?:,\s*"(?:[^"\\]|\\.)*"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+\.?\d*|true|false|null|\[.*?\]|\{.*?\})\s*)*\}'
        
        # 查找所有匹配的JSON对象
        json_matches = re.findall(json_pattern, json_str, re.DOTALL)
        
        if json_matches:
            # 取最长的匹配项（最可能是完整的JSON）
            valid_json = max(json_matches, key=len)
            log_print(f"从AI输出中提取的JSON: {valid_json}")
            return json.loads(valid_json)
        else:
            # 如果正则匹配失败，尝试原始方法
            log_print("正则匹配JSON失败，尝试原始方法")
            # 找到第一个 '{' 和最后一个 '}'
            first_brace = json_str.find('{')
            last_brace = json_str.rfind('}')
            
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                # 提取有效的JSON部分
                valid_json = json_str[first_brace:last_brace + 1]
                log_print(f"提取的有效JSON: {valid_json}")
                return json.loads(valid_json)
            else:
                # 尝试直接解析原始字符串
                return json.loads(json_str)
            
    except json.JSONDecodeError as e:
        log_print(f"JSON解析错误: {e}")
        # 尝试更复杂的修复策略
        try:
            # 移除多余的大括号
            cleaned_str = re.sub(r'^\s*{\s*{\s*', '{', json_str)
            cleaned_str = re.sub(r'\s*}\s*}\s*$', '}', cleaned_str)
            log_print(f"清理后的JSON: {cleaned_str}")
            return json.loads(cleaned_str)
        except json.JSONDecodeError as e2:
            log_print(f"二次解析失败: {e2}")
            return None
    except Exception as e:
        log_print(f"解析过程中发生错误: {e}")
        return None

# 控制鼠标函数
def move_mouse_to_coordinates(coordinates, action, type_information, duration=MOUSE_CONFIG["move_duration"], scale=1):
    """
    将鼠标移动到指定坐标点并执行相应操作
    :param coordinates: 目标坐标，可以是单点[x, y]或拖拽坐标[[x1, y1], [x2, y2]]
    :param duration: 移动动画时间（秒），默认0.1秒
    """
    # 验证坐标有效性的辅助函数
    def validate_coordinate(coord):
        """确保坐标值在合理范围内"""
        # 正常屏幕坐标应该在0到数万之间，设置一个合理的范围限制
        if isinstance(coord, (int, float)):
            # 限制坐标在-100000到100000之间，防止极端异常值
            return max(-100000, min(100000, coord))
        return coord
    
    # 验证并修复坐标
    def fix_coordinates(coords):
        """修复坐标数据，确保其格式正确且值在合理范围内"""
        if isinstance(coords[0], list):
            # 拖拽坐标 [[x1, y1], [x2, y2]]
            return [
                [validate_coordinate(coords[0][0]), validate_coordinate(coords[0][1])],
                [validate_coordinate(coords[1][0]), validate_coordinate(coords[1][1])]
            ]
        else:
            # 单点坐标 [x, y]
            return [validate_coordinate(coords[0]), validate_coordinate(coords[1])]
    
    # 修复坐标
    coordinates = fix_coordinates(coordinates)
    # 先处理页面加载状态
    if action == "page_loading":
        log_print("检测到页面正在加载，暂停3秒...")
        action_str = "检测到页面正在加载，暂停3秒..."+"\n"
        time.sleep(0.5)
        log_print("暂停结束，继续操作")
        action_str = action_str + "暂停结束，继续操作"+"\n"
        return action_str, None
    
    # 获取图像实际宽高
    image_path = SCREENSHOT_CONFIG["input_path"]
    img = cv2.imread(image_path)
    if img is not None:
        img_height, img_width, _ = img.shape
    else:
        img_width = None
        img_height = None
    
    action_str = ""
    
    # 处理热键操作
    if action == "hotkey":
        if type_information:
            # 解析快捷键组合
            keys = type_information.split()
            
            # 根据操作系统处理快捷键
            current_os = platform.system()
            if current_os == "Darwin":  # macOS
                # 在macOS上将win键替换为command键
                keys = ["command" if key == "win" or key == "meta" else key for key in keys]
                keys = ["command" if key == "cmd" else key for key in keys]
            else:  # Windows和其他系统
                # 在Windows上将meta键替换为win键
                keys = ["win" if key == "meta" else key for key in keys]
            
            log_print(f"执行热键操作: {'+'.join(keys)}")
            pyautogui.hotkey(*keys)
            action_str = f"执行热键操作: {'+'.join(keys)}"+"\n"
        else:
            log_print("热键操作但未提供快捷键信息")
        return action_str, None
    
    # 处理拖拽操作
    if action == "drag" and isinstance(coordinates[0], list):
        # 获取起始和结束坐标
        start_x, start_y = coordinates[0]
        end_x, end_y = coordinates[1]
        
        # 映射坐标
        start_x, start_y = map_coordinates(start_x, start_y, scale, img_width, img_height)
        
        # 通知主窗口拖拽起点坐标（仅在坐标有效时）
        if coordinate_callback and 0 <= start_x <= 100000 and 0 <= start_y <= 100000:
            try:
                coordinate_callback((start_x, start_y))
            except Exception as e:
                log_print(f"调用坐标回调函数时出错: {e}")
        
        end_x, end_y = map_coordinates(end_x, end_y, scale, img_width, img_height)
        
        # 通知主窗口拖拽终点坐标（仅在坐标有效时）
        if coordinate_callback and 0 <= end_x <= 100000 and 0 <= end_y <= 100000:
            try:
                coordinate_callback((end_x, end_y))
            except Exception as e:
                log_print(f"调用坐标回调函数时出错: {e}")
        
        # 执行拖拽操作
        pyautogui.moveTo(start_x, start_y, duration=duration)
        log_print(f"鼠标已移动到拖拽起点: ({start_x}, {start_y})")
        action_str = f"鼠标已移动到拖拽起点: ({start_x}, {start_y})"+"\n"
        
        # 按下鼠标左键并拖动到终点
        pyautogui.dragTo(end_x, end_y, duration=duration*10)
        log_print(f"已完成拖拽操作: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        action_str = action_str + f"已完成拖拽操作: ({start_x}, {start_y}) -> ({end_x}, {end_y})"+"\n"
        
        # 保存映射后的坐标
        mapped_coordinates = [[start_x, start_y], [end_x, end_y]]
    else:
        # 处理单点操作
        x, y = coordinates
        
        # 映射坐标
        x, y = map_coordinates(x, y, scale, img_width, img_height)
        
        # 通知主窗口AI输出的坐标（仅在坐标有效时）
        if coordinate_callback and 0 <= x <= 100000 and 0 <= y <= 100000:
            try:
                coordinate_callback((x, y))
                log_print(f"已通知主窗口AI输出的坐标: ({x}, {y})")
            except Exception as e:
                log_print(f"调用坐标回调函数时出错: {e}")
        
        # 移动鼠标
        pyautogui.moveTo(x, y, duration=duration)
        log_print(f"鼠标已移动到坐标: ({x}, {y})")
        action_str = f"鼠标已移动到坐标: ({x}, {y})"+"\n"
        
        # 保存映射后的坐标
        mapped_coordinates = [x, y]
        
        # 执行相应操作
        if action == "click":
            pyautogui.click()
            log_print(f"已点击 ({x}, {y})")
            action_str = action_str + f"已点击 ({x}, {y})"+"\n"
        elif action == "double_click":
            pyautogui.doubleClick()
            log_print(f"已双击 ({x}, {y})")
            action_str = action_str + f"已双击 ({x}, {y})"+"\n" 
        elif action == "long_press":
            pyautogui.mouseDown()
            log_print(f"已长按 ({x}, {y})")
            action_str = action_str + f"已长按 ({x}, {y})"+"\n" 
        elif action == "right_click":
            pyautogui.rightClick()
            log_print(f"已右键点击 ({x}, {y})")
            action_str = action_str + f"已右键点击 ({x}, {y})"+"\n" 
        elif action == "scroll_up":
            pyautogui.scroll(500)
            log_print(f"已向上滚动 ({x}, {y})")
            action_str = action_str + f"已向上滚动 ({x}, {y})"+"\n" 
        elif action == "scroll_down":
            pyautogui.scroll(-500)
            log_print(f"已向下滚动 ({x}, {y})")
            action_str = action_str + f"已向下滚动 ({x}, {y})"+"\n" 
        else:
            log_print(f"未知操作: {action}")
    
    time.sleep(0.2)
    if type_information != "" and action != "hotkey":
        # 将type_information保存到剪切板
        pyperclip.copy(type_information)
        
        # 根据操作系统执行粘贴
        current_os = platform.system()
        time.sleep(0.1)
        if current_os == "Darwin":  # macOS
            # macOS上使用更可靠的粘贴方法
            # 先确保焦点在正确的输入框中
            time.sleep(0.2)
            # 使用keydown和keyup确保按键持续时间足够
            pyautogui.keyDown('command')
            time.sleep(0.1)
            pyautogui.press('v')
            time.sleep(0.1)
            pyautogui.keyUp('command')
        else:  # Windows和其他系统
            pyautogui.hotkey('ctrl', 'v')
        
        log_print(f"已粘贴: {type_information}")
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        log_print("已发送")
        action_str = action_str + f"已发送: {type_information}"+"\n" 
    # 将鼠标快速移动到屏幕的最左上角
    pyautogui.moveTo(0, 0, duration=duration)
    time.sleep(1.5)

    return action_str, mapped_coordinates

# 定义自动控制电脑的函数
def auto_control_computer(user_content, max_visual_model_iterations=EXECUTION_CONFIG["default_max_iterations"]):
    global should_exit
    before_output = []  # 将记忆改为列表，方便管理数量
    current_status = "未完成"
    # 创建一个收集报错信息的列表
    error_messages = []
    # 用于跟踪鼠标坐标的列表
    recent_coordinates = []
    # 连续相同坐标的次数
    same_coordinate_count = 0

    # 清空label文件夹中的所有标记图片
    label_dir = SCREENSHOT_CONFIG["output_path"]
    if os.path.exists(label_dir):
        # 删除所有以screen_label开头的png文件
        for filename in os.listdir(label_dir):
            if filename.startswith("screen_label") and filename.endswith(".png"):
                file_path = os.path.join(label_dir, filename)
                os.remove(file_path)
        log_print(f"已清空label文件夹: {label_dir}")

    # 视觉模型循环次数
    for i in range(max_visual_model_iterations):
        # 检查退出标志
        if should_exit:
            log_print("检测到退出标志，停止循环...")
            return "程序已被用户中断"
        log_print("\n")
        log_print(f"=================第 {i} 次循环===============")
        start_time = time.time()
        log_print("\n")
        if i == 0:
            before_output = []
            before_content = ""
        else:
            # 添加新的记录到列表
            before_output.append(str(next_element))
            # 保持最多保存10条记录
            if len(before_output) > 10:
                before_output.pop(0)  # 删除最旧的记录
            # 将列表连接成字符串
            before_output_str = "".join(before_output)
            before_content = "之前的AI输出操作为: "+before_output_str+"\n"+"之前已完成的操作为:"+action_str
        
        try:
            success, scale = capture_screen_and_save(
                save_path=SCREENSHOT_CONFIG["input_path"],
                optimize_for_speed=SCREENSHOT_CONFIG["optimize_for_speed"],
                max_png=SCREENSHOT_CONFIG["max_png"]
            )
            if not success:
                log_print("屏幕截图保存失败")
                continue
            log_print(f"屏幕截图已保存为 {os.path.basename(SCREENSHOT_CONFIG['input_path'])}")

            # is_page_loading_message = is_page_loading()
            # log_print(is_page_loading_message)

            next_element = get_next_element(before_content+"\n"+user_content)

            # 解析JSON响应
            if next_element:
                next_element = parse_json(next_element)
                current_status = next_element.get('current_status', '未知状态')
                whether_completed = next_element.get('whether_completed', 'difficult')
                element_info = next_element.get('element_info', '未知元素')
                coordinates = next_element.get('coordinates', [0, 0])
                action = next_element.get('action', '未知操作')
                type_information = next_element.get('type_information', '')

                if whether_completed == "True":
                    log_print(f"AI分析用时: {time.time() - start_time:.2f}秒")
                    return current_status
                    break
                elif whether_completed == "difficult":
                    log_print(f"AI分析用时: {time.time() - start_time:.2f}秒")
                    return current_status
                    break
                else:
                    pass
                
                log_print(f"AI分析用时: {time.time() - start_time:.2f}秒")
                log_print(f"下一步应该点击的元素: {element_info}")
                #location_str = get_location(element_info)
                
                # 检查坐标是否与之前相同
                # 使用值比较而不是引用比较
                coordinates_match = False
                for coord in recent_coordinates:
                    if coord[0] == coordinates[0] and coord[1] == coordinates[1]:
                        coordinates_match = True
                        break
                        
                if not coordinates_match:
                    recent_coordinates.append(coordinates.copy())  # 复制坐标列表
                    same_coordinate_count = 1
                    # 保持列表长度为3
                    if len(recent_coordinates) > 3:
                        recent_coordinates.pop(0)
                else:
                    same_coordinate_count += 1
                
                # 如果连续3次相同坐标，清空记忆
                if same_coordinate_count >= 3:
                    log_print("检测到连续3次相同坐标，清空记忆")
                    before_output = []  # 清空记忆列表
                    same_coordinate_count = 0
                    recent_coordinates = []
                    
                action_str, mapped_coordinates = move_mouse_to_coordinates(coordinates, action, type_information, scale=scale)
                # 标记坐标点
                if mapped_coordinates:
                    # 获取图像实际宽高
                    image_path = SCREENSHOT_CONFIG["input_path"]
                    img = cv2.imread(image_path)
                    if img is not None:
                        img_height, img_width = img.shape[:2]
                        
                        # 将实际屏幕坐标转换回图片上的坐标用于标记
                        if isinstance(mapped_coordinates[0], list):
                            # 拖拽坐标 [[x1, y1], [x2, y2]]
                            image_coordinates = []
                            for coord in mapped_coordinates:
                                # 应用缩放比例将实际坐标转换为图片坐标
                                img_x = int(coord[0] * scale)
                                img_y = int(coord[1] * scale)
                                image_coordinates.append([img_x, img_y])
                        else:
                            # 单点坐标 [x, y]
                            # 应用缩放比例将实际坐标转换为图片坐标
                            img_x = int(mapped_coordinates[0] * scale)
                            img_y = int(mapped_coordinates[1] * scale)
                            image_coordinates = [img_x, img_y]
                        
                        # 标记图片上的坐标
                        # 为每次循环生成不同的输出文件名
                        output_filename = f"screen_label{i+1}.png"
                        output_path = os.path.join(SCREENSHOT_CONFIG["output_path"], output_filename)
                        mark_coordinate_on_image(
                            image_coordinates,
                            input_path=SCREENSHOT_CONFIG["input_path"],
                            output_path=output_path
                        )
            else:
                log_print("错误：未收到模型响应")
        except Exception as e:
            # 收集报错信息
            error_messages.append(f"第 {i} 次循环发生错误: {e}")
            log_print(f"发生错误: {e}")
            # 抛出异常，让AIWorker的run方法捕获
            raise e

    return current_status


if __name__ == "__main__":
    log_print("=== 本地图片分析工具 ===")
    log_print("按 Ctrl+C 可以随时退出程序")
    
    # 如果需要继续其他功能，可以取消下面的注释
    user_content = input("请输入您的需求：")
    time.sleep(3)
    # 获取时间字符串，年月日时分
    time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    # 用户输入内容添加时间
    user_content = "当前时间为:"+time_str + "\n" + "用户任务为:"+user_content
    log_print("正在处理...")
    log_print(user_content)
    #time.sleep(5)
    current_time = time.time()

    auto_control_computer(user_content, max_visual_model_iterations=EXECUTION_CONFIG["max_visual_model_iterations"])
    log_print(f"处理时间: {time.time() - current_time} 秒")
    
    # 如果是用户中断，打印友好提示
    if should_exit:
        log_print("程序已成功退出")


