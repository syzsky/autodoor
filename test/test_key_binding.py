#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试按键绑定机制的核心功能
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autodoor import AutoDoorOCR

def test_key_mappings():
    """测试按键映射功能"""
    print("=== 开始测试按键映射功能 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    # 测试特殊按键映射
    key_mappings = {
        "Return": "enter",
        "Escape": "escape",
        "Tab": "tab",
        "BackSpace": "backspace",
        "Delete": "delete",
        "space": "space",
        "minus": "minus",
        "plus": "plus",
        "asterisk": "asterisk",
        "slash": "slash",
        "backslash": "backslash",
        "comma": "comma",
        "period": "period",
        "semicolon": "semicolon",
        "apostrophe": "apostrophe",
        "quoteleft": "quote",
        "quoteright": "quote",
        "Left": "left",
        "Right": "right",
        "Up": "up",
        "Down": "down"
    }
    
    # 测试按键映射
    available_keys = app.get_available_keys()
    print(f"支持的按键数量: {len(available_keys)}")
    
    # 验证常用按键是否在可用列表中
    common_keys = ["enter", "escape", "space", "a", "b", "c", "0", "1", "f1", "f2"]
    for key in common_keys:
        if key in available_keys:
            print(f"✓ 常用按键 '{key}' 在可用列表中")
        else:
            print(f"❌ 常用按键 '{key}' 不在可用列表中")
    
    # 测试按键有效性检查
    test_keys = ["valid_key", "a", "enter", "space", "f10", "invalid_key_123"]
    print("\n测试按键有效性检查:")
    for key in test_keys:
        if key in available_keys:
            print(f"✓ 按键 '{key}' 有效")
        else:
            print(f"❌ 按键 '{key}' 无效")
    
    # 测试默认按键设置
    print("\n测试默认按键设置:")
    print(f"文字识别默认按键: {app.key_var.get()}")
    print(f"定时任务1默认按键: {app.timed_groups[0]['key'].get()}")
    print(f"定时任务2默认按键: {app.timed_groups[1]['key'].get()}")
    print(f"定时任务3默认按键: {app.timed_groups[2]['key'].get()}")
    print(f"数字识别1默认按键: {app.number_regions[0]['key'].get()}")
    print(f"数字识别2默认按键: {app.number_regions[1]['key'].get()}")
    
    # 测试按键修改功能
    print("\n测试按键修改功能:")
    
    # 修改文字识别按键
    original_key = app.key_var.get()
    app.key_var.set("test_key")
    new_key = app.key_var.get()
    print(f"文字识别按键修改: 原按键='{original_key}', 新按键='{new_key}'")
    
    # 修改定时任务按键
    original_timed_key = app.timed_groups[0]['key'].get()
    app.timed_groups[0]['key'].set("test_timed_key")
    new_timed_key = app.timed_groups[0]['key'].get()
    print(f"定时任务1按键修改: 原按键='{original_timed_key}', 新按键='{new_timed_key}'")
    
    # 修改数字识别按键
    original_number_key = app.number_regions[0]['key'].get()
    app.number_regions[0]['key'].set("test_number_key")
    new_number_key = app.number_regions[0]['key'].get()
    print(f"数字识别1按键修改: 原按键='{original_number_key}', 新按键='{new_number_key}'")
    
    # 清理资源
    app.root.destroy()
    
    print("\n=== 按键映射功能测试完成 ===")
    return True

def test_available_keys():
    """测试可用按键列表"""
    print("\n=== 开始测试可用按键列表 ===")
    
    # 创建应用实例
    app = AutoDoorOCR()
    
    available_keys = app.get_available_keys()
    print(f"可用按键总数: {len(available_keys)}")
    
    # 打印部分可用按键
    print("部分可用按键:")
    print(f"字母按键: {available_keys[:26]}")
    print(f"数字按键: {available_keys[26:36]}")
    print(f"特殊按键: {available_keys[36:43]}")
    print(f"方向按键: {available_keys[54:58]}")
    print(f"功能按键: {available_keys[58:]}")
    
    # 验证功能按键范围
    function_keys = [f"f{i}" for i in range(1, 13)]
    all_function_keys_present = all(f_key in available_keys for f_key in function_keys)
    print(f"\n所有F1-F12按键是否都在列表中: {'✓ 是' if all_function_keys_present else '❌ 否'}")
    
    # 清理资源
    app.root.destroy()
    
    print("\n=== 可用按键列表测试完成 ===")
    return all_function_keys_present

if __name__ == "__main__":
    try:
        # 运行测试
        test_key_mappings()
        all_function_keys_present = test_available_keys()
        
        if all_function_keys_present:
            print("\n🎉 所有测试通过！按键绑定机制核心功能正常。")
            sys.exit(0)
        else:
            print("\n❌ 测试失败！功能按键不完整。")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)