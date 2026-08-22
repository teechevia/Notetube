from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db, SourceModel
from database.vector_store import add_documents_to_store, get_vector_store
from services.loaders import load_youtube, load_url
from pydantic import BaseModel
import uuid

router = APIRouter()

class SourceCreate(BaseModel):
    url: str
    type: str # youtube, url

@router.post("/sources")
def add_source(source: SourceCreate, db: Session = Depends(get_db)):
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

    # Save to SQLite
    db_source = SourceModel(title=title, type=source.type, url=source.url)
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    # Add to ChromaDB
    # Add metadata to docs so we know which source they belong to
    for doc in docs:
        doc.metadata["source_id"] = db_source.id
    
    add_documents_to_store(docs)

    return {"id": db_source.id, "title": db_source.title, "type": db_source.type, "url": db_source.url}

@router.get("/sources")
def get_sources(db: Session = Depends(get_db)):
    sources = db.query(SourceModel).all()
    return sources

@router.delete("/sources/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    # Remove from SQLite
    db_source = db.query(SourceModel).filter(SourceModel.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    db.delete(db_source)
    db.commit()
    
    # Remove from ChromaDB
    from database.vector_store import delete_source_from_store
    try:
        delete_source_from_store(source_id)
    except Exception as e:
        print(f"Error deleting from Chroma: {e}")
        
    return {"message": "Source deleted"}

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
def chat_with_sources(req: ChatRequest):
    vector_store = get_vector_store()
    
    # 1. Retrieve relevant documents
    results = vector_store.similarity_search(req.query, k=5)
    
    if not results:
        return {"answer": "I don't have any sources uploaded yet, or I couldn't find any relevant information."}
        
    # 2. Construct prompt
    context = "\n\n".join([doc.page_content for doc in results])
    prompt = f"Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know.\n\nContext:\n{context}\n\nQuestion: {req.query}\nAnswer:"
    
    # 3. Generate response with Gemini
    from services.ai import ask_ai
    answer = ask_ai(prompt, system_instruction="You are a helpful study assistant talking to the user about their uploaded documents.")
    
    return {"answer": answer}

