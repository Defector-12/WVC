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
                        <p class="leading-relaxed">${this._escapeHtml(content)}</p>
                    </div>
                </div>
            `;
        } else if (type === 'ai') {
            // 处理AI回复内容，解析markdown和知识库引用
            const processedContent = this._processAIContent(content);
            
            messageDiv.innerHTML = `
                <div class="ai-avatar">
                    <img src="logo.png" alt="logo" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; background: white;" />
                </div>
                <div class="flex-1 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 shadow-sm">
                    <div class="flex items-center mb-3">
                        <span class="text-sm font-medium text-indigo-600">关务翻译助手</span>
                        <span class="ml-2 px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full">翻译完成</span>
                    </div>
                    <div class="text-gray-700 leading-relaxed">${processedContent}</div>
                </div>
            `;
        } else if (type === 'system') {
            messageDiv.innerHTML = `
                <div class="ai-avatar bg-green-500">
                    <i class="fas fa-info-circle text-lg"></i>
                </div>
                <div class="flex-1 bg-green-50 rounded-2xl p-6">
                    <p class="text-green-700">${this._escapeHtml(content)}</p>
                </div>
            `;
        } else if (type === 'loading') {
            messageDiv.innerHTML = `
                <div class="ai-avatar">
                    <i class="fas fa-spinner fa-spin text-lg"></i>
                </div>
                <div class="flex-1 bg-gray-50 rounded-2xl p-6">
                    <p class="text-gray-600">${this._escapeHtml(content)}</p>
                </div>
            `;
        } else if (type === 'error') {
            messageDiv.innerHTML = `
                <div class="ai-avatar bg-red-500">
                    <i class="fas fa-exclamation-triangle text-lg"></i>
                </div>
                <div class="flex-1 bg-red-50 rounded-2xl p-6">
                    <p class="text-red-700">${this._escapeHtml(content)}</p>
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
    
    // 处理AI内容，解析markdown和知识库引用
    _processAIContent(content) {
        try {
            // 检测是否包含翻译工作流格式
            const hasWorkflow = content.includes('# 翻译工作流执行过程') || 
                               content.includes('## 1. 原文拆解与专业术语提取');
            
            // 首先处理知识库引用格式
            let processedContent = this._processKnowledgeReferences(content);
            
            // 如果包含工作流，进行特殊处理
            if (hasWorkflow) {
                // 为工作流标题添加样式
                processedContent = processedContent.replace(
                    /(# 翻译工作流执行过程)/g, 
                    '<h2 class="text-xl font-bold text-blue-700 my-4 border-b border-blue-200 pb-2">$1</h2>'
                );
                
                // 为步骤标题添加样式
                processedContent = processedContent.replace(
                    /(## \d+\.\s+[^#\n]+)/g,
                    '<h3 class="text-lg font-semibold text-blue-600 mt-4 mb-2">$1</h3>'
                );
                
                // 为子步骤标题添加样式
                processedContent = processedContent.replace(
                    /(### \d+\.\d+\.\s+[^#\n]+)/g,
                    '<h4 class="text-md font-medium text-blue-500 mt-3 mb-2">$1</h4>'
                );
                
                // 添加分隔线
                processedContent = processedContent.replace(
                    /(## 7\. 最终译文\s*\n)/g,
                    '<hr class="my-4 border-t-2 border-blue-300">\n$1'
                );
                
                // 特别突出最终译文部分
                processedContent = processedContent.replace(
                    /(## 7\. 最终译文\s*\n)([\s\S]+?)(?=\s*#|$)/g,
                    '<h3 class="text-lg font-semibold text-green-600 mt-4 mb-2">$1</h3><div class="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">$2</div>'
                );
            }
            
            // 然后使用marked.js解析markdown（如果可用）
            if (typeof marked !== 'undefined' && !hasWorkflow) {
                // 只有在非工作流格式时才使用marked解析，避免破坏自定义样式
                // 配置marked选项
                marked.setOptions({
                    breaks: true,  // 支持换行
                    gfm: true      // 支持GitHub风格的markdown
                });
                
                processedContent = marked.parse(processedContent);
            } else if (hasWorkflow) {
                // 如果是工作流格式，手动处理一些基本的markdown格式
                // 处理无序列表
                processedContent = processedContent.replace(/- (.*?)(?=\n|$)/g, '<li class="ml-4">• $1</li>');
                // 处理换行
                processedContent = processedContent.replace(/\n/g, '<br>');
            }
            
            return processedContent;
        } catch (error) {
            console.warn('处理AI内容时出错:', error);
            // 如果处理失败，返回转义后的原始内容
            return this._escapeHtml(content);
        }
    }
    
    // 处理知识库引用格式
    _processKnowledgeReferences(content) {
        // 处理 [数字] 格式的引用
        content = content.replace(/\[(\d+)\]/g, '<span class="knowledge-ref" title="知识库引用 $1">[$1]</span>');
        
        // 处理 【数字】 格式的引用
        content = content.replace(/【(\d+)】/g, '<span class="knowledge-ref" title="知识库引用 $1">【$1】</span>');
        
        // 处理 WVC数据集 等特殊标记
        content = content.replace(/(WVC数据集)/g, '<span class="dataset-ref" title="数据集引用">$1</span>');
        
        return content;
    }
    
    // HTML转义函数
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // 移除上传的文件
    removeUploadedFile() {
        this.currentFile = null;
        // 子类可以重写这个方法来处理UI更新
    }
} 