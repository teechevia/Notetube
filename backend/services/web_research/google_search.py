from google import genai
from google.genai import types

from config import GEMINI_API_KEY

from .models import WebSearchResult


DEFAULT_MODEL = "gemini-2.5-flash"


def _extract_grounding_chunks(response):
    candidates = getattr(response, "candidates", None) or []

    if not candidates:
        return []

    grounding = getattr(candidates[0], "grounding_metadata", None)

    if not grounding:
        return []

    return getattr(grounding, "grounding_chunks", None) or []


def search_web(
    query: str,
    model: str = DEFAULT_MODEL,
) -> tuple[str, list[WebSearchResult]]:
    client = genai.Client(api_key=GEMINI_API_KEY)

    tool = types.Tool(
        google_search=types.GoogleSearch()
    )

    config = types.GenerateContentConfig(
        tools=[tool]
    )

    response = client.models.generate_content(
        model=model,
        contents=query,
        config=config,
    )

    results = []

    for chunk in _extract_grounding_chunks(response):
        web = getattr(chunk, "web", None)

        if not web:
            continue

        title = getattr(web, "title", "") or ""
        url = getattr(web, "uri", "") or ""

        if not url:
            continue

        results.append(
            WebSearchResult(
                title=title,
                url=url,
                snippet="",
                domain="",
                source_type="web",
            )
        )

    return response.text or "", results
