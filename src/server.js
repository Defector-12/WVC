import dotenv from 'dotenv';
import express from 'express';
import cors from 'cors';
import { MODEL_CONFIG } from './config/model.js';
import fetch from 'node-fetch';
import path from 'path';
import { fileURLToPath } from 'url';
import { TranslationService } from './services/translationservice.js';
import fileUpload from 'express-fileupload';
import { logMessage } from './utils/logger.js';
import { retryOperation } from './utils/retry.js';
import {diskStorage} from "multer";

// 加载环境变量
dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 环境变量检查
const checkEnvironment = () => {
    const requiredVars = ['NODE_ENV', 'PORT'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
        console.error(`[${new Date().toISOString()}] [error] 缺少必要的环境变量: ${missingVars.join(', ')}`);
        process.env.PORT = process.env.PORT || '3003';
        process.env.NODE_ENV = process.env.NODE_ENV || 'production';
    }
   
    console.log(`[${new Date().toISOString()}] [info] 环境变量配置: NODE_ENV=${process.env.NODE_ENV}, PORT=${process.env.PORT}`);
};

// 执行一次环境变量检查
checkEnvironment();

// 创建 Express 应用
const app = express();

// 检查环境变量
logMessage('环境变量检查:', {
    VIVO_APP_ID: process.env.VIVO_APP_ID,
    VIVO_APP_KEY: process.env.VIVO_APP_KEY ? '已设置' : '未设置'
});

// 配置CORS
app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Accept'],
    credentials: true
}));

// 文件上传中间件
app.use(fileUpload({
    createParentPath: true,
    limits: { 
        fileSize: 10 * 1024 * 1024 // 10MB
    },
    abortOnLimit: true
}));

// 请求体解析
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 静态文件服务
app.use(express.static(path.join(__dirname, '..')));
app.use('/styles', express.static(path.join(__dirname, '../styles')));
app.use('/assets', express.static(path.join(__dirname, '../assets')));
app.use('/src', express.static(path.join(__dirname)));

// 请求日志中间件
app.use((req, res, next) => {
    logMessage(`收到请求: ${req.method} ${req.url}`);
    next();
});

// 错误处理中间件
app.use((err, req, res, next) => {
    logMessage(`服务器错误: ${err.stack}`, 'error');
    res.status(500).json({
        error: '服务器内部错误',
        output: { text: '服务器内部错误，请稍后重试' }
    });
});

// 请求超时设置
const REQUEST_TIMEOUT = 60000; // 60秒

// 通用的模型调用函数
async function callModel(req, res) {
    const requestTimer = setTimeout(() => {
        logMessage('请求超时', 'error');
        throw new Error('Request timeout');
    }, REQUEST_TIMEOUT);

    try {
        let inputText = '';
        const type = req.body.type; // 从请求体中获取类型
        
        // 获取语言参数
        const sourceLang = req.body.sourceLang || 'zh';
        const targetLang = req.body.targetLang || 'en';
        
        logMessage(`语言参数: ${sourceLang} -> ${targetLang}`);
        
        // 获取输入文本
        if (req.body.message) {
            inputText = req.body.message;
        } else if (req.files && req.files.file) {
            // 处理文件上传
            const file = req.files.file;
            inputText = file.data.toString('utf8');
        } else if (req.body.text) {
            inputText = req.body.text;
        }

        if (!inputText) {
            logMessage('请求缺少输入文本', 'warn');
            throw new Error('请提供输入文本或文件');
        }

        // 创建翻译服务实例并使用重试机制
        const translationService = new TranslationService();
        logMessage(`开始处理${type}请求: ${inputText.substring(0, 100)}...`);

        const result = await retryOperation(async () => {
            // 传递语言参数给翻译服务
            const response = await translationService.startTranslationSession(
                inputText, 
                type, 
                sourceLang, 
                targetLang
            );
            if (!response || !response.translation) {
                throw new Error('无法获取有效响应');
            }
            return response.translation;
        });

        logMessage('请求处理完成');
        clearTimeout(requestTimer);
        return result;
    } catch (error) {
        clearTimeout(requestTimer);
        logMessage(`模型调用错误: ${error.message}`, 'error');
        throw error;
    }
}

// API端点配置
app.post('/api/query', async (req, res) => {
    const responseTimer = setTimeout(() => {
        if (!res.headersSent) {
            res.status(504).json({
                code: 504,
                msg: '请求超时',
                data: {
                    content: '处理请求时超时，请稍后重试'
                }
            });
        }
    }, REQUEST_TIMEOUT);

    try {
        const type = req.body.type;
        if (!type) {
            clearTimeout(responseTimer);
            return res.status(400).json({ 
                code: 400,
                msg: '缺少type参数',
                data: {
                    content: '请提供请求类型'
                }
            });
        }

        // 处理请求
        const result = await callModel(req, res);
        
        clearTimeout(responseTimer);
        if (!res.headersSent) {
            res.json({
                code: 0,
                msg: 'success',
                data: {
                    content: result || '处理完成',
                    sessionId: req.body.sessionId || null,
                    requestId: req.body.requestId || null
                }
            });
        }
    } catch (error) {
        clearTimeout(responseTimer);
        logMessage('API错误', 'error', error);
        if (!res.headersSent) {
            res.status(500).json({
                code: 500,
                msg: error.message,
                data: {
                    content: '处理请求时发生错误'
                }
            });
        }
    }
});

// 健康检查端点
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 优雅关闭服务器
process.on('SIGTERM', () => {
    console.log(`[${new Date().toISOString()}] [info] 收到 SIGTERM 信号，准备关闭服务器...`);
    app.close(() => {
        console.log(`[${new Date().toISOString()}] [info] 服务器已安全关闭`);
        process.exit(0);
    });
});

// 启动服务器
const server = app.listen(process.env.PORT || 3003, '0.0.0.0', () => {
    console.log(`[${new Date().toISOString()}] [info] 服务器运行在端口 ${server.address().port}`);
    console.log(`[${new Date().toISOString()}] [info] 翻译服务使用 VivoGPT（蓝心大模型）`);
}).on('error', (err) => {
    console.error(`[${new Date().toISOString()}] [error] 服务器启动失败:`, err.message);
});