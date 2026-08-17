import re


def safe_filename(name: str) -> str:
    """
    Content-Disposition header values must be ASCII with no quotes/control
    characters — anything else risks the ASGI server rejecting a malformed
    header and resetting the connection (which the browser reports as a
    generic network failure, not a normal HTTP error). Since filenames here
    are partly built from user-entered data (athlete code), sanitize before
    it ever reaches a header.
    """
    ascii_only = name.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r'[\\"\r\n\x00-\x1f]', "", ascii_only)
    cleaned = cleaned.strip() or "download"
    return cleaned
