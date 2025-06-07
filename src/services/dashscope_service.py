#!/usr/bin/env python
# encoding: utf-8

"""
DashScope翻译服务模块
提供基于阿里云DashScope API的海关专业翻译功能
使用已训练好的海关领域翻译模型
"""

import os
import json
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
        self.workspace_id = "llm-crtlndfq40oj579k"  # 业务空间ID
        self.memory_id = "e30ca0abc71549c28bc93586d3630430"  # 默认记忆体ID
        self.is_available = False
        
        # 从 WVC/aliyun 文件获取的知识库ID列表
        self.knowledge_base_ids = ["didtamgrxs", "ebnq5okz57", "fc2ov71ytv", "ihu3fyuhwk", "s9gacm0ko0"]
        
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
                logger.info(f"- 使用知识库IDs: {self.knowledge_base_ids}")
                
                # 检查提示词模板文件路径
                self._check_prompt_template_file()
            else:
                logger.warning("DashScope翻译服务初始化失败：无法连接到API")
                
        except ImportError as e:
            logger.error(f"DashScope库未安装或导入失败: {e}")
            logger.error("请运行: pip install dashscope>=1.20.11")
            self.is_available = False
        except Exception as e:
            logger.error(f"DashScope初始化失败: {e}")
            self.is_available = False
    
    def _check_prompt_template_file(self):
        """
        检查提示词模板文件是否存在，并记录路径信息，帮助诊断文件路径问题。
        """
        try:
            # 获取可能的提示词模板文件路径
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            possible_paths = [
                os.path.join(current_dir, "prompt"),                  # WVC/prompt
                os.path.join(os.path.dirname(current_dir), "prompt"), # prompt
                "WVC/prompt",                                         # 相对路径
                "prompt"                                              # 当前目录
            ]
            
            # 检查哪些路径存在
            found_paths = []
            for path in possible_paths:
                if os.path.exists(path):
                    found_paths.append(path)
            
            if found_paths:
                logger.info(f"找到提示词模板文件，可用路径: {', '.join(found_paths)}")
            else:
                logger.warning(f"未找到提示词模板文件，已尝试以下路径: {', '.join(possible_paths)}")
                logger.warning(f"当前工作目录: {os.getcwd()}")
                
        except Exception as e:
            logger.error(f"检查提示词模板文件时发生错误: {str(e)}")
    
    def _test_connection(self) -> bool:
        """
        测试 DashScope 连接。

        逻辑调整：
        1. 先发送最简单的调用（不携带 rag_options），如果返回不是 401（未授权）即视为可用；
        2. 若第一步因权限或其他问题抛异常，则返回 False；
        3. 不再在探活阶段携带 knowledge_base_ids，避免因知识库配置问题导致连接判定失败。
        """
        try:
            # 基础探活请求（不携带知识库等可选参数），确保 API Key 与 App ID 有效。
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt="ping"
            )

            # 只要不是未授权错误即可认为服务可用；400 及其他错误交由业务调用时再处理。
            return response.status_code != 401

        except Exception as e:
            logger.debug(f"连接测试失败: {e}")
            return False
    
    async def translate_text(self, 
                           text: str, 
                           source_lang: str = "zh", 
                           target_lang: str = "en",
                           context: Optional[str] = None,
                           show_workflow: bool = True) -> Dict[str, Any]:
        """
        执行文本翻译
        
        Args:
            text (str): 待翻译的文本
            source_lang (str): 源语言代码 (zh, en, ja, ko等)
            target_lang (str): 目标语言代码
            context (str, optional): 额外的上下文信息
            show_workflow (bool): 是否展示翻译工作流过程，默认为True
            
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
            prompt = self._build_translation_prompt(text, source_lang, target_lang, context, show_workflow)
            
            logger.info(f"开始DashScope翻译: {text[:50]}...")
            logger.info(f"使用 App ID: {self.app_id}")
            logger.info(f"使用知识库 IDs: {self.knowledge_base_ids}")
            logger.info(f"显示工作流: {show_workflow}")
            logger.info(f"实际调用API前 - 源语言: {source_lang}, 目标语言: {target_lang}, Prompt (部分): {prompt[:100]}...")
            
            # 使用正确的DashScope API调用方式
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=prompt,
                rag_options={
                    "pipeline_ids": self.knowledge_base_ids
                }
            )
            
            # 检查API响应状态
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                logger.error(f"Request ID: {getattr(response, 'request_id', 'N/A')}") # 记录 request_id 方便排查
                return {
                    "success": False,
                    "error": error_msg,
                    "translation": None
                }
            
            # 提取翻译结果
            if hasattr(response, 'output') and hasattr(response.output, 'text'):
                translation_result = response.output.text.strip()
            else:
                logger.error(f"无法提取翻译结果，响应结构异常. Request ID: {getattr(response, 'request_id', 'N/A')}")
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
            logger.error(error_msg, exc_info=True) # 添加 exc_info=True 获取更详细的traceback
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
                                context: Optional[str] = None,
                                show_workflow: bool = True) -> str:
        """
        构建专业的海关翻译提示词，并要求反馈工作流过程。
        提示词模板从 WVC/prompt 文件加载。
        
        Args:
            text (str): 待翻译文本
            source_lang (str): 源语言
            target_lang (str): 目标语言
            context (str, optional): 额外上下文
            show_workflow (bool): 是否展示翻译工作流过程，默认为True
            
        Returns:
            str: 构建好的提示词, 如果模板文件加载失败则返回错误提示或默认提示。
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

        # 创建基础提示词
        if show_workflow:
            prompt = f"""请将以下从{source_lang_name}翻译成{target_lang_name}：
            
{text}

重要指示：你必须严格按照以下工作流格式展示翻译过程，这是最重要的要求。最终输出必须包含完整的工作流过程和步骤，而不仅仅是最终翻译。

# 翻译工作流执行过程：
## 1. 原文拆解与专业术语提取
在这个部分，详细列出从原文中提取的所有专业术语。
例如：
- economic operators：经济运营商
- customs treatment：海关处理

## 2. 术语检索与翻译
### 2.1. 术语拆解与提取
详细描述每个专业术语的拆解过程和含义。

### 2.2. 术语检索与校验
列出每个术语从知识库中检索到的翻译及相关信息，包括来源。

## 3. 初步译文生成
根据上述检索结果生成的初步译文，完整呈现。

## 4. 译文检查
检查初步译文中是否有专业术语和专业知识的错误，列出发现的问题。

## 5. 错误纠正
如有错误，在这里详细说明纠正过程和理由。

## 6. 译文润色
对译文进行润色，使其流畅、严谨、符合海关公文写作规范。

## 7. 最终译文
输出最终润色后的完整译文。

注意：这些步骤一个都不能省略，必须完整展示整个翻译过程。每个部分都必须有实质性内容，不能只有标题。最终交付的结果必须是完整的工作流格式，而不只是最终译文。
"""
        else:
            # 不显示工作流时的简化提示词
            prompt = f"""请将以下从{source_lang_name}翻译成{target_lang_name}：
            
{text}

请直接提供专业、准确的翻译结果，无需展示翻译过程。要求：
1. 确保专业海关术语翻译准确
2. 保持原文的格式和结构
3. 确保翻译的语法正确、表达流畅
4. 遵循目标语言的行文习惯
"""

        prompt_template = ""
        try:
            # 查找提示词模板文件的路径
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            possible_paths = [
                os.path.join(current_dir, "prompt"),                  # WVC/prompt
                os.path.join(os.path.dirname(current_dir), "prompt"), # prompt
                "WVC/prompt",                                         # 相对路径
                "prompt"                                              # 当前目录
            ]
            
            # 找到第一个存在的路径
            prompt_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    prompt_file_path = path
                    break
            
            if not prompt_file_path:
                raise FileNotFoundError(f"无法找到提示词模板文件，已尝试路径: {', '.join(possible_paths)}")
                
            logger.info(f"使用提示词模板文件: {prompt_file_path}")
            
            # 加载提示词模板文件
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
            
            # 如果模板存在，使用模板中的知识库和限制条件等信息补充提示词
            if prompt_template:
                # 从模板中提取知识库数据解析注意事项、翻译原则、润色原则等关键部分
                knowledge_section = ""
                if "# 知识库数据解析注意事项" in prompt_template:
                    knowledge_start = prompt_template.find("# 知识库数据解析注意事项")
                    knowledge_end = prompt_template.find("#", knowledge_start + 1)
                    if knowledge_end > knowledge_start:
                        knowledge_section = prompt_template[knowledge_start:knowledge_end].strip()
                
                translation_principles = ""
                if "# 翻译原则：" in prompt_template:
                    principles_start = prompt_template.find("# 翻译原则：")
                    principles_end = prompt_template.find("#", principles_start + 1)
                    if principles_end > principles_start:
                        translation_principles = prompt_template[principles_start:principles_end].strip()
                
                polish_principles = ""
                if "# 润色原则：" in prompt_template:
                    polish_start = prompt_template.find("# 润色原则：")
                    polish_end = prompt_template.find("#", polish_start + 1)
                    if polish_end > polish_start:
                        polish_principles = prompt_template[polish_start:polish_end].strip()
                
                # 附加提取的部分到提示词中
                if knowledge_section:
                    prompt += f"\n\n{knowledge_section}"
                if translation_principles:
                    prompt += f"\n\n{translation_principles}"
                if polish_principles:
                    prompt += f"\n\n{polish_principles}"

        except FileNotFoundError:
            logger.error("提示词模板文件 WVC/prompt 未找到。将使用默认提示词。")
            # 使用上面创建的基础提示词，已经定义了
        except Exception as e:
            logger.error(f"加载或格式化提示词模板 WVC/prompt 时发生错误: {e}")
            # 使用上面创建的基础提示词，已经定义了
        
        # 添加额外上下文 (如果提供)
        if context:
            prompt += f"\n\n## 参考信息：\n{context}\n"
        
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
    
    def _build_memory_chat_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """
        构建带长期记忆的对话提示词
        
        Args:
            prompt (str): 用户问题
            context (str, optional): 额外上下文
            
        Returns:
            str: 构建好的对话提示词
        """
        memory_prompt = f"""你是一位专业的海关业务专家，具有长期记忆能力，能够记住之前的对话内容和用户偏好。

用户问题：{prompt}

请根据以下要求回答：
1. 结合之前的对话记忆，提供个性化的专业解答
2. 如果是延续之前的话题，请体现连贯性
3. 提供准确、专业的海关业务解答
4. 如涉及法规条文，请引用具体条款
5. 如涉及操作流程，请提供详细步骤
6. 语言简洁明了，便于理解

"""
        
        # 添加额外上下文
        if context:
            memory_prompt += f"参考信息：\n{context}\n\n"
        
        memory_prompt += "专业解答："
        
        return memory_prompt
    
    async def create_memory(self, description: Optional[str] = None) -> Dict[str, Any]:
        """
        创建长期记忆体
        
        Args:
            description (str, optional): 记忆体描述
            
        Returns:
            Dict[str, Any]: 包含记忆体ID的结果
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "memory_id": None
            }
        
        try:
            import requests
            
            # 构建创建记忆体的API请求
            url = f"https://dashscope.aliyuncs.com/api/v1/{self.workspace_id}/memories"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {}
            if description:
                data["description"] = description
            
            logger.info("开始创建长期记忆体...")
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                memory_id = result.get("memoryId")
                logger.info(f"长期记忆体创建成功: {memory_id}")
                
                return {
                    "success": True,
                    "memory_id": memory_id,
                    "description": description,
                    "request_id": result.get("requestId")
                }
            else:
                error_msg = f"创建记忆体失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "memory_id": None
                }
                
        except Exception as e:
            error_msg = f"创建记忆体过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "memory_id": None
            }
    
    async def chat_with_memory(self, prompt: str, memory_id: Optional[str] = None, context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用长期记忆进行对话
        
        Args:
            prompt (str): 用户问题
            memory_id (str, optional): 记忆体ID，如果不提供则使用默认记忆体
            context (str, optional): 额外上下文
            
        Returns:
            Dict[str, Any]: 包含对话结果的字典
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用",
                "response": None
            }
        
        try:
            # 使用提供的记忆体ID或默认记忆体ID
            used_memory_id = memory_id or self.memory_id
            
            # 构建带记忆的对话提示词
            chat_prompt = self._build_memory_chat_prompt(prompt, context)
            
            logger.info(f"开始DashScope长期记忆对话: {prompt[:50]}...")
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=chat_prompt,
                memory_id=used_memory_id
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
            else:
                logger.error("无法提取对话结果，响应结构异常")
                return {
                    "success": False,
                    "error": "无法提取对话结果",
                    "response": None
                }
            
            logger.info(f"DashScope长期记忆对话完成: {chat_result[:50]}...")
            
            return {
                "success": True,
                "response": chat_result,
                "prompt": prompt,
                "memory_id": used_memory_id,
                "model_used": self.model_name
            }
            
        except Exception as e:
            error_msg = f"DashScope长期记忆对话过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "response": None
            }
    
    async def save_memory_info(self, info: str, memory_id: Optional[str] = None) -> Dict[str, Any]:
        """
        保存信息到长期记忆体
        
        Args:
            info (str): 要保存的信息
            memory_id (str, optional): 记忆体ID
            
        Returns:
            Dict[str, Any]: 保存结果
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "DashScope服务不可用"
            }
        
        try:
            # 使用提供的记忆体ID或默认记忆体ID
            used_memory_id = memory_id or self.memory_id
            
            # 通过对话的方式保存信息到记忆体
            save_prompt = f"请记住以下信息：{info}"
            
            logger.info(f"开始保存信息到记忆体: {info[:50]}...")
            
            response = self.Application.call(
                api_key=self.api_key,
                app_id=self.app_id,
                prompt=save_prompt,
                memory_id=used_memory_id
            )
            
            if response.status_code != self.HTTPStatus.OK:
                error_msg = f"API调用失败: {response.status_code} - {getattr(response, 'message', '未知错误')}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
            
            logger.info("信息保存到记忆体成功")
            
            return {
                "success": True,
                "info": info,
                "memory_id": used_memory_id,
                "message": "信息已保存到长期记忆体"
            }
            
        except Exception as e:
            error_msg = f"保存信息到记忆体过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

# 尝试创建全局服务实例
try:
    translation_service = DashScopeTranslationService()
    logger.info("DashScope翻译服务实例创建成功")
except Exception as e:
    logger.error(f"DashScope翻译服务实例创建失败: {e}")
    translation_service = None 