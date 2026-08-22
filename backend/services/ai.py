from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

def ask_ai(prompt: str, system_instruction: str = None):
    if system_instruction:
        config = {"system_instruction": system_instruction}
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt, config=config)
    else:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    
    return response.text

