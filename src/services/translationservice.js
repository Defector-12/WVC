import { VivoGPTService } from '../../vivogpt.js';
import { PromptService } from './promptService.js';

// 翻译服务 - 直接使用VivoGPT
export class TranslationService {
    constructor() {
        this.vivoGPT = new VivoGPTService();
    }

    // 开始翻译会话
    async startTranslationSession(text, type = 'terminology', sourceLang = 'zh', targetLang = 'en') {
        try {
            console.log(`\n=== 翻译服务开始 ===`);
            console.log(`输入文本: "${text}"`);
            console.log(`翻译类型: ${type}`);
            console.log(`源语言: ${sourceLang} → 目标语言: ${targetLang}`);
            
            // 生成提示词
            const prompt = PromptService.generatePrompt(text, type, null, sourceLang, targetLang);
            console.log(`生成的完整提示词: "${prompt}"`);
            
            // 直接使用VivoGPT翻译
            console.log('调用VivoGPT服务...');
            const result = await this.vivoGPT.callModel(prompt, type);
            console.log('VivoGPT翻译成功:', result);
            console.log(`翻译结果: "${result.content}"`);
            console.log(`=== 翻译服务结束 ===\n`);
            
            return {
                translation: result.content,
                sessionId: result.sessionId,
                apiUsed: 'vivo'
            };
        } catch (error) {
            console.error('翻译服务失败:', error);
            throw new Error(`翻译失败: ${error.message}`);
        }
    }

    // 继续翻译会话
    async continueTranslation(text, sessionId, type = 'terminology', sourceLang = 'zh', targetLang = 'en') {
        if (!sessionId) {
            throw new Error('会话ID不能为空');
        }
        try {
            const prompt = PromptService.generatePrompt(text, type, null, sourceLang, targetLang);
            
            // 直接使用VivoGPT翻译
            const result = await this.vivoGPT.callModel(prompt, type);
            return {
                translation: result.content,
                sessionId: result.sessionId,
                apiUsed: 'vivo'
            };
        } catch (error) {
            console.error('翻译服务错误:', error);
            throw new Error(`翻译失败: ${error.message}`);
        }
    }
}
