text = "Python is a powerful programming language."
chunk_size = 15
def chunk_text(text: str, chunk_size: int = 3000) -> list[str]:
    chunks = []
    i = 0
    while(i<len(text)):
        end = i + chunk_size
        if (end<len(text)):
            last_space = text.rfind(' ', i, end)
            if (last_space!=-1):
                end = last_space + 1
            
        chunk = text[i:end]
        chunks.append(chunk)
        i = end
    return chunks

print(chunk_text(text, chunk_size))