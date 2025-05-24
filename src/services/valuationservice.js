import { VivoGPTService } from '../../vivogpt.js';

// 海关估价服务
export class ValuationService {
    constructor() {
        this.vivoGPT = new VivoGPTService();
    }

    // 海关估价查询
    async getValuation(productInfo) {
        try {
            // 构建提示词
            const prompt = `请根据以下商品信息进行海关估价分析：\n${JSON.stringify(productInfo, null, 2)}`;

            const result = await this.vivoGPT.callModel(prompt);
            
            return {
                valuation: result.content,
                sessionId: result.sessionId
            };
        } catch (error) {
            console.error('海关估价服务错误:', error);
            throw new Error(`估价失败: ${error.message}`);
        }
    }

    // 批量估价查询
    async batchValuation(products) {
        const results = [];
        for (const product of products) {
            try {
                const result = await this.getValuation(product);
                results.push({
                    product: product,
                    valuation: result.valuation,
                    success: true
                });
            } catch (error) {
                results.push({
                    product: product,
                    error: error.message,
                    success: false
                });
            }
        }
        return results;
    }
}