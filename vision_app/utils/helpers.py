def build_api_url(base: str, path: str) -> str:
    base = (base or "").rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    path = path.lstrip("/")
    return f"{base}/{path}"

def safe_trim(s: str, limit: int = 1200):
    if s is None:
        return None
    return s if len(s) <= limit else (s[:limit] + "...(trimmed)")

def extract_choice_content(data: dict):
    try:
        if not isinstance(data, dict):
            return None
        choices = data.get("choices")
        if not choices or not isinstance(choices, list):
            return None
        first = choices[0]
        msg = first.get("message")
        if isinstance(msg, dict) and "content" in msg:
            return msg["content"]
        if "text" in first:
            return first["text"]
        return None
    except Exception:
        return None
