import re

with open('frontend/src/services/geminiLive.js', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('console.debug("Gemini Live: connected");', 'console.log("LIVE_CONNECTED");')
text = re.sub(r'console\.debug\(\s*"Gemini Live tool call:"[^)]+\);', 'console.log("LIVE_TOOL_CALL", functionCall.name, functionCall.args);', text)

text = re.sub(r'(const result = await onToolCall\?\.\([\s\S]*?\);)', r'\1\nconsole.log("LIVE_TOOL_RESULT");', text)
text = re.sub(r'(session\.sendToolResponse\(\{\s*functionResponses,?\s*\}\);)', r'\1\nconsole.log("LIVE_TOOL_RESPONSE_SENT");', text)

text = text.replace('playAudioChunk(part.inlineData.data);', 'console.log("LIVE_MODEL_AUDIO"); playAudioChunk(part.inlineData.data);')
text = text.replace('onTurnComplete?.();', 'console.log("LIVE_TURN_COMPLETE"); onTurnComplete?.();')

with open('frontend/src/services/geminiLive.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Logs added successfully.")
