from services.ai import ask_ai

def summarize_text(transcript: str):

    prompt = f"""
    You are an expert educator. Create a highly organized, comprehensive set of study notes from the following educational transcript.
    
    Please structure the notes using Markdown with:
    - # Main Title
    - ## Key Topics (with bullet points)
    - ## Detailed Explanations
    - ## Important Terms & Definitions
    - ## Quick Summary

    Make it very easy to read and beautifully formatted.

    Transcript:

    {transcript}
    """

    summary = ask_ai(prompt)

    return summary