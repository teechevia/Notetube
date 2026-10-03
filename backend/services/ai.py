from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


def ask_ai(
    prompt: str,
    system_instruction: str = None,
    model: str = None,
):
    selected_model = model or "gemini-2.5-flash"

    if system_instruction:
        config = {
            "system_instruction": system_instruction
        }

        response = client.models.generate_content(
            model=selected_model,
            contents=prompt,
            config=config,
        )
    else:
        response = client.models.generate_content(
            model=selected_model,
            contents=prompt,
        )

    return response.text
