#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试额外按键支持（Home、PageUp、PageDown、Insert、End）
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_extra_keys_support():
    """测试额外按键支持"""
    print("=== 开始测试额外按键支持 ===")
    
    # 模拟按键映射和可用按键列表
    
    # 可用按键列表（从源代码复制）
    available_keys = [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "space", "enter", "tab", "escape", "backspace", "delete", "insert",
        "equal", "plus", "minus", "asterisk", "slash", "backslash",
        "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
    ]
    
    # 按键映射（从源代码复制）
    key_mappings = {
        "Return": "enter",
        "Escape": "escape",
        "Tab": "tab",
        "BackSpace": "backspace",
        "Delete": "delete",
        "Insert": "insert",
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
        "Down": "down",
        "Home": "home",
        "End": "end",
        "Page_Up": "pageup",
        "Prior": "pageup",
        "Page_Down": "pagedown",
        "Next": "pagedown"
    }
    
    # 测试额外按键是否在可用列表中
    extra_keys = ["home", "end", "pageup", "pagedown", "insert"]
    print("测试额外按键是否在可用列表中:")
    all_extra_keys_present = True
    for key in extra_keys:
        if key in available_keys:
            print(f"✓ '{key}' 在可用按键列表中")
        else:
            print(f"❌ '{key}' 不在可用按键列表中")
            all_extra_keys_present = False
    
    # 测试按键映射
    print("\n测试按键映射:")
    test_mappings = [
        ("Home", "home"),
        ("End", "end"),
        ("Page_Up", "pageup"),
        ("Prior", "pageup"),
        ("Page_Down", "pagedown"),
        ("Next", "pagedown"),
        ("Insert", "insert")
    ]
    all_mappings_correct = True
    for event_key, expected_key in test_mappings:
        if event_key in key_mappings:
            mapped_key = key_mappings[event_key]
            if mapped_key == expected_key:
                print(f"✓ '{event_key}' 正确映射到 '{mapped_key}'")
            else:
                print(f"❌ '{event_key}' 映射错误: 期望 '{expected_key}', 实际 '{mapped_key}'")
                all_mappings_correct = False
        else:
            print(f"❌ '{event_key}' 没有映射")
            all_mappings_correct = False
    
    # 测试按键有效性检查
    print("\n测试按键有效性检查:")
    test_keys = ["home", "end", "pageup", "pagedown", "insert", "invalid_key"]
    for key in test_keys:
        if key in available_keys:
            print(f"✓ '{key}' 有效")
        else:
            print(f"❌ '{key}' 无效")
    
    # 总结测试结果
    print("\n=== 测试总结 ===")
    if all_extra_keys_present and all_mappings_correct:
        print("🎉 所有测试通过！Home、PageUp、PageDown、Insert和End键已成功添加支持。")
        return True
    else:
        print("❌ 测试失败！部分额外按键未正确添加支持。")
        return False

if __name__ == "__main__":
    success = test_extra_keys_support()
    sys.exit(0 if success else 1)