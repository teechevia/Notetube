def should_research_web(
    query: str,
    notebook_context: str,
    has_relevant_evidence: bool = True,
) -> bool:
    normalized_query = query.lower().strip()

    if not notebook_context.strip():
        return True

    if not has_relevant_evidence:
        return True

    research_keywords = (
        "latest",
        "current",
        "recent",
        "research",
        "study",
        "paper",
        "according to",
        "outside",
        "compare with",
        "compare to",
        "external",
        "web",
    )

    if any(
        keyword in normalized_query
        for keyword in research_keywords
    ):
        return True

    return False
