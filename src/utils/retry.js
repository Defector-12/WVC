import { logMessage } from './logger.js';

/**
 * 重试操作函数
 * @param {Function} operation - 要重试的异步操作
 * @param {number} maxRetries - 最大重试次数
 * @param {number} delay - 重试之间的延迟时间（毫秒）
 * @returns {Promise<any>} - 操作结果
 * @throws {Error} - 如果所有重试都失败则抛出错误
 */
const retryOperation = async (operation, maxRetries = 3, delay = 1000) => {
    let lastError;
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;
            logMessage(`操作失败，尝试第 ${attempt} 次重试，错误: ${error.message}`, 'warn');
            if (attempt < maxRetries) {
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw new Error(`操作在 ${maxRetries} 次尝试后失败: ${lastError.message}`);
};

export { retryOperation }; 