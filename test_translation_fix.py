#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试翻译功能修复
"""

import requests
import json
import time

def test_translation_api():
    """测试翻译API"""
    print("=== 测试翻译功能修复 ===")
    
    # 测试数据
    test_data = {
        "message": "原产地证书",
        "sourceLang": "zh", 
        "targetLang": "en"
    }
    
    try:
        # 发送翻译请求
        print(f"发送翻译请求: {test_data}")
        response = requests.post(
            "http://127.0.0.1:3005/api/query",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"翻译成功!")
            print(f"原文: {test_data['message']}")
            print(f"译文: {result.get('data', {}).get('content', '无结果')}")
            print(f"模型: {result.get('data', {}).get('model_used', '未知')}")
            return True
        else:
            print(f"翻译失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_chat_api():
    """测试对话API"""
    print("\n=== 测试对话功能 ===")
    
    test_data = {
        "message": "你好，请介绍一下海关的基本职能"
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:3005/api/chat",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=10
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"对话成功!")
            print(f"问题: {test_data['message']}")
            print(f"回答: {result.get('data', {}).get('content', '无结果')[:100]}...")
            return True
        else:
            print(f"对话失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 对话测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试...")
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 测试翻译功能
    translation_ok = test_translation_api()
    
    # 测试对话功能
    chat_ok = test_chat_api()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"翻译功能: {'✅ 正常' if translation_ok else '❌ 异常'}")
    print(f"对话功能: {'✅ 正常' if chat_ok else '❌ 异常'}")
    
    if translation_ok and chat_ok:
        print("🎉 所有功能测试通过！")
    else:
        print("⚠️ 部分功能存在问题，需要进一步排查") 