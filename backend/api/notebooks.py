from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db, Notebook, User
from database.vector_store import delete_notebook_from_store
from pydantic import BaseModel

router = APIRouter()

class NotebookCreate(BaseModel):
    title: str
    description: str = ""

@router.post("/notebooks")
def create_notebook(notebook: NotebookCreate, db: Session = Depends(get_db)):
    # For now, hardcode user 1 until auth is built
    user = db.query(User).first()
    if not user:
        user = User(email="test@example.com")
        db.add(user)
        db.commit()
        db.refresh(user)

    db_notebook = Notebook(title=notebook.title, description=notebook.description, user_id=user.id)
    db.add(db_notebook)
    db.commit()
    db.refresh(db_notebook)
    return db_notebook

@router.get("/notebooks")
def list_notebooks(db: Session = Depends(get_db)):
    return db.query(Notebook).all()

@router.delete("/notebooks/{notebook_id}")
def delete_notebook(notebook_id: int, db: Session = Depends(get_db)):
    notebook = db.query(Notebook).filter(Notebook.id == notebook_id).first()
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")

    db.delete(notebook)
    db.commit()
    delete_notebook_from_store(notebook_id)
    return {"message": "Notebook deleted"}
