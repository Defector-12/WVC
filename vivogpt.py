# encoding: utf-8
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import time
import requests
from auth_util import gen_sign_headers
import os
import aiofiles
import tempfile
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入DashScope翻译服务，如果失败则使用备用方案
try:
    from src.services.dashscope_service import translation_service
    # 检查translation_service是否成功创建
    if translation_service is not None:
        DASHSCOPE_AVAILABLE = True
        logger.info("DashScope翻译服务加载成功")
    else:
        DASHSCOPE_AVAILABLE = False
        logger.warning("DashScope翻译服务实例为None，将使用备用翻译方案")
except Exception as e:
    logger.warning(f"DashScope翻译服务加载失败: {e}，将使用备用翻译方案")
    DASHSCOPE_AVAILABLE = False
    translation_service = None

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="assets"), name="static")
app.mount("/styles", StaticFiles(directory="styles"), name="styles")
app.mount("/src", StaticFiles(directory="src"), name="src")

# VIVO模型配置（备用方案）
VIVO_CONFIG = {
    "app_id": "2025880184",
    "app_key": "giowHrLPbUvQfPtD",
    "base_url": "https://api.vivo.com.cn/nlp"
}

class QueryRequest(BaseModel):
    """查询请求模型"""
    type: str = "terminology"
    message: str
    sourceLang: Optional[str] = "zh"
    targetLang: Optional[str] = "en"

async def dashscope_translate(text: str, source_lang: str, target_lang: str) -> dict:
    """
    使用DashScope进行翻译
    """
    try:
        if not DASHSCOPE_AVAILABLE:
            raise Exception("DashScope服务不可用")
        
        # 调用DashScope翻译服务
        result = await translation_service.translate_text(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        if result.get('success'):
            return {
                "success": True,
                "translation": result.get('translation', ''),
                "explanation": f"使用DashScope海关专业翻译模型完成翻译",
                "model_used": "DashScope-Customs"
            }
        else:
            raise Exception(result.get('error', 'DashScope翻译失败'))
            
    except Exception as e:
        logger.error(f"DashScope翻译错误: {e}")
        raise Exception(f"DashScope翻译失败: {str(e)}")

async def vivo_translate(text: str, source_lang: str, target_lang: str) -> dict:
    """
    使用VIVO蓝心大模型进行翻译（备用方案）
    """
    try:
        # 语言映射
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
        
        source_name = lang_map.get(source_lang, source_lang)
        target_name = lang_map.get(target_lang, target_lang)
        
        # 构建海关专业翻译提示词
        prompt = f"""作为专业的海关术语翻译专家，请将以下{source_name}内容准确翻译成{target_name}。

翻译要求：
1. 保持海关专业术语的准确性
2. 遵循国际海关组织标准
3. 保持原文结构和格式
4. 确保翻译专业、准确

待翻译内容：{text}

请直接提供翻译结果："""

        # 构建请求
        headers = gen_sign_headers(VIVO_CONFIG["app_id"], VIVO_CONFIG["app_key"])
        headers["Content-Type"] = "application/json"
        
        data = {
            "requestId": str(uuid.uuid4()),
            "messages": [{"role": "user", "content": prompt}],
            "model": "vivo-BlueLM-TB-70B",
            "extra": {
                "temperature": 0.3,
                "max_tokens": 2000
            }
        }
        
        response = requests.post(
            f"{VIVO_CONFIG['base_url']}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0 and result.get("data"):
                translation = result["data"]["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "translation": translation.strip(),
                    "explanation": "使用VIVO蓝心大模型-70B完成翻译",
                    "model_used": "VIVO-BlueLM-70B"
                }
        
        raise Exception(f"VIVO API调用失败: {response.status_code}")
        
    except Exception as e:
        logger.error(f"VIVO翻译错误: {e}")
        raise Exception(f"VIVO翻译失败: {str(e)}")

async def simple_translate(text: str, source_lang: str, target_lang: str) -> dict:
    """
    改进的翻译备用方案 - 扩展词典 + 基本翻译逻辑
    """
    # 扩展的海关术语对照表
    terminology_dict = {
        # 基础海关术语
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
        
        # 扩展术语
        "运费": "Freight",
        "价目": "Price List",
        "运费价目": "Freight Price List",
        "报关": "Customs Declaration",
        "清关": "Customs Clearance",
        "关税配额": "Tariff Quota",
        "免税": "Duty Free",
        "征税": "Taxation",
        "退税": "Tax Refund",
        "核销": "Verification and Write-off",
        "监管": "Supervision",
        "查验": "Inspection",
        "缉私": "Anti-smuggling",
        "走私": "Smuggling",
        "违规": "Violation",
        "处罚": "Penalty",
        "申报": "Declaration",
        "审核": "Review",
        "批准": "Approval",
        "许可证": "License",
        "配额": "Quota",
        "限制": "Restriction",
        "禁止": "Prohibition",
        "准入": "Market Access",
        "贸易": "Trade",
        "出口": "Export",
        "进口": "Import",
        "转口": "Re-export",
        "过境": "Transit",
        "仓储": "Warehousing",
        "物流": "Logistics",
        "承运人": "Carrier",
        "货代": "Freight Forwarder",
        "代理": "Agent",
        "委托": "Entrust",
        "货物": "Goods",
        "商品": "Commodity",
        "产品": "Product",
        "样品": "Sample",
        "展品": "Exhibition Goods",
        "包装": "Packaging",
        "标识": "Marking",
        "标签": "Label",
        "条码": "Barcode",
        "单证": "Documents",
        "发票": "Invoice",
        "装箱单": "Packing List",
        "提单": "Bill of Lading",
        "保险单": "Insurance Policy",
        "合同": "Contract",
        "订单": "Purchase Order",
        "汇率": "Exchange Rate",
        "外汇": "Foreign Exchange",
        "结汇": "Foreign Exchange Settlement",
        "付汇": "Foreign Exchange Payment"
    }
    
    translated_text = text
    exact_match_found = False
    
    # 1. 精确匹配翻译
    if source_lang == "zh" and target_lang == "en":
        for zh_term, en_term in terminology_dict.items():
            if zh_term == text.strip():  # 精确匹配
                translated_text = en_term
                exact_match_found = True
                break
            elif zh_term in text:  # 部分匹配
                translated_text = translated_text.replace(zh_term, en_term)
                exact_match_found = True
                
    elif source_lang == "en" and target_lang == "zh":
        for zh_term, en_term in terminology_dict.items():
            if en_term.lower() == text.strip().lower():  # 精确匹配
                translated_text = zh_term
                exact_match_found = True
                break
            elif en_term.lower() in text.lower():  # 部分匹配
                translated_text = translated_text.replace(en_term, zh_term)
                exact_match_found = True
    
    # 2. 如果没有词典匹配，使用基本翻译逻辑
    if not exact_match_found:
        # 基本的字符级翻译逻辑（适用于常见词汇）
        basic_translations = {
            # 中文到英文的基本词汇
            "费": "fee",
            "价": "price", 
            "目": "list",
            "单": "form",
            "证": "certificate",
            "书": "document",
            "关": "customs",
            "税": "tax",
            "货": "goods",
            "物": "cargo",
            "品": "product",
            "码": "code",
            "号": "number",
            "类": "category",
            "别": "classification",
            "级": "grade",
            "等": "class",
            "区": "zone",
            "港": "port",
            "站": "station",
            "场": "yard",
            "库": "warehouse",
            "仓": "storage"
        }
        
        if source_lang == "zh" and target_lang == "en":
            # 对于中文，尝试基本的语义理解
            if "运费" in text and "价目" in text:
                translated_text = "Freight Rate List"
            elif "运费" in text:
                translated_text = "Freight"
            elif "价目" in text:
                translated_text = "Price List"
            elif "费用" in text:
                translated_text = "Fee"
            elif "价格" in text:
                translated_text = "Price"
            elif "清单" in text:
                translated_text = "List"
            elif "目录" in text:
                translated_text = "Catalog"
            else:
                # 组合翻译：分解词汇并重组
                result_parts = []
                for char in text:
                    if char in basic_translations:
                        result_parts.append(basic_translations[char])
                    else:
                        result_parts.append(char)
                
                if result_parts and len(result_parts) > 1:
                    translated_text = " ".join(result_parts).title()
                else:
                    # 如果都无法翻译，至少提供一个英文描述
                    translated_text = f"Chinese Term: {text}"
        
        elif source_lang == "en" and target_lang == "zh":
            # 英文到中文的基本翻译
            en_to_zh = {
                "freight": "运费",
                "price": "价格", 
                "list": "清单",
                "rate": "费率",
                "cost": "成本",
                "fee": "费用",
                "charge": "收费",
                "customs": "海关",
                "tax": "税",
                "duty": "关税",
                "goods": "货物",
                "cargo": "货物",
                "product": "产品",
                "certificate": "证书",
                "document": "文件",
                "form": "表单",
                "declaration": "申报",
                "import": "进口",
                "export": "出口"
            }
            
            text_lower = text.lower()
            for en_word, zh_word in en_to_zh.items():
                if en_word in text_lower:
                    translated_text = translated_text.replace(en_word, zh_word)
                    exact_match_found = True
    
    # 3. 构建说明信息
    explanation = "使用内置术语词典完成翻译"
    if exact_match_found:
        explanation += "（词典匹配）"
    else:
        explanation += "（基本语义翻译）"
    
    return {
        "success": True,
        "translation": translated_text,
        "explanation": explanation,
        "model_used": "Enhanced-Dictionary"
    }

@app.post("/api/query")
async def query_endpoint(request: Request):
    """
    统一查询端点，支持术语翻译等功能
    """
    try:
        # 获取请求数据
        content_type = request.headers.get("content-type", "")
        logger.info(f"收到请求，Content-Type: {content_type}")
        
        if content_type.startswith("application/json"):
            data = await request.json()
            logger.info(f"JSON数据: {data}")
        else:
            # 处理 multipart/form-data
            form = await request.form()
            data = dict(form)
            logger.info(f"Form数据: {data}")
            
        query_type = data.get('type', 'terminology')
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
        
        # 尝试多种翻译服务，按优先级顺序
        translation_result = None
        last_error = None
        services_attempted = []
        
        # 1. 首先尝试DashScope专业翻译
        if DASHSCOPE_AVAILABLE:
            try:
                logger.info("=== 尝试DashScope翻译 ===")
                services_attempted.append("DashScope")
                translation_result = await dashscope_translate(message, source_lang, target_lang)
                logger.info("✅ DashScope翻译成功!")
                logger.info(f"翻译结果: {translation_result.get('translation', '')[:100]}...")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ DashScope翻译失败: {e}")
        else:
            logger.info("⚠️ DashScope服务不可用，跳过")
        
        # 2. 如果DashScope失败，尝试VIVO翻译
        if not translation_result:
            try:
                logger.info("=== 尝试VIVO翻译 ===")
                services_attempted.append("VIVO")
                translation_result = await vivo_translate(message, source_lang, target_lang)
                logger.info("✅ VIVO翻译成功!")
                logger.info(f"翻译结果: {translation_result.get('translation', '')[:100]}...")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"❌ VIVO翻译失败: {e}")
        
        # 3. 如果都失败，使用改进的简单翻译
        if not translation_result:
            try:
                logger.info("=== 使用增强词典翻译 ===")
                services_attempted.append("Enhanced-Dictionary")
                translation_result = await simple_translate(message, source_lang, target_lang)
                logger.info("✅ 增强词典翻译完成!")
                logger.info(f"翻译结果: {translation_result.get('translation', '')}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"❌ 所有翻译方案都失败: {e}")
        
        # 返回结果
        if translation_result and translation_result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": translation_result.get('translation', ''),
                    "explanation": translation_result.get('explanation', ''),
                    "model_used": translation_result.get('model_used', 'Unknown'),
                    "services_attempted": services_attempted  # 添加尝试的服务列表
                }
            }
            logger.info(f"=== 最终返回结果 ===")
            logger.info(f"翻译: {response_data['data']['content']}")
            logger.info(f"使用模型: {response_data['data']['model_used']}")
            logger.info(f"尝试的服务: {services_attempted}")
            return response_data
        else:
            error_response = {
                "code": -1,
                "message": f"翻译失败: {last_error or '未知错误'}",
                "services_attempted": services_attempted
            }
            logger.error(f"❌ 翻译失败，返回错误: {error_response}")
            return JSONResponse(
                status_code=500,
                content=error_response
            )
        
    except Exception as e:
        logger.error(f"💥 Query endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.get("/api/test-translate")
async def test_translate():
    """测试翻译功能的简单端点"""
    test_text = "运费价目"
    result = await simple_translate(test_text, "zh", "en")
    
    return {
        "input": test_text,
        "output": result.get('translation', ''),
        "explanation": result.get('explanation', ''),
        "model": result.get('model_used', ''),
        "success": result.get('success', False),
        "dashscope_available": DASHSCOPE_AVAILABLE
    }

@app.get("/api/test")
async def test_endpoint():
    """测试端点，用于检查服务状态"""
    return {
        "status": "ok",
        "dashscope_available": DASHSCOPE_AVAILABLE,
        "timestamp": time.time(),
        "message": "海关翻译服务运行正常"
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
    uvicorn.run(app, host="0.0.0.0", port=8000)

