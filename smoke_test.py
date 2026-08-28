from dotenv import load_dotenv
import os

load_dotenv()

for key in ("AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION", "GEMINI_API_KEY", "DATABASE_URL"):
    print(f"{key} loaded: {key in os.environ}")
