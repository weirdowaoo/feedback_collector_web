/**
 * 主应用逻辑
 */
class FeedbackApp {
    constructor() {
        this.currentRequestId = null;
        this.uploadedImages = [];
        this.isSubmitting = false;
        this.pasteListenerSetup = false;

        // DOM 元素
        this.elements = {};

        // 绑定方法
        this.init = this.init.bind(this);
        this.initElements = this.initElements.bind(this);
        this.initEventListeners = this.initEventListeners.bind(this);
        this.initWebSocketHandlers = this.initWebSocketHandlers.bind(this);
        this.showFeedbackForm = this.showFeedbackForm.bind(this);
        this.hideFeedbackForm = this.hideFeedbackForm.bind(this);
        this.submitFeedback = this.submitFeedback.bind(this);
        this.cancelFeedback = this.cancelFeedback.bind(this);
        this.clearForm = this.clearForm.bind(this);
        this.handleFileUpload = this.handleFileUpload.bind(this);
        this.addImagePreview = this.addImagePreview.bind(this);
        this.removeImage = this.removeImage.bind(this);
        this.showNotification = this.showNotification.bind(this);
        this.updateSubmitStatus = this.updateSubmitStatus.bind(this);
    }

    /**
     * 初始化应用
     */
    init() {
        this.initElements();
        this.initEventListeners();
        this.initWebSocketHandlers();
        this.loadUserSettings();

        console.log('Feedback collection app initialized');
    }

    /**
     * 初始化DOM元素引用
     */
    initElements() {
        this.elements = {
            waitingState: document.getElementById('waitingState'),
            feedbackForm: document.getElementById('feedbackForm'),
            submitStatus: document.getElementById('submitStatus'),
            requestInfo: document.getElementById('requestInfo'),
            feedbackText: document.getElementById('feedbackText'),
            uploadArea: document.getElementById('uploadArea'),
            fileInput: document.getElementById('fileInput'),
            imagePreview: document.getElementById('imagePreview'),
            autoAppend: document.getElementById('autoAppend'),
            submitBtn: document.getElementById('submitBtn'),
            cancelBtn: document.getElementById('cancelBtn'),
            selectImageBtn: document.getElementById('selectImageBtn'),
            pasteImageBtn: document.getElementById('pasteImageBtn'),
            clearImagesBtn: document.getElementById('clearImagesBtn'),
            statusIcon: document.getElementById('statusIcon'),
            statusTitle: document.getElementById('statusTitle'),
            statusMessage: document.getElementById('statusMessage'),
            notifications: document.getElementById('notifications')
        };
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 提交按钮
        if (this.elements.submitBtn) {
            this.elements.submitBtn.addEventListener('click', this.submitFeedback);
        }

        // 取消按钮
        if (this.elements.cancelBtn) {
            this.elements.cancelBtn.addEventListener('click', this.cancelFeedback);
        }

        // 选择图片按钮
        if (this.elements.selectImageBtn) {
            this.elements.selectImageBtn.addEventListener('click', () => {
                this.elements.fileInput?.click();
            });
        }

        // 粘贴图片按钮
        if (this.elements.pasteImageBtn) {
            this.elements.pasteImageBtn.addEventListener('click', this.pasteImageFromClipboard.bind(this));
        }

        // 清除图片按钮
        if (this.elements.clearImagesBtn) {
            this.elements.clearImagesBtn.addEventListener('click', this.clearAllImages.bind(this));
        }

        // 文件上传区域
        if (this.elements.uploadArea) {
            this.elements.uploadArea.addEventListener('click', () => {
                this.elements.fileInput?.click();
            });

            // 拖拽上传
            this.elements.uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.elements.uploadArea.classList.add('dragover');
            });

            this.elements.uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                this.elements.uploadArea.classList.remove('dragover');
            });

            this.elements.uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                this.elements.uploadArea.classList.remove('dragover');

                const files = Array.from(e.dataTransfer.files);
                this.handleFileUpload(files);
            });
        }

        // 文件输入
        if (this.elements.fileInput) {
            this.elements.fileInput.addEventListener('change', (e) => {
                const files = Array.from(e.target.files);
                this.handleFileUpload(files);
                e.target.value = ''; // 清空输入，允许重复选择同一文件
            });
        }

        // 键盘快捷键
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter 或 Cmd+Enter 提交
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                if (this.elements.feedbackForm.style.display !== 'none') {
                    this.submitFeedback();
                }
            }

            // ESC 取消
            if (e.key === 'Escape') {
                e.preventDefault();
                if (this.elements.feedbackForm.style.display !== 'none') {
                    this.cancelFeedback();
                }
            }
        });

        // 文本框自动调整高度
        if (this.elements.feedbackText) {
            this.elements.feedbackText.addEventListener('input', (e) => {
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
            });
        }

        // 监听自动附加选项变化，保存用户设置
        if (this.elements.autoAppend) {
            this.elements.autoAppend.addEventListener('change', () => {
                this.saveUserSettings();
            });
        }
    }

    /**
     * 初始化WebSocket消息处理器
     */
    initWebSocketHandlers() {
        if (!window.wsManager) {
            console.error('WebSocket manager not initialized');
            return;
        }

        // 反馈请求
        window.wsManager.onMessageType('request_feedback', (data) => {
            this.handleFeedbackRequest(data);
        });

        // 反馈响应
        window.wsManager.onMessageType('feedback_response', (data) => {
            this.handleFeedbackResponse(data);
        });

        // 清空界面
        window.wsManager.onMessageType('clear_interface', (data) => {
            this.clearForm();
            this.hideFeedbackForm();
        });

        // 请求超时
        window.wsManager.onMessageType('request_timeout', (data) => {
            this.handleRequestTimeout(data);
        });

        // 请求取消
        window.wsManager.onMessageType('request_cancelled', (data) => {
            this.handleRequestCancelled(data);
        });

        // 连接状态变化
        window.wsManager.onConnectionChange((status) => {
            if (status === 'connected') {
                this.showNotification('success', this.getText('connection_restored'));
            } else if (status === 'disconnected') {
                this.showNotification('warning', this.getText('connection_lost'));
            }
        });
    }

    /**
     * 处理反馈请求
     */
    handleFeedbackRequest(data) {
        console.log('收到反馈请求:', data);

        this.currentRequestId = data.id;

        // 更新请求信息
        if (this.elements.requestInfo) {
            const timeout = data.timeout || 600;
            const timeoutText = this.getText('timeout');
            this.elements.requestInfo.innerHTML = `
                <strong>请求ID:</strong> ${data.id}<br>
                <strong>超时时间:</strong> ${timeout}秒<br>
                <strong>请求时间:</strong> ${new Date(data.timestamp).toLocaleString()}
            `;
        }

        // 显示反馈表单
        this.showFeedbackForm();

        // 聚焦到文本框
        setTimeout(() => {
            this.elements.feedbackText?.focus();
        }, 100);
    }

    /**
     * 处理反馈响应
     */
    handleFeedbackResponse(data) {
        console.log('收到反馈响应:', data);

        if (data.status === 'success') {
            this.updateSubmitStatus('success', this.getText('submitted'), data.message);
            this.showNotification('success', this.getText('submit_success'));
        } else {
            this.updateSubmitStatus('error', this.getText('error'), data.message);
            this.showNotification('error', this.getText('submit_error') + ': ' + data.message);
        }

        this.isSubmitting = false;

        // 3秒后隐藏状态
        setTimeout(() => {
            this.hideFeedbackForm();
        }, 3000);
    }

    /**
     * 处理请求超时
     */
    handleRequestTimeout(data) {
        console.log('请求超时:', data);
        this.updateSubmitStatus('error', this.getText('timeout'), data.message);
        this.showNotification('warning', this.getText('timeout'));

        setTimeout(() => {
            this.hideFeedbackForm();
        }, 3000);
    }

    /**
     * 处理请求取消
     */
    handleRequestCancelled(data) {
        console.log('请求取消:', data);
        this.updateSubmitStatus('error', this.getText('cancelled'), data.message);
        this.showNotification('info', this.getText('cancelled'));

        setTimeout(() => {
            this.hideFeedbackForm();
        }, 3000);
    }

    /**
     * 显示反馈表单
     */
    showFeedbackForm() {
        // 只清空文本内容和图片，保持用户设置
        this.clearFormContent();

        // 重新加载用户设置，确保状态正确
        this.loadUserSettings();

        this.elements.waitingState.style.display = 'none';
        this.elements.submitStatus.style.display = 'none';
        this.elements.feedbackForm.style.display = 'block';
    }

    /**
     * 隐藏反馈表单
     */
    hideFeedbackForm() {
        this.elements.feedbackForm.style.display = 'none';
        this.elements.submitStatus.style.display = 'none';
        this.elements.waitingState.style.display = 'block';

        this.currentRequestId = null;
        this.clearFormContent(); // 只清空内容，保持用户设置
    }

    /**
     * 提交反馈
     */
    async submitFeedback() {
        if (this.isSubmitting || !this.currentRequestId) {
            return;
        }

        this.isSubmitting = true;

        // 获取反馈内容
        const text = this.elements.feedbackText?.value?.trim() || '';
        const autoAppend = this.elements.autoAppend?.checked ?? true;

        // 检查是否有内容
        if (!text && this.uploadedImages.length === 0) {
            this.showNotification('warning', this.getText('enter_feedback_or_upload'));
            this.isSubmitting = false;
            return;
        }

        // 准备提交数据
        const submitData = {
            type: 'feedback_submit',
            request_id: this.currentRequestId,
            text: text,
            images: this.uploadedImages,
            auto_append: autoAppend,
            language: window.APP_CONFIG?.language || 'CN',
            timestamp: new Date().toISOString()
        };

        // 发送数据
        const success = window.wsManager.send(submitData);

        if (!success) {
            this.showNotification('error', this.getText('send_failed'));
            this.isSubmitting = false;
        } else {
            // 发送成功，立即显示提交成功
            this.updateSubmitStatus('success', this.getText('submitted'), this.getText('feedback_submitted_success'));
            this.elements.feedbackForm.style.display = 'none';
            this.elements.submitStatus.style.display = 'block';
            this.showNotification('success', this.getText('submit_success'));

            // 3秒后隐藏界面
            setTimeout(() => {
                this.hideFeedbackForm();
                this.isSubmitting = false;
            }, 3000);
        }
    }

    /**
     * 取消反馈
     */
    cancelFeedback() {
        if (this.isSubmitting) {
            return;
        }

        // 如果有当前请求ID，发送取消消息到服务器
        if (this.currentRequestId) {
            const cancelData = {
                type: 'feedback_cancel',
                request_id: this.currentRequestId,
                timestamp: new Date().toISOString()
            };

            const success = window.wsManager.send(cancelData);
            if (success) {
                console.log('已发送取消反馈消息:', cancelData);
            } else {
                console.warn('发送取消反馈消息失败');
            }
        }

        this.hideFeedbackForm();
        this.showNotification('info', this.getText('cancelled'));
    }

    /**
     * 清空表单内容（不影响用户设置）
     */
    clearFormContent() {
        if (this.elements.feedbackText) {
            this.elements.feedbackText.value = '';
            this.elements.feedbackText.style.height = 'auto';
        }

        this.uploadedImages = [];
        this.updateImagePreview();

        this.isSubmitting = false;
    }

    /**
     * 清空表单（完全重置，包括用户设置）
     */
    clearForm() {
        this.clearFormContent();

        // 只有在明确需要重置用户设置时才调用
        // 通常情况下不应该重置用户的选择
        // if (this.elements.autoAppend) {
        //     this.elements.autoAppend.checked = true;
        // }
    }

    /**
     * 处理文件上传
     */
    async handleFileUpload(files) {
        const maxFileSize = window.APP_CONFIG?.maxFileSize || 10 * 1024 * 1024;
        const allowedExtensions = window.APP_CONFIG?.allowedExtensions || ['.png', '.jpg', '.jpeg', '.gif', '.webp'];

        for (const file of files) {
            try {
                // 检查文件类型
                if (!file.type.startsWith('image/')) {
                    this.showNotification('error', `${file.name}: ${this.getText('file_type_not_supported')}`);
                    continue;
                }

                // 检查文件扩展名
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowedExtensions.includes(ext)) {
                    this.showNotification('error', `${file.name}: ${this.getText('file_type_not_supported')}`);
                    continue;
                }

                // 检查文件大小
                if (file.size > maxFileSize) {
                    this.showNotification('error', `${file.name}: ${this.getText('file_too_large')}`);
                    continue;
                }

                // 读取文件
                const imageData = await this.readFileAsDataURL(file);

                // 添加到上传列表
                const imageInfo = {
                    name: file.name,
                    size: file.size,
                    type: file.type,
                    data: imageData,
                    uploadTime: new Date().toISOString()
                };

                this.uploadedImages.push(imageInfo);
                this.updateImagePreview();

                console.log('Image uploaded successfully:', file.name);

            } catch (error) {
                console.error('File processing failed:', error);
                this.showNotification('error', `${file.name}: ${this.getText('processing_failed')}`);
            }
        }
    }

    /**
     * 读取文件为Data URL
     */
    readFileAsDataURL(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsDataURL(file);
        });
    }

    /**
     * 更新图片预览
     */
    updateImagePreview() {
        if (!this.elements.imagePreview) return;

        this.elements.imagePreview.innerHTML = '';

        if (this.uploadedImages.length === 0) {
            const placeholder = document.createElement('div');
            placeholder.className = 'no-images-placeholder';
            placeholder.textContent = this.getText('no_images_selected');
            this.elements.imagePreview.appendChild(placeholder);
        } else {
            this.uploadedImages.forEach((image, index) => {
                this.addImagePreview(image, index);
            });
        }
    }

    /**
     * 添加图片预览
     */
    addImagePreview(imageInfo, index) {
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';

        const img = document.createElement('img');
        img.src = imageInfo.data;
        img.alt = imageInfo.name;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'image-remove';
        removeBtn.innerHTML = '×';
        removeBtn.title = this.getText('delete_image');
        removeBtn.onclick = () => this.removeImage(index);

        const info = document.createElement('div');
        info.className = 'image-info';
        info.textContent = `${imageInfo.name} (${this.formatFileSize(imageInfo.size)})`;

        imageItem.appendChild(img);
        imageItem.appendChild(removeBtn);
        imageItem.appendChild(info);

        this.elements.imagePreview.appendChild(imageItem);
    }

    /**
     * 移除图片
     */
    removeImage(index) {
        this.uploadedImages.splice(index, 1);
        this.updateImagePreview();
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';

        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 显示通知
     */
    showNotification(type, message, duration = 5000) {
        if (!this.elements.notifications) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.innerHTML = '×';
        closeBtn.onclick = () => notification.remove();

        notification.innerHTML = `<div>${message}</div>`;
        notification.appendChild(closeBtn);

        this.elements.notifications.insertBefore(notification, this.elements.notifications.firstChild);

        // 自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }

    /**
     * 更新提交状态
     */
    updateSubmitStatus(type, title, message) {
        if (!this.elements.statusIcon || !this.elements.statusTitle || !this.elements.statusMessage) {
            return;
        }

        // 更新图标
        this.elements.statusIcon.className = 'status-icon';
        switch (type) {
            case 'loading':
                this.elements.statusIcon.classList.add('loading');
                this.elements.statusIcon.textContent = '⏳';
                break;
            case 'success':
                this.elements.statusIcon.classList.add('success');
                this.elements.statusIcon.textContent = '✅';
                break;
            case 'error':
                this.elements.statusIcon.classList.add('error');
                this.elements.statusIcon.textContent = '❌';
                break;
            default:
                this.elements.statusIcon.textContent = '⏳';
        }

        // 更新文本
        this.elements.statusTitle.textContent = title;
        this.elements.statusMessage.textContent = message;
    }

    /**
     * 获取本地化文本
     */
    getText(key) {
        const texts = window.APP_CONFIG?.texts || {};
        return texts[key] || key;
    }

    /**
     * 从剪贴板粘贴图片
     */
    async pasteImageFromClipboard() {
        try {
            // 首先检查是否支持 Clipboard API
            if (!navigator.clipboard || !navigator.clipboard.read) {
                this.showNotification('error', this.getText('clipboard_api_not_supported'));
                this.setupPasteEventListener();
                return;
            }

            // 检查权限
            const permission = await navigator.permissions.query({ name: 'clipboard-read' });
            if (permission.state === 'denied') {
                this.showNotification('error', this.getText('clipboard_permission_denied'));
                this.setupPasteEventListener();
                return;
            }

            const clipboardItems = await navigator.clipboard.read();

            for (const clipboardItem of clipboardItems) {
                for (const type of clipboardItem.types) {
                    if (type.startsWith('image/')) {
                        const blob = await clipboardItem.getType(type);
                        const file = new File([blob], `pasted-image-${Date.now()}.png`, { type });
                        await this.handleFileUpload([file]);
                        this.showNotification('success', this.getText('image_pasted_success'));
                        return;
                    }
                }
            }

            this.showNotification('warning', this.getText('no_images_in_clipboard'));
        } catch (error) {
            console.error('Paste image failed:', error);

            // 根据错误类型提供不同的提示
            if (error.name === 'NotAllowedError') {
                this.showNotification('error', this.getText('clipboard_access_denied'));
            } else if (error.name === 'NotFoundError') {
                this.showNotification('warning', this.getText('no_image_content_in_clipboard'));
            } else {
                this.showNotification('error', this.getText('paste_image_failed'));
            }

            // 设置备用的粘贴事件监听器
            this.setupPasteEventListener();
        }
    }

    /**
     * 设置备用的粘贴事件监听器
     */
    setupPasteEventListener() {
        if (this.pasteListenerSetup) return;

        const pasteHandler = async (e) => {
            e.preventDefault();

            try {
                const items = e.clipboardData?.items;
                if (!items) return;

                for (let i = 0; i < items.length; i++) {
                    const item = items[i];
                    if (item.type.startsWith('image/')) {
                        const file = item.getAsFile();
                        if (file) {
                            await this.handleFileUpload([file]);
                            this.showNotification('success', this.getText('image_pasted_success'));
                            return;
                        }
                    }
                }

                this.showNotification('warning', this.getText('no_images_in_clipboard'));
            } catch (error) {
                console.error('Paste handler error:', error);
                this.showNotification('error', this.getText('paste_error'));
            }
        };

        document.addEventListener('paste', pasteHandler);
        this.pasteListenerSetup = true;

        // 显示提示信息
        this.showNotification('info', this.getText('paste_shortcut_enabled'), 3000);
    }

    /**
     * 清除所有图片
     */
    clearAllImages() {
        if (this.uploadedImages.length === 0) {
            this.showNotification('info', this.getText('no_images_to_clear'));
            return;
        }

        this.uploadedImages = [];
        this.updateImagePreview();
        this.showNotification('success', this.getText('all_images_cleared'));
    }

    /**
     * 保存用户设置到本地存储
     */
    saveUserSettings() {
        try {
            const settings = {
                autoAppend: this.elements.autoAppend?.checked ?? true,
                timestamp: new Date().toISOString()
            };

            localStorage.setItem('feedbackCollectorSettings', JSON.stringify(settings));
            console.log('用户设置已保存:', settings);
        } catch (error) {
            console.error('保存用户设置失败:', error);
        }
    }

    /**
     * 从本地存储加载用户设置
     */
    loadUserSettings() {
        try {
            const settingsStr = localStorage.getItem('feedbackCollectorSettings');
            if (!settingsStr) {
                // 如果没有保存的设置，使用默认值
                console.log('未找到保存的用户设置，使用默认值');
                return;
            }

            const settings = JSON.parse(settingsStr);
            console.log('加载用户设置:', settings);

            // 应用设置
            if (this.elements.autoAppend && typeof settings.autoAppend === 'boolean') {
                this.elements.autoAppend.checked = settings.autoAppend;
            }
        } catch (error) {
            console.error('加载用户设置失败:', error);
            // 如果加载失败，清除可能损坏的数据
            try {
                localStorage.removeItem('feedbackCollectorSettings');
            } catch (e) {
                console.error('清除损坏的设置数据失败:', e);
            }
        }
    }

    /**
     * 重置用户设置为默认值
     */
    resetUserSettings() {
        try {
            localStorage.removeItem('feedbackCollectorSettings');

            // 重置界面
            if (this.elements.autoAppend) {
                this.elements.autoAppend.checked = true;
            }

            this.showNotification('success', this.getText('settings_reset_success') || '设置已重置为默认值');
            console.log('用户设置已重置为默认值');
        } catch (error) {
            console.error('重置用户设置失败:', error);
            this.showNotification('error', this.getText('settings_reset_failed') || '重置设置失败');
        }
    }
}

// 创建全局应用实例
window.feedbackApp = new FeedbackApp();

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.feedbackApp.init();
}); 