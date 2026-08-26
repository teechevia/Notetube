# ARCHITECTURE AUDIT: NoteTube

## 1. Current Architecture
NoteTube currently operates as a Minimum Viable Product (MVP) single-workspace application.
- **Frontend:** React 18, Vite, Tailwind CSS, Axios. Operates as a single large App.jsx component representing the entire workspace.
- **Backend:** FastAPI, Uvicorn, SQLite (SQLAlchemy), ChromaDB (via Langchain), Google GenAI SDK (gemini-2.5-flash).
- **Data Model:** A single SourceModel table storing id, title, type, and url. No concept of distinct users or notebooks.
- **Vector Storage:** ChromaDB persisted to ./chroma_db.
- **Audio:** edge-tts used for generating audio streams synchronously.

## 2. Current Features (Working)
- YouTube URL and PDF local file ingestion.
- RAG-based chat using Gemini.
- Markdown rendering in chat.
- Studio Artifact Generation (FAQ, Briefing Doc, Study Guide, Timeline, Table of Contents).
- Deep Dive Podcast generation (Text-to-Speech via edge-tts with two voices).
- Live Podcast Interactive Mode (generating real-time host responses).
- Light/Dark mode (NotebookLM exact hex codes).
- "New Workspace" feature (which dangerously wipes the entire database).

## 3. Missing Features (From NotebookLM Target)
- Multi-notebook architecture.
- Authentication / User accounts.
- Source chunk citation tracking.
- Hybrid retrieval (BM25 + Vector).
- Video Overviews, Slide Decks, Infographics, Mind Maps.
- Note-taking system.
- Background task queues (Celery/RQ) for long-running generation.
- Audio player state persistence across navigation.

## 4. Technical Debt & Issues
- App.jsx is extremely monolithic (over 700 lines). Needs to be broken down into modular components.
- Synchronous processing for YouTube/PDF parsing and Audio Generation blocks the server.
- Error handling is basic; UI relies on a generic alert or single text string for most failures.

## 5. Recommended Migrations
1. **Database:** Migrate SQLite to support User, Notebook, Source, Artifact, Message.
2. **Frontend:** Refactor App.jsx into modular directories.
3. **Backend Services:** Move generation logic into background tasks.
4. **Vector DB:** Add metadata filtering by notebook_id to ensure data isolation.

## 6. Implementation Priority
Phase 1: Foundation (Multi-notebook Data Model, API abstractions).
Phase 2: Component Refactor (Break down App.jsx).
Phase 3: Asynchronous Job System.
Phase 4: Advanced Studio (Video, Slides, Infographics).
