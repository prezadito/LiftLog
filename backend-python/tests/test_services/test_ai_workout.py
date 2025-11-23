"""Tests for AI workout planner services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ai_workout_planner.gpt_planner import GptAiWorkoutPlanner
from app.services.ai_workout_planner.gpt_chat_planner import GptChatWorkoutPlanner
from app.models.schemas.ai_workout import AiWorkoutAttributes, AiSessionAttributes
from app.core.enums import ExperienceLevel


@pytest.mark.asyncio
async def test_gpt_planner_initialization():
    """Test GPT workout planner initialization."""
    planner = GptAiWorkoutPlanner()
    assert planner.client is not None
    assert planner.model == "gpt-4o"


@pytest.mark.asyncio
async def test_build_workout_plan_prompt():
    """Test workout plan prompt building."""
    planner = GptAiWorkoutPlanner()

    attrs = AiWorkoutAttributes(
        age=30,
        gender="male",
        weight_kg=75.0,
        experience_level=ExperienceLevel.INTERMEDIATE,
        goals="Build muscle and strength",
        days_per_week=4,
        additional_preferences="Focus on compound movements",
    )

    prompt = planner._build_workout_plan_prompt(attrs)

    assert "30" in prompt
    assert "male" in prompt
    assert "75" in prompt
    assert "Intermediate" in prompt
    assert "4-day" in prompt
    assert "Build muscle and strength" in prompt
    assert "compound movements" in prompt


@pytest.mark.asyncio
async def test_build_session_prompt():
    """Test session prompt building."""
    planner = GptAiWorkoutPlanner()

    attrs = AiSessionAttributes(
        age=25,
        gender="female",
        weight_kg=60.0,
        experience_level=ExperienceLevel.BEGINNER,
        focus="Upper body strength",
        duration_minutes=45,
        available_equipment="Dumbbells, resistance bands",
    )

    prompt = planner._build_session_prompt(attrs)

    assert "45-minute" in prompt
    assert "25" in prompt
    assert "female" in prompt
    assert "Beginner" in prompt
    assert "Upper body strength" in prompt
    assert "Dumbbells, resistance bands" in prompt


@pytest.mark.asyncio
async def test_chat_planner_initialization():
    """Test chat workout planner initialization."""
    planner = GptChatWorkoutPlanner()
    connection_id = "test-connection-123"

    planner.initialize_connection(connection_id)

    assert connection_id in planner._conversations
    assert len(planner._conversations[connection_id]) == 1  # System message
    assert planner._conversations[connection_id][0]["role"] == "system"


@pytest.mark.asyncio
async def test_chat_planner_restart():
    """Test chat conversation restart."""
    planner = GptChatWorkoutPlanner()
    connection_id = "test-connection-456"

    # Initialize and add a message
    planner.initialize_connection(connection_id)
    planner._conversations[connection_id].append(
        {"role": "user", "content": "Hello"}
    )

    assert len(planner._conversations[connection_id]) == 2

    # Restart should reset to just system message
    planner.restart_chat(connection_id)
    assert len(planner._conversations[connection_id]) == 1
    assert planner._conversations[connection_id][0]["role"] == "system"


@pytest.mark.asyncio
async def test_chat_planner_cleanup():
    """Test connection cleanup."""
    planner = GptChatWorkoutPlanner()
    connection_id = "test-connection-789"

    planner.initialize_connection(connection_id)
    assert connection_id in planner._conversations

    planner.cleanup_connection(connection_id)
    assert connection_id not in planner._conversations


@pytest.mark.asyncio
async def test_chat_planner_conversation_length():
    """Test conversation length tracking."""
    planner = GptChatWorkoutPlanner()
    connection_id = "test-connection-length"

    # No conversation yet
    assert planner.get_conversation_length(connection_id) == 0

    # After initialization
    planner.initialize_connection(connection_id)
    assert planner.get_conversation_length(connection_id) == 1

    # After adding messages
    planner._conversations[connection_id].append(
        {"role": "user", "content": "Test"}
    )
    assert planner.get_conversation_length(connection_id) == 2
