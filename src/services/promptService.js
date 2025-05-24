// 提示词生成服务
export class PromptService {
    // 语言映射表
    static languageMap = {
        'zh': '中文',
        'en': '英文',
        'ja': '日文',
        'ko': '韩文',
        'fr': '法文',
        'de': '德文',
        'es': '西班牙文',
        'ru': '俄文'
    };

    static basePrompts = {
        'classification': "作为海关商品归类专家，请对以下商品进行HS编码归类并说明理由：",
        'valuation': "作为海关估价专家，请对以下商品进行估价分析并提供合理建议：",
        'customs-consulting': "作为海关业务咨询专家，请针对以下问题提供专业的解答和建议："
    };

    /**
     * 生成提示词
     * @param {string} query - 用户输入的文本
     * @param {string} type - 请求类型（'terminology', 'classification', 'valuation', 'customs-consulting'）
     * @param {string} fileContent - 文件内容（可选）
     * @param {string} sourceLang - 源语言代码（可选）
     * @param {string} targetLang - 目标语言代码（可选）
     * @returns {string} 生成的提示词
     */
    static generatePrompt(query, type, fileContent = null, sourceLang = 'zh', targetLang = 'en') {
        let prompt = '';
        
        if (type === 'terminology') {
            // 动态生成翻译提示词
            const sourceLanguage = this.languageMap[sourceLang] || '中文';
            const targetLanguage = this.languageMap[targetLang] || '英文';
            
            // 使用通用翻译提示词，不限制为海关术语
            prompt = `你是专业的翻译专家。请将以下${sourceLanguage}文本翻译成${targetLanguage}。

要求：
1. 只输出${targetLanguage}翻译结果
2. 不要输出${sourceLanguage}原文
3. 不要添加任何解释或注释
4. 保持翻译的准确性和自然性

需要翻译的${sourceLanguage}文本：`;
            
            console.log(`生成通用翻译提示词: ${sourceLanguage} → ${targetLanguage}`);
        } else {
            prompt = this.basePrompts[type] || "请回答以下问题：";
        }
        
        if (fileContent) {
            prompt += `\n文件内容：\n${fileContent}\n`;
        }
        
        if (query) {
            prompt += `\n${query}`;
        }
        
        console.log('最终生成的提示词:', prompt);
        return prompt;
    }

    static getTranslationExample(sourceLang, targetLang) {
        // 提供更强制性的翻译示例来指导模型正确理解任务
        const examples = {
            'en_zh': [
                { source: 'Certificate of Origin', target: '原产地证书' },
                { source: 'Customs Declaration', target: '海关申报单' },
                { source: 'Import License', target: '进口许可证' }
            ],
            'zh_en': [
                { source: '原产地证书', target: 'Certificate of Origin' },
                { source: '海关申报单', target: 'Customs Declaration' },
                { source: '进口许可证', target: 'Import License' }
            ],
            'en_ja': [
                { source: 'Certificate of Origin', target: '原産地証明書' },
                { source: 'Customs Declaration', target: '税関申告書' }
            ],
            'zh_ja': [
                { source: '原产地证书', target: '原産地証明書' },
                { source: '海关申报单', target: '税関申告書' }
            ]
        };
        
        const exampleKey = `${sourceLang}_${targetLang}`;
        const exampleList = examples[exampleKey];
        
        if (exampleList && exampleList.length > 0) {
            let exampleText = '';
            exampleList.forEach((example, index) => {
                exampleText += `输入：${example.source}\n输出：${example.target}\n`;
                if (index < exampleList.length - 1) exampleText += '\n';
            });
            return exampleText;
        }
        
        // 如果没有具体示例，使用通用的强制性说明
        const sourceLanguage = this.languageMap[sourceLang] || '源语言';
        const targetLanguage = this.languageMap[targetLang] || '目标语言';
        
        return `输入：[${sourceLanguage}文本]
输出：[对应的${targetLanguage}翻译]

注意：输出必须完全是${targetLanguage}，绝对不能包含${sourceLanguage}原文！`;
    }
} 