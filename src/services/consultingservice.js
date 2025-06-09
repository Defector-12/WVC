import axios from 'axios';

// 关务咨询服务 - 通过HTTP请求Python后端
export class ConsultingService {
    constructor() {
        this.apiBase = process.env.PY_API_BASE || 'http://localhost:3005';
    }

    // 开始咨询会话
    async startConsultation(question) {
        try {
            const res = await axios.post(`${this.apiBase}/api/chat`, {
                message: question
            });
            return {
                answer: res.data?.data?.content,
                sessionId: res.data?.data?.session_id
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
            const res = await axios.post(`${this.apiBase}/api/chat`, {
                message: question,
                session_id: sessionId
            });
            return {
                answer: res.data?.data?.content,
                sessionId: res.data?.data?.session_id
            };
        } catch (error) {
            console.error('关务咨询服务错误:', error);
            throw new Error(`咨询失败: ${error.message}`);
        }
    }
}