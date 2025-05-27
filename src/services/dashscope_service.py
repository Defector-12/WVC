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
        # 使用阿里云文档中提供的配置
        self.api_key = "sk-fc310cd28bc74ff5be86913e3816f4d5"  # 阿里云文档中的API Key
        self.app_id = "43f10f032fce4a52b8c40e3eb5a01c5d"  # 训练好的海关翻译模型ID
        self.model_name = "qwen-plus-latest"  # 使用的模型
        self.is_available = False
        
        # 尝试导入并配置DashScope
        try:
            import dashscope
            from dashscope import Application
            from http import HTTPStatus
            
            self.dashscope = dashscope
            self.Application = Application
            self.HTTPStatus = HTTPStatus
            
            # 设置API Key
            os.environ['DASHSCOPE_API_KEY'] = self.api_key
            self.dashscope.api_key = self.api_key
            
            # 测试连接
            if self._test_connection():
                self.is_available = True
                logger.info(f"DashScope翻译服务初始化成功")
                logger.info(f"- 模型ID: {self.app_id}")
                logger.info(f"- 模型名称: {self.model_name}")
            else:
                logger.warning("DashScope翻译服务初始化失败：无法连接到API")
                
        except ImportError as e:
            logger.error(f"DashScope库未安装或导入失败: {e}")
            logger.error("请运行: pip install dashscope>=1.20.11")
            self.is_available = False
        except Exception as e:
            logger.error(f"DashScope初始化失败: {e}")
            self.is_available = False
    
    def _test_connection(self) -> bool:
        """
        测试DashScope连接
        
        Returns:
            bool: 是否成功连接到API
        """
        try:
            # 进行一个简单的测试调用
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt='测试'
            )
            
            # 如果没有401错误，则认为连接成功
            return response.status_code != 401
            
        except Exception as e:
            logger.debug(f"连接测试失败: {e}")
            return False
    
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
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "translation": None
            }
        
        try:
            # 构建专业的海关翻译提示词
            prompt = self._build_translation_prompt(text, source_lang, target_lang, context)
            
            logger.info(f"开始DashScope翻译: {text[:50]}...")
            
            # 使用正确的DashScope API调用方式
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=prompt
            )
            
            # 检查API响应状态
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "translation": None
                }
            
            # 提取翻译结果
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                translation_result = response.output.text.strip()
            else:
                logger.error(f"无法提取翻译结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取翻译结果",
                    "translation": None
                }
            
            logger.info(f"DashScope翻译完成: {translation_result[:50]}...")
            
            return {
                "success": True,
                "translation": translation_result,
                "source_text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "session_id": getattr(response, 'request_id', None),
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope翻译过程中发生错误: {str(e)}"
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
    
    async def chat_single_turn(self, prompt: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        单轮对话
        
        Args:
            prompt (str): 用户输入的问题
            context (str, optional): 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 包含回答结果和相关信息的字典
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "response": None
            }
        
        try:
            # 构建海关专业对话提示词
            chat_prompt = self._build_chat_prompt(prompt, context)
            
            logger.info(f"开始DashScope单轮对话: {prompt[:50]}...")
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=chat_prompt
            )
            
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "response": None
                }
            
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                chat_result = response.output.text.strip()
                session_id = getattr(response.output, 'session_id', None)
            else:
                logger.error("无法提取对话结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取对话结果",
                    "response": None
                }
            
            logger.info(f"DashScope单轮对话完成: {chat_result[:50]}...")
            
            return {
                "success": True,
                "response": chat_result,
                "session_id": session_id,
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope单轮对话过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "response": None
            }
    
    async def chat_multi_turn(self, prompt: str, session_id: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        多轮对话
        
        Args:
            prompt (str): 用户输入的问题
            session_id (str): 会话ID，用于维持对话上下文
            context (str, optional): 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 包含回答结果和相关信息的字典
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "response": None
            }
        
        try:
            # 构建海关专业对话提示词
            chat_prompt = self._build_chat_prompt(prompt, context)
            
            logger.info(f"开始DashScope多轮对话: {prompt[:50]}... (session: {session_id})")
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=chat_prompt,
                session_id=session_id
            )
            
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "response": None
                }
            
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                chat_result = response.output.text.strip()
                new_session_id = getattr(response.output, 'session_id', session_id)
            else:
                logger.error("无法提取对话结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取对话结果",
                    "response": None
                }
            
            logger.info(f"DashScope多轮对话完成: {chat_result[:50]}...")
            
            return {
                "success": True,
                "response": chat_result,
                "session_id": new_session_id,
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope多轮对话过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "response": None
            }
    
    async def explain_terminology(self, term: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        专业名词解释
        
        Args:
            term (str): 需要解释的专业名词
            context (str, optional): 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 包含解释结果的字典
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "explanation": None
            }
        
        try:
            # 构建专业名词解释提示词
            explanation_prompt = self._build_explanation_prompt(term, context)
            
            logger.info(f"开始DashScope专业名词解释: {term}")
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=explanation_prompt
            )
            
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "explanation": None
                }
            
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                explanation_result = response.output.text.strip()
            else:
                logger.error("无法提取解释结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取解释结果",
                    "explanation": None
                }
            
            logger.info(f"DashScope专业名词解释完成: {explanation_result[:50]}...")
            
            return {
                "success": True,
                "explanation": explanation_result,
                "term": term,
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope专业名词解释过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "explanation": None
            }
    
    async def query_knowledge_base(self, query: str, pipeline_ids: Optional[list] = None) -> Dict[str, Any]:
        """
        检索知识库
        
        Args:
            query (str): 查询问题
            pipeline_ids (list, optional): 知识库ID列表
            
        Returns:
            Dict[str, Any]: 包含检索结果的字典
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "response": None
            }
        
        try:
            logger.info(f"开始DashScope知识库检索: {query[:50]}...")
            
            # 构建知识库检索参数
            rag_options = {}
            if pipeline_ids:
                rag_options["pipeline_ids"] = pipeline_ids
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=query,
                rag_options=rag_options if rag_options else None
            )
            
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "response": None
                }
            
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                knowledge_result = response.output.text.strip()
            else:
                logger.error("无法提取知识库检索结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取知识库检索结果",
                    "response": None
                }
            
            logger.info(f"DashScope知识库检索完成: {knowledge_result[:50]}...")
            
            return {
                "success": True,
                "response": knowledge_result,
                "query": query,
                "pipeline_ids": pipeline_ids,
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope知识库检索过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "response": None
            }
    
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
        
        # 构建专业的海关翻译提示词
        prompt = f"""你是一位专业的海关行业翻译专家，精通海关术语、国际贸易法规和相关专业词汇。

请将以下{source_lang_name}内容准确翻译成{target_lang_name}：

原文：{text}

翻译要求：
1. 准确使用海关和国际贸易领域的专业术语
2. 保持原文的专业性和准确性
3. 遵循目标语言的行业规范和习惯表达
4. 如果是专有名词或缩写，请保留原文并在括号中提供翻译
5. 直接输出翻译结果，不需要额外说明

"""
        
        # 添加额外上下文
        if context:
            prompt += f"参考信息：\n{context}\n\n"
        
        prompt += "翻译结果："
        
        return prompt
    
    def _build_chat_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """
        构建海关专业对话提示词
        
        Args:
            prompt (str): 用户问题
            context (str, optional): 额外上下文
            
        Returns:
            str: 构建好的对话提示词
        """
        chat_prompt = f"""你是一位专业的海关业务专家，精通海关法规、国际贸易、商品归类、关税政策等领域知识。

用户问题：{prompt}

请根据以下要求回答：
1. 提供准确、专业的海关业务解答
2. 如涉及法规条文，请引用具体条款
3. 如涉及操作流程，请提供详细步骤
4. 语言简洁明了，便于理解
5. 如果问题超出海关业务范围，请礼貌说明并引导到相关话题

"""
        
        # 添加额外上下文
        if context:
            chat_prompt += f"参考信息：\n{context}\n\n"
        
        chat_prompt += "专业解答："
        
        return chat_prompt
    
    def _build_explanation_prompt(self, term: str, context: Optional[str] = None) -> str:
        """
        构建专业名词解释提示词
        
        Args:
            term (str): 需要解释的专业名词
            context (str, optional): 额外上下文
            
        Returns:
            str: 构建好的解释提示词
        """
        explanation_prompt = f"""你是一位海关业务专家，请对以下海关或国际贸易专业名词进行详细解释。

专业名词：{term}

请按以下格式提供解释：
1. 定义：简明扼要的定义
2. 适用范围：该名词的使用场景和适用范围
3. 相关法规：涉及的主要法律法规（如有）
4. 实际应用：在海关业务中的具体应用
5. 注意事项：需要特别注意的要点（如有）

"""
        
        # 添加额外上下文
        if context:
            explanation_prompt += f"参考信息：\n{context}\n\n"
        
        explanation_prompt += "详细解释："
        
        return explanation_prompt

# 尝试创建全局服务实例
try:
    translation_service = DashScopeTranslationService()
    logger.info("DashScope翻译服务实例创建成功")
except Exception as e:
    logger.error(f"DashScope翻译服务实例创建失败: {e}")
    translation_service = None 