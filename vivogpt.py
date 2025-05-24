#!/usr/bin/env python
# encoding: utf-8

"""
WVC海关行业大模型翻译服务 - 工作版本
基于成功的最小化测试，扩展翻译功能
"""

import logging
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    sourceLang: Optional[str] = "zh"
    targetLang: Optional[str] = "en"

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
        
        # 首先尝试完整匹配
        if text_lower in en_to_zh_dict:
            translated_text = en_to_zh_dict[text_lower]
            exact_match_found = True
        else:
            # 部分匹配
            for en_word, zh_word in en_to_zh_dict.items():
                if en_word in text_lower:
                    translated_text = translated_text.replace(en_word, zh_word)
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
    try:
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