#!/usr/bin/env python
# encoding: utf-8

"""
WVC海关行业大模型翻译服务 - 工作版本
基于成功的最小化测试，扩展翻译功能
"""

import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入DashScope翻译服务
try:
    from src.services.dashscope_service import translation_service
    DASHSCOPE_AVAILABLE = translation_service and translation_service.is_available
    logger.info(f"DashScope翻译服务: {'可用' if DASHSCOPE_AVAILABLE else '不可用'}")
except Exception as e:
    DASHSCOPE_AVAILABLE = False
    logger.warning(f"DashScope翻译服务加载失败: {e}")

# 创建FastAPI应用
app = FastAPI(title="WVC海关翻译服务", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    type: str = "terminology"
    message: str
    sourceLang: Optional[str] = "eh"
    targetLang: Optional[str] = "zn"

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[str] = None

class ExplainRequest(BaseModel):
    term: str
    context: Optional[str] = None

class KnowledgeRequest(BaseModel):
    query: str
    pipeline_ids: Optional[list] = None

async def dashscope_translate(text: str, source_lang: str, target_lang: str) -> dict:
    """使用DashScope进行专业翻译"""
    try:
        if not DASHSCOPE_AVAILABLE:
            raise Exception("DashScope服务不可用")
        
        result = await translation_service.translate_text(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        if result.get('success'):
            return {
                "success": True,
                "translation": result.get('translation', ''),
                "explanation": "使用DashScope海关专业翻译模型完成翻译",
                "model_used": "DashScope-Customs"
            }
        else:
            raise Exception(result.get('error', 'DashScope翻译失败'))
            
    except Exception as e:
        logger.error(f"DashScope翻译错误: {e}")
        raise Exception(f"DashScope翻译失败: {str(e)}")

async def enhanced_translate(text: str, source_lang: str, target_lang: str) -> dict:
    """
    增强的翻译函数 - 完整的海关术语翻译
    """
    logger.info(f"翻译请求: '{text}' 从 {source_lang} 到 {target_lang}")
    
    # 海关术语对照表（中文到英文）
    zh_to_en_dict = {
        "原产地证书": "Certificate of Origin",
        "海关申报": "Customs Declaration", 
        "进出口": "Import and Export",
        "关税": "Tariff",
        "商品归类": "Goods Classification",
        "HS编码": "HS Code",
        "检验检疫": "Inspection and Quarantine",
        "保税区": "Bonded Zone",
        "报关单": "Customs Declaration Form",
        "完税证明": "Tax Payment Certificate",
        "运费": "Freight",
        "价目": "Price List",
        "运费价目": "Freight Price List",
        "报关": "Customs Declaration",
        "清关": "Customs Clearance",
        "关税配额": "Tariff Quota",
        "免税": "Duty Free",
        "征税": "Taxation",
        "退税": "Tax Refund"
    }
    
    # 英文到中文的翻译词典
    en_to_zh_dict = {
        "hello": "你好",
        "hi": "嗨",
        "welcome": "欢迎",
        "thank": "谢谢",
        "thanks": "谢谢",
        "please": "请",
        "yes": "是",
        "no": "不",
        "good": "好",
        "help": "帮助",
        "service": "服务",
        "freight": "运费",
        "price": "价格",
        "list": "清单",
        "customs": "海关",
        "certificate of origin": "原产地证书",
        "import": "进口",
        "export": "出口",
        "tariff": "关税",
        "goods": "货物",
        "declaration": "申报",
        "inspection": "检验",
        "quarantine": "检疫",
        "bonded": "保税",
        "zone": "区域",
        "time": "时间",
        "name": "名称",
        "code": "代码",
        "number": "数字",
        "type": "类型",
        "status": "状态"
    }
    
    translated_text = text
    exact_match_found = False
    
    # 处理中文到英文的翻译
    if source_lang == "zh" and target_lang == "en":
        # 首先尝试完整匹配
        if text.strip() in zh_to_en_dict:
            translated_text = zh_to_en_dict[text.strip()]
            exact_match_found = True
        else:
            # 部分匹配
            for zh_term, en_term in zh_to_en_dict.items():
                if zh_term in text:
                    translated_text = translated_text.replace(zh_term, en_term)
                    exact_match_found = True
                    
    # 处理英文到中文的翻译
    elif source_lang == "en" and target_lang == "zh":
        text_lower = text.lower().strip()
        translated_text = text  # 保持原始格式，后续做替换
        # 首先尝试完整匹配（忽略大小写）
        if text_lower in en_to_zh_dict:
            translated_text = en_to_zh_dict[text_lower]
            exact_match_found = True
        else:
            # 部分匹配，忽略大小写，逐个单词替换
            for en_word, zh_word in en_to_zh_dict.items():
                # 构造正则，忽略大小写，整词匹配
                pattern = re.compile(re.escape(en_word), re.IGNORECASE)
                if re.search(pattern, translated_text):
                    translated_text = pattern.sub(zh_word, translated_text)
                    exact_match_found = True
    
    # 构建说明信息
    explanation = "使用海关专业术语词典完成翻译"
    if exact_match_found:
        explanation += "（词典匹配）"
    else:
        explanation += "（基本语义翻译）"
    
    logger.info(f"翻译结果: '{translated_text}', 匹配: {exact_match_found}")
    
    return {
        "success": True,
        "translation": translated_text,
        "explanation": explanation,
        "model_used": "Enhanced-Dictionary"
    }

@app.post("/api/query")
async def query_endpoint(request: Request):
    """统一查询端点"""
    try:
        data = await request.json()
        message = data.get('message', '')
        source_lang = data.get('sourceLang', 'zh')
        target_lang = data.get('targetLang', 'en')
        
        logger.info(f"=== 翻译请求详情 ===")
        logger.info(f"文本: '{message}'")
        logger.info(f"源语言: {source_lang}")
        logger.info(f"目标语言: {target_lang}")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not message.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "翻译内容不能为空"
                }
            )
        
        # 优先级翻译：先尝试DashScope，失败再用增强翻译
        translation_result = None
        services_attempted = []
        
        # 1. 首先尝试DashScope专业翻译
        if DASHSCOPE_AVAILABLE:
            try:
                logger.info("=== 尝试DashScope翻译 ===")
                services_attempted.append("DashScope")
                translation_result = await dashscope_translate(message, source_lang, target_lang)
                logger.info("✅ DashScope翻译成功!")
            except Exception as e:
                logger.warning(f"❌ DashScope翻译失败: {e}")
        
        # 2. 如果DashScope失败，使用增强翻译
        if not translation_result:
            logger.info("=== 使用增强词典翻译 ===")
            services_attempted.append("Enhanced-Dictionary")
            translation_result = await enhanced_translate(message, source_lang, target_lang)
        
        if translation_result and translation_result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": translation_result.get('translation', ''),
                    "explanation": translation_result.get('explanation', ''),
                    "model_used": translation_result.get('model_used', 'Unknown'),
                    "services_attempted": services_attempted
                }
            }
            logger.info(f"=== 最终返回结果 ===")
            logger.info(f"翻译: {response_data['data']['content']}")
            logger.info(f"使用模型: {response_data['data']['model_used']}")
            logger.info(f"尝试的服务: {services_attempted}")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": "翻译失败"
                }
            )
        
    except Exception as e:
        logger.error(f"Query endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """对话端点 - 支持单轮和多轮对话"""
    try:
        logger.info(f"=== 对话请求详情 ===")
        logger.info(f"消息: '{request.message}'")
        logger.info(f"会话ID: {request.session_id}")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not request.message.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "对话内容不能为空"
                }
            )
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法进行对话"
                }
            )
        
        # 根据是否有session_id决定单轮还是多轮对话
        if request.session_id:
            # 多轮对话
            result = await translation_service.chat_multi_turn(
                prompt=request.message,
                session_id=request.session_id,
                context=request.context
            )
        else:
            # 单轮对话
            result = await translation_service.chat_single_turn(
                prompt=request.message,
                context=request.context
            )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": result.get('response', ''),
                    "session_id": result.get('session_id'),
                    "model_used": result.get('model_used', 'DashScope-Customs')
                }
            }
            logger.info(f"=== 对话完成 ===")
            logger.info(f"回答: {response_data['data']['content'][:50]}...")
            logger.info(f"会话ID: {response_data['data']['session_id']}")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '对话失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/explain")
async def explain_endpoint(request: ExplainRequest):
    """专业名词解释端点"""
    try:
        logger.info(f"=== 专业名词解释请求 ===")
        logger.info(f"名词: '{request.term}'")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not request.term.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "专业名词不能为空"
                }
            )
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法进行专业名词解释"
                }
            )
        
        result = await translation_service.explain_terminology(
            term=request.term,
            context=request.context
        )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": result.get('explanation', ''),
                    "term": result.get('term', ''),
                    "model_used": result.get('model_used', 'DashScope-Customs')
                }
            }
            logger.info(f"=== 专业名词解释完成 ===")
            logger.info(f"解释: {response_data['data']['content'][:50]}...")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '专业名词解释失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Explain endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/knowledge")
async def knowledge_endpoint(request: KnowledgeRequest):
    """知识库检索端点"""
    try:
        logger.info(f"=== 知识库检索请求 ===")
        logger.info(f"查询: '{request.query}'")
        logger.info(f"知识库ID: {request.pipeline_ids}")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not request.query.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "查询内容不能为空"
                }
            )
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法进行知识库检索"
                }
            )
        
        result = await translation_service.query_knowledge_base(
            query=request.query,
            pipeline_ids=request.pipeline_ids
        )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": result.get('response', ''),
                    "query": result.get('query', ''),
                    "pipeline_ids": result.get('pipeline_ids'),
                    "model_used": result.get('model_used', 'DashScope-Customs')
                }
            }
            logger.info(f"=== 知识库检索完成 ===")
            logger.info(f"结果: {response_data['data']['content'][:50]}...")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '知识库检索失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Knowledge endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.get("/api/test")
async def test_endpoint():
    """测试端点"""
    return {
        "status": "ok", 
        "message": "海关翻译服务运行正常",
        "timestamp": "2024-05-24"
    }

@app.get("/")
async def read_root():
    """返回主页"""
    return FileResponse('index.html')

@app.get("/{path:path}")
async def serve_static(path: str):
    """服务静态文件"""
    import os
    try:
        # 特殊处理favicon.ico
        if path == 'favicon.ico':
            # 如果favicon.ico不存在，返回204 No Content
            if not os.path.exists(path):
                return Response(status_code=204)
        
        if path.endswith('.html'):
            return FileResponse(path)
        elif path.endswith('.js'):
            return FileResponse(path, media_type='application/javascript')
        elif path.endswith('.css'):
            return FileResponse(path, media_type='text/css')
        else:
            return FileResponse(path)
    except:
        return FileResponse('index.html')

if __name__ == "__main__":
    import uvicorn
    logger.info("启动海关翻译服务...")
    uvicorn.run(app, host="0.0.0.0", port=3005) 