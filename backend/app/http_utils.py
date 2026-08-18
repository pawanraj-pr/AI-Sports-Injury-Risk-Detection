import re


def safe_filename(name: str) -> str:
    
    ascii_only = name.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r'[\\"\r\n\x00-\x1f]', "", ascii_only)
    cleaned = cleaned.strip() or "download"
    return cleaned
