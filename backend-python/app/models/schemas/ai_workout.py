"""AI workout request/response schemas using Pydantic."""

from pydantic import BaseModel, Field
from app.core.enums import ExperienceLevel


class AiWorkoutAttributes(BaseModel):
    """Attributes for AI workout plan generation."""

    age: int = Field(..., ge=13, le=120)
    gender: str = Field(..., max_length=50)
    weight_kg: float = Field(..., ge=20, le=500)
    experience_level: ExperienceLevel
    goals: str = Field(..., max_length=500)
    days_per_week: int = Field(..., ge=1, le=7)
    additional_preferences: str | None = Field(None, max_length=1000)


class AiSessionAttributes(BaseModel):
    """Attributes for AI single session generation."""

    age: int = Field(..., ge=13, le=120)
    gender: str = Field(..., max_length=50)
    weight_kg: float = Field(..., ge=20, le=500)
    experience_level: ExperienceLevel
    focus: str = Field(..., max_length=200)
    duration_minutes: int = Field(..., ge=15, le=180)
    available_equipment: str | None = Field(None, max_length=500)


class ExerciseBlueprint(BaseModel):
    """Single exercise in a workout."""

    name: str
    sets: int
    reps_min: int
    reps_max: int
    rest_seconds: int
    notes: str | None = None


class SessionBlueprint(BaseModel):
    """Single workout session."""

    name: str
    exercises: list[ExerciseBlueprint]
    estimated_duration_minutes: int


class ProgramBlueprint(BaseModel):
    """Complete workout program."""

    name: str
    description: str
    sessions: list[SessionBlueprint]
    duration_weeks: int


class GenerateAiWorkoutPlanRequest(BaseModel):
    """Request to generate AI workout plan."""

    attributes: AiWorkoutAttributes


class GenerateAiSessionRequest(BaseModel):
    """Request to generate AI workout session."""

    attributes: AiSessionAttributes
