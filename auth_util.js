import crypto from 'crypto';

// 生成随机字符串
function genNonce(length = 8) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 生成规范的查询字符串
function genCanonicalQueryString(params) {
    if (!params || Object.keys(params).length === 0) {
        return '';
    }
    
    return Object.keys(params)
        .sort()
        .map(key => {
            return `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`;
        })
        .join('&');
}

// 生成签名
function genSignature(appSecret, signingString) {
    // 将密钥转换为UTF-8编码的Buffer
    const secretBuffer = Buffer.from(appSecret, 'utf-8');
    // 确保签名字符串是Buffer
    const signingBuffer = Buffer.from(signingString, 'utf-8');
    
    // 创建HMAC对象
    const hmac = crypto.createHmac('sha256', secretBuffer);
    hmac.update(signingBuffer);
    
    // 获取签名并进行Base64编码
    return hmac.digest('base64');
}

// 生成签名头部
function genSignHeaders(appId, appKey, method, uri, query) {
    method = method.toUpperCase();
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const nonce = genNonce();
    const canonicalQueryString = genCanonicalQueryString(query);
    
    // 构建签名头部字符串
    const signedHeadersString = [
        `x-ai-gateway-app-id:${appId}`,
        `x-ai-gateway-timestamp:${timestamp}`,
        `x-ai-gateway-nonce:${nonce}`
    ].join('\n');
    
    // 构建签名字符串
    const signingString = [
        method,
        uri,
        canonicalQueryString,
        appId,
        timestamp,
        signedHeadersString
    ].join('\n');
    
    // 生成签名
    const signature = genSignature(appKey, signingString);
    
    // 返回所有必要的头部
    return {
        'X-AI-GATEWAY-APP-ID': appId,
        'X-AI-GATEWAY-TIMESTAMP': timestamp,
        'X-AI-GATEWAY-NONCE': nonce,
        'X-AI-GATEWAY-SIGNED-HEADERS': 'x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce',
        'X-AI-GATEWAY-SIGNATURE': signature
    };
}

export { genSignHeaders };