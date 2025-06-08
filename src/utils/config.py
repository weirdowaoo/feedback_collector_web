"""
配置管理模块
"""

import os
from typing import List


class Config:
    """应用配置类"""

    def __init__(self):
        # Web 服务器配置
        self.WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
        self.WEB_PORT = int(os.getenv("WEB_PORT", "9999"))

        # MCP 配置
        self.MCP_TIMEOUT = int(os.getenv("MCP_DIALOG_TIMEOUT", "600"))

        # 语言配置
        self.LANGUAGE = os.getenv("LANGUAGE", "CN")

        # 文件上传配置
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        self.ALLOWED_EXTENSIONS = [".png", ".jpg",
                                   ".jpeg", ".gif", ".webp", ".bmp"]

        # WebSocket 配置
        self.WS_HEARTBEAT_INTERVAL = int(
            os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
        self.WS_RECONNECT_ATTEMPTS = int(
            os.getenv("WS_RECONNECT_ATTEMPTS", "5"))

        # 日志配置
        self.LOG_LEVEL = "ERROR"

        # 临时文件目录
        self.TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/feedback_collector")

        # 确保临时目录存在
        os.makedirs(self.TEMP_DIR, exist_ok=True)

    def get_web_url(self) -> str:
        """获取Web服务器访问URL"""
        return f"http://{self.WEB_HOST}:{self.WEB_PORT}"

    def is_allowed_file_extension(self, filename: str) -> bool:
        """检查文件扩展名是否被允许"""
        if not filename:
            return False

        ext = os.path.splitext(filename.lower())[1]
        return ext in self.ALLOWED_EXTENSIONS

    def get_language_config(self) -> dict:
        """获取语言配置"""
        return {
            "default": self.LANGUAGE,
            "supported": ["CN", "EN"]
        }
