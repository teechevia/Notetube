import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from database.db import (
    get_db,
    SourceModel,
    Notebook,
    ChatMessage,
    Artifact,
)

from database.vector_store import (
    add_documents_to_store,
    get_vector_store,
    rerank_documents,
    get_neighbor_chunks,
)

from services.loaders import (
    load_youtube,
    load_url,
    load_pdf,
)

from services.job_manager import (
    create_job,
    get_job,
)

import uuid
import os
import shutil


router = APIRouter()


class SourceCreate(BaseModel):
    url: str
    type: str  # youtube, url


# ============================================================
# SOURCE: URL / YOUTUBE
# ============================================================

@router.post("/notebooks/{notebook_id}/sources")
def add_source(
    notebook_id: int,
    source: SourceCreate,
    db: Session = Depends(get_db),
):
    if source.type == "youtube":
        docs = load_youtube(source.url)
        title = "YouTube Video"

    elif source.type == "url":
        docs = load_url(source.url)
        title = "Web Page"

    else:
        raise HTTPException(
            status_code=400,
            detail="Type not supported yet",
        )

    if not docs:
        raise HTTPException(
            status_code=400,
            detail="Failed to load content",
        )

    db_source = SourceModel(
        title=title,
        type=source.type,
        url=source.url,
        notebook_id=notebook_id,
    )

    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    for doc in docs:
        doc.metadata["source_id"] = db_source.id
        doc.metadata["notebook_id"] = notebook_id

    try:
        add_documents_to_store(docs)

    except Exception as exc:
        import traceback
        traceback.print_exc()

        db.delete(db_source)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to index source: {exc}",
        )

    return {
        "id": db_source.id,
        "title": db_source.title,
        "type": db_source.type,
        "url": db_source.url,
    }


# ============================================================
# SOURCE: FILE
# ============================================================

@router.post("/notebooks/{notebook_id}/sources/file")
async def add_source_file(
    notebook_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = (
        file.filename.split(".")[-1].lower()
        if "." in file.filename
        else ""
    )

    temp_file_path = f"temp_{uuid.uuid4().hex}.{ext}"

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == "pdf":
            docs = load_pdf(temp_file_path)

        elif ext in ["txt", "md"]:
            from services.loaders import load_txt
            docs = load_txt(temp_file_path)

        elif ext == "docx":
            from services.loaders import load_docx
            docs = load_docx(temp_file_path)

        elif ext == "pptx":
            from services.loaders import load_pptx
            docs = load_pptx(temp_file_path)

        elif ext in ["mp3", "wav"]:
            from services.loaders import load_audio
            docs = load_audio(temp_file_path)

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type",
            )

    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    if not docs:
        raise HTTPException(
            status_code=400,
            detail="Failed to load file content",
        )

    db_source = SourceModel(
        title=file.filename,
        type=ext,
        url="Local File",
        notebook_id=notebook_id,
    )

    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    for doc in docs:
        doc.metadata["source_id"] = db_source.id
        doc.metadata["notebook_id"] = notebook_id

    try:
        add_documents_to_store(docs)

    except Exception as exc:
        import traceback
        traceback.print_exc()

        db.delete(db_source)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to index file: {exc}",
        )

    return {
        "id": db_source.id,
        "title": db_source.title,
        "type": db_source.type,
        "url": db_source.url,
    }


# ============================================================
# GET SOURCES
# ============================================================

@router.get("/notebooks/{notebook_id}/sources")
def get_sources(
    notebook_id: int,
    db: Session = Depends(get_db),
):
    sources = (
        db.query(SourceModel)
        .filter(SourceModel.notebook_id == notebook_id)
        .all()
    )

    return sources


# ============================================================
# DELETE SOURCE
# ============================================================

@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
def delete_source(
    notebook_id: int,
    source_id: int,
    db: Session = Depends(get_db),
):
    db_source = (
        db.query(SourceModel)
        .filter(
            SourceModel.id == source_id,
            SourceModel.notebook_id == notebook_id,
        )
        .first()
    )

    if not db_source:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    from database.vector_store import delete_source_from_store

    try:
        delete_source_from_store(source_id)

    except Exception as exc:
        print(
            f"Error deleting from Chroma: {exc}"
        )

    db.delete(db_source)
    db.commit()

    return {
        "message": "Source deleted"
    }


# ============================================================
# CHAT
# ============================================================

class ChatRequest(BaseModel):
    query: str
    source_ids: list[int] = Field(default_factory=list)


def build_source_filter(
    notebook_id: int,
    source_ids: list[int],
):
    """
    Build Chroma-compatible metadata filters.

    Chroma requires multiple metadata conditions to be
    combined using $and.
    """

    if not source_ids:
        return {
            "notebook_id": notebook_id
        }

    if len(source_ids) == 1:
        return {
            "$and": [
                {"notebook_id": notebook_id},
                {"source_id": source_ids[0]},
            ]
        }

    return {
        "$and": [
            {"notebook_id": notebook_id},
            {
                "source_id": {
                    "$in": source_ids
                }
            },
        ]
    }


# ============================================================
# RAG 2.5 — EVIDENCE-ISOLATED CHAT
# ============================================================

def decompose_query(query: str) -> list[str]:
    """
    Split a user message into independent questions.

    Keeps simple questions as-is and separates common
    multi-question patterns.
    """

    import re

    query = query.strip()

    if not query:
        return []

    # Split on question marks while preserving natural wording.
    parts = re.split(r"(?<=\?)\s+", query)

    questions = [
        part.strip()
        for part in parts
        if part.strip()
    ]

    # If the message is already a single question,
    # keep it unchanged.
    if len(questions) <= 1:
        return [query]

    return questions


@router.post("/notebooks/{notebook_id}/chat")
def chat_with_sources(
    notebook_id: int,
    req: ChatRequest,
):
    """
    RAG 2.5 — Multi-question, structure-aware retrieval.

    Pipeline:

        1. Decompose multi-question user query
        2. Retrieve independently for each question
        3. CrossEncoder initial reranking
        4. Neighbor chunk expansion
        5. CrossEncoder final reranking
        6. Combine evidence
        7. Generate one grounded answer
    """

    from services.ai_router import generate_text
    from services.ai_config import Task

    rag_start = time.perf_counter()

    vector_store = get_vector_store()

    questions = decompose_query(req.query)

    if not questions:
        return {
            "answer": "Please ask a question about your uploaded sources."
        }

    filter_dict = build_source_filter(
        notebook_id,
        req.source_ids,
    )

    all_evidence = []

    print("\n========== RAG 2.5 DEBUG ==========")
    print("ORIGINAL QUERY:", req.query)
    print("DECOMPOSED QUESTIONS:", questions)

    for question_index, question in enumerate(
        questions,
        start=1,
    ):
        # ----------------------------------------------------
        # RETRIEVAL TIMING
        # ----------------------------------------------------

        retrieval_start = time.perf_counter()

        candidates = vector_store.similarity_search(
            question,
            k=50,
            filter=filter_dict,
        )

        retrieval_time = (
            time.perf_counter() - retrieval_start
        )

        if not candidates:
            print(
                f"QUESTION {question_index}: "
                f"no candidates"
            )
            print(
                f"TIMING — retrieval: "
                f"{retrieval_time:.3f}s"
            )
            continue

        # ----------------------------------------------------
        # INITIAL RERANK TIMING
        # ----------------------------------------------------

        initial_rerank_start = time.perf_counter()

        initial_results = rerank_documents(
            query=question,
            documents=candidates,
            top_k=6,
        )

        initial_rerank_time = (
            time.perf_counter() -
            initial_rerank_start
        )

        if not initial_results:
            print(
                f"QUESTION {question_index}: "
                f"initial reranking failed"
            )
            continue

        # ----------------------------------------------------
        # NEIGHBOR EXPANSION TIMING
        # ----------------------------------------------------

        expansion_start = time.perf_counter()

        expanded_documents = get_neighbor_chunks(
            documents=initial_results,
            window=2,
        )

        expansion_time = (
            time.perf_counter() -
            expansion_start
        )

        all_documents = (
            initial_results +
            expanded_documents
        )

        unique_documents = []
        seen_chunks = set()

        for doc in all_documents:
            key = (
                doc.metadata.get("source_id"),
                doc.metadata.get("chunk_index"),
            )

            if key in seen_chunks:
                continue

            seen_chunks.add(key)
            unique_documents.append(doc)

        # ----------------------------------------------------
        # FINAL RERANK TIMING
        # ----------------------------------------------------

        final_rerank_start = time.perf_counter()

        final_results = rerank_documents(
            query=question,
            documents=unique_documents,
            top_k=8,
        )

        final_rerank_time = (
            time.perf_counter() -
            final_rerank_start
        )

        # ----------------------------------------------------
        # DEBUG
        # ----------------------------------------------------

        print(
            f"\n--- QUESTION {question_index} ---"
        )
        print("QUERY:", question)
        print("CANDIDATES:", len(candidates))
        print("INITIAL RERANKED:", len(initial_results))
        print("EXPANDED:", len(expanded_documents))
        print("UNIQUE:", len(unique_documents))
        print("FINAL RERANKED:", len(final_results))
        print(
            "SELECTED CHUNKS:",
            [
                doc.metadata.get("chunk_index")
                for doc in final_results
            ],
        )

        print(
            "TIMING — retrieval: "
            f"{retrieval_time:.3f}s | "
            "initial rerank: "
            f"{initial_rerank_time:.3f}s | "
            "expansion: "
            f"{expansion_time:.3f}s | "
            "final rerank: "
            f"{final_rerank_time:.3f}s"
        )

        for doc in final_results:
            all_evidence.append(
                {
                    "question_index": question_index,
                    "question": question,
                    "document": doc,
                }
            )

    if not all_evidence:
        print(
            "TIMING — TOTAL: "
            f"{time.perf_counter() - rag_start:.3f}s"
        )

        return {
            "answer": (
                "I couldn't find enough relevant "
                "information in the uploaded sources."
            )
        }

    # --------------------------------------------------------
    # RAG 2.5 — Organize evidence by question.
    #
    # Each question keeps its own evidence pool so the final
    # model does not accidentally use evidence retrieved for
    # another question.
    # --------------------------------------------------------

    evidence_by_question = {}

    for item in all_evidence:
        question_index = item["question_index"]

        if question_index not in evidence_by_question:
            evidence_by_question[question_index] = []

        evidence_by_question[question_index].append(item)

    # --------------------------------------------------------
    # Deduplicate chunks within each question.
    # --------------------------------------------------------

    for question_index, items in evidence_by_question.items():

        unique_items = []
        seen_chunks = set()

        for item in items:
            doc = item["document"]

            key = (
                doc.metadata.get("source_id"),
                doc.metadata.get("chunk_index"),
            )

            if key in seen_chunks:
                continue

            seen_chunks.add(key)
            unique_items.append(item)

        evidence_by_question[question_index] = unique_items

    # --------------------------------------------------------
    # Build isolated, question-labelled context.
    # --------------------------------------------------------

    context_parts = []
    total_unique_evidence = 0

    for question_index in sorted(evidence_by_question):

        items = evidence_by_question[question_index]

        if not items:
            continue

        question = items[0]["question"]

        context_parts.append(
            f"========== QUESTION {question_index} ==========\n"
            f"Question: {question}\n"
        )

        for evidence_index, item in enumerate(
            items,
            start=1,
        ):
            doc = item["document"]

            source_id = doc.metadata.get(
                "source_id"
            )

            chunk_index = doc.metadata.get(
                "chunk_index"
            )

            metadata_label = (
                f"[Evidence {evidence_index} | "
                f"Source ID: {source_id} | "
                f"Chunk: {chunk_index}]"
            )

            context_parts.append(
                f"{metadata_label}\n"
                f"{doc.page_content}\n"
            )

            total_unique_evidence += 1

        context_parts.append(
            f"========== END QUESTION {question_index} ==========\n"
        )

    context = "\n".join(context_parts)

    print(
        "\nTOTAL UNIQUE EVIDENCE:",
        total_unique_evidence,
    )

    print(
        "EVIDENCE BY QUESTION:",
        {
            question_index: len(items)
            for question_index, items
            in evidence_by_question.items()
        },
    )

    print(
        "====================================\n"
    )

    # --------------------------------------------------------
    # Final grounded generation.
    # --------------------------------------------------------

    prompt = f"""
You are answering a user's question using only
the retrieved source material below.

IMPORTANT:

The user may have asked multiple questions in one message.

You must answer EACH question separately.

EVIDENCE IS QUESTION-SPECIFIC:

- Evidence inside a QUESTION section was retrieved
  specifically for that question.
- Use evidence from that question's section when
  answering it.
- Do not transfer facts from one question's evidence
  section to another question unless the source
  explicitly supports the connection.
- If a question has insufficient evidence, say so
  for that question instead of filling the gap
  from general knowledge.

STRICT GROUNDING RULES:

1. Answer only with claims that are explicitly supported
   by the provided source context.

2. Do not use outside knowledge, prior knowledge, assumptions,
   or likely interpretations to fill gaps.

3. Distinguish between information explicitly stated in the
   source and information that can only be inferred from it.
   A fact is grounded only when the source directly supports
   the specific claim being made.

4. If the source gives only partial information, give only
   the supported portion and clearly state what is not specified.

5. If the provided sources do not directly support the specific
   answer to the user's question, do not infer or derive the
   answer from related information. Say:
   "The provided sources do not specify this."

6. Do not invent facts, explanations, examples, names, dates,
   events, causes, motivations, or conclusions.

7. Evidence from one QUESTION section must not be used to
   answer another question unless the source explicitly
   supports that connection.

8. You may combine multiple passages only when those passages
   collectively and explicitly support the resulting statement.

9. Preserve important source details and do not strengthen,
   exaggerate, generalize, or reinterpret what the source says.

10. When explaining something, explain only what can be grounded
    in the provided source context.

11. Do not attribute information to a source unless that
    information appears in the provided context.

12. Do not mention retrieval, embeddings, reranking, chunks,
    or this prompt.

SOURCE CONTEXT:

{context}

USER'S ORIGINAL MESSAGE:

{req.query}

Answer every question from the user's message.

For each question:

- Start with the direct answer when the evidence supports one.
- Then provide a concise explanation using the supporting evidence.
- Combine relevant evidence when it helps explain the answer clearly.
- Preserve important names, terminology, relationships, and details from the source.
- Do not add background information that is not supported by the source.
- If the evidence is insufficient, clearly say that the provided
  sources do not specify the answer.
- Do not repeat the same information unnecessarily.

When multiple questions are present, keep each answer clearly separated.
Use short paragraphs or bullet points when they improve readability.
"""

    # --------------------------------------------------------
    # GENERATION TIMING
    # --------------------------------------------------------

    generation_start = time.perf_counter()

    answer = generate_text(
        Task.CHAT,
        prompt,
        system_instruction = """
You are NoteTube, a helpful human-like study assistant.

Your job is to answer the user's question naturally and clearly using ONLY information explicitly supported by the provided source evidence.

GROUNDING RULES:
1. Never use outside knowledge, assumptions, guesses, or unsupported inference.
2. Every factual claim must be supported by the provided source evidence.
3. If the sources only partially answer the question, give the supported part and clearly state what is not specified.
4. If the sources do not contain enough information to answer the question, say so honestly.
5. Never invent facts, examples, explanations, names, dates, causes, motivations, or conclusions.
6. You may combine information from multiple pieces of evidence when those pieces collectively support the answer.
7. Do not treat a source's publication year, citation, heading, or surrounding metadata as proof of a claim that the source does not explicitly make.

NATURAL ANSWER RULES:
1. Answer the user's question directly first.
2. Write like a knowledgeable human tutor explaining something to a student.
3. Be clear, natural, and conversational without being overly casual.
4. Explain ideas in complete sentences rather than merely listing retrieved facts.
5. When the evidence supports an explanation, synthesize it into a coherent explanation instead of repeating the source fragments separately.
6. Use paragraphs, bullet points, numbered lists, or headings only when they genuinely improve readability.
7. Do NOT expose internal retrieval details such as:
   - chunk IDs
   - source IDs
   - retrieval scores
   - evidence IDs
   - question IDs
   - reranking
   - embeddings
   - vector search
   - context windows
   - internal metadata
8. Do not talk about "retrieved chunks", "the context", "the RAG pipeline", or how you found the answer.
9. Do not sound like a debugging tool, API response, database query, or research log.
10. Do not unnecessarily say "According to the provided sources" or "The provided sources state". Simply answer naturally when the evidence supports it.
11. If something is genuinely missing from the sources, explain that naturally. For example:
   "The material identifies the Othering Model but does not provide its definition, so I can't explain the model itself from this source alone."
12. Preserve important details from the source without copying irrelevant metadata.
13. Never sacrifice factual accuracy for a more complete-sounding answer.

SOURCE ATTRIBUTION:
- Mention a source, author, page, section, or publication when it is useful to the user's understanding.
- Do not expose internal source IDs or chunk numbers.
- If page numbers are available and relevant, you may say "page 60".
- If an author or work is explicitly identified in the evidence, you may naturally mention it.

IMPORTANT:
The user wants an answer, not a report about the retrieval process.
Think through the evidence internally, then give only the final human-readable answer.
"""
    )

    generation_time = (
        time.perf_counter() -
        generation_start
    )

    total_time = (
        time.perf_counter() -
        rag_start
    )

    print(
        f"TIMING — generation: "
        f"{generation_time:.3f}s | "
        f"TOTAL: "
        f"{total_time:.3f}s"
    )

    return {
        "answer": answer
    }


# ============================================================
# STUDIO
# ============================================================

class StudioRequest(BaseModel):
    format: str
    instruction: str | None = None
    host_a_name: str | None = "Host A"
    host_b_name: str | None = "Host B"
    source_ids: list[int] = Field(default_factory=list)


def collect_studio_source_text(
    notebook_id: int,
    source_ids: list[int],
):
    vector_store = get_vector_store()
    collection = vector_store._collection

    where_filter = build_source_filter(
        notebook_id,
        source_ids,
    )

    results = collection.get(
        where=where_filter
    )

    if not results or not results.get("documents"):
        raise ValueError(
            "No sources available to generate from."
        )

    return "\n\n".join(
        results["documents"]
    )


# ============================================================
# HUMAN NOTES JOB
# ============================================================

def run_human_notes_job(
    job_id: int,
    notebook_id: int,
    source_ids: list[int],
):
    """
    Background worker for human-quality note generation.
    """

    from services.generators import generate_human_notes

    db = None

    try:
        full_text = collect_studio_source_text(
            notebook_id,
            source_ids,
        )

        notes = generate_human_notes(
            full_text,
            job_id=job_id,
        )

        from database.db import SessionLocal

        db = SessionLocal()

        artifact = Artifact(
            notebook_id=notebook_id,
            type="human_notes",
            title="Study Notes",
            content=notes,
        )

        db.add(artifact)
        db.commit()
        db.refresh(artifact)

        print(
            f"Human notes job {job_id} completed. "
            f"Artifact {artifact.id} created."
        )

    except Exception as exc:
        print(
            f"Human notes job {job_id} failed: {exc}"
        )

        from services.job_manager import fail_job

        fail_job(
            job_id,
            str(exc),
        )

    finally:
        if db:
            db.close()


# ============================================================
# STUDIO GENERATION
# ============================================================

@router.post(
    "/notebooks/{notebook_id}/studio/generate"
)
def generate_studio_content(
    notebook_id: int,
    req: StudioRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # HUMAN NOTES = BACKGROUND JOB
    # --------------------------------------------------------

    if req.format == "human_notes":
        try:
            collect_studio_source_text(
                notebook_id,
                req.source_ids,
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            )

        job_id = create_job(
            notebook_id=notebook_id,
            source_id=(
                req.source_ids[0]
                if len(req.source_ids) == 1
                else None
            ),
            job_type="human_notes",
            total_units=1,
        )

        background_tasks.add_task(
            run_human_notes_job,
            job_id,
            notebook_id,
            req.source_ids,
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "message": "Human notes generation started.",
        }

    # --------------------------------------------------------
    # SYNCHRONOUS STUDIO GENERATION
    # --------------------------------------------------------

    try:
        full_text = collect_studio_source_text(
            notebook_id,
            req.source_ids,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    from services.generators import (
        generate_briefing_doc,
        generate_flashcards,
        generate_quiz,
        generate_faq,
        generate_podcast_script,
    )

    if req.format == "briefing":
        return {
            "content": generate_briefing_doc(
                full_text
            )
        }

    elif req.format == "flashcards":
        return {
            "content": generate_flashcards(
                full_text
            )
        }

    elif req.format == "quiz":
        return {
            "content": generate_quiz(
                full_text
            )
        }

    elif req.format == "faq":
        return {
            "content": generate_faq(
                full_text
            )
        }

    elif req.format == "podcast":
        script = generate_podcast_script(
            full_text,
            instruction=req.instruction or "",
            host_a=req.host_a_name or "Host A",
            host_b=req.host_b_name or "Host B",
        )

        return {
            "content": script
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Unknown format",
        )


# ============================================================
# JOB STATUS
# ============================================================

@router.get("/jobs/{job_id}")
def get_processing_job(
    job_id: int,
):
    job = get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


# ============================================================
# PODCAST AUDIO
# ============================================================

@router.post("/studio/podcast/audio")
async def generate_podcast_audio(
    req: dict,
):
    script = req.get("script", [])

    voice_a = req.get(
        "voice_a",
        "en-US-ChristopherNeural",
    )

    voice_b = req.get(
        "voice_b",
        "en-US-JennyNeural",
    )

    host_a = req.get(
        "host_a_name",
        "Host A",
    )

    host_b = req.get(
        "host_b_name",
        "Host B",
    )

    if not script:
        raise HTTPException(
            status_code=400,
            detail="Script is required",
        )

    import edge_tts
    import tempfile

    from fastapi.responses import FileResponse

    combined_audio_path = os.path.join(
        tempfile.gettempdir(),
        f"podcast_{uuid.uuid4().hex}.mp3",
    )

    with open(
        combined_audio_path,
        "wb",
    ) as combined_file:

        for line in script:
            speaker = line.get("speaker")
            text = line.get("text")

            voice = (
                voice_a
                if speaker == host_a
                else voice_b
            )

            communicate = edge_tts.Communicate(
                text,
                voice,
            )

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    combined_file.write(
                        chunk["data"]
                    )

    return FileResponse(
        combined_audio_path,
        media_type="audio/mpeg",
        filename="podcast.mp3",
    )


# ============================================================
# INTERACTIVE PODCAST
# ============================================================

class PodcastInteractRequest(BaseModel):
    message: str
    chat_history: str
    host_a_name: str = "Host A"
    host_b_name: str = "Host B"
    voice_a: str = "en-US-ChristopherNeural"
    voice_b: str = "en-US-JennyNeural"


@router.post("/studio/podcast/interact")
async def interact_podcast(
    req: PodcastInteractRequest,
    db: Session = Depends(get_db),
):
    from services.generators import (
        generate_interactive_podcast_response
    )

    script = generate_interactive_podcast_response(
        req.message,
        req.chat_history,
        req.host_a_name,
        req.host_b_name,
    )

    return {
        "content": script
    }


# ============================================================
# CHAT HISTORY
# ============================================================

class ChatHistoryRequest(BaseModel):
    messages: list[dict]


@router.get(
    "/notebooks/{notebook_id}/chat_history"
)
def get_chat_history(
    notebook_id: int,
    db: Session = Depends(get_db),
):
    msgs = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.notebook_id == notebook_id
        )
        .order_by(ChatMessage.id.asc())
        .all()
    )

    return [
        {
            "role": m.role,
            "text": m.text,
            "audioUrl": m.audio_url,
        }
        for m in msgs
    ]


@router.post(
    "/notebooks/{notebook_id}/chat_history"
)
def save_chat_history(
    notebook_id: int,
    req: ChatHistoryRequest,
    db: Session = Depends(get_db),
):
    (
        db.query(ChatMessage)
        .filter(
            ChatMessage.notebook_id == notebook_id
        )
        .delete()
    )

    for m in req.messages:
        msg = ChatMessage(
            notebook_id=notebook_id,
            role=m.get("role"),
            text=m.get("text"),
            audio_url=m.get("audioUrl"),
        )

        db.add(msg)

    db.commit()

    return {
        "status": "ok"
    }