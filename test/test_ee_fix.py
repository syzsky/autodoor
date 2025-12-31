#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本来验证修复错误识别"ee"问题
"""

import os
import sys
import time
from PIL import Image, ImageDraw, ImageFont

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autodoor import AutoDoorOCR

def create_test_image(text, size=(100, 30), noise_level=0):
    """创建测试图像，支持添加噪点"""
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
    
    # 添加噪点
    if noise_level > 0:
        import random
        pixels = image.load()
        for i in range(image.width):
            for j in range(image.height):
                if random.random() < noise_level:
                    pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    return image

def test_ee_recognition_fix():
    """测试修复错误识别"ee"问题"""
    print("=== 开始测试修复错误识别'ee'问题 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    # 测试用例
    test_cases = [
        # 正常情况
        ("2864/2864", 0, "正常X/Y格式"),
        ("123/456", 0, "正常X/Y格式"),
        ("5/6", 0, "短数字X/Y格式"),
        # 模拟可能导致"ee"识别的情况
        ("2864/2864", 0.1, "带10%噪点的X/Y格式"),
        ("2864/2864", 0.2, "带20%噪点的X/Y格式"),
        ("2864", 0, "纯数字格式"),
        ("", 0, "空字符串"),
        ("   ", 0, "只有空格"),
    ]
    
    for i, (test_text, noise_level, description) in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: '{test_text}' ({description}, 噪点: {noise_level*100}%)")
        
        # 创建测试图像
        image = create_test_image(test_text, noise_level=noise_level)
        
        # 保存测试图像以便查看
        test_image_path = f"test_ee_fix_{i+1}.png"
        image.save(test_image_path)
        print(f"创建测试图像: {test_image_path}")
        
        # 执行OCR识别
        ocr_result = app.ocr_number(image)
        print(f"OCR识别结果: '{ocr_result}'")
        
        # 解析数字
        parsed_number = app.parse_number(ocr_result)
        print(f"解析结果: {parsed_number}")
        
        # 检查是否识别出"ee"
        if "ee" in ocr_result.lower():
            print(f"❌ 仍识别出'ee'错误")
        else:
            print(f"✓ 未识别出'ee'错误")
        
        # 清理测试图像
        os.remove(test_image_path)
    
    # 测试可能导致"ee"的边缘情况
    print("\n=== 测试边缘情况 ===")
    
    # 创建一个可能被误识别为"ee"的图像
    # 例如，创建一个模糊的图像
    image = create_test_image("2864/2864")
    # 应用模糊效果
    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=2))
    test_image_path = "test_blurred.png"
    blurred_image.save(test_image_path)
    print(f"创建模糊测试图像: {test_image_path}")
    
    ocr_result = app.ocr_number(blurred_image)
    print(f"模糊图像OCR识别结果: '{ocr_result}'")
    
    if "ee" in ocr_result.lower():
        print(f"❌ 模糊图像仍识别出'ee'错误")
    else:
        print(f"✓ 模糊图像未识别出'ee'错误")
    
    # 清理测试图像
    os.remove(test_image_path)
    
    # 测试OCR配置是否只识别允许的字符
    print("\n=== 测试OCR字符白名单 ===")
    
    # 创建包含禁止字符的图像
    forbidden_chars_image = create_test_image("abc123/def456")
    test_image_path = "test_forbidden_chars.png"
    forbidden_chars_image.save(test_image_path)
    print(f"创建包含禁止字符的测试图像: {test_image_path}")
    
    ocr_result = app.ocr_number(forbidden_chars_image)
    print(f"OCR识别结果: '{ocr_result}'")
    
    # 检查是否只识别了数字和/
    allowed_chars = set("0123456789/")
    actual_chars = set(ocr_result)
    if actual_chars.issubset(allowed_chars):
        print(f"✓ OCR只识别了允许的字符")
    else:
        forbidden_chars_found = actual_chars - allowed_chars
        print(f"❌ OCR识别了禁止字符: {forbidden_chars_found}")
    
    # 清理测试图像
    os.remove(test_image_path)
    
    # 清理资源
    app.root.destroy()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    # 确保导入ImageFilter
    from PIL import ImageFilter
    test_ee_recognition_fix()