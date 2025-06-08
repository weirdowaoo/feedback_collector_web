"""
Web 服务器入口
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict
import uuid
from datetime import datetime
import json

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.core.websocket_manager import WebSocketManager
from src.utils.config import Config
from src.utils.logger import setup_logger
from src.utils.i18n import get_all_texts

# 初始化配置和日志
config = Config()
logger = setup_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="MCP Web Feedback Collector",
    description="Web版MCP反馈收集器",
    version="1.0.0"
)

# 全局WebSocket管理器
websocket_manager: Optional[WebSocketManager] = None
feedback_storage: Dict[str, Dict] = {}  # 存储反馈数据

# 设置静态文件和模板目录
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "web" / "static"
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

# 确保目录存在
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 设置模板引擎
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def set_websocket_manager(manager: WebSocketManager):
    """设置全局WebSocket管理器"""
    global websocket_manager, feedback_storage
    websocket_manager = manager
    # 设置反馈存储
    websocket_manager.set_feedback_storage(feedback_storage)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global websocket_manager, feedback_storage

    try:
        # 检查是否已设置WebSocket管理器，如果没有则创建一个新的
        if websocket_manager is None:
            logger.warning("WebSocket管理器未设置，创建新的WebSocket管理器")
            websocket_manager = WebSocketManager()

        # 设置反馈存储
        websocket_manager.set_feedback_storage(feedback_storage)

        logger.info(f"Web服务器启动成功，监听地址: {config.get_web_url()}")
        logger.info(
            f"使用WebSocket管理器，当前连接数: {websocket_manager.get_connection_count()}")

    except Exception as e:
        logger.error(f"Web服务器启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global websocket_manager

    try:
        if websocket_manager:
            await websocket_manager.cleanup()

        logger.info("Web服务器已关闭")

    except Exception as e:
        logger.error(f"Web服务器关闭时发生错误: {e}")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页面"""
    try:
        # 获取语言参数
        language = request.query_params.get("lang", config.LANGUAGE)

        # 模板上下文
        context = {
            "request": request,
            "language": language,
            "texts": get_all_texts(language),
            "config": {
                "web_host": config.WEB_HOST,
                "web_port": config.WEB_PORT,
                "max_file_size": config.MAX_FILE_SIZE,
                "allowed_extensions": config.ALLOWED_EXTENSIONS,
                "ws_heartbeat_interval": config.WS_HEARTBEAT_INTERVAL
            }
        }

        return templates.TemplateResponse("index.html", context)

    except Exception as e:
        logger.error(f"渲染主页面失败: {e}")
        return HTMLResponse(
            content=f"<h1>页面加载失败</h1><p>错误信息: {str(e)}</p>",
            status_code=500
        )


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "connections": websocket_manager.get_connection_count() if websocket_manager else 0,
        "config": {
            "host": config.WEB_HOST,
            "port": config.WEB_PORT,
            "language": config.LANGUAGE
        }
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接处理"""
    global websocket_manager

    if not websocket_manager:
        await websocket.close(code=1000, reason="WebSocket管理器未初始化")
        return

    # 先接受 WebSocket 连接
    await websocket.accept()

    # 然后通过管理器管理连接
    await websocket_manager.connect(websocket)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            # 处理客户端消息
            await websocket_manager.handle_client_message(websocket, data)

    except WebSocketDisconnect:
        logger.info("WebSocket连接断开")
    except Exception as e:
        logger.error(f"WebSocket处理错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


@app.post("/api/request_feedback")
async def api_request_feedback(request: Request):
    """API 端点：请求用户反馈"""
    global websocket_manager

    if not websocket_manager:
        return {"error": "WebSocket管理器未初始化"}

    try:
        # 解析请求数据
        data = await request.json()
        request_id = data.get("id", str(uuid.uuid4()))
        timeout = data.get("timeout", 600)
        language = data.get("language", "CN")

        # 发送反馈请求到所有客户端
        request_data = {
            "type": "request_feedback",
            "id": request_id,
            "timestamp": datetime.now().isoformat(),
            "timeout": timeout,
            "language": language
        }

        await websocket_manager.broadcast_message(request_data)

        return {
            "status": "success",
            "request_id": request_id,
            "message": "反馈请求已发送"
        }

    except Exception as e:
        logger.error(f"API 请求反馈失败: {e}")
        return {"error": str(e)}


@app.get("/api/feedback/{request_id}")
async def api_get_feedback(request_id: str):
    """API 端点：获取反馈结果"""
    global feedback_storage

    # 检查反馈是否存在
    if request_id in feedback_storage:
        return feedback_storage[request_id]
    else:
        return {
            "status": "waiting",
            "request_id": request_id,
            "message": "等待用户在 Web 界面提交反馈"
        }


async def start_web_server(shared_websocket_manager: Optional[WebSocketManager] = None):
    """启动Web服务器"""
    try:
        # 必须在服务器启动前设置WebSocket管理器
        if shared_websocket_manager:
            set_websocket_manager(shared_websocket_manager)
            logger.info("已设置共享的WebSocket管理器")
        else:
            logger.warning("未提供共享的WebSocket管理器，将创建新实例")
            set_websocket_manager(WebSocketManager())

        # 配置uvicorn
        uvicorn_config = uvicorn.Config(
            app=app,
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            log_level=config.LOG_LEVEL.lower(),
            access_log=True,
            loop="asyncio"
        )

        # 创建服务器实例
        server = uvicorn.Server(uvicorn_config)

        # 在后台任务中运行服务器
        await server.serve()

    except Exception as e:
        logger.error(f"启动Web服务器失败: {e}")
        raise


def run_web_server():
    """运行Web服务器（同步版本）"""
    try:
        uvicorn.run(
            app,
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            log_level=config.LOG_LEVEL.lower(),
            access_log=True
        )
    except Exception as e:
        logger.error(f"运行Web服务器失败: {e}")
        raise


if __name__ == "__main__":
    run_web_server()
