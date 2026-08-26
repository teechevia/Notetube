# 🎧 NoteTube

> An AI-powered knowledge workspace inspired by NotebookLM — transform YouTube videos and documents into an interactive knowledge base, conversations, study materials, and AI-generated podcasts.

---

## 📌 Overview

NoteTube is an AI-powered knowledge workspace for understanding, exploring, and interacting with information from multiple sources.

You can add sources such as:

- 🎥 YouTube videos
- 📄 PDF documents
- 📝 TXT files
- 📝 Markdown files

NoteTube processes these sources for semantic retrieval and lets you interact with them through AI chat, source-specific analysis, study tools, and podcast generation.

The workspace is organized around three main areas:

- 📚 **Sources** — manage and select knowledge sources
- 💬 **Interactive Session** — ask questions and chat with your knowledge
- 🧠 **Studio** — generate study materials and podcasts

---

## ✨ Features

### 📚 Knowledge Base

Add and manage multiple sources inside a workspace.

Supported sources:

- YouTube videos
- PDF documents
- TXT files
- Markdown files

Sources can be:

- Added
- Deleted
- Selected individually
- Selected together
- Selected all at once
- Deselected at any time

Selecting a source does **not** duplicate it. Source selection is maintained as application state.

---

### 💬 Interactive AI Chat

Chat with your sources using Retrieval-Augmented Generation (RAG).

Examples:

    Summarize this document.

    What are the main ideas?

    Explain this topic simply.

    What are the most important recommendations?

    Compare these sources.

    Test my knowledge.

### 🎯 Source-Specific Work

Choose exactly which sources should be used for an operation.

Single source:

    ☑ Research Paper.pdf
    ☐ Lecture Notes.pdf
    ☐ YouTube Video

The operation uses only the selected source.

Multiple sources:

    ☑ Research Paper.pdf
    ☑ Lecture Notes.pdf
    ☐ YouTube Video

The operation can use both selected sources.

This supports workflows such as:

- Single-document summaries
- Multi-document summaries
- Comparisons
- Study guides
- Questions and answers
- Notes
- Knowledge tests
- Cross-source analysis

---

## 🧠 NoteTube Studio

NoteTube Studio provides additional tools for working with selected sources.

Current Studio capabilities include:

- FAQ
- Study Guide
- Table of Contents
- Timeline
- Briefing Document
- Podcast generation

Studio operations can use one or multiple selected sources.

---

## 🎙️ AI Podcast

NoteTube can transform source material into an AI-generated podcast-style conversation.

Current podcast functionality includes:

- Two AI hosts
- Host voice selection
- Director's Notes
- Custom podcast instructions
- Generated dialogue
- Audio generation
- Podcast playback
- Live Podcast Mode

The interactive podcast mode can use the current knowledge context to generate context-aware responses.

---

# 🧠 AI Architecture

NoteTube currently uses Google's Gemini API for AI generation.

The general RAG pipeline is:

    Source
       ↓
    Document Processing
       ↓
    Text Extraction
       ↓
    Text Chunking
       ↓
    Embedding Generation
       ↓
    ChromaDB
       ↓
    User Question
       ↓
    Query Embedding
       ↓
    Semantic Search
       ↓
    Selected Source Filtering
       ↓
    Relevant Context
       ↓
    Gemini
       ↓
    AI Response

When sources are selected, retrieval is restricted to those sources.

---

# 🏗️ Technology Stack

## Frontend

- React 18
- Vite
- Tailwind CSS
- Lucide React
- Axios

## Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite

## AI

- Google Gemini API
- Google GenAI SDK
- Gemini embeddings

## Vector Search

- ChromaDB

## Document Processing

- YouTube Transcript API
- PyPDF / LangChain document loaders
- Recursive text splitting

## Audio

- Edge TTS

---

# 📁 Project Structure

    NoteTube/
    │
    ├── backend/
    │   ├── main.py
    │   ├── api/
    │   ├── database/
    │   ├── services/
    │   └── ...
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   ├── pages/
    │   │   ├── hooks/
    │   │   └── ...
    │   ├── package.json
    │   └── ...
    │
    ├── docs/
    │   ├── RESPONSIVE_QA.md
    │   ├── RESPONSIVE_LAYOUT_AUDIT.md
    │   ├── VISUAL_POLISH.md
    │   └── ...
    │
    ├── requirements.txt
    ├── README.md
    ├── .gitignore
    └── ...

---

# ⚙️ Requirements

Before running NoteTube, install:

- Python 3.10+
- Node.js 18+
- npm
- Git

You also need a Google Gemini API key.

---

# 🚀 Installation

## 1. Clone the repository

    git clone https://github.com/teechevia/Notetube.git
    cd Notetube

To switch to a specific branch:

    git checkout <branch-name>

---

# 🐍 Backend Setup

From the NoteTube root directory:

## Create a virtual environment

    python -m venv venv

## Activate it on Windows PowerShell

    .\venv\Scripts\Activate

After activation, your terminal should look similar to:

    (venv) PS D:\...\Notetube>

## Install dependencies

    pip install -r requirements.txt

---

# 🔐 Environment Variables

Create a `.env` file in the location expected by the backend configuration.

For example:

    GEMINI_API_KEY=your_gemini_api_key_here

Replace the placeholder with your actual Gemini API key.

### ⚠️ Never commit secrets

Do not put API keys directly into source code.

Your `.gitignore` should exclude files and directories such as:

    .env
    venv/
    __pycache__/
    node_modules/
    chroma_db/

---

# ▶️ Run NoteTube

NoteTube requires both the backend and frontend development servers.

## Terminal 1 — Backend

From the project root:

    .\venv\Scripts\Activate
    cd backend
    python -m uvicorn main:app --reload --port 8000

The backend normally runs at:

    http://127.0.0.1:8000

FastAPI documentation:

    http://127.0.0.1:8000/docs

Keep this terminal running.

---

## Terminal 2 — Frontend

Open a second terminal.

From the NoteTube root:

    cd frontend
    npm install
    npm run dev

Vite will display the frontend URL in the terminal.

It will normally be:

    http://localhost:5173

Open the displayed URL in your browser.

---

# 🔎 Retrieval-Augmented Generation

When a user asks a question, NoteTube performs semantic retrieval.

    User Question
          ↓
    Generate Query Embedding
          ↓
    Search ChromaDB
          ↓
    Retrieve Relevant Chunks
          ↓
    Apply Selected Source Filters
          ↓
    Build AI Context
          ↓
    Send Context + Question to Gemini
          ↓
    Generate Answer

Source selection directly affects retrieval.

For example, if only `Research Paper.pdf` is selected, the retrieval operation is restricted to that source.

---

# 🗂️ Source Selection

Users can change source selection at any time.

## One source

    ☑ Research Paper.pdf
    ☐ Lecture Notes.pdf
    ☐ YouTube Video

Only the selected source is used for the relevant operation.

## Multiple sources

    ☑ Research Paper.pdf
    ☑ Lecture Notes.pdf
    ☐ YouTube Video

The operation can use both selected sources.

## All sources

Users can select all available sources when workspace-wide analysis is desired.

Selection does not create duplicate sources.

---

# 💾 Conversation Persistence

Conversation history is persisted by the application.

After refreshing the browser, the current workspace should retain:

- Sources
- Conversation messages
- Workspace state
- Current conversation

Refreshing the page should not create a new empty conversation.

Conversation history and source selection are separate concepts.

Deleting a source should not automatically remove unrelated conversation history.

---

# 🗄️ Data Storage

## SQLite

SQLite stores structured application data such as:

- Source metadata
- Workspace information
- Conversation history
- Chat messages

## ChromaDB

ChromaDB stores and searches document embeddings used for semantic retrieval.

The vector database is persisted locally.

---

# 🌐 API

The backend exposes endpoints for source management, chat, Studio, and podcast functionality.

Examples include:

    POST   /sources
    POST   /sources/pdf
    GET    /sources
    DELETE /sources/{id}
    DELETE /sources/all

    POST   /chat

    POST   /studio/generate

    POST   /studio/podcast/interact
    POST   /studio/podcast/audio

Conversation persistence endpoints are also provided for storing and retrieving chat history.

---

# 📱 Responsive Design

NoteTube uses a responsive three-panel workspace that adapts to smaller screens without changing the underlying information architecture.

## Desktop

    1920 × 1080
    1440 × 900
    1280 × 800

## Tablet

    1024 × 768
    834 × 1194
    768 × 1024

## Mobile

    430 × 932
    412 × 915
    390 × 844
    375 × 812
    360 × 800

The interface uses:

- CSS Grid
- Flexbox
- Tailwind responsive classes
- Mobile Sources navigation
- Mobile Studio navigation
- Independent panel scrolling
- Responsive cards
- Responsive typography

The desktop workspace retains the Sources / Interactive Session / Studio structure, while smaller screens provide mobile-oriented navigation and drawers.

---

# 🧪 Development & Testing

Before committing changes, verify that:

- Backend starts successfully
- Frontend starts successfully
- Sources can be added
- Sources can be deleted
- Sources can be selected
- Multiple sources can be selected
- Sources can be deselected
- Selected sources control AI operations
- Chat works
- Conversation survives page refresh
- Studio actions work
- Podcast generation works
- Theme switching works
- Mobile navigation works
- Mobile source deletion works
- Intended panel scrolling works
- No unnecessary horizontal overflow is introduced

---

# 🧹 Before Committing

Do not commit temporary or generated development files.

Check that the repository does not contain unintended:

    .env
    venv/
    node_modules/
    __pycache__/
    temporary screenshots
    debug output
    temporary browser recordings
    generated test files
    local databases
    temporary scripts

Keep secrets and local development artifacts out of Git.

---

# 🔀 Git Workflow

Create a feature branch:

    git checkout -b your-branch-name

Check changes:

    git status

Stage changes:

    git add .

Commit:

    git commit -m "Describe your changes"

Push:

    git push origin your-branch-name

---

# 🛡️ Security

Never commit:

- API keys
- Passwords
- Authentication tokens
- `.env` files
- Private credentials

If a secret is accidentally committed, revoke or rotate it immediately.

---

# 🐛 Troubleshooting

## Backend does not start

Activate the virtual environment:

    .\venv\Scripts\Activate

Reinstall dependencies:

    pip install -r requirements.txt

Start the backend:

    cd backend
    python -m uvicorn main:app --reload --port 8000

---

## Frontend does not start

From the frontend directory:

    npm install
    npm run dev

---

## Gemini API errors

Check that:

- Your Gemini API key exists.
- The environment variable name matches the backend configuration.
- The `.env` file is in the expected location.
- The API key is valid.
- The key has not been accidentally committed to Git.

---

## Port 8000 is already in use

Stop the process using the port or start the backend on another port:

    python -m uvicorn main:app --reload --port 8001

Make sure the frontend/backend configuration uses the corresponding port.

---

# 📖 Documentation

Additional project documentation is available in:

    docs/

Documentation may include:

- Architecture notes
- Responsive QA reports
- Development notes
- Feature implementation notes
- Visual polish notes
- Persistence implementation notes

---

# 🚧 Project Status

NoteTube is actively under development.

Current development focuses on:

- Source ingestion
- Semantic search
- RAG-based conversations
- Persistent conversations
- Source selection
- Multi-source analysis
- AI study tools
- AI podcasts
- Responsive workspace behavior

---

# 🎯 Vision

The long-term goal of NoteTube is to create a powerful personal knowledge workspace where users can bring their own information and transform it into an interactive learning environment.

The intended workflow is:

    IMPORT
      ↓
    UNDERSTAND
      ↓
    ASK
      ↓
    EXPLORE
      ↓
    STUDY
      ↓
    CREATE
      ↓
    REMEMBER

NoteTube aims to turn static information into an interactive AI-powered learning experience.

---
---

# 🛣️ Roadmap / Future Plans

NoteTube is actively evolving toward a more capable personal AI knowledge workspace.

Planned improvements include:

- 🧠 Advanced human-quality note generation
- 📖 Rich, structured notes with better explanations and learning flow
- 🖼️ Visual elements and diagrams inside generated notes
- 📄 Downloadable notes in PDF format
- 💾 Offline access to generated notes
- 🌐 Web-assisted research and fact enrichment
- 🤖 Multi-model AI architecture with automatic model selection
- 🎯 Intelligent routing of tasks to the most suitable available AI model
- 🎙️ Improved AI podcast generation
- 📊 Better study materials and interactive learning tools
- 🔎 More accurate source-grounded research and retrieval
- 📚 Advanced multi-source comparison and synthesis
- 🧩 More powerful Studio generation tools
- 📱 Continued mobile UX improvements
- ⚡ Performance and reliability improvements

The goal is for NoteTube to become an intelligent research and learning workspace that can choose the appropriate AI capability for each task while keeping the user's knowledge, sources, conversations, and generated materials connected in one workspace.

---
---

# 👥 Contributors

NoteTube is developed collaboratively using Git and feature branches.

Contributions, improvements, testing, and feedback are welcome.

---

# 📄 License

NoteTube is licensed under the MIT License.

See the [LICENSE](LICENSE) file for the full license text.

---

# ⭐ Note

NoteTube is inspired by the concept of AI-powered knowledge workspaces and is an independent project. It is not affiliated with or endorsed by Google or NotebookLM.

---