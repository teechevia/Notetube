from .synthesis import build_web_research_context


def augment_rag_context(
    notebook_context: str,
    web_context: str = "",
) -> str:
    return build_web_research_context(
        notebook_context=notebook_context,
        web_context=web_context,
    )
