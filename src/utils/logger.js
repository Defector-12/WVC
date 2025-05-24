import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 创建日志目录
const logDir = path.join(__dirname, '..', '..', 'logs');
if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir);
}

// 日志文件路径
const logFile = path.join(logDir, 'app.log');

/**
 * 记录日志消息
 * @param {string} message - 日志消息
 * @param {string} level - 日志级别 ('info', 'warn', 'error')
 * @param {any} data - 附加数据
 */
export const logMessage = (message, level = 'info', data = null) => {
    const timestamp = new Date().toISOString();
    let logString = `[${timestamp}] [${level}] ${message}`;
    
    if (data) {
        if (typeof data === 'object') {
            logString += ': ' + JSON.stringify(data, null, 2);
        } else {
            logString += ': ' + data;
        }
    }
    
    console.log(logString);
}; 