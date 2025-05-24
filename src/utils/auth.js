import crypto from 'crypto';

// 生成随机字符串
function generateRandomString(length = 8) {
    const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 生成规范的查询字符串
function generateCanonicalQueryString(queryParams) {
    if (!queryParams || Object.keys(queryParams).length === 0) {
        return '';
    }

    return Object.keys(queryParams)
        .sort()
        .map(key => {
            const encodedKey = encodeURIComponent(key);
            const encodedValue = encodeURIComponent(String(queryParams[key]));
            return `${encodedKey}=${encodedValue}`;
        })
        .join('&');
}

// 生成签名
function generateSignature(appKey, signingString) {
    try {
        const hmac = crypto.createHmac('sha256', appKey);
        hmac.update(signingString);
        return hmac.digest('base64');
    } catch (err) {
        console.error('create sign exception', err);
        return '';
    }
}

// 生成签名头部
export function generateSignHeaders(appId, appKey, method, uri, queryParams) {
    const nonce = generateRandomString(8);
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const canonicalQueryString = generateCanonicalQueryString(queryParams);

    const signedHeadersString = `x-ai-gateway-app-id:${appId}\nx-ai-gateway-timestamp:${timestamp}\nx-ai-gateway-nonce:${nonce}`;
    
    const signingString = [
        method,
        uri,
        canonicalQueryString,
        appId,
        timestamp,
        signedHeadersString
    ].join('\n');

    const signature = generateSignature(appKey, signingString);

    return {
        'X-AI-GATEWAY-APP-ID': appId,
        'X-AI-GATEWAY-TIMESTAMP': timestamp,
        'X-AI-GATEWAY-NONCE': nonce,
        'X-AI-GATEWAY-SIGNED-HEADERS': 'x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce',
        'X-AI-GATEWAY-SIGNATURE': signature
    };
}