# YouTube Import Fix

## Root Cause
When adding YouTube videos, the backend (`load_youtube` in `backend/services/loaders.py`) was using `YouTubeTranscriptApi().fetch(video_id)`. Recently, YouTube has rolled out changes that block direct fetching via certain internal API routes, resulting in a `502 Bad Gateway` error and returning an empty document array. This empty array triggered a `400 Bad Request` downstream, causing the frontend to pop up the `Failed to add source` alert.

## Fix
Refactored `load_youtube` to use the more robust `api.list(video_id)` method instead. It now gracefully discovers the available transcripts, prioritizing manually created English transcripts, then falling back to auto-generated English ones, and finally to any available language transcript if English isn't present. This successfully extracts the `.start` and `.text` segments without hitting the `502` wall.

*Note: Since the backend was running in your own terminal (and possibly without `--reload`), you will need to restart your `uvicorn` instance for the Python changes to take effect.*
