# 海关专业翻译系统 - API配置说明

## 环境变量配置

为了确保系统正常运行，请按以下方式配置环境变量：

### 1. DashScope API配置 (主要翻译模型)

```bash
# 阿里云DashScope API密钥
export DASHSCOPE_API_KEY="sk-f8dcf20a07ac4b889d74f56b7bf654e7"

# 海关专业翻译模型ID
export DASHSCOPE_MODEL_ID="43f10f032fce4a52b8c40e3eb5a01c5d"
```

### 2. VIVO蓝心大模型配置 (备用模型)

```bash
# VIVO应用ID
export VIVO_APP_ID="2025880184"

# VIVO应用密钥
export VIVO_APP_KEY="giowHrLPbUvQfPtD"
```

### 3. 系统配置

```bash
# 服务器端口
export PORT=8000

# 服务器主机
export HOST="0.0.0.0"

# 日志级别
export LOG_LEVEL="INFO"

# 最大缓存大小
export MAX_CACHE_SIZE=1000
```

## 快速启动

### 1. 安装依赖

```bash
# Python依赖
pip install -r requirements.txt

# Node.js依赖
npm install
```

### 2. 配置环境变量

在系统中设置上述环境变量，或创建 `.env` 文件：

```bash
# Linux/macOS
source ./set_env.sh

# Windows
set_env.bat
```

### 3. 启动服务

```bash
# 启动Python后端服务
python vivogpt.py

# 或使用uvicorn
uvicorn vivogpt:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问服务

打开浏览器访问: http://localhost:8000

## API使用说明

### 翻译API

**端点:** `POST /api/query`

**请求体:**
```json
{
    "type": "terminology",
    "message": "待翻译的海关术语",
    "sourceLang": "zh",
    "targetLang": "en"
}
```

**响应格式:**
```json
{
    "code": 0,
    "data": {
        "content": "翻译结果",
        "explanation": "术语解释（可选）",
        "model_used": "DashScope",
        "sessionId": "会话ID",
        "requestId": "请求ID"
    }
}
```

### 模型优先级

1. **术语翻译**: 优先使用DashScope专业海关翻译模型
2. **模型回退**: 如果DashScope不可用，自动切换到VIVO蓝心大模型
3. **其他功能**: 商品归类、估价、咨询等使用VIVO蓝心大模型

## 故障排除

### 常见问题

1. **DashScope API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 查看日志中的错误信息

2. **VIVO模型调用失败**
   - 检查应用ID和密钥配置
   - 确认API限制和配额

3. **服务启动失败**
   - 检查端口是否被占用
   - 确认依赖包安装完整

### 日志查看

系统日志会输出详细的API调用信息，包括：
- 使用的模型类型
- 请求处理时间
- 错误信息和回退情况

## 模型性能

### DashScope专业翻译模型
- **优势**: 专门针对海关领域训练，术语翻译准确率高
- **适用**: 海关术语翻译、专业文档翻译
- **限制**: 仅支持翻译功能

### VIVO蓝心大模型
- **优势**: 通用能力强，支持多种任务类型
- **适用**: 咨询问答、商品归类、估价分析
- **限制**: QPS限制为2，需要合理控制请求频率

## 技术支持

如有技术问题，请查看：
1. 项目日志文件
2. API文档和错误代码
3. 相关模型服务商的官方文档 