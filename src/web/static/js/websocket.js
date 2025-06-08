/**
 * WebSocket 通信管理器
 */
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1秒
        this.heartbeatInterval = null;
        this.messageHandlers = new Map();
        this.connectionCallbacks = [];

        // 绑定方法
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.send = this.send.bind(this);
        this.onMessage = this.onMessage.bind(this);
        this.onOpen = this.onOpen.bind(this);
        this.onClose = this.onClose.bind(this);
        this.onError = this.onError.bind(this);
    }

    /**
     * 连接到WebSocket服务器
     */
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;

            console.log('Connecting to WebSocket:', wsUrl);

            this.ws = new WebSocket(wsUrl);
            this.ws.onopen = this.onOpen;
            this.ws.onmessage = this.onMessage;
            this.ws.onclose = this.onClose;
            this.ws.onerror = this.onError;

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * 断开WebSocket连接
     */
    disconnect() {
        this.isConnected = false;
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * 发送消息到服务器
     */
    send(data) {
        if (!this.isConnected || !this.ws) {
            console.warn('WebSocket not connected, cannot send message:', data);
            return false;
        }

        try {
            const message = JSON.stringify(data);
            this.ws.send(message);
            console.log('Sending message:', data);
            return true;
        } catch (error) {
            console.error('Failed to send message:', error);
            return false;
        }
    }

    /**
     * 连接打开事件
     */
    onOpen(event) {
        console.log('WebSocket connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // 启动心跳
        this.startHeartbeat();

        // 更新连接状态
        this.updateConnectionStatus('connected');

        // 通知连接回调
        this.connectionCallbacks.forEach(callback => {
            try {
                callback('connected');
            } catch (error) {
                console.error('Connection callback execution failed:', error);
            }
        });
    }

    /**
     * 接收消息事件
     */
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);

            const messageType = data.type;
            if (this.messageHandlers.has(messageType)) {
                const handler = this.messageHandlers.get(messageType);
                handler(data);
            } else {
                console.warn('Unknown message type:', messageType);
            }

        } catch (error) {
            console.error('Message processing failed:', error);
        }
    }

    /**
     * 连接关闭事件
     */
    onClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();

        // 更新连接状态
        this.updateConnectionStatus('disconnected');

        // 通知连接回调
        this.connectionCallbacks.forEach(callback => {
            try {
                callback('disconnected');
            } catch (error) {
                console.error('Connection callback execution failed:', error);
            }
        });

        // 尝试重连（如果不是主动关闭）
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }

    /**
     * 连接错误事件
     */
    onError(event) {
        console.error('WebSocket connection error:', event);
        this.updateConnectionStatus('error');
    }

    /**
     * 安排重连
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Maximum reconnection attempts reached, stopping reconnection');
            this.updateConnectionStatus('failed');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // 指数退避

        console.log(`Attempting reconnection #${this.reconnectAttempts} in ${delay}ms`);
        this.updateConnectionStatus('reconnecting');

        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }

    /**
     * 启动心跳
     */
    startHeartbeat() {
        this.stopHeartbeat();

        const interval = (window.APP_CONFIG?.wsHeartbeatInterval || 30) * 1000;
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'heartbeat',
                    timestamp: new Date().toISOString()
                });
            }
        }, interval);
    }

    /**
     * 停止心跳
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    /**
     * 注册消息处理器
     */
    onMessageType(type, handler) {
        this.messageHandlers.set(type, handler);
    }

    /**
     * 移除消息处理器
     */
    offMessageType(type) {
        this.messageHandlers.delete(type);
    }

    /**
     * 注册连接状态回调
     */
    onConnectionChange(callback) {
        this.connectionCallbacks.push(callback);
    }

    /**
     * 更新连接状态显示
     */
    updateConnectionStatus(status) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const connectionCount = document.getElementById('connectionCount');

        if (!statusIndicator || !statusText) return;

        // 清除所有状态类
        statusIndicator.className = 'status-indicator';

        // 获取文本配置
        const texts = window.APP_CONFIG?.texts || {};

        switch (status) {
            case 'connected':
                statusIndicator.classList.add('connected');
                statusText.textContent = texts.connected || 'Connected';
                break;
            case 'disconnected':
                statusIndicator.classList.add('disconnected');
                statusText.textContent = texts.disconnected || 'Disconnected';
                break;
            case 'reconnecting':
                statusText.textContent = texts.reconnecting || 'Reconnecting...';
                break;
            case 'error':
            case 'failed':
                statusIndicator.classList.add('disconnected');
                statusText.textContent = texts.error || 'Connection Error';
                break;
            default:
                statusText.textContent = texts.connecting || 'Connecting...';
        }

        // 更新连接数（如果可用）
        if (connectionCount && status === 'connected') {
            // 这里可以从服务器获取连接数，暂时设为1
            connectionCount.textContent = '1';
        } else if (connectionCount) {
            connectionCount.textContent = '0';
        }
    }

    /**
     * 获取连接状态
     */
    getConnectionStatus() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED
        };
    }
}

// 创建全局WebSocket管理器实例
window.wsManager = new WebSocketManager();

// 页面加载完成后自动连接
document.addEventListener('DOMContentLoaded', () => {
    window.wsManager.connect();
});

// 页面卸载时断开连接
window.addEventListener('beforeunload', () => {
    window.wsManager.disconnect();
}); 