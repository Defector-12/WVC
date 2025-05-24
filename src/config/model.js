export const MODEL_CONFIG = {
    // 蓝心大模型配置 - 唯一翻译服务
    vivoAPI: {
        appId: process.env.VIVO_APP_ID || '2025880184',
        appKey: process.env.VIVO_APP_KEY || 'giowHrLPbUvQfPtD',
        uri: '/vivogpt/completions',
        domain: 'api-ai.vivo.com.cn',
        model: 'vivo-BlueLM-TB-Pro',
        method: 'POST',
        enabled: true
    },

    // 各功能模块的特定配置
    translation: {
        temperature: 0.1  // 翻译使用极低温度确保准确性
    },
    consulting: {
        temperature: 0.8
    },
    classification: {
        temperature: 0.7
    },
    valuation: {
        temperature: 0.7
    }
};