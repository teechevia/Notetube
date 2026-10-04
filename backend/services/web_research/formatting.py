from .models import WebEvidence


MAX_WEB_CONTEXT_CHARS = 24000


def format_web_evidence(evidence: list[WebEvidence]) -> str:
    if not evidence:
        return ""

    sections = []
    total_chars = 0

    for index, item in enumerate(evidence, start=1):
        section = (
            f"========== WEB SOURCE {index} ==========\n"
            f"Title: {item.title}\n"
            f"Domain: {item.domain}\n"
            f"Type: {item.source_type}\n"
            f"URL: {item.url}\n"
            f"Content:\n{item.content.strip()}\n"
            f"========== END WEB SOURCE {index} =========="
        )

        separator_chars = 2 if sections else 0
        available = MAX_WEB_CONTEXT_CHARS - total_chars - separator_chars

        if available <= 0:
            break

        if len(section) > available:
            section = section[:available]

        if sections:
            total_chars += 2

        sections.append(section)
        total_chars += len(section)

        if total_chars >= MAX_WEB_CONTEXT_CHARS:
            break

    return "\n\n".join(sections)
