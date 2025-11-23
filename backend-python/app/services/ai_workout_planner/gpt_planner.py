"""GPT-4o based AI workout planner service."""

import logging
import json
from typing import Any
from openai import AsyncOpenAI

from app.core.config import settings
from app.models.schemas.ai_workout import (
    AiWorkoutAttributes,
    AiSessionAttributes,
    ProgramBlueprint,
    SessionBlueprint,
    ExerciseBlueprint,
)

logger = logging.getLogger(__name__)


class GptAiWorkoutPlanner:
    """
    AI workout planner using GPT-4o with function calling.

    Generates personalized workout plans and sessions based on user attributes.
    """

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_workout_plan(
        self, attributes: AiWorkoutAttributes
    ) -> ProgramBlueprint:
        """
        Generate a complete workout program using GPT-4o.

        Args:
            attributes: User attributes for personalization

        Returns:
            ProgramBlueprint with complete workout program
        """
        # Construct the prompt
        prompt = self._build_workout_plan_prompt(attributes)

        # Define function schema for structured output
        function_schema = {
            "name": "create_workout_plan",
            "description": "Create a personalized workout program",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Program name"},
                    "description": {"type": "string", "description": "Program description"},
                    "duration_weeks": {"type": "integer", "description": "Program duration in weeks"},
                    "sessions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "estimated_duration_minutes": {"type": "integer"},
                                "exercises": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "sets": {"type": "integer"},
                                            "reps_min": {"type": "integer"},
                                            "reps_max": {"type": "integer"},
                                            "rest_seconds": {"type": "integer"},
                                            "notes": {"type": "string"},
                                        },
                                        "required": ["name", "sets", "reps_min", "reps_max", "rest_seconds"],
                                    },
                                },
                            },
                            "required": ["name", "estimated_duration_minutes", "exercises"],
                        },
                    },
                },
                "required": ["name", "description", "duration_weeks", "sessions"],
            },
        }

        try:
            # Call GPT-4o with function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert fitness coach and personal trainer with deep knowledge of exercise science, program design, and progressive overload.",
                    },
                    {"role": "user", "content": prompt},
                ],
                functions=[function_schema],
                function_call={"name": "create_workout_plan"},
                temperature=0.7,
            )

            # Parse function call result
            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("GPT-4o did not return a function call")

            plan_data = json.loads(function_call.arguments)

            # Convert to ProgramBlueprint
            return self._parse_program_blueprint(plan_data)

        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            raise

    async def generate_session(
        self, attributes: AiSessionAttributes
    ) -> SessionBlueprint:
        """
        Generate a single workout session using GPT-4o.

        Args:
            attributes: Session attributes for personalization

        Returns:
            SessionBlueprint with workout session
        """
        # Construct the prompt
        prompt = self._build_session_prompt(attributes)

        # Define function schema
        function_schema = {
            "name": "create_workout_session",
            "description": "Create a single workout session",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "estimated_duration_minutes": {"type": "integer"},
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sets": {"type": "integer"},
                                "reps_min": {"type": "integer"},
                                "reps_max": {"type": "integer"},
                                "rest_seconds": {"type": "integer"},
                                "notes": {"type": "string"},
                            },
                            "required": ["name", "sets", "reps_min", "reps_max", "rest_seconds"],
                        },
                    },
                },
                "required": ["name", "estimated_duration_minutes", "exercises"],
            },
        }

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert fitness coach designing effective workout sessions.",
                    },
                    {"role": "user", "content": prompt},
                ],
                functions=[function_schema],
                function_call={"name": "create_workout_session"},
                temperature=0.7,
            )

            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("GPT-4o did not return a function call")

            session_data = json.loads(function_call.arguments)

            return self._parse_session_blueprint(session_data)

        except Exception as e:
            logger.error(f"Error generating workout session: {e}")
            raise

    def _build_workout_plan_prompt(self, attrs: AiWorkoutAttributes) -> str:
        """Build prompt for workout plan generation."""
        return f"""Create a personalized {attrs.days_per_week}-day per week workout program for:

User Profile:
- Age: {attrs.age}
- Gender: {attrs.gender}
- Weight: {attrs.weight_kg} kg
- Experience Level: {attrs.experience_level.value}
- Goals: {attrs.goals}
{f"- Additional Preferences: {attrs.additional_preferences}" if attrs.additional_preferences else ""}

Design a complete program with {attrs.days_per_week} unique sessions per week. Include:
1. Progressive overload principles
2. Appropriate exercise selection for experience level
3. Balanced training split
4. Proper rest periods based on intensity
5. Exercise variations to prevent plateaus

Focus on evidence-based programming that aligns with the user's goals."""

    def _build_session_prompt(self, attrs: AiSessionAttributes) -> str:
        """Build prompt for single session generation."""
        return f"""Create a single {attrs.duration_minutes}-minute workout session for:

User Profile:
- Age: {attrs.age}
- Gender: {attrs.gender}
- Weight: {attrs.weight_kg} kg
- Experience Level: {attrs.experience_level.value}
- Focus: {attrs.focus}
{f"- Available Equipment: {attrs.available_equipment}" if attrs.available_equipment else ""}

Design an effective workout that:
1. Fits within {attrs.duration_minutes} minutes
2. Targets the specified focus area
3. Matches the experience level
4. Uses available equipment (or bodyweight if none specified)
5. Includes proper warm-up and progression"""

    def _parse_program_blueprint(self, data: dict[str, Any]) -> ProgramBlueprint:
        """Parse GPT response into ProgramBlueprint."""
        sessions = [
            self._parse_session_blueprint(session_data)
            for session_data in data["sessions"]
        ]

        return ProgramBlueprint(
            name=data["name"],
            description=data["description"],
            duration_weeks=data["duration_weeks"],
            sessions=sessions,
        )

    def _parse_session_blueprint(self, data: dict[str, Any]) -> SessionBlueprint:
        """Parse session data into SessionBlueprint."""
        exercises = [
            ExerciseBlueprint(
                name=ex["name"],
                sets=ex["sets"],
                reps_min=ex["reps_min"],
                reps_max=ex["reps_max"],
                rest_seconds=ex["rest_seconds"],
                notes=ex.get("notes"),
            )
            for ex in data["exercises"]
        ]

        return SessionBlueprint(
            name=data["name"],
            estimated_duration_minutes=data["estimated_duration_minutes"],
            exercises=exercises,
        )


# Singleton instance
_gpt_ai_workout_planner: GptAiWorkoutPlanner | None = None


def get_gpt_ai_workout_planner() -> GptAiWorkoutPlanner:
    """Dependency injection for GPT AI workout planner."""
    global _gpt_ai_workout_planner
    if _gpt_ai_workout_planner is None:
        _gpt_ai_workout_planner = GptAiWorkoutPlanner()
    return _gpt_ai_workout_planner
