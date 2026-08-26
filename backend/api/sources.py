from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database.db import get_db, SourceModel, Notebook, ChatMessage
from database.vector_store import add_documents_to_store, get_vector_store
from services.loaders import load_youtube, load_url, load_pdf
from pydantic import BaseModel
import uuid
import os
import shutil

router = APIRouter()

class SourceCreate(BaseModel):
    url: str
    type: str # youtube, url

@router.post("/notebooks/{notebook_id}/sources")
def add_source(notebook_id: int, source: SourceCreate, db: Session = Depends(get_db)):
    if source.type == "youtube":
        docs = load_youtube(source.url)
        title = "YouTube Video"
    elif source.type == "url":
        docs = load_url(source.url)
        title = "Web Page"
    else:
        raise HTTPException(status_code=400, detail="Type not supported yet")

    if not docs:
        raise HTTPException(status_code=400, detail="Failed to load content")

    db_source = SourceModel(title=title, type=source.type, url=source.url, notebook_id=notebook_id)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    for doc in docs:
        doc.metadata["source_id"] = db_source.id
        doc.metadata["notebook_id"] = notebook_id
    add_documents_to_store(docs)
    return {"id": db_source.id, "title": db_source.title, "type": db_source.type, "url": db_source.url}

@router.post("/notebooks/{notebook_id}/sources/file")
async def add_source_file(notebook_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    temp_file_path = f"temp_{uuid.uuid4().hex}.{ext}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == 'pdf':
            docs = load_pdf(temp_file_path)
        elif ext in ['txt', 'md']:
            from services.loaders import load_txt
            docs = load_txt(temp_file_path)
        elif ext == 'docx':
            from services.loaders import load_docx
            docs = load_docx(temp_file_path)
        elif ext == 'pptx':
            from services.loaders import load_pptx
            docs = load_pptx(temp_file_path)
        elif ext in ['mp3', 'wav']:
            from services.loaders import load_audio
            docs = load_audio(temp_file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    if not docs:
        raise HTTPException(status_code=400, detail="Failed to load file content")

    db_source = SourceModel(title=file.filename, type=ext, url="Local File", notebook_id=notebook_id)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    for doc in docs:
        doc.metadata["source_id"] = db_source.id
        doc.metadata["notebook_id"] = notebook_id

    add_documents_to_store(docs)
    return {"id": db_source.id, "title": db_source.title, "type": db_source.type, "url": db_source.url}

@router.get("/notebooks/{notebook_id}/sources")
def get_sources(notebook_id: int, db: Session = Depends(get_db)):
    sources = db.query(SourceModel).filter(SourceModel.notebook_id == notebook_id).all()
    return sources

@router.delete("/notebooks/{notebook_id}/sources/{source_id}")
def delete_source(notebook_id: int, source_id: int, db: Session = Depends(get_db)):
    db_source = db.query(SourceModel).filter(SourceModel.id == source_id, SourceModel.notebook_id == notebook_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(db_source)
    db.commit()

    from database.vector_store import delete_source_from_store
    try:
        delete_source_from_store(source_id)
    except Exception as e:
        print(f"Error deleting from Chroma: {e}")

    return {"message": "Source deleted"}

class ChatRequest(BaseModel):
    query: str
    source_ids: list[int] = []

@router.post("/notebooks/{notebook_id}/chat")
def chat_with_sources(notebook_id: int, req: ChatRequest):
    vector_store = get_vector_store()

    # Simple workaround for chroma filtering (Chroma doesn't natively support easy IN queries through langchain wrapper in some versions, but we can filter after or use simple dict if 1 source)
    # Actually, langchain chromadb supports $in operator for lists!
    filter_dict = {"notebook_id": notebook_id}
    if req.source_ids:
        if len(req.source_ids) == 1:
            filter_dict["source_id"] = req.source_ids[0]
        else:
            filter_dict["source_id"] = {"$in": req.source_ids}

    results = vector_store.similarity_search(req.query, k=5, filter=filter_dict)

    if not results:
        return {"answer": "I don't have any sources uploaded yet, or I couldn't find any relevant information."}

    context = "\n\n".join([doc.page_content for doc in results])
    prompt = f"Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.\n\nContext:\n{context}\n\nQuestion: {req.query}\nAnswer:"

    from services.ai import ask_ai
    answer = ask_ai(prompt, system_instruction="You are a helpful study assistant talking to the user about their uploaded documents.")

    return {"answer": answer}

class StudioRequest(BaseModel):
    format: str # briefing, flashcards, quiz, faq, podcast
    instruction: str | None = None
    host_a_name: str | None = "Host A"
    host_b_name: str | None = "Host B"

@router.post("/notebooks/{notebook_id}/studio/generate")
def generate_studio_content(notebook_id: int, req: StudioRequest, db: Session = Depends(get_db)):
    vector_store = get_vector_store()

    collection = vector_store._collection
    results = collection.get(where={"notebook_id": notebook_id})

    if not results or not results["documents"]:
        raise HTTPException(status_code=400, detail="No sources available to generate from.")

    full_text = "\n\n".join(results["documents"])

    from services.generators import generate_briefing_doc, generate_flashcards, generate_quiz, generate_faq, generate_podcast_script, generate_human_notes

    if req.format == "briefing":
        return {"content": generate_briefing_doc(full_text)}
    elif req.format == "human_notes":
        return {"content": generate_human_notes(full_text)}
    elif req.format == "flashcards":
        return {"content": generate_flashcards(full_text)}
    elif req.format == "quiz":
        return {"content": generate_quiz(full_text)}
    elif req.format == "faq":
        return {"content": generate_faq(full_text)}
    elif req.format == "podcast":
        script = generate_podcast_script(
            full_text,
            instruction=req.instruction or "",
            host_a=req.host_a_name or "Host A",
            host_b=req.host_b_name or "Host B"
        )
        return {"content": script}
    else:
        raise HTTPException(status_code=400, detail="Unknown format")

@router.post("/studio/podcast/audio")
async def generate_podcast_audio(req: dict):
    script = req.get("script", [])
    voice_a = req.get("voice_a", "en-US-ChristopherNeural")
    voice_b = req.get("voice_b", "en-US-JennyNeural")
    host_a = req.get("host_a_name", "Host A")
    host_b = req.get("host_b_name", "Host B")

    if not script:
        raise HTTPException(status_code=400, detail="Script is required")

    import edge_tts
    import tempfile
    import os
    from fastapi.responses import FileResponse

    combined_audio_path = os.path.join(tempfile.gettempdir(), f"podcast_{uuid.uuid4().hex}.mp3")

    with open(combined_audio_path, "wb") as combined_file:
        for line in script:
            speaker = line.get("speaker")
            text = line.get("text")
            voice = voice_a if speaker == host_a else voice_b

            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    combined_file.write(chunk["data"])

    return FileResponse(combined_audio_path, media_type="audio/mpeg", filename="podcast.mp3")

class PodcastInteractRequest(BaseModel):
    message: str
    chat_history: str
    host_a_name: str = "Host A"
    host_b_name: str = "Host B"
    voice_a: str = "en-US-ChristopherNeural"
    voice_b: str = "en-US-JennyNeural"

@router.post("/studio/podcast/interact")
async def interact_podcast(req: PodcastInteractRequest, db: Session = Depends(get_db)):
    from services.generators import generate_interactive_podcast_response

    script = generate_interactive_podcast_response(
        req.message,
        req.chat_history,
        req.host_a_name,
        req.host_b_name
    )

    return {"content": script}


class ChatHistoryRequest(BaseModel):
    messages: list[dict]

@router.get("/notebooks/{notebook_id}/chat_history")
def get_chat_history(notebook_id: int, db: Session = Depends(get_db)):
    msgs = db.query(ChatMessage).filter(ChatMessage.notebook_id == notebook_id).order_by(ChatMessage.id.asc()).all()
    return [{"role": m.role, "text": m.text, "audioUrl": m.audio_url} for m in msgs]

@router.post("/notebooks/{notebook_id}/chat_history")
def save_chat_history(notebook_id: int, req: ChatHistoryRequest, db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.notebook_id == notebook_id).delete()
    for m in req.messages:
        msg = ChatMessage(notebook_id=notebook_id, role=m.get("role"), text=m.get("text"), audio_url=m.get("audioUrl"))
        db.add(msg)
    db.commit()
    return {"status": "ok"}
