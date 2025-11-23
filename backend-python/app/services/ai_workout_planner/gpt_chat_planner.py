"""GPT-4o chat-based workout planner for real-time interaction."""

import logging
import asyncio
from typing import AsyncGenerator
from collections.abc import AsyncIterator
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class GptChatWorkoutPlanner:
    """
    Chat-based AI workout planner using GPT-4o streaming.

    Maintains conversation state per connection for interactive planning.
    """

    def __init__(self):
        """Initialize OpenAI client and conversation storage."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

        # Store conversation history per connection
        self._conversations: dict[str, list[dict[str, str]]] = {}

        # Store active streaming tasks
        self._active_streams: dict[str, asyncio.Task] = {}

    def initialize_connection(self, connection_id: str) -> None:
        """
        Initialize a new chat conversation.

        Args:
            connection_id: Unique connection identifier
        """
        self._conversations[connection_id] = [
            {
                "role": "system",
                "content": """You are an expert fitness coach and personal trainer. You help users design personalized workout programs through interactive conversation.

Guidelines:
- Ask clarifying questions about goals, experience, and preferences
- Provide evidence-based training recommendations
- Design progressive programs appropriate for the user's level
- Be encouraging and motivational
- Keep responses concise but informative
- Focus on sustainable, long-term fitness habits""",
            }
        ]
        logger.info(f"Initialized chat conversation for {connection_id}")

    async def stream_response(
        self, connection_id: str, user_message: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream GPT-4o response for a user message.

        Args:
            connection_id: Unique connection identifier
            user_message: User's message

        Yields:
            Response chunks from GPT-4o
        """
        if connection_id not in self._conversations:
            self.initialize_connection(connection_id)

        # Add user message to conversation
        self._conversations[connection_id].append(
            {"role": "user", "content": user_message}
        )

        try:
            # Stream response from GPT-4o
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=self._conversations[connection_id],
                stream=True,
                temperature=0.8,
                max_tokens=1000,
            )

            # Collect full response for conversation history
            full_response = ""

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Add assistant's response to conversation history
            self._conversations[connection_id].append(
                {"role": "assistant", "content": full_response}
            )

        except Exception as e:
            logger.error(f"Error streaming GPT response: {e}")
            yield f"\n\n[Error: {str(e)}]"

    def stop_generation(self, connection_id: str) -> None:
        """
        Stop in-progress response generation.

        Args:
            connection_id: Unique connection identifier
        """
        if connection_id in self._active_streams:
            task = self._active_streams[connection_id]
            task.cancel()
            del self._active_streams[connection_id]
            logger.info(f"Stopped generation for {connection_id}")

    def restart_chat(self, connection_id: str) -> None:
        """
        Clear conversation history and restart.

        Args:
            connection_id: Unique connection identifier
        """
        if connection_id in self._conversations:
            del self._conversations[connection_id]
        self.initialize_connection(connection_id)
        logger.info(f"Restarted chat for {connection_id}")

    def cleanup_connection(self, connection_id: str) -> None:
        """
        Clean up resources for a disconnected client.

        Args:
            connection_id: Unique connection identifier
        """
        if connection_id in self._conversations:
            del self._conversations[connection_id]
        if connection_id in self._active_streams:
            self._active_streams[connection_id].cancel()
            del self._active_streams[connection_id]
        logger.info(f"Cleaned up connection {connection_id}")

    def get_conversation_length(self, connection_id: str) -> int:
        """Get number of messages in conversation."""
        if connection_id not in self._conversations:
            return 0
        return len(self._conversations[connection_id])


# Singleton instance
_gpt_chat_workout_planner: GptChatWorkoutPlanner | None = None


def get_gpt_chat_workout_planner() -> GptChatWorkoutPlanner:
    """Dependency injection for GPT chat workout planner."""
    global _gpt_chat_workout_planner
    if _gpt_chat_workout_planner is None:
        _gpt_chat_workout_planner = GptChatWorkoutPlanner()
    return _gpt_chat_workout_planner
