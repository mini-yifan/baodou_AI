# -*- coding: utf-8 -*-
"""
Mac应用资源路径处理模块
提供Mac应用打包环境检测和资源路径获取功能
"""
import os
import re
import platform


def is_mac_app():
    """
    检测是否为Mac系统下的打包app状态
    
    Returns:
        bool: 如果是在Mac系统下打包的app中运行则返回True，否则返回False
    """
    # 检查操作系统
    current_os = platform.system()
    if current_os != "Darwin":
        return False
    
    # 检查是否在.app包内运行
    import sys
    executable_path = sys.executable
    if ".app/Contents/MacOS" in executable_path:
        return True
    
    # 检查当前工作目录是否在.app包内
    cwd = os.getcwd()
    if ".app/Contents" in cwd:
        return True
    
    return False


def get_app_resource_path():
    """
    获取app资源包路径
    
    Returns:
        str: 返回app资源包路径，如果不是在Mac app环境中运行则返回空字符串
    """
    if not is_mac_app():
        return ""
    
    # 尝试获取资源路径
    import sys
    
    # 方法1：通过sys.executable获取
    executable_path = sys.executable
    if ".app/Contents/MacOS" in executable_path:
        # 基础资源路径
        base_resource_path = executable_path.replace(".app/Contents/MacOS", ".app/Contents/Resources")
        
        # 直接检查config.json是否存在
        if os.path.exists(os.path.join(base_resource_path, "config.json")):
            return base_resource_path
        
        # 尝试多种可能的资源路径
        possible_paths = [
            base_resource_path,  # 标准路径: .app/Contents/Resources
            os.path.join(base_resource_path, os.path.basename(executable_path)),  # 带应用名: .app/Contents/Resources/app_name
            os.path.join(os.path.dirname(base_resource_path), "Resources")  # 备用路径
        ]
        
        # 检查哪个路径存在config.json
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "config.json")):
                return path
        
        # 如果都没找到config.json，返回基础路径
        return base_resource_path
    
    # 方法2：通过当前工作目录获取
    cwd = os.getcwd()
    if ".app/Contents" in cwd:
        app_match = re.search(r'(.+\.app)/Contents', cwd)
        if app_match:
            app_path = app_match.group(1)
            # 基础资源路径
            base_resource_path = os.path.join(app_path, "Contents", "Resources")
            
            # 直接检查config.json是否存在
            if os.path.exists(os.path.join(base_resource_path, "config.json")):
                return base_resource_path
            
            # 尝试多种可能的资源路径
            possible_paths = [
                base_resource_path,  # 标准路径: .app/Contents/Resources
                os.path.join(base_resource_path, os.path.basename(cwd)),  # 带应用名: .app/Contents/Resources/app_name
                os.path.join(os.path.dirname(base_resource_path), "Resources")  # 备用路径
            ]
            
            # 检查哪个路径存在config.json
            for path in possible_paths:
                if os.path.exists(os.path.join(path, "config.json")):
                    return path
            
            # 如果都没找到config.json，返回基础路径
            return base_resource_path
    
    return ""


def get_resource_file_path(relative_path):
    """
    获取资源文件的完整路径
    
    Args:
        relative_path (str): 相对于资源包的文件路径
        
    Returns:
        str: 在Mac app环境中返回资源包完整路径，否则返回原始路径
    """
    if not is_mac_app():
        return relative_path
    
    resource_path = get_app_resource_path()
    if resource_path:
        # 1. 优先检查直接在Resources目录下的文件
        resources_dir = resource_path if resource_path.endswith("Resources") else os.path.dirname(resource_path)
        direct_path = os.path.join(resources_dir, relative_path)
        
        # 添加调试信息
        # print(f"Mac App环境 - 资源路径: {resource_path}")
        # print(f"Mac App环境 - 尝试直接路径: {direct_path}")
        # print(f"Mac App环境 - 直接路径文件存在: {os.path.exists(direct_path)}")
        
        # 如果文件存在，直接返回
        if os.path.exists(direct_path):
            return direct_path
        
        # 2. 检查是否在Resources/baodou_AI目录下
        baodou_ai_path = os.path.join(resources_dir, "baodou_AI", relative_path)
        # print(f"Mac App环境 - 尝试baodou_AI路径: {baodou_ai_path}")
        # print(f"Mac App环境 - baodou_AI路径文件存在: {os.path.exists(baodou_ai_path)}")
        
        if os.path.exists(baodou_ai_path):
            return baodou_ai_path
        
        # 3. 尝试标准路径
        full_path = os.path.join(resource_path, relative_path)
        # print(f"Mac App环境 - 尝试标准路径: {full_path}")
        # print(f"Mac App环境 - 标准路径文件存在: {os.path.exists(full_path)}")
        
        if os.path.exists(full_path):
            return full_path
        
        # 4. 添加更详细的调试信息
        # print(f"Mac App环境 - Resources目录内容:")
        try:
            for item in os.listdir(resources_dir):
                item_path = os.path.join(resources_dir, item)
                # print(f"  - {item} (目录: {os.path.isdir(item_path)})")
                if os.path.isdir(item_path) and item == "baodou_AI":
                    # print(f"    baodou_AI目录内容:")
                    try:
                        for subitem in os.listdir(item_path):
                            # print(f"      - {subitem}")
                            pass
                    except Exception as e:
                        # print(f"      无法列出baodou_AI目录内容: {e}")
                        pass
        except Exception as e:
            # print(f"  无法列出Resources目录内容: {e}")
            pass
        
        # 5. 如果所有路径都无效，返回原始路径
        # print(f"Mac App环境 - 所有尝试路径均无效，返回原始路径: {relative_path}")
        return relative_path
    
    return relative_path


def get_default_imgs_path():
    """
    获取默认的imgs文件夹路径
    
    Returns:
        str: 在Mac app环境中返回资源包内的imgs路径，否则返回"imgs"
    """
    return get_resource_file_path("imgs")