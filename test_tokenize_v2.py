import re

def tokenize_v2(text: str) -> list[str]:
    """Tokenize text, treating hyphens as word separators."""
    # First replace hyphens with spaces, then tokenize
    text = text.replace('-', ' ')
    return re.findall(r"[\w./]+|[\u4e00-\u9fff]", text.lower())

def tokenize_original(text: str) -> list[str]:
    return re.findall(r"[\w./-]+|[\u4e00-\u9fff]", text.lower())

text = "- User prefers Markdown-first memory."

print(f"Original tokenization: {tokenize_original(text)}")
print(f"v2 tokenization: {tokenize_v2(text)}")

query = "markdown memory"
print(f"\nQuery original: {tokenize_original(query)}")
print(f"Query v2: {tokenize_v2(query)}")