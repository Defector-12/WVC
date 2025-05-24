#!/usr/bin/env python
# encoding: utf-8

"""
DashScope翻译服务模块
提供基于阿里云DashScope API的海关专业翻译功能
使用已训练好的海关领域翻译模型
"""

import os
import logging
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashScopeTranslationService:
    """
    DashScope翻译服务类
    封装了对阿里云DashScope API的调用，专门用于海关领域翻译
    """
    
    def __init__(self):
        """
        初始化DashScope翻译服务
        设置API密钥和模型ID
        """
        # 翻译模型配置
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-f8dcf20a07ac4b889d74f56b7bf654e7")
        self.app_id = "43f10f032fce4a52b8c40e3eb5a01c5d"  # 训练好的海关翻译模型ID
        
        # 验证配置
        if not self.api_key:
            raise ValueError("DashScope API密钥未配置")
        
        # 尝试导入并配置DashScope
        try:
            import dashscope
            from dashscope import Generation
            dashscope.api_key = self.api_key
            self.dashscope = dashscope
            self.Generation = Generation
            logger.info(f"DashScope翻译服务初始化成功，模型ID: {self.app_id}")
        except ImportError as e:
            logger.error(f"DashScope库未安装或导入失败: {e}")
            raise ImportError("请安装dashscope库：pip install dashscope")
        except Exception as e:
            logger.error(f"DashScope初始化失败: {e}")
            raise
    
    async def translate_text(self, 
                           text: str, 
                           source_lang: str = "zh", 
                           target_lang: str = "en",
                           context: Optional[str] = None) -> Dict[str, Any]:
        """
        执行文本翻译
        
        Args:
            text (str): 待翻译的文本
            source_lang (str): 源语言代码 (zh, en, ja, ko等)
            target_lang (str): 目标语言代码
            context (str, optional): 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 包含翻译结果和相关信息的字典
        """
        try:
            # 构建专业的海关翻译提示词
            prompt = self._build_translation_prompt(text, source_lang, target_lang, context)
            
            logger.info(f"开始翻译: {text[:50]}...")
            
            # 使用正确的DashScope API调用方式
            response = self.Generation.call(
                model=self.app_id,  # 使用自定义模型ID
                prompt=prompt,
                top_p=0.8,
                temperature=0.3,
                max_tokens=2000
            )
            
            # 检查API响应状态
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code} - {response.message}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "translation": None
                }
            
            # 提取翻译结果
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                translation_result = response.output.text.strip()
            elif hasattr(response, 'output') and hasattr(response.output, 'choices'):
                translation_result = response.output.choices[0].message.content.strip()
            else:
                translation_result = str(response.output).strip()
            
            logger.info(f"翻译完成: {translation_result[:50]}...")
            
            return {
                "success": True,
                "translation": translation_result,
                "source_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "session_id": getattr(response, 'request_id', None)
            }
            
        except Exception as e:
            error_msg = f"翻译过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "translation": None
            }
    
    async def translate_with_terminology(self, 
                                       text: str, 
                                       terminology_dict: Optional[Dict[str, str]] = None,
                                       source_lang: str = "zh", 
                                       target_lang: str = "en") -> Dict[str, Any]:
        """
        使用术语词典进行翻译
        
        Args:
            text (str): 待翻译的文本
            terminology_dict (Dict[str, str], optional): 术语对照词典
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            
        Returns:
            Dict[str, Any]: 翻译结果
        """
        # 如果提供了术语词典，将其添加到上下文中
        context = None
        if terminology_dict:
            terminology_context = "请参考以下术语对照表进行翻译：\n"
            for source_term, target_term in terminology_dict.items():
                terminology_context += f"{source_term} -> {target_term}\n"
            context = terminology_context
        
        return await self.translate_text(text, source_lang, target_lang, context)
    
    async def batch_translate(self, 
                            text_list: list, 
                            source_lang: str = "zh", 
                            target_lang: str = "en") -> list:
        """
        批量翻译多个文本
        
        Args:
            text_list (list): 待翻译的文本列表
            source_lang (str): 源语言代码
            target_lang (str): 目标语言代码
            
        Returns:
            list: 翻译结果列表
        """
        results = []
        for i, text in enumerate(text_list):
            logger.info(f"正在处理第 {i+1}/{len(text_list)} 个文本")
            result = await self.translate_text(text, source_lang, target_lang)
            results.append(result)
        
        return results
    
    def _build_translation_prompt(self, 
                                text: str, 
                                source_lang: str, 
                                target_lang: str, 
                                context: Optional[str] = None) -> str:
        """
        构建专业的海关翻译提示词
        
        Args:
            text (str): 待翻译文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            context (str, optional): 额外上下文
            
        Returns:
            str: 构建好的提示词
        """
        # 语言代码映射
        lang_map = {
            "zh": "中文",
            "en": "英文", 
            "ja": "日文",
            "ko": "韩文",
            "fr": "法文",
            "de": "德文",
            "es": "西班牙文",
            "ru": "俄文"
        }
        
        source_lang_name = lang_map.get(source_lang, source_lang)
        target_lang_name = lang_map.get(target_lang, target_lang)
        
        # 构建基础提示词
        prompt = f"""作为专业的海关术语翻译专家，请将以下{source_lang_name}内容准确翻译成{target_lang_name}。

翻译要求：
1. 保持海关专业术语的准确性和一致性
2. 遵循国际海关组织的标准术语规范
3. 保持原文的结构和格式
4. 对于HS编码、法规条款等特殊内容保持原样
5. 确保翻译结果专业、准确、易懂

"""
        
        # 添加额外上下文
        if context:
            prompt += f"参考信息：\n{context}\n\n"
        
        # 添加待翻译文本
        prompt += f"待翻译内容：\n{text}\n\n请提供准确的翻译结果："
        
        return prompt

# 尝试创建全局服务实例
try:
    translation_service = DashScopeTranslationService()
    logger.info("DashScope翻译服务实例创建成功")
except Exception as e:
    logger.error(f"DashScope翻译服务实例创建失败: {e}")
    translation_service = None 