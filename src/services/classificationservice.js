import axios from 'axios';

// 商品归类服务 - 通过HTTP请求Python后端
export class ClassificationService {
    constructor() {
        this.apiBase = process.env.PY_API_BASE || 'http://localhost:3005';
    }

    // 商品归类查询
    async classifyProduct(productInfo) {
        try {
            const res = await axios.post(`${this.apiBase}/api/query`, {
                message: JSON.stringify(productInfo),
                type: 'classification'
            });
            return {
                classification: res.data?.data?.content,
                sessionId: res.data?.data?.session_id
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