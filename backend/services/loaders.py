from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from youtube_transcript_api import YouTubeTranscriptApi
import re

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

def extract_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return match.group(1) if match else None

def load_youtube(url):
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        
        full_text = []
        for t in transcript:
            # Format: [MM:SS] Text
            minutes = int(t.start // 60)
            seconds = int(t.start % 60)
            time_str = f"[{minutes:02d}:{seconds:02d}]"
            full_text.append(f"{time_str} {t.text}")
            
        final_text = "\n".join(full_text)
        
        doc = Document(page_content=final_text, metadata={"source": url, "type": "youtube"})
        return text_splitter.split_documents([doc])
    except Exception as e:
        print(f"Error loading YouTube: {e}")
        return []

def load_url(url):
    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        return text_splitter.split_documents(docs)
    except Exception as e:
        print(f"Error loading URL: {e}")
        return []

def load_pdf(file_path):
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        return text_splitter.split_documents(docs)
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return []

