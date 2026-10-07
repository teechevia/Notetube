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
            (
                f"[SOURCE CHUNK {offset + j}]"
                f" [source_id={getattr(chunk, "metadata", {}).get("source_id", "unknown")}]"
                f" [chunk_index={getattr(chunk, "metadata", {}).get("chunk_index", offset + j)}]\n"
                f"{getattr(chunk, "page_content", chunk)}"
            )
            for j, chunk in enumerate(batch)
        )

        prompt = f"""
You are extracting structured knowledge from SOURCE CHUNKS for a
long-context knowledge system.

The SOURCE CHUNKS are the ONLY factual authority.

Your goal is NOT merely to list facts. Preserve the actual knowledge,
explanations, mechanisms, models, examples, arguments, and relationships
contained in the source so that downstream generators can produce
human-quality study material without needing the original chunks.

========================
CORE EXTRACTION PRINCIPLE
========================

Extract MEANING, not just metadata.

When the source explains a concept, model, theory, process, argument,
mechanism, or example, preserve the explanation in enough detail to
reconstruct what the source actually teaches.

For each substantive concept or model, capture when supported:

- What it is.
- The question or problem it addresses.
- The central idea or explanation.
- How it works or unfolds.
- Its components, stages, or factors.
- Explicit causes and effects.
- Explicit relationships with other ideas.
- Source-provided examples.
- Evidence or reasoning used by the source.
- Explicit consequences or implications.
- Explicit comparisons or contrasts.
- Conditions, exceptions, limitations, and uncertainty.
- Supporting source chunk references.

NEVER reduce a substantive model to only its name or category.

If a chunk explains a model through several stages, preserve those stages
and what happens at each stage.

If a chunk explains why a phenomenon occurs, preserve that explanation.

If a source example illustrates a mechanism, preserve both the example and
the source-supported connection between them.

IMPORTANT INFERENCE RULE:
Never create an "implied", "inferred", "suggested", "potential", or
"interpretive" relationship, process, definition, cause, effect, or
explanation.

If the source does not explicitly support a field, OMIT that field.

Do not turn source material into:
- recommendations or policy advice
- strategic advice
- predictions not explicitly stated by the source
- interpretations of what a model "really means"
- synthesized causal mechanisms that the source does not explicitly state
- claims that separate concepts are mutually reinforcing
- claims about what readers, organizations, governments, or businesses
  should do

A conclusion may summarize source-supported claims, but it must not add a
new recommendation, interpretation, implication, or causal relationship.

Do not write phrases such as:
- implied within
- implied process
- inferred relationship
- potential overlap
- can be viewed as
- may represent
- suggests that [when the source does not explicitly say it]

The knowledge representation must contain source-supported knowledge,
not your own interpretation of how separate source statements fit together.

========================
STRICT GROUNDING
========================

DO NOT use pretrained knowledge.

DO NOT fill gaps using common knowledge.

DO NOT infer information that the source does not explicitly support.

DO NOT add definitions, explanations, causes, effects, examples,
applications, benefits, limitations, historical context, technical
details, relationships, or interpretations unless supported by the source.

Do not make a source statement stronger than it is.

Preserve uncertainty, disagreement, qualifications, conditions,
exceptions, and limitations.

When the source presents multiple viewpoints, preserve the distinction
between them.

========================
TRACEABILITY
========================

Every substantive extracted item MUST include its supporting chunk
reference in the form [Chunk N].

If information is distributed across multiple chunks, preserve all
relevant chunk references.

Do not remove a reference merely because the same concept appears
elsewhere.

========================
PRIORITY
========================

Prioritize substantive knowledge over incidental metadata.

CORE KNOWLEDGE:
Central models, concepts, mechanisms, arguments, theories, processes,
conclusions, and explanations.

SUPPORTING KNOWLEDGE:
Details that explain, qualify, connect, or provide evidence for core ideas.

EXAMPLES:
Concrete examples explicitly provided by the source.

CONTEXT:
Background needed to understand or organize the material.

ADMINISTRATIVE / BIBLIOGRAPHIC:
ISBNs, publishers, addresses, catalogue information, library notices,
copyright information, and similar metadata.

Preserve administrative information when present, but do not allow it to
replace substantive subject knowledge.

========================
OUTPUT FORMAT
========================

## Core Knowledge

For every major substantive concept, model, theory, or idea:

### [Concept / Model Name]

- What it is:
- Central question or problem:
- Core explanation:
- Mechanism / how it works:
- Components / stages:
- Causes and effects:
- Relationships:
- Examples:
- Consequences / implications:
- Conditions / limitations / uncertainty:
- Supporting chunks:

Only include fields supported by the source.
Do NOT force unsupported fields.

If several chunks describe the same concept, combine them while preserving
all relevant chunk references.

## Processes and Sequences

Capture source-described processes, stages, chains, or progressions.

Preserve the actual order and explain what happens at each stage when the
source provides that information.

## Relationships and Connections

Capture explicit relationships, dependencies, contrasts, comparisons,
cause-effect links, or connections between concepts.

## Evidence and Examples

Preserve important source-provided evidence, examples, cases,
observations, quotations, or demonstrations when they help explain the
substantive knowledge.

## Important Details

Preserve important terminology, numbers, dates, conditions, exceptions,
qualifications, limitations, uncertainty, and explicit conclusions.

## Administrative / Bibliographic

Keep useful metadata compactly.

========================
DEDUPLICATION
========================

Remove only genuine repetition.

Do NOT remove information merely because two chunks discuss the same
concept if they provide different explanations, examples, evidence,
qualifications, or mechanisms.

When combining repeated information, retain the richest
source-supported explanation and preserve every relevant chunk reference.

========================
QUALITY CHECK
========================

Before finalizing, verify:

1. Explanations were preserved, not just names.
2. Models retain their mechanisms, stages, and reasoning when present.
3. Important examples and evidence were preserved.
4. Relationships between ideas were preserved.
5. Qualifications and uncertainty were preserved.
6. Every substantive claim has a [Chunk N] reference.
7. No outside knowledge was introduced.
8. Metadata does not overwhelm substantive knowledge.

The output becomes persistent knowledge used by downstream generators.
Information lost here may not be recoverable later.

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
- PRESERVE every existing [Chunk N] source reference and keep it attached
  to the factual information it supports.
- Do not remove, rename, merge, or invent chunk references.
- If multiple chunks support the same statement, preserve all relevant
  chunk references.
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

    # Recursively consolidate sections so the final synthesis
    # never receives an unbounded amount of source material.
    current_sections = merged_sections
    synthesis_round = 1

    while len(current_sections) > 4:
        next_sections = []

        for i in range(0, len(current_sections), 4):
            group = current_sections[i:i + 4]

            group_text = "\n\n".join(
                f"[Knowledge Section {i + j + 1}]\n{section}"
                for j, section in enumerate(group)
            )

            recursive_prompt = f"""
You are consolidating knowledge from several sections of the SAME source.

This is a knowledge-preservation task, NOT a short summary.

Rules:
- Use ONLY the supplied sections.
- Do not introduce outside knowledge.
- Do not invent facts, examples, explanations, causes, or conclusions.
- Preserve unique information.
- Remove only genuine duplication.
- Preserve terminology, definitions, facts, numbers, dates,
  qualifications, exceptions, examples, processes, relationships,
  comparisons, and conclusions.
- PRESERVE every existing [Chunk N] source reference and keep it attached
  to the factual information it supports.
- Do not remove, rename, merge, or invent chunk references.
- If multiple chunks support the same statement, preserve all relevant
  chunk references.
- Do not collapse distinct concepts into generic statements.
- Prefer completeness and clarity over brevity.

Return one detailed consolidated knowledge section.

KNOWLEDGE SECTIONS:

{group_text}
"""

            next_sections.append(
                generate_text(
                    Task.HUMAN_NOTES,
                    recursive_prompt,
                    system_instruction=(
                        "You are a strict academic knowledge consolidator. "
                        "The supplied sections are the only factual authority. "
                        "Preserve meaningful information and context."
                    ),
                )
            )

        current_sections = next_sections
        synthesis_round += 1

    if len(current_sections) == 1:
        return current_sections[0]

    sections_text = "\n\n".join(
        f"[Consolidated Section {i + 1}]\n{section}"
        for i, section in enumerate(current_sections)
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
- PRESERVE every existing [Chunk N] source reference and keep it attached
  to the factual information it supports.
- Do not remove, rename, merge, or invent chunk references.
- If multiple chunks support the same statement, preserve all relevant
  chunk references.
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
        "Create exactly 10 source-grounded flashcards from the supplied source.\n\n"
        "STRICT SOURCE RULES:\n"
        "- Every question and answer must be directly supported by the source.\n"
        "- Do NOT use outside knowledge.\n"
        "- Do NOT invent facts, examples, explanations, relationships, or "
        "definitions.\n"
        "- Answers must preserve the meaning of the source.\n"
        "- Prefer important definitions, explicit facts, processes, "
        "examples, and relationships stated in the source.\n"
        "- If the source contains fewer than 10 distinct facts, create "
        "different questions from the available source information without "
        "adding new information.\n\n"
        "Return ONLY a valid JSON array of exactly 10 objects. "
        "Each object must have exactly two keys: "
        "'front' and 'back'. "
        "Do NOT include markdown code fences.\n\n"
        f"Source:\n{transcript}"
    )

    res = generate_text(
        Task.FLASHCARDS,
        prompt,
        system_instruction=(
            "Generate only source-grounded flashcards. "
            "The source is the only factual authority. "
            "Never add outside or inferred information."
        ),
    )

    try:
        cards = json.loads(clean_json_response(res))

        if not isinstance(cards, list) or len(cards) != 10:
            raise ValueError("Expected exactly 10 flashcards")

        for card in cards:
            if (
                not isinstance(card, dict)
                or set(card.keys()) != {"front", "back"}
                or not isinstance(card["front"], str)
                or not isinstance(card["back"], str)
            ):
                raise ValueError("Invalid flashcard structure")

        return cards

    except Exception as e:
        return [
            {
                "front": "Error generating flashcards",
                "back": str(e),
            }
        ]


def generate_quiz(transcript: str):
    prompt = (
        "Create exactly 5 source-grounded multiple-choice questions from "
        "the supplied source.\n\n"
        "STRICT SOURCE RULES:\n"
        "- Every question must be answerable from the source alone.\n"
        "- The correct answer must be explicitly supported by the source.\n"
        "- Every distractor must also be derived from information stated "
        "in the source.\n"
        "- Do NOT invent facts merely to create distractors.\n"
        "- Do NOT use outside knowledge or inferred information.\n"
        "- Do NOT create causes, effects, purposes, examples, relationships, "
        "or conclusions that are not explicitly stated.\n\n"
        "Return ONLY a valid JSON array of exactly 5 objects. "
        "Each object must have exactly these keys: "
        "'question', 'options', and 'answer'. "
        "'options' must contain exactly 4 strings. "
        "'answer' must exactly match one option. "
        "Do NOT include markdown code fences.\n\n"
        f"Source:\n{transcript}"
    )

    res = generate_text(
        Task.QUIZ,
        prompt,
        system_instruction=(
            "Generate a source-grounded quiz only. "
            "The source is the only factual authority. "
            "Never introduce outside or inferred facts."
        ),
    )

    try:
        quiz = json.loads(clean_json_response(res))

        if not isinstance(quiz, list) or len(quiz) != 5:
            raise ValueError("Expected exactly 5 quiz questions")

        for item in quiz:
            if (
                not isinstance(item, dict)
                or set(item.keys()) != {"question", "options", "answer"}
                or not isinstance(item["question"], str)
                or not isinstance(item["options"], list)
                or len(item["options"]) != 4
                or not all(isinstance(option, str) for option in item["options"])
                or not isinstance(item["answer"], str)
                or item["answer"] not in item["options"]
            ):
                raise ValueError("Invalid quiz structure")

        return quiz

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
        "Create a source-grounded Briefing Doc from the supplied source.\n\n"
        "STRICT SOURCE RULES:\n"
        "- The source is the ONLY factual authority.\n"
        "- Every factual statement must be explicitly stated in the source "
        "or be a direct grammatical restatement of a source statement.\n"
        "- You may shorten, reorder, format, or combine statements only when "
        "the resulting sentence preserves exactly the information stated.\n"
        "- Do NOT change relationships between facts.\n"
        "- Do NOT turn a purpose into a capability, a capability into a "
        "result, or an action into an independently stated outcome.\n"
        "- Do NOT add outside knowledge or common knowledge.\n"
        "- Do NOT invent examples, causes, effects, purposes, benefits, "
        "limitations, applications, relationships, or conclusions.\n"
        "- Do NOT infer information merely because it seems logically obvious.\n"
        "- If a detail cannot be stated directly from the source, omit it.\n\n"
        "Use Markdown with exactly these sections:\n"
        "## Executive Summary\n"
        "## Key Takeaways\n"
        "## Detailed Breakdown\n\n"
        "GROUNDING CHECK:\n"
        "Before returning the answer, inspect every factual sentence. "
        "Remove any sentence that adds information not explicitly present "
        "in the source. Prefer omission over unsupported detail.\n\n"
        f"Source:\n{transcript}"
    )

    return generate_text(
        Task.BRIEFING,
        prompt,
        system_instruction=(
            "Create a strictly source-grounded briefing. The supplied source "
            "is the only factual authority. Every factual statement must be "
            "explicitly supported by the source. Never add inferred outcomes, "
            "relationships, explanations, or outside knowledge."
        ),
    )



def prepare_studio_knowledge(source_documents, job_id=None):
    """
    Prepare source material for all long-context Studio generators.

    Structured source chunks are preserved for hierarchical processing.
    Small sources are passed through directly; larger sources are converted
    into bounded, source-grounded knowledge through extraction and synthesis.
    """
    if not source_documents:
        return ""

    if isinstance(source_documents, str):
        chunks = [
            chunk.strip()
            for chunk in source_documents.split("\n\n")
            if chunk.strip()
        ]
        transcript = source_documents
    else:
        chunks = [
            document
            for document in source_documents
            if getattr(document, "page_content", "").strip()
        ]
        transcript = "\n\n".join(
            document.page_content.strip()
            for document in chunks
        )

    if not chunks:
        return ""

    if len(chunks) <= 12:
        return transcript

    summaries = summarize_chunks(
        chunks,
        batch_size=12,
        job_id=job_id,
    )

    return synthesize_summaries(
        summaries,
        job_id=job_id,
    )


def prepare_source_knowledge(source_documents, job_id=None):
    """
    Build persistent knowledge representations independently for each source.

    Returns:
        dict[int, str]: source_id -> source-grounded knowledge
    """
    if not source_documents:
        return {}

    if isinstance(source_documents, str):
        return {}

    grouped = {}

    for document in source_documents:
        metadata = getattr(document, "metadata", {}) or {}
        source_id = metadata.get("source_id")

        if source_id is None:
            continue

        try:
            source_id = int(source_id)
        except (TypeError, ValueError):
            continue

        if getattr(document, "page_content", "").strip():
            grouped.setdefault(source_id, []).append(document)

    knowledge = {}

    for source_id, documents in grouped.items():
        knowledge[source_id] = prepare_studio_knowledge(
            documents,
            job_id=job_id,
        )

    return knowledge


def generate_human_notes(
    source_documents,
    job_id=None,
    prepared_knowledge=None,
):
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

    if not source_documents:
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
        source_for_notes = (
            prepared_knowledge
            if prepared_knowledge is not None
            else prepare_studio_knowledge(
                source_documents,
                job_id=job_id,
            )
        )

        if job_id:
            update_progress(
                job_id,
                completed_units=0,
                total_units=1,
                stage="generating_final_notes",
            )

        prompt = f"""
You are an expert study-note writer.

Transform the SOURCE MATERIAL into clear, human-quality study notes that
help a reader understand and remember the material.

The SOURCE MATERIAL is the only factual authority.
Improve clarity, organization, emphasis, and teaching structure, but NEVER
introduce factual information that is absent from the source.

========================
CORE PRINCIPLE
========================

Do not merely mechanically summarize or list facts.

Teach the material using ONLY information supported by the source.

Prioritize:

1. Core knowledge and major ideas.
2. Important supporting concepts.
3. Explicit relationships between ideas.
4. Source-provided examples and evidence.
5. Source-described processes, sequences, causes, effects, and implications.
6. Important terminology, numbers, dates, conditions, qualifications,
   limitations, and uncertainty.
7. Bibliographic or administrative metadata only when useful, and keep it
   compact.

If the source contains little information about something, do not fill the
gap using outside knowledge.

========================
ALLOWED TRANSFORMATIONS
========================

You MAY:

- Rewrite difficult source language in clearer language.
- Combine multiple source statements when the combination adds no new fact.
- Explain a concept using several source-supported statements together.
- Group scattered information about the same concept.
- Organize information into a logical learning sequence.
- Remove genuine repetition.
- Highlight an explicitly stated important point.
- Organize related concepts together when useful, but DO NOT create a
  new relationship, comparison, cause-effect link, implication, or
  interpretation unless the source explicitly supports that connection.
- If concepts merely appear related, present them separately rather than
  inventing a connection.
- Never label an inference as source-supported.
- Preserve and explain source-provided examples when their purpose is
  supported by the source.
- Turn source-described processes into clear step-by-step explanations.
- Preserve ONLY stages and transitions explicitly stated in the prepared
  SOURCE MATERIAL.
- Do not invent intermediate stages or mechanisms.
- Do not convert two adjacent facts into a causal or procedural sequence
  unless the prepared SOURCE MATERIAL explicitly describes that sequence.
- Do NOT insert intermediate steps, mechanisms, causes, effects, or
  transitions that are not explicitly described by the source.
- Use headings, bullets, tables, callouts, and concise paragraphs when they
  improve understanding.
- Give substantially more space to central knowledge than to incidental
  metadata.

========================
STRICT GROUNDING
========================

DO NOT use pretrained knowledge to fill gaps.

DO NOT add facts because they are:
- commonly known
- logically implied
- technically correct
- useful for understanding
- likely true
- associated with the topic

DO NOT invent:
- examples
- applications
- causes
- effects
- benefits
- limitations
- motivations
- consequences
- definitions
- relationships
- comparisons
- processes
- interpretations
- historical context
- technical explanations

unless the SOURCE MATERIAL supports them.

Do not make a claim stronger than the source makes it.

Do not convert an implication into a stated fact.

Do not remove uncertainty, conditions, exceptions, or qualifications.

========================
IMPORTANCE AND PRIORITY
========================

Internally classify information as:

CORE KNOWLEDGE
The central concepts, arguments, models, mechanisms, conclusions, and ideas
that the source is primarily about.

SUPPORTING KNOWLEDGE
Details that explain, qualify, connect, or provide evidence for core ideas.

EXAMPLES
Concrete examples explicitly provided by the source.

CONTEXT
Background information that helps organize the material.

ADMINISTRATIVE / BIBLIOGRAPHIC
ISBNs, publishers, addresses, catalogue information, library notices,
copyright details, and similar metadata.

Do NOT give administrative metadata the same weight as substantive knowledge.

========================
STUDY NOTE STRUCTURE
========================

# Study Notes

## Overview

Explain what the source is fundamentally about.
Focus on the actual subject matter rather than bibliographic metadata.

## Core Concepts

Identify and teach the most important concepts.

Do not force every concept into a rigid definition template.

For each major concept, use the source-supported information that actually
helps explain it. A concept may contain a definition, explanation, example,
evidence, or connection when those are supported by the source.

## How the Ideas Fit Together

Explain ONLY relationships, dependencies, contrasts, or connections that
are explicitly present in the SOURCE MATERIAL.

Do NOT create a new relationship merely because two concepts appear in the
same source or seem conceptually related.

IMPORTANT EVIDENCE BOUNDARY:
The prepared SOURCE MATERIAL is already an extracted knowledge
representation. Treat it as an evidence boundary.

A relationship, explanation, process step, cause, effect, implication,
comparison, interpretation, or connection may appear in the final notes
ONLY if that information is explicitly stated in the prepared SOURCE
MATERIAL.

Do not derive a new connection by reasoning across separate source items.

Do not infer that:
- one concept explains another
- one concept causes another
- one concept represents another
- one concept reflects another
- one concept extends another
- one concept responds to another
- two concepts are analogous
- two concepts are culturally related
- two concepts form a larger pattern

unless the prepared SOURCE MATERIAL explicitly states that relationship.

If the relationship is not explicitly present in the prepared SOURCE
MATERIAL, omit it.

Do NOT interpret one model through another model unless the prepared SOURCE
MATERIAL explicitly makes that connection.

Do NOT describe a concept as reflecting, analogous to, similar to,
complementary to, extending, reinforcing, re-framing, representing,
illustrating, responding to, resulting from, or contributing to another
concept unless the source explicitly states that relationship.

Do NOT use phrases such as:
- reflects
- mirrors
- analogous to
- represents
- illustrates
- responds to
- builds on
- extends
- reinforces
- re-frames
- cultural reinterpretation
- ongoing reinterpretation
unless the source explicitly makes that relationship.

If no explicit relationship is present, omit the connection rather than
creating one.

The goal is to help the reader understand the structure of the material,
not to invent a more coherent structure than the source provides.

## Detailed Explanation

Teach the central material in a logical progression.

Prefer coherent explanations over repetitive lists of definitions.

Combine related source information when doing so improves understanding
without adding factual content.

## Processes and Sequences

Include this section only when the source describes an actual process,
sequence, chain, or progression.

Preserve the source-supported order and meaning.

## Examples

Include useful examples explicitly provided by the source.

Explain what an example demonstrates only when that interpretation is
supported by the source.

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

Do not allow incidental metadata to overwhelm these details.

## Key Takeaways

Give concise, high-value takeaways covering the central ideas.

Avoid repeating the same information unnecessarily.

## Source Metadata

Include only useful bibliographic or administrative information.
Keep this section compact.

Omit any section that has no meaningful source-supported content.

========================
QUALITY STANDARD
========================

The final result should feel like notes prepared by an excellent teacher
who carefully studied this source.

The notes should be:

- clear
- explanatory
- well organized
- selective
- useful for learning
- useful for revision
- detailed where the source is detailed
- concise where the source is incidental
- completely faithful to the source

Do NOT optimize for maximum information density.

Optimize for understanding while remaining completely source-grounded.

========================
FINAL GROUNDING CHECK
========================

Before producing the answer, inspect every factual claim.

Ask:

"Can this claim be supported directly by the SOURCE MATERIAL?"

If explicitly stated → KEEP IT.
If directly restated → KEEP IT.
If multiple source statements combine without adding information → KEEP IT.
If merely implied → REMOVE IT.
If based on common knowledge → REMOVE IT.
If logically obvious but unstated → REMOVE IT.
If useful but unsupported → REMOVE IT.

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
        "Create a source-grounded Frequently Asked Questions document "
        "from the supplied source.\n\n"
        "STRICT SOURCE RULES:\n"
        "- Every question must be answerable from the source.\n"
        "- Every answer must contain only information supported by the source.\n"
        "- Do NOT add outside knowledge.\n"
        "- Do NOT invent examples, explanations, causes, effects, purposes, "
        "applications, relationships, or conclusions.\n"
        "- Do NOT infer information that is merely implied or logically obvious.\n"
        "- Prefer questions about definitions, explicit facts, processes, "
        "examples, and relationships actually stated in the source.\n\n"
        "Use Markdown. Format each item as:\n"
        "Q: <question>\n"
        "A: <answer>\n\n"
        f"Source:\n{transcript}"
    )

    return generate_text(
        Task.FAQ,
        prompt,
        system_instruction=(
            "Create a source-grounded FAQ. The supplied source is the "
            "only factual authority. Never add outside or inferred information."
        ),
    )


def generate_podcast_script(
    text: str,
    instruction: str = "",
    host_a: str = "Host A",
    host_b: str = "Host B",
) -> list:

    prompt = f"""
Create a two-person podcast script using ONLY the supplied source material.

The speakers may sound conversational, but every factual statement must
remain directly supported by the source.

STRICT SOURCE RULES:
- The source is the ONLY factual authority.
- Do NOT add outside knowledge or common knowledge.
- Do NOT invent examples, facts, explanations, causes, effects, purposes,
  applications, benefits, limitations, relationships, or conclusions.
- Do NOT add introductory context that is not in the source.
- Do NOT add opinions, commentary, evaluations, summaries of implications,
  or closing statements containing unsupported information.
- Do NOT infer information merely because it seems obvious or useful.
- Questions may only ask about information explicitly present in the source.
- Answers must only restate or directly quote information supported by source.
- Conversational wording must not introduce new meaning.
- Simple acknowledgements such as "Okay", "Right", or "I see" are allowed
  when they contain no factual claims.

IMPORTANT:
Do not make the podcast "engaging" by adding background knowledge,
opinions, examples, or contextual commentary. Engagement must come only
from the dialogue structure and natural wording.

"""

    if instruction:
        prompt += (
            f"PODCAST INSTRUCTION: {instruction}\n"
            "The instruction must not override any source-grounding rule.\n\n"
        )

    prompt += f"""
Return ONLY a valid JSON array of objects.
Each object must have exactly:
- 'speaker': either "{host_a}" or "{host_b}"
- 'text': the spoken line

Do NOT wrap the JSON in markdown code fences.

FINAL GROUNDING CHECK:
Before returning the JSON, inspect every spoken line.
Remove any factual claim, context, opinion, implication, or conclusion
that is not directly supported by the source.

Source Material:
{text}
"""

    response = generate_text(
        Task.PODCAST,
        prompt,
        system_instruction=(
            "Return valid JSON only. The source is the only factual authority. "
            "Every factual statement must be directly supported by the source. "
            "Never add outside knowledge, context, opinions, implications, "
            "or unsupported conclusions."
        ),
    )

    try:
        cleaned_response = clean_json_response(response)
        script = json.loads(cleaned_response)

        if not isinstance(script, list) or not script:
            raise ValueError("Expected a non-empty podcast script")

        valid_speakers = {host_a, host_b}

        for item in script:
            if (
                not isinstance(item, dict)
                or set(item.keys()) != {"speaker", "text"}
                or item["speaker"] not in valid_speakers
                or not isinstance(item["text"], str)
                or not item["text"].strip()
            ):
                raise ValueError("Invalid podcast structure")

        return script

    except Exception:
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
    evidence_context: str = "",
) -> list:

    prompt = f"""
You are roleplaying as two intelligent podcast hosts, '{host_a}' and '{host_b}'.

The user has just joined your live podcast and said:
"{user_message}"

Here is the recent context of the conversation:
{chat_history}

Here is the relevant evidence retrieved from the user's notebook:
{evidence_context}

IMPORTANT GROUNDING RULES:

- The notebook evidence is the factual authority for this conversation.
- Use the evidence to answer the user's question or respond to their comment.
- Do not use outside knowledge, assumptions, guesses, or unsupported facts.
- Do not invent details that are not supported by the evidence.
- If the evidence does not answer the user's question, say naturally that
  the notebook material does not provide enough information.
- Never mention retrieval, embeddings, reranking, chunks, vector search,
  context windows, or internal system details.
- Keep the conversation natural and podcast-like.
- The hosts may explain, clarify, connect, or briefly react to supported
  information, but every factual claim must remain grounded in the evidence.
- Do not simply read the evidence aloud. Discuss it naturally.

Generate a very short, continuous podcast response
(1 to 3 lines total) where the hosts reply directly to the user.

Return the response as a JSON array of objects, where each object has
'speaker' (either "{host_a}" or "{host_b}") and 'text'.

Do NOT wrap the output in markdown code blocks, just raw JSON.
"""

    response = generate_text(
        Task.PODCAST,
        prompt,
        system_instruction=(
            "You are a source-grounded live podcast host. "
            "Return only a valid JSON array. "
            "Every factual claim must be supported by the provided "
            "notebook evidence."
        ),
    )

    try:
        print("========== PODCAST RAW AI RESPONSE ==========")
        print(repr(response))
        print("========== END PODCAST RAW RESPONSE ==========")

        cleaned_response = clean_json_response(response)

        decoder = json.JSONDecoder()
        parsed_response, _ = decoder.raw_decode(cleaned_response.lstrip())

        if not isinstance(parsed_response, list) or not parsed_response:
            raise ValueError("Expected a non-empty podcast response")

        return parsed_response

    except (json.JSONDecodeError, ValueError):
        return [
            {
                "speaker": host_a,
                "text": "I think we hit a small technical glitch. Let?s try that again.",
            }
        ]


