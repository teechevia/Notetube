from services.ai import ask_ai
from services.providers.base import AIProvider


GEMINI_MODEL_MAP = {
    "reasoning_long_context": "gemini-2.5-flash",
    "long_context_fast": "gemini-2.5-flash",
    "structured_output": "gemini-2.5-flash",
    "reasoning_structured": "gemini-2.5-flash",
}


class GeminiProvider(AIProvider):
    def generate_text(
        self,
        prompt: str,
        system_instruction: str = None,
        model: str = None,
    ) -> str:

        selected_model = GEMINI_MODEL_MAP.get(
            model,
            model or "gemini-2.5-flash",
        )

        return ask_ai(
            prompt,
            system_instruction,
            model=selected_model,
        )
