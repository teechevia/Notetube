from fastapi import FastAPI
from routes.youtube import router

app = FastAPI()

app.include_router(router)