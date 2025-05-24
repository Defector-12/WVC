// 通用聊天功能处理
export class ChatHandler {
    constructor(type) {
        this.type = type; // 'terminology', 'classification', 'valuation', 'consulting'
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.fileInput = document.getElementById('fileInput');
        this.dropZone = document.getElementById('dropZone');
        this.fileInfo = document.getElementById('fileInfo');
        this.removeFile = document.getElementById('removeFile');
        this.currentFile = null;
        
        // 移动端菜单元素
        this.menuButton = document.getElementById('menuButton');
        this.mobileNav = document.getElementById('mobileNav');
        this.closeMenu = document.getElementById('closeMenu');
        
        this.setupEventListeners();
        this.setupMobileMenu();
    }

    setupEventListeners() {
        if (!this.messageInput || !this.sendButton || !this.chatMessages) {
            console.error('Required DOM elements not found');
            return;
        }

        // 发送按钮点击事件
        this.sendButton.addEventListener('click', () => this.handleSend());
        
        // 回车发送消息
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        });
        
        // 文件拖放处理
        if (this.dropZone) {
            this.dropZone.addEventListener('click', () => {
                if (this.fileInput) this.fileInput.click();
            });

            this.dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.add('file-upload-zone-active');
            });
            
            this.dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('file-upload-zone-active');
            });
            
            this.dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.dropZone.classList.remove('file-upload-zone-active');
                const file = e.dataTransfer.files[0];
                this.handleFileUpload(file);
            });
        }
        
        // 文件选择处理
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    this.handleFileUpload(file);
                }
            });
        }
        
        // 移除文件
        if (this.removeFile) {
            this.removeFile.addEventListener('click', () => {
                this.removeUploadedFile();
            });
        }

        // 优化移动端输入体验
        if (this.messageInput) {
            // 自动调整输入框高度
            this.messageInput.addEventListener('input', () => {
                this.messageInput.style.height = 'auto';
                this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
            });

            // 处理软键盘弹出
            const viewportHeight = window.visualViewport.height;
            window.visualViewport.addEventListener('resize', () => {
                if (window.visualViewport.height < viewportHeight) {
                    // 软键盘弹出，调整聊天容器高度
                    this.chatMessages.style.height = `${window.visualViewport.height - 60}px`;
                } else {
                    // 软键盘收起，恢复原始高度
                    this.chatMessages.style.height = '';
                }
            });

            // 优化移动端触摸反馈
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => {
                button.addEventListener('touchstart', () => {
                    button.style.transform = 'scale(0.95)';
                }, { passive: true });

                button.addEventListener('touchend', () => {
                    button.style.transform = '';
                }, { passive: true });
            });
        }
    }

    setupMobileMenu() {
        if (this.menuButton && this.mobileNav) {
            // 创建遮罩层
            const overlay = document.createElement('div');
            overlay.className = 'mobile-nav-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.4);
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s ease;
                z-index: 1000;
                backdrop-filter: blur(4px);
                -webkit-backdrop-filter: blur(4px);
            `;
            document.body.appendChild(overlay);

            // 打开菜单
            this.menuButton.addEventListener('click', () => {
                this.mobileNav.classList.add('active');
                overlay.style.visibility = 'visible';
                overlay.style.opacity = '1';
                document.body.style.overflow = 'hidden';
                
                // 添加进入动画
                this.mobileNav.style.transform = 'translateX(0)';
                this.menuButton.style.opacity = '0';
            });

            // 关闭菜单函数
            const closeMenu = () => {
                this.mobileNav.style.transform = 'translateX(-100%)';
                overlay.style.opacity = '0';
                
                // 延迟隐藏遮罩层，等待动画完成
                setTimeout(() => {
                    overlay.style.visibility = 'hidden';
                    this.mobileNav.classList.remove('active');
                    document.body.style.overflow = '';
                    this.menuButton.style.opacity = '1';
                }, 300);
            };

            this.closeMenu?.addEventListener('click', closeMenu);
            overlay.addEventListener('click', closeMenu);

            // 处理滑动手势
            let touchStartX = 0;
            let touchMoveX = 0;
            let initialTransform = 0;
            let isSwiping = false;

            const handleTouchStart = (e) => {
                if (!this.mobileNav.classList.contains('active')) return;
                touchStartX = e.touches[0].clientX;
                initialTransform = 0;
                isSwiping = true;
                
                // 移除过渡效果，实现跟手效果
                this.mobileNav.style.transition = 'none';
            };

            const handleTouchMove = (e) => {
                if (!isSwiping) return;
                
                touchMoveX = e.touches[0].clientX;
                const diffX = touchMoveX - touchStartX;
                
                // 只允许向左滑动关闭
                if (diffX < 0) {
                    this.mobileNav.style.transform = `translateX(${diffX}px)`;
                    // 更新遮罩层透明度
                    const opacity = Math.max(0, 1 + (diffX / this.mobileNav.offsetWidth));
                    overlay.style.opacity = opacity.toString();
                }
            };

            const handleTouchEnd = () => {
                if (!isSwiping) return;
                
                // 恢复过渡效果
                this.mobileNav.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
                
                const diffX = touchMoveX - touchStartX;
                const threshold = this.mobileNav.offsetWidth * 0.3; // 30% 的宽度作为阈值
                
                if (diffX < -threshold) {
                    closeMenu();
                } else {
                    // 恢复原位
                    this.mobileNav.style.transform = 'translateX(0)';
                    overlay.style.opacity = '1';
                }
                
                isSwiping = false;
            };

            this.mobileNav.addEventListener('touchstart', handleTouchStart, { passive: true });
            this.mobileNav.addEventListener('touchmove', handleTouchMove, { passive: true });
            this.mobileNav.addEventListener('touchend', handleTouchEnd, { passive: true });

            // 处理键盘事件
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.mobileNav.classList.contains('active')) {
                    closeMenu();
                }
            });

            // 处理屏幕旋转
            window.addEventListener('orientationchange', () => {
                if (this.mobileNav.classList.contains('active')) {
                    closeMenu();
                }
            });

            // 优化移动端触摸反馈
            const addTouchFeedback = (element) => {
                element.addEventListener('touchstart', () => {
                    element.style.transform = 'scale(0.98)';
                    element.style.opacity = '0.8';
                }, { passive: true });

                element.addEventListener('touchend', () => {
                    element.style.transform = '';
                    element.style.opacity = '';
                }, { passive: true });
            };

            // 为所有可点击元素添加触摸反馈
            document.querySelectorAll('.mobile-nav-item, .close-button, .menu-button').forEach(addTouchFeedback);
        }
    }

    async handleFileUpload(file) {
        if (!file) return;
        
        // 检查文件类型
        const allowedTypes = [
            'text/plain',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        
        if (!allowedTypes.includes(file.type)) {
            alert('请上传支持的文件格式：.txt, .doc, .docx, .pdf');
            return;
        }
        
        // 添加文件大小限制
        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
        if (file.size > MAX_FILE_SIZE) {
            alert('文件大小不能超过10MB');
            return;
        }
        
        this.currentFile = file;
        
        // 显示文件信息
        if (this.fileInfo) {
            const fileNameElement = this.fileInfo.querySelector('.file-info-name');
            if (fileNameElement) {
                fileNameElement.textContent = file.name;
                this.fileInfo.classList.remove('hidden');
                if (this.dropZone) this.dropZone.classList.add('hidden');
            }
        }
        
        // 显示上传进度
        const progressBar = document.createElement('div');
        progressBar.className = 'upload-progress';
        this.fileInfo?.appendChild(progressBar);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('type', this.type);

            const xhr = new XMLHttpRequest();
            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressBar.style.width = percentComplete + '%';
                }
            };

            // 使用Promise包装XHR请求
            const response = await new Promise((resolve, reject) => {
                xhr.onload = () => resolve(xhr.response);
                xhr.onerror = () => reject(new Error('网络连接错误'));
                xhr.open('POST', '/api/query');
                xhr.responseType = 'json';
                xhr.send(formData);
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`请求失败: ${response.status} ${errorText}`);
            }
            
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                throw new Error('服务器响应格式错误');
            }

            if (data.code === 0 && data.data && data.data.content) {
                this.addMessage(data.data.content, 'ai');
            } else {
                throw new Error(data.msg || '无效的响应格式');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage(error.message || '文件处理失败，请稍后重试', 'error');
        } finally {
            progressBar.remove();
        }
    }

    removeUploadedFile() {
        if (this.fileInfo) {
            this.fileInfo.classList.add('hidden');
            if (this.dropZone) this.dropZone.classList.remove('hidden');
        }
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        this.currentFile = null;
    }

    async handleSend() {
        if (!this.messageInput || !this.chatMessages) return;
        
        const message = this.messageInput.value.trim();
        if (!message && !this.currentFile) return;
        
        // 添加用户消息到聊天区域
        if (message) {
            this.addMessage(message, 'user');
        }
        
        // 显示加载状态
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'flex items-center justify-center p-4';
        loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin text-blue-600"></i>';
        this.chatMessages.appendChild(loadingDiv);
        
        try {
            // 准备请求数据
            const formData = new FormData();
            formData.append('type', this.type);
            if (message) formData.append('message', message);
            if (this.currentFile) formData.append('file', this.currentFile);
            
            // 发送请求到后端
            let response;
            try {
                response = await fetch('/api/query', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'same-origin',
                    mode: 'cors'
                });
            } catch (networkError) {
                throw new Error('网络连接错误，请检查网络连接并重试');
            }
            
            // 移除加载状态
            if (loadingDiv.parentNode) {
                this.chatMessages.removeChild(loadingDiv);
            }
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`请求失败: ${response.status} ${errorText}`);
            }
            
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                throw new Error('服务器响应格式错误');
            }

            if (data.code === 0 && data.data && data.data.content) {
                this.addMessage(data.data.content, 'ai');
                // 清空输入框
                this.messageInput.value = '';
                // 如果有文件，清除文件
                if (this.currentFile) {
                    this.removeUploadedFile();
                }
            } else {
                throw new Error(data.msg || '无效的响应格式');
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

    addMessage(content, type) {
        if (!this.chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex items-start space-x-3 mb-4';
        
        const iconDiv = document.createElement('div');
        iconDiv.className = 'flex-shrink-0';
        
        const iconContainer = document.createElement('div');
        iconContainer.className = type === 'user' ? 
            'w-8 h-8 bg-green-100 rounded-full flex items-center justify-center' :
            'w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center';
        
        const icon = document.createElement('i');
        icon.className = type === 'user' ? 
            'fas fa-user text-lg text-green-600' :
            'fas fa-robot text-lg text-blue-600';
        
        iconContainer.appendChild(icon);
        iconDiv.appendChild(iconContainer);
        messageDiv.appendChild(iconDiv);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'flex-1 bg-gray-50 rounded-lg p-4';
        contentDiv.innerHTML = `<p class="text-gray-700">${content}</p>`;
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // 滚动到底部
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
} 