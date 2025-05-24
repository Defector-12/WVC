import { ChatHandler } from './chat.js';

// 商品归类模块
class Classification {
    constructor() {
        this.currentFile = null;
        this.initializeUI();
    }

    initializeUI() {
        this.initProductInput();
        this.initFileUpload();
    }

    initProductInput() {
        const productInput = document.getElementById('product-input');
        const submitButton = document.getElementById('submit-button');
        const resultArea = document.getElementById('result-area');

        if (submitButton && productInput) {
            submitButton.addEventListener('click', () => this.handleSubmit(productInput, resultArea));
            productInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSubmit(productInput, resultArea);
                }
            });
        }
    }

    initFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const removeFile = document.getElementById('removeFile');
        const fileName = fileInfo.querySelector('.file-info-name');
        const dropZone = document.getElementById('dropZone');

        // 点击上传区域触发文件选择
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // 文件拖放支持
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('drag-over');
            
            const file = e.dataTransfer.files[0];
            if (this.validateFile(file)) {
                fileInput.files = e.dataTransfer.files;
                const event = new Event('change');
                fileInput.dispatchEvent(event);
            }
        });

        // 文件选择处理
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (this.validateFile(file)) {
                this.currentFile = file;
                fileName.textContent = file.name;
                fileInfo.classList.remove('hidden');
            } else {
                fileInput.value = '';
            }
        });

        // 文件移除处理
        removeFile.addEventListener('click', () => {
            this.currentFile = null;
            fileInput.value = '';
            fileInfo.classList.add('hidden');
        });
    }

    validateFile(file) {
        const allowedTypes = [
            'image/jpeg',
            'image/png',
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ];
        
        if (file && allowedTypes.includes(file.type)) {
            return true;
        } else {
            alert('请上传支持的文件格式：JPG、PNG、PDF、DOC、DOCX');
            return false;
        }
    }

    async handleSubmit(productInput, resultArea) {
        const description = productInput.value.trim();
        if (!description) return;

        try {
            // 显示加载状态
            resultArea.innerHTML = '<div class="loading">正在分析商品信息...</div>';

            // TODO: 调用后端API获取大模型分析结果
            const response = await this.getClassificationResult(description);
            this.displayResult(response, resultArea);
        } catch (error) {
            console.error('Error:', error);
            resultArea.innerHTML = '<div class="error">抱歉，分析商品信息时出现错误。</div>';
        }
    }

    async getClassificationResult(description) {
        // TODO: 实现与后端API的通信
        // 这里将来需要替换为实际的API调用
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    hsCode: '8471.30.00',
                    description: '便携式计算机',
                    explanation: '这是一个测试响应。实际使用时将通过API获取大模型的分析结果。'
                });
            }, 1000);
        });
    }

    displayResult(result, resultArea) {
        resultArea.innerHTML = `
            <div class="classification-result">
                <div class="result-item">
                    <strong>HS编码：</strong>
                    <span>${result.hsCode}</span>
                </div>
                <div class="result-item">
                    <strong>商品名称：</strong>
                    <span>${result.description}</span>
                </div>
                <div class="result-item">
                    <strong>分析说明：</strong>
                    <p>${result.explanation}</p>
                </div>
            </div>
        `;
    }
}

// 初始化商品归类模块
document.addEventListener('DOMContentLoaded', () => {
    new Classification();
});

// 初始化商品归类聊天处理器
const chatHandler = new ChatHandler('classification');