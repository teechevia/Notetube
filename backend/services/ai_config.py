from enum import Enum


class Task(Enum):
    CHAT = "CHAT"
    HUMAN_NOTES = "HUMAN_NOTES"
    BRIEFING = "BRIEFING"
    FLASHCARDS = "FLASHCARDS"
    QUIZ = "QUIZ"
    FAQ = "FAQ"
    PODCAST = "PODCAST"


# What each task needs.
TASK_REQUIREMENTS = {
    Task.CHAT: {
        "reasoning": True,
        "long_context": True,
        "structured_output": False,
    },

    Task.HUMAN_NOTES: {
        "reasoning": True,
        "long_context": True,
        "structured_output": False,
    },

    Task.BRIEFING: {
        "reasoning": False,
        "long_context": True,
        "structured_output": False,
    },

    Task.FLASHCARDS: {
        "reasoning": False,
        "long_context": True,
        "structured_output": True,
    },

    Task.QUIZ: {
        "reasoning": True,
        "long_context": True,
        "structured_output": True,
    },

    Task.FAQ: {
        "reasoning": False,
        "long_context": True,
        "structured_output": True,
    },

    Task.PODCAST: {
        "reasoning": True,
        "long_context": True,
        "structured_output": False,
    },
}


# Model strategy for each task.
#
# These are capabilities, NOT specific model IDs.
# Providers decide which currently available model
# satisfies the strategy.

TASK_MODEL_STRATEGY = {
    Task.CHAT: "reasoning_long_context",
    Task.HUMAN_NOTES: "reasoning_long_context",
    Task.BRIEFING: "long_context_fast",
    Task.FLASHCARDS: "structured_output",
    Task.QUIZ: "reasoning_structured",
    Task.FAQ: "structured_output",
    Task.PODCAST: "reasoning_long_context",
}


# Provider fallback order.
#
# This controls reliability.
# It does NOT claim that one provider is universally
# better than another.

AI_ROUTING_CONFIG = {
    Task.CHAT: {
        "providers": ["gemini", "openrouter", "groq"],
    },

    Task.HUMAN_NOTES: {
        "providers": ["gemini", "openrouter", "groq"],
    },

    Task.BRIEFING: {
        "providers": ["gemini", "openrouter", "groq"],
    },

    Task.FLASHCARDS: {
        "providers": ["openrouter", "gemini", "groq"],
    },

    Task.QUIZ: {
        "providers": ["gemini", "openrouter", "groq"],
    },

    Task.FAQ: {
        "providers": ["openrouter", "gemini", "groq"],
    },

    Task.PODCAST: {
        "providers": ["gemini", "openrouter", "groq"],
    },
}
