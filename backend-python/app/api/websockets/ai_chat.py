"""WebSocket endpoint for real-time AI workout chat."""

import json
import logging
from uuid import uuid4
from typing import Annotated
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_rate_limit_db
from app.core.enums import AppStore
from app.services.purchase_verification.facade import (
    PurchaseVerificationService,
    get_purchase_verification_service,
)
from app.services.rate_limit import RateLimitService, get_rate_limit_service
from app.services.ai_workout_planner.gpt_chat_planner import (
    GptChatWorkoutPlanner,
    get_gpt_chat_workout_planner,
)

logger = logging.getLogger(__name__)


async def ai_chat_websocket(
    websocket: WebSocket,
    planner: Annotated[GptChatWorkoutPlanner, Depends(get_gpt_chat_workout_planner)],
    verification_service: Annotated[
        PurchaseVerificationService, Depends(get_purchase_verification_service)
    ],
    rate_limit_db: Annotated[AsyncSession, Depends(get_rate_limit_db)],
):
    """
    WebSocket endpoint for real-time AI workout chat.

    Implements SignalR-compatible message format:
    Client sends: {"method": "MethodName", "arguments": [...]}
    Server responds: Text chunks or {"error": "message"}

    Methods:
    - Introduce: Authenticate with purchase token
    - SendMessage: Send chat message and get streaming response
    - StopInProgress: Stop current response generation
    - RestartChat: Clear conversation and start fresh
    """
    await websocket.accept()
    connection_id = str(uuid4())
    authenticated = False
    app_store = None
    pro_token = None

    logger.info(f"WebSocket connection established: {connection_id}")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            method = message.get("method")
            args = message.get("arguments", [])

            if method == "Introduce":
                # Authenticate the connection
                if len(args) < 2:
                    await websocket.send_json(
                        {"error": "Invalid Introduce arguments"}
                    )
                    continue

                try:
                    app_store = AppStore(args[0])
                    pro_token = args[1]
                except (ValueError, IndexError):
                    await websocket.send_json({"error": "Invalid app store or token"})
                    continue

                # Verify purchase token
                is_valid = await verification_service.is_valid_purchase_token(
                    app_store, pro_token
                )

                if not is_valid:
                    await websocket.send_json({"error": "Invalid purchase token"})
                    await websocket.close(code=1008)  # Policy violation
                    return

                # Check rate limits
                rate_limiter = await get_rate_limit_service(rate_limit_db)
                rate_limit_result = await rate_limiter.check_rate_limit(
                    app_store, pro_token
                )

                if rate_limit_result.is_rate_limited:
                    retry_after = rate_limit_result.retry_after
                    await websocket.send_json(
                        {
                            "error": "Rate limit exceeded",
                            "retry_after": retry_after.isoformat()
                            if retry_after
                            else None,
                        }
                    )
                    await websocket.close(code=1008)
                    return

                authenticated = True
                planner.initialize_connection(connection_id)
                await websocket.send_text("Authenticated. Ready to chat!")
                logger.info(f"Connection {connection_id} authenticated")

            elif method == "SendMessage":
                if not authenticated:
                    await websocket.send_json({"error": "Not authenticated"})
                    continue

                if len(args) < 1:
                    await websocket.send_json({"error": "Message required"})
                    continue

                user_message = args[0]

                # Stream GPT response
                try:
                    async for chunk in planner.stream_response(
                        connection_id, user_message
                    ):
                        await websocket.send_text(chunk)
                except Exception as e:
                    logger.error(f"Error streaming response: {e}")
                    await websocket.send_json({"error": str(e)})

            elif method == "StopInProgress":
                planner.stop_generation(connection_id)
                await websocket.send_text("[Generation stopped]")

            elif method == "RestartChat":
                planner.restart_chat(connection_id)
                await websocket.send_text("Chat restarted. Let's begin again!")

            else:
                await websocket.send_json({"error": f"Unknown method: {method}"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        # Cleanup
        planner.cleanup_connection(connection_id)
        logger.info(f"Cleaned up connection: {connection_id}")
