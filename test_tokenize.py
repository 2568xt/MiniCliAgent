import re

def _tokenize(text: str) -> list[str]:
    return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())

text = "- User prefers Markdown-first memory."
tokens = _tokenize(text)
print(f"Text: {repr(text)}")
print(f"Tokens: {tokens}")

# Check what happens with just "Markdown-first memory"
text2 = "Markdown-first memory."
tokens2 = _tokenize(text2)
print(f"\nText2: {repr(text2)}")
print(f"Tokens2: {tokens2}")

# Check for query
query = "markdown memory"
query_tokens = _tokenize(query)
print(f"\nQuery: {repr(query)}")
print(f"Query tokens: {query_tokens}")