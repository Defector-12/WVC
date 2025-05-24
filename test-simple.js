import fetch from 'node-fetch';

async function testSimpleTranslation() {
    console.log('测试简化后的翻译功能...\n');
    
    const testCases = [
        {
            name: 'hello翻译测试',
            data: {
                message: 'hello',
                sourceLang: 'en',
                targetLang: 'zh',
                type: 'terminology'
            }
        },
        {
            name: 'world翻译测试',
            data: {
                message: 'world',
                sourceLang: 'en', 
                targetLang: 'zh',
                type: 'terminology'
            }
        },
        {
            name: '你好翻译测试',
            data: {
                message: '你好',
                sourceLang: 'zh',
                targetLang: 'en', 
                type: 'terminology'
            }
        }
    ];
    
    for (const testCase of testCases) {
        console.log(`=== ${testCase.name} ===`);
        try {
            const response = await fetch('http://localhost:3003/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(testCase.data)
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log(`✅ 翻译成功: "${testCase.data.message}" → "${result.data.content}"`);
            } else {
                console.log(`❌ 请求失败: ${response.status}`);
            }
        } catch (error) {
            console.log(`❌ 错误: ${error.message}`);
        }
        console.log('');
    }
}

// 等待一下让服务器启动
setTimeout(() => {
    testSimpleTranslation().then(() => {
        console.log('翻译测试完成！');
        process.exit(0);
    }).catch(error => {
        console.error('测试失败:', error);
        process.exit(1);
    });
}, 2000); // 等待2秒 