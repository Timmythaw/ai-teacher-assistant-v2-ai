"""
AI Teaching Assistant Agents.

This module contains specialized agents for educational tasks:
- CurriculumAgent: Lesson planning and curriculum design
- AssessmentAgent: Quiz and test generation (coming soon)
- EmailAgent: Communication drafting (coming soon)
"""

from src.agents.curriculum_agent import (
    create_curriculum_agent,
    generate_lesson_plan_from_request,
    load_curriculum_prompt,
)

__all__ = [
    # Curriculum Agent
    "create_curriculum_agent",
    "generate_lesson_plan_from_request",
    "load_curriculum_prompt",
    # Future: Assessment Agent
    # "create_assessment_agent",
    # Future: Email Agent
    # "create_email_agent",
]
