import { VivoGPTService } from '../../vivogpt.js';

// 商品归类服务
export class ClassificationService {
    constructor() {
        this.vivoGPT = new VivoGPTService();
    }

    // 商品归类查询
    async classifyProduct(productInfo) {
        try {
            // 构建提示词
            const prompt = `请根据以下商品信息进行海关商品归类：\n${JSON.stringify(productInfo, null, 2)}`;

            const result = await this.vivoGPT.callModel(prompt);
            
            return {
                classification: result.content,
                sessionId: result.sessionId
            };
        } catch (error) {
            console.error('商品归类服务错误:', error);
            throw new Error(`商品归类失败: ${error.message}`);
        }
    }

    // 批量商品归类
    async batchClassifyProducts(products) {
        const results = [];
        for (const product of products) {
            try {
                const result = await this.classifyProduct(product);
                results.push({
                    product: product,
                    classification: result.classification,
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