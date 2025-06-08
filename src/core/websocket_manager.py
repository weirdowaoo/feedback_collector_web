"""
WebSocket 连接管理器
"""

import asyncio
import json
import weakref
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from src.utils.logger import setup_logger, log_request, log_error

logger = setup_logger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 使用弱引用集合存储活跃连接
        self._connections: Set[WebSocket] = set()
        self._connection_info: Dict[WebSocket, Dict] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # 心跳间隔（秒）
        self._feedback_storage: Optional[Dict] = None

    def set_feedback_storage(self, feedback_storage: Dict):
        """设置反馈存储引用"""
        self._feedback_storage = feedback_storage

    async def connect(self, websocket: WebSocket, client_info: Optional[Dict] = None):
        """
        管理新的WebSocket连接（连接应该已经被接受）

        Args:
            websocket: WebSocket连接对象
            client_info: 客户端信息
        """
        try:
            # 注意：WebSocket 连接应该在调用此方法之前已经被接受
            self._connections.add(websocket)

            # 存储连接信息
            info = {
                "connected_at": datetime.now().isoformat(),
                "client_info": client_info or {},
                "last_heartbeat": datetime.now().isoformat()
            }
            self._connection_info[websocket] = info

            logger.info(f"新的WebSocket连接已建立，当前连接数: {len(self._connections)}")

            # 启动心跳任务（如果还没有启动）
            if self._heartbeat_task is None or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(
                    self._heartbeat_loop())

            # 发送连接确认消息
            await self.send_to_client(websocket, {
                "type": "connection_established",
                "timestamp": datetime.now().isoformat(),
                "message": "WebSocket连接已建立"
            })

        except Exception as e:
            log_error(logger, e, "WebSocket连接建立失败")
            raise

    async def disconnect(self, websocket: WebSocket):
        """
        断开WebSocket连接

        Args:
            websocket: WebSocket连接对象
        """
        try:
            if websocket in self._connections:
                self._connections.remove(websocket)

            if websocket in self._connection_info:
                del self._connection_info[websocket]

            logger.info(f"WebSocket连接已断开，当前连接数: {len(self._connections)}")

        except Exception as e:
            log_error(logger, e, "WebSocket连接断开处理失败")

    async def send_to_client(self, websocket: WebSocket, data: Dict):
        """
        向指定客户端发送消息

        Args:
            websocket: WebSocket连接对象
            data: 要发送的数据
        """
        try:
            if websocket in self._connections:
                message = json.dumps(data, ensure_ascii=False)
                await websocket.send_text(message)

        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            log_error(logger, e, f"向客户端发送消息失败: {data}")

    async def broadcast_message(self, data: Dict):
        """
        向所有连接的客户端广播消息

        Args:
            data: 要广播的数据
        """
        if not self._connections:
            logger.warning("没有活跃的WebSocket连接，无法广播消息")
            return

        message = json.dumps(data, ensure_ascii=False)
        disconnected_clients = []

        for websocket in self._connections.copy():
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.append(websocket)
            except Exception as e:
                log_error(logger, e, f"向客户端广播消息失败")
                disconnected_clients.append(websocket)

        # 清理断开的连接
        for websocket in disconnected_clients:
            await self.disconnect(websocket)

        logger.info(f"消息已广播到 {len(self._connections)} 个客户端")

    async def handle_client_message(self, websocket: WebSocket, message: str):
        """
        处理客户端发送的消息

        Args:
            websocket: WebSocket连接对象
            message: 客户端消息
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "heartbeat":
                await self._handle_heartbeat(websocket, data)
            elif message_type == "feedback_submit":
                await self._handle_feedback_submission(websocket, data)
            elif message_type == "feedback_cancel":
                await self._handle_feedback_cancellation(websocket, data)

            elif message_type == "request_feedback":
                # request_feedback 应该由服务器发送到客户端，而不是从客户端接收
                logger.warning(f"收到客户端发送的 request_feedback 消息，这通常是测试脚本的错误用法")
                await self.send_to_client(websocket, {
                    "type": "error",
                    "message": "request_feedback 消息应该由服务器发送，而不是客户端发送"
                })
            else:
                logger.warning(f"收到未知类型的消息: {message_type}")
                await self.send_to_client(websocket, {
                    "type": "error",
                    "message": f"未知的消息类型: {message_type}"
                })

        except json.JSONDecodeError:
            logger.error(f"收到无效的JSON消息: {message}")
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "无效的JSON格式"
            })
        except Exception as e:
            log_error(logger, e, "处理客户端消息失败")

    async def _handle_heartbeat(self, websocket: WebSocket, data: Dict):
        """处理心跳消息"""
        if websocket in self._connection_info:
            self._connection_info[websocket]["last_heartbeat"] = datetime.now(
            ).isoformat()

        # 回复心跳
        await self.send_to_client(websocket, {
            "type": "heartbeat_response",
            "timestamp": datetime.now().isoformat()
        })

    async def _handle_feedback_submission(self, websocket: WebSocket, data: Dict):
        """处理反馈提交消息"""
        logger.info(f"收到反馈提交请求: {data.get('request_id', 'unknown')}")
        logger.info(f"反馈存储对象: {type(self._feedback_storage)}")
        logger.info(f"反馈存储内容: {self._feedback_storage}")

        if self._feedback_storage is None:
            logger.error("反馈存储未设置")
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "服务器配置错误"
            })
            return

        request_id = data.get("request_id")
        if request_id:
            # 存储反馈数据
            self._feedback_storage[request_id] = {
                "status": "completed",
                "data": {
                    "text": data.get("text", ""),
                    "images": data.get("images", []),
                    "auto_append": data.get("auto_append", True),
                    "language": data.get("language", "CN"),
                    "timestamp": data.get("timestamp", datetime.now().isoformat())
                },
                "completed_at": datetime.now().isoformat()
            }

            logger.info(
                f"反馈已存储，请求ID: {request_id}, 自动附加: {data.get('auto_append', True)}")

            # 向客户端发送确认
            await self.send_to_client(websocket, {
                "type": "feedback_received",
                "request_id": request_id,
                "status": "success"
            })
        else:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "缺少请求ID"
            })

    async def _handle_feedback_cancellation(self, websocket: WebSocket, data: Dict):
        """处理反馈取消消息"""
        logger.info(f"收到反馈取消请求: {data.get('request_id', 'unknown')}")

        if self._feedback_storage is None:
            logger.error("反馈存储未设置")
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "服务器配置错误"
            })
            return

        request_id = data.get("request_id")
        if request_id:
            # 存储取消状态
            self._feedback_storage[request_id] = {
                "status": "cancelled",
                "data": {
                    "reason": "用户取消",
                    "timestamp": data.get("timestamp", datetime.now().isoformat())
                },
                "cancelled_at": datetime.now().isoformat()
            }

            logger.info(f"反馈已取消，请求ID: {request_id}")

            # 向客户端发送确认
            await self.send_to_client(websocket, {
                "type": "feedback_cancelled",
                "request_id": request_id,
                "status": "success"
            })
        else:
            await self.send_to_client(websocket, {
                "type": "error",
                "message": "缺少请求ID"
            })

    async def _heartbeat_loop(self):
        """心跳循环任务"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                if not self._connections:
                    continue

                # 发送心跳请求
                heartbeat_data = {
                    "type": "heartbeat_request",
                    "timestamp": datetime.now().isoformat()
                }

                await self.broadcast_message(heartbeat_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error(logger, e, "心跳循环任务错误")

    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self._connections)

    def get_connection_info(self) -> List[Dict]:
        """获取所有连接信息"""
        return list(self._connection_info.values())

    async def cleanup(self):
        """清理资源"""
        try:
            # 取消心跳任务
            if self._heartbeat_task and not self._heartbeat_task.done():
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass

            # 关闭所有连接
            for websocket in self._connections.copy():
                try:
                    await websocket.close()
                except Exception:
                    pass

            self._connections.clear()
            self._connection_info.clear()

            logger.info("WebSocket管理器资源清理完成")

        except Exception as e:
            log_error(logger, e, "WebSocket管理器清理失败")
