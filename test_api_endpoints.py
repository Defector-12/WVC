#!/usr/bin/env python
# encoding: utf-8

"""
测试Web服务API端点功能
特别关注翻译API的输出格式修复
"""

import requests
import json
import time
import logging
import argparse
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 服务器URL
DEFAULT_SERVER_URL = "http://127.0.0.1:3005"

def test_translation_api(server_url, test_text=None):
    """测试翻译API是否能正确处理翻译并从工作流中提取最终译文"""
    logger.info("=== 测试翻译API与工作流格式 ===")
    
    if test_text is None:
        # 默认测试文本
        test_text = """In order to increase clarity for the economic operators in respect of the customs treatment of goods entering the
customs territory of the Union, rules should be defined for situations where the presumption of the customs status of Union goods
does not apply."""
    
    # 测试数据
    test_data = {
        "message": test_text,
        "sourceLang": "en", 
        "targetLang": "zh"
    }
    
    try:
        # 发送翻译请求
        logger.info(f"发送翻译请求...")
        logger.info(f"原文: {test_text[:100]}...")
        response = requests.post(
            f"{server_url}/api/query",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30  # 增加超时时间，翻译可能需要较长时间
        )
        
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('code') == 0:
                # 获取翻译结果
                translation = result.get('data', {}).get('content', '')
                model_used = result.get('data', {}).get('model_used', '未知')
                explanation = result.get('data', {}).get('explanation', '')
                
                logger.info(f"翻译成功!")
                logger.info(f"使用模型: {model_used}")
                logger.info(f"解释: {explanation}")
                logger.info(f"译文: {translation}")
                
                # 获取工作流源API作为可选测试
                try:
                    logger.info("测试工作流源API...")
                    sources_response = requests.post(
                        f"{server_url}/api/show_last_answer_sources",
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if sources_response.status_code == 200:
                        sources_result = sources_response.json()
                        if sources_result.get('code') == 0:
                            formatted_sources = sources_result.get('data', {}).get('formatted_sources', '')
                            logger.info("工作流源获取成功!")
                            logger.info(f"工作流源 (部分): {formatted_sources[:200]}...")
                        else:
                            logger.warning(f"工作流源获取失败: {sources_result.get('message', '未知错误')}")
                    else:
                        logger.warning(f"工作流源API响应异常: {sources_response.status_code}")
                except Exception as e:
                    logger.warning(f"工作流源API调用失败 (这不影响翻译测试): {e}")
                
                # 翻译测试成功
                return True, "翻译API测试成功"
            else:
                logger.error(f"翻译请求失败: {result.get('message', '未知错误')}")
                return False, f"翻译请求失败: {result.get('message', '未知错误')}"
        else:
            logger.error(f"翻译API响应异常: {response.status_code}")
            try:
                error_message = response.json().get('message', '未知错误')
            except:
                error_message = response.text
            return False, f"翻译API响应异常: {response.status_code}, 错误: {error_message}"
            
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到服务器 {server_url}，请确保服务器正在运行")
        return False, f"无法连接到服务器 {server_url}"
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False, f"测试过程中发生错误: {str(e)}"

def test_chat_api(server_url):
    """测试对话API"""
    logger.info("\n=== 测试对话API ===")
    
    test_data = {
        "message": "你好，请介绍一下海关的基本职能"
    }
    
    try:
        response = requests.post(
            f"{server_url}/api/chat",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=15
        )
        
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                logger.info(f"对话成功!")
                logger.info(f"问题: {test_data['message']}")
                logger.info(f"回答 (部分): {result.get('data', {}).get('content', '无结果')[:200]}...")
                return True, "对话API测试成功"
            else:
                logger.error(f"对话请求失败: {result.get('message', '未知错误')}")
                return False, f"对话请求失败: {result.get('message', '未知错误')}"
        else:
            logger.error(f"对话API响应异常: {response.status_code}")
            try:
                error_message = response.json().get('message', '未知错误')
            except:
                error_message = response.text
            return False, f"对话API响应异常: {response.status_code}, 错误: {error_message}"
            
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到服务器 {server_url}，请确保服务器正在运行")
        return False, f"无法连接到服务器 {server_url}"
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
        return False, f"测试过程中发生错误: {str(e)}"

def test_server_health(server_url):
    """测试服务器健康状态"""
    logger.info("=== 测试服务器健康状态 ===")
    
    try:
        response = requests.get(
            f"{server_url}/api/test",
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"服务器健康检查成功! 状态码: {response.status_code}")
            try:
                result = response.json()
                logger.info(f"服务器响应: {result}")
            except:
                logger.info(f"服务器响应: {response.text}")
            return True, "服务器健康"
        else:
            logger.warning(f"服务器健康检查返回非200状态码: {response.status_code}")
            return False, f"服务器返回非200状态码: {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到服务器 {server_url}，请确保服务器正在运行")
        return False, f"无法连接到服务器 {server_url}"
    except Exception as e:
        logger.error(f"健康检查过程中发生错误: {e}")
        return False, f"健康检查错误: {str(e)}"

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试Web服务API端点功能')
    parser.add_argument('--url', type=str, default=DEFAULT_SERVER_URL,
                        help=f'服务器URL (默认: {DEFAULT_SERVER_URL})')
    parser.add_argument('--wait', type=int, default=2,
                        help='等待服务器启动的秒数 (默认: 2)')
    parser.add_argument('--test', type=str, choices=['all', 'health', 'translation', 'chat'],
                        default='all', help='指定要运行的测试 (默认: all)')
    
    args = parser.parse_args()
    
    # 等待服务器启动
    if args.wait > 0:
        logger.info(f"等待服务器启动... ({args.wait}秒)")
        time.sleep(args.wait)
    
    # 记录测试结果
    test_results = {}
    
    # 测试服务器健康状态
    if args.test in ['all', 'health']:
        health_ok, health_msg = test_server_health(args.url)
        test_results['health'] = (health_ok, health_msg)
        
        # 如果健康检查失败，可能没必要继续其他测试
        if not health_ok and args.test == 'all':
            logger.warning("服务器健康检查失败，跳过其他测试")
            
    # 测试翻译功能
    if args.test in ['all', 'translation'] and (args.test != 'all' or test_results.get('health', (True, ''))[0]):
        translation_ok, translation_msg = test_translation_api(args.url)
        test_results['translation'] = (translation_ok, translation_msg)
    
    # 测试对话功能
    if args.test in ['all', 'chat'] and (args.test != 'all' or test_results.get('health', (True, ''))[0]):
        chat_ok, chat_msg = test_chat_api(args.url)
        test_results['chat'] = (chat_ok, chat_msg)
    
    # 总结测试结果
    logger.info("\n=== 测试总结 ===")
    all_tests_passed = True
    
    for test_name, (success, message) in test_results.items():
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{test_name.capitalize()} 测试: {status} - {message}")
        all_tests_passed = all_tests_passed and success
    
    if all_tests_passed:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.warning("⚠️ 部分测试失败，请检查日志了解详情")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 