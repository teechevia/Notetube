from fastapi import APIRouter
from models.request_models import VideoRequest
from services.transcript import process_video

router = APIRouter()

@router.get("/")
def home():
    return {"message": "LectureLens AI backend running"}
 
@router.post("/video")
def receive_video(video: VideoRequest):
    return process_video(video.url)
