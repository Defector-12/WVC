#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试复杂翻译案例
"""

import requests
import json

def test_complex_translation():
    """测试复杂翻译案例"""
    url = "http://localhost:3005/api/query"
    
    # 用户提供的测试案例
    test_text = "However, for reasons of a proportionate response to the respective phytosanitary risk, it should be possible to establish the frequency rate of the identity checks and physical checks of the consignments of certain plants, plant products and other objects at a level lower than 100 %."
    
    print(f"=== 测试复杂英文翻译 ===")
    print(f"输入文本长度: {len(test_text)} 字符")
    print(f"输入: {test_text[:100]}...")
    
    data = {
        "type": "terminology",
        "message": test_text,
        "sourceLang": "en", 
        "targetLang": "zh"
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"翻译结果: {result['data']['content']}")
            print(f"说明: {result['data']['explanation']}")
            print(f"使用模型: {result['data']['model_used']}")
            if 'services_attempted' in result['data']:
                print(f"尝试的服务: {result['data']['services_attempted']}")
        else:
            print(f"错误: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")

    # 再测试简单案例
    print(f"\n=== 测试简单英文翻译 ===")
    simple_cases = ["hello", "world", "good"]
    
    for word in simple_cases:
        print(f"\n测试: '{word}'")
        data = {
            "type": "terminology",
            "message": word,
            "sourceLang": "en", 
            "targetLang": "zh"
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"  翻译结果: {result['data']['content']}")
                print(f"  使用模型: {result['data']['model_used']}")
                if 'services_attempted' in result['data']:
                    print(f"  尝试的服务: {result['data']['services_attempted']}")
            else:
                print(f"  错误: {response.text}")
        except Exception as e:
            print(f"  异常: {e}")

if __name__ == "__main__":
    test_complex_translation() 