import json
import time

from app.agent.llm import chat

tools = [{
    "type": "function",
    "function": {
        "name": "get_available_slots",
        "description": "List free appointment times for a service on a given date.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date as YYYY-MM-DD"},
            },
            "required": ["date"],
        },
    },
}]

questions = [
    "Hi there!",
    "What times do you have free on 2026-11-04?",
]

for text in questions:
    messages = [
        {"role": "system", "content": "You are a receptionist for a salon. Use tools when needed."},
        {"role": "user", "content": text},
    ]
    start = time.perf_counter()
    reply = chat(messages, tools)
    elapsed = time.perf_counter() - start
    print(f"\n> {text}  ({elapsed:.1f}s)")
    print(json.dumps(reply, indent=2))