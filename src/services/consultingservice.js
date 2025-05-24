import { VivoGPTService } from '../../vivogpt.js';

// 关务咨询服务
export class ConsultingService {
    constructor() {
        this.vivoGPT = new VivoGPTService();
    }

    // 开始咨询会话
    async startConsultation(question) {
        try {
            // 构建提示词
            const prompt = `请回答以下关务咨询问题：\n${question}`;

            const result = await this.vivoGPT.callModel(prompt);
            
            return {
                answer: result.content,
                sessionId: result.sessionId
            };
        } catch (error) {
            console.error('关务咨询服务错误:', error);
            throw new Error(`咨询失败: ${error.message}`);
        }
    }

    // 继续咨询会话
    async continueConsultation(question, sessionId) {
        if (!sessionId) {
            throw new Error('会话ID不能为空');
        }
        try {
            const result = await this.vivoGPT.callModel(question);
            
            return {
                answer: result.content,
                sessionId: result.sessionId
            };
        } catch (error) {
            console.error('关务咨询服务错误:', error);
            throw new Error(`咨询失败: ${error.message}`);
        }
    }
}