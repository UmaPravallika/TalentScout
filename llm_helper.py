# llm_helper.py
import json
import requests
from typing import Dict, Generator, List, Optional

# Ollama local API endpoint (ensure ollama serve is running)
OLLAMA_API_URL = "http://localhost:11434/api/chat"

def _ollama_chat_request(model: str, messages: List[Dict], stream: bool = True, temperature: float = 0.7):
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {"temperature": temperature}
    }
    resp = requests.post(OLLAMA_API_URL, json=payload, stream=stream, timeout=300)
    resp.raise_for_status()
    return resp

def stream_llm(model: str, messages: List[Dict], temperature: float = 0.7) -> Generator[str, None, None]:
    """
    Stream tokens from Ollama to the UI. Yields chunks of text.
    """
    resp = _ollama_chat_request(model=model, messages=messages, stream=True, temperature=temperature)
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
            # Ollama streaming lines include a "message" object
            delta = data.get("message", {}).get("content", "")
            if delta:
                yield delta
        except json.JSONDecodeError:
            # ignore malformed lines
            continue

def complete_llm(model: str, messages: List[Dict], temperature: float = 0.7) -> str:
    """
    Non-streaming completion (useful when we need to parse JSON output).
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature}
    }
    resp = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "")

def safe_json_extract(text: str) -> Optional[dict]:
    """
    Extract JSON object from a text response safely.
    """
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end+1])
    except Exception:
        pass
    return None
