#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置保存和加载功能测试脚本
用于验证所有设置项的持久化和恢复功能
"""

import os
import sys
import json
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autodoor import AutoDoorOCR

def test_config_persistence():
    """测试配置持久化功能"""
    print("=== 开始测试配置保存和加载功能 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    # 1. 保存默认配置
    print("1. 保存默认配置")
    app.save_config()
    
    # 2. 修改配置项
    print("2. 修改配置项")
    
    # 修改基本OCR配置
    app.ocr_interval_var.set(10)
    app.pause_duration_var.set(300)
    app.key_var.set("enter")
    app.language_var.set("chi_sim")
    
    # 修改关键词
    app.keywords_var.set("test1,test2,test3")
    
    # 修改点击模式和坐标
    app.click_mode_var.set("custom")
    app.x_coord_var.set(50)
    app.y_coord_var.set(100)
    
    # 修改定时任务配置
    app.timed_groups[0]["enabled"].set(True)
    app.timed_groups[0]["interval"].set(5)
    app.timed_groups[0]["key"].set("space")
    
    # 修改数字识别配置
    app.number_regions[0]["enabled"].set(True)
    app.number_regions[0]["threshold"].set(800)
    app.number_regions[0]["key"].set("f5")
    
    # 等待监听器触发保存
    time.sleep(1.5)
    
    # 3. 手动保存配置
    print("3. 手动保存配置")
    app.save_config()
    
    # 4. 验证配置文件存在
    print("4. 验证配置文件存在")
    if os.path.exists(app.config_file):
        print(f"✓ 配置文件已创建: {app.config_file}")
    else:
        print(f"✗ 配置文件未创建: {app.config_file}")
        return False
    
    # 5. 读取配置文件内容
    print("5. 读取配置文件内容")
    with open(app.config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print(f"   配置版本: {config.get('version')}")
    print(f"   保存时间: {config.get('last_save_time')}")
    
    # 6. 验证配置项是否正确保存
    print("6. 验证配置项是否正确保存")
    
    # 验证基本OCR配置
    ocr_config = config.get('ocr', {})
    assert ocr_config.get('interval') == 10, f"OCR间隔保存错误: {ocr_config.get('interval')}"
    assert ocr_config.get('pause_duration') == 300, f"暂停时长保存错误: {ocr_config.get('pause_duration')}"
    assert ocr_config.get('custom_key') == "enter", f"自定义按键保存错误: {ocr_config.get('custom_key')}"
    assert ocr_config.get('language') == "chi_sim", f"语言保存错误: {ocr_config.get('language')}"
    assert ocr_config.get('custom_keywords') == ["test1", "test2", "test3"], f"关键词保存错误: {ocr_config.get('custom_keywords')}"
    print("   ✓ 基本OCR配置保存正确")
    
    # 验证点击模式配置
    click_config = config.get('click', {})
    assert click_config.get('mode') == "custom", f"点击模式保存错误: {click_config.get('mode')}"
    assert click_config.get('x') == 50, f"X坐标保存错误: {click_config.get('x')}"
    assert click_config.get('y') == 100, f"Y坐标保存错误: {click_config.get('y')}"
    print("   ✓ 点击模式配置保存正确")
    
    # 验证定时任务配置
    timed_config = config.get('timed_key_press', {})
    timed_groups = timed_config.get('groups', [])
    assert len(timed_groups) >= 1, "定时任务组保存错误"
    assert timed_groups[0].get('enabled') == True, f"定时任务启用状态保存错误: {timed_groups[0].get('enabled')}"
    assert timed_groups[0].get('interval') == 5, f"定时任务间隔保存错误: {timed_groups[0].get('interval')}"
    assert timed_groups[0].get('key') == "space", f"定时任务按键保存错误: {timed_groups[0].get('key')}"
    print("   ✓ 定时任务配置保存正确")
    
    # 验证数字识别配置
    number_config = config.get('number_recognition', {})
    number_regions = number_config.get('regions', [])
    assert len(number_regions) >= 1, "数字识别区域保存错误"
    assert number_regions[0].get('enabled') == True, f"数字识别启用状态保存错误: {number_regions[0].get('enabled')}"
    assert number_regions[0].get('threshold') == 800, f"数字识别阈值保存错误: {number_regions[0].get('threshold')}"
    assert number_regions[0].get('key') == "f5", f"数字识别按键保存错误: {number_regions[0].get('key')}"
    print("   ✓ 数字识别配置保存正确")
    
    # 7. 创建新实例并加载配置
    print("7. 创建新实例并加载配置")
    app2 = AutoDoorOCR()
    config_loaded = app2.load_config()
    
    assert config_loaded == True, "配置加载失败"
    print("   ✓ 配置加载成功")
    
    # 8. 验证加载的配置是否正确
    print("8. 验证加载的配置是否正确")
    
    # 验证基本OCR配置
    assert app2.ocr_interval_var.get() == 10, f"OCR间隔加载错误: {app2.ocr_interval_var.get()}"
    assert app2.pause_duration_var.get() == 300, f"暂停时长加载错误: {app2.pause_duration_var.get()}"
    assert app2.key_var.get() == "enter", f"自定义按键加载错误: {app2.key_var.get()}"
    assert app2.language_var.get() == "chi_sim", f"语言加载错误: {app2.language_var.get()}"
    assert app2.keywords_var.get() == "test1,test2,test3", f"关键词加载错误: {app2.keywords_var.get()}"
    print("   ✓ 基本OCR配置加载正确")
    
    # 验证点击模式配置
    assert app2.click_mode_var.get() == "custom", f"点击模式加载错误: {app2.click_mode_var.get()}"
    assert app2.x_coord_var.get() == 50, f"X坐标加载错误: {app2.x_coord_var.get()}"
    assert app2.y_coord_var.get() == 100, f"Y坐标加载错误: {app2.y_coord_var.get()}"
    print("   ✓ 点击模式配置加载正确")
    
    # 验证定时任务配置
    assert app2.timed_groups[0]["enabled"].get() == True, f"定时任务启用状态加载错误: {app2.timed_groups[0]["enabled"].get()}"
    assert app2.timed_groups[0]["interval"].get() == 5, f"定时任务间隔加载错误: {app2.timed_groups[0]["interval"].get()}"
    assert app2.timed_groups[0]["key"].get() == "space", f"定时任务按键加载错误: {app2.timed_groups[0]["key"].get()}"
    print("   ✓ 定时任务配置加载正确")
    
    # 验证数字识别配置
    assert app2.number_regions[0]["enabled"].get() == True, f"数字识别启用状态加载错误: {app2.number_regions[0]["enabled"].get()}"
    assert app2.number_regions[0]["threshold"].get() == 800, f"数字识别阈值加载错误: {app2.number_regions[0]["threshold"].get()}"
    assert app2.number_regions[0]["key"].get() == "f5", f"数字识别按键加载错误: {app2.number_regions[0]["key"].get()}"
    print("   ✓ 数字识别配置加载正确")
    
    # 9. 清理资源
    print("9. 清理资源")
    app.root.destroy()
    app2.root.destroy()
    
    print("=== 配置保存和加载功能测试通过 ===")
    return True

def test_config_format():
    """测试配置文件格式"""
    print("\n=== 开始测试配置文件格式 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    # 保存配置
    app.save_config()
    
    # 读取配置文件
    with open(app.config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 验证配置文件结构
    expected_keys = ['version', 'last_save_time', 'ocr', 'tesseract', 'click', 'timed_key_press', 'number_recognition']
    for key in expected_keys:
        assert key in config, f"配置文件缺少必要字段: {key}"
    
    print(f"✓ 配置文件包含所有必要字段: {expected_keys}")
    
    # 验证各部分结构
    assert isinstance(config['ocr'], dict), "ocr配置应为字典类型"
    assert isinstance(config['tesseract'], dict), "tesseract配置应为字典类型"
    assert isinstance(config['click'], dict), "click配置应为字典类型"
    assert isinstance(config['timed_key_press'], dict), "timed_key_press配置应为字典类型"
    assert isinstance(config['number_recognition'], dict), "number_recognition配置应为字典类型"
    
    print("✓ 所有配置部分结构正确")
    
    # 验证版本号
    assert isinstance(config['version'], str), "version应为字符串类型"
    print(f"✓ 版本号格式正确: {config['version']}")
    
    # 验证时间戳
    assert isinstance(config['last_save_time'], str), "last_save_time应为字符串类型"
    print(f"✓ 时间戳格式正确: {config['last_save_time']}")
    
    # 清理资源
    app.root.destroy()
    
    print("=== 配置文件格式测试通过 ===")
    return True

if __name__ == "__main__":
    try:
        # 运行测试
        test_config_persistence()
        test_config_format()
        
        print("\n🎉 所有测试通过！配置保存和加载功能正常工作。")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)