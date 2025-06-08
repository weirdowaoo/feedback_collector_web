#!/usr/bin/env python3
"""
独立的 MCP 服务器
通过 HTTP API 与 Web 服务器通信
"""

from src.utils.logger import setup_logger
from src.utils.i18n import get_text
from fastmcp import FastMCP, Image
from typing import List, Union, Any
import asyncio
import json
import uuid
import aiohttp
import base64
from datetime import datetime
from pathlib import Path
import sys
import os

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# 初始化日志
logger = setup_logger(__name__)

# 创建 MCP 应用
mcp = FastMCP("MCP Web Feedback Collector")

# Web 服务器配置
WEB_HOST = os.getenv("WEB_HOST", "localhost")
WEB_PORT = os.getenv("WEB_PORT", "9999")
WEB_BASE_URL = f"http://{WEB_HOST}:{WEB_PORT}"

# 反馈收集配置
FEEDBACK_TIMEOUT = int(os.getenv("FEEDBACK_TIMEOUT", "600"))


@mcp.tool()
async def collect_feedback() -> List[Union[str, Image]]:
    """
    收集用户反馈的交互式工具。
    显示反馈收集界面，用户可以提供文字和/或图片反馈。

    Returns:
        包含用户反馈内容的列表，包括文本内容和图片内容
    """
    try:
        # 生成唯一请求ID
        request_id = str(uuid.uuid4())

        logger.info(f"开始收集反馈，请求ID: {request_id}")

        # 通过 HTTP API 发送反馈请求
        async with aiohttp.ClientSession() as session:
            # 1. 发送反馈请求
            request_data = {
                "id": request_id,
                "timeout": FEEDBACK_TIMEOUT
            }

            try:
                async with session.post(
                    f"{WEB_BASE_URL}/api/request_feedback",
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        error_msg = f"发送反馈请求失败: HTTP {response.status}"
                        logger.error(error_msg)
                        return [error_msg]

                    result = await response.json()
                    if result.get("status") != "success":
                        error_msg = f"发送反馈请求失败: {result.get('error', '未知错误')}"
                        logger.error(error_msg)
                        return [error_msg]

            except asyncio.TimeoutError:
                return ["连接 Web 服务器超时，请确保 Web 服务器正在运行"]
            except aiohttp.ClientError as e:
                return [f"连接 Web 服务器失败: {str(e)}。请确保 Web 服务器正在运行在 {WEB_BASE_URL}"]

            logger.info("反馈请求已发送，等待用户在 Web 界面提交反馈...")

            # 2. 轮询等待反馈结果
            start_time = datetime.now()
            poll_interval = 2  # 每2秒检查一次

            while True:
                # 检查是否超时
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= FEEDBACK_TIMEOUT:
                    return ["反馈收集超时，请重试"]

                # 等待一段时间再检查
                await asyncio.sleep(poll_interval)

                # 检查反馈状态
                try:
                    async with session.get(
                        f"{WEB_BASE_URL}/api/feedback/{request_id}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result = await response.json()

                            if result.get("status") == "completed":
                                # 反馈已完成
                                feedback_data = result.get("data", {})

                                # 从反馈数据中获取用户选择的语言
                                user_language = feedback_data.get(
                                    "language", "CN")

                                # 构建返回内容列表
                                content_list = []

                                # 处理文字反馈
                                if feedback_data.get("text"):
                                    text_prefix = get_text(
                                        "user_text_feedback", user_language)
                                    text_content = f"{text_prefix}{feedback_data['text']}"
                                    content_list.append(text_content)

                                # 处理图片反馈
                                if feedback_data.get("images"):
                                    images_prefix = get_text(
                                        "user_uploaded_images", user_language)
                                    content_list.append(images_prefix)

                                    for i, img in enumerate(feedback_data["images"]):
                                        # 获取图片信息
                                        img_name = img.get(
                                            'name', f'image_{i+1}')
                                        img_size = img.get('size', 0)
                                        img_data = img.get('data', '')
                                        img_type = img.get('type', 'image/png')

                                        # 添加图片描述文本
                                        if user_language == "EN":
                                            img_description = f"Image {i+1}: {img_name} ({img_size} bytes)"
                                        else:
                                            img_description = f"图片{i+1}: {img_name} ({img_size} bytes)"
                                        content_list.append(img_description)

                                        # 处理图片数据
                                        if img_data:
                                            try:
                                                # 如果数据包含 data URL 前缀，去除它
                                                if img_data.startswith('data:'):
                                                    # 格式: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
                                                    img_data = img_data.split(',', 1)[
                                                        1]

                                                # 解码 base64 数据
                                                img_bytes = base64.b64decode(
                                                    img_data)

                                                # 确定图片格式
                                                img_format = "png"  # 默认格式
                                                if img_type:
                                                    if "jpeg" in img_type or "jpg" in img_type:
                                                        img_format = "jpeg"
                                                    elif "gif" in img_type:
                                                        img_format = "gif"
                                                    elif "webp" in img_type:
                                                        img_format = "webp"

                                                # 创建 Image 对象
                                                image_obj = Image(
                                                    data=img_bytes, format=img_format)
                                                content_list.append(image_obj)

                                                logger.debug(
                                                    f"成功处理图片 {img_name}，格式: {img_format}，大小: {len(img_bytes)} bytes")

                                            except Exception as e:
                                                logger.error(
                                                    f"处理图片 {img_name} 时出错: {str(e)}")
                                                error_text = f"图片处理失败: {img_name} - {str(e)}" if user_language == "CN" else f"Image processing failed: {img_name} - {str(e)}"
                                                content_list.append(error_text)

                                # 如果没有任何反馈内容，添加空反馈提示
                                if not content_list:
                                    empty_feedback_text = get_text(
                                        "user_empty_feedback", user_language)
                                    content_list.append(empty_feedback_text)

                                # 根据用户设置决定是否添加自动附加prompt
                                auto_append = feedback_data.get(
                                    "auto_append", True)
                                if auto_append:
                                    # 根据语言添加重要提示
                                    auto_append_text = f"{get_text('auto_append_prompt', user_language)}"
                                    content_list.append(auto_append_text)

                                logger.info(
                                    f"反馈收集完成，请求ID: {request_id}, 自动附加prompt: {auto_append}, 内容项数: {len(content_list)}")
                                return content_list

                            elif result.get("status") == "cancelled":
                                # 反馈被用户取消
                                cancel_data = result.get("data", {})
                                cancel_reason = cancel_data.get(
                                    "reason", "用户取消")
                                logger.info(
                                    f"反馈被取消，请求ID: {request_id}, 原因: {cancel_reason}")
                                return [f"反馈收集已取消: {cancel_reason}"]

                            elif result.get("status") == "error":
                                error_msg = result.get("message", "反馈处理出错")
                                logger.error(f"反馈处理错误: {error_msg}")
                                return [f"反馈收集失败: {error_msg}"]

                            # 状态为 waiting，继续等待

                except asyncio.TimeoutError:
                    logger.warning("检查反馈状态超时，继续等待...")
                    continue
                except aiohttp.ClientError as e:
                    logger.warning(f"检查反馈状态失败: {e}，继续等待...")
                    continue

    except Exception as e:
        error_msg = f"反馈收集出错: {str(e)}"
        logger.error(error_msg)
        return [error_msg]


if __name__ == "__main__":
    # 运行 MCP 服务器
    mcp.run()
