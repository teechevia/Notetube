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
    prompt = f"Create 10 important flashcards from this text. Return ONLY a valid JSON array of objects. Each object must have exactly two keys: 'front' (the question or term) and 'back' (the answer or definition). Do NOT include markdown blocks like ```json.\n\nText:\n{transcript}"
    res = ask_ai(prompt)
    try:
        return json.loads(clean_json_response(res))
    except Exception as e:
        return [{"front": "Error generating flashcards", "back": str(e)}]

def generate_quiz(transcript: str):
    prompt = f"Create a 5-question multiple choice quiz from this text. Return ONLY a valid JSON array of objects. Each object must have: 'question' (string), 'options' (array of 4 strings), and 'answer' (the exact string of the correct option). Do NOT include markdown blocks.\n\nText:\n{transcript}"
    res = ask_ai(prompt)
    try:
        return json.loads(clean_json_response(res))
    except Exception as e:
        return [{"question": "Error generating quiz", "options": ["A", "B", "C", "D"], "answer": "A"}]

def generate_briefing_doc(transcript: str):
    prompt = f"Create a comprehensive Briefing Doc summarizing this text. Use Markdown. Include an Executive Summary, Key Takeaways, and Detailed Breakdown.\n\nText:\n{transcript}"
    return ask_ai(prompt)

def generate_human_notes(transcript: str):
    prompt = f"Act as a diligent student watching a lecture. Create natural, human-made study notes based on this text. Use bullet points, bold text for emphasis, and make it look like authentic personal notes rather than a robotic AI summary.\n\nText:\n{transcript}"
    return ask_ai(prompt)

def generate_faq(transcript: str):
    prompt = f"Create a Frequently Asked Questions (FAQ) document based on this text. Use Markdown. Format as Q: and A: pairs.\n\nText:\n{transcript}"
    return ask_ai(prompt)

def generate_podcast_script(text: str, instruction: str = "", host_a: str = "Host A", host_b: str = "Host B") -> list:
    base_prompt = "You are writing a podcast script..."

    prompt = f"""
    Based on the following source material, generate a two-person podcast script between '{host_a}' and '{host_b}'.

    Make it conversational, engaging, and informative.
    """

    if instruction:
        prompt += f"\nCRITICAL INSTRUCTION FOR THE PODCAST: {instruction}\n"

    prompt += f"""
    Return the response as a JSON array of objects, where each object has 'speaker' (either "{host_a}" or "{host_b}") and 'text'.
    Do NOT wrap the output in markdown code blocks, just raw JSON.

    Source Material:
    {text}
    """

    response = ask_ai(prompt, system_instruction="You must reply with valid JSON array only.")

    import json
    try:
        # Try to parse and strip any potential markdown formatting
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        return [{"speaker": host_a, "text": "Error generating podcast script."}]

def generate_interactive_podcast_response(user_message: str, chat_history: str, host_a: str = "Host A", host_b: str = "Host B") -> list:
    prompt = f"""
    You are roleplaying as two podcast hosts, '{host_a}' and '{host_b}'.
    The user has just joined your live podcast and said: "{user_message}"

    Here is the recent context of the conversation:
    {chat_history}

    Generate a very short, continuous podcast response (1 to 3 lines total) where the hosts reply directly to the user or discuss what the user just said.

    Return the response as a JSON array of objects, where each object has 'speaker' (either "{host_a}" or "{host_b}") and 'text'.
    Do NOT wrap the output in markdown code blocks, just raw JSON.
    """

    response = ask_ai(prompt, system_instruction="You must reply with valid JSON array only.")

    import json
    try:
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        return [{"speaker": host_a, "text": "Whoa, looks like we had a technical glitch!"}]
