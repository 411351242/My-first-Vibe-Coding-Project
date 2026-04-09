import sys
import os

# Add backend to path just in case
sys.path.append(os.path.abspath('.'))

from google import genai
from backend.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
try:
    res = client.models.generate_content(
        model='gemini-3.1-pro-preview', 
        contents='hello'
    )
    print('SUCCESS:', res.text)
except Exception as e:
    print('ERROR:', type(e).__name__)
    print(str(e))
