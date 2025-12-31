#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数字识别功能测试脚本
用于验证X/Y格式数字的识别和解析
"""

import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autodoor import AutoDoorOCR

def create_test_image(text, size=(100, 30)):
    """创建测试图像"""
    # 创建白色背景图像
    image = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(image)
    
    # 尝试使用不同的字体
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype('arial.ttf', 20)
    except IOError:
        # 如果系统字体不可用，使用默认字体
        font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # 绘制文字（黑色）
    draw.text((x, y), text, fill='black', font=font)
    
    return image

def test_xy_format_recognition():
    """测试X/Y格式数字识别"""
    print("=== 开始测试X/Y格式数字识别 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    # 测试用例
    test_cases = [
        "123/456",
        "789/1011",
        " 2864 / 2864 ",  # 带空格的情况
        "5/6",
        "1234/5678",
        "28642864"  # 非X/Y格式
    ]
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: '{test_text}'")
        
        # 创建测试图像
        image = create_test_image(test_text)
        
        # 保存测试图像以便查看
        test_image_path = f"test_image_{i+1}.png"
        image.save(test_image_path)
        print(f"创建测试图像: {test_image_path}")
        
        # 执行OCR识别
        ocr_result = app.ocr_number(image)
        print(f"OCR识别结果: '{ocr_result}'")
        
        # 解析数字
        parsed_number = app.parse_number(ocr_result)
        print(f"解析结果: {parsed_number}")
        
        # 清理测试图像
        os.remove(test_image_path)
    
    # 测试实际的数字识别循环
    print("\n=== 测试数字识别循环 ===")
    
    # 创建一个模拟的区域
    mock_region = (0, 0, 100, 30)
    
    # 创建一个X/Y格式的测试图像
    test_image = create_test_image("2864/2864")
    test_image.save("test_xy_format.png")
    
    # 模拟截图函数
    def mock_take_screenshot(region):
        return Image.open("test_xy_format.png")
    
    # 保存原始的take_screenshot方法
    original_take_screenshot = app.take_screenshot
    
    try:
        # 替换为模拟方法
        app.take_screenshot = mock_take_screenshot
        
        # 执行一次数字识别循环（简化版）
        print("执行数字识别循环...")
        screenshot = app.take_screenshot(mock_region)
        text = app.ocr_number(screenshot)
        print(f"OCR识别结果: '{text}'")
        number = app.parse_number(text)
        print(f"解析结果: {number}")
        
        if number is not None:
            print(f"✓ 成功识别并解析X/Y格式数字")
        else:
            print(f"✗ 无法识别X/Y格式数字")
            
    finally:
        # 恢复原始方法
        app.take_screenshot = original_take_screenshot
        # 清理测试图像
        os.remove("test_xy_format.png")
    
    # 清理资源
    app.root.destroy()
    
    print("\n=== 数字识别功能测试完成 ===")

if __name__ == "__main__":
    test_xy_format_recognition()