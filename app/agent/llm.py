import httpx
from app.config import settings 

def chat(messages: list[dict], tools: list[dict] = None) -> dict:
    """ Send a conversation to the model and return it's reply message"""

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "stream": False,
        "think": False,
    }

    if tools: 
        payload["tools"] = tools

    response = httpx.post(f'{settings.ollama_url}/api/chat', json=payload, timeout = 60)
    response.raise_for_status()
    return response.json()['message']
