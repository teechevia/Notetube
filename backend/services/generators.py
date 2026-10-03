import json

from services.ai_router import generate_text
from services.ai_config import Task


def summarize_chunks(chunks, batch_size=12, job_id=None):
    """
    Extract source-grounded knowledge from chunks.

    Every extracted item remains traceable to source chunk IDs.

    If job_id is provided:
    - the job is started
    - progress is updated after each completed batch
    - the job is failed if any batch fails
    """

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from services.job_manager import (
        start_job,
        update_progress,
        fail_job,
    )

    if not chunks:
        return []

    batches = [
        chunks[i:i + batch_size]
        for i in range(0, len(chunks), batch_size)
    ]

    total_batches = len(batches)

    if job_id:
        start_job(job_id)
        update_progress(
            job_id,
            completed_units=0,
            total_units=total_batches,
            stage="extracting_knowledge",
        )

    def process_batch(index):
        batch = batches[index]
        offset = index * batch_size

        batch_text = "\n\n".join(
            f"[SOURCE CHUNK {offset + j}]\n{chunk}"
            for j, chunk in enumerate(batch)
        )

        prompt = f"""
You are an evidence-first knowledge extractor.

Your ONLY factual authority is the SOURCE CHUNKS below.

Your job is to extract information that is explicitly supported
by those chunks while preserving enough detail for later note generation.

CRITICAL GROUNDING RULES:

1. NEVER add outside knowledge.
2. NEVER infer information that is not explicitly stated.
3. NEVER convert a possibility into a fact.
4. NEVER add motivations, purposes, benefits, applications,
   causes, effects, or implications unless explicitly stated.
5. NEVER add examples that are not in the source.
6. NEVER rename or reinterpret a concept in a way that changes
   its meaning.
7. Preserve exact numbers, names, terminology, conditions,
   qualifications, and uncertainty.
8. If something is not stated, DO NOT fill the gap.
9. Every factual item MUST contain its source chunk ID.
10. Evidence must be copied directly or nearly directly from
    the source. Do not fabricate evidence.

IMPORTANT:
"separately" does NOT mean "in parallel".
"checks" does NOT mean "accepts or rejects".
"used for X" does NOT mean "designed to achieve X".
Do not make these kinds of logical expansions.

OUTPUT FORMAT:

## Evidence

For every meaningful factual statement, create an item:

- [Chunk N] Evidence: "short exact quote from source"
  Fact: faithful restatement of ONLY what the evidence says.

## Concepts and Definitions

Only include concepts explicitly defined or described by the source.

- [Chunk N] Concept: ...
  Evidence: "..."

## Processes and Sequences

Only include steps explicitly described by the source.

- [Chunk N] Step: ...
  Evidence: "..."

## Explicit Relationships

Only include relationships explicitly stated by the source.

- [Chunk N] Relationship: ...
  Evidence: "..."

## Explicit Examples

Only include examples explicitly present in the source.

- [Chunk N] Example: ...
  Evidence: "..."

## Explicit Conclusions

Only include conclusions explicitly stated in the source.

- [Chunk N] Conclusion: ...
  Evidence: "..."

SOURCE CHUNKS:

{batch_text}
"""

        result = generate_text(
            Task.HUMAN_NOTES,
            prompt,
            system_instruction=(
                "You are a strict source-grounding engine. "
                "The supplied chunks are the only factual authority. "
                "Do not infer, extrapolate, generalize, or add outside "
                "knowledge. Every factual statement must be traceable "
                "to an explicit source chunk."
            ),
        )

        return index, result

    results = [None] * total_batches
    completed = 0
    errors = []

    with ThreadPoolExecutor(
        max_workers=min(4, total_batches)
    ) as executor:

        futures = [
            executor.submit(process_batch, i)
            for i in range(total_batches)
        ]

        for future in as_completed(futures):
            try:
                index, result = future.result()
                results[index] = result
                completed += 1

                if job_id:
                    update_progress(
                        job_id,
                        completed_units=completed,
                        total_units=total_batches,
                        stage="extracting_knowledge",
                    )

            except Exception as exc:
                errors.append(str(exc))
                completed += 1

                if job_id:
                    update_progress(
                        job_id,
                        completed_units=completed,
                        total_units=total_batches,
                        stage="extracting_knowledge",
                    )

    if errors:
        error_message = " | ".join(errors)

        if job_id:
            fail_job(job_id, error_message)

        raise RuntimeError(
            f"Knowledge extraction failed: {error_message}"
        )

    return results


def synthesize_summaries(summaries, job_id=None):
    """
    Consolidate knowledge representations while preserving source detail.

    This stage is intentionally NOT a compact summary.
    """

    from services.job_manager import (
        update_progress,
        fail_job,
    )

    if not summaries:
        return ""

    if len(summaries) == 1:
        return summaries[0]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    group_size = 4

    groups = [
        summaries[i:i + group_size]
        for i in range(0, len(summaries), group_size)
    ]

    total_units = len(groups) + 1

    if job_id:
        update_progress(
            job_id,
            completed_units=0,
            total_units=total_units,
            stage="synthesizing_knowledge",
        )

    def merge_group(index):
        group = groups[index]

        group_text = "\n\n".join(
            f"[Knowledge Section {index * group_size + j + 1}]\n{summary}"
            for j, summary in enumerate(group)
        )

        prompt = f"""
You are consolidating knowledge extracted from multiple sections
of the SAME source.

This is a knowledge-preservation task, NOT a short summarization task.

Rules:
- Use ONLY the supplied knowledge sections.
- Do not introduce outside knowledge.
- Do not invent facts, examples, explanations, causes, or conclusions.
- Preserve unique information.
- Remove only genuine duplication.
- Preserve definitions and terminology.
- Preserve important facts, numbers, dates, qualifications, and exceptions.
- Preserve examples.
- Preserve processes and sequences.
- Preserve comparisons and relationships.
- Preserve conclusions supported by the source.
- If two sections contain related information, connect them without
  deleting their individual details.
- Do NOT compress detailed information into generic statements.

Organize the result under:

## Topics

## Concepts and Definitions

## Important Facts and Details

## Processes and Sequences

## Examples

## Relationships and Connections

## Conclusions

The output should remain detailed enough that another model can
create comprehensive study notes without needing the original chunks.

KNOWLEDGE SECTIONS:

{group_text}
"""

        result = generate_text(
            Task.HUMAN_NOTES,
            prompt,
            system_instruction=(
                "You are an expert academic knowledge consolidator. "
                "Preserve all meaningful source-supported information. "
                "Do not trade factual detail for brevity."
            ),
        )

        return index, result

    merged_sections = [None] * len(groups)
    completed_groups = 0
    errors = []

    with ThreadPoolExecutor(
        max_workers=min(4, len(groups))
    ) as executor:

        futures = [
            executor.submit(merge_group, i)
            for i in range(len(groups))
        ]

        for future in as_completed(futures):
            try:
                index, result = future.result()
                merged_sections[index] = result
                completed_groups += 1

                if job_id:
                    update_progress(
                        job_id,
                        completed_units=completed_groups,
                        total_units=total_units,
                        stage="synthesizing_knowledge",
                    )

            except Exception as exc:
                errors.append(str(exc))
                completed_groups += 1

    if errors:
        error_message = " | ".join(errors)

        if job_id:
            fail_job(job_id, error_message)

        raise RuntimeError(
            f"Knowledge synthesis failed: {error_message}"
        )

    if len(merged_sections) == 1:
        return merged_sections[0]

    sections_text = "\n\n".join(
        f"[Consolidated Section {i + 1}]\n{section}"
        for i, section in enumerate(merged_sections)
    )

    prompt = f"""
You are creating the final knowledge representation of a source.

The material below contains consolidated knowledge from different
parts of the same source.

Create one coherent, detailed knowledge representation that can be
used as the source material for comprehensive human-quality study notes.

This is NOT a short summary.

Rules:
- Use ONLY information contained in the supplied sections.
- Do not introduce outside knowledge.
- Do not invent facts, examples, explanations, causes, or conclusions.
- Preserve unique information.
- Remove genuine repetition only.
- Preserve important terminology.
- Preserve definitions.
- Preserve facts, numbers, dates, qualifications, and exceptions.
- Preserve examples.
- Preserve processes and sequences.
- Preserve relationships and comparisons.
- Preserve source-supported conclusions.
- Do not collapse several distinct concepts into one generic statement.
- Prefer completeness and clarity over brevity.

Organize logically so that related information is easy to understand.

CONSOLIDATED SECTIONS:

{sections_text}
"""

    try:
        result = generate_text(
            Task.HUMAN_NOTES,
            prompt,
            system_instruction=(
                "You are an expert academic knowledge synthesizer. "
                "The supplied consolidated sections are the only factual "
                "authority. Preserve meaningful information and context. "
                "Do not aggressively compress the material."
            ),
        )

        if job_id:
            update_progress(
                job_id,
                completed_units=total_units,
                total_units=total_units,
                stage="synthesis_complete",
            )

        return result

    except Exception as exc:
        if job_id:
            fail_job(job_id, str(exc))

        raise


def clean_json_response(res: str):
    res = res.strip()

    if res.startswith("```json"):
        res = res[7:]

    if res.endswith("```"):
        res = res[:-3]

    return res.strip()


def generate_flashcards(transcript: str):
    prompt = (
        "Create 10 important flashcards from this text. "
        "Return ONLY a valid JSON array of objects. "
        "Each object must have exactly two keys: "
        "'front' (the question or term) and "
        "'back' (the answer or definition). "
        "Do NOT include markdown blocks like ```json.\n\n"
        f"Text:\n{transcript}"
    )

    res = generate_text(Task.FLASHCARDS, prompt)

    try:
        return json.loads(clean_json_response(res))

    except Exception as e:
        return [
            {
                "front": "Error generating flashcards",
                "back": str(e),
            }
        ]


def generate_quiz(transcript: str):
    prompt = (
        "Create a 5-question multiple choice quiz from this text. "
        "Return ONLY a valid JSON array of objects. "
        "Each object must have: 'question' (string), "
        "'options' (array of 4 strings), and "
        "'answer' (the exact string of the correct option). "
        "Do NOT include markdown blocks.\n\n"
        f"Text:\n{transcript}"
    )

    res = generate_text(Task.QUIZ, prompt)

    try:
        return json.loads(clean_json_response(res))

    except Exception:
        return [
            {
                "question": "Error generating quiz",
                "options": ["A", "B", "C", "D"],
                "answer": "A",
            }
        ]


def generate_briefing_doc(transcript: str):
    prompt = (
        "Create a comprehensive Briefing Doc summarizing this text. "
        "Use Markdown. Include an Executive Summary, Key Takeaways, "
        "and Detailed Breakdown.\n\n"
        f"Text:\n{transcript}"
    )

    return generate_text(Task.BRIEFING, prompt)


def generate_human_notes(transcript: str, job_id=None):
    """
    Generate human-quality study notes from large source material.

    The source is processed hierarchically:

        source chunks
        -> batch knowledge extraction
        -> knowledge synthesis
        -> final study notes
    """

    from services.job_manager import (
        start_job,
        update_progress,
        complete_job,
        fail_job,
    )

    chunks = [
        chunk.strip()
        for chunk in transcript.split("\n\n")
        if chunk.strip()
    ]

    if not chunks:
        return ""

    if job_id:
        start_job(job_id)

        update_progress(
            job_id,
            completed_units=0,
            total_units=1,
            stage="preparing_source",
        )

    try:
        # Small source:
        # No chunk-level extraction is necessary.
        if len(chunks) <= 12:
            source_for_notes = transcript

            if job_id:
                update_progress(
                    job_id,
                    completed_units=1,
                    total_units=2,
                    stage="preparing_source",
                )

        else:
            # Large source:
            # First stage = source-grounded knowledge extraction.
            summaries = summarize_chunks(
                chunks,
                batch_size=12,
                job_id=job_id,
            )

            # Second stage = hierarchical synthesis.
            source_for_notes = synthesize_summaries(
                summaries,
                job_id=job_id,
            )

        if job_id:
            update_progress(
                job_id,
                completed_units=0,
                total_units=1,
                stage="generating_final_notes",
            )

        prompt = f"""
You are transforming SOURCE MATERIAL into study notes.

ABSOLUTE RULE:
The SOURCE MATERIAL is the complete and only factual authority.

Your job is NOT to explain the subject using your own knowledge.
Your job is to reorganize and clarify what the source actually says.

SOURCE FIDELITY HAS PRIORITY OVER COMPLETENESS.

If the source contains little information, the final notes must contain
little information.

========================
ALLOWED TRANSFORMATIONS
========================

You MAY:

- Rewrite a source statement using clearer language.
- Simplify wording without changing its factual meaning.
- Combine multiple source statements when the combined statement adds
  no information beyond those statements.
- Reorder source statements for better organization.
- Convert source statements into bullets, tables, or lists.
- Repeat information in a different section when necessary for structure.
- Explain a term ONLY when the source itself provides that explanation.
- State a relationship ONLY when the source explicitly establishes it.
- State a process ONLY when the source explicitly describes that process.
- State a cause, effect, purpose, benefit, limitation, or significance
  ONLY when the source explicitly states it.

========================
ABSOLUTE PROHIBITIONS
========================

DO NOT use pretrained knowledge.

DO NOT add facts because they are:
- commonly known
- logically implied
- technically correct
- useful for understanding
- likely true
- associated with the topic

DO NOT invent:
- examples
- explanations
- causes
- effects
- purposes
- applications
- benefits
- limitations
- relationships
- comparisons
- processes
- sequences
- motivations
- consequences

DO NOT expand a short source statement into a broader explanation.

If the source says:

"Branches allow different lines of development."

You may write:

"Branches allow different lines of development."

You may also write:

"Branches provide different lines of development."

You MUST NOT write:

"Branches allow developers to work independently."

You MUST NOT write:

"Branches are useful for developing features and fixes."

You MUST NOT write:

"Branches allow multiple developers to work simultaneously."

Those statements may be true in general, but they are NOT supported
by the source.

========================
SECTION RULES
========================

# Study Notes

## Overview

Only state what the source explicitly says about the overall material.

Do not invent a broader description of the subject.

## Core Concepts

List concepts explicitly present in the source.

For each concept, include ONLY information explicitly supported by
the source.

Use:

### Concept Name

**Definition:** Only if the source defines it.

**Explanation:** Only if the source explains it.

**Example:** Only if the source gives an example.

**Connections:** Only if the source explicitly connects it to another
concept.

Do NOT create missing sections just to make the notes look complete.

## Detailed Explanation

Rewrite and organize the source information into a logical order.

Do not add explanations that are absent from the source.

## Processes and Sequences

Include this section ONLY if the source explicitly describes a process
or sequence.

Preserve the source's actual order.

Do NOT construct a process by combining facts that merely appear
related.

## Comparisons and Relationships

Include ONLY relationships or comparisons that the source explicitly
states as a relationship.

Do NOT create a relationship merely because two source statements
appear related.

For example, if the source says:

"Branches allow different lines of development."
"Developers can merge branches to combine changes."

Do NOT combine them into a new relationship such as:
"Branches can later be merged to combine development lines."

Keep the statements separate unless the source explicitly connects them.

## Examples

Include ONLY examples explicitly present in the source.

If there are no examples, omit this section.

## Important Details

Preserve important:
- facts
- terminology
- numbers
- dates
- conditions
- exceptions
- qualifications
- limitations
- uncertainty
- explicit conclusions

## Key Takeaways

Create concise takeaways by restating the most important source
statements.

Do NOT introduce new information.

========================
FINAL GROUNDING CHECK
========================

Before producing the answer, inspect EVERY factual statement.

For each statement ask:

"Where exactly is this information supported by the SOURCE MATERIAL?"

If the answer is:
- explicitly stated → KEEP IT
- directly restated → KEEP IT
- merely implied → REMOVE IT
- common knowledge → REMOVE IT
- logically obvious → REMOVE IT
- likely true → REMOVE IT
- useful but absent → REMOVE IT

When uncertain, REMOVE the statement.

The final notes must contain less information rather than unsupported
information.

SOURCE MATERIAL:

{source_for_notes}
"""

        result = generate_text(
            Task.HUMAN_NOTES,
            prompt,
            system_instruction=(
                "You are an expert academic tutor creating source-grounded "
                "study notes. The supplied material is the ONLY factual "
                "authority. You may clarify and reorganize information "
                "without changing its meaning, but you must never add "
                "outside knowledge, unsupported explanations, invented "
                "examples, or unstated relationships. Prioritize "
                "comprehension, completeness, structure, and learning value."
            ),
        )

        if job_id:
            update_progress(
                job_id,
                completed_units=1,
                total_units=1,
                stage="notes_generated",
            )

            complete_job(job_id)

        return result

    except Exception as exc:
        if job_id:
            fail_job(job_id, str(exc))

        raise


def generate_faq(transcript: str):
    prompt = (
        "Create a Frequently Asked Questions (FAQ) document based "
        "on this text. Use Markdown. Format as Q: and A: pairs.\n\n"
        f"Text:\n{transcript}"
    )

    return generate_text(Task.FAQ, prompt)


def generate_podcast_script(
    text: str,
    instruction: str = "",
    host_a: str = "Host A",
    host_b: str = "Host B",
) -> list:

    prompt = f"""
Based on the following source material, generate a two-person podcast
script between '{host_a}' and '{host_b}'.

Make it conversational, engaging, and informative.
"""

    if instruction:
        prompt += (
            f"\nCRITICAL INSTRUCTION FOR THE PODCAST: "
            f"{instruction}\n"
        )

    prompt += f"""
Return the response as a JSON array of objects, where each object has
'speaker' (either "{host_a}" or "{host_b}") and 'text'.

Do NOT wrap the output in markdown code blocks, just raw JSON.

Source Material:
{text}
"""

    response = generate_text(
        Task.PODCAST,
        prompt,
        system_instruction="You must reply with valid JSON array only.",
    )

    try:
        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        return json.loads(cleaned_response)

    except json.JSONDecodeError:
        return [
            {
                "speaker": host_a,
                "text": "Error generating podcast script.",
            }
        ]


def generate_interactive_podcast_response(
    user_message: str,
    chat_history: str,
    host_a: str = "Host A",
    host_b: str = "Host B",
) -> list:

    prompt = f"""
You are roleplaying as two podcast hosts, '{host_a}' and '{host_b}'.
The user has just joined your live podcast and said:
"{user_message}"

Here is the recent context of the conversation:
{chat_history}

Generate a very short, continuous podcast response
(1 to 3 lines total) where the hosts reply directly to the user
or discuss what the user just said.

Return the response as a JSON array of objects, where each object has
'speaker' (either "{host_a}" or "{host_b}") and 'text'.

Do NOT wrap the output in markdown code blocks, just raw JSON.
"""

    response = generate_text(
        Task.PODCAST,
        prompt,
        system_instruction="You must reply with valid JSON array only.",
    )

    try:
        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        return json.loads(cleaned_response)

    except json.JSONDecodeError:
        return [
            {
                "speaker": host_a,
                "text": "Whoa, looks like we had a technical glitch!",
            }
        ]