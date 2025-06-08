"""
日志管理模块
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别，默认从环境变量获取

    Returns:
        配置好的日志记录器
    """
    # 获取日志级别
    if level is None:
        level = "INFO"

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # 添加处理器到日志记录器
    logger.addHandler(console_handler)

    return logger


def log_request(logger: logging.Logger, request_id: str, action: str, details: str = ""):
    """
    记录请求日志

    Args:
        logger: 日志记录器
        request_id: 请求ID
        action: 操作类型
        details: 详细信息
    """
    timestamp = datetime.now().isoformat()
    message = f"[{request_id}] {action}"
    if details:
        message += f" - {details}"

    logger.info(message)


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """
    记录错误日志

    Args:
        logger: 日志记录器
        error: 异常对象
        context: 错误上下文
    """
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg = f"{context} - {error_msg}"

    logger.error(error_msg, exc_info=True)
