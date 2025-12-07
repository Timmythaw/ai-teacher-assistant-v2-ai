import os

from google.adk.agents import Agent
from google.genai import types
import vertexai
from vertexai.agent_engines import AdkApp

model = "gemini-2.0-flash"

safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]

generate_content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.2,
    max_output_tokens=1024,
    top_p=0.8,
)

agent = Agent(
    model=model,
    name="currency_exchange_agent",
    generate_content_config=generate_content_config,
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex-key.json"
PROJECT_ID = "edu-teacher-assistant-prod"
vertexai.init(project=PROJECT_ID, location="us-central1")

app = AdkApp(agent=agent)


async def main():
    async for event in app.async_stream_query(
        user_id="user-123",  # Required
        message="What is the exchange rate from US dollars to thai baht?",
    ):
        print(event)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
