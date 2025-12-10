# """
# Curriculum Agent for ADK Web UI.
# """

# import os
# from pathlib import Path
# import sys

# # Add parent directory to path for imports
# parent_dir = Path(__file__).parent.parent
# sys.path.insert(0, str(parent_dir))

# from dotenv import load_dotenv

# # Load .env from parent directory (override any existing env vars)
# load_dotenv(parent_dir / ".env", override=True)

# # Verify credentials - fix the path resolution
# creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials/vertex-key.json")

# # Convert to absolute path (handle both relative paths starting with ./ and absolute paths)
# if not Path(creds_path).is_absolute():
#     # Remove leading ./ if present and resolve relative to parent dir
#     creds_path = str(parent_dir / creds_path.lstrip("./"))
# else:
#     creds_path = str(Path(creds_path))

# # Check if file exists
# if not Path(creds_path).exists():
#     print(f"❌ Credentials not found: {creds_path}")
#     print(f"   Looking in parent dir: {parent_dir}")
#     print("   Files in parent dir:")
#     for f in parent_dir.glob("*.json"):
#         print(f"     - {f.name}")
#     sys.exit(1)

# print(f"✅ Using credentials: {creds_path}")

# # Set the environment variable with absolute path
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

# # Ensure project and region are set in environment for genai Client
# # The ADK's GoogleLLM creates a Client() with no args, so it relies on env vars
# project = os.getenv("GOOGLE_CLOUD_PROJECT")
# region = os.getenv("GOOGLE_CLOUD_REGION")

# if not project:
#     print("❌ GOOGLE_CLOUD_PROJECT not set in .env")
#     sys.exit(1)
# if not region:
#     print("❌ GOOGLE_CLOUD_REGION not set in .env")
#     sys.exit(1)

# print(f"✅ Vertex AI config: project={project}, region={region}")

# # Monkey-patch google.genai.Client to use Vertex AI by default
# # This is needed because ADK creates Client() with no args
# from google import genai

# _original_client_init = genai.Client.__init__

# def _patched_client_init(self, **kwargs):
#     # If no explicit config provided, use Vertex AI with env vars
#     if not kwargs.get('api_key') and not kwargs.get('vertexai'):
#         kwargs['vertexai'] = True
#         kwargs['project'] = project
#         kwargs['location'] = region
#     return _original_client_init(self, **kwargs)

# genai.Client.__init__ = _patched_client_init
# print("✅ Patched genai.Client to use Vertex AI by default")

# # Import and create agent
# from src.agents.curriculum_agent import create_curriculum_agent

# root_agent = create_curriculum_agent()

# print("✅ Curriculum agent ready!")
# print(f"   Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
# print(f"   Model: {os.getenv('SPECIALIST_MODEL')}")
