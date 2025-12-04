import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import vertexai
from vertexai.generative_models import GenerativeModel

# SCOPES: Permissions we are requesting
SCOPES = [
    'https://www.googleapis.com/auth/documents',    # Docs
    'https://www.googleapis.com/auth/forms.body',   # Forms
    'https://www.googleapis.com/auth/drive.file',   # Drive (Created files only)
    'https://www.googleapis.com/auth/gmail.compose' # Gmail (Drafts only)
]

def authenticate_user():
    """Handles the user login flow (OAuth 2.0)."""
    creds = None
    # Check if we already have a valid token from a previous login
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If no valid token, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ ERROR: credentials.json not found. Please move it to this folder.")
                return None
            
            # Launch the browser for login
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the token for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def init_orchestrator():
    # 1. Point to the Service Account Key for Vertex AI
    # This fixes the "DefaultCredentialsError"
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex-key.json"
    
    # Initialize Vertex AI
    # Replace with your actual Project ID from Google Cloud
    PROJECT_ID = "edu-teacher-assistant-prod" 
    vertexai.init(project=PROJECT_ID, location="us-central1")
    
    model = GenerativeModel("gemini-2.0-flash-exp")
    print("🧠 Orchestrator (Gemini 2.0) initialized.")
    return model

def main():
    print("🚀 Starting AI Teacher Assistant...")
    
    # 1. Authenticate Workspace
    creds = authenticate_user()
    if not creds:
        return
    print("✅ Workspace Authentication successful.")

    # 2. Initialize AI
    try:
        model = init_orchestrator()
        # 3. Simple Test
        response = model.generate_content("Hello! Please confirm you are ready to assist.")
        print(f"\n🤖 Agent Response: {response.text}")
    except Exception as e:
        print(f"\n❌ AI Error: {e}")
        print("Tip: Ensure you have enabled the 'Vertex AI API' in Google Cloud Console.")

if __name__ == '__main__':
    main()