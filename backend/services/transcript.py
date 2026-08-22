from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from services.summarizer import summarize_text

def process_video(url: str):
    parsed_url = urlparse(url)
    video_id = None
    
    if parsed_url.hostname == 'youtu.be':
        video_id = parsed_url.path[1:]
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com') and parsed_url.path == '/watch':
        video_id_list = parse_qs(parsed_url.query).get("v")
        if video_id_list:
            video_id = video_id_list[0]

    if not video_id:
        return {"error": "Invalid Youtube URL"}

    try:
        transcript = YouTubeTranscriptApi().fetch(video_id)
    except Exception as e:
        return {"error": "Could not retrieve transcript. Subtitles might be disabled for this video."}

    text = " ".join([entry.text for entry in transcript])

    summary = summarize_text(text)

    return {
        "video_id": video_id,
        "transcript": text,
        "summary": summary
    }