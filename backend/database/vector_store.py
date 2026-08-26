import chromadb
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import GEMINI_API_KEY
import os

# Initialize Gemini Embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2", google_api_key=GEMINI_API_KEY)

# Initialize ChromaDB Local Client
persist_directory = "./chroma_db"
os.makedirs(persist_directory, exist_ok=True)

# Using langchain Chroma wrapper
def get_vector_store():
    return Chroma(
        collection_name="notetube_sources",
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

def add_documents_to_store(docs):
    vector_store = get_vector_store()
    vector_store.add_documents(docs)
    vector_store.persist()

def delete_source_from_store(source_id: int):
    vector_store = get_vector_store()
    vector_store._collection.delete(where={"source_id": source_id})
    vector_store.persist()



def delete_notebook_from_store(notebook_id: int):
    try:
        vector_store = get_vector_store()
        vector_store._collection.delete(where={"notebook_id": notebook_id})
        vector_store.persist()
    except Exception as e:
        print(f"Error deleting chroma notebook: {e}")
