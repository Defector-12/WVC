import axios from 'axios';
import { PromptService } from './promptService.js';

// 翻译服务 - 通过HTTP请求Python后端
export class TranslationService {
    constructor() {
        // 可以根据需要设置后端API地址
        this.apiBase = process.env.PY_API_BASE || 'http://localhost:3005';
    }

    async translate(message, sourceLang = 'zh', targetLang = 'en') {
        try {
            const res = await axios.post(`${this.apiBase}/api/query`, {
                message,
                sourceLang,
                targetLang
            });
            return res.data;
        } catch (error) {
            console.error('翻译服务错误:', error);
            throw new Error(`翻译失败: ${error.message}`);
        }
    }
}
