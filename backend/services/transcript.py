from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from services.summarizer import summarize_text

def process_video(url: str):
    parsed_url = urlparse(url)
    video_id = parse_qs(parsed_url.query).get("v")

    if not video_id:
        return {"error": "Invalid Youtube URL"}

    transcript = YouTubeTranscriptApi().fetch(video_id[0])

    text = " ".join([entry.text for entry in transcript])

    summary = summarize_text(text)

    return {
        "video_id": video_id[0],
        "transcript": text,
        "summary": summary
    }