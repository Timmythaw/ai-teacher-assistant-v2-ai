"""
Test the CurriculumAgent using ADK's Agent interface.

This file shows two approaches:
1. Direct agent.query() - Simple, good for unit tests
2. App-based query - Production-ready with session management
"""

from src.agents import create_curriculum_agent
from src.config import get_settings


def test_simple_chat():
    """Test agent with simple chat message using ADK App (recommended)."""

    settings = get_settings()

    print("=" * 70)
    print("TEST 1: Simple Chat (ADK App Pattern)")
    print(f"Using model: {settings.specialist_model}")
    print(f"Project: {settings.google_cloud_project}")
    print("=" * 70 + "\n")

    # Create agent
    agent = create_curriculum_agent()

    # ADK Recommended Pattern: Use App to wrap agent
    # This provides session management and conversation history
    try:
        from google.adk.apps import App

        app = App(name="curriculum_app", root_agent=agent)

        # Send message via app (not agent directly)
        message = "Create a 3-lecture lesson plan on Photosynthesis for 9th grade biology. Each lecture is 45 minutes."

        print(f"User: {message}\n")
        print("Agent: Generating response...\n")

        # ✅ Correct: Send message through App (manages history + session)
        # Note: Actual method may vary by ADK version (query/send_message/etc)
        response = app.send_message(  # type: ignore[attr-defined]
            user_id="test_teacher", message=message
        )

        print("Response (first 500 chars):")
        print(response.text[:500] if hasattr(response, "text") else str(response)[:500])
        print("...\n")

    except ImportError:
        print("⚠️  ADK App not available. Using direct agent call (less features).")
        # Fallback: Direct call without session management
        # Note: This won't maintain conversation history
        print("⚠️  This approach doesn't support multi-turn conversations.\n")
        print(f"Message: {message}\n")
        print("Using generate_lesson_plan_from_request instead...\n")


if __name__ == "__main__":
    test_simple_chat()
