#!/usr/bin/env python
# encoding: utf-8

"""
WVC海关行业大模型翻译服务 - 工作版本
基于成功的最小化测试，扩展翻译功能
"""

import logging
from typing import Optional, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import json

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

# 全局变量用于缓存上一次翻译的完整输出 (包含工作流)
last_translation_full_output_cache: Optional[str] = None
# 新增全局变量，用于缓存最终翻译结果（不含工作流）
last_translation_result_only_cache: Optional[str] = None

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

def format_translation_output(text: str) -> str:
    """
    将翻译工作流的Markdown格式转换为更易读的阅读格式，并删除不必要的空格
    
    Args:
        text (str): 原始翻译输出文本（包含Markdown格式）
        
    Returns:
        str: 格式化后的文本
    """
    if not text:
        return ""
    
    # 预处理，处理可能的异常格式
    # 处理行首的#号标记，确保它们被正确识别
    # 替换掉可能存在的"## 2.1"这样的格式（确保空格正确）
    text = re.sub(r'^(#+)\s*(\d+\.\d+)', r'\1 \2', text, flags=re.MULTILINE)
    
    # 分行处理，以便更精确地处理每一行
    lines = text.split('\n')
    processed_lines = []
    in_table = False
    table_data = []
    in_section_2_2 = False  # 标记是否处于2.2节(术语检索与校验部分)
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 检测是否进入2.2节(术语检索与校验部分)
        if re.match(r'^#+\s+2\.2', line) or re.search(r'术语检索与校验', line):
            in_section_2_2 = True
        # 检测是否离开2.2节
        elif in_section_2_2 and re.match(r'^#+\s+\d+', line) and not re.match(r'^#+\s+2\.2', line):
            in_section_2_2 = False
            
        # 1. 处理Markdown标题
        if re.match(r'^#+\s+', line):
            # 提取标题级别和内容
            header_match = re.match(r'^(#+)\s+(.*?)$', line)
            if header_match:
                level = len(header_match.group(1))
                content = header_match.group(2)
                
                # 根据标题级别应用不同的格式
                if level == 1:  # # 一级标题
                    processed_line = f"【{content}】："
                elif level == 2:  # ## 二级标题
                    # 检查是否是数字编号的标题（如 ## 1. 标题）
                    if re.match(r'^\d+\.\s+', content):
                        processed_line = f"【{content}】："
                    else:
                        processed_line = f"【{content}】："
                elif level == 3:  # ### 三级标题
                    # 检查是否是数字编号的标题（如 ### 2.1 标题）
                    if re.match(r'^\d+\.\d+\s+', content):
                        processed_line = f"【{content}】："
                    else:
                        processed_line = f"【{content}】："
                else:  # 更深层次的标题
                    processed_line = f"【{content}】："
                
                processed_lines.append(processed_line)
                i += 1
                continue
        
        # 2. 处理表格 - 对于2.2节特殊处理，转为列表而非表格
        if line.strip().startswith('|') and line.strip().endswith('|'):
            # 检测是否处于2.2节(术语检索与校验部分)
            in_section_2_2 = False
            for j in range(max(0, i-10), i):  # 向上查找10行以内是否有2.2节标题
                if j < len(lines) and (re.match(r'^#+\s+2\.2', lines[j]) or re.search(r'术语检索与校验', lines[j])):
                    in_section_2_2 = True
                    break
            
            # 如果在2.2节且是表格开始，不使用表格格式而是转为列表
            if in_section_2_2 and not in_table:
                in_table = True
                table_data = []
                table_data.append(line)
                i += 1
                # 收集表格内容直到表格结束
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_data.append(lines[i])
                    i += 1
                
                # 转换表格为列表
                headers = []
                rows = []
                
                for idx, table_line in enumerate(table_data):
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    if idx == 0:  # 表头
                        headers = cells
                    elif not re.match(r'\s*[-:]+\s*', ''.join(cells)):  # 不是分隔行
                        rows.append(cells)
                
                # 输出为列表格式
                for row_idx, row in enumerate(rows):
                    item_number = row_idx + 1
                    item_text = f"• {item_number}. "
                    
                    for col_idx, cell in enumerate(row):
                        if col_idx < len(headers) and headers[col_idx].strip() and cell.strip():
                            item_text += f"{headers[col_idx]}: {cell}  "
                    
                    processed_lines.append(item_text)
                
                in_table = False
                continue
            # 非2.2节的表格正常处理
            elif not in_section_2_2:
                if not in_table:
                    in_table = True
                    table_data = []
                
                # 收集表格行数据
                table_data.append(line)
                i += 1
                continue
        elif in_table and not in_section_2_2:
            # 表格结束，处理收集的表格数据（针对非2.2节的表格）
            if table_data:
                # 解析表格数据
                parsed_table = []
                max_cols = 0
                
                for table_line in table_data:
                    if re.match(r'\|\s*[-:]+\s*\|', table_line):
                        continue  # 跳过分隔行
                    
                    # 分割并清理单元格
                    cells = [cell.strip() for cell in table_line.split('|')[1:-1]]
                    parsed_table.append(cells)
                    max_cols = max(max_cols, len(cells))
                
                # 确保所有行都有相同数量的列
                for row_idx, row in enumerate(parsed_table):
                    if len(row) < max_cols:
                        parsed_table[row_idx] = row + [''] * (max_cols - len(row))
                
                # 计算每列的最大宽度
                col_widths = [0] * max_cols
                for row in parsed_table:
                    for j, cell in enumerate(row):
                        col_widths[j] = max(col_widths[j], len(cell))
                
                # 重建表格，使用固定宽度格式
                formatted_table = []
                for row in parsed_table:
                    formatted_row = []
                    for j, cell in enumerate(row):
                        formatted_row.append(cell.ljust(col_widths[j]))
                    
                    formatted_table.append("| " + " | ".join(formatted_row) + " |")
                
                # 在第一行和第二行之间添加分隔行
                if len(formatted_table) > 1:
                    separator_line = "|-" + "-|-".join(["-" * w for w in col_widths]) + "-|"
                    formatted_table.insert(1, separator_line)
                
                processed_lines.extend(formatted_table)
            
            in_table = False
            # 注意：不再添加当前行，因为我们会在下一次循环中处理它
            # 我们不增加索引i，这样当前行会在下次循环中被处理
            continue
        
        # 3. 处理列表项
        list_match = re.match(r'^(\s*)[-*]\s+(.*?)$', line)
        if list_match:
            indent = list_match.group(1)
            content = list_match.group(2)
            processed_lines.append(f"{indent}• {content}")
            i += 1
            continue
        
        # 4. 处理数字列表
        num_list_match = re.match(r'^(\s*)(\d+)\.(\s+)(.*?)$', line)
        if num_list_match:
            indent = num_list_match.group(1)
            number = num_list_match.group(2)
            spaces = num_list_match.group(3)
            content = num_list_match.group(4)
            processed_lines.append(f"{indent}{number}.{spaces}{content}")
            i += 1
            continue
        
        # 5. 处理引用
        quote_match = re.match(r'^>\s+(.*?)$', line)
        if quote_match:
            content = quote_match.group(1)
            processed_lines.append(f"『{content}』")
            i += 1
            continue
        
        # 6. 处理代码块
        if line.strip().startswith('```') or line.strip() == '```':
            # 跳过代码块标记
            i += 1
            continue
        
        # 7. 处理水平线
        if re.match(r'^-{3,}$|^_{3,}$|^\*{3,}$', line.strip()):
            processed_lines.append("—" * 30)  # 使用长破折号作为分隔线
            i += 1
            continue
        
        # 处理内联格式（在行内部的标记）
        # 处理加粗
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line = re.sub(r'__(.*?)__', r'\1', line)
        
        # 处理斜体
        line = re.sub(r'\*(.*?)\*', r'\1', line)
        line = re.sub(r'_(.*?)_', r'\1', line)
        
        # 处理链接
        line = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', line)
        
        # 处理图片
        line = re.sub(r'!\[(.*?)\]\((.*?)\)', r'[图片:\1]', line)
        
        # 8. 正常文本行
        processed_lines.append(line)
        i += 1
    
    # 将处理后的行重新组合
    processed_text = '\n'.join(processed_lines)
    
    # 最终清理
    # 1. 删除连续的空行
    processed_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', processed_text)
    
    # 2. 处理可能遗留的标记
    # 确保没有遗漏的Markdown标题标记
    processed_text = re.sub(r'^#+\s+', '', processed_text, flags=re.MULTILINE)
    
    # 3. 处理特殊格式的标题行（##2.1 这种格式）
    processed_text = re.sub(r'##(\d+\.\d+)(.*?)$', r'【\1\2】：', processed_text, flags=re.MULTILINE)
    processed_text = re.sub(r'##\s+(\d+\.\d+)(.*?)$', r'【\1\2】：', processed_text, flags=re.MULTILINE)
    
    # 4. 处理连续的冒号
    processed_text = re.sub(r'：\s*：', '：', processed_text)
    
    # 5. 清理可能的双重标记
    processed_text = re.sub(r'【【([^】]+)】】', r'【\1】', processed_text)
    
    # 6. 清理行首和行尾的空白
    processed_text = re.sub(r'^\s+', '', processed_text, flags=re.MULTILINE)
    processed_text = re.sub(r'\s+$', '', processed_text, flags=re.MULTILINE)
    
    # 7. 移除特殊的"##"标记
    processed_text = re.sub(r'##\s*(\d+\.\d+)', r'【\1】：', processed_text)
    
    # 8. 检测和删除连续重复的内容块
    lines = processed_text.split('\n')
    if len(lines) > 10:  # 只有当内容足够长时才检查重复
        half_length = len(lines) // 2
        first_half = lines[:half_length]
        second_half = lines[half_length:2*half_length]
        
        # 检查两半是否基本相同
        similarity = sum(1 for a, b in zip(first_half, second_half) if a == b) / len(first_half) if first_half else 0
        
        if similarity > 0.7:  # 如果相似度超过70%，认为存在重复
            processed_text = '\n'.join(lines[:half_length + (len(lines) - 2*half_length)])
    
    return processed_text

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

class MemoryRequest(BaseModel):
    description: Optional[str] = None

class MemoryChatRequest(BaseModel):
    message: str
    memory_id: Optional[str] = None
    context: Optional[str] = None

class SaveMemoryRequest(BaseModel):
    info: str
    memory_id: Optional[str] = None

async def dashscope_translate(text: str, source_lang: str, target_lang: str, show_workflow: bool = True) -> dict:
    """使用DashScope进行专业翻译"""
    try:
        if not DASHSCOPE_AVAILABLE:
            raise Exception("DashScope服务不可用")
        
        result = await translation_service.translate_text(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            show_workflow=show_workflow
        )
        
        if result.get('success'):
            # 确保保存完整的翻译工作流输出
            full_translation_output = result.get('translation', '')
            logger.info(f"DashScope返回完整工作流长度: {len(full_translation_output)} 字符")
            
            return {
                "success": True,
                "translation": full_translation_output,
                "explanation": "使用DashScope海关专业翻译模型完成翻译",
                "model_used": "DashScope-Customs",
                "full_workflow": full_translation_output  # 额外保存完整工作流
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
    global last_translation_full_output_cache 
    global last_translation_result_only_cache
    try:
        data = await request.json()
        message = data.get('message', '')
        
        requested_source_lang = data.get('sourceLang')
        requested_target_lang = data.get('targetLang')
        
        logger.info(f"=== 翻译请求详情 ===")
        logger.info(f"文本: '{message}'")
        if requested_source_lang and requested_target_lang:
            logger.info(f"客户端请求的源语言: {requested_source_lang}, 目标语言: {requested_target_lang}")
        else:
            logger.info("客户端未明确指定源语言或目标语言，将进行自动检测。")
        
        if not message.strip():
            last_translation_full_output_cache = None # Clear cache on empty input
            last_translation_result_only_cache = None
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "翻译内容不能为空"
                }
            )
        
        # 检测用户是否想要直接翻译（不显示工作流）
        direct_translation_patterns = [
            r'直接翻译',
            r'只要翻译',
            r'只需翻译',
            r'仅翻译',
            r'仅需要翻译',
            r'不需要工作流',
            r'不要工作流',
            r'无需工作流',
            r'不用显示工作流',
            r'不显示工作流',
            r'隐藏工作流',
            r'无工作流',
            r'direct.*translate',
            r'just.*translate',
            r'only.*translate',
            r'translate.*only',
            r'without.*workflow',
            r'no.*workflow'
        ]
        
        # 检查是否匹配直接翻译意图
        is_direct_translation_intent = False
        matched_pattern = None
        for pattern in direct_translation_patterns:
            if re.search(pattern, message.lower(), re.IGNORECASE):
                is_direct_translation_intent = True
                matched_pattern = pattern
                logger.info(f"检测到意图: 直接翻译（不显示工作流），匹配模式: '{pattern}'")
                break

        # 意图识别：检测用户是否请求显示上一次翻译的来源
        intent_patterns = [
            r'显示.*上一.*回答.*来源',
            r'显示.*上一.*翻译.*来源',
            r'查看.*上一.*回答.*来源',
            r'查看.*上一.*翻译.*来源',
            r'上一.*回答.*来源.*是什么',
            r'上一.*翻译.*来源.*是什么',
            r'总结.*上一.*回答.*来源',
            r'总结.*上一.*翻译.*来源',
            r'上一.*回答.*引用',
            r'上一.*翻译.*引用',
            r'show.*previous.*translation.*source',
            r'display.*previous.*translation.*source',
            r'show.*last.*translation.*source',
            r'display.*last.*translation.*source',
            r'previous.*translation.*source',
            r'last.*translation.*reference',
        ]
        
        # 检查是否匹配任一意图模式
        is_show_sources_intent = False
        for pattern in intent_patterns:
            if re.search(pattern, message.lower(), re.IGNORECASE):
                is_show_sources_intent = True
                logger.info(f"检测到意图: 显示上一次翻译的来源信息，匹配模式: '{pattern}'")
                break
        
        # 如果是请求显示来源的意图，直接调用相应功能
        if is_show_sources_intent:
            logger.info("转发请求到 show_last_answer_sources_endpoint")
            sources_response = await show_last_answer_sources_endpoint()
            
            # 如果sources_response是一个Response对象，需要提取其内容
            if isinstance(sources_response, Response):
                try:
                    sources_content = sources_response.body.decode('utf-8')
                    sources_data = json.loads(sources_content)
                    return sources_data
                except Exception as e:
                    logger.error(f"处理来源响应时出错: {e}")
                    return sources_response
            
            # 如果已经是一个字典或其他直接可返回的数据
            return sources_response
        
        # 检测文本中是否包含中文或英文字符
        is_chinese_char = any('\u4e00' <= char <= '\u9fff' for char in message)
        is_english_char = any('a' <= char.lower() <= 'z' for char in message)
        
        # 基于文本内容的自动语言检测结果
        detected_source_lang = None
        detected_target_lang = None
        
        if is_chinese_char and not is_english_char:
            detected_source_lang = 'zh'
            detected_target_lang = 'en'
            logger.info(f"自动检测结果: 输入语言为中文 (zh), 目标语言设定为英文 (en)")
        elif is_english_char and not is_chinese_char:
            detected_source_lang = 'en'
            detected_target_lang = 'zh'
            logger.info(f"自动检测结果: 输入语言为英文 (en), 目标语言设定为中文 (zh)")
        else: # 混合或无法明确判断
            # 统计中文字符和英文字符的数量，选择占比更高的作为源语言
            chinese_count = sum(1 for char in message if '\u4e00' <= char <= '\u9fff')
            english_count = sum(1 for char in message if 'a' <= char.lower() <= 'z')
            
            if chinese_count > english_count:
                detected_source_lang = 'zh'
                detected_target_lang = 'en'
                logger.info(f"自动检测结果: 输入语言为混合文本，中文字符占比更高，判定为中文 (zh) -> 英文 (en)")
            else:
                detected_source_lang = 'en'
                detected_target_lang = 'zh'
                logger.info(f"自动检测结果: 输入语言为混合文本，英文字符占比更高或相等，判定为英文 (en) -> 中文 (zh)")

        # 确定最终使用的源语言和目标语言
        actual_source_lang: str
        actual_target_lang: str

        if requested_source_lang and requested_target_lang:
            # 客户端指定了语言，但我们会验证是否与检测结果一致
            if requested_source_lang != detected_source_lang:
                logger.warning(f"警告: 客户端指定的源语言 ({requested_source_lang}) 与自动检测的源语言 ({detected_source_lang}) 不一致")
                # 选择使用检测结果而不是客户端指定的语言
                actual_source_lang = detected_source_lang
                actual_target_lang = detected_target_lang
                logger.info(f"已覆盖客户端指定的语言，使用自动检测的语言: 源语言 {actual_source_lang}, 目标语言 {actual_target_lang}")
            else:
                actual_source_lang = requested_source_lang
                actual_target_lang = requested_target_lang
                logger.info(f"客户端指定的语言与自动检测一致: 源语言 {actual_source_lang}, 目标语言 {actual_target_lang}")
        else:
            # 客户端没有指定语言，使用自动检测的结果
            actual_source_lang = detected_source_lang
            actual_target_lang = detected_target_lang
            logger.info(f"使用自动检测的语言: 源语言 {actual_source_lang}, 目标语言 {actual_target_lang}")

        # 处理消息message，移除特定前缀
        processed_message = message
        if actual_source_lang == 'en' and message.startswith("翻译："):
            processed_message = message[len("翻译："):].lstrip()
            logger.info(f"源语言为英文且检测到中文'翻译：'前缀，已移除。处理后文本: '{processed_message[:100]}...'" )
        elif actual_source_lang == 'zh' and message.lower().startswith("translate:"):
            processed_message = message[len("translate:"):].lstrip()
            logger.info(f"源语言为中文且检测到英文'translate:'前缀，已移除。处理后文本: '{processed_message[:100]}...'" )
        
        # 如果检测到直接翻译意图，预处理文本，移除表达直接翻译意图的部分
        if is_direct_translation_intent and matched_pattern:
            # 移除匹配的模式及其前后可能的标点符号
            processed_message = re.sub(r'[，,：:。.；;]?\s*' + matched_pattern + r'\s*[，,：:。.；;]?\s*', ' ', processed_message, flags=re.IGNORECASE)
            processed_message = processed_message.strip()
            logger.info(f"检测到直接翻译意图，移除相关表述后的文本: '{processed_message[:100]}...'")
        
        translation_type = "terminology" # 默认
        
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        translation_result = None
        services_attempted = []
        
        if DASHSCOPE_AVAILABLE:
            try:
                logger.info("=== 尝试DashScope翻译 ===")
                services_attempted.append("DashScope")
                # 根据用户意图决定是否展示工作流
                translation_result = await dashscope_translate(
                    processed_message, 
                    actual_source_lang, 
                    actual_target_lang,
                    show_workflow=not is_direct_translation_intent  # 如果是直接翻译意图，则不显示工作流
                )
                if translation_result.get("success"):
                    logger.info("✅ DashScope翻译成功!")
                    
                    # 保存完整的翻译输出
                    full_translation_output = translation_result.get('full_workflow') or translation_result.get('translation', '')
                    last_translation_full_output_cache = full_translation_output
                    logger.info(f"已保存完整工作流输出到缓存，长度: {len(full_translation_output)} 字符")
                    
                    if is_direct_translation_intent:
                        # 直接使用翻译结果，不需要额外处理
                        translation_result['translation'] = full_translation_output
                        # 也缓存为最终结果
                        last_translation_result_only_cache = full_translation_output
                        logger.info(f"直接翻译模式：使用纯翻译结果，长度: {len(full_translation_output)} 字符")
                    else:
                        # 带工作流的情况，需要格式化和提取最终译文
                        # 格式化翻译输出，将Markdown格式转换为易读格式，并删除不必要的空格
                        formatted_output = format_translation_output(full_translation_output)
                        
                        # 提取最终译文部分（只包含翻译结果，不包含工作流）
                        final_translation_only = extract_final_translation(full_translation_output)
                        # 缓存最终译文
                        if final_translation_only:
                            last_translation_result_only_cache = final_translation_only
                            logger.info(f"已提取并缓存最终译文，长度: {len(final_translation_only)} 字符")
                        
                        # 使用格式化后的完整输出
                        translation_result['translation'] = formatted_output
                        logger.info(f"使用格式化后的工作流输出，长度: {len(formatted_output)} 字符")
                else:
                    logger.warning(f"❌ DashScope翻译返回失败状态: {translation_result.get('explanation', '无具体错误')}")
                    last_translation_full_output_cache = None 
                    last_translation_result_only_cache = None
            except Exception as e:
                logger.warning(f"❌ DashScope翻译过程中发生严重错误: {e}")
                last_translation_full_output_cache = None 
                last_translation_result_only_cache = None
        
        if not translation_result or not translation_result.get("success"):
            if "Enhanced-Dictionary" not in services_attempted:
                try:
                    logger.info("=== 尝试增强词典翻译 ===")
                    services_attempted.append("Enhanced-Dictionary")
                    translation_result = await enhanced_translate(processed_message, actual_source_lang, actual_target_lang)
                    if translation_result.get("success"):
                        logger.info("✅ 增强词典翻译成功!")
                        # Not updating last_translation_full_output_cache as enhanced_translate lacks detailed workflow
                    else:
                        logger.warning(f"❌ 增强词典翻译未提供有效结果或失败: {translation_result.get('explanation', '无具体错误')}")
                except Exception as e:
                    logger.warning(f"❌ 增强词典翻译过程中发生严重错误: {e}")

        if not translation_result or not translation_result.get("success"):
            logger.error("所有翻译服务尝试均失败或未返回成功结果。")
            last_translation_full_output_cache = None 
            last_translation_result_only_cache = None
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": "翻译失败，所有服务均未能成功处理请求。"
                }
            )
        
        response_data = {
            "code": 0,
            "message": "success",
            "data": {
                "content": translation_result.get('translation', ''), 
                "explanation": translation_result.get('explanation', ''),
                "model_used": translation_result.get('model_used', 'Unknown'),
                "services_attempted": services_attempted,
                "is_direct_translation": is_direct_translation_intent  # 添加标志表明是否是直接翻译模式
            }
        }
        logger.info(f"=== 最终返回结果 ===")
        logger.info(f"翻译 (部分): {response_data['data']['content'][:200]}...") # Log part of content
        logger.info(f"使用模型: {response_data['data']['model_used']}")
        logger.info(f"尝试的服务: {services_attempted}")
        logger.info(f"直接翻译模式: {is_direct_translation_intent}")
        return response_data
        
    except Exception as e:
        logger.error(f"Query endpoint error: {e}", exc_info=True)
        last_translation_full_output_cache = None # Clear cache on any general error in endpoint
        last_translation_result_only_cache = None
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/show_last_answer_sources")
async def show_last_answer_sources_endpoint():
    """
    提取并返回上一次成功翻译（通过DashScope且包含工作流）的知识库来源信息。
    """
    global last_translation_full_output_cache
    logger.info("=== 请求上一回答来源 ===")

    if not last_translation_full_output_cache:
        logger.info("缓存中未找到上一次翻译的详细输出。")
        return JSONResponse(
            status_code=404,
            content={
                "code": -1,
                "message": "上一次翻译的详细输出未找到，无法提取来源。可能尚未进行翻译，或上一次翻译未使用包含工作流的服务，或该服务调用失败。"
            }
        )

    if not DASHSCOPE_AVAILABLE or not translation_service:
        logger.error("DashScope服务不可用，无法执行来源提取。")
        return JSONResponse(
            status_code=503, # Service Unavailable
            content={
                "code": -1,
                "message": "依赖的AI服务不可用，暂时无法提取来源信息。"
            }
        )
        
    # 格式化上一次翻译的详细输出
    formatted_output = format_translation_output(last_translation_full_output_cache)
    
    # It's important that last_translation_full_output_cache contains the part with the workflow.
    # Our prompt for dashscope_translate was designed to output this.
    workflow_text_from_cache = formatted_output

    source_extraction_prompt = f"""# 角色
你是一个文本分析和总结助手，你的任务是从给定的文本中提取并格式化知识库来源信息。

# 任务说明
用户提供了一段由"C-Lingo海关翻译大模型"在其"工作流执行过程"中生成的文本。这段文本描述了模型在翻译时识别的专业术语、它们的翻译以及可能的来源信息（通常在"2.1. 术语拆解与提取"和"2.2. 术语检索与校验"部分）。
请你仔细阅读这段输入的工作流描述文本，提取所有被识别的专业术语及其对应的知识库来源，并严格按照以下指定的格式进行输出。

# 输入的工作流描述文本：
'''
{workflow_text_from_cache}
'''

# 输出格式要求：
（请严格参照以下示例格式进行输出，确保编号、术语、箭头"→"、翻译、换行、缩进以及来源细节的格式完全一致。每个术语条目占两行。）
以下是上一回答中使用的知识库来源明细：

1.  [术语原文1] → [术语翻译1]
    [来源编号/索引1] ([来源名称1]: [来源中关于此术语的具体内容或匹配片段1])
2.  [术语原文2] → [术语翻译2]
    [来源编号/索引2] ([来源名称2]: [来源中关于此术语的具体内容或匹配片段2])
... 等等，列出所有识别到的术语和来源。

# 重要格式细节：
-   列表项以数字加点（例如 "1."）开始。
-   第一行包含：原文术语，空格，右箭头 "→"，空格，翻译后术语。
-   第二行以四个空格缩进开始，然后是来源编号/索引（通常是数字），然后是空格，然后是括号括起来的来源详细信息。
-   来源详细信息格式为："来源名称: 具体内容或匹配片段"。
-   例如，如果工作流描述包含： "提取出核心术语如"非欧盟货物"（non-Union goods）... "非欧盟货物"根据词典测试集[2]对应"non-Union goods"。"
    则输出应类似：
    1.  非欧盟货物 → non-Union goods
        2 (词典测试集: non-Union goods对应"非欧盟货物")

# 指示：
-   仔细分析输入文本中的所有部分，尤其关注"术语拆解与提取"、"术语检索与校验"、"参考知识"等可能包含术语来源的部分。
-   确保提取所有可能的知识来源，包括词典、法规文件、数据库等。
-   如果发现知识库编号（如[1]、[2]等），请一定要包含这些编号。
-   如果输入文本中没有明确的知识来源信息，或者该部分内容为空或不包含可识别的术语来源，请输出："未能在上一次翻译的详细输出中找到可提取的来源信息。"
-   只输出以"以下是上一回答中使用的知识库来源明细："开头的格式化列表，或者上述的"未找到信息"的提示。不要包含任何其他对话、解释或注释。
"""
    
    try:
        logger.info("调用DashScope进行来源提取...")
        # Using chat_single_turn as it's a general purpose call to the model.
        # The prompt is engineered for a specific formatted output.
        extraction_result = await translation_service.chat_single_turn(prompt=source_extraction_prompt)
        
        if extraction_result.get("success"):
            formatted_sources = extraction_result.get("response", "")
            logger.info("✅ 来源提取成功。")
            return { # Returning as a direct object, assuming front-end will render it.
                "code": 0,
                "message": "success",
                "data": {
                    "content": formatted_sources,
                    "formatted_sources": formatted_sources,
                    "model_used": "DashScope-Knowledge-Extraction"
                }
            }
        else:
            logger.error(f"❌ 来源提取失败: {extraction_result.get('error', '未知错误')}")
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": f"提取来源信息失败: {extraction_result.get('error', 'AI服务未能处理请求')}"
                }
            )
    except Exception as e:
        logger.error(f"调用来源提取服务时发生严重错误: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误导致来源提取失败: {str(e)}"
            }
        )

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """对话端点 - 支持单轮和多轮对话"""
    global last_translation_full_output_cache
    global last_translation_result_only_cache
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
        
        # 检测用户是否希望直接展示最终译文（不显示工作流）
        show_final_translation_patterns = [
            r'直接展示最终译文',
            r'仅展示最终译文',
            r'只展示最终译文',
            r'只显示最终译文',
            r'只要最终译文',
            r'给我最终译文',
            r'只要译文',
            r'仅要译文',
            r'去掉工作流',
            r'不要工作流',
            r'不显示工作流',
            r'only.*final.*translation',
            r'just.*translation',
            r'show.*only.*translation',
            r'without.*workflow'
        ]
        
        # 检查是否匹配直接展示最终译文意图
        is_show_final_translation_intent = False
        for pattern in show_final_translation_patterns:
            if re.search(pattern, request.message.lower(), re.IGNORECASE):
                is_show_final_translation_intent = True
                logger.info(f"检测到意图: 直接展示最终译文，匹配模式: '{pattern}'")
                break
                
        # 如果是请求直接展示最终译文
        if is_show_final_translation_intent:
            logger.info("用户要求直接展示最终译文")
            
            # 检查是否有缓存的最终译文
            if last_translation_result_only_cache:
                logger.info(f"找到缓存的最终译文，长度: {len(last_translation_result_only_cache)} 字符")
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "content": last_translation_result_only_cache,
                        "explanation": "直接展示最终译文（不含工作流）",
                        "model_used": "Cached-Final-Translation",
                        "session_id": request.session_id
                    }
                }
            # 如果没有专门缓存的最终译文，但有完整工作流，尝试提取最终译文
            elif last_translation_full_output_cache:
                logger.info("未找到缓存的最终译文，但找到完整工作流，尝试提取最终译文")
                final_translation = extract_final_translation(last_translation_full_output_cache)
                
                if final_translation:
                    logger.info(f"从完整工作流中提取出最终译文，长度: {len(final_translation)} 字符")
                    # 缓存提取出的最终译文
                    last_translation_result_only_cache = final_translation
                    
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "content": final_translation,
                            "explanation": "从上一次翻译中提取出的最终译文（不含工作流）",
                            "model_used": "Extracted-Final-Translation",
                            "session_id": request.session_id
                        }
                    }
                else:
                    logger.warning("无法从完整工作流中提取出最终译文")
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "content": "抱歉，无法从上一次翻译中提取出最终译文。请尝试使用'直接翻译'重新进行翻译。",
                            "session_id": request.session_id
                        }
                    }
            else:
                logger.warning("未找到任何翻译缓存")
                return {
                    "code": 0,
                    "message": "success",
                    "data": {
                        "content": "抱歉，找不到上一次的翻译结果。请先进行翻译，然后再请求展示最终译文。",
                        "session_id": request.session_id
                    }
                }
        
        # 检测用户消息是否为翻译请求
        translation_prefix_patterns = [
            r'^翻译[：:]\s*',
            r'^translate[：:]\s*',
            r'^translation[：:]\s*'
        ]
        
        is_translation_request = False
        for pattern in translation_prefix_patterns:
            if re.search(pattern, request.message, re.IGNORECASE):
                is_translation_request = True
                logger.info(f"检测到翻译请求前缀，将转发到翻译功能")
                break
        
        # 如果是翻译请求，重定向到翻译功能
        if is_translation_request:
            try:
                logger.info(f"转发翻译请求到翻译功能")
                
                # 直接调用翻译函数，不使用query_endpoint
                # 从消息中去除翻译前缀
                clean_message = request.message
                for pattern in translation_prefix_patterns:
                    clean_message = re.sub(pattern, '', clean_message, flags=re.IGNORECASE)
                
                # 检测语言
                is_chinese_char = any('\u4e00' <= char <= '\u9fff' for char in clean_message)
                is_english_char = any('a' <= char.lower() <= 'z' for char in clean_message)
                
                source_lang = None
                target_lang = None
                
                if is_chinese_char and not is_english_char:
                    source_lang = 'zh'
                    target_lang = 'en'
                    logger.info(f"自动检测结果: 输入语言为中文 (zh), 目标语言设定为英文 (en)")
                elif is_english_char and not is_chinese_char:
                    source_lang = 'en'
                    target_lang = 'zh'
                    logger.info(f"自动检测结果: 输入语言为英文 (en), 目标语言设定为中文 (zh)")
                else:
                    # 统计中文字符和英文字符的数量，选择占比更高的作为源语言
                    chinese_count = sum(1 for char in clean_message if '\u4e00' <= char <= '\u9fff')
                    english_count = sum(1 for char in clean_message if 'a' <= char.lower() <= 'z')
                    
                    if chinese_count > english_count:
                        source_lang = 'zh'
                        target_lang = 'en'
                        logger.info(f"自动检测结果: 输入语言为混合文本，中文字符占比更高，判定为中文 (zh) -> 英文 (en)")
                    else:
                        source_lang = 'en'
                        target_lang = 'zh'
                        logger.info(f"自动检测结果: 输入语言为混合文本，英文字符占比更高或相等，判定为英文 (en) -> 中文 (zh)")
                
                # 调用翻译服务
                translation_result = await dashscope_translate(clean_message, source_lang, target_lang)
                
                if translation_result.get("success"):
                    logger.info("✅ 聊天中的翻译请求成功!")
                    
                    # 保存完整的翻译输出（包含工作流）
                    full_translation_output = translation_result.get('full_workflow') or translation_result.get('translation', '')
                    last_translation_full_output_cache = full_translation_output
                    logger.info(f"已保存完整工作流输出到缓存，长度: {len(full_translation_output)} 字符")
                    
                    # 提取最终译文部分（只包含翻译结果，不包含工作流）
                    final_translation_only = extract_final_translation(full_translation_output)
                    # 缓存最终译文
                    if final_translation_only:
                        last_translation_result_only_cache = final_translation_only
                        logger.info(f"已提取并缓存最终译文，长度: {len(final_translation_only)} 字符")
                    
                    # 格式化翻译输出，将Markdown格式转换为易读格式，并删除不必要的空格
                    formatted_output = format_translation_output(full_translation_output)
                    
                    # 构建响应
                    return {
                        "code": 0,
                        "message": "success",
                        "data": {
                            "content": formatted_output,
                            "explanation": "使用DashScope海关专业翻译模型完成翻译",
                            "model_used": "DashScope-Customs",
                            "services_attempted": ["DashScope"],
                            "session_id": request.session_id
                        }
                    }
                else:
                    # 翻译失败，返回错误信息
                    error_msg = translation_result.get('error', 'DashScope翻译失败')
                    logger.error(f"❌ 聊天中的翻译请求失败: {error_msg}")
                    
                    return JSONResponse(
                        status_code=500,
                        content={
                            "code": -1,
                            "message": f"翻译失败: {error_msg}"
                        }
                    )
            except Exception as e:
                logger.error(f"处理聊天中的翻译请求时出错: {e}", exc_info=True)
                return JSONResponse(
                    status_code=500,
                    content={
                        "code": -1,
                        "message": f"处理翻译请求时出错: {str(e)}"
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

@app.post("/api/memory/create")
async def create_memory_endpoint(request: MemoryRequest):
    """创建长期记忆体端点"""
    try:
        logger.info(f"=== 创建记忆体请求 ===")
        logger.info(f"描述: '{request.description}'")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法创建记忆体"
                }
            )
        
        result = await translation_service.create_memory(
            description=request.description
        )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "memory_id": result.get('memory_id'),
                    "description": result.get('description'),
                    "request_id": result.get('request_id')
                }
            }
            logger.info(f"=== 记忆体创建完成 ===")
            logger.info(f"记忆体ID: {response_data['data']['memory_id']}")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '创建记忆体失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Create memory endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/memory/chat")
async def memory_chat_endpoint(request: MemoryChatRequest):
    """长期记忆对话端点"""
    try:
        logger.info(f"=== 长期记忆对话请求 ===")
        logger.info(f"消息: '{request.message}'")
        logger.info(f"记忆体ID: {request.memory_id}")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not request.message.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "消息内容不能为空"
                }
            )
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法进行长期记忆对话"
                }
            )
        
        result = await translation_service.chat_with_memory(
            prompt=request.message,
            memory_id=request.memory_id,
            context=request.context
        )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "content": result.get('response', ''),
                    "memory_id": result.get('memory_id'),
                    "model_used": result.get('model_used', 'DashScope-Customs')
                }
            }
            logger.info(f"=== 长期记忆对话完成 ===")
            logger.info(f"回答: {response_data['data']['content'][:50]}...")
            logger.info(f"记忆体ID: {response_data['data']['memory_id']}")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '长期记忆对话失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Memory chat endpoint error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "message": f"服务器内部错误: {str(e)}"
            }
        )

@app.post("/api/memory/save")
async def save_memory_endpoint(request: SaveMemoryRequest):
    """保存信息到记忆体端点"""
    try:
        logger.info(f"=== 保存记忆信息请求 ===")
        logger.info(f"信息: '{request.info}'")
        logger.info(f"记忆体ID: {request.memory_id}")
        logger.info(f"DashScope可用: {DASHSCOPE_AVAILABLE}")
        
        if not request.info.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "code": -1,
                    "message": "保存信息不能为空"
                }
            )
        
        if not DASHSCOPE_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={
                    "code": -1,
                    "message": "DashScope服务不可用，无法保存记忆信息"
                }
            )
        
        result = await translation_service.save_memory_info(
            info=request.info,
            memory_id=request.memory_id
        )
        
        if result.get('success'):
            response_data = {
                "code": 0,
                "message": "success",
                "data": {
                    "info": result.get('info'),
                    "memory_id": result.get('memory_id'),
                    "message": result.get('message')
                }
            }
            logger.info(f"=== 记忆信息保存完成 ===")
            logger.info(f"记忆体ID: {response_data['data']['memory_id']}")
            return response_data
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": -1,
                    "message": result.get('error', '保存记忆信息失败')
                }
            )
        
    except Exception as e:
        logger.error(f"Save memory endpoint error: {e}", exc_info=True)
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

# 提取最终翻译结果的函数
def extract_final_translation(text: str) -> Optional[str]:
    """
    从完整的翻译工作流中提取最终译文部分
    
    Args:
        text (str): 完整的翻译工作流文本
        
    Returns:
        Optional[str]: 提取出的最终译文，如果未找到则返回None
    """
    if not text:
        return None
    
    # 尝试多种可能的最终译文标记
    final_translation_markers = [
        r'## 7\.\s+最终译文',
        r'## 7[\.、]\s*最终译文',
        r'##\s*7[\.、]?\s*最终译文',
        r'# 7[\.、]?\s*最终译文',
        r'7[\.、]\s*最终译文',
        r'最终译文[:：]',
        r'最终翻译[:：]',
        r'Final Translation[:：]',
    ]
    
    for marker in final_translation_markers:
        match = re.search(marker, text, re.IGNORECASE)
        if match:
            # 找到标记后的文本
            start_pos = match.end()
            
            # 查找下一个标题（以#开头的行）或文本结束
            next_title_match = re.search(r'\n\s*#', text[start_pos:])
            if next_title_match:
                end_pos = start_pos + next_title_match.start()
                final_translation = text[start_pos:end_pos].strip()
            else:
                # 如果没有下一个标题，取到文本结束
                final_translation = text[start_pos:].strip()
            
            # 如果提取的文本过短，可能是提取错误，尝试下一个标记
            if len(final_translation) < 5:
                continue
                
            return final_translation
    
    # 如果所有标记都未匹配，尝试寻找最后一个段落作为译文
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if paragraphs and len(paragraphs[-1]) > 10:  # 确保段落不是太短
        return paragraphs[-1]
    
    return None

if __name__ == "__main__":
    import uvicorn
    logger.info("启动海关翻译服务...")
    uvicorn.run(app, host="0.0.0.0", port=3005) 