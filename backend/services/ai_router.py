from services.ai_config import Task, AI_ROUTING_CONFIG
from services.providers.base import AIProvider
from services.providers.gemini import GeminiProvider


PROVIDERS: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
}


def generate_text(task: Task, prompt: str, system_instruction: str = None) -> str:
    """
    Routes text generation requests through the configured AI provider.
    """
    config = AI_ROUTING_CONFIG.get(task)
    if not config:
        raise ValueError(f"No routing configuration found for task: {task}")

    provider_name = config.get("provider")
    provider_class = PROVIDERS.get(provider_name)

    if not provider_class:
        raise NotImplementedError(
            f"Provider '{provider_name}' is not implemented yet."
        )

    provider = provider_class()
    return provider.generate_text(prompt, system_instruction)
