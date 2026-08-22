from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import sources

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources.router)