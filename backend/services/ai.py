from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def ask_ai(prompt: str):

    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)

    return response.text

