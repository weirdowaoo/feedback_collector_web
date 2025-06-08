"""
国际化模块
集中管理所有多语言文本
"""

from typing import Dict, Any


class I18n:
    """国际化文本管理类"""

    # 所有文本定义
    TEXTS = {
        "CN": {
            # 通用
            "connecting": "连接中...",
            "connected": "已连接",
            "disconnected": "连接断开",
            "reconnecting": "重新连接中...",
            "error": "发生错误",
            "success": "成功",
            "warning": "警告",
            "info": "信息",
            "cancel": "取消",
            "submit": "提交",
            "clear": "清除",
            "select": "选择",
            "paste": "粘贴",

            # 页面标题和头部
            "page_title": "MCP Web 反馈收集器",
            "app_title": "MCP Web 反馈收集器",



            # 等待状态
            "waiting_title": "等待反馈请求...",
            "waiting_description": "当AI需要收集反馈时，此界面将自动激活",

            # 反馈表单
            "text_feedback_label": "文字反馈",
            "text_feedback_placeholder": "请输入您的反馈内容...",
            "image_feedback_label": "图片反馈",
            "select_image": "选择图片",
            "paste_image": "粘贴图片",
            "clear_images": "清除图片",
            "no_images_selected": "未选择图片",
            "auto_append_label": "自动附加设置",
            "auto_append_description": "自动附加调用反馈收集器 prompt",
            "submit_feedback": "提交反馈",

            # 操作提示
            "shortcuts_hint": "快捷键：⌘+Enter (Ctrl+Enter) 提交反馈，ESC 取消",
            "timeout_hint": "对话框将在 10 分钟后自动关闭",

            # 反馈状态
            "feedback_requested": "请提供反馈",
            "submitting": "提交中...",
            "submitted": "提交成功",
            "cancelled": "已取消",
            "timeout": "请求超时",

            # 消息提示
            "submit_success": "反馈提交成功",
            "submit_error": "反馈提交失败",
            "connection_lost": "连接丢失，正在重连...",
            "connection_restored": "连接已恢复",
            "feedback_submitted_success": "您的反馈已成功提交",
            "send_failed": "发送失败，请检查网络连接",
            "enter_feedback_or_upload": "请输入反馈内容或上传图片",

            # 文件上传
            "file_too_large": "文件过大",
            "file_type_not_supported": "不支持的文件类型",
            "processing_failed": "处理失败",
            "image_pasted_success": "图片粘贴成功",
            "no_images_in_clipboard": "剪贴板中没有找到图片",
            "paste_error": "粘贴图片时发生错误",
            "clipboard_api_not_supported": "您的浏览器不支持剪贴板API，请尝试使用Ctrl+V快捷键",
            "clipboard_permission_denied": "剪贴板读取权限被拒绝，请在浏览器设置中允许此权限",
            "paste_shortcut_enabled": "已启用Ctrl+V快捷键粘贴图片功能",
            "no_images_to_clear": "没有图片需要清除",
            "all_images_cleared": "已清除所有图片",
            "delete_image": "删除图片",
            "clipboard_access_denied": "剪贴板访问被拒绝，请允许浏览器访问剪贴板或使用Ctrl+V快捷键",
            "no_image_content_in_clipboard": "剪贴板中没有找到图片内容",
            "paste_image_failed": "粘贴图片失败，请尝试使用Ctrl+V快捷键或重新复制图片",

            # MCP 工具相关
            "user_text_feedback": "用户文字反馈：",
            "user_uploaded_images": "用户上传图片：",
            "user_empty_feedback": "用户提交了空反馈",
            "feedback_collection_timeout": "用户反馈收集超时或被取消",
            "feedback_collection_error": "反馈收集过程中发生错误",
            "mcp_components_not_initialized": "MCP 服务器组件未正确初始化，请重启服务器",
            "auto_append_prompt": "\n\n以下是你需要非常注意的 2 点：\n1. 对以上用户反馈进行处理（或回答）。\n2. 在处理完（或回答完）以上用户反馈后，必须重新调用 <feedback-collector-web.collect_feedback> MCP 以获取用户反馈",

            # Web 服务器连接相关
            "web_server_timeout": "连接 Web 服务器超时，请确保 Web 服务器正在运行",
            "web_server_connection_failed": "连接 Web 服务器失败，请确保 Web 服务器正在运行",
            "connections_label": "连接数：",
        },

        "EN": {
            # 通用
            "connecting": "Connecting...",
            "connected": "Connected",
            "disconnected": "Disconnected",
            "reconnecting": "Reconnecting...",
            "error": "Error",
            "success": "Success",
            "warning": "Warning",
            "info": "Info",
            "cancel": "Cancel",
            "submit": "Submit",
            "clear": "Clear",
            "select": "Select",
            "paste": "Paste",

            # 页面标题和头部
            "page_title": "MCP Web Feedback Collector",
            "app_title": "MCP Web Feedback Collector",



            # 等待状态
            "waiting_title": "Waiting for feedback request...",
            "waiting_description": "This interface will activate automatically when AI needs to collect feedback",

            # 反馈表单
            "text_feedback_label": "Text Feedback",
            "text_feedback_placeholder": "Please enter your feedback...",
            "image_feedback_label": "Image Feedback",
            "select_image": "Select Image",
            "paste_image": "Paste Image",
            "clear_images": "Clear Images",
            "no_images_selected": "No images selected",
            "auto_append_label": "Automatic Append Settings",
            "auto_append_description": "Automatically Append Feedback Collector Prompt",
            "submit_feedback": "Submit Feedback",

            # 操作提示
            "shortcuts_hint": "Shortcuts: ⌘+Enter (Ctrl+Enter) to submit, ESC to cancel",
            "timeout_hint": "Dialog will close automatically in 10 minutes",

            # 反馈状态
            "feedback_requested": "Please provide feedback",
            "submitting": "Submitting...",
            "submitted": "Submitted",
            "cancelled": "Cancelled",
            "timeout": "Timeout",

            # 消息提示
            "submit_success": "Feedback submitted successfully",
            "submit_error": "Feedback submission failed",
            "connection_lost": "Connection lost, reconnecting...",
            "connection_restored": "Connection restored",
            "feedback_submitted_success": "Your feedback has been successfully submitted",
            "send_failed": "Send failed, please check network connection",
            "enter_feedback_or_upload": "Please enter feedback content or upload images",

            # 文件上传
            "file_too_large": "File too large",
            "file_type_not_supported": "File type not supported",
            "processing_failed": "Processing failed",
            "image_pasted_success": "Image pasted successfully",
            "no_images_in_clipboard": "No images found in clipboard",
            "paste_error": "Error occurred while pasting image",
            "clipboard_api_not_supported": "Your browser does not support Clipboard API, please try using Ctrl+V shortcut",
            "clipboard_permission_denied": "Clipboard read permission denied, please allow this permission in browser settings",
            "paste_shortcut_enabled": "Ctrl+V shortcut for pasting images is now enabled",
            "no_images_to_clear": "No images to clear",
            "all_images_cleared": "All images cleared",
            "delete_image": "Delete image",
            "clipboard_access_denied": "Clipboard access denied, please allow browser to access clipboard or use Ctrl+V shortcut",
            "no_image_content_in_clipboard": "No image content found in clipboard",
            "paste_image_failed": "Failed to paste image, please try using Ctrl+V shortcut or copy the image again",

            # MCP 工具相关
            "user_text_feedback": "User text feedback: ",
            "user_uploaded_images": "User uploaded images: ",
            "user_empty_feedback": "User submitted empty feedback",
            "feedback_collection_timeout": "User feedback collection timed out or was cancelled",
            "feedback_collection_error": "Error occurred during feedback collection",
            "mcp_components_not_initialized": "MCP server components not properly initialized, please restart the server",
            "auto_append_prompt": "\n\nThe following are the 2 points you must pay attention to:\n1. Process (or answer) the above user feedback.\n2. After processing (or answering) the above user feedback, you must re-call <feedback-collector-web.collect_feedback> MCP to get user feedback",

            # Web 服务器连接相关
            "web_server_timeout": "Web server connection timeout, please ensure the web server is running",
            "web_server_connection_failed": "Failed to connect to web server, please ensure the web server is running",
            "connections_label": "Connections: ",
        }
    }

    def __init__(self, language: str = "CN"):
        """
        初始化国际化实例

        Args:
            language: 语言代码，CN 或 EN
        """
        self.language = language if language in self.TEXTS else "CN"

    def get(self, key: str, default: str = None) -> str:
        """
        获取指定键的文本

        Args:
            key: 文本键
            default: 默认值，如果未找到则返回此值

        Returns:
            对应语言的文本
        """
        texts = self.TEXTS.get(self.language, self.TEXTS["CN"])
        return texts.get(key, default or key)

    def set_language(self, language: str):
        """
        设置语言

        Args:
            language: 语言代码，CN 或 EN
        """
        if language in self.TEXTS:
            self.language = language

    def get_all_texts(self, language: str = None) -> Dict[str, str]:
        """
        获取指定语言的所有文本

        Args:
            language: 语言代码，如果为None则使用当前语言

        Returns:
            包含所有文本的字典
        """
        lang = language or self.language
        return self.TEXTS.get(lang, self.TEXTS["CN"])

    def get_supported_languages(self) -> list:
        """
        获取支持的语言列表

        Returns:
            支持的语言代码列表
        """
        return list(self.TEXTS.keys())


# 创建默认实例
default_i18n = I18n()


def get_text(key: str, language: str = "CN", default: str = None) -> str:
    """
    便捷函数：获取指定语言的文本

    Args:
        key: 文本键
        language: 语言代码
        default: 默认值

    Returns:
        对应语言的文本
    """
    i18n = I18n(language)
    return i18n.get(key, default)


def get_all_texts(language: str = "CN") -> Dict[str, str]:
    """
    便捷函数：获取指定语言的所有文本

    Args:
        language: 语言代码

    Returns:
        包含所有文本的字典
    """
    i18n = I18n(language)
    return i18n.get_all_texts()
