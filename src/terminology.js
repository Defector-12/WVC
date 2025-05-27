// 术语翻译页面的交互逻辑
import { ChatHandler } from './chat.js';

// 扩展ChatHandler类来处理术语翻译特定功能
class TerminologyHandler extends ChatHandler {
    constructor() {
        super('terminology');
        
        // 获取语言选择元素
        this.sourceLangSelect = document.getElementById('sourceLang');
        this.targetLangSelect = document.getElementById('targetLang');
        
        // 获取翻译结果容器
        this.translationResult = document.getElementById('translationResult');
        this.translationText = document.getElementById('translationText');
        this.explanationText = document.getElementById('explanationText');
        
        // 设置语言切换按钮
        this.langSwitchBtn = document.getElementById('langSwitchBtn');
        
        // 初始化会话ID（用于多轮对话）
        this.sessionId = null;
        
        // 添加额外的事件监听器
        this.setupTranslationListeners();
    }
    
    setupTranslationListeners() {
        // 语言切换按钮
        if (this.langSwitchBtn) {
            this.langSwitchBtn.addEventListener('click', () => {
                const sourceLang = this.sourceLangSelect.value;
                const targetLang = this.targetLangSelect.value;
                
                // 交换语言
                this.sourceLangSelect.value = targetLang;
                this.targetLangSelect.value = sourceLang;
            });
        }
        
        // 复制结果按钮
        const copyButton = document.getElementById('copyButton');
        if (copyButton) {
            copyButton.addEventListener('click', () => {
                const textToCopy = this.translationText.textContent;
                navigator.clipboard.writeText(textToCopy)
                    .then(() => {
                        alert('已复制到剪贴板');
                    })
                    .catch(err => {
                        console.error('复制失败:', err);
                    });
            });
        }
        
        // 保存按钮
        const saveButton = document.getElementById('saveButton');
        if (saveButton) {
            saveButton.addEventListener('click', () => {
                this.saveToHistory(
                    this.messageInput.value,
                    this.translationText.textContent
                );
                alert('已保存到翻译历史');
            });
        }
    }
    
    // 重写handleSend方法，增加对语言选择的处理
    async handleSend() {
        if (!this.messageInput || !this.chatMessages) return;
        
        const message = this.messageInput.value.trim();
        if (!message && !this.currentFile) return;
        
        // 添加用户消息到聊天区域
        if (message) {
            this.addMessage(message, 'user');
        }
        
        // 检测消息类型：翻译、对话还是专业名词解释
        const messageType = this.detectMessageType(message);
        
        // 显示加载状态
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'flex items-center justify-center p-4';
        loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin text-blue-600"></i>';
        this.chatMessages.appendChild(loadingDiv);
        
        try {
            let response;
            
            if (messageType === 'translation') {
                // 翻译请求
                response = await this.handleTranslation(message);
            } else if (messageType === 'explanation') {
                // 专业名词解释请求
                response = await this.handleExplanation(message);
            } else {
                // 对话请求
                response = await this.handleChat(message);
            }
            
            // 移除加载状态
            if (loadingDiv.parentNode) {
                this.chatMessages.removeChild(loadingDiv);
            }
            
            // 处理响应
            if (response && response.code === 0 && response.data && response.data.content) {
                // 在聊天区域显示结果
                this.addMessage(response.data.content, 'ai');
                
                // 如果是翻译结果且存在专门的翻译结果区域，也显示结果
                if (messageType === 'translation' && this.translationResult && this.translationText) {
                    this.translationText.textContent = response.data.content;
                    if (this.explanationText && response.data.explanation) {
                        this.explanationText.textContent = response.data.explanation || '无额外解释';
                    }
                    this.translationResult.classList.remove('hidden');
                }
                
                // 保存会话ID（用于多轮对话）
                if (response.data.session_id) {
                    this.sessionId = response.data.session_id;
                }
                
                // 清空输入框
                this.messageInput.value = '';
                // 如果有文件，清除文件
                if (this.currentFile) {
                    this.removeUploadedFile();
                }
            } else {
                throw new Error(response?.message || '无效的响应格式');
            }
        } catch (error) {
            console.error('Error:', error);
            // 移除加载状态
            if (loadingDiv.parentNode) {
                this.chatMessages.removeChild(loadingDiv);
            }
            // 显示用户友好的错误消息
            const errorMessage = error.message || '请求失败，请稍后重试';
            this.addMessage(errorMessage, 'error');
        }
    }
    
    // 检测消息类型
    detectMessageType(message) {
        // 检测是否为专业名词解释请求
        const explanationKeywords = ['什么是', '解释', '定义', '含义', '是什么', '什么意思'];
        if (explanationKeywords.some(keyword => message.includes(keyword))) {
            return 'explanation';
        }
        
        // 检测是否为翻译请求（包含明显的翻译意图或不同语言文字）
        const hasChineseAndEnglish = /[\u4e00-\u9fa5]/.test(message) && /[a-zA-Z]/.test(message);
        const translationKeywords = ['翻译', '译成', 'translate', '英文', '中文'];
        if (hasChineseAndEnglish || translationKeywords.some(keyword => message.toLowerCase().includes(keyword.toLowerCase()))) {
            return 'translation';
        }
        
        // 默认为对话
        return 'chat';
    }
    
    // 处理翻译请求
    async handleTranslation(message) {
        const sourceLang = this.sourceLangSelect ? this.sourceLangSelect.value : 'en';
        const targetLang = this.targetLangSelect ? this.targetLangSelect.value : 'zh';
        
        const requestBody = {
            type: this.type,
            message: message,
            sourceLang: sourceLang,
            targetLang: targetLang
        };
        
        // 注意：文件上传功能暂时不支持，如需要可以单独处理
        if (this.currentFile) {
            console.warn('文件上传功能暂时不支持，将忽略文件');
        }
        
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`翻译请求失败: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // 处理专业名词解释请求
    async handleExplanation(message) {
        // 提取专业名词（简单的提取逻辑）
        let term = message;
        const explanationKeywords = ['什么是', '解释', '定义', '含义', '是什么', '什么意思'];
        for (const keyword of explanationKeywords) {
            if (message.includes(keyword)) {
                term = message.replace(keyword, '').trim();
                break;
            }
        }
        
        const response = await fetch('/api/explain', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                term: term,
                context: null
            })
        });
        
        if (!response.ok) {
            throw new Error(`专业名词解释请求失败: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // 处理对话请求
    async handleChat(message) {
        const requestBody = {
            message: message,
            session_id: this.sessionId || null,
            context: null
        };
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`对话请求失败: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // 添加保存到历史记录的方法
    saveToHistory(term, translation) {
        try {
            // 从localStorage获取现有历史
            const history = JSON.parse(localStorage.getItem('translationHistory') || '[]');
            
            // 添加新条目
            history.unshift({
                term,
                translation,
                timestamp: new Date().toISOString(),
                sourceLang: this.sourceLangSelect ? this.sourceLangSelect.value : 'en',
                targetLang: this.targetLangSelect ? this.targetLangSelect.value : 'zh'
            });
            
            // 限制历史记录数量（例如最多保存20条）
            if (history.length > 20) {
                history.pop();
            }
            
            // 保存回localStorage
            localStorage.setItem('translationHistory', JSON.stringify(history));
        } catch (error) {
            console.error('保存历史记录失败:', error);
        }
    }
    
    // 加载历史记录的方法
    loadHistory() {
        try {
            const historyList = document.getElementById('historyList');
            const emptyHistory = document.getElementById('emptyHistory');
            
            if (!historyList) return;
            
            const history = JSON.parse(localStorage.getItem('translationHistory') || '[]');
            
            if (history.length === 0) {
                if (emptyHistory) emptyHistory.classList.remove('hidden');
                return;
            }
            
            if (emptyHistory) emptyHistory.classList.add('hidden');
            
            // 清除现有内容
            historyList.innerHTML = '';
            
            // 添加历史记录项
            history.forEach((item, index) => {
                const date = new Date(item.timestamp).toLocaleString();
                
                const historyItem = document.createElement('div');
                historyItem.className = 'p-4 border border-gray-200 rounded-lg hover:bg-gray-50';
                historyItem.innerHTML = `
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="font-medium">${item.term}</p>
                            <p class="text-gray-600 mt-1">${item.translation}</p>
                        </div>
                        <div class="text-sm text-gray-500">${date}</div>
                    </div>
                    <div class="mt-2 flex justify-end">
                        <button class="text-blue-600 hover:text-blue-800 text-sm use-result-btn" data-index="${index}">
                            使用此结果
                        </button>
                    </div>
                `;
                
                historyList.appendChild(historyItem);
            });
            
            // 添加历史记录点击事件
            document.querySelectorAll('.use-result-btn').forEach(button => {
                button.addEventListener('click', () => {
                    const index = button.getAttribute('data-index');
                    const item = history[index];
                    
                    // 填充输入框和结果区域
                    this.messageInput.value = item.term;
                    if (this.sourceLangSelect && item.sourceLang) {
                        this.sourceLangSelect.value = item.sourceLang;
                    }
                    if (this.targetLangSelect && item.targetLang) {
                        this.targetLangSelect.value = item.targetLang;
                    }
                    
                    if (this.translationResult && this.translationText) {
                        this.translationText.textContent = item.translation;
                        this.translationResult.classList.remove('hidden');
                    }
                });
            });
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    }
}

// 初始化术语翻译处理器
document.addEventListener('DOMContentLoaded', () => {
    const handler = new TerminologyHandler();
    
    // 加载历史记录
    handler.loadHistory();
});