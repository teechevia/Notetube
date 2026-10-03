import os

from groq import Groq

from services.providers.base import AIProvider


GROQ_MODEL_MAP = {
    "reasoning_long_context": "openai/gpt-oss-120b",
    "long_context_fast": "openai/gpt-oss-20b",
    "structured_output": "openai/gpt-oss-20b",
    "reasoning_structured": "openai/gpt-oss-120b",
}


class GroqProvider(AIProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        self.client = Groq(api_key=api_key)

    def generate_text(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None,
    ) -> str:

        selected_model = GROQ_MODEL_MAP.get(
            model,
            model or "llama-3.3-70b-versatile",
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