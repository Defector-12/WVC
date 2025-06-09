import axios from 'axios';

// 海关估价服务 - 通过HTTP请求Python后端
export class ValuationService {
    constructor() {
        this.apiBase = process.env.PY_API_BASE || 'http://localhost:3005';
    }

    // 海关估价查询
    async getValuation(productInfo) {
        try {
            const res = await axios.post(`${this.apiBase}/api/query`, {
                message: JSON.stringify(productInfo),
                type: 'valuation'
            });
            return {
                valuation: res.data?.data?.content,
                sessionId: res.data?.data?.session_id
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