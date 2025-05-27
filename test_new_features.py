#!/usr/bin/env python
# encoding: utf-8

"""
测试新功能：对话、专业名词解释、知识库检索
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.dashscope_service import translation_service

async def test_chat_functionality():
    """测试对话功能"""
    print("🔄 测试单轮对话功能...")
    
    if not translation_service or not translation_service.is_available:
        print("❌ DashScope服务不可用，跳过对话测试")
        return False
    
    try:
        # 测试单轮对话
        result = await translation_service.chat_single_turn("你好，请介绍一下海关的基本职能")
        
        if result.get('success'):
            print("✅ 单轮对话测试成功")
            print(f"回答: {result.get('response', '')[:100]}...")
            
            # 测试多轮对话
            session_id = result.get('session_id')
            if session_id:
                print("\n🔄 测试多轮对话功能...")
                result2 = await translation_service.chat_multi_turn(
                    "那么报关流程是怎样的？", 
                    session_id
                )
                
                if result2.get('success'):
                    print("✅ 多轮对话测试成功")
                    print(f"回答: {result2.get('response', '')[:100]}...")
                    return True
                else:
                    print(f"❌ 多轮对话测试失败: {result2.get('error')}")
                    return False
            else:
                print("⚠️ 未获取到会话ID，无法测试多轮对话")
                return True
        else:
            print(f"❌ 单轮对话测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 对话功能测试异常: {e}")
        return False

async def test_explanation_functionality():
    """测试专业名词解释功能"""
    print("\n🔄 测试专业名词解释功能...")
    
    if not translation_service or not translation_service.is_available:
        print("❌ DashScope服务不可用，跳过专业名词解释测试")
        return False
    
    try:
        # 测试专业名词解释
        result = await translation_service.explain_terminology("HS编码")
        
        if result.get('success'):
            print("✅ 专业名词解释测试成功")
            print(f"解释: {result.get('explanation', '')[:150]}...")
            return True
        else:
            print(f"❌ 专业名词解释测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 专业名词解释功能测试异常: {e}")
        return False

async def test_knowledge_base_functionality():
    """测试知识库检索功能"""
    print("\n🔄 测试知识库检索功能...")
    
    if not translation_service or not translation_service.is_available:
        print("❌ DashScope服务不可用，跳过知识库检索测试")
        return False
    
    try:
        # 测试知识库检索
        result = await translation_service.query_knowledge_base("如何办理进出口许可证？")
        
        if result.get('success'):
            print("✅ 知识库检索测试成功")
            print(f"结果: {result.get('response', '')[:150]}...")
            return True
        else:
            print(f"❌ 知识库检索测试失败: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ 知识库检索功能测试异常: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 开始测试新功能")
    print("=" * 50)
    
    # 检查DashScope服务状态
    if translation_service:
        print(f"📊 DashScope服务状态: {'可用' if translation_service.is_available else '不可用'}")
        print(f"📊 模型ID: {translation_service.app_id}")
        print(f"📊 模型名称: {translation_service.model_name}")
    else:
        print("❌ DashScope服务未初始化")
        return
    
    # 运行测试
    test_results = []
    
    # 测试对话功能
    chat_result = await test_chat_functionality()
    test_results.append(("对话功能", chat_result))
    
    # 测试专业名词解释功能
    explanation_result = await test_explanation_functionality()
    test_results.append(("专业名词解释", explanation_result))
    
    # 测试知识库检索功能
    knowledge_result = await test_knowledge_base_functionality()
    test_results.append(("知识库检索", knowledge_result))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📊 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有功能测试通过！新功能集成成功！")
    else:
        print("⚠️ 部分功能测试失败，请检查相关配置")

if __name__ == "__main__":
    asyncio.run(main()) 