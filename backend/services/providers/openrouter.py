from openai import OpenAI
from config import OPENROUTER_API_KEY

from services.providers.base import AIProvider


OPENROUTER_MODEL_MAP = {
    "reasoning_long_context": "openrouter/free",
    "long_context_fast": "openrouter/free",
    "structured_output": "openrouter/free",
    "reasoning_structured": "openrouter/free",
}


class OpenRouterProvider(AIProvider):
    def __init__(self):
        api_key = OPENROUTER_API_KEY

        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate_text(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None,
    ) -> str:

        selected_model = OPENROUTER_MODEL_MAP.get(
            model,
            model or "openrouter/free",
        )

        messages = []

        if system_instruction:
            messages.append({
                "role": "system",
                "content": system_instruction,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        response = self.client.chat.completions.create(
            model=selected_model,
            messages=messages,
        )

        return response.choices[0].message.content