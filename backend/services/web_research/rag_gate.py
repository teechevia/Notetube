from .gate import should_research_web


def should_augment_rag(
    query: str,
    notebook_context: str,
    evidence_by_question: dict,
) -> bool:
    has_relevant_evidence = any(
        bool(items)
        for items in evidence_by_question.values()
    )

    return should_research_web(
        query=query,
        notebook_context=notebook_context,
        has_relevant_evidence=has_relevant_evidence,
    )
