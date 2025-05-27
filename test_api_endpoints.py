#!/usr/bin/env python
# encoding: utf-8

"""
API端点测试脚本
测试所有新添加的API功能：翻译、对话、专业名词解释、知识库检索
"""

import requests
import json
import time

BASE_URL = "http://localhost:3005"

def test_translation_api():
    """测试翻译API"""
    print("🔄 测试翻译API...")
    
    url = f"{BASE_URL}/api/query"
    data = {
        "type": "terminology",
        "message": "hello",
        "sourceLang": "en",
        "targetLang": "zh"
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 翻译API测试成功")
                print(f"翻译结果: {result['data']['content']}")
                return True
            else:
                print(f"❌ 翻译API返回错误: {result.get('message')}")
                return False
        else:
            print(f"❌ 翻译API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 翻译API测试异常: {e}")
        return False

def test_chat_api():
    """测试对话API"""
    print("\n🔄 测试对话API...")
    
    url = f"{BASE_URL}/api/chat"
    
    # 测试单轮对话
    data = {
        "message": "你好，请介绍一下海关的基本职能",
        "session_id": None,
        "context": None
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 单轮对话API测试成功")
                print(f"回答: {result['data']['content'][:100]}...")
                
                # 测试多轮对话
                session_id = result['data'].get('session_id')
                if session_id:
                    print("\n🔄 测试多轮对话...")
                    data2 = {
                        "message": "那么报关流程是怎样的？",
                        "session_id": session_id,
                        "context": None
                    }
                    
                    response2 = requests.post(url, json=data2, timeout=30)
                    if response2.status_code == 200:
                        result2 = response2.json()
                        if result2.get('code') == 0:
                            print("✅ 多轮对话API测试成功")
                            print(f"回答: {result2['data']['content'][:100]}...")
                            return True
                        else:
                            print(f"❌ 多轮对话API返回错误: {result2.get('message')}")
                            return False
                    else:
                        print(f"❌ 多轮对话API请求失败: {response2.status_code}")
                        return False
                else:
                    print("⚠️ 未获取到会话ID，但单轮对话成功")
                    return True
            else:
                print(f"❌ 对话API返回错误: {result.get('message')}")
                return False
        else:
            print(f"❌ 对话API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 对话API测试异常: {e}")
        return False

def test_explain_api():
    """测试专业名词解释API"""
    print("\n🔄 测试专业名词解释API...")
    
    url = f"{BASE_URL}/api/explain"
    data = {
        "term": "HS编码",
        "context": None
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 专业名词解释API测试成功")
                print(f"解释: {result['data']['content'][:150]}...")
                return True
            else:
                print(f"❌ 专业名词解释API返回错误: {result.get('message')}")
                return False
        else:
            print(f"❌ 专业名词解释API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 专业名词解释API测试异常: {e}")
        return False

def test_knowledge_api():
    """测试知识库检索API"""
    print("\n🔄 测试知识库检索API...")
    
    url = f"{BASE_URL}/api/knowledge"
    data = {
        "query": "如何办理进出口许可证？",
        "pipeline_ids": None
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print("✅ 知识库检索API测试成功")
                print(f"结果: {result['data']['content'][:150]}...")
                return True
            else:
                print(f"❌ 知识库检索API返回错误: {result.get('message')}")
                return False
        else:
            print(f"❌ 知识库检索API请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 知识库检索API测试异常: {e}")
        return False

def test_server_status():
    """测试服务器状态"""
    print("🔄 测试服务器状态...")
    
    url = f"{BASE_URL}/api/test"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print("✅ 服务器状态正常")
            print(f"状态: {result.get('status')}")
            print(f"消息: {result.get('message')}")
            return True
        else:
            print(f"❌ 服务器状态检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器状态检查异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🚀 开始API端点测试")
    print("=" * 60)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    time.sleep(2)
    
    # 运行测试
    test_results = []
    
    # 测试服务器状态
    server_result = test_server_status()
    test_results.append(("服务器状态", server_result))
    
    if not server_result:
        print("❌ 服务器未启动，无法进行API测试")
        return
    
    # 测试翻译API
    translation_result = test_translation_api()
    test_results.append(("翻译API", translation_result))
    
    # 测试对话API
    chat_result = test_chat_api()
    test_results.append(("对话API", chat_result))
    
    # 测试专业名词解释API
    explain_result = test_explain_api()
    test_results.append(("专业名词解释API", explain_result))
    
    # 测试知识库检索API
    knowledge_result = test_knowledge_api()
    test_results.append(("知识库检索API", knowledge_result))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📋 API测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 项API测试通过")
    
    if passed == total:
        print("🎉 所有API测试通过！系统功能完整！")
    else:
        print("⚠️ 部分API测试失败，请检查相关配置")
    
    print("\n💡 提示：")
    print("- 翻译功能：支持中英文互译")
    print("- 对话功能：支持单轮和多轮对话")
    print("- 专业名词解释：提供详细的海关术语解释")
    print("- 知识库检索：基于海关知识库的专业问答")

if __name__ == "__main__":
    main() 