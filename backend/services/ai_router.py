from services.ai_config import (
    Task,
    AI_ROUTING_CONFIG,
    TASK_REQUIREMENTS,
    TASK_MODEL_STRATEGY,
)
from services.providers.base import AIProvider
from services.providers.gemini import GeminiProvider
from services.providers.groq import GroqProvider
from services.providers.openrouter import OpenRouterProvider
from services.ai_cache import (
    make_cache_key,
    get_cached,
    set_cached,
    get_key_lock,
)


PROVIDERS: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
}


def generate_text(
    task: Task,
    prompt: str,
    system_instruction: str = None,
) -> str:
    """
    Generate text for a NoteTube task with persistent response caching.

    Flow:
        Task
        -> Requirements
        -> Model Strategy
        -> Cache
        -> Provider
        -> Response
        -> Cache
    """

    config = AI_ROUTING_CONFIG.get(task)

    if not config:
        raise ValueError(
            f"No routing configuration found for task: {task}"
        )

    requirements = TASK_REQUIREMENTS.get(task)

    if requirements is None:
        raise ValueError(
            f"No task requirements found for task: {task}"
        )

    model_strategy = TASK_MODEL_STRATEGY.get(task)

    if model_strategy is None:
        raise ValueError(
            f"No model strategy found for task: {task}"
        )

    provider_names = config.get("providers", [])

    if not provider_names:
        raise ValueError(
            f"No providers configured for task: {task}"
        )

    # Create a deterministic cache key from the complete request.
    cache_key = make_cache_key(
        task,
        prompt,
        system_instruction,
        model_strategy,
    )

    # Fast path: cached response means no API call.
    cached_response = get_cached(cache_key)

    if cached_response is not None:
        return cached_response

    # Prevent duplicate simultaneous requests for the same request.
    cache_lock = get_key_lock(cache_key)

    with cache_lock:
        # Another request may have completed while we waited.
        cached_response = get_cached(cache_key)

        if cached_response is not None:
            return cached_response

        errors = []

        for provider_name in provider_names:
            provider_class = PROVIDERS.get(provider_name)

            if not provider_class:
                errors.append(
                    f"{provider_name}: provider is not implemented"
                )
                continue

            try:
                provider = provider_class()

                response = provider.generate_text(
                    prompt,
                    system_instruction,
                    model=model_strategy,
                )

                # Cache only successful non-empty responses.
                set_cached(
                    cache_key,
                    task,
                    model_strategy,
                    response,
                )

                return response

            except Exception as exc:
                errors.append(
                    f"{provider_name}: {exc}"
                )

    raise RuntimeError(
        f"All AI providers failed for task '{task.value}'. "
        f"Strategy: {model_strategy}. "
        f"Requirements: {requirements}. "
        f"Errors: {' | '.join(errors)}"
    )