// 基础聊天处理器类
export class ChatHandler {
    constructor(type = 'chat') {
        this.type = type;
        
        // 获取基本DOM元素
        this.messageInput = document.getElementById('messageInput');
        this.chatMessages = document.getElementById('chatMessages');
        this.sendButton = document.getElementById('sendButton');
        
        // 文件上传相关
        this.currentFile = null;
        
        // 初始化事件监听器
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // 发送按钮点击事件
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.handleSend());
        }
        
        // 输入框回车事件
        if (this.messageInput) {
            this.messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSend();
                }
            });
        }
    }
    
    // 基础的发送处理方法（子类可以重写）
    async handleSend() {
        if (!this.messageInput || !this.chatMessages) return;
        
        const message = this.messageInput.value.trim();
        if (!message && !this.currentFile) return;
        
        // 添加用户消息
        if (message) {
            this.addMessage(message, 'user');
        }
        
        // 清空输入框
        this.messageInput.value = '';
        
        // 子类应该重写这个方法来处理具体的消息发送逻辑
        console.log('ChatHandler: handleSend method should be overridden by subclass');
    }
    
    // 添加消息到聊天区域
    addMessage(content, type) {
        if (!this.chatMessages) return null;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-4 fade-in';

        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="flex-1 flex justify-start">
                    <div class="bg-blue-600 text-white rounded-2xl p-6 flex-1">
                        <p class="leading-relaxed">${content}</p>
                    </div>
                </div>
            `;
        } else if (type === 'ai') {
            messageDiv.innerHTML = `
                <div class="ai-avatar">
                    <img src="logo.png" alt="logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: white;" />
                </div>
                <div class="flex-1 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 shadow-sm">
                    <div class="flex items-center mb-3">
                        <span class="text-sm font-medium text-indigo-600">关务翻译助手</span>
                        <span class="ml-2 px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full">翻译完成</span>
                    </div>
                    <p class="text-gray-700 leading-relaxed">${content}</p>
                </div>
            `;
        } else if (type === 'loading') {
            messageDiv.innerHTML = `
                <div class="ai-avatar">
                    <i class="fas fa-spinner fa-spin text-lg"></i>
                </div>
                <div class="flex-1 bg-gray-50 rounded-2xl p-6">
                    <p class="text-gray-600">${content}</p>
                </div>
            `;
        } else if (type === 'error') {
            messageDiv.innerHTML = `
                <div class="ai-avatar bg-red-500">
                    <i class="fas fa-exclamation-triangle text-lg"></i>
                </div>
                <div class="flex-1 bg-red-50 rounded-2xl p-6">
                    <p class="text-red-700">${content}</p>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        const scrollOptions = {
            behavior: 'smooth',
            block: 'end'
        };
        messageDiv.scrollIntoView(scrollOptions);
        
        return messageDiv;
    }
    
    // 移除上传的文件
    removeUploadedFile() {
        this.currentFile = null;
        // 子类可以重写这个方法来处理UI更新
    }
} 