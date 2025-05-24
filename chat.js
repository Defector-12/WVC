/**
 * 海关专业翻译聊天处理模块
 * 提供与后端API的通信功能，支持DashScope和VIVO双模型
 */

// 发送消息的异步函数，处理与后端的通信和响应
const handleSend = async function() {
    try {
        // 构建请求体，支持多语言翻译
        const requestBody = {
            type: 'terminology',  // 默认为术语翻译
            message: this.message,
            sourceLang: this.sourceLang || 'zh',  // 源语言，默认中文
            targetLang: this.targetLang || 'en'   // 目标语言，默认英文
        };

        console.log('发送翻译请求:', requestBody);

        // 发送POST请求到统一API端点
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        // 检查HTTP响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 解析响应数据
        const data = await response.json();
        
        // 验证响应格式
        if (!data || data.code !== 0 || !data.data || !data.data.content) {
            throw new Error('无效的响应格式或翻译失败');
        }

        // 记录使用的模型信息
        const modelUsed = data.data.model_used || 'Unknown';
        console.log(`翻译完成，使用模型: ${modelUsed}`);
        
        // 处理翻译结果
        const translationResult = data.data.content;
        const explanation = data.data.explanation;
        
        // 构建显示内容
        let displayContent = translationResult;
        if (explanation) {
            displayContent += `\n\n解释: ${explanation}`;
        }
        
        // 添加模型信息标记
        displayContent += `\n\n[使用模型: ${modelUsed}]`;
        
        // 将结果添加到聊天界面
        this.addMessage('assistant', displayContent);
        
        // 清空输入框
        this.message = '';
        
    } catch (error) {
        console.error('翻译请求错误:', error);
        
        // 显示友好的错误消息
        const errorMessage = error.message || '发送消息时发生未知错误';
        this.showError(`翻译失败: ${errorMessage}`);
    }
}

// 导出函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { handleSend };
} 