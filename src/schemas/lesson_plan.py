"""
Pydantic schemas for lesson planning.

Defines structured inputs and outputs for the CurriculumArchitect agent.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field, HttpUrl, ValidationInfo, field_validator

# ============================================================================
# ENUMS
# ============================================================================


class Difficulty(str, Enum):
    """Learning difficulty levels."""

    LOW = "low"
    MEDIUM = "medium"
    HARD = "hard"


class TeachingApproach(str, Enum):
    """Teaching methodologies."""

    INQUIRY_BASED = "inquiry-based"
    DIRECT = "direct"
    PROJECT_BASED = "project-based"
    MIXED = "mixed"


class AssessmentType(str, Enum):
    """Types of assessments."""

    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    DIAGNOSTIC = "diagnostic"


class ResourceType(str, Enum):
    """Types of supplementary resources."""

    VIDEO = "video"
    ARTICLE = "article"
    INTERACTIVE = "interactive"
    DATASET = "dataset"
    TOOL = "tool"


# ============================================================================
# INPUT SCHEMAS
# ============================================================================


class LessonPlanRequest(BaseModel):
    """
    Teacher's request for a comprehensive lesson plan.

    This captures all requirements for generating a multi-lecture course plan.
    """

    # Core Identifiers
    topic: str = Field(
        ...,
        description="Main topic/subject to teach",
        min_length=3,
        examples=["Machine Learning Fundamentals", "Photosynthesis", "World War II"],
    )

    grade: str = Field(
        ...,
        description="Grade level or education stage",
        examples=["9th Grade", "Undergraduate Year 3", "High School AP"],
    )

    # Course Structure
    lecture_duration: int = Field(
        ...,
        description="Duration of each lecture in minutes",
        ge=30,
        le=180,
        examples=[45, 90, 120],
    )

    total_periods: int = Field(
        ...,
        description="Total number of lecture periods",
        ge=1,
        le=30,
        examples=[10, 15, 20],
    )

    # Pedagogical Configuration
    difficulty: Difficulty = Field(
        ...,
        description="Overall difficulty level",
    )

    teaching_approach: TeachingApproach = Field(
        ...,
        description="Preferred teaching methodology",
    )

    prior_knowledge: str = Field(
        ...,
        description="Assumed prior knowledge of students",
        examples=[
            "Students have completed Introduction to Programming",
            "Basic understanding of cell biology",
            "No prior knowledge assumed",
        ],
    )

    # Lab Configuration
    lab_required: bool = Field(
        default=False,
        description="Whether hands-on lab sessions are needed",
    )

    programming_language: str | None = Field(
        default=None,
        description="Programming language for CS/tech labs (required if lab_required=True for tech courses)",
        examples=["Python", "Java", "R", "MATLAB"],
    )

    # Resources
    resource_files: list[Path] = Field(
        default_factory=list,
        description="Local paths to uploaded files (will be cached)",
    )

    cached_content_name: str | None = Field(
        default=None,
        description="Vertex AI Context Cache identifier (if files already cached)",
    )

    # Optional Context
    additional_context: str | None = Field(
        default=None,
        description="Any additional requirements or preferences",
    )

    @field_validator("programming_language")
    @classmethod
    def validate_programming_language_for_labs(
        cls, v: str | None, info: ValidationInfo[Any]
    ) -> str | None:
        """Ensure programming language is specified for tech labs."""
        # Note: This will be enforced by the agent asking follow-up questions
        return v

    class Config:
        """Pydantic configuration."""

        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "topic": "Introduction to Machine Learning",
                "grade": "Undergraduate Year 3",
                "lecture_duration": 90,
                "total_periods": 10,
                "difficulty": "medium",
                "teaching_approach": "mixed",
                "prior_knowledge": "Students have completed Linear Algebra and Python Programming",
                "lab_required": True,
                "programming_language": "Python",
                "resource_files": ["lecture_slides.pdf"],
                "additional_context": "Focus on practical applications in industry",
            }
        }


# ============================================================================
# OUTPUT SCHEMAS - Detailed Components
# ============================================================================


class TimelineSegment(BaseModel):
    """A single segment in the lecture timeline."""

    start_minute: int = Field(..., ge=0, description="Start time in minutes from lecture start")
    duration: int = Field(..., ge=1, description="Duration in minutes")
    activity: str = Field(..., description="What happens during this segment")
    instructor_notes: str | None = Field(
        default=None,
        description="Tips or notes for the instructor",
    )

    @property
    def end_minute(self) -> int:
        """Calculate end time."""
        return self.start_minute + self.duration


class Activity(BaseModel):
    """A detailed learning activity."""

    title: str = Field(..., description="Activity name")
    description: str = Field(..., description="Detailed description of the activity")
    duration: int = Field(..., ge=1, description="Expected duration in minutes")
    materials_needed: list[str] = Field(
        default_factory=list,
        description="Specific materials for this activity",
    )
    instructions: list[str] = Field(
        ...,
        description="Step-by-step instructions",
    )
    learning_outcomes: list[str] = Field(
        default_factory=list,
        description="What students should achieve",
    )


class Assessment(BaseModel):
    """Assessment for a lecture period."""

    type: AssessmentType = Field(..., description="Type of assessment")
    title: str = Field(..., description="Assessment title")
    description: str = Field(..., description="What is being assessed")
    questions_or_tasks: list[str] = Field(
        ...,
        description="Specific questions or tasks",
    )
    rubric: str | None = Field(
        default=None,
        description="Grading rubric or success criteria",
    )
    estimated_time: int = Field(..., ge=1, description="Time to complete in minutes")


class Differentiation(BaseModel):
    """Differentiation strategies for diverse learners."""

    support_strategies: list[str] = Field(
        ...,
        description="Strategies for students who need additional support",
    )
    challenge_strategies: list[str] = Field(
        ...,
        description="Extensions for advanced students",
    )
    accommodations: list[str] = Field(
        default_factory=list,
        description="Specific accommodations (e.g., for students with disabilities)",
    )


class Homework(BaseModel):
    """Homework assignment for a lecture period."""

    title: str = Field(..., description="Assignment title")
    description: str = Field(..., description="What students need to do")
    tasks: list[str] = Field(..., description="Specific tasks")
    estimated_time: int = Field(..., ge=5, description="Expected time in minutes")
    due_date_offset: int = Field(
        default=7,
        description="Days until due (from lecture date)",
    )
    resources_needed: list[str] = Field(
        default_factory=list,
        description="Resources students need",
    )


class ResourceLink(BaseModel):
    """A supplementary educational resource."""

    title: str = Field(..., description="Resource title")
    url: HttpUrl = Field(..., description="Link to resource")
    type: ResourceType = Field(..., description="Type of resource")
    description: str = Field(..., description="Why this resource is relevant")
    recommended_for: list[int] = Field(
        default_factory=list,
        description="Which lecture periods this resource supports (1-indexed)",
    )


# ============================================================================
# OUTPUT SCHEMAS - Lecture Period
# ============================================================================


class LecturePeriod(BaseModel):
    """Complete plan for a single lecture period."""

    period_number: int = Field(..., ge=1, description="Lecture number in sequence")
    title: str = Field(..., description="Lecture title")

    learning_objectives: list[str] = Field(
        ...,
        min_length=2,
        description="Specific, measurable learning objectives",
    )

    materials: list[str] = Field(
        ...,
        description="All required materials and resources",
    )

    detailed_timeline: list[TimelineSegment] = Field(
        ...,
        description="Minute-by-minute breakdown of the lecture",
    )

    detailed_activities: list[Activity] = Field(
        ...,
        min_length=1,
        description="Step-by-step activities",
    )

    assessment: Assessment = Field(
        ...,
        description="Assessment for this lecture",
    )

    differentiation: Differentiation = Field(
        ...,
        description="Differentiation strategies",
    )

    homework: Homework = Field(
        ...,
        description="Homework assignment",
    )

    @field_validator("detailed_timeline")
    @classmethod
    def validate_timeline_continuity(cls, segments: list[TimelineSegment]) -> list[TimelineSegment]:
        """Ensure timeline segments are continuous."""
        if not segments:
            raise ValueError("Timeline cannot be empty")

        # Sort by start time
        sorted_segments = sorted(segments, key=lambda x: x.start_minute)

        # Check continuity
        for i in range(len(sorted_segments) - 1):
            current_end = sorted_segments[i].end_minute
            next_start = sorted_segments[i + 1].start_minute
            if current_end != next_start:
                raise ValueError(
                    f"Timeline gap detected: segment ends at {current_end} "
                    f"but next starts at {next_start}"
                )

        return sorted_segments


# ============================================================================
# OUTPUT SCHEMAS - Complete Lesson Plan
# ============================================================================


class CompleteLessonPlan(BaseModel):
    """
    Complete multi-lecture lesson plan.

    This is the final output from the CurriculumArchitect agent.
    """

    # Metadata
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="When this plan was generated",
    )

    course_title: str = Field(..., description="Overall course title")
    course_description: str = Field(..., description="Course overview")

    # Original Request Context
    request: LessonPlanRequest = Field(
        ...,
        description="Original request that generated this plan",
    )

    # Lecture Periods
    lectures: list[LecturePeriod] = Field(
        ...,
        min_length=1,
        description="Detailed plan for each lecture period",
    )

    # Supplementary Resources
    resource_links: list[ResourceLink] = Field(
        default_factory=list,
        description="Curated external resources",
    )

    # Course-Level Information
    progression_map: str = Field(
        ...,
        description="How lectures build on each other throughout the course",
    )

    prerequisites_summary: str = Field(
        ...,
        description="Summary of what students need to know before starting",
    )

    learning_outcomes_summary: list[str] = Field(
        ...,
        description="Overall course learning outcomes",
    )

    @field_validator("lectures")
    @classmethod
    def validate_lecture_count(
        cls, lectures: list[LecturePeriod], info: ValidationInfo[Any]
    ) -> list[LecturePeriod]:
        """Ensure lecture count matches request."""
        request = info.data.get("request")
        if request and len(lectures) != request.total_periods:
            raise ValueError(f"Expected {request.total_periods} lectures, got {len(lectures)}")
        return lectures

    class Config:
        """Pydantic configuration."""

        json_schema_extra: ClassVar[dict[str, Any]] = {
            "example": {
                "course_title": "Introduction to Machine Learning",
                "course_description": "A comprehensive 10-week course covering ML fundamentals",
                "lectures": [],  # Simplified for brevity
                "progression_map": "Lectures 1-3 cover foundations, 4-7 introduce algorithms...",
            }
        }


# ============================================================================
# CLARIFICATION SCHEMAS
# ============================================================================


class ClarificationQuestion(BaseModel):
    """A question the agent needs answered before proceeding."""

    question: str = Field(..., description="The question to ask")
    field_name: str = Field(..., description="Which input field this clarifies")
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested answers",
    )
    required: bool = Field(
        default=True,
        description="Whether this must be answered",
    )


class ClarificationRequest(BaseModel):
    """Agent's request for more information."""

    message: str = Field(
        ...,
        description="Friendly message explaining what's needed",
    )
    questions: list[ClarificationQuestion] = Field(
        ...,
        min_length=1,
        description="Specific questions",
    )
