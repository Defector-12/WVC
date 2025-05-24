#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试DashScope API集成
验证海关翻译模型是否正常工作
"""

import os
import sys
import asyncio
from http import HTTPStatus

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入DashScope服务
from src.services.dashscope_service import DashScopeTranslationService

async def test_dashscope_service():
    """测试DashScope翻译服务"""
    print("=== 测试DashScope翻译服务 ===\n")
    
    # 创建服务实例
    service = DashScopeTranslationService()
    
    if not service.is_available:
        print("❌ DashScope服务不可用")
        return False
    
    print("✅ DashScope服务初始化成功\n")
    
    # 测试用例
    test_cases = [
        {
            "text": "原产地证书",
            "source": "zh",
            "target": "en",
            "description": "中文到英文 - 基础术语"
        },
        {
            "text": "Certificate of Origin",
            "source": "en", 
            "target": "zh",
            "description": "英文到中文 - 基础术语"
        },
        {
            "text": "海关申报单需要包含商品的HS编码、原产地证书和完税证明",
            "source": "zh",
            "target": "en",
            "description": "中文到英文 - 复杂句子"
        },
        {
            "text": "进出口货物报关单",
            "source": "zh",
            "target": "en",
            "description": "中文到英文 - 专业术语"
        }
    ]
    
    # 执行测试
    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['description']}")
        print(f"原文: {test_case['text']}")
        
        try:
            result = await service.translate_text(
                text=test_case['text'],
                source_lang=test_case['source'],
                target_lang=test_case['target']
            )
            
            if result['success']:
                print(f"翻译: {result['translation']}")
                print(f"模型: {result.get('model_used', 'Unknown')}")
                print("✅ 成功\n")
                success_count += 1
            else:
                print(f"❌ 失败: {result.get('error', '未知错误')}\n")
                
        except Exception as e:
            print(f"❌ 异常: {str(e)}\n")
    
    print(f"\n=== 测试结果: {success_count}/{len(test_cases)} 成功 ===")
    return success_count == len(test_cases)

def test_direct_api():
    """直接测试DashScope API（同步版本）"""
    print("\n=== 直接测试DashScope API ===\n")
    
    try:
        from dashscope import Application
        import os
        
        # 设置API Key
        api_key = "sk-fc310cd28bc74ff5be86913e3816f4d5"
        os.environ['DASHSCOPE_API_KEY'] = api_key
        
        # 测试调用
        response = Application.call(
            api_key=api_key,
            app_id='43f10f032fce4a52b8c40e3eb5a01c5d',
            prompt='请将"原产地证书"翻译成英文'
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == HTTPStatus.OK:
            print(f"✅ API调用成功!")
            print(f"翻译结果: {response.output.text}")
            return True
        else:
            print(f"❌ API调用失败:")
            print(f"错误信息: {response.message}")
            if hasattr(response, 'request_id'):
                print(f"请求ID: {response.request_id}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    # 先测试直接API调用
    direct_success = test_direct_api()
    
    # 再测试服务封装
    print("\n" + "="*50 + "\n")
    
    # 运行异步测试
    service_success = asyncio.run(test_dashscope_service())
    
    # 总结
    print("\n" + "="*50)
    print("=== 总体测试结果 ===")
    print(f"直接API测试: {'✅ 成功' if direct_success else '❌ 失败'}")
    print(f"服务封装测试: {'✅ 成功' if service_success else '❌ 失败'}") 