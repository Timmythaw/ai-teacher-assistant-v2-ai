"""
CurriculumArchitect Agent - Expert lesson planner using Google ADK.

This agent uses:
- Google ADK's Agent class for orchestration
- Built-in google_search tool from ADK
- Your custom search_tool.py for query optimization
- Vertex AI Search for uploaded course materials (when configured)
- Structured output matching your Pydantic schemas
"""

import os
from pathlib import Path

from google.adk.agents.llm_agent import Agent
from google.adk.tools.google_search_tool import google_search
import vertexai
from vertexai.generative_models import GenerationConfig

from src.config import get_settings
from src.schemas.lesson_plan import (
    LessonPlanRequest,
)
from src.utils.logger import logger


def load_curriculum_prompt() -> str:
    """Load the curriculum architect system instruction from file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "curriculum_architect.txt"

    if not prompt_path.exists():
        logger.warning(f"Prompt file not found: {prompt_path}, using default")
        return """You are an expert CurriculumArchitect agent specializing in comprehensive lesson planning for educators.

# YOUR ROLE
You help teachers create detailed, standards-aligned lesson plans across multiple lecture periods.

# CORE RESPONSIBILITIES
1. Generate comprehensive lesson plans with learning objectives, timeline, activities, assessments
2. Ask clarifying questions if critical information is missing
3. Search for supplementary resources (videos, articles, simulations)
4. Reference uploaded materials when available

If you need clarification, respond with this JSON structure:
{
  "message": "I need a few details before generating your lesson plan.",
  "questions": [...]
}

Otherwise, generate a complete lesson plan following the CompleteLessonPlan schema."""

    with Path.open(prompt_path, encoding="utf-8") as f:
        prompt = f.read()

    logger.info("Loaded curriculum prompt from file", path=str(prompt_path))
    return prompt


def create_curriculum_agent(
    datastore_id: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
) -> Agent:
    """
    Create the CurriculumArchitect agent using Google ADK.

    Args:
        datastore_id: Optional Vertex AI Search datastore ID.
                     If None, uses settings.vertex_ai_search_datastore_id
        model: Optional model override. If None, uses settings.specialist_model
        temperature: Model temperature (0.0-1.0). Default 0.7 for creative generation
        max_output_tokens: Maximum tokens in response. Default 8192 for long lesson plans

    Returns:
        Configured ADK Agent instance

    Example:
        >>> agent = create_curriculum_agent()  # Uses settings defaults
        >>> # Or with overrides:
        >>> agent = create_curriculum_agent(
        ...     datastore_id="custom-datastore-123",
        ...     model="gemini-3-pro-preview"
        ... )
    """

    # Load settings
    settings = get_settings()

    # Use settings defaults if not provided
    if model is None:
        model = settings.specialist_model

    if datastore_id is None:
        datastore_id = settings.vertex_ai_search_datastore_id

    # Set credentials for Vertex AI (required for authentication)
    # This must be done before vertexai.init()
    if settings.google_application_credentials.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
            settings.google_application_credentials.absolute()
        )
        logger.info(
            "Set GOOGLE_APPLICATION_CREDENTIALS", path=str(settings.google_application_credentials)
        )
    else:
        logger.warning(
            "Service account key not found",
            expected_path=str(settings.google_application_credentials),
        )

    project_id = settings.google_cloud_project
    location = settings.google_cloud_region

    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    logger.info("Initialized Vertex AI", project=project_id, location=location)

    # Load system instruction from file
    instruction = load_curriculum_prompt()

    # Configure generation parameters (temperature, max tokens, etc.)
    # These are passed to the model at inference time
    generation_config = GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        top_p=0.95,  # Optional: nucleus sampling
    )

    # Configure tools - use list[Any] to support multiple tool types
    from typing import Any

    tools: list[Any] = [
        google_search,  # Built-in ADK Google Search tool
    ]

    # Add Vertex AI Search if datastore configured
    if datastore_id:
        try:
            from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool

            # Configure Vertex AI Search for course materials
            # Note: VertexAiSearchTool initialization may vary by ADK version
            vertex_search = VertexAiSearchTool(
                data_store_id=datastore_id,
            )  # type: ignore[call-arg]
            tools.append(vertex_search)

            logger.info("Added Vertex AI Search tool", datastore_id=datastore_id)
        except ImportError as e:
            logger.warning("Vertex AI Search not available, continuing without it", error=str(e))

    # Create Vertex AI client and set it as the default client for genai
    # This ensures ADK Agent uses Vertex AI instead of AI Studio
    from google import genai

    genai.client = genai.Client(  # type: ignore[assignment]
        vertexai=True,
        project=project_id,
        location=location,
    )

    logger.info("Configured genai with Vertex AI client", project=project_id, location=location)

    # Create the agent using ADK's Agent class
    # The agent will now use the Vertex AI client we configured above
    # Note: Generation config should be applied when calling agent.query()
    # Store it on the agent for later use
    agent = Agent(
        model=model,
        name="curriculum_agent",
        description="Expert lesson planning agent that creates comprehensive, standards-aligned lesson plans across multiple lecture periods",
        instruction=instruction,
        tools=tools,
    )

    # Store generation config on agent for use in query calls
    agent._generation_config = generation_config  # type: ignore[attr-defined]

    logger.info(
        "CurriculumAgent created",
        model=model,
        temperature=temperature,
        max_tokens=max_output_tokens,
        tools_count=len(tools),
        has_datastore=bool(datastore_id),
        project=settings.google_cloud_project,
        region=settings.google_cloud_region,
    )

    return agent


def generate_lesson_plan_from_request(agent: Agent, request: LessonPlanRequest) -> str:
    """
    Generate a lesson plan from a structured request.

    This is a helper for programmatic usage (your test scripts).
    For ADK CLI usage, the agent handles messages directly.

    Args:
        agent: The curriculum agent instance
        request: Structured lesson plan request

    Returns:
        Agent's response (JSON string of CompleteLessonPlan or ClarificationRequest)
    """

    # Build prompt from request
    prompt = f"""Generate a comprehensive lesson plan with the following requirements:

**Topic**: {request.topic}
**Grade Level**: {request.grade}
**Lecture Duration**: {request.lecture_duration} minutes
**Total Periods**: {request.total_periods}
**Difficulty**: {request.difficulty.value}
**Teaching Approach**: {request.teaching_approach.value}
**Prior Knowledge**: {request.prior_knowledge}
"""

    if request.lab_required:
        prompt += "\n**Lab Required**: Yes"
        if request.programming_language:
            prompt += f" (Language: {request.programming_language})"

    if request.additional_context:
        prompt += f"\n\n**Additional Context**: {request.additional_context}"

    prompt += "\n\nGenerate a complete lesson plan following the CompleteLessonPlan schema. Output valid JSON only."

    logger.info("Generating lesson plan", topic=request.topic, periods=request.total_periods)

    # Send message to agent with generation config
    # Note: If agent has _generation_config stored, you can pass it to the model
    # The exact API depends on ADK version - this is a placeholder
    response = agent.query(prompt)  # type: ignore[attr-defined]

    # Alternative: If you need direct control, use GenerativeModel directly:
    # from vertexai.generative_models import GenerativeModel
    # model = GenerativeModel(agent.model)
    # response = model.generate_content(prompt, generation_config=agent._generation_config)

    return response.text  # type: ignore[no-any-return]
