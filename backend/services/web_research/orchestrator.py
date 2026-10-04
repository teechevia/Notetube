from .agent import research_web
from .rag_gate import should_augment_rag
from .formatting import format_web_evidence
from .augmentation import augment_rag_context


def run_research_augmentation(
    query: str,
    notebook_context: str,
    evidence_by_question: dict,
):
    if not should_augment_rag(
        query=query,
        notebook_context=notebook_context,
        evidence_by_question=evidence_by_question,
    ):
        return {
            "researched": False,
            "query": query,
            "evidence": [],
            "context": notebook_context,
        }

    try:
        research = research_web(query)
    except Exception as exc:
        return {
            "researched": False,
            "query": query,
            "evidence": [],
            "results": [],
            "context": notebook_context,
            "error": str(exc),
        }

    evidence = research["evidence"]

    if not evidence:
        return {
            "researched": True,
            "query": query,
            "plan": research["plan"],
            "results": research["results"],
            "evidence": [],
            "context": notebook_context,
        }

    web_context = format_web_evidence(evidence)

    combined_context = augment_rag_context(
        notebook_context=notebook_context,
        web_context=web_context,
    )

    return {
        "researched": True,
        "query": query,
        "plan": research["plan"],
        "results": research["results"],
        "evidence": evidence,
        "context": combined_context,
    }
