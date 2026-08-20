from services.ai import ask_ai

def summarize_text(transcript: str):

    prompt = f"""
    Summarize the following educational transcript.

    Give:
    - Important topics
    - Key points
    - Simple explanation

    Transcript:

    {transcript}
    """

    summary = ask_ai(prompt)

    return summary