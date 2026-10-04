def build_web_research_context(
    notebook_context: str,
    web_context: str,
) -> str:
    sections = []

    if notebook_context.strip():
        sections.append(
            "========== NOTEBOOK SOURCES ==========\n"
            "These are the user's provided sources. "
            "Treat them as the primary source of truth for notebook-specific questions.\n\n"
            f"{notebook_context.strip()}\n"
            "========== END NOTEBOOK SOURCES =========="
        )

    if web_context.strip():
        sections.append(
            "========== WEB RESEARCH ==========\n"
            "These sources were retrieved from the web as supplementary research. "
            "Do not represent web information as if it came from the notebook sources.\n\n"
            f"{web_context.strip()}\n"
            "========== END WEB RESEARCH =========="
        )

    return "\n\n".join(sections)


WEB_RESEARCH_INSTRUCTIONS = """
Use web research only as supplementary evidence.

Rules:
1. Prefer notebook sources for claims about the user's uploaded material.
2. Use web sources only when they add relevant information or fill a genuine gap.
3. Never claim that web-derived information came from the notebook.
4. Do not invent facts that are unsupported by the provided evidence.
5. When notebook and web sources disagree, make the distinction explicit.
6. Prefer official and research sources over general web pages.
7. Keep web-derived claims clearly attributable to their web sources.
"""
