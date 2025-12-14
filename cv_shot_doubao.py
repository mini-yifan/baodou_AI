import cv2
import numpy as np
import pyautogui
import os
import time

def capture_screen_and_save(save_path="imgs/screen.png", optimize_for_speed=True, max_png=1280):
    """
    使用OpenCV实现自动截屏并保存到指定路径
    
    参数:
        save_path: 保存路径，默认为"imgs/screen.png"
        optimize_for_speed: 是否优化速度（减少日志和使用更快的保存参数）
        max_png: 图片最大尺寸限制
    """
    # 创建输出目录（如果不存在）
    output_dir = os.path.dirname(save_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        if not optimize_for_speed:
            print(f"创建文件夹: {output_dir}")
    
    try:
        if not optimize_for_speed:
            print("正在执行截屏...")
            start_time = time.time()
        
        # 使用pyautogui进行截屏
        screenshot = pyautogui.screenshot()
        
        # 转换PIL图像为OpenCV格式（BGR）
        screenshot_np = np.array(screenshot)
        screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        scale = 1
        if optimize_for_speed:
            # # 将图片等比例缩小一半
            # screenshot_bgr = cv2.resize(screenshot_bgr, None, fx=0.5, fy=0.5)
            # 若图片的最长边大于max_png,则将最长边缩小为max_png,其他边等比缩小
            height, width, _ = screenshot_bgr.shape
            max_edge = max(height, width)
            if max_edge > max_png:
                scale = max_png / max_edge
                screenshot_bgr = cv2.resize(screenshot_bgr, None, fx=scale, fy=scale)
            
        # 使用更快的保存参数
        save_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 1] if optimize_for_speed else []
        success = cv2.imwrite(save_path, screenshot_bgr, save_params)
        
        if success and not optimize_for_speed:
            # 获取文件信息
            file_size = os.path.getsize(save_path) / 1024  # KB
            img_height, img_width, _ = screenshot_bgr.shape
            
            print(f"截屏成功！")
            print(f"保存路径: {os.path.abspath(save_path)}")
            print(f"图像尺寸: {img_width} x {img_height} 像素")
            print(f"文件大小: {file_size:.2f} KB")
            print(f"处理耗时: {(time.time() - start_time):.2f} 秒")
        elif not success:
            print("保存图像失败")
            
        return success, scale

    except Exception as e:
        print(f"截屏过程中发生错误: {e}")
        return False, scale

def mark_coordinate_on_image(coordinates, input_path="imgs/screen.png", output_path="imgs/screen_label.png", point_radius=10, point_color=(0, 0, 255), thickness=-1):
    """
    在图片上标记指定坐标点
    
    参数:
        coordinates: tuple或list，坐标点(x, y)或两个坐标点[[x1, y1], [x2, y2]]
        input_path: 输入图片路径
        output_path: 输出图片路径
        point_radius: 标记点的半径
        point_color: 标记点的颜色，使用BGR格式，默认为红色(0, 0, 255)
        thickness: 线条粗细，-1表示填充
    
    返回:
        bool: 标记成功返回True，失败返回False
    """
    try:
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            return False
        
        # 读取图片
        image = cv2.imread(input_path)
        if image is None:
            return False
        
        # 获取图片尺寸
        img_height, img_width = image.shape[:2]
        
        # 处理坐标点
        points_to_mark = []
        
        if isinstance(coordinates[0], list) or isinstance(coordinates[0], tuple):
            # 两个坐标点 [[x1, y1], [x2, y2]]
            for coord in coordinates:
                if isinstance(coord, (list, tuple)) and len(coord) == 2:
                    x, y = int(coord[0]), int(coord[1])
                    # 检查坐标是否在图片范围内
                    if 0 <= x < img_width and 0 <= y < img_height:
                        points_to_mark.append((x, y))
        else:
            # 单点坐标 [x, y]
            if len(coordinates) == 2:
                x, y = int(coordinates[0]), int(coordinates[1])
                # 检查坐标是否在图片范围内
                if 0 <= x < img_width and 0 <= y < img_height:
                    points_to_mark.append((x, y))
        
        if not points_to_mark:
            return False
        
        # 在图片上标记所有有效坐标点
        for i, (x, y) in enumerate(points_to_mark):
            # 在图片上画圆标记点
            cv2.circle(image, (x, y), point_radius, point_color, thickness)
            
            # 添加坐标文本
            if len(points_to_mark) == 1:
                text = f"({x}, {y})"
            else:
                text = f"P{i+1} ({x}, {y})"
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            font_color = (0, 0, 255)
            font_thickness = 2
            
            # 文本位置在点的上方一点，对于多个点，错开一点位置
            offset = i * 40
            text_position = (x - 30 + offset, y - 20)
            cv2.putText(image, text, text_position, font, font_scale, font_color, font_thickness)
        
        # 创建输出目录（如果不存在）
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存标记后的图片，使用低压缩级别加快保存速度
        save_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 1]
        success = cv2.imwrite(output_path, image, save_params)
        
        return success
            
    except Exception as e:
        # 静默处理错误以提高速度
        return False

# 坐标映射
def map_coordinates(x, y, scale, img_width=None, img_height=None):
    """
    将坐标映射到实际屏幕上
    
    参数:
        x: 输入的x坐标（相对坐标，归一化至1000）
        y: 输入的y坐标（相对坐标，归一化至1000）
        scale: 图像缩放比例
        img_width: 图像实际宽度
        img_height: 图像实际高度
    
    返回:
        tuple: 实际屏幕上的坐标
    """
    # 确保坐标值在合理范围内
    x = max(-100000, min(100000, x))
    y = max(-100000, min(100000, y))
    
    # 如果提供了图像宽高，使用相对坐标到绝对坐标的转换公式
    if img_width and img_height:
        # 将相对坐标转换为绝对坐标
        x_abs = (x / 1000) * img_width
        y_abs = (y / 1000) * img_height
    else:
        # 保持原有逻辑，直接除以缩放比例
        x_abs = x
        y_abs = y
    
    # 应用缩放比例映射到实际屏幕
    x_r = x_abs / scale
    y_r = y_abs / scale
    
    # 确保最终坐标在有效范围内
    x_r = max(0, min(100000, x_r))
    y_r = max(0, min(100000, y_r))
    
    return x_r, y_r


def main():
    """
    主函数，执行截屏操作和坐标标记测试
    """
    print("=== OpenCV 截屏工具 ===")
    
    # 执行截屏
    capture_screen_and_save()
    
    # # 测试坐标标记功能
    # print("\n=== 测试坐标标记功能 ===")
    # # 使用示例坐标 (837, 877) - 这是之前vl_model_test.py中识别出的AI输入框位置
    # test_coordinates = (837, 877)
    # print(f"将在图片上标记坐标: {test_coordinates}")
    
    # # 调用坐标标记函数
    # success = mark_coordinate_on_image(test_coordinates)
    
    # if success:
    #     print("坐标标记测试成功完成！")
    # else:
    #     print("坐标标记测试失败，请检查错误信息")

if __name__ == "__main__":
    time.sleep(5)
    main()