#!/usr/bin/env python
# encoding: utf-8

"""
检查提示词模板文件加载功能
"""

import os
import logging
import codecs

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_prompt_files():
    """检查提示词模板文件是否存在"""
    logger.info("======= 检查 WVC 提示词模板文件 =======")
    
    # 显示当前工作目录
    logger.info(f"当前工作目录: {os.getcwd()}")
    
    # 检查prompt文件是否存在
    prompt_paths = [
        "prompt",
        "WVC/prompt",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompt")
    ]
    
    logger.info("检查提示词模板文件:")
    found_files = []
    for path in prompt_paths:
        if os.path.exists(path):
            logger.info(f"✅ 提示词模板文件存在: {path}")
            found_files.append(path)
        else:
            logger.info(f"❌ 提示词模板文件不存在: {path}")
    
    if found_files:
        logger.info("✅ 提示词模板文件检查通过")
        
        # 读取第一个找到的提示词文件内容
        try:
            # 尝试不同的编码方式读取文件
            content = None
            encodings = ['utf-8', 'gbk', 'latin1']
            
            for encoding in encodings:
                try:
                    with codecs.open(found_files[0], 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"✅ 成功使用 {encoding} 编码读取提示词文件")
                    break
                except UnicodeDecodeError:
                    logger.warning(f"❌ 使用 {encoding} 编码读取提示词文件失败")
            
            if content:
                # 检查文件内容是否包含必要的工作流部分
                workflow_sections = [
                    "翻译工作流",
                    "对原文进行拆解",
                    "针对每个名词和动词分别从知识库中检索专业术语",
                    "严格按照检索出的专业术语生成整体的初步译文",
                    "译后检查",
                    "纠正错误",
                    "润色译文",
                    "输出最终译文"
                ]
                
                missing_sections = []
                for section in workflow_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if missing_sections:
                    logger.warning(f"⚠️ 提示词文件缺少以下工作流部分: {', '.join(missing_sections)}")
                else:
                    logger.info("✅ 提示词文件包含所有必要的工作流部分")
                    
                # 统计文件大小和行数
                logger.info(f"📊 提示词文件大小: {os.path.getsize(found_files[0])/1024:.2f} KB")
                logger.info(f"📊 提示词文件行数: {len(content.split(os.linesep))}")
                
            else:
                logger.error("❌ 无法使用任何编码读取提示词文件")
                
        except Exception as e:
            logger.error(f"❌ 读取提示词文件时出错: {e}")
        
        return True
    else:
        logger.error("❌ 未找到任何提示词模板文件，服务可能无法正常工作")
        return False

def check_dashscope_service():
    """检查dashscope_service是否能正确加载提示词"""
    logger.info("\n======= 检查 dashscope_service 提示词加载 =======")
    
    dashscope_service_path = os.path.join("src", "services", "dashscope_service.py")
    if not os.path.exists(dashscope_service_path):
        logger.error(f"❌ dashscope_service.py 文件不存在: {dashscope_service_path}")
        return False
    
    # 读取dashscope_service.py文件内容
    try:
        with open(dashscope_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否包含加载提示词的代码
        prompt_loading_patterns = [
            "load_prompt",
            "get_prompt",
            "read_prompt",
            "open('prompt'",
            "open(\"prompt\"",
            "os.path.join",
            "with open"
        ]
        
        found_patterns = []
        for pattern in prompt_loading_patterns:
            if pattern in content:
                found_patterns.append(pattern)
        
        if found_patterns:
            logger.info(f"✅ dashscope_service.py 包含加载提示词的代码: {', '.join(found_patterns)}")
            return True
        else:
            logger.warning("⚠️ dashscope_service.py 可能不包含加载提示词的代码")
            return False
            
    except Exception as e:
        logger.error(f"❌ 读取 dashscope_service.py 时出错: {e}")
        return False

if __name__ == "__main__":
    prompt_check = check_prompt_files()
    service_check = check_dashscope_service()
    
    if prompt_check and service_check:
        logger.info("\n✅ 所有检查均已通过，提示词文件配置正确")
    else:
        logger.warning("\n⚠️ 部分检查未通过，请检查提示词文件配置") 