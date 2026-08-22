import json
from services.ai import ask_ai

def clean_json_response(res: str):
    res = res.strip()
    if res.startswith("```json"):
        res = res[7:]
    if res.endswith("```"):
        res = res[:-3]
    return res.strip()

def generate_flashcards(transcript: str):
    prompt = f"Create 10 important flashcards from this transcript. Return ONLY a valid JSON array of objects. Each object must have exactly two keys: 'front' (the question or term) and 'back' (the answer or definition). Do NOT include markdown blocks like ```json.\n\nTranscript:\n{transcript}"
    res = ask_ai(prompt)
    try:
        return json.loads(clean_json_response(res))
    except Exception as e:
        return [{"front": "Error generating flashcards", "back": str(e)}]

def generate_quiz(transcript: str):
    prompt = f"Create a 5-question multiple choice quiz from this transcript. Return ONLY a valid JSON array of objects. Each object must have: 'question' (string), 'options' (array of 4 strings), and 'answer' (the exact string of the correct option). Do NOT include markdown blocks.\n\nTranscript:\n{transcript}"
    res = ask_ai(prompt)
    try:
        return json.loads(clean_json_response(res))
    except Exception as e:
        return [{"question": "Error generating quiz", "options": ["A", "B", "C", "D"], "answer": "A"}]

def generate_ppt(transcript: str):
    prompt = f"Create a presentation slide deck outline from this transcript. Use Markdown. Each slide should have a title starting with '## Slide: [Title]' and 3-5 concise bullet points. Make it well-structured and engaging.\n\nTranscript:\n{transcript}"
    return ask_ai(prompt)

def generate_podcast(transcript: str):
    prompt = f"Write a conversational, engaging podcast script based on this transcript. There should be two hosts (Host A and Host B) discussing the key takeaways in a fun, easy-to-understand way. Use Markdown formatting.\n\nTranscript:\n{transcript}"
    return ask_ai(prompt)

