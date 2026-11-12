import logging

from app.agent.loop import build_system_prompt, respond
from app.db import SessionLocal

logging.basicConfig(level=logging.INFO, format="  [%(name)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
TENANT_ID = 1

with SessionLocal() as db:
    messages = [{"role": "system", "content": build_system_prompt(db, TENANT_ID)}]
    print("Type 'quit' to exit.")
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in {"quit", "exit"}:
            break
        if text:
            print("Receptionist:", respond(db, TENANT_ID, messages, text))