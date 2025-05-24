import { MODEL_CONFIG } from './src/config/model.js';
import fetch from 'node-fetch';
import { genSignHeaders } from './auth_util.js';
import crypto from 'crypto';

// 蓝心大模型服务
export class VivoGPTService {
    constructor() {
        this.config = MODEL_CONFIG.vivoAPI;
    }

    // 调用蓝心大模型
    async callModel(prompt, taskType = 'general') {
        try {
            console.log(`\n--- VivoGPT API调用开始 ---`);
            console.log(`任务类型: ${taskType}`);
            console.log(`输入提示词长度: ${prompt.length} 字符`);
            console.log(`配置检查 - appId: ${this.config.appId}, appKey: ${this.config.appKey ? '已设置' : '未设置'}`);
            
            // 生成请求ID和会话ID
            const requestId = crypto.randomUUID();
            const sessionId = crypto.randomUUID();
            const params = { requestId };

            // 生成签名头部
            const headers = genSignHeaders(
                this.config.appId,
                this.config.appKey,
                'POST',
                this.config.uri,
                params
            );

            // 添加内容类型头部
            headers['Content-Type'] = 'application/json';

            // 根据任务类型设置不同的温度
            let temperature = 0.9;  // 默认温度
            if (taskType === 'terminology') {
                temperature = 0.1;  // 翻译任务使用低温度，确保准确性
            }

            // 打印配置信息用于调试
            console.log('API配置:', {
                domain: this.config.domain,
                uri: this.config.uri,
                appId: this.config.appId,
                appKey: this.config.appKey ? this.config.appKey.substring(0, 8) + '...' : '未设置',
                model: this.config.model,
                requestId,
                sessionId,
                temperature,
                taskType
            });

            // 构建请求体
            const requestBody = {
                model: this.config.model,
                prompt: prompt,
                sessionId: sessionId,
                extra: {
                    temperature: temperature
                }
            };

            console.log('完整请求体:', JSON.stringify(requestBody, null, 2));
            console.log('请求头部:', headers);

            // 发送请求
            const apiUrl = `https://${this.config.domain}${this.config.uri}?${new URLSearchParams(params)}`;
            console.log(`请求URL: ${apiUrl}`);
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers,
                body: JSON.stringify(requestBody)
            });

            const responseText = await response.text();
            console.log(`HTTP状态码: ${response.status}`);
            console.log('API原始响应:', responseText);

            if (!response.ok) {
                console.error('API响应错误:', {
                    status: response.status,
                    statusText: response.statusText,
                    responseText
                });
                throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
            }

            const data = JSON.parse(responseText);
            console.log('解析后的响应数据:', JSON.stringify(data, null, 2));
            
            if (data.code !== 0) {
                console.error(`API返回错误代码: ${data.code}, 消息: ${data.msg}`);
                throw new Error(data.msg || '模型调用失败');
            }

            const result = {
                content: data.data.content,
                sessionId: data.data.sessionId,
                requestId: data.data.requestId
            };
            
            console.log(`提取的内容: "${result.content}"`);
            console.log(`--- VivoGPT API调用结束 ---\n`);
            
            return result;
        } catch (error) {
            console.error('VivoGPT模型调用错误:', error);
            throw new Error(`模型调用失败: ${error.message}`);
        }
    }
}
